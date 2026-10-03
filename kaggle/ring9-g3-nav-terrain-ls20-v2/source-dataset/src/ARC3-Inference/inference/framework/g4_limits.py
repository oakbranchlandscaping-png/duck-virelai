"""G4.3 evidence records for observed limits, persistence, and reversal.

G4.2 supplies a finite, counter-masked orbit.  This module tests the narrow
claims that can follow from an observed masked null: the endpoint repeats,
the endpoint survives a control intervention when one is available, and an
already-confirmed lever may restore an earlier orbit state.  Reversal is not
accepted until the original lever becomes effective again.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from inference.framework.counter_verification import MaskLaw
from inference.framework.masked_world_state import partition_delta, raw_address, world_address


Grid = tuple[tuple[int, ...], ...]
CellChange = tuple[int, int, int, int]


class G4LimitError(ValueError):
    """A G4.3 observation or explanation violates its evidence."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _grid(value: Sequence[Sequence[int]]) -> Grid:
    return tuple(tuple(int(cell) for cell in row) for row in value)


def _address(grid: Grid, law: MaskLaw | None) -> str:
    return raw_address(grid) if law is None else world_address(grid, law)


@dataclass(frozen=True)
class LimitProbeSpec:
    operation_kind: str
    intervention: Mapping[str, Any]
    candidate_entity_id: str | None = None


@dataclass(frozen=True)
class LimitObservation:
    operation_kind: str
    evidence_ref: str
    transition_id: int
    intervention: Mapping[str, Any]
    candidate_entity_id: str | None
    before_world_address: str
    after_world_address: str
    disposition: str
    changed_cell_count: int
    changed_cells: tuple[CellChange, ...]
    restored_orbit_state_index: int | None = None
    boundary_state: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LeverLimitAnswer:
    answer_id: str
    answer_kind: str
    entity_id: str
    endpoint_disposition: str
    persistence_disposition: str
    reversal_disposition: str
    inverse_entity_id: str | None
    restored_orbit_state_index: int | None
    original_reenabled: bool | None
    mechanism_explanation: str
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]


class LeverLimitStudy:
    """A bounded G4.3 experiment for one completed CLICK-lever orbit."""

    def __init__(
        self,
        *,
        entity_id: str,
        intervention: Mapping[str, Any],
        orbit_state_sequence: Sequence[str],
        orbit_stop_disposition: str,
        mask_law: MaskLaw | None,
        recurrence_to_state_index: int | None = None,
        observed_period: int | None = None,
        control_intervention: Mapping[str, Any] | None = None,
        inverse_candidates: Sequence[tuple[str, Mapping[str, Any]]] = (),
    ) -> None:
        states = tuple(str(item) for item in orbit_state_sequence)
        if len(states) < 2:
            raise G4LimitError("G4.3 requires a completed G4.2 state sequence")
        if orbit_stop_disposition not in {
            "NULL_AT_OBSERVED_STATE", "OBSERVED_STATE_RECURRENCE"
        }:
            raise G4LimitError("G4.3 requires an observed masked null or exact recurrence")
        self.entity_id = str(entity_id)
        self.intervention = dict(intervention)
        self.orbit_state_sequence = states
        self.orbit_stop_disposition = str(orbit_stop_disposition)
        self.recurrence_to_state_index = recurrence_to_state_index
        self.observed_period = observed_period
        self.mask_law = mask_law
        self.control_intervention = (
            None if control_intervention is None else dict(control_intervention)
        )
        self.inverse_candidates = tuple(
            (str(candidate), dict(candidate_intervention))
            for candidate, candidate_intervention in inverse_candidates
            if str(candidate) != self.entity_id
        )
        recurrence_branch = self.orbit_stop_disposition == "OBSERVED_STATE_RECURRENCE"
        if recurrence_branch:
            if recurrence_to_state_index is None or observed_period is None:
                raise G4LimitError("recurrence confirmation requires its observed index and period")
            recurrence_index = int(recurrence_to_state_index)
            period = int(observed_period)
            if recurrence_index < 0 or period < 1:
                raise G4LimitError("recurrence index and period must describe a positive cycle")
            expected = states[recurrence_index + 1 : recurrence_index + period + 1]
            if len(expected) != period or states[-1] != states[recurrence_index]:
                raise G4LimitError("recurrence metadata does not match the G4.2 state sequence")
            self._recurrence_expected_addresses = expected
        else:
            self._recurrence_expected_addresses = ()
        self._recurrence_confirmation_index = 0
        self.observations: list[LimitObservation] = []
        self.endpoint_disposition = "UNTESTED"
        self.persistence_disposition = (
            "NOT_APPLICABLE_TO_RECURRENCE_CONFIRMATION"
            if recurrence_branch
            else "UNTESTED" if self.control_intervention is not None else "NO_CONTROL_AVAILABLE"
        )
        self.reversal_disposition = (
            "NOT_APPLICABLE_TO_RECURRENCE_CONFIRMATION"
            if recurrence_branch
            else "UNTESTED" if self.inverse_candidates else "NO_CANDIDATE_AVAILABLE"
        )
        self.inverse_entity_id: str | None = None
        self.restored_orbit_state_index: int | None = None
        self.original_reenabled: bool | None = None
        self._candidate_index = 0
        self._phase = "RECONFIRM_RECURRENCE" if recurrence_branch else "CONFIRM_ENDPOINT"
        self._current_address = states[-1]

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def ready_for_answer(self) -> bool:
        return self._phase == "ANSWER_REQUIRED"

    @property
    def interrupted(self) -> bool:
        return self._phase == "BOUNDARY_INTERRUPTED"

    def next_probe(self) -> LimitProbeSpec | None:
        if self._phase == "RECONFIRM_RECURRENCE":
            return LimitProbeSpec("RECONFIRM_RECURRENCE", dict(self.intervention))
        if self._phase == "CONFIRM_ENDPOINT":
            return LimitProbeSpec("CONFIRM_ENDPOINT", dict(self.intervention))
        if self._phase == "TEST_PERSISTENCE":
            assert self.control_intervention is not None
            return LimitProbeSpec("TEST_PERSISTENCE", dict(self.control_intervention))
        if self._phase == "TEST_INVERSE":
            if self._candidate_index >= len(self.inverse_candidates):
                self.reversal_disposition = "NO_INVERSE_OBSERVED"
                self._phase = "ANSWER_REQUIRED"
                return None
            candidate, intervention = self.inverse_candidates[self._candidate_index]
            return LimitProbeSpec("TEST_INVERSE", dict(intervention), candidate)
        if self._phase == "REAPPLY_ORIGINAL":
            return LimitProbeSpec(
                "REAPPLY_ORIGINAL", dict(self.intervention), self.inverse_entity_id
            )
        return None

    def _changed_cells(self, left: Grid, right: Grid) -> tuple[CellChange, ...]:
        if self.mask_law is None:
            return tuple(
                (row, col, value, right[row][col])
                for row, values in enumerate(left)
                for col, value in enumerate(values)
                if value != right[row][col]
            )
        delta = partition_delta(left, right, self.mask_law)
        return tuple(
            (row, col, left[row][col], right[row][col])
            for row, col in sorted(delta.world_cells)
        )

    def record(
        self,
        *,
        evidence_ref: str,
        transition_id: int,
        before: Sequence[Sequence[int]],
        after: Sequence[Sequence[int]],
        boundary_state: Mapping[str, Any] | None = None,
    ) -> LimitObservation:
        spec = self.next_probe()
        if spec is None:
            raise G4LimitError("G4.3 has no active probe")
        left, right = _grid(before), _grid(after)
        before_address = _address(left, self.mask_law)
        after_address = _address(right, self.mask_law)
        if before_address != self._current_address:
            raise G4LimitError(
                "the G4.3 chain is discontinuous from the last counter-masked state"
            )
        changed = self._changed_cells(left, right)
        terminal = bool(boundary_state) and any(
            bool(boundary_state.get(key))
            for key in ("done", "level_completed", "game_over", "run_complete")
        )
        restored_index: int | None = None
        if terminal:
            disposition = "BOUNDARY_INTERRUPTED"
            self._phase = "BOUNDARY_INTERRUPTED"
        elif spec.operation_kind == "RECONFIRM_RECURRENCE":
            expected_address = self._recurrence_expected_addresses[
                self._recurrence_confirmation_index
            ]
            if after_address == expected_address:
                self._recurrence_confirmation_index += 1
                if self._recurrence_confirmation_index == len(
                    self._recurrence_expected_addresses
                ):
                    disposition = "EXACT_RECURRENCE_RECONFIRMED"
                    self.endpoint_disposition = disposition
                    self._phase = "ANSWER_REQUIRED"
                else:
                    disposition = "RECURRENCE_STATE_MATCHED"
            else:
                disposition = "RECURRENCE_DIVERGED"
                self.endpoint_disposition = disposition
                self._phase = "ANSWER_REQUIRED"
        elif spec.operation_kind == "CONFIRM_ENDPOINT":
            if after_address == before_address:
                disposition = "ENDPOINT_CONFIRMED"
                self.endpoint_disposition = "SATURATED_AT_OBSERVED_STATE"
                self._phase = (
                    "TEST_PERSISTENCE"
                    if self.control_intervention is not None
                    else "TEST_INVERSE" if self.inverse_candidates else "ANSWER_REQUIRED"
                )
            else:
                disposition = "ENDPOINT_NOT_REPRODUCED"
                self.endpoint_disposition = disposition
                self._phase = "ANSWER_REQUIRED"
        elif spec.operation_kind == "TEST_PERSISTENCE":
            if after_address == before_address:
                disposition = "PERSISTED_THROUGH_CONTROL"
                self.persistence_disposition = disposition
                self._phase = "TEST_INVERSE" if self.inverse_candidates else "ANSWER_REQUIRED"
            else:
                disposition = "CONTROL_CHANGED_STATE"
                self.persistence_disposition = disposition
                self._phase = "ANSWER_REQUIRED"
        elif spec.operation_kind == "TEST_INVERSE":
            if after_address == before_address:
                disposition = "CANDIDATE_NULL"
                self._candidate_index += 1
                if self._candidate_index >= len(self.inverse_candidates):
                    self.reversal_disposition = "NO_INVERSE_OBSERVED"
                    self._phase = "ANSWER_REQUIRED"
            elif after_address in self.orbit_state_sequence[:-1]:
                restored_index = self.orbit_state_sequence.index(after_address)
                disposition = "EXACT_ORBIT_STATE_RESTORED"
                self.reversal_disposition = "REVERSAL_CANDIDATE"
                self.inverse_entity_id = spec.candidate_entity_id
                self.restored_orbit_state_index = restored_index
                self._phase = "REAPPLY_ORIGINAL"
            else:
                disposition = "STATE_RELEASED_WITHOUT_EXACT_RESTORATION"
                self.reversal_disposition = disposition
                self.inverse_entity_id = spec.candidate_entity_id
                self._phase = "REAPPLY_ORIGINAL"
        else:
            if after_address != before_address:
                disposition = "ORIGINAL_REENABLED"
                self.original_reenabled = True
                if self.reversal_disposition == "REVERSAL_CANDIDATE":
                    self.reversal_disposition = "EXACT_REVERSAL_DEMONSTRATED"
            else:
                disposition = "ORIGINAL_STILL_NULL"
                self.original_reenabled = False
                if self.reversal_disposition == "REVERSAL_CANDIDATE":
                    self.reversal_disposition = "RESTORATION_WITHOUT_REENABLEMENT"
            self._phase = "ANSWER_REQUIRED"

        observation = LimitObservation(
            operation_kind=spec.operation_kind,
            evidence_ref=str(evidence_ref),
            transition_id=int(transition_id),
            intervention=dict(spec.intervention),
            candidate_entity_id=spec.candidate_entity_id,
            before_world_address=before_address,
            after_world_address=after_address,
            disposition=disposition,
            changed_cell_count=len(changed),
            changed_cells=changed,
            restored_orbit_state_index=restored_index,
            boundary_state=None if not boundary_state else dict(boundary_state),
        )
        self.observations.append(observation)
        self._current_address = after_address
        return observation

    def snapshot(self, *, include_cells: bool = True) -> dict[str, Any]:
        observations = [asdict(item) for item in self.observations]
        if not include_cells:
            for item in observations:
                item.pop("changed_cells", None)
        return {
            "schema": "virelai-g4-lever-limit-study-v1",
            "entity_id": self.entity_id,
            "intervention": dict(self.intervention),
            "orbit_stop_disposition": self.orbit_stop_disposition,
            "orbit_state_sequence": list(self.orbit_state_sequence),
            "recurrence_to_state_index": self.recurrence_to_state_index,
            "observed_period": self.observed_period,
            "recurrence_confirmation_progress": self._recurrence_confirmation_index,
            "recurrence_expected_addresses": list(self._recurrence_expected_addresses),
            "phase": self.phase,
            "endpoint_disposition": self.endpoint_disposition,
            "persistence_disposition": self.persistence_disposition,
            "reversal_disposition": self.reversal_disposition,
            "inverse_entity_id": self.inverse_entity_id,
            "restored_orbit_state_index": self.restored_orbit_state_index,
            "original_reenabled": self.original_reenabled,
            "observations": observations,
        }


def validate_limit_answer(
    raw: Mapping[str, Any], study: LeverLimitStudy
) -> LeverLimitAnswer:
    if not study.ready_for_answer:
        raise G4LimitError("a G4.3 answer is premature while the study remains active")
    if str(raw.get("answer_kind") or "").strip().upper() != "LEVER_LIMIT_OBSERVATION":
        raise G4LimitError("answer_kind must be LEVER_LIMIT_OBSERVATION")
    if str(raw.get("entity_id") or "").strip() != study.entity_id:
        raise G4LimitError("entity_id must match the active G4.3 lever")
    exact = {
        "endpoint_disposition": study.endpoint_disposition,
        "persistence_disposition": study.persistence_disposition,
        "reversal_disposition": study.reversal_disposition,
        "inverse_entity_id": study.inverse_entity_id,
        "restored_orbit_state_index": study.restored_orbit_state_index,
        "original_reenabled": study.original_reenabled,
    }
    for key, value in exact.items():
        if raw.get(key) != value:
            raise G4LimitError(f"{key} must exactly match the observed G4.3 record")
    refs = tuple(str(item) for item in raw.get("evidence_refs") or ())
    required_refs = tuple(item.evidence_ref for item in study.observations)
    if refs != required_refs:
        raise G4LimitError("evidence_refs must preserve every G4.3 observation in order")
    explanation = str(raw.get("mechanism_explanation") or "").strip()
    if len(explanation.split()) < 10:
        raise G4LimitError("mechanism_explanation must describe the observed scoped limit")
    competing = tuple(
        str(item).strip() for item in raw.get("competing_models") or () if str(item).strip()
    )
    if not competing:
        raise G4LimitError("at least one competing model is required")
    falsifier = str(raw.get("falsifier") or "").strip()
    if len(falsifier.split()) < 5:
        raise G4LimitError("falsifier must name a concrete later contradiction")
    limitations = tuple(
        str(item).strip() for item in raw.get("limitations") or () if str(item).strip()
    )
    seed = {"entity": study.entity_id, "refs": required_refs, **exact}
    return LeverLimitAnswer(
        answer_id="G4L-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16],
        answer_kind="LEVER_LIMIT_OBSERVATION",
        entity_id=study.entity_id,
        mechanism_explanation=explanation,
        evidence_refs=refs,
        competing_models=competing,
        falsifier=falsifier,
        limitations=limitations,
        **exact,
    )


__all__ = [
    "G4LimitError",
    "LeverLimitAnswer",
    "LeverLimitStudy",
    "LimitObservation",
    "LimitProbeSpec",
    "validate_limit_answer",
]
