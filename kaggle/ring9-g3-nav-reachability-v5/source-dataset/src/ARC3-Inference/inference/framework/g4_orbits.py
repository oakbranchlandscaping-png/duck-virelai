"""G4.2 repeated-activation records for confirmed levers.

The broad G3 sweep establishes that an intervention is a lever.  G4.2 then
repeats that same intervention and compares complete counter-masked states.
It stops only on an observed masked null, an exact prior-state recurrence, or
an external boundary that interrupts the experiment.  A run budget never
becomes evidence that an orbit is complete.
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


class G4OrbitError(ValueError):
    """A repeated-activation record or explanation violates its evidence."""


def string_list(raw: Any, name: str, *, required: bool, error: type[ValueError] = G4OrbitError) -> tuple[str, ...]:
    """A list of strings, strictly: a bare string is refused, never split into characters (R9-R12)."""
    if raw is None and not required:
        return ()
    if not isinstance(raw, (list, tuple)) or not all(isinstance(item, str) for item in raw):
        raise error(f"{name} must be a list of strings")
    values = tuple(item.strip() for item in raw if item.strip())
    if required and not values:
        raise error(f"{name} must not be empty")
    return values


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _grid(value: Sequence[Sequence[int]]) -> Grid:
    return tuple(tuple(int(cell) for cell in row) for row in value)


def _address(grid: Grid, law: MaskLaw | None) -> str:
    return raw_address(grid) if law is None else world_address(grid, law)


@dataclass(frozen=True)
class LeverOrbitStep:
    activation_index: int
    evidence_ref: str
    transition_id: int
    before_world_address: str
    after_world_address: str
    disposition: str
    world_changed: bool
    changed_cell_count: int
    changed_cells: tuple[CellChange, ...]
    recurrence_to_state_index: int | None = None
    observed_period: int | None = None
    boundary_state: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LeverOrbitAnswer:
    answer_id: str
    answer_kind: str
    entity_id: str
    intervention: Mapping[str, Any]
    stop_disposition: str
    state_sequence: tuple[str, ...]
    recurrence_to_state_index: int | None
    observed_period: int | None
    mechanism_explanation: str
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]


class LeverOrbit:
    """Lossless observed orbit of one known lever from its current state."""

    def __init__(
        self,
        *,
        entity_id: str,
        intervention: Mapping[str, Any],
        mask_law: MaskLaw | None,
    ) -> None:
        self.entity_id = str(entity_id)
        self.intervention = dict(intervention)
        self.mask_law = mask_law
        self.initial_grid: Grid | None = None
        self.state_sequence: list[str] = []
        self.steps: list[LeverOrbitStep] = []
        self.stop_disposition: str | None = None

    @property
    def closed(self) -> bool:
        return self.stop_disposition is not None

    def record(
        self,
        *,
        evidence_ref: str,
        transition_id: int,
        before: Sequence[Sequence[int]],
        after: Sequence[Sequence[int]],
        boundary_state: Mapping[str, Any] | None = None,
    ) -> LeverOrbitStep:
        if self.closed:
            raise G4OrbitError("the lever orbit is already closed")
        left, right = _grid(before), _grid(after)
        before_address = _address(left, self.mask_law)
        after_address = _address(right, self.mask_law)
        if self.initial_grid is None:
            self.initial_grid = left
            self.state_sequence.append(before_address)
        elif before_address != self.state_sequence[-1]:
            raise G4OrbitError(
                "the repeated-activation chain is discontinuous: the next before-state "
                "does not match the previous after-state"
            )

        if self.mask_law is None:
            changed = tuple(
                (row, col, value, right[row][col])
                for row, values in enumerate(left)
                for col, value in enumerate(values)
                if value != right[row][col]
            )
        else:
            delta = partition_delta(left, right, self.mask_law)
            changed = tuple(
                (row, col, left[row][col], right[row][col])
                for row, col in sorted(delta.world_cells)
            )

        terminal = bool(boundary_state) and any(
            bool(boundary_state.get(key))
            for key in ("done", "level_completed", "game_over", "run_complete")
        )
        recurrence_index: int | None = None
        period: int | None = None
        if terminal:
            disposition = "BOUNDARY_INTERRUPTED"
        elif after_address == before_address:
            disposition = "NULL_AT_OBSERVED_STATE"
            recurrence_index = len(self.state_sequence) - 1
            period = 0
        elif after_address in self.state_sequence:
            disposition = "OBSERVED_STATE_RECURRENCE"
            recurrence_index = self.state_sequence.index(after_address)
            period = len(self.state_sequence) - recurrence_index
        else:
            disposition = "NOVEL_STATE_REVEALED"

        self.state_sequence.append(after_address)
        step = LeverOrbitStep(
            activation_index=len(self.steps) + 1,
            evidence_ref=str(evidence_ref),
            transition_id=int(transition_id),
            before_world_address=before_address,
            after_world_address=after_address,
            disposition=disposition,
            world_changed=bool(changed),
            changed_cell_count=len(changed),
            changed_cells=changed,
            recurrence_to_state_index=recurrence_index,
            observed_period=period,
            boundary_state=None if not boundary_state else dict(boundary_state),
        )
        self.steps.append(step)
        if disposition != "NOVEL_STATE_REVEALED":
            self.stop_disposition = disposition
        return step

    def snapshot(self, *, include_cells: bool = True) -> dict[str, Any]:
        steps = [asdict(item) for item in self.steps]
        if not include_cells:
            for item in steps:
                item.pop("changed_cells", None)
        return {
            "schema": "virelai-g4-lever-orbit-v1",
            "entity_id": self.entity_id,
            "intervention": dict(self.intervention),
            "mask_law_version_id": (
                None if self.mask_law is None else self.mask_law.law_version_id
            ),
            "status": self.stop_disposition or "ACTIVE",
            "state_sequence": list(self.state_sequence),
            "unique_state_count": len(set(self.state_sequence)),
            "activation_count": len(self.steps),
            "steps": steps,
        }


def validate_orbit_answer(raw: Mapping[str, Any], orbit: LeverOrbit) -> LeverOrbitAnswer:
    if not orbit.closed:
        raise G4OrbitError("an orbit answer is premature while repeated activation remains open")
    if orbit.stop_disposition == "BOUNDARY_INTERRUPTED":
        raise G4OrbitError("a boundary-interrupted orbit is unresolved and cannot be closed by prose")
    answer_kind = str(raw.get("answer_kind") or "").strip().upper()
    if answer_kind != "LEVER_ORBIT_OBSERVATION":
        raise G4OrbitError("answer_kind must be LEVER_ORBIT_OBSERVATION")
    if str(raw.get("entity_id") or "").strip() != orbit.entity_id:
        raise G4OrbitError("entity_id must match the active lever")
    if _canonical(raw.get("intervention")) != _canonical(orbit.intervention):
        raise G4OrbitError("intervention must exactly match the repeated confirmed action")
    if str(raw.get("stop_disposition") or "").strip() != orbit.stop_disposition:
        raise G4OrbitError("stop_disposition must match the observed orbit boundary")
    supplied_states = tuple(str(item) for item in raw.get("state_sequence") or ())
    if supplied_states != tuple(orbit.state_sequence):
        raise G4OrbitError("state_sequence must exactly match the counter-masked observation record")
    last = orbit.steps[-1]
    supplied_recurrence = raw.get("recurrence_to_state_index")
    supplied_period = raw.get("observed_period")
    if supplied_recurrence != last.recurrence_to_state_index:
        raise G4OrbitError("recurrence_to_state_index must match the observed record")
    if supplied_period != last.observed_period:
        raise G4OrbitError("observed_period must match the observed record")
    explanation = str(raw.get("mechanism_explanation") or "").strip()
    if len(explanation.split()) < 8:
        raise G4OrbitError("mechanism_explanation must describe the repeated observed behavior")
    refs = tuple(str(item).strip() for item in raw.get("evidence_refs") or () if str(item).strip())
    required_refs = tuple(item.evidence_ref for item in orbit.steps)
    if refs != required_refs:
        raise G4OrbitError("evidence_refs must list every orbit transition in observation order")
    competing = string_list(raw.get("competing_models"), "competing_models", required=True)
    falsifier = str(raw.get("falsifier") or "").strip()
    if len(falsifier.split()) < 5:
        raise G4OrbitError("falsifier must name a concrete later contradiction")
    limitations = string_list(raw.get("limitations"), "limitations", required=False)
    seed = {
        "entity": orbit.entity_id,
        "states": orbit.state_sequence,
        "refs": required_refs,
        "explanation": explanation,
    }
    return LeverOrbitAnswer(
        answer_id="G4O-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16],
        answer_kind=answer_kind,
        entity_id=orbit.entity_id,
        intervention=dict(orbit.intervention),
        stop_disposition=str(orbit.stop_disposition),
        state_sequence=tuple(orbit.state_sequence),
        recurrence_to_state_index=last.recurrence_to_state_index,
        observed_period=last.observed_period,
        mechanism_explanation=explanation,
        evidence_refs=refs,
        competing_models=competing,
        falsifier=falsifier,
        limitations=limitations,
    )


__all__ = [
    "G4OrbitError",
    "LeverOrbit",
    "LeverOrbitAnswer",
    "LeverOrbitStep",
    "validate_orbit_answer",
]
