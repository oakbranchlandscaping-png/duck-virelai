"""Memory stage M-1 (R9-R07): the card is built from slots, bounded, and sufficient.

Author: Claude (Alpha build seat), 2026-09-29. DESIGN_VIRELAI_MEMORY_v1 §5.3, §10 (T1, T3, T5, T7,
T10, T11); memory laws M3, M4, M5, M7 (DOCTRINE_FRICTION_AXIOMS_v3).

The strongest test here is the stress ladder: a simulated Duck that reads **only the card** — the
payload production puts in the prompt — carries a synthetic world with 2, 8 and 20 levers from G2 to
a satisfied G4-A. If any gate needed something the card did not show, it could not finish (M5). And
the card must be the same size whether the world holds 2 levers or 20 (M4).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from card_duck import run_ladder
from inference.framework.card_builder import (
    CARD_BUDGET,
    CERTIFIED,
    build_card,
    fill_certified_fields,
    worst_case_request_chars,
)
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import GateContractError

V2_RECORD = Path(__file__).parent / "fixtures" / "ft09_kaggle_v2_record.json.gz"
FLATNESS = 1_000  # characters: the most any gate's card may grow from 2 levers to 20
LADDER_GATES = ["G2-COUNTER", "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS"]


@pytest.fixture(scope="module")
def ladders():
    return {levers: run_ladder(levers) for levers in (2, 8, 20)}


@pytest.fixture(scope="module")
def v2():
    return replay(load_record(V2_RECORD), measure=False)


@pytest.fixture(scope="module")
def v2_in_g2():
    return replay(load_record(V2_RECORD), max_steps=56, measure=False)


def test_a_duck_that_reads_only_the_card_completes_the_ladder(ladders):
    """M5: the card carries everything each step needs, from the counter to every lever's orbit."""
    for levers, run in ladders.items():
        assert run.gates == LADDER_GATES, levers
        assert run.machine.gate_id == "G4-B-LEVER-RELATIONS"  # the ladder's last built gate (R9-R12)
        assert run.machine.status == "SATISFIED", (levers, run.stopped)
        orbits = run.machine.target_journal.active_product("G4.2-LEVER-ORBITS").payload
        assert len(orbits["lever_entities"]) == levers
        assert orbits["phase1_status"] == "COMPLETE"


def test_the_card_is_flat_in_the_number_of_findings(ladders):
    """T1 / M4: no gate's card grows with the levers found, and none exceeds its budget."""
    for gate in LADDER_GATES:
        sizes = {levers: run.largest[gate] for levers, run in ladders.items()}
        assert max(sizes.values()) < CARD_BUDGET, (gate, sizes)
        assert sizes[20] - sizes[2] <= FLATNESS, (gate, sizes)
    for levers, run in ladders.items():
        assert not run.over_budget, (levers, run.over_budget)


def test_the_v2_record_replays_with_answers_written_from_the_card():
    """The five accepted live answers, rebuilt from the card's templates, are accepted again."""
    result = replay(load_record(V2_RECORD), answer_source="card")
    assert (result.steps_replayed, result.answers_used, result.stopped) == (121, 5, None)
    assert max(sample.chars for sample in result.samples) < CARD_BUDGET


def test_a_field_without_a_slot_cannot_reach_the_card(v2):
    """T3 / M3: the card is built, not trimmed; state it has no slot for changes nothing."""
    machine = v2.machine
    before = build_card(machine).render()
    original = machine.gate_view

    def noisy_view():
        view = dict(original())
        view["attribution_contract"] = {"confirmation_records": ["x" * 5_000] * 20}
        view["some_future_ledger"] = list(range(10_000))
        return view

    machine.gate_view = noisy_view
    try:
        assert build_card(machine).render() == before
    finally:
        machine.gate_view = original


def test_identical_levers_group_into_one_digest_line_and_a_different_one_does_not(ladders):
    """T5 / M7: grouping is by exact signature; it never merges items that differ."""
    same = ladders[20]
    lines = [line for line in build_card(same.machine).payload["world_model"] if line.startswith("[G3-LEVERS] levers")]
    assert len(lines) == 1 and "levers x20" in lines[0]
    odd = run_ladder(8, wide_last=True)
    lines = [line for line in build_card(odd.machine).payload["world_model"] if line.startswith("[G3-LEVERS] levers")]
    assert sorted(line.split(":")[0] for line in lines) == ["[G3-LEVERS] levers x1", "[G3-LEVERS] levers x7"]


def test_the_world_model_shows_only_what_gates_have_certified(v2, v2_in_g2):
    """T7 / M2: a product appears in the digest only once its gate closes."""
    during_g2 = v2_in_g2.machine
    assert during_g2.gate_id == "G2-COUNTER"
    gates = [line.split("]")[0][1:] for line in build_card(during_g2).payload["world_model"]]
    assert gates == ["G0-ACTION-METADATA", "G1-EGO"]
    in_g3 = v2.machine
    gates = [line.split("]")[0][1:] for line in build_card(in_g3).payload["world_model"]]
    assert gates == ["G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER"]
    counter_line = build_card(in_g3).payload["world_model"][2]
    assert "EFFECTIVE_TRANSITIONS_ONLY" in counter_line and "period 32" in counter_line


def test_the_card_shows_the_budgets_the_world_imposes(v2):
    card = build_card(v2.machine).payload
    budgets = card["progress"]["budgets"]
    assert budgets["counter_source_cells_remaining"] == 38  # 64 bar cells less 13 ticks of 2
    assert budgets["counter_ticks_remaining"] == 19


def test_the_same_state_renders_the_same_bytes(v2):
    """T11 / M7."""
    first = v2
    second = replay(load_record(V2_RECORD), measure=False)
    assert build_card(first.machine).render() == build_card(first.machine).render()
    assert build_card(first.machine).render() == build_card(second.machine).render()


def test_certified_fields_are_filled_by_the_controller_but_still_checked():
    machine = replay(load_record(V2_RECORD), max_steps=56, measure=False).machine  # its own: it submits
    card = build_card(machine).payload
    template = card["answer_template"]
    assert template["candidate_id"] == CERTIFIED
    assert template["evidence_refs"] == CERTIFIED
    assert template["novel_prediction"]["scope"] == CERTIFIED
    filled = fill_certified_fields(machine, template)
    live = machine.gate_view()["answer_template"]
    assert filled["candidate_id"] == live["candidate_id"]
    assert filled["novel_prediction"]["scope"] == live["novel_prediction"]["scope"]
    wrong = {**template, "candidate_id": "COUNTER-CANDIDATE-not-this-one"}
    with pytest.raises(GateContractError):
        machine.submit_answer(json.loads(json.dumps({
            **wrong, "trigger": "EFFECTIVE_TRANSITIONS_ONLY",
            "tracked_variable": "t", "mechanism": "m", "bookkeeping_reason": "b",
            "competing_models": ["c"], "falsifier": "f",
        })))


def test_preflight_worst_case_request_fits_the_model_window():
    """T10: the largest request a turn can make, every slot at budget, fits the context window."""
    from inference.agent.tool_agent import ToolAgent

    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True)
    tools_chars = len(json.dumps(agent._tools(Path("unused_tool_runtime_state.json"))))
    worst = worst_case_request_chars(
        system_prompt_chars=len(agent._system_prompt),
        tool_schema_chars=tools_chars,
        prompt_body_chars=4_000,
        tool_output_chars=2 * 4 * 1_024,  # two tool results at the 1,024-token output cap
        output_reserve_chars=3 * 16_384,  # a 16k-token reasoning and answer reserve
    )
    assert worst // 3 < 65_536, worst  # three characters per token, the harness's own estimate
