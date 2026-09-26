from inference.framework.counter_verification import MaskLaw
from inference.framework.masked_world_state import (
    MaskedStateArchive,
    partition_delta,
    raw_address,
    world_address,
)


LAW = MaskLaw(
    law_id="MASK-test",
    law_version_id="MASK-V1-test",
    revision=1,
    status="OBSERVED",
    cells=((0, 0), (0, 1), (0, 2)),
    rewrite="7->4",
    witness_evidence_refs=("E-1", "E-2"),
    demonstration_ref="E-3",
)


def test_counter_only_frames_have_distinct_raw_but_equal_world_addresses():
    left = ((7, 7, 4), (0, 2, 0))
    right = ((7, 4, 4), (0, 2, 0))
    assert raw_address(left) != raw_address(right)
    assert world_address(left, LAW) == world_address(right, LAW)
    delta = partition_delta(left, right, LAW)
    assert delta.raw_cells == frozenset({(0, 1)})
    assert delta.hud_cells == delta.raw_cells
    assert delta.world_cells == frozenset()
    assert delta.is_hud_only is True


def test_real_world_change_survives_counter_mask():
    left = ((7, 7, 4), (0, 2, 0))
    right = ((7, 4, 4), (0, 3, 0))
    delta = partition_delta(left, right, LAW)
    assert delta.hud_cells == frozenset({(0, 1)})
    assert delta.world_cells == frozenset({(1, 1)})
    assert delta.world_changed is True
    assert world_address(left, LAW) != world_address(right, LAW)


def test_archive_preserves_raw_states_and_retroactively_collapses_counter_ticks():
    archive = MaskedStateArchive(LAW)
    first = ((7, 7, 4), (0, 2, 0))
    second = ((7, 4, 4), (0, 2, 0))
    third = ((4, 4, 4), (0, 3, 0))
    archive.record_transition(evidence_ref="E-2", before=first, after=second)
    archive.record_transition(evidence_ref="E-3", before=second, after=third)
    snapshot = archive.snapshot()
    assert snapshot["raw_state_count"] == 3
    assert snapshot["world_state_count"] == 2
    assert snapshot["world_revisit_count"] == 1
    assert snapshot["hud_only_transition_count"] == 1
    assert snapshot["world_change_transition_count"] == 1
    assert archive.states[0].raw_grid == first
