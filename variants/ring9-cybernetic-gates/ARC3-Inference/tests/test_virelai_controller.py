from dataclasses import replace

import pytest

from inference.framework.virelai_controller import (
    build_controller_snapshot,
    canonical_controller_bytes,
    compile_rule_versions,
    phase_contracts,
    validate_controller_snapshot,
)
from inference.framework.virelai_world_model import (
    Claim,
    EvidenceRef,
    MechanicRule,
    WinRecord,
    empty_world_model,
)


def _model():
    return empty_world_model(
        game_id="fixture",
        observed_through_step=8,
        levels_observed=(1,),
        current_level=1,
        source_schema="fixture",
    )


def _observed_rule(**changes):
    base = MechanicRule(
        rule_id="M-1",
        trigger_action="ACTION3",
        trigger_object_type="T-lever",
        affected_ids=("O-target",),
        transformation="CLASS_REWRITE",
        levels_observed=(1,),
        claim_id="C-1",
        subject_ids=("O-lever",),
        condition="WHEN_CLICKED",
        witness_transition_ids=(3, 7),
        scope="L1",
        status="OBSERVED",
        parameters=("observed_state_transition=blue->red",),
    )
    return replace(base, **changes)


def _claim():
    return Claim(
        claim_id="C-1",
        predicate="lever rewrite observed",
        status="OBSERVED",
        scope="L1",
        witness_count=2,
        evidence=(
            EvidenceRef(3, 1, 3, "blue became red", action_id=3),
            EvidenceRef(7, 1, 7, "blue became red", action_id=3),
        ),
    )


def test_phase_contracts_have_operational_obligations():
    rows = phase_contracts()
    assert {item.phase for item in rows} >= {"CONTROL", "PHYSICS_GRAMMAR", "TRANSFER"}
    assert all(item.obligations and item.opening_rule and item.advance_rule for item in rows)
    assert all(item.defer_rule and item.reopen_rule for item in rows)


def test_first_predictive_family_is_discrete_state_transition():
    model = replace(_model(), mechanics=(_observed_rule(),), claims=(_claim(),))
    rule = compile_rule_versions(model)[0]
    assert rule.family == "DISCRETE_STATE_TRANSITION"
    assert (rule.predicted_from, rule.predicted_to) == ("blue", "red")
    assert rule.condition == "WHEN_CLICKED"
    assert rule.witness_transition_ids == (3, 7)


def test_non_discrete_rule_preserves_missing_distinction():
    model = replace(
        _model(),
        mechanics=(_observed_rule(parameters=()),),
        claims=(_claim(),),
    )
    rule = compile_rule_versions(model)[0]
    assert rule.family == "VISIBLE_TRANSFORMATION"
    assert rule.distinction_needed == "exact discrete before/after state"


def test_snapshot_is_byte_deterministic_and_bounded():
    model = replace(_model(), mechanics=(_observed_rule(),), claims=(_claim(),))
    left = build_controller_snapshot(model)
    right = build_controller_snapshot(model)
    assert canonical_controller_bytes(left) == canonical_controller_bytes(right)
    assert left.focus.phase == "PHYSICS_GRAMMAR"
    assert len(left.focus.alternatives) <= 2
    assert left.focus.evidence_transition_ids == (3, 7)


def test_transfer_outranks_ordinary_current_level_focus():
    model = replace(
        _model(),
        current_level=2,
        levels_observed=(1, 2),
        observed_through_step=20,
        wins=(WinRecord(
            win_id="W-1",
            completed_level=1,
            transition_id=10,
            winning_action="ACTION3",
            acted_object_id=None,
            participating_ids=(),
            preconditions_observed=(),
            separator_predicates=(),
            earlier_same_action_failures=2,
            causal_status="UNKNOWN",
        ),),
        claims=(Claim(
            claim_id="C-win",
            predicate="level ended",
            status="OBSERVED",
            scope="L1",
            witness_count=1,
            evidence=(EvidenceRef(10, 1, 10, "level ended", action_id=3),),
        ),),
    )
    snapshot = build_controller_snapshot(model)
    assert snapshot.focus.phase == "TRANSFER"
    assert snapshot.focus.evidence_transition_ids == (10,)


def test_validation_rejects_unknown_evidence_reference():
    model = replace(_model(), mechanics=(_observed_rule(),), claims=(_claim(),))
    snapshot = build_controller_snapshot(model)
    broken_focus = replace(snapshot.focus, evidence_transition_ids=(99,))
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_controller_snapshot(replace(snapshot, focus=broken_focus), model)
