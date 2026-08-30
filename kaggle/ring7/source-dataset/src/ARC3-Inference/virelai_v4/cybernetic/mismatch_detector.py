"""
cybernetic/mismatch_detector.py — WO-CYBERNETIC-01

Stateful detector: consumes ActionMatchResult entries one at a time,
maintains a sliding window, and emits a MismatchReport with flags.

Flags:
  PREDICTION_FAILURE — N consecutive low-match actions
  MODEL_STALE        — running average drops below threshold
  LEVER_DEAD         — zero observed delta with positive prediction

Imports: collections.deque, dataclasses, typing, sibling ActionMatchResult.
No imports from execution/, discovery/, observer/, spine/, crucible/.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from virelai_v4.cybernetic.execution_monitor import ActionMatchResult


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MismatchReport:
    """Snapshot of detector state after processing one action."""
    flags: FrozenSet[str]
    running_match_avg: Optional[float]   # None if no predictions in window
    worst_lever: Optional[str]           # lever_id with lowest avg match_ratio
    total_actions_monitored: int


# ── Detector ──────────────────────────────────────────────────────────────────

class MismatchDetector:
    """Sliding-window mismatch detector for execution feedback loop.

    Instantiated fresh for each execution run.  Cross-life persistence
    is through the MismatchReport stored on state, not this object.
    """

    def __init__(
        self,
        failure_window: int = 3,
        failure_threshold: float = 0.5,
        stale_window: int = 5,
        stale_threshold: float = 0.6,
    ) -> None:
        self._failure_window = failure_window
        self._failure_threshold = failure_threshold
        self._stale_window = stale_window
        self._stale_threshold = stale_threshold

        self._recent: deque[ActionMatchResult] = deque(
            maxlen=stale_window,
        )
        self._lever_ratios: Dict[str, List[float]] = {}
        self._total: int = 0

    # ── Public API ────────────────────────────────────────────────────────

    def update(self, result: ActionMatchResult) -> MismatchReport:
        """Ingest one ActionMatchResult and return updated report."""
        self._recent.append(result)
        self._total += 1

        if result.match_ratio is not None:
            self._lever_ratios.setdefault(result.lever_id, []).append(
                result.match_ratio,
            )

        flags: set[str] = set()

        if self._check_prediction_failure():
            flags.add("PREDICTION_FAILURE")
        if self._check_model_stale():
            flags.add("MODEL_STALE")
        if self._check_lever_dead(result):
            flags.add("LEVER_DEAD")

        return MismatchReport(
            flags=frozenset(flags),
            running_match_avg=self._running_match_avg(),
            worst_lever=self._worst_lever(),
            total_actions_monitored=self._total,
        )

    # ── Flag Logic (private) ──────────────────────────────────────────────

    def _check_prediction_failure(self) -> bool:
        """Last failure_window entries all have verdict CONTRADICTED."""
        recent = list(self._recent)
        tail = recent[-self._failure_window:]
        if len(tail) < self._failure_window:
            return False
        return all(r.verdict == "CONTRADICTED" for r in tail)

    def _check_model_stale(self) -> bool:
        """More than 60% of recent verdicts (excluding None) are CONTRADICTED."""
        verdicts = [r.verdict for r in self._recent if r.verdict is not None]
        if not verdicts:
            return False
        contradicted = sum(1 for v in verdicts if v == "CONTRADICTED")
        return contradicted / len(verdicts) > 0.6

    @staticmethod
    def _check_lever_dead(result: ActionMatchResult) -> bool:
        """Zero observed delta when positive delta was predicted."""
        return (
            result.observed_delta_px == 0
            and result.predicted_delta_px is not None
            and result.predicted_delta_px > 0
        )

    # ── Helpers (private) ─────────────────────────────────────────────────

    def _running_match_avg(self) -> Optional[float]:
        """Mean match_ratio over window, excluding None entries."""
        ratios = [
            r.match_ratio for r in self._recent
            if r.match_ratio is not None
        ]
        if not ratios:
            return None
        return sum(ratios) / len(ratios)

    def _worst_lever(self) -> Optional[str]:
        """Lever with the lowest lifetime average match_ratio."""
        if not self._lever_ratios:
            return None
        return min(
            self._lever_ratios,
            key=lambda lid: (
                sum(self._lever_ratios[lid]) / len(self._lever_ratios[lid])
            ),
        )
