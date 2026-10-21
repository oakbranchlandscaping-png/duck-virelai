"""WO-RUNTIME-01 §6 / Director ruling Q3: G3 after an unresolved G2 with live counter candidates.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Fail-first: on the base an unresolved G2 does not exist,
so nothing builds an exclusion region and an in-region counter tick would read as a remote lever response.
"""
from __future__ import annotations

from inference.framework.counter_verification import CounterCandidate
from inference.framework.lever_attribution import attribute_lever_outcome
from inference.framework.record_replay import load_record, replay

LS20 = "tests/fixtures/ls20_kaggle_unified_v1_record.json.gz"


def _candidate(cid: str, cells, source=12, replacement=11) -> CounterCandidate:
    return CounterCandidate(candidate_id=cid, rewrite=f"{source}->{replacement}", observed_support=tuple(cells[:1]),
                            full_bar_footprint=tuple(cells), footprint_geometry="ROW", source_integer=source,
                            replacement_integer=replacement, witness_evidence_refs=("E-x",),
                            witness_transition_ids=(1,), intervention_keys=("k",), amount_per_transition=(1,))


def _outcome(changes, acted=(5, 5), transition=9):
    return {"transition_id": transition, "acted_site": {"row": acted[0], "col": acted[1]},
            "changed_cells": [{"row": r, "col": c, "before": b, "after": a} for r, c, b, a in changes],
            "site_transitions": [{"row": r, "col": c, "before": b, "after": a} for r, c, b, a in changes]}


def _attribution(outcome, target_cells):
    return attribute_lever_outcome(outcome, evidence_ref=f"E-{outcome['transition_id']}", channel="POINTER",
                                   target_member_id="M0001", target_cells=target_cells, counter_mask_cells=(),
                                   ego_motion_cells=(), pre_action_owner_member_id="M0001")


def test_the_region_is_the_union_of_every_plausible_candidate():
    from inference.framework.counter_exclusion import Exclusion

    region = Exclusion([_candidate("A", [(0, 0), (0, 1)]), _candidate("B", [(9, 9)])]).region
    assert region == frozenset({(0, 0), (0, 1), (9, 9)})


def test_evidence_entirely_inside_the_region_cannot_certify_alone():
    """WO 24, 36: a counter tick inside R stays inconclusive with a typed masking reason; no false lever."""
    from inference.framework.counter_exclusion import Exclusion

    exclusion = Exclusion([_candidate("A", [(0, 0), (0, 1), (0, 2)])])
    raw = _attribution(_outcome([(0, 2, 12, 11)]), target_cells=[(5, 5)])
    assert raw.positive  # without exclusion the tick is a remote "lever" response
    screened = exclusion.screen(raw, target_cells=[(5, 5)], outcome=_outcome([(0, 2, 12, 11)]))
    assert not screened.positive
    assert screened.disposition == "UNRESOLVED_ATTRIBUTION"
    assert any("COUNTER_UNRESOLVED_EXCLUSION" in item for item in screened.limitations)
    assert any("COUNTER_UNRESOLVED" in item for item in screened.limitations)


def test_evidence_outside_the_region_still_qualifies():
    from inference.framework.counter_exclusion import Exclusion

    exclusion = Exclusion([_candidate("A", [(0, 0), (0, 1)])])
    outcome = _outcome([(0, 1, 12, 11), (5, 5, 3, 4)])
    screened = exclusion.screen(_attribution(outcome, [(5, 5)]), target_cells=[(5, 5)], outcome=outcome)
    assert screened.positive and set(screened.residue_cells) == {(5, 5)}
    assert any("COUNTER_UNRESOLVED" in item for item in screened.limitations)


def test_independently_localized_in_region_evidence_qualifies():
    """WO 25: inside R, but on the acted entity's own cells and predicted by no surviving candidate."""
    from inference.framework.counter_exclusion import Exclusion

    exclusion = Exclusion([_candidate("A", [(5, 5), (5, 6)])])
    outcome = _outcome([(5, 5, 3, 4)])  # not the candidate's 12->11 rewrite
    screened = exclusion.screen(_attribution(outcome, [(5, 5)]), target_cells=[(5, 5)], outcome=outcome)
    assert screened.positive


def test_in_region_evidence_a_candidate_predicts_does_not_qualify_even_on_the_entity():
    from inference.framework.counter_exclusion import Exclusion

    exclusion = Exclusion([_candidate("A", [(5, 5), (5, 6)])])
    outcome = _outcome([(5, 5, 12, 11)])
    screened = exclusion.screen(_attribution(outcome, [(5, 5)]), target_cells=[(5, 5)], outcome=outcome)
    assert not screened.positive


def test_unresolved_g2_with_a_live_candidate_carries_its_exclusion_region_to_g3():
    """WO 23: the G2 close records the plausible candidates and the region; G3 runs conservatively."""
    from inference.framework import counter_exclusion, gate_closure

    machine = replay(load_record(LS20), max_steps=11, measure=False).machine
    assert machine.counter.candidate is not None
    gate_closure.close_gate(machine, "G2-COUNTER", "HARD_BUDGET_SPENT")
    payload = machine.target_journal.active_product("G2-COUNTER").payload
    assert payload["status"] == "UNRESOLVED" and payload["product_kind"] == "COUNTER_UNRESOLVED"
    assert payload["plausible_counter_candidates"] and payload["counter_exclusion_region"]
    region = counter_exclusion.for_machine(machine).region
    assert region == frozenset(tuple(cell) for cell in payload["counter_exclusion_region"])
    assert machine.gate_id == "G3-LEVERS"


def test_an_old_inconclusive_row_is_never_promoted_by_rescreening():
    from inference.framework.counter_exclusion import Exclusion

    exclusion = Exclusion([_candidate("A", [(0, 0), (0, 1), (0, 2)])])
    outcome = _outcome([(0, 2, 12, 11)])
    held = exclusion.screen(_attribution(outcome, [(5, 5)]), target_cells=[(5, 5)], outcome=outcome)
    again = exclusion.screen(held, target_cells=[(5, 5)], outcome=outcome)
    assert not again.positive


def test_without_an_unresolved_g2_nothing_is_screened():
    from inference.framework import counter_exclusion

    machine = replay(load_record(LS20), max_steps=12, measure=False).machine
    assert counter_exclusion.for_machine(machine) is None
