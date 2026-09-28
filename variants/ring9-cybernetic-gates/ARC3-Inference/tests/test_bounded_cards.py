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

import json

from inference.agent import tool_agent
from test_g2_counter_axiom import _act, _answer, _replay_real_segment

BUDGET = tool_agent._GATED_GATE_CONTEXT_MAX_CHARS


def _binding_context_chars(machine) -> int:
    """Mirror ToolAgent._binding_gate_payload + _gate_context_update rendering."""
    view = machine.gate_view()
    context = dict(view)
    if view.get("next_operation") == "QUERY_NEXT_PROBE":
        capability = machine.next_probe_capability()
        if capability is not None:
            context["current_probe"] = capability
            context["instruction"] = "x" * 110
    return len("VIRELAI GATE (binding):\n" + json.dumps(context, sort_keys=True))


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


def test_every_card_through_a_full_ft09_g3_sweep_fits_the_budget():
    machine, grid = _close_g2_on_ft09()
    worst = _binding_context_chars(machine)
    transition_id = 58
    while machine.gate_id == "G3-LEVERS" and machine.next_probe_capability() is not None:
        _g3_null_click(machine, grid, transition_id)
        transition_id += 1
        worst = max(worst, _binding_context_chars(machine))
        assert worst < BUDGET, f"card reached {worst} characters at transition {transition_id}"
    assert transition_id - 58 >= 60, "the sweep should visit the whole ft09 roster"


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
