from __future__ import annotations

import pytest

from inference.framework.lever_attribution import (
    COUNTER_ONLY_DISPOSITION,
    LeverAttributionError,
    LeverEvidenceAccumulator,
    attribute_lever_outcome,
)


def outcome(*changes, acted_site=None, boundary=None, transition_id=1):
    return {
        "transition_id": transition_id,
        "acted_site": acted_site,
        "changed_cells": [
            {"row": row, "col": col, "before": before, "after": after}
            for row, col, before, after in changes
        ],
        "boundary_event": boundary or {"state": "PLAYING"},
    }


def test_pointer_owner_attributes_local_and_remote_residue_after_subtraction():
    result = attribute_lever_outcome(
        outcome(
            (1, 1, 2, 4),       # target-local response
            (4, 4, 7, 8),       # remote response
            (0, 0, 11, 3),      # counter tick
            (2, 2, 9, 3),       # ego motion
            (3, 3, 5, 9),       # ordinary ground exchange
            acted_site={"row": 1, "col": 1},
        ),
        evidence_ref="E-pointer",
        channel="POINTER",
        target_member_id="M1",
        target_cells=[(1, 1)],
        counter_mask_cells=[(0, 0)],
        ego_motion_cells=[(2, 2)],
        ground_exchange_cells=[(3, 3)],
        pre_action_owner_member_id="M1",
    )
    assert result.disposition == "LOCAL_AND_REMOTE_LEVER_WITNESS"
    assert result.counter_masked_cells == ((0, 0),)
    assert result.ego_motion_cells == ((2, 2),)
    assert result.ground_exchange_cells == ((3, 3),)
    assert result.local_residue_cells == ((1, 1),)
    assert result.remote_residue_cells == ((4, 4),)
    assert result.positive


def test_pointer_requires_pre_action_owner_even_when_remote_delta_exists():
    result = attribute_lever_outcome(
        outcome((4, 4, 7, 8), acted_site={"row": 1, "col": 1}),
        evidence_ref="E-wrong-owner",
        channel="POINTER",
        target_member_id="M1",
        target_cells=[(1, 1)],
        counter_mask_cells=[],
        ego_motion_cells=[],
        pre_action_owner_member_id="M2",
    )
    assert result.disposition == "UNRESOLVED_ATTRIBUTION"
    assert result.remote_residue_cells == ((4, 4),)
    assert not result.positive


def test_body_contact_line_attributes_remote_witness():
    result = attribute_lever_outcome(
        outcome((2, 2, 6, 3), (5, 5, 1, 9)),
        evidence_ref="E-body",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[(2, 2)],
        body_contact_cells=[(2, 2)],
    )
    # The target-owned contact cell is retained as local evidence even though
    # the ego enters it; the third-worldline change remains remote.
    assert result.disposition == "LOCAL_AND_REMOTE_LEVER_WITNESS"
    assert result.attribution_basis == "BODY_CONTACT_LINE"
    assert result.local_residue_cells == ((2, 2),)
    assert result.remote_residue_cells == ((5, 5),)


def test_visible_delta_without_body_contact_is_unresolved_not_remote_effect_absence():
    result = attribute_lever_outcome(
        outcome((5, 5, 1, 9)),
        evidence_ref="E-no-contact",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[],
    )
    assert result.disposition == "UNRESOLVED_ATTRIBUTION"
    assert result.remote_residue_cells == ((5, 5),)
    assert not result.inertness_claim_permitted


def test_refused_contact_with_only_counter_tick_is_scoped_null_not_inert():
    result = attribute_lever_outcome(
        outcome((0, 0, 11, 3)),
        evidence_ref="E-null",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[(0, 0)],
        ego_motion_cells=[],
        refused_contact=True,
    )
    assert result.contact_attributed
    assert result.disposition == "SCOPED_NULL_RESPONSE"
    assert result.residue_cells == ()
    assert not result.inertness_claim_permitted


def test_ego_only_residue_is_ambiguous_when_remote_drive_cannot_be_excluded():
    result = attribute_lever_outcome(
        outcome((2, 2, 6, 3)),
        evidence_ref="E-ego-confounded",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[],
        ego_confounded_cells=[(2, 2)],
        body_contact_cells=[(2, 2)],
    )
    assert result.disposition == "AMBIGUOUS_EGO_MASKED"
    assert result.ego_confounded_cells == ((2, 2),)
    assert not result.positive


def test_boundary_transition_is_deferred_to_g4_even_with_residue():
    result = attribute_lever_outcome(
        outcome(
            (2, 2, 6, 3),
            (5, 5, 1, 9),
            boundary={"state": "GAME_OVER", "game_over": True},
        ),
        evidence_ref="E-boundary",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[],
        body_contact_cells=[(2, 2)],
    )
    assert result.disposition == "BOUNDARY_EVENT_DEFERRED"
    assert result.boundary_state == "GAME_OVER"
    assert not result.positive


def test_positive_witness_is_permanent_when_later_contact_is_silent():
    accumulator = LeverEvidenceAccumulator()
    positive = attribute_lever_outcome(
        outcome((5, 5, 1, 9)),
        evidence_ref="E-positive",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[],
        body_contact_cells=[(2, 2)],
    )
    first = accumulator.record(positive)
    assert first.status == "LEVER_REMOTE"

    silent = attribute_lever_outcome(
        outcome(transition_id=2),
        evidence_ref="E-silent",
        channel="BODY",
        target_member_id="M6",
        target_cells=[(2, 2)],
        counter_mask_cells=[],
        ego_motion_cells=[],
        refused_contact=True,
    )
    second = accumulator.record(silent)
    assert second.status == "LEVER_REMOTE"
    assert [item.evidence_ref for item in second.remote_witnesses] == ["E-positive"]
    assert second.null_evidence_refs == ("E-silent",)
    assert not second.inertness_claim_permitted


def test_previews_are_rejected_because_attribution_requires_lossless_cells():
    with pytest.raises(LeverAttributionError, match="lossless changed_cells"):
        attribute_lever_outcome(
            {"transition_id": 1, "changed_cells_preview": []},
            evidence_ref="E-preview",
            channel="BODY",
            target_member_id="M6",
            target_cells=[(2, 2)],
            counter_mask_cells=[],
            ego_motion_cells=[],
        )


def test_counter_only_target_is_audited_without_becoming_unresolved_or_a_lever():
    result = attribute_lever_outcome(
        outcome((0, 0, 11, 3), acted_site={"row": 0, "col": 0}),
        evidence_ref="E-counter-only",
        channel="POINTER",
        target_member_id="M-counter",
        target_cells=[(0, 0)],
        counter_mask_cells=[(0, 0)],
        ego_motion_cells=[],
        pre_action_owner_member_id=None,
        target_is_counter=True,
    )
    record = LeverEvidenceAccumulator().record(result)

    assert result.disposition == COUNTER_ONLY_DISPOSITION
    assert result.residue_cells == ()
    assert not result.positive
    assert record.counter_only_evidence_refs == ("E-counter-only",)
    assert record.unresolved_evidence_refs == ()


def test_unresolved_pointer_owner_with_only_known_counter_delta_is_scoped_no_lever():
    result = attribute_lever_outcome(
        outcome((0, 0, 11, 3), acted_site={"row": 9, "col": 9}),
        evidence_ref="E-target-counter-only",
        channel="POINTER",
        target_member_id="M-target",
        target_cells=[(2, 2)],
        counter_mask_cells=[(0, 0)],
        ego_motion_cells=[],
        pre_action_owner_member_id=None,
        target_is_counter=False,
    )
    record = LeverEvidenceAccumulator().record(result)

    assert not result.contact_attributed
    assert result.disposition == COUNTER_ONLY_DISPOSITION
    assert result.residue_cells == ()
    assert not result.inertness_claim_permitted
    assert record.counter_only_evidence_refs == ("E-target-counter-only",)
    assert record.unresolved_evidence_refs == ()
