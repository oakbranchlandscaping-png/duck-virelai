"""Unified tree regression: a bounded PRESUMED_UNREACHABLE target must not block G3's inventory.

Author: Claude (Alpha build seat), 2026-10-05. Review of the Ring 9 unification (501a6e6).

On the NAV line (main 130a374) a target Duck declared PRESUMED_UNREACHABLE, with its record in
``_bounded_ambiguities``, counted as bounded: the completed roster had a legal move (the coverage
report) and the inventory accepted it as an ambiguous entity. The merge replaced main's inline
check with the click line's ``_unbounded_entities`` helper (R9-R21), whose bounded set predates the
NAV state. At 501a6e6 the same roster reports "no legal move", A2 rests the level in PLAY-NORMAL
(R9-R24 D22), and G4 never opens on a NAV world that has one unreachable target.
"""
from __future__ import annotations

from test_g3_scheduler import machine_for

NAV_ACTIONS = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]


def _roster_with_one_unreachable_target():
    machine = machine_for(NAV_ACTIONS, "EMBODIED_EGO")
    adapter = machine._adapters["G3-LEVERS"]
    assert machine.next_probe_capability() is not None  # opens the roster and its journal
    journal = adapter.lifecycle_journal
    ledger = adapter._ensure_entity_ledger()
    first, second = (ledger.entity_for_member(item["member_id"]) for item in adapter._ensure_frontier()[:2])
    journal.transition(first, "PRESUMED_UNREACHABLE", evidence_ref="E-ROUTE-EXHAUSTED", actor="TEST",
                       reason="reachable component exhausted")
    adapter._bounded_ambiguities[first] = {
        "evidence_ref": "E-ROUTE-EXHAUSTED", "retry_condition": "terrain or world state changes",
        "disposition": "PRESUMED_UNREACHABLE", "terminal_state": "PRESUMED_UNREACHABLE",
    }
    journal.attempt(second, evidence_ref="E-SECOND-NULL")
    journal.response(second, positive=False, evidence_ref="E-SECOND-NULL")
    journal.close(second, evidence_ref="E-SECOND-NULL")
    adapter._target_index = len(adapter._ensure_frontier())
    assert machine.next_probe_capability() is None
    return machine, adapter, first, second


def test_a_bounded_unreachable_target_leaves_the_completed_roster_a_legal_move():
    machine, adapter, first, _second = _roster_with_one_unreachable_target()
    assert machine.legal_move_status()["legal"] is True
    assert first not in adapter._unbounded_entities()
    assert adapter.answer_blocked() is None


def test_the_coverage_report_accepts_a_bounded_unreachable_target():
    machine, adapter, first, second = _roster_with_one_unreachable_target()
    answer = machine.submit_answer({
        "answer_id": "G3-coverage-test",
        "lever_entities": [],
        "clean_null_entities": [second],
        "ambiguous_entities": [first],
        "evidence_refs": ["E-ROUTE-EXHAUSTED", "E-SECOND-NULL"],
        "explanation": "One target closed null; the other is outside the exhausted reachable component.",
        "competing_models": ["The unreachable target may become reachable after the world changes."],
        "falsifier": "A certified path or contact to the unreachable target becomes available.",
    })
    assert answer.answer_kind == "G3_BOUNDED_COVERAGE_REPORT"
    assert adapter._bounded_coverage_answer is answer
