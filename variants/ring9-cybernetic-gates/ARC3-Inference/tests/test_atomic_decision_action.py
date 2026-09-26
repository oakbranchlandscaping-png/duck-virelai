import pytest

from inference.framework.virelai_controller import (
    ControllerActionBridge,
    decision_envelope_from_dict,
    validate_decision_envelope,
)


def _envelope(*, purpose="TEST_RULE", focus="F-1", actions=("LEFT",), prediction=True, **extra):
    decision = {"focus_id": focus, "purpose": purpose, **extra}
    if prediction:
        decision["prediction"] = {
            "claim_id": "RV-1",
            "expected": "CHANGED",
            "scope": {"representation": "WORLDLINE", "identifier": "O-1"},
        }
    return decision_envelope_from_dict(decision, actions=actions, declared_at_transition=4)


def test_rejected_envelope_never_calls_environment():
    calls = []
    bridge = ControllerActionBridge(active_focus_id="F-1", legal_actions=("LEFT",), executor=lambda actions: calls.append(actions))
    receipt = bridge.execute(_envelope(focus="F-stale"))
    assert not receipt.accepted
    assert calls == []


@pytest.mark.parametrize("purpose", ["EXPLORE", "NAVIGATE"])
def test_non_predictive_purposes_may_execute_without_prediction(purpose):
    calls = []
    bridge = ControllerActionBridge(active_focus_id="F-1", legal_actions=("LEFT",), executor=lambda actions: calls.append(actions) or {"ok": True})
    receipt = bridge.execute(_envelope(purpose=purpose, prediction=False))
    assert receipt.accepted and len(calls) == 1
    assert receipt.executed_actions == _envelope(purpose=purpose, prediction=False).actions


def test_tests_require_one_action_prediction_and_scope():
    with pytest.raises(ValueError, match="exactly one"):
        validate_decision_envelope(_envelope(actions=("LEFT", "LEFT")), active_focus_id="F-1", legal_actions=("LEFT",))
    with pytest.raises(ValueError, match="prospective prediction"):
        validate_decision_envelope(_envelope(prediction=False), active_focus_id="F-1", legal_actions=("LEFT",))


def test_illegal_action_never_calls_environment():
    calls = []
    bridge = ControllerActionBridge(active_focus_id="F-1", legal_actions=("RIGHT",), executor=lambda actions: calls.append(actions))
    receipt = bridge.execute(_envelope(actions=("LEFT",)))
    assert not receipt.accepted and not calls


def test_pursue_win_requires_reference():
    with pytest.raises(ValueError, match="requires a prior win"):
        validate_decision_envelope(_envelope(purpose="PURSUE_WIN", prediction=False), active_focus_id="F-1", legal_actions=("LEFT",))


def test_pointer_action_and_focus_proposal_parse_canonically():
    envelope = _envelope(
        purpose="EXPLORE",
        prediction=False,
        actions=({"action": "MOUSE", "row": 3, "col": 9},),
        proposed_focus={"question": "Does B reverse A?", "reason": "separates two rules", "evidence_transition_ids": [7, 3, 7]},
    )
    validate_decision_envelope(envelope, active_focus_id="F-1", legal_actions=("MOUSE",))
    assert envelope.actions[0].parameters == (("col", 9), ("row", 3))
    assert envelope.proposed_focus.evidence_transition_ids == (3, 7)


def test_accepted_decision_is_idempotent_on_retry():
    calls = []
    bridge = ControllerActionBridge(active_focus_id="F-1", legal_actions=("LEFT",), executor=lambda actions: calls.append(actions) or {"ok": True})
    envelope = _envelope()
    assert bridge.execute(envelope).accepted
    assert bridge.execute(envelope).accepted
    assert len(calls) == 1
