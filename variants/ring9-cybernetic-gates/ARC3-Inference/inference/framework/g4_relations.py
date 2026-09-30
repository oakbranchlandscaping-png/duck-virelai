"""G4-B, levers together: frozen predictions, graded on the counter-masked board (R9-R12).

Author: Claude (Alpha build seat), 2026-09-29.

The target (BUILD_PLAN_G4_CLICK_COMPLETION v2 onward): find how the levers affect each other;
before each test, declare what you expect. Duck freezes one prediction at a time: the one action
to take, and what it will do to every lever's region and to the rest of the board. The controller
takes that action (one frame in, one action out) and grades the prediction against the
counter-masked frame. Nothing here is world-specific: a lever's region and its recorded steps come
from the lever's own G4.1 anatomy and G4-A run.

Per region, an outcome is one of:

- ``UNCHANGED``: no masked cell of the region changed;
- ``STEPS``: the region changed exactly as one of the lever's own recorded presses changed it;
- ``CHANGES``: the region changed some other way.

A prediction of ``CHANGES`` is met by ``STEPS`` or ``CHANGES``. Cells outside every region are
graded ``NO_CHANGE`` or ``CHANGES``. A prediction is SUPPORTED when every expectation is met, and
CONTRADICTED otherwise. Contradicted predictions stay on the record. Two different masked outcomes
of the same action from the same masked board are recorded as a missing condition.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from inference.framework.counter_verification import MaskLaw
from inference.framework.g4_orbits import string_list
from inference.framework.masked_world_state import partition_delta, raw_address, world_address

UNCHANGED, STEPS, CHANGES = "UNCHANGED", "STEPS", "CHANGES"
NO_CHANGE = "NO_CHANGE"
EXPECTATIONS = (UNCHANGED, STEPS, CHANGES)
ELSEWHERE = (NO_CHANGE, CHANGES)
PENDING, SUPPORTED, CONTRADICTED = "PENDING", "SUPPORTED", "CONTRADICTED"
PREDICTION_KIND, RELATIONS_KIND = "LEVER_PREDICTION", "LEVER_RELATIONS"


class G4RelationError(ValueError):
    """A prediction or description that does not meet the G4-B contract."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def strings(raw: Any, name: str, *, required: bool) -> tuple[str, ...]:
    return string_list(raw, name, required=required, error=G4RelationError)


def _words(raw: Any, name: str, minimum: int) -> str:
    text = raw.strip() if isinstance(raw, str) else ""
    if len(text.split()) < minimum:
        raise G4RelationError(f"{name} must be a sentence of at least {minimum} words")
    return text


# ---- lever regions --------------------------------------------------------------------------

@dataclass(frozen=True)
class LeverRegion:
    """A lever's own cells, and the exact changes its own presses made there (G4.1 and G4-A)."""

    entity_id: str
    click: dict[str, Any]
    cells: tuple[tuple[int, int], ...]
    steps: tuple[tuple[tuple[int, int, int, int], ...], ...]
    lever_class: str | None = None

    def observe(self, changed: Mapping[tuple[int, int], tuple[int, int]]) -> str:
        mine = tuple(sorted((r, c, *changed[(r, c)]) for r, c in self.cells if (r, c) in changed))
        if not mine:
            return UNCHANGED
        return STEPS if mine in self.steps else CHANGES

    def state_label(self, grid: Sequence[Sequence[int]]) -> str:
        """Which recorded state the region is in now: S0, S1, ... in first-seen order."""
        now = tuple(grid[r][c] for r, c in self.cells)
        for index, content in enumerate(self._contents()):
            if content == now:
                return f"S{index}"
        return "UNRECORDED"

    def _contents(self) -> list[tuple[int, ...]]:
        seen: list[tuple[int, ...]] = []
        for step in self.steps:
            if len(step) != len(self.cells):
                continue
            for column in (2, 3):
                content = tuple(cell[column] for cell in step)
                if content not in seen:
                    seen.append(content)
        return seen

    def bbox(self) -> list[int] | None:
        rows, cols = [r for r, _ in self.cells], [c for _, c in self.cells]
        return [min(rows), min(cols), max(rows), max(cols)] if self.cells else None


def lever_regions(
    anatomies: Sequence[Mapping[str, Any]], orbits: Sequence[Mapping[str, Any]],
    classes: Mapping[str, str] | None = None,
) -> tuple[LeverRegion, ...]:
    """One region per lever: its LOCAL anatomy cells (all its channels if none is local)."""
    steps_by_entity = {str(item.get("entity_id")): item.get("steps") or () for item in orbits}
    regions: list[LeverRegion] = []
    for anatomy in anatomies:
        entity_id = str(anatomy.get("entity_id") or "")
        channels = [item for item in anatomy.get("channels") or () if isinstance(item, Mapping)]
        local = [item for item in channels if item.get("locality") == "LOCAL"] or channels
        cells = tuple(sorted({(int(r), int(c)) for item in local for r, c in item.get("cells") or ()}))
        runs = steps_by_entity.get(entity_id, ())
        if not cells:  # no anatomy cells recorded: the cells the lever's own run changed
            cells = tuple(sorted({(int(r), int(c)) for step in runs for r, c, *_ in step.get("changed_cells") or ()}))
        if not entity_id:
            raise G4RelationError("a lever anatomy has no entity_id")
        inside = set(cells)
        steps = []
        for step in runs:
            change = tuple(sorted(
                (int(r), int(c), int(b), int(a)) for r, c, b, a in step.get("changed_cells") or ()
                if (int(r), int(c)) in inside
            ))
            if change and change not in steps:
                steps.append(change)
        regions.append(LeverRegion(
            entity_id=entity_id, click=dict(anatomy.get("intervention") or {}), cells=cells,
            steps=tuple(steps), lever_class=(classes or {}).get(entity_id),
        ))
    return tuple(regions)


def masked_changes(
    before: Sequence[Sequence[int]], after: Sequence[Sequence[int]], law: MaskLaw | None,
) -> dict[tuple[int, int], tuple[int, int]]:
    """The changed cells outside the counter mask, as {(row, col): (before, after)}."""
    if law is None:
        cells = {(r, c) for r, row in enumerate(before) for c, value in enumerate(row) if value != after[r][c]}
    else:
        cells = set(partition_delta(before, after, law).world_cells)
    return {(r, c): (int(before[r][c]), int(after[r][c])) for r, c in sorted(cells)}


def masked_address(grid: Sequence[Sequence[int]], law: MaskLaw | None) -> str:
    return raw_address(grid) if law is None else world_address(grid, law)


# ---- predictions ----------------------------------------------------------------------------

@dataclass
class Prediction:
    prediction_id: str
    action: dict[str, Any]
    acted_lever: str | None
    expected: dict[str, str]
    named: list[str]
    elsewhere: str
    because: str
    declared_at_transition: int
    status: str = PENDING
    observed: dict[str, str] | None = None
    observed_elsewhere: str | None = None
    missed: list[str] = field(default_factory=list)
    evidence_ref: str | None = None
    transition_id: int | None = None
    answer_kind: str = PREDICTION_KIND

    @property
    def graded(self) -> bool:
        return self.status in {SUPPORTED, CONTRADICTED}

    def compact(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "prediction_id": self.prediction_id, "acted_lever": self.acted_lever,
            "action": self.action, "status": self.status,
        }
        if self.observed is not None:
            out["observed"] = {key: value for key, value in self.observed.items() if value != UNCHANGED}
            out["observed_elsewhere"] = self.observed_elsewhere
            out["missed"] = list(self.missed)
        return out


def validate_prediction(
    raw: Mapping[str, Any], regions: Sequence[LeverRegion], *, prediction_id: str,
    declared_at_transition: int, action: dict[str, Any],
) -> Prediction:
    """Freeze Duck's prediction; ``action`` is already normalized and admitted by the caller."""
    if str(raw.get("answer_kind") or "").strip().upper() != PREDICTION_KIND:
        raise G4RelationError(f"answer_kind must be {PREDICTION_KIND}")
    known = {region.entity_id: region for region in regions}
    expected_raw = raw.get("expected")
    if not isinstance(expected_raw, Mapping) or not expected_raw:
        raise G4RelationError("expected must map lever entity_ids to UNCHANGED, STEPS or CHANGES")
    expected = {region.entity_id: UNCHANGED for region in regions}
    for key, value in expected_raw.items():
        entity_id = str(key).strip()
        if entity_id not in known:
            raise G4RelationError(f"expected names an unknown lever {entity_id!r}")
        outcome = str(value or "").strip().upper()
        if outcome not in EXPECTATIONS:
            raise G4RelationError(f"expected[{entity_id!r}] must be one of {list(EXPECTATIONS)}")
        expected[entity_id] = outcome
    elsewhere = str(raw.get("elsewhere") or NO_CHANGE).strip().upper()
    if elsewhere not in ELSEWHERE:
        raise G4RelationError(f"elsewhere must be one of {list(ELSEWHERE)}")
    acted = next((region.entity_id for region in regions if _canonical(region.click) == _canonical(action)), None)
    return Prediction(
        prediction_id=prediction_id, action=dict(action), acted_lever=acted, expected=expected,
        named=sorted(str(key).strip() for key in expected_raw), elsewhere=elsewhere,
        because=_words(raw.get("because"), "because", 5), declared_at_transition=int(declared_at_transition),
    )


def _met(expected: str, observed: str) -> bool:
    return observed == expected or (expected == CHANGES and observed == STEPS)


def grade(
    prediction: Prediction, regions: Sequence[LeverRegion],
    changed: Mapping[tuple[int, int], tuple[int, int]], *, evidence_ref: str, transition_id: int,
) -> Prediction:
    """Grade a frozen prediction on the transition that executed it (never an earlier one)."""
    if transition_id <= prediction.declared_at_transition:
        raise G4RelationError("a prediction is graded only on a transition after it was frozen")
    observed = {region.entity_id: region.observe(changed) for region in regions}
    inside = {cell for region in regions for cell in region.cells}
    elsewhere = CHANGES if any(cell not in inside for cell in changed) else NO_CHANGE
    missed = [key for key, value in prediction.expected.items() if not _met(value, observed[key])]
    if elsewhere != prediction.elsewhere:
        missed.append("elsewhere")
    prediction.observed = observed
    prediction.observed_elsewhere = elsewhere
    prediction.missed = missed
    prediction.status = CONTRADICTED if missed else SUPPORTED
    prediction.evidence_ref = evidence_ref
    prediction.transition_id = int(transition_id)
    return prediction


@dataclass
class OutcomeRecord:
    """Every graded transition by (action, masked board before); a split is a missing condition."""

    seen: dict[str, dict[str, Any]] = field(default_factory=dict)
    conditions: list[dict[str, Any]] = field(default_factory=list)

    def note(self, action: Mapping[str, Any], before: str, after: str, evidence_ref: str) -> dict[str, Any] | None:
        key = _canonical([action, before])
        row = self.seen.setdefault(key, {"action": dict(action), "before_address": before, "outcomes": {}})
        row["outcomes"].setdefault(after, []).append(evidence_ref)
        if len(row["outcomes"]) < 2:
            return None
        condition_id = "MC-" + hashlib.sha256(key.encode()).hexdigest()[:10]
        existing = next((item for item in self.conditions if item["condition_id"] == condition_id), None)
        record = {
            "condition_id": condition_id, "action": dict(action), "before_address": before,
            "outcomes": {address: list(refs) for address, refs in row["outcomes"].items()},
            "reading": "the same action from the same masked board had different outcomes: a condition is missing",
        }
        if existing is None:
            self.conditions.append(record)
        else:
            existing.update(record)
        return record


def coverage(predictions: Sequence[Prediction], levers: Sequence[str]) -> tuple[list[str], list[str]]:
    """Levers pressed in a graded prediction, and those not yet."""
    acted = {item.acted_lever for item in predictions if item.graded and item.acted_lever}
    return [item for item in levers if item in acted], [item for item in levers if item not in acted]


# ---- the description ------------------------------------------------------------------------

@dataclass(frozen=True)
class RelationsAnswer:
    answer_id: str
    answer_kind: str
    description: str
    relations: tuple[dict[str, Any], ...]
    open_conditions: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]


def _relation(raw: Any, index: int, ledger: Mapping[str, Prediction], known: set[str]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise G4RelationError(f"relations[{index}] must be an object with levers, claim and prediction_refs")
    levers = strings(raw.get("levers"), f"relations[{index}].levers", required=True)
    unknown = [item for item in levers if item not in known]
    if unknown:
        raise G4RelationError(f"relations[{index}] names unknown levers {unknown}")
    refs = strings(raw.get("prediction_refs"), f"relations[{index}].prediction_refs", required=True)
    for ref in refs:
        if ref not in ledger:
            raise G4RelationError(f"relations[{index}] cites an unknown prediction {ref!r}")
        if ledger[ref].status != SUPPORTED:
            raise G4RelationError(
                f"relations[{index}] cites {ref}, which is {ledger[ref].status}: a relation rests only on supported predictions"
            )
    covered = {ledger[ref].acted_lever for ref in refs} | {name for ref in refs for name in ledger[ref].named}
    uncovered = [item for item in levers if item not in covered]
    if uncovered:
        raise G4RelationError(
            f"relations[{index}] is about {uncovered}, which none of its cited predictions pressed or named"
        )
    return {"levers": list(levers), "claim": _words(raw.get("claim"), f"relations[{index}].claim", 5),
            "prediction_refs": list(refs)}


def validate_relations_answer(
    raw: Mapping[str, Any], predictions: Sequence[Prediction], levers: Sequence[str],
    conditions: Sequence[Mapping[str, Any]],
) -> RelationsAnswer:
    if str(raw.get("answer_kind") or "").strip().upper() != RELATIONS_KIND:
        raise G4RelationError(f"answer_kind must be {RELATIONS_KIND}")
    _acted, missing = coverage(predictions, levers)
    if missing:
        raise G4RelationError(f"press every lever in a graded prediction first; not yet: {missing}")
    ledger = {item.prediction_id: item for item in predictions}
    relations_raw = raw.get("relations")
    if not isinstance(relations_raw, (list, tuple)) or not relations_raw:
        raise G4RelationError("relations must be a non-empty list")
    relations = tuple(_relation(item, index, ledger, set(levers)) for index, item in enumerate(relations_raw))
    recorded = sorted(item["condition_id"] for item in conditions)
    declared = sorted(strings(raw.get("open_conditions") or [], "open_conditions", required=False))
    if declared != recorded:
        raise G4RelationError(f"open_conditions must list exactly the recorded missing conditions: {recorded}")
    description = _words(raw.get("description"), "description", 20)
    seed = {"description": description, "relations": relations}
    return RelationsAnswer(
        answer_id="G4B-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16],
        answer_kind=RELATIONS_KIND,
        description=description,
        relations=relations,
        open_conditions=tuple(declared),
        competing_models=strings(raw.get("competing_models"), "competing_models", required=True),
        falsifier=_words(raw.get("falsifier"), "falsifier", 5),
        limitations=strings(raw.get("limitations"), "limitations", required=False),
    )


__all__ = [
    "CHANGES", "CONTRADICTED", "G4RelationError", "LeverRegion", "NO_CHANGE", "OutcomeRecord",
    "PENDING", "PREDICTION_KIND", "Prediction", "RELATIONS_KIND", "RelationsAnswer", "STEPS",
    "SUPPORTED", "UNCHANGED", "coverage", "grade", "lever_regions", "masked_address",
    "masked_changes", "strings", "validate_prediction", "validate_relations_answer",
]
