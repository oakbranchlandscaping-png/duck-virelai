"""Replay the two v2 rehearsal G3 lifecycle crashes in HYBRID worlds, k008 and k013.

Author: Claude (Alpha build seat), 2026-10-10. This is the G3 lifecycle slice. Ruling 23 gave it to Sol;
the Director reassigned it to Claude.

Both worlds are HYBRID: G3 clicks every roster row first (CLICK phase), then pilots the ego to the
same rows (NAV phase).

**The crash.** A pointer null closed its row (`G3-CLOSED`, "entity G3 obligations complete") while the
body-contact obligation for the same row was still owed. NAV then went back to the row:
- In k008, a GAME_OVER during the pursuit tried `G3-CLOSED -> AMBIGUOUS`, at transition 61.
- In k013, Duck's reachability release tried `G3-CLOSED -> PRESUMED_UNREACHABLE`.

Neither is a legal transition, and the table stays as it is. The row closed too early. In a HYBRID
world, a pointer null records the negative response and leaves the row open for its NAV pass.
NAV skips rows whose G3 work is already settled.

**How the replay works.** The records come from `tools/record_g3_lifecycle_fixtures.py`. They hold the
recorded transitions and answers, and the gate machine re-derives everything else. The NAV steps are
driven the way the live controller drives them: it plans first, then acts. At every step the test
asserts that the controller's planned action equals the recorded one.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from inference.framework.controller_executor import ANSWER, CONTROLLER, DUCK, next_owned_step
from inference.framework.record_replay import (
    load_record, lossless_outcome, merge_recorded_answer, record_like_live, replay,
)
from inference.framework.virelai_gates import GateContractError

FIXTURES = Path(__file__).parent / "fixtures"
K008 = FIXTURES / "ring9_v2_k008_g3_lifecycle_record.json.gz"
K013 = FIXTURES / "ring9_v2_k013_g3_lifecycle_record.json.gz"
K008_FIRST_NAV = 43  # G3-LEVERS:NAV:1:1 in the live run
K013_FIRST_NAV = 401
K008_POINTER_NULLS = ("E0001", "E0002", "E0004", "E0005", "E0006")
K013_LIVE_LEVERS = {  # the live target ledger's LEVER_FOUND rows, all pointer witnesses
    "E0007", "E0008", "E0009", "E0010", "E0011", "E0012", "E0013", "E0014", "E0024",
}


def _cut(record, transition_id):
    return next(i for i, step in enumerate(record["steps"]) if step["transition_id"] == transition_id)


def _drive(path, first_nav, plans_through=None):
    """Replay up to the first G3 NAV step, then plan and act as the controller does.

    The controller's planned action must equal the recorded one through ``plans_through`` (every step when it is
    None). After it the recorded actions play back as history: the planner is still asked, its plans are kept,
    but it is not held to the live run's choices (Sol, 2026-10-11, G3 reset continuity revision 2).
    """
    record = load_record(path)
    cut = _cut(record, first_nav)
    result = replay(record, max_steps=cut, measure=False)
    machine = result.machine
    g3 = machine._adapters["G3-LEVERS"]
    result.plans = {}
    for step in record["steps"][cut:]:
        capability = machine.next_probe_capability()
        planned = g3.planned_nav_step(capability["target"])
        result.plans[int(step["transition_id"])] = planned
        assert planned is not None, step["transition_id"]
        if plans_through is None or int(step["transition_id"]) <= plans_through:
            assert planned.action == step["action"]["action"], step["transition_id"]
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"], **dict(step.get("decision") or {})}, [step["action"]]
        )
        result.grid, outcome = lossless_outcome(
            result.grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"),
            probe_id=probe.probe_id,
        )
        record_like_live(machine, probe, outcome, record["valid_actions"])
        result.steps_replayed += 1
    return record, result, machine, g3


@pytest.fixture(scope="module")
def k008():
    # The live k008 pursuit was planned from a stale ego (its ledger missed RESET 31): plans are held to the
    # live run only at T43; T44 onward is historical playback through the T61 boundary.
    return _drive(K008, K008_FIRST_NAV, plans_through=K008_FIRST_NAV)


@pytest.fixture(scope="module")
def k013():
    """Drive k013, release E0001 with Duck's recorded answer, then let the controller run the NAV pass.

    Every later row of this world is in the same unreachable component, so the controller reuses that
    understanding (reachability semantic reuse) to release each row, and needs no recorded frame.
    """
    record, _result, machine, g3 = _drive(K013, K013_FIRST_NAV)
    journal = g3.lifecycle_journal
    levers_at_nav_start = {entity_id: list(item.events) for entity_id, item in journal.entities.items() if item.witness_refs}
    step = next_owned_step(machine)  # the live controller's planning call certifies the routing limit
    pending = dict(g3._pending_reachability or {})
    template = machine.gate_view()["answer_template"]
    machine.submit_answer(merge_recorded_answer(template, record["answers"][-1]))
    released = (journal.entities["E0001"].state, [event.to_state for event in journal.entities["E0001"].events],
                g3._target_index)
    for _ in range(80):  # the controller's own loop, reachability answers only
        if g3._complete_reason:
            break
        owned = next_owned_step(machine)
        if owned.owner == CONTROLLER and owned.kind == ANSWER:
            assert owned.answer["answer_kind"] == "TARGET_REACHABILITY"
            machine.submit_answer(owned.answer)
        else:
            assert owned.owner == DUCK  # a routing limit is certified first, then answered next call
    nav_end = {
        "complete_reason": g3._complete_reason,
        "unbounded": g3._unbounded_entities(),
        "lever_events": {entity_id: list(journal.entities[entity_id].events) for entity_id in levers_at_nav_start},
        "levers": _levers(g3),
    }
    inventory_step = next_owned_step(machine)  # the controller answers the completed roster from the record
    try:
        inventory = machine.submit_answer(inventory_step.answer)
        refusal = None
    except GateContractError as error:
        inventory, refusal = None, str(error)
    return {
        "first_step": step, "pending": pending, "released": released, "machine": machine, "g3": g3,
        "levers_at_nav_start": levers_at_nav_start, "nav_end": nav_end,
        "inventory_step": inventory_step, "inventory": inventory, "refusal": refusal,
    }


def _levers(g3):
    """Entities holding a witness, entities with a lever discovery, and G4-ready entities lacking either ref."""
    journal = g3.lifecycle_journal
    return (
        {entity_id for entity_id, item in journal.entities.items() if item.witness_refs},
        {item["entity_id"] for item in g3._lever_discoveries.values()},
        {entity_id for entity_id, item in journal.entities.items()
         if item.state == "G4-READY" and not (item.witness_refs and item.answer_refs)},
    )


def _assert_no_lever_without_witness(g3, expected_levers):
    _assert_lever_sets(_levers(g3), expected_levers)


def _assert_lever_sets(levers, expected_levers):
    witnessed, discovered, unsupported = levers
    assert witnessed == discovered == set(expected_levers)
    assert unsupported == set()


def test_k008_pointer_nulls_stay_open_for_the_nav_pass():
    record = load_record(K008)
    result = replay(record, max_steps=_cut(record, K008_FIRST_NAV), measure=False)
    g3 = result.machine._adapters["G3-LEVERS"]
    for entity_id in K008_POINTER_NULLS:
        lifecycle = g3.lifecycle_journal.entities[entity_id]
        assert lifecycle.state == "NO_RESPONSE_YET", entity_id
        assert lifecycle.events[-1].reason == "scoped null observation"


def test_k008_boundary_during_the_nav_pursuit_completes_without_a_crash(k008):
    record, result, _machine, g3 = k008
    assert result.steps_replayed == sum(step.get("kind") != "RESET" for step in record["steps"])
    lifecycle = g3.lifecycle_journal.entities["E0001"]
    assert [event.to_state for event in lifecycle.events] == [
        "ATTEMPTED", "NO_RESPONSE_YET", "ATTEMPTED", "AMBIGUOUS",
    ]
    assert lifecycle.events[-1].reason == "target attempt interrupted by boundary"
    assert g3._deferred_observations[-1]["observation"] == "LEVER_TARGET_ATTEMPT_INTERRUPTED_BY_BOUNDARY"
    assert g3._deferred_observations[-1]["entity_id"] == "E0001"
    _assert_no_lever_without_witness(g3, ())


def test_k008_t44_plan_starts_from_the_egos_true_post_reset_footprint(k008):
    """G3 reset continuity: at T44 the repaired planner stands where the ego really is after RESET 31, not
    where the stale ledger left it before the death (the live run's stand)."""
    from test_g3_ledger_frame_sync import _record_board

    _record, result, _machine, g3 = k008
    plan = result.plans[44]
    ledger = g3.entity_ledger
    ego = ledger.entities[ledger.role_entities("EGO")[0]].sightings[0]
    top, left = min(r for r, _ in ego.cells), min(c for _, c in ego.cells)
    shape = {(r - top, c - left) for r, c in ego.cells}

    def ego_at(stand, board):  # the ego's footprint, anchored at ``stand``, on a board rebuilt from the record
        return {board[stand[0] + r][stand[1] + c] for r, c in shape} == {ego.integer}

    after_t43, before_death = _record_board("k008", 43), _record_board("k008", 30)
    assert tuple(plan.stand) == (12, 16) and ego_at(plan.stand, after_t43)
    assert ego_at((12, 12), before_death) and not ego_at((12, 12), after_t43)  # the live run's stale stand


def test_k013_reachability_release_completes_without_a_crash(k013):
    assert k013["first_step"].owner == DUCK
    assert k013["pending"]["target_entity_id"] == "E0001"
    state, transitions, target_index = k013["released"]
    assert state == "PRESUMED_UNREACHABLE"
    assert transitions == ["ATTEMPTED", "NO_RESPONSE_YET", "ATTEMPTED", "PRESUMED_UNREACHABLE"]
    assert target_index == 1


def test_k013_nav_pass_completes_past_the_pointer_witnessed_levers(k013):
    """NAV pursues again only rows whose G3 obligation is still open. Ruling 22 settles a
    pointer-witnessed lever at G3 and sends its repetition, mechanism and conditions to G4.

    Without the skip, this pass crashed on the first lever row (`G4-READY -> PRESUMED_UNREACHABLE`
    for E0007).
    """
    nav_end = k013["nav_end"]
    assert nav_end["complete_reason"] == "NAV_ENUMERATION_COMPLETE"
    assert nav_end["unbounded"] == {}
    assert nav_end["lever_events"] == k013["levers_at_nav_start"]  # untouched by the NAV pass
    _assert_lever_sets(nav_end["levers"], K013_LIVE_LEVERS)


def test_k013_controller_inventory_is_accepted_after_a_terrain_close(k013):
    """A terrain close settles a row that the CLICK pass had bounded as ambiguous (E0018).

    The bound must go with it, as it already does on a reachability reopen and on a mu return.
    The stale bound listed E0018 as ambiguous while the journal held it as a scoped null, so G3
    refused the controller's inventory.
    """
    step = k013["inventory_step"]
    assert (step.owner, step.kind, step.answer["answer_kind"]) == (CONTROLLER, ANSWER, "LEVER_INVENTORY")
    assert k013["refusal"] is None
    g3 = k013["g3"]
    journal = g3.lifecycle_journal
    inventory = k013["inventory"].novel_prediction
    assert set(inventory["lever_entities"]) == K013_LIVE_LEVERS
    assert "E0018" in inventory["clean_null_entities"] and "E0018" not in inventory["ambiguous_entities"]
    assert journal.entities["E0018"].events[-1].actor == "NAV_TERRAIN_MAP"
    assert set(inventory["ambiguous_entities"]) == {
        entity_id for entity_id, item in journal.entities.items() if item.state == "PRESUMED_UNREACHABLE"
    }
    assert g3._inventory_answer is k013["inventory"]
    _assert_no_lever_without_witness(g3, K013_LIVE_LEVERS)
