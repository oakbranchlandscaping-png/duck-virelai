"""Typed G3 explanation contract derived from admitted lever evidence."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping

from inference.framework.lever_attribution import LeverAttribution


class LeverDossierError(ValueError):
    """A proposed dossier is malformed or contradicts admitted G3 scope."""


@dataclass(frozen=True)
class LeverDossierAnswer:
    answer_id: str
    answer_kind: str
    target_member_id: str
    explanation: str
    intervention: Mapping[str, Any]
    effect_summary: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    conditions: tuple[str, ...]
    limitations: tuple[str, ...]


def _bbox(cells: tuple[tuple[int, int], ...]) -> list[int] | None:
    if not cells:
        return None
    return [
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    ]


def effect_summary(
    attribution: LeverAttribution, *, witness_evidence_ref: str
) -> dict[str, Any]:
    """Return the only causal scope a G3 dossier may claim."""
    return {
        "schema": "virelai-g3-effect-summary-v1",
        "target_member_id": attribution.target_member_id,
        "witness_evidence_ref": str(witness_evidence_ref),
        "causal_scope": "NON_COUNTER_RESIDUE_ONLY",
        "counter_treatment": "COUNTER_CHANGES_EXCLUDED_FROM_LEVER_CAUSALITY",
        "local_changed_cell_count": len(attribution.local_residue_cells),
        "local_changed_bbox": _bbox(attribution.local_residue_cells),
        "remote_changed_cell_count": len(attribution.remote_residue_cells),
        "remote_changed_bbox": _bbox(attribution.remote_residue_cells),
        "counter_masked_cell_count": len(attribution.counter_masked_cells),
    }


def _string_list(raw: Any, field: str, *, required: bool) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise LeverDossierError(f"{field} must be a list of strings")
    if any(not isinstance(item, str) for item in raw):
        raise LeverDossierError(f"{field} must contain only strings")
    values = tuple(item.strip() for item in raw if item.strip())
    if required and not values:
        raise LeverDossierError(f"{field} must not be empty")
    return values


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _validate_counter_language(explanation: str, *, counter_cells: int) -> None:
    if counter_cells <= 0:
        return
    lowered = explanation.lower()
    exclusion_terms = ("exclud", "mask", "bookkeeping", "not causal", "not a lever effect")
    if "counter" not in lowered or not any(term in lowered for term in exclusion_terms):
        raise LeverDossierError(
            "explanation must explicitly state that observed counter changes were excluded"
        )
    for sentence in re.split(r"[.!?;]+", lowered):
        if "counter" not in sentence:
            continue
        causal_terms = ("effect", "cause", "caused", "trigger", "changed", "response")
        if any(term in sentence for term in causal_terms) and not any(
            term in sentence for term in exclusion_terms
        ):
            raise LeverDossierError(
                "a sentence assigns counter change without stating its exclusion from lever causality"
            )


def validate_lever_dossier(
    raw: Mapping[str, Any],
    *,
    answer_id: str,
    target_member_id: str,
    expected_intervention: Mapping[str, Any],
    expected_effect_summary: Mapping[str, Any],
    required_evidence_refs: tuple[str, ...],
) -> LeverDossierAnswer:
    explanation = str(raw.get("explanation") or raw.get("mechanism") or "").strip()
    if len(explanation.split()) < 8:
        raise LeverDossierError(
            "explanation must describe the intervention, observed response, and causal scope"
        )
    intervention = raw.get("intervention")
    if not isinstance(intervention, Mapping) or not intervention:
        raise LeverDossierError("intervention must be a non-empty action object")
    if _canonical(intervention) != _canonical(expected_intervention):
        raise LeverDossierError("intervention must exactly match the prospectively confirmed action")
    summary = raw.get("effect_summary")
    if not isinstance(summary, Mapping):
        raise LeverDossierError("effect_summary must be the supplied structured object")
    if _canonical(summary) != _canonical(expected_effect_summary):
        raise LeverDossierError(
            "effect_summary must exactly match the admitted counter-masked lever residue"
        )
    refs = _string_list(raw.get("evidence_refs"), "evidence_refs", required=True)
    if set(refs) != set(required_evidence_refs) or len(refs) != len(required_evidence_refs):
        raise LeverDossierError(
            "evidence_refs must exactly name the witness and its supported confirmation"
        )
    competing = _string_list(
        raw.get("competing_models"), "competing_models", required=True
    )
    if any(len(item.split()) < 3 for item in competing):
        raise LeverDossierError("each competing model must be an explanatory phrase")
    falsifier = str(raw.get("falsifier") or "").strip()
    if len(falsifier.split()) < 5:
        raise LeverDossierError("falsifier must describe a concrete later contradiction")
    conditions = _string_list(
        raw.get("conditions", []), "conditions", required=False
    )
    limitations = _string_list(
        raw.get("limitations", []), "limitations", required=False
    )
    _validate_counter_language(
        explanation,
        counter_cells=int(expected_effect_summary.get("counter_masked_cell_count") or 0),
    )
    return LeverDossierAnswer(
        answer_id=answer_id,
        answer_kind="LEVER_DOSSIER",
        target_member_id=target_member_id,
        explanation=explanation,
        intervention=dict(intervention),
        effect_summary=dict(summary),
        evidence_refs=refs,
        competing_models=competing,
        falsifier=falsifier,
        conditions=conditions,
        limitations=limitations,
    )


__all__ = [
    "LeverDossierAnswer",
    "LeverDossierError",
    "effect_summary",
    "validate_lever_dossier",
]
