"""Axiom A6: what Duck is shown each turn is bounded regardless of world size.

Author: Claude (Alpha build seat), 2026-09-28.

Regression for REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md. G2 closed live on ft09, then the G3
card came to 67,939 characters against the runtime's 24,000-character budget and the game ended.
Detail is queried, never pushed: the card carries counts, the current target, a bounded window of
the ranked roster and paged query handles; the lossless record stays in ``snapshot()``.

The tests walk every gate state of the largest recorded world (ft09: 65 ranked objects) from the
real G2 record through a complete scripted G3 sweep and assert each binding card fits the budget.
"""
from __future__ import annotations

import pytest

from inference.agent import tool_agent
from inference.framework.gate_card import render_binding_gate_context
from test_g2_counter_axiom import _act, _answer, _replay_real_segment

BUDGET = tool_agent._GATED_GATE_CONTEXT_MAX_CHARS


def _binding_context_chars(machine) -> int:
    """The production renderer (R9-R06 moved it to inference.framework.gate_card)."""
    return len(render_binding_gate_context(machine))


def _close_g2_on_ft09():
    machine, grid, _ = _replay_real_segment()
    control = {"action": "ACTION6", "row": 36, "col": 36}
    _answer(machine, action=control, predicate="COUNTER_REWRITE", amount=2)
    changed = [[r, c, 8, 9] for r in range(36, 42) for c in range(36, 42)]
    changed += [[63, 59, 12, 11], [63, 58, 12, 11]]
    grid, _ = _act(machine, grid, 57, control, changed)
    assert machine.gate_id == "G3-LEVERS"
    return machine, grid


def _g3_null_click(machine, grid, transition_id):
    from test_g2_counter_axiom import _outcome

    capability = machine.next_probe_capability()
    assert capability is not None
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    _after, outcome = _outcome(grid, transition_id, capability["actions"][0], [])
    machine.record_outcome(probe, outcome)


def test_ft09_g3_card_fits_the_budget_on_entry():
    machine, _grid = _close_g2_on_ft09()
    chars = _binding_context_chars(machine)
    assert chars < BUDGET, f"G3 entry card is {chars} characters"
    view = machine.gate_view()
    frontier = view["inherited_frontier"]
    assert frontier["view"] == "WINDOWED_ROSTER"
    assert frontier["candidate_count"] == 64
    assert len(frontier["candidates"]) < frontier["candidate_count"]
    assert frontier["candidates_omitted"] == frontier["candidate_count"] - len(frontier["candidates"])
    assert "inventory" in frontier["roster_query"]
    # The current target is always on the card.
    capability = machine.next_probe_capability()
    assert capability["target"]["member_id"] in {row["member_id"] for row in frontier["candidates"]}


@pytest.mark.parametrize("inherits, clicks, inherited", [(False, 64, 0), (True, 10, 54)])
def test_every_card_through_a_full_ft09_g3_sweep_fits_the_budget(inherits, clicks, inherited):
    """Pre-D5 protocol: G3 clicks the whole roster. R9-R08 (ruling D5): G2's 54 total nulls are
    inherited as scoped nulls, so G3 clicks only the 10 objects G2 never saw null."""
    machine, grid = _close_g2_on_ft09()
    machine.protocol["g3_inherits_g2_nulls"] = inherits
    worst = _binding_context_chars(machine)
    transition_id = 58
    while machine.gate_id == "G3-LEVERS" and machine.next_probe_capability() is not None:
        _g3_null_click(machine, grid, transition_id)
        transition_id += 1
        worst = max(worst, _binding_context_chars(machine))
        assert worst < BUDGET, f"card reached {worst} characters at transition {transition_id}"
    assert transition_id - 58 == clicks
    inheritance = machine._adapters["G3-LEVERS"]._inheritance
    assert (0 if inheritance is None else inheritance.count) == inherited


def test_every_g2_card_of_the_real_ft09_record_fits_the_budget():
    from test_g2_counter_axiom import _decode, _load, _machine

    data = _load()
    grid = _decode(data["initial_grid"])
    machine = _machine(grid)
    worst = _binding_context_chars(machine)
    for step in data["steps"]:
        grid, _ = _act(machine, grid, step["transition_id"], step["action"], step["changed"])
        worst = max(worst, _binding_context_chars(machine))
    assert worst < BUDGET, f"a G2 card reached {worst} characters"


def test_snapshot_keeps_the_lossless_roster():
    machine, _grid = _close_g2_on_ft09()
    snapshot = machine._adapters["G3-LEVERS"].snapshot()
    assert len(snapshot["inherited_frontier"]["candidates"]) == 64
    assert len(snapshot["source_frontier"]["candidates"]) == 65
