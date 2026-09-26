from __future__ import annotations

from inference.agent.runtime_state import Frame
from inference.framework.probe_evidence import compact_probe_outcome, compile_probe_outcome


def _compile(before, after, *, action=None, reported=True):
    return compile_probe_outcome(
        probe_id="G1-EGO:test",
        transition_id=1,
        action=action or {"action": "ACTION1"},
        before_frame=Frame(grid=before, step=0, level=1),
        after_frame=Frame(grid=after, step=1, level=1),
        available_actions_before=["ACTION1"],
        available_actions_after=["ACTION1"],
        callback_payload={"board_changed": reported, "state": "PLAYING"},
    )


def test_unchanged_frames_override_incorrect_global_changed_flag():
    grid = ((0, 0), (0, 5))
    outcome = _compile(grid, grid, reported=True)
    assert not outcome["board_changed"]
    assert outcome["changed_cell_count"] == 0
    assert outcome["reported_board_changed"]
    assert "callback board_changed disagrees with captured frames" in outcome["limitations"]


def test_coordinate_scope_keeps_target_unchanged_and_remote_changed_separate():
    before = ((0, 0, 0), (0, 5, 0), (0, 0, 0))
    after = ((2, 0, 0), (0, 5, 0), (0, 0, 0))
    outcome = _compile(
        before,
        after,
        action={"action": "ACTION6", "row": 1, "col": 1},
    )
    assert outcome["board_changed"]
    assert outcome["target_local_changed_cell_count"] == 0
    assert outcome["remote_changed_cell_count"] == 1
    assert outcome["target_local_changes"] == []
    assert outcome["remote_changes"] == [
        {"row": 0, "col": 0, "before": 0, "after": 2}
    ]


def test_coordinate_scope_can_report_local_and_remote_changes_together():
    before = ((0, 0, 0), (0, 5, 0), (0, 0, 0))
    after = ((2, 0, 0), (0, 6, 0), (0, 0, 0))
    outcome = _compile(
        before,
        after,
        action={"action": "ACTION6", "row": 1, "col": 1},
    )
    assert outcome["target_local_changed_cell_count"] == 1
    assert outcome["remote_changed_cell_count"] == 1
    assert outcome["integer_transition_counts"] == {"0->2": 1, "5->6": 1}


def test_non_coordinate_action_does_not_invent_a_remote_scope():
    before = ((0, 5), (0, 0))
    after = ((0, 0), (0, 5))
    outcome = _compile(before, after)
    assert outcome["changed_cell_count"] == 2
    assert outcome["target_scope"] is None
    assert outcome["target_local_changed_cell_count"] is None
    assert outcome["remote_changed_cell_count"] is None
    assert outcome["unscoped_changed_cell_count"] == 2


def test_shape_change_is_lossless_and_explicitly_limited():
    outcome = _compile(((1,),), ((1, 2),), reported=True)
    assert outcome["shape_before"] == [1, 1]
    assert outcome["shape_after"] == [1, 2]
    assert outcome["changed_cells"] == [
        {"row": 0, "col": 1, "before": None, "after": 2}
    ]
    assert outcome["integer_transition_counts"] == {"MISSING->2": 1}
    assert "grid shape changed across the transition" in outcome["limitations"]


def test_compact_outcome_preserves_counts_refs_and_bounded_preview():
    before = (tuple(0 for _ in range(20)),)
    after = (tuple(1 for _ in range(20)),)
    outcome = _compile(before, after)
    compact = compact_probe_outcome(outcome, preview_limit=3)
    assert "changed_cells" not in compact
    assert compact["changed_cell_count"] == 20
    assert len(compact["changed_cells_preview"]) == 3
    assert compact["changed_cells_truncated"]
    assert compact["lossless_diff_ref"].startswith("D-")
    assert compact["site_transition_coverage"] == "TOTAL"
    assert compact["site_transitions_omitted"] == 20
    assert "site_transitions" not in compact


def test_total_site_ledger_retains_held_cells_for_footprint_arithmetic():
    outcome = _compile(((1, 1, 1, 0),), ((0, 1, 1, 1),))
    assert outcome["site_transition_coverage"] == "TOTAL"
    assert outcome["site_transitions"] == [
        {"row": 0, "col": 0, "before": 1, "after": 0, "outcome": "CHANGED"},
        {"row": 0, "col": 1, "before": 1, "after": 1, "outcome": "HELD"},
        {"row": 0, "col": 2, "before": 1, "after": 1, "outcome": "HELD"},
        {"row": 0, "col": 3, "before": 0, "after": 1, "outcome": "CHANGED"},
    ]


def test_geometry_change_has_typed_absence_for_total_site_ledger():
    outcome = _compile(((1,),), ((1, 2),))
    assert outcome["site_transition_coverage"] == "UNDEFINED_ACROSS_GEOMETRY_CHANGE"
    assert outcome["site_transitions"] is None
