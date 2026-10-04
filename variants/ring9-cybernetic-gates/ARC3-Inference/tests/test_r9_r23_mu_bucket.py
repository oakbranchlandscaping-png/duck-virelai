"""R9-R23: the mu bucket. Objects that stump a gate never stop the ladder, and are retried when stuck.

Author: Claude (Alpha build seat), 2026-10-03. RULING_MU_BUCKET_v1_2026-10-03 (Director-ruled).

Live (ring9-carry-vc33-v6, level 3): G3 certified 7 levers, but one object (E0028) could not be attributed.
Levers pressed earlier in the sweep had moved it: by its click it occupied no cell, and the clicked cell
belonged to E0071, an object born mid-sweep. G3 then waited for evidence no move could bring, and the A2
watchdog ended the run. Under the ruling, G3 closes PARTIAL with E0028 in the mu bucket, and the ladder
studies the 7 levers. A stuck ladder returns to mu, but only on a changed board.

Fixture: the v6 run's own record (110 transitions), driven as live: the controller's own answers, Duck's
recorded answers where Duck answered, every recorded action through a freshly issued capability. The
positive retry is shown on the same level-3 board with one clean-null object recast as a mystery
(the stand-in documented in ``_recast_as_mystery``), because no live run has yet produced one.
Each test failed before R9-R23.
"""
from __future__ import annotations

import json

from inference.framework import mu_return
from inference.framework.controller_executor import next_owned_step, return_to_mu_if_stuck
from inference.framework.level_model import freeze_level
from inference.framework.mu_return import return_to_mu, world_address_now
from inference.framework.record_replay import (
    _answer_index, click_world_machine, decode_grid, load_record, lossless_outcome, merge_recorded_answer,
    record_like_live, record_protocol,
)

from tests.test_r9_r21_g3_contradicted import FIXTURES

VC33_CARRY_V6 = FIXTURES / "vc33_kaggle_carry_v6_record.json.gz"
SEVEN = ["E0010", "E0011", "E0012", "E0013", "E0015", "E0016", "E0017"]
LEVERS, REACTIONS, ORBITS = "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS"


def _drive_v6():
    """The whole live record as live; Duck's recorded answers are used only where the gate asks Duck."""
    record = load_record(VC33_CARRY_V6)
    grid = decode_grid(record["initial_grid"])
    machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
    pending: dict[str, list] = {}
    for answer in record["answers"]:
        pending.setdefault(answer["gate_id"], []).append(answer)

    def answers() -> None:
        while True:
            owned = next_owned_step(machine)
            if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
                machine.submit_answer(json.loads(json.dumps(owned.answer)))
                continue
            view = machine.gate_view()
            template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
            due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
            ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
            if template and (ready or (due and owned.owner == "DUCK" and queue)):
                machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
                continue
            return

    for step in record["steps"]:
        answers()
        capability = machine.next_probe_capability()
        assert capability is not None, (step["transition_id"], machine.gate_id)
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"))
        record_like_live(machine, probe, outcome, record["valid_actions"])
    answers()
    return machine, grid


def _recast_as_mystery(machine, entity_id="E0014"):
    """Stand-in: a clean-null object still on the board, filed as if its try had been unresolved elsewhere."""
    g3 = machine._adapters[LEVERS]
    ledger, journal = g3._ensure_entity_ledger(), g3.lifecycle_journal
    member = next(key for key, value in ledger.member_to_entity.items() if value == entity_id)
    journal.reopen(entity_id, evidence_ref="STAND-IN", reason="recast as a mystery for the positive retry")
    journal.transition(entity_id, "AMBIGUOUS", evidence_ref="STAND-IN", actor="STAND-IN", reason="stand-in")
    record = g3._bound_ambiguity(
        member_id=member, entity_id=entity_id, evidence_ref="E-STAND-IN",
        disposition="UNRESOLVED_ATTRIBUTION", reason="stand-in for an unresolved first try",
    )
    machine.mu.file(record, gate_id=LEVERS, tried_address="an-earlier-board", transition_id=0)
    return set(map(tuple, ledger.cells_for(entity_id)))


def _controller_steps(machine, grid, responsive, transition=110, limit=40):
    """Let the controller act; on this stand-in board only clicks on ``responsive`` change anything remote."""
    for _ in range(limit):
        step = next_owned_step(machine)
        if step.owner != "CONTROLLER":
            return grid
        if step.kind == "ANSWER":
            machine.submit_answer(json.loads(json.dumps(step.answer)))
            continue
        probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
        transition += 1
        hit = (step.action["row"], step.action["col"]) in responsive
        changed = [[r, c, grid[r][c], (grid[r][c] + 1) % 10] for r in (2, 3) for c in range(10, 16)] if hit else []
        grid, outcome = lossless_outcome(grid, transition, step.action, changed)
        record_like_live(machine, probe, outcome, ["ACTION6"])
    return grid


def test_g3_closes_partial_and_the_ladder_studies_the_seven_levers():
    """M-2 (D13, D17): the mystery object no longer stops level 3; the controller writes the inventory."""
    machine, _grid = _drive_v6()
    inventory = machine.target_journal.active_product(LEVERS).payload
    assert inventory["closure"] == "PARTIAL"
    assert inventory["lever_entities"] == SEVEN and inventory["ambiguous_entities"] == ["E0028"]
    text = machine._adapters[LEVERS]._inventory_answer.mechanism
    assert "mu bucket" in text and "rewrite their own cells" not in text
    assert machine.gate_id == ORBITS and machine.legal_move_status()["legal"] is True
    machine.gate_view()
    assert list(machine._adapters[ORBITS]._ordered_entities) == SEVEN


def test_the_mystery_is_filed_with_its_board_and_is_not_retried_on_the_same_board():
    """M-1, M-4 (D12): the entry keeps the board it was tried on and who owned the clicked cell."""
    machine, _grid = _drive_v6()
    entry = machine.mu.entries["E0028"]
    assert entry["status"] == "OPEN" and entry["inertness_claim_permitted"] is False
    (first,) = entry["tries"]
    assert first["transition_id"] == 107 and first["clicked_owner"] == "E0071" and first["tried_address"]
    assert first["tried_address"] == world_address_now(machine)  # nothing outside the counter changed since
    assert machine.mu.revisitable(world_address_now(machine)) == [] and return_to_mu(machine) == []


def test_a_mystery_that_left_the_board_is_settled_absent_not_clicked(monkeypatch):
    """M-4: on a changed board, an object that occupies no cell is closed ABSENT; G3 stays closed."""
    machine, _grid = _drive_v6()
    monkeypatch.setattr(mu_return, "world_address_now", lambda _machine: "a-changed-board")
    assert return_to_mu(machine) == []
    assert machine.mu.entries["E0028"]["status"] == "ABSENT"
    assert machine.target_journal.active_product(LEVERS) is not None


def test_a_mystery_that_responds_on_a_changed_board_joins_the_lever_study():
    """M-5 (D14, D15): witness, repeat and dossier as usual; G4 keeps its work and queues the late lever."""
    machine, grid = _drive_v6()
    machine.gate_view()
    reactions = machine._adapters[REACTIONS]
    kept = {entity: answer.answer_id for entity, answer in reactions._answers.items()}
    responsive = _recast_as_mystery(machine)
    assert return_to_mu(machine) == ["E0014"] and machine.gate_id == LEVERS
    probe = machine._adapters[LEVERS].next_probe()
    assert probe.purpose == "MU_REVISIT" and (probe.actions[0]["row"], probe.actions[0]["col"]) in responsive
    _controller_steps(machine, grid, responsive)
    inventory = machine.target_journal.active_product(LEVERS).payload
    assert inventory["closure"] == "PARTIAL" and inventory["ambiguous_entities"] == ["E0028"]
    assert sorted(inventory["lever_entities"]) == sorted([*SEVEN, "E0014"])
    assert machine.mu.entries["E0014"]["status"] == "RESOLVED_LEVER"
    assert {entity: reactions._answers[entity].answer_id for entity in kept} == kept  # earlier answers kept
    assert "E0014" in reactions._answers
    machine.gate_view()
    assert machine._adapters[ORBITS]._ordered_entities[-1] == "E0014"
    assert machine._adapters["G4-B-LEVER-RELATIONS"]._answer is None  # Phase 2 restarts on the new lever set


def test_the_controller_returns_to_mu_only_when_stuck(monkeypatch):
    """M-4 (D14): never while a gate still has a move; before a stop, when the board has changed."""
    machine, _grid = _drive_v6()
    _recast_as_mystery(machine)
    assert return_to_mu_if_stuck(machine) is None and machine.mu.entries["E0014"]["status"] == "OPEN"
    monkeypatch.setattr(machine.target_router, "current", lambda: None)  # every built gate satisfied
    assert return_to_mu_if_stuck(machine) == "mu return on a changed board: retrying E0014"


def test_each_level_model_freezes_its_mu_bucket():
    """M-6 (D16): open questions travel with the level's frozen model."""
    machine, _grid = _drive_v6()
    assert [model["mu"] for model in machine.levels] == [[], []]
    model = freeze_level(machine, {"transition_id": 110, "boundary_event": {"level_before": 3, "level_after": 4}})
    assert [(item["entity_id"], item["status"]) for item in model["mu"]] == [("E0028", "OPEN")]
