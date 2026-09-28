"""G4-A guided lever study: Duck chooses the presses, the controller audits the record.

Author: Claude (Alpha build seat), 2026-09-27.

Director ruling (2026-09-27): G3 stays scripted; G4 becomes stated targets. The controller gives
Duck a direct, explicit target and a closure test, then lets Duck execute it as needed. The
controller never picks Duck's next move. It records every action, applies the counter mask, reads
lever runs out of Duck's own presses, and checks the record against the target.

G4-A target, per lever: press the lever's confirmation click repeatedly until the counter-masked
board stops changing or returns to an earlier state, then confirm that endpoint:

- a masked null is confirmed by one more press that is also null;
- a recurrence of period N is confirmed by N more presses that retrace the recorded states.

A run is a sequence of consecutive presses of the same click. Any other action, a discontinuous
board (for example a system reset), or a boundary ends the run. Evidence is never discarded: ended
runs stay in the lever's history.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from inference.framework.counter_verification import MaskLaw
from inference.framework.g4_orbits import G4OrbitError, LeverOrbit, _address, _grid


RUNNING = "RUNNING"
CONFIRMING = "CONFIRMING"
CONFIRMED = "CONFIRMED"
DIVERGED = "DIVERGED"
INTERRUPTED = "INTERRUPTED"
BROKEN = "BROKEN"

COMPLETE_STATUSES = frozenset({CONFIRMED, DIVERGED})
OPEN_STATUSES = frozenset({RUNNING, CONFIRMING})

_TERMINAL_KEYS = ("done", "level_completed", "game_over", "run_complete")


def is_terminal(boundary_state: Mapping[str, Any] | None) -> bool:
    return bool(boundary_state) and any(bool(boundary_state.get(key)) for key in _TERMINAL_KEYS)


def level_changed(boundary_state: Mapping[str, Any] | None) -> bool:
    state = dict(boundary_state or {})
    before, after = state.get("level_before"), state.get("level_after")
    return bool(state.get("level_completed")) or (
        before is not None and after is not None and before != after
    )


class LeverRun:
    """One run of consecutive same-click presses on one lever, plus its confirmation tail."""

    def __init__(
        self,
        *,
        run_id: str,
        entity_id: str,
        intervention: Mapping[str, Any],
        mask_law: MaskLaw | None,
    ) -> None:
        self.run_id = str(run_id)
        self.entity_id = str(entity_id)
        self.intervention = dict(intervention)
        self.mask_law = mask_law
        self.orbit = LeverOrbit(entity_id=entity_id, intervention=intervention, mask_law=mask_law)
        self.status = RUNNING
        self.end_reason: str | None = None
        self.confirmation: list[dict[str, Any]] = []
        self._expected: tuple[str, ...] = ()
        self._confirm_index = 0
        self._last_after: str | None = None

    @property
    def complete(self) -> bool:
        return self.status in COMPLETE_STATUSES

    @property
    def open(self) -> bool:
        return self.status in OPEN_STATUSES

    def continues_from(self, before: Sequence[Sequence[int]]) -> bool:
        return self._last_after is None or _address(_grid(before), self.mask_law) == self._last_after

    def end(self, reason: str) -> None:
        """Another action, a discontinuity, or a boundary ended an open run."""
        if self.open:
            self.status = BROKEN
            self.end_reason = str(reason)

    def record(
        self,
        *,
        evidence_ref: str,
        transition_id: int,
        before: Sequence[Sequence[int]],
        after: Sequence[Sequence[int]],
        boundary_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record one press of this run's click. The caller guarantees continuity."""
        if not self.open:
            raise G4OrbitError("this lever run is no longer open")
        after_address = _address(_grid(after), self.mask_law)
        if self.status == RUNNING:
            step = self.orbit.record(
                evidence_ref=evidence_ref,
                transition_id=transition_id,
                before=before,
                after=after,
                boundary_state=boundary_state,
            )
            self._last_after = after_address
            if step.disposition == "BOUNDARY_INTERRUPTED":
                self.status = INTERRUPTED
                self.end_reason = "boundary during the run"
            elif step.disposition == "NULL_AT_OBSERVED_STATE":
                self._expected = (after_address,)
                self.status = CONFIRMING
            elif step.disposition == "OBSERVED_STATE_RECURRENCE":
                states = self.orbit.state_sequence
                index = int(step.recurrence_to_state_index or 0)
                period = int(step.observed_period or 0)
                self._expected = tuple(states[index + 1: index + period + 1])
                self.status = CONFIRMING
            return {"phase": "RUN", "disposition": step.disposition, "run_status": self.status}

        expected = self._expected[self._confirm_index]
        before_address = _address(_grid(before), self.mask_law)
        if is_terminal(boundary_state):
            disposition = "BOUNDARY_INTERRUPTED"
            self.status = INTERRUPTED
            self.end_reason = "boundary during confirmation"
        elif after_address == expected:
            self._confirm_index += 1
            if self._confirm_index == len(self._expected):
                disposition = (
                    "ENDPOINT_CONFIRMED"
                    if self.orbit.stop_disposition == "NULL_AT_OBSERVED_STATE"
                    else "RECURRENCE_CONFIRMED"
                )
                self.status = CONFIRMED
            else:
                disposition = "RECURRENCE_STATE_MATCHED"
        else:
            disposition = "CONFIRMATION_DIVERGED"
            self.status = DIVERGED
        self._last_after = after_address
        self.confirmation.append({
            "evidence_ref": str(evidence_ref),
            "transition_id": int(transition_id),
            "before_world_address": before_address,
            "after_world_address": after_address,
            "expected_world_address": expected,
            "disposition": disposition,
        })
        return {"phase": "CONFIRMATION", "disposition": disposition, "run_status": self.status}

    @property
    def confirmation_required(self) -> int:
        return len(self._expected)

    def lever_class(self) -> str:
        """Single-lever class from this run's own record (no cross-lever information)."""
        if self.status == DIVERGED:
            return "DIVERGENT"
        if self.status != CONFIRMED:
            return "UNCLASSIFIED"
        if self.orbit.stop_disposition == "NULL_AT_OBSERVED_STATE":
            return "ABSORBING"
        period = self.orbit.steps[-1].observed_period if self.orbit.steps else None
        if period == 2:
            return "TOGGLE"
        if isinstance(period, int) and period > 2:
            return "CYCLE"
        return "RECURRENT"

    def snapshot(self, *, include_cells: bool = True) -> dict[str, Any]:
        return {
            "schema": "virelai-g4a-lever-run-v1",
            "run_id": self.run_id,
            "entity_id": self.entity_id,
            "intervention": dict(self.intervention),
            "status": self.status,
            "end_reason": self.end_reason,
            "orbit": self.orbit.snapshot(include_cells=include_cells),
            "confirmation_required": self.confirmation_required,
            "confirmation": [dict(item) for item in self.confirmation],
            "lever_class": self.lever_class(),
        }


__all__ = [
    "BROKEN",
    "COMPLETE_STATUSES",
    "CONFIRMED",
    "CONFIRMING",
    "DIVERGED",
    "INTERRUPTED",
    "LeverRun",
    "RUNNING",
    "is_terminal",
    "level_changed",
]
