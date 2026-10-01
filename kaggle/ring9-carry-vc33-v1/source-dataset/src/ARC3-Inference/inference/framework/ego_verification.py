"""Scoped prospective verification for the G1 ego gate.

The comparison contract is ported from ``virelai_controller.compare_outcome``.
This module adapts that behavior to the production-shaped H2 ProbeOutcome
record.  It assigns no semantic meaning to action numbers or grid integers.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Any, Iterable, Mapping

from inference.framework.probe_evidence import EVIDENCE_SCHEMA


COMPARISON_OUTCOMES = frozenset(
    {"SUPPORTED", "CONTRADICTED", "INDETERMINATE", "UNMATCHED"}
)
SCOPE_REPRESENTATIONS = frozenset(
    {"VISIBLE_OBSERVATION", "CELLS", "REGION", "ACTED_COMPONENT", "WORLDLINE"}
)
FORM_PREDICATES = frozenset(
    {"STILL", "RECOLOR", "PURE_TRANSLATION", "GROW", "SHRINK", "DEFORM"}
)
PATTERN_PREDICATES = frozenset({"PATTERN_TRANSLATION"})
PREDICATES = frozenset({
    "NO_CHANGE", "ANY_CHANGE", "EXACT_CELL_DELTA",
    *FORM_PREDICATES, *PATTERN_PREDICATES,
})


class EgoVerificationError(ValueError):
    """A prospective prediction is malformed and cannot be journaled."""


@dataclass(frozen=True)
class ActionSpec:
    action: str
    parameters: tuple[tuple[str, int | str], ...] = ()


@dataclass(frozen=True)
class ScopeSpec:
    representation: str
    cells: tuple[tuple[int, int], ...] = ()
    region: tuple[int, int, int, int] | None = None
    identifier: str | None = None


@dataclass(frozen=True)
class ProspectivePrediction:
    prediction_id: str
    probe_id: str
    declared_at_transition: int
    action: ActionSpec
    scope: ScopeSpec
    predicate: str
    expected_parameters: tuple[tuple[str, Any], ...]
    evidence_basis: tuple[str, ...]
    falsifier: str


@dataclass(frozen=True)
class ScopedComparison:
    comparison_id: str
    prediction_id: str
    probe_id: str
    transition_id: int
    outcome: str
    predicate: str
    scoped_changes: tuple[tuple[int, int, int | None, int | None], ...]
    remote_changes: tuple[tuple[int, int, int | None, int | None], ...]
    limitations: tuple[str, ...]
    observed_form: str | None = None
    observed_recolor: bool | None = None
    observed_translation: tuple[int, int] | None = None
    before_footprint: tuple[tuple[int, int], ...] = ()
    after_footprint: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class EgoLaw:
    law_id: str
    law_version_id: str
    revision: int
    status: str
    parent_law_version_id: str | None
    mode: str
    subjects: tuple[str, ...]
    opaque_action_laws: tuple[tuple[str, str], ...]
    conditions: tuple[str, ...]
    constraints: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    demonstration_ref: str
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]
    witness_transition_ids: tuple[int, ...]
    contradiction_transition_ids: tuple[int, ...]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _action_spec(raw: Mapping[str, Any]) -> ActionSpec:
    action = str(raw.get("action") or "").strip().upper()
    if not action:
        raise EgoVerificationError("prediction action is required")
    parameters: list[tuple[str, int | str]] = []
    for key, value in sorted(raw.items()):
        if key == "action":
            continue
        if not isinstance(value, (int, str)) or isinstance(value, bool):
            raise EgoVerificationError(f"prediction action parameter {key!r} must be int or str")
        parameters.append((str(key), value))
    return ActionSpec(action=action, parameters=tuple(parameters))


def _scope_spec(raw: Mapping[str, Any]) -> ScopeSpec:
    representation = str(raw.get("representation") or "").strip().upper()
    if representation not in SCOPE_REPRESENTATIONS:
        raise EgoVerificationError(f"unsupported prediction scope: {representation!r}")
    cells = tuple(
        sorted({(int(cell[0]), int(cell[1])) for cell in raw.get("cells", ())})
    )
    region_raw = raw.get("region")
    region = None if region_raw is None else tuple(int(value) for value in region_raw)
    if representation == "CELLS" and not cells:
        raise EgoVerificationError("CELLS scope requires at least one pre-action cell")
    if representation == "REGION" and (region is None or len(region) != 4):
        raise EgoVerificationError("REGION scope requires [min_row, min_col, max_row, max_col]")
    if representation == "WORLDLINE" and not raw.get("identifier"):
        raise EgoVerificationError("WORLDLINE scope requires an identifier")
    return ScopeSpec(
        representation=representation,
        cells=cells,
        region=region,  # type: ignore[arg-type]
        identifier=(str(raw["identifier"]) if raw.get("identifier") is not None else None),
    )


def prediction_from_mapping(raw: Mapping[str, Any]) -> ProspectivePrediction:
    """Validate and freeze a prediction before its action is admitted."""
    probe_id = str(raw.get("probe_id") or "").strip()
    if not probe_id:
        raise EgoVerificationError("prediction probe_id is required")
    declared_at_transition = int(raw.get("declared_at_transition", -1))
    if declared_at_transition < 0:
        raise EgoVerificationError("declared_at_transition must be zero or greater")
    action_raw = raw.get("action")
    scope_raw = raw.get("scope")
    if not isinstance(action_raw, Mapping):
        raise EgoVerificationError("prediction action must be an object")
    if not isinstance(scope_raw, Mapping):
        raise EgoVerificationError("prediction scope must be an object")
    predicate = str(raw.get("predicate") or "").strip().upper()
    if predicate not in PREDICATES:
        raise EgoVerificationError(f"unsupported prediction predicate: {predicate!r}")
    expected_raw = raw.get("expected_parameters", {})
    if not isinstance(expected_raw, Mapping):
        raise EgoVerificationError("expected_parameters must be an object")
    expected = tuple(sorted((str(key), value) for key, value in expected_raw.items()))
    if predicate == "EXACT_CELL_DELTA":
        changes = expected_raw.get("changes")
        if not isinstance(changes, (list, tuple)):
            raise EgoVerificationError("EXACT_CELL_DELTA requires expected_parameters.changes")
        _normalize_changes(changes)
    if predicate in FORM_PREDICATES:
        _validate_form_expectation(predicate, expected_raw, scope=_scope_spec(scope_raw))
    if predicate == "PATTERN_TRANSLATION":
        _validate_pattern_translation(expected_raw, scope=_scope_spec(scope_raw))
    basis = tuple(str(value) for value in raw.get("evidence_basis", ()))
    falsifier = str(raw.get("falsifier") or "").strip()
    if not basis or not falsifier:
        raise EgoVerificationError("prediction requires evidence_basis and falsifier")
    seed = {
        "probe_id": probe_id,
        "declared_at_transition": declared_at_transition,
        "action": raw["action"],
        "scope": raw["scope"],
        "predicate": predicate,
        "expected_parameters": expected_raw,
        "evidence_basis": basis,
        "falsifier": falsifier,
    }
    prediction_id = str(
        raw.get("prediction_id")
        or "PRED-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16]
    )
    return ProspectivePrediction(
        prediction_id=prediction_id,
        probe_id=probe_id,
        declared_at_transition=declared_at_transition,
        action=_action_spec(action_raw),
        scope=_scope_spec(scope_raw),
        predicate=predicate,
        expected_parameters=expected,
        evidence_basis=basis,
        falsifier=falsifier,
    )


def _action_payload(spec: ActionSpec) -> dict[str, Any]:
    return {"action": spec.action, **dict(spec.parameters)}


def _normalize_changes(
    changes: Iterable[Mapping[str, Any]],
) -> tuple[tuple[int, int, int | None, int | None], ...]:
    normalized = []
    for item in changes:
        if not isinstance(item, Mapping):
            raise EgoVerificationError("cell changes must be objects")
        normalized.append(
            (
                int(item["row"]),
                int(item["col"]),
                None if item.get("before") is None else int(item["before"]),
                None if item.get("after") is None else int(item["after"]),
            )
        )
    return tuple(sorted(normalized))


def _normalize_footprint(raw: Any, *, name: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise EgoVerificationError(f"{name} must be a non-empty coordinate list")
    try:
        cells = tuple(sorted({(int(cell[0]), int(cell[1])) for cell in raw}))
    except (TypeError, ValueError, IndexError) as exc:
        raise EgoVerificationError(f"{name} contains an invalid coordinate") from exc
    if len(cells) != len(raw):
        raise EgoVerificationError(f"{name} must not contain duplicate coordinates")
    return cells


def _normal_shape(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    frozen = frozenset(cells)
    min_row = min(row for row, _ in frozen)
    min_col = min(col for _, col in frozen)
    return frozenset((row - min_row, col - min_col) for row, col in frozen)


def _translation(
    before: Iterable[tuple[int, int]], after: Iterable[tuple[int, int]]
) -> tuple[int, int] | None:
    left, right = frozenset(before), frozenset(after)
    if len(left) != len(right) or _normal_shape(left) != _normal_shape(right):
        return None
    offset = (
        min(row for row, _ in right) - min(row for row, _ in left),
        min(col for _, col in right) - min(col for _, col in left),
    )
    return offset if offset != (0, 0) else None


def _form_for(
    before: Iterable[tuple[int, int]],
    after: Iterable[tuple[int, int]],
    *,
    recolor: bool,
) -> tuple[str, tuple[int, int] | None]:
    left, right = frozenset(before), frozenset(after)
    if left == right:
        return ("RECOLOR" if recolor else "STILL"), None
    displacement = _translation(left, right)
    if displacement is not None:
        return "PURE_TRANSLATION", displacement
    if left < right:
        return "GROW", None
    if right < left:
        return "SHRINK", None
    return "DEFORM", None


def _validate_form_expectation(
    predicate: str, expected: Mapping[str, Any], *, scope: ScopeSpec
) -> None:
    if scope.representation != "CELLS":
        raise EgoVerificationError("form predicates require a CELLS pre-action scope")
    before = _normalize_footprint(expected.get("before_footprint"), name="before_footprint")
    after = _normalize_footprint(expected.get("after_footprint"), name="after_footprint")
    if before != scope.cells:
        raise EgoVerificationError("before_footprint must exactly equal scope.cells")
    if isinstance(expected.get("before_integer"), bool) or not isinstance(
        expected.get("before_integer"), int
    ):
        raise EgoVerificationError("form predicates require integer before_integer")
    if isinstance(expected.get("after_integer"), bool) or not isinstance(
        expected.get("after_integer"), int
    ):
        raise EgoVerificationError("form predicates require integer after_integer")
    if not isinstance(expected.get("recolor"), bool):
        raise EgoVerificationError("form predicates require boolean recolor")
    declared_form, displacement = _form_for(
        before, after, recolor=bool(expected["recolor"])
    )
    if predicate != declared_form:
        raise EgoVerificationError(
            f"declared footprints imply {declared_form}, not {predicate}"
        )
    if bool(expected["recolor"]) != (expected["before_integer"] != expected["after_integer"]):
        raise EgoVerificationError("recolor must equal the declared integer-class change")
    if predicate == "PURE_TRANSLATION":
        raw_displacement = expected.get("displacement")
        if not isinstance(raw_displacement, (list, tuple)) or len(raw_displacement) != 2:
            raise EgoVerificationError("PURE_TRANSLATION requires displacement [dr, dc]")
        if tuple(int(value) for value in raw_displacement) != displacement:
            raise EgoVerificationError("displacement does not produce after_footprint")


def _validate_pattern_translation(
    expected: Mapping[str, Any], *, scope: ScopeSpec
) -> None:
    """Validate a color-agnostic, possibly multi-integer translation claim.

    Duck sees letter-coded components rather than raw integer ids.  This
    contract therefore asks it for observable geometry only; the verifier uses
    the lossless site ledger to test whether the whole declared pattern moved.
    """
    if scope.representation != "CELLS":
        raise EgoVerificationError(
            "PATTERN_TRANSLATION requires a CELLS pre-action scope"
        )
    before = _normalize_footprint(
        expected.get("before_footprint"), name="before_footprint"
    )
    after = _normalize_footprint(
        expected.get("after_footprint"), name="after_footprint"
    )
    if before != scope.cells:
        raise EgoVerificationError("before_footprint must exactly equal scope.cells")
    raw_displacement = expected.get("displacement")
    if not isinstance(raw_displacement, (list, tuple)) or len(raw_displacement) != 2:
        raise EgoVerificationError(
            "PATTERN_TRANSLATION requires displacement [dr, dc]"
        )
    displacement = tuple(int(value) for value in raw_displacement)
    translated = tuple(sorted(
        (row + displacement[0], col + displacement[1]) for row, col in before
    ))
    if translated != after:
        raise EgoVerificationError("displacement does not produce after_footprint")
    if displacement == (0, 0):
        raise EgoVerificationError("PATTERN_TRANSLATION displacement must be nonzero")


def _site_maps(
    outcome: Mapping[str, Any],
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]] | None:
    if outcome.get("site_transition_coverage") != "TOTAL":
        return None
    rows = outcome.get("site_transitions")
    if not isinstance(rows, list):
        return None
    before: dict[tuple[int, int], int] = {}
    after: dict[tuple[int, int], int] = {}
    try:
        for item in rows:
            cell = int(item["row"]), int(item["col"])
            before[cell] = int(item["before"])
            after[cell] = int(item["after"])
    except (TypeError, ValueError, KeyError):
        return None
    return before, after


def _component(
    values: Mapping[tuple[int, int], int], seed: tuple[int, int], integer: int
) -> frozenset[tuple[int, int]]:
    if values.get(seed) != integer:
        return frozenset()
    seen = {seed}
    frontier = [seed]
    while frontier:
        row, col = frontier.pop()
        for cell in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if cell not in seen and values.get(cell) == integer:
                seen.add(cell)
                frontier.append(cell)
    return frozenset(seen)


def _indeterminate_boundary(outcome: Mapping[str, Any]) -> str | None:
    if not outcome.get("before_frame_ref") or not outcome.get("after_frame_ref"):
        return "complete before/after frame evidence is unavailable"
    if outcome.get("shape_before") != outcome.get("shape_after"):
        return "grid geometry changed across the transition"
    boundary = outcome.get("boundary_event")
    if isinstance(boundary, Mapping) and any(
        bool(boundary.get(key))
        for key in ("done", "level_completed", "game_over", "run_complete")
    ):
        return "terminal or level boundary crossed during the transition"
    return None


def _scope_changes(
    prediction: ProspectivePrediction,
    outcome: Mapping[str, Any],
    *,
    resolved_worldline_cells: Iterable[tuple[int, int]] | None,
) -> tuple[
    tuple[tuple[int, int, int | None, int | None], ...] | None,
    tuple[tuple[int, int, int | None, int | None], ...],
    str | None,
]:
    all_changes = _normalize_changes(outcome.get("changed_cells", ()))
    representation = prediction.scope.representation
    if representation == "VISIBLE_OBSERVATION":
        return all_changes, (), None
    if representation == "ACTED_COMPONENT":
        local = outcome.get("target_local_changes")
        remote = outcome.get("remote_changes")
        if outcome.get("target_scope") is None or local is None or remote is None:
            return None, (), "acted component was not resolved from the pre-action frame"
        return _normalize_changes(local), _normalize_changes(remote), None
    if representation == "WORLDLINE":
        if resolved_worldline_cells is None:
            return None, (), "worldline identity was not resolved at the pre-action boundary"
        cells = set(resolved_worldline_cells)
    elif representation == "CELLS":
        cells = set(prediction.scope.cells)
    elif representation == "REGION" and prediction.scope.region is not None:
        r0, c0, r1, c1 = prediction.scope.region
        cells = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        }
    else:
        return None, (), "scope representation is unavailable"
    scoped = tuple(item for item in all_changes if (item[0], item[1]) in cells)
    remote = tuple(item for item in all_changes if (item[0], item[1]) not in cells)
    return scoped, remote, None


def compare_probe_outcome(
    prediction: ProspectivePrediction,
    outcome: Mapping[str, Any],
    *,
    resolved_worldline_cells: Iterable[tuple[int, int]] | None = None,
) -> ScopedComparison:
    """Compare one journaled prediction with its exact H2 ProbeOutcome."""
    transition_id = int(outcome.get("transition_id", -1))
    comparison_id = "CMP-" + hashlib.sha256(
        f"{prediction.prediction_id}|{transition_id}".encode()
    ).hexdigest()[:16]

    def result(
        verdict: str,
        *,
        scoped: tuple[tuple[int, int, int | None, int | None], ...] = (),
        remote: tuple[tuple[int, int, int | None, int | None], ...] = (),
        limitations: tuple[str, ...] = (),
        observed_form: str | None = None,
        observed_recolor: bool | None = None,
        observed_translation: tuple[int, int] | None = None,
        before_footprint: tuple[tuple[int, int], ...] = (),
        after_footprint: tuple[tuple[int, int], ...] = (),
    ) -> ScopedComparison:
        return ScopedComparison(
            comparison_id=comparison_id,
            prediction_id=prediction.prediction_id,
            probe_id=prediction.probe_id,
            transition_id=transition_id,
            outcome=verdict,
            predicate=prediction.predicate,
            scoped_changes=scoped,
            remote_changes=remote,
            limitations=limitations,
            observed_form=observed_form,
            observed_recolor=observed_recolor,
            observed_translation=observed_translation,
            before_footprint=before_footprint,
            after_footprint=after_footprint,
        )

    if outcome.get("schema") != EVIDENCE_SCHEMA:
        return result("UNMATCHED", limitations=("Outcome is not an H2 ProbeOutcome.",))
    if str(outcome.get("probe_id") or "") != prediction.probe_id:
        return result("UNMATCHED", limitations=("Outcome belongs to a different probe.",))
    if transition_id <= prediction.declared_at_transition:
        return result(
            "UNMATCHED",
            limitations=("Prediction was not recorded before the resulting transition.",),
        )
    if _canonical(outcome.get("action")) != _canonical(_action_payload(prediction.action)):
        return result("UNMATCHED", limitations=("Executed action differs from the declared action.",))
    boundary = _indeterminate_boundary(outcome)
    if boundary is not None:
        return result("INDETERMINATE", limitations=(boundary,))
    if prediction.predicate == "PATTERN_TRANSLATION":
        expected = dict(prediction.expected_parameters)
        before_footprint = _normalize_footprint(
            expected["before_footprint"], name="before_footprint"
        )
        after_footprint = _normalize_footprint(
            expected["after_footprint"], name="after_footprint"
        )
        displacement = tuple(int(value) for value in expected["displacement"])
        maps = _site_maps(outcome)
        if maps is None:
            return result(
                "INDETERMINATE",
                limitations=(
                    "total fixed-geometry site evidence is unavailable",
                    "Scope was not widened.",
                ),
                before_footprint=before_footprint,
                after_footprint=after_footprint,
            )
        before_values, after_values = maps
        pairs = tuple(zip(before_footprint, after_footprint))
        pattern_preserved = all(
            before_values.get(source) == after_values.get(destination)
            for source, destination in pairs
        )
        all_changes = _normalize_changes(outcome.get("changed_cells", ()))
        footprint_union = set(before_footprint) | set(after_footprint)
        scoped = tuple(
            item for item in all_changes if (item[0], item[1]) in footprint_union
        )
        remote = tuple(
            item for item in all_changes if (item[0], item[1]) not in footprint_union
        )
        vacated_cells = set(before_footprint) - set(after_footprint)
        entered_cells = set(after_footprint) - set(before_footprint)
        support_changed = bool(scoped) and all(
            any((item[0], item[1]) == cell for item in scoped)
            for cell in vacated_cells | entered_cells
        )
        supported = pattern_preserved and support_changed
        limitations = [
            "Pattern verdict verifies declared geometry and exact integer arrangement without assigning integer semantics."
        ]
        if remote:
            limitations.append(
                "Remote changes were observed separately and do not reverse the scoped verdict."
            )
        if not pattern_preserved:
            limitations.append(
                "The declared multi-integer pattern was not preserved at the predicted destination."
            )
        return result(
            "SUPPORTED" if supported else "CONTRADICTED",
            scoped=scoped,
            remote=remote,
            limitations=tuple(limitations),
            observed_form="PATTERN_TRANSLATION" if pattern_preserved else None,
            observed_recolor=False if pattern_preserved else None,
            observed_translation=displacement if pattern_preserved else None,
            before_footprint=before_footprint,
            after_footprint=after_footprint if pattern_preserved else (),
        )
    if prediction.predicate in FORM_PREDICATES:
        expected = dict(prediction.expected_parameters)
        before_footprint = _normalize_footprint(
            expected["before_footprint"], name="before_footprint"
        )
        after_footprint = _normalize_footprint(
            expected["after_footprint"], name="after_footprint"
        )
        maps = _site_maps(outcome)
        if maps is None:
            return result(
                "INDETERMINATE",
                limitations=(
                    "total fixed-geometry site evidence is unavailable",
                    "Scope was not widened.",
                ),
                before_footprint=before_footprint,
                after_footprint=after_footprint,
            )
        before_values, after_values = maps
        before_integer = int(expected["before_integer"])
        after_integer = int(expected["after_integer"])
        resolved_before = _component(before_values, before_footprint[0], before_integer)
        if resolved_before != frozenset(before_footprint):
            return result(
                "INDETERMINATE",
                limitations=(
                    "declared pre-action footprint is not the exact 4-connected equal-integer component",
                    "Scope was not widened.",
                ),
                before_footprint=before_footprint,
                after_footprint=after_footprint,
            )
        resolved_after = _component(after_values, after_footprint[0], after_integer)
        all_changes = _normalize_changes(outcome.get("changed_cells", ()))
        footprint_union = set(before_footprint) | set(after_footprint)
        scoped = tuple(
            item for item in all_changes if (item[0], item[1]) in footprint_union
        )
        remote = tuple(
            item for item in all_changes if (item[0], item[1]) not in footprint_union
        )
        expected_recolor = bool(expected["recolor"])
        observed_recolor = before_integer != after_integer
        observed_form, observed_translation = _form_for(
            before_footprint,
            resolved_after or after_footprint,
            recolor=observed_recolor,
        )
        supported = (
            resolved_after == frozenset(after_footprint)
            and prediction.predicate == observed_form
            and expected_recolor == observed_recolor
            and all(before_values.get(cell) == before_integer for cell in before_footprint)
            and all(after_values.get(cell) == after_integer for cell in after_footprint)
        )
        limitations = [
            "Form verdict uses declared 4-connected equal-integer component correspondence."
        ]
        if not resolved_after:
            limitations.append(
                "The predicted after component was absent; no alternative correspondence was guessed."
            )
            observed_form = None
            observed_recolor = None
            observed_translation = None
        elif resolved_after != frozenset(after_footprint):
            limitations.append(
                "The after component footprint differed from the exact prediction."
            )
        if remote:
            limitations.append(
                "Remote changes were observed separately and do not reverse the scoped verdict."
            )
        return result(
            "SUPPORTED" if supported else "CONTRADICTED",
            scoped=scoped,
            remote=remote,
            limitations=tuple(limitations),
            observed_form=observed_form,
            observed_recolor=observed_recolor,
            observed_translation=observed_translation,
            before_footprint=before_footprint,
            after_footprint=tuple(sorted(resolved_after)) if resolved_after else (),
        )
    scoped, remote, scope_error = _scope_changes(
        prediction,
        outcome,
        resolved_worldline_cells=resolved_worldline_cells,
    )
    if scoped is None:
        return result(
            "INDETERMINATE",
            remote=remote,
            limitations=(scope_error or "Prediction scope could not be resolved.", "Scope was not widened."),
        )

    if prediction.predicate == "NO_CHANGE":
        supported = not scoped
    elif prediction.predicate == "ANY_CHANGE":
        supported = bool(scoped)
    else:
        expected = dict(prediction.expected_parameters).get("changes", ())
        supported = scoped == _normalize_changes(expected)
    limitations = ["Verdict applies only to the declared scope."]
    if remote:
        limitations.append(
            "Remote changes were observed separately and do not reverse the scoped verdict."
        )
    return result(
        "SUPPORTED" if supported else "CONTRADICTED",
        scoped=scoped,
        remote=remote,
        limitations=tuple(limitations),
    )


def ego_law_from_supported(
    answer: Mapping[str, Any], comparison: ScopedComparison
) -> EgoLaw:
    """Create the first immutable EgoLaw version from a supported demonstration."""
    if comparison.outcome != "SUPPORTED":
        raise EgoVerificationError("EgoLaw requires a supported scoped demonstration")
    answer_id = str(answer.get("answer_id") or "").strip()
    if not answer_id:
        raise EgoVerificationError("EgoLaw requires the explanatory answer_id")
    law_id = "EL-" + hashlib.sha256(f"G1-EGO|{answer_id}".encode()).hexdigest()[:16]
    version_seed = f"{law_id}|v1|{comparison.comparison_id}"
    laws = answer.get("action_laws")
    if not isinstance(laws, Mapping):
        raise EgoVerificationError("EgoLaw requires opaque action laws")
    return EgoLaw(
        law_id=law_id,
        law_version_id="ELV-" + hashlib.sha256(version_seed.encode()).hexdigest()[:16],
        revision=1,
        status="OBSERVED",
        parent_law_version_id=None,
        mode=str(answer.get("answer_kind") or "UNRESOLVED").strip().upper().replace(" ", "_"),
        subjects=tuple(str(value) for value in answer.get("subjects", ())),
        opaque_action_laws=tuple(sorted((str(key), str(value)) for key, value in laws.items())),
        conditions=tuple(str(value) for value in answer.get("conditions", ())),
        constraints=tuple(str(value) for value in answer.get("constraints", ())),
        evidence_refs=tuple(str(value) for value in answer.get("evidence_refs", ())),
        demonstration_ref=comparison.comparison_id,
        competing_models=tuple(str(value) for value in answer.get("competing_models", ())),
        falsifier=str(answer.get("falsifier") or ""),
        limitations=tuple(
            dict.fromkeys(
                (*[str(value) for value in answer.get("limitations", ())], *comparison.limitations)
            )
        ),
        witness_transition_ids=(comparison.transition_id,),
        contradiction_transition_ids=(),
    )


def ego_law_from_interface(answer: Mapping[str, Any], *, prerequisite_ref: str) -> EgoLaw:
    """Create a pointer EgoLaw from the controller-supplied action interface."""
    answer_id = str(answer.get("answer_id") or "").strip()
    laws = answer.get("action_laws")
    if not answer_id or not isinstance(laws, Mapping) or set(laws) != {"ACTION6"}:
        raise EgoVerificationError(
            "Interface-grounded pointer EgoLaw requires an answer_id and ACTION6 law"
        )
    law_id = "EL-" + hashlib.sha256(f"G1-EGO|{answer_id}".encode()).hexdigest()[:16]
    version_seed = f"{law_id}|v1|{prerequisite_ref}|INTERFACE_AXIOM"
    return EgoLaw(
        law_id=law_id,
        law_version_id="ELV-" + hashlib.sha256(version_seed.encode()).hexdigest()[:16],
        revision=1,
        status="INTERFACE_AXIOM",
        parent_law_version_id=None,
        mode="POINTER_GOD_MODE",
        subjects=tuple(str(value) for value in answer.get("subjects", ())),
        opaque_action_laws=tuple(
            sorted((str(key), str(value)) for key, value in laws.items())
        ),
        conditions=tuple(str(value) for value in answer.get("conditions", ())),
        constraints=tuple(str(value) for value in answer.get("constraints", ())),
        evidence_refs=(prerequisite_ref,),
        demonstration_ref=prerequisite_ref,
        competing_models=tuple(
            str(value) for value in answer.get("competing_models", ())
        ),
        falsifier=str(answer.get("falsifier") or ""),
        limitations=tuple(str(value) for value in answer.get("limitations", ())),
        witness_transition_ids=(),
        contradiction_transition_ids=(),
    )


def revise_ego_law(parent: EgoLaw, comparison: ScopedComparison) -> EgoLaw | None:
    """Append a supported or contradicted law version; preserve the parent."""
    if comparison.outcome not in {"SUPPORTED", "CONTRADICTED"}:
        return None
    witnesses = parent.witness_transition_ids
    contradictions = parent.contradiction_transition_ids
    status = parent.status
    if comparison.outcome == "SUPPORTED":
        witnesses = tuple(sorted(set((*witnesses, comparison.transition_id))))
    else:
        contradictions = tuple(sorted(set((*contradictions, comparison.transition_id))))
        status = "CONTRADICTED"
    revision = parent.revision + 1
    seed = f"{parent.law_id}|v{revision}|{comparison.comparison_id}|{comparison.outcome}"
    return replace(
        parent,
        law_version_id="ELV-" + hashlib.sha256(seed.encode()).hexdigest()[:16],
        revision=revision,
        status=status,
        parent_law_version_id=parent.law_version_id,
        demonstration_ref=comparison.comparison_id,
        witness_transition_ids=witnesses,
        contradiction_transition_ids=contradictions,
    )
