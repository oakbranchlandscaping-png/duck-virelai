from inference.framework.counter_verification import (
    MASK_SENTINEL,
    compare_counter_prediction,
    compare_counter_boundary,
    compile_counter_candidates,
    mask_law_from_supported,
    masked_grid,
    monitor_locked_counter,
    prediction_for,
)


def outcome(step, row, col, changed, *, evidence_id=None):
    return {
        "evidence_id": evidence_id or f"E-{step}",
        "transition_id": step,
        "shape_before": [3, 4],
        "shape_after": [3, 4],
        "action": {"action": "ACTION6", "row": row, "col": col},
        "acted_site": {"row": row, "col": col},
        "changed_cells": changed,
    }


def rewrite(row, col, before=7, after=4):
    return {"row": row, "col": col, "before": before, "after": after}


def test_recurrent_remote_rewrite_compiles_candidate_across_distinct_clicks():
    evidence = [
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1)]),
    ]
    candidates = compile_counter_candidates(evidence)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.status == "SCHEDULED_BOOKKEEPING_CANDIDATE"
    assert candidate.rewrite == "7->4"
    assert candidate.observed_support == ((0, 0), (0, 1))
    assert candidate.witness_evidence_refs == ("E-1", "E-2")


def test_same_intervention_and_direct_target_are_not_candidates():
    same = [
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 0, [rewrite(0, 1)]),
    ]
    assert compile_counter_candidates(same) == ()
    targeted = [
        outcome(1, 0, 0, [rewrite(0, 0)]),
        outcome(2, 0, 1, [rewrite(0, 1)]),
    ]
    assert compile_counter_candidates(targeted) == ()


def test_flat_reversal_or_geometry_change_breaks_the_candidate_window():
    flat = [outcome(1, 2, 0, [rewrite(0, 0)]), outcome(2, 2, 1, [])]
    assert compile_counter_candidates(flat) == ()
    reversal = [
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1, before=4, after=7)]),
    ]
    assert compile_counter_candidates(reversal) == ()
    geometry = [outcome(1, 2, 0, [rewrite(0, 0)]), outcome(2, 2, 1, [rewrite(0, 1)])]
    geometry[1]["shape_after"] = [4, 4]
    assert compile_counter_candidates(geometry) == ()


def test_supported_future_recurrence_issues_reversible_mask_law():
    candidate = compile_counter_candidates([
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1)]),
    ])[0]
    prediction = prediction_for(candidate, declared_at_transition=2)
    future = outcome(3, 2, 2, [rewrite(0, 2)])
    comparison = compare_counter_prediction(prediction, future, evidence_ref="E-3")
    assert comparison.outcome == "SUPPORTED"
    law = mask_law_from_supported(candidate, comparison)
    raw = ((7, 7, 7, 0), (0, 0, 0, 0), (1, 2, 3, 4))
    view = masked_grid(raw, law)
    assert raw[0] == (7, 7, 7, 0)
    assert view[0] == (MASK_SENTINEL, MASK_SENTINEL, MASK_SENTINEL, 0)
    assert law.reversibility == "RAW_GRID_PRESERVED_MASK_IS_DERIVED_VIEW"


def test_two_class_exchange_recovers_and_masks_the_full_bar_footprint():
    first = outcome(1, 2, 0, [rewrite(0, 2)])
    first["site_transitions"] = [
        {"row": 0, "col": col, "before": value, "after": 4 if col == 2 else value}
        for col, value in enumerate((7, 7, 7, 4))
    ]
    second = outcome(2, 2, 1, [rewrite(0, 1)])
    second["site_transitions"] = [
        {"row": 0, "col": col, "before": value, "after": 4 if col == 1 else value}
        for col, value in enumerate((7, 7, 4, 4))
    ]
    candidate = compile_counter_candidates([first, second])[0]
    assert candidate.source_integer == 7
    assert candidate.replacement_integer == 4
    assert candidate.footprint_geometry == "HORIZONTAL_BAR"
    assert candidate.full_bar_footprint == ((0, 0), (0, 1), (0, 2), (0, 3))

    prediction = prediction_for(candidate, declared_at_transition=2)
    comparison = compare_counter_prediction(
        prediction, outcome(3, 2, 2, [rewrite(0, 0)]), evidence_ref="E-3"
    )
    law = mask_law_from_supported(candidate, comparison)
    assert law.cells == candidate.full_bar_footprint


def test_prediction_must_be_future_and_exact_rate():
    candidate = compile_counter_candidates([
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1)]),
    ])[0]
    prediction = prediction_for(candidate, declared_at_transition=2)
    stale = compare_counter_prediction(prediction, outcome(2, 2, 2, [rewrite(0, 2)]), evidence_ref="E-X")
    assert stale.outcome == "INDETERMINATE"
    wrong_rate = compare_counter_prediction(
        prediction,
        outcome(3, 2, 2, [rewrite(0, 2), rewrite(0, 3)]),
        evidence_ref="E-3",
    )
    assert wrong_rate.outcome == "CONTRADICTED"


def test_counter_locks_only_when_extrema_coincide_with_boundary_event():
    first = outcome(1, 2, 0, [rewrite(0, 2)])
    first["site_transitions"] = [
        {"row": 0, "col": col, "before": value, "after": 4 if col == 2 else value}
        for col, value in enumerate((7, 7, 7, 4))
    ]
    second = outcome(2, 2, 1, [rewrite(0, 1)])
    second["site_transitions"] = [
        {"row": 0, "col": col, "before": value, "after": 4 if col == 1 else value}
        for col, value in enumerate((7, 7, 4, 4))
    ]
    candidate = compile_counter_candidates([first, second])[0]
    terminal = outcome(4, 2, 2, [rewrite(0, 0)])
    terminal["site_transitions"] = [
        {"row": 0, "col": col, "before": value, "after": 4}
        for col, value in enumerate((7, 4, 4, 4))
    ]
    terminal["boundary_event"] = {"state": "GAME_OVER", "game_over": True}
    boundary = compare_counter_boundary(
        candidate, terminal, evidence_ref="E-4", prior_standing=(1, 3)
    )
    assert boundary.outcome == "SUPPORTED"
    assert boundary.boundary_kind == "GAME_OVER_AT_SOURCE_MIN_REPLACEMENT_MAX"


def test_extrema_without_consequence_remain_pending():
    candidate = compile_counter_candidates([
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1)]),
    ])[0]
    plain = outcome(3, 2, 2, [rewrite(0, 0)])
    plain["boundary_event"] = {"state": "PLAYING", "game_over": False}
    boundary = compare_counter_boundary(
        candidate, plain, evidence_ref="E-3", prior_standing=None
    )
    assert boundary.outcome == "PENDING"


def test_locked_counter_monitor_separates_world_delta_and_reopens_on_violations():
    candidate = compile_counter_candidates([
        outcome(1, 2, 0, [rewrite(0, 0)]),
        outcome(2, 2, 1, [rewrite(0, 1)]),
    ])[0]
    prediction = prediction_for(candidate, declared_at_transition=2)
    comparison = compare_counter_prediction(
        prediction, outcome(3, 2, 2, [rewrite(0, 2)]), evidence_ref="E-3"
    )
    law = mask_law_from_supported(candidate, comparison)
    later = outcome(4, 2, 3, [rewrite(0, 0), rewrite(2, 2, before=1, after=6)])
    verdict = monitor_locked_counter(candidate, law, later)
    assert verdict.disposition == "VALID"
    assert verdict.hud_changed_cells == ((0, 0),)
    assert verdict.world_changed_cells == ((2, 2),)

    held = monitor_locked_counter(candidate, law, outcome(5, 2, 3, []))
    assert held.reason == "LOCKED_COUNTER_UNEXPECTEDLY_HELD"
    targeted = monitor_locked_counter(candidate, law, outcome(6, 0, 0, [rewrite(0, 0)]))
    assert targeted.reason == "COUNTER_DIRECTLY_TARGETED"
    entangled = outcome(7, 2, 3, [rewrite(0, 0, before=7, after=9)])
    assert monitor_locked_counter(candidate, law, entangled).reason == (
        "COUNTER_ARITHMETIC_CHANGED_OR_ENTANGLED"
    )
