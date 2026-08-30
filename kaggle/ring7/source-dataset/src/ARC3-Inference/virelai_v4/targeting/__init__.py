"""virelai_v4/targeting/__init__.py — Targeting package public API."""

from .assessor import assess_target_state, TargetState, TierAssessment, TierStatus
from .router import route

__all__ = [
    "assess_target_state", "TargetState", "TierAssessment", "TierStatus",
    "route",
]
