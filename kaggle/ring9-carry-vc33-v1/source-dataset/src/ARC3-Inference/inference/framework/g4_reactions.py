"""Evidence-bound G4 reaction anatomy for confirmed G3 levers.

G3 proves that an intervention has a non-counter world effect.  This module
starts the deeper study without replaying the broad search: it partitions the
exact G3 residue into spatial effect channels and requires Duck to explain the
controller-supplied arithmetic in ordinary language.  It deliberately makes
no claims yet about repetition, reversibility, conditions, coupling, or an
object identity through time; those are later G4 subtrees.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

from inference.framework.lever_attribution import LeverAttribution


class G4ReactionError(ValueError):
    """The proposed G4 anatomy or explanation is not evidence-bound."""


Cell = tuple[int, int]
Change = tuple[int, int, int | None, int | None]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _components(cells: Iterable[Cell]) -> tuple[tuple[Cell, ...], ...]:
    remaining = set(cells)
    found: list[tuple[Cell, ...]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        frontier = [seed]
        component = {seed}
        while frontier:
            row, col = frontier.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        found.append(tuple(sorted(component)))
    return tuple(sorted(found, key=lambda item: (item[0], len(item))))


@dataclass(frozen=True)
class EffectChannel:
    channel_id: str
    locality: str
    transform: str
    changed_cell_count: int
    cells: tuple[Cell, ...]
    bbox: tuple[int, int, int, int]
    integer_transitions: tuple[tuple[int | None, int | None, int], ...]
    signed_integer_delta: int | None


@dataclass(frozen=True)
class LeverEffectAnatomy:
    anatomy_id: str
    entity_id: str
    target_member_id: str
    intervention: Mapping[str, Any]
    witness_evidence_ref: str
    confirmation_evidence_ref: str
    dossier_answer_ref: str
    attribution_id: str
    mask_law_version_id: str | None
    residue_cell_count: int
    local_residue_cell_count: int
    remote_residue_cell_count: int
    channels: tuple[EffectChannel, ...]
    coverage_complete: bool
    open_questions: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class LeverReactionAnswer:
    answer_id: str
    answer_kind: str
    entity_id: str
    target_member_id: str
    intervention: Mapping[str, Any]
    effect_channels: tuple[Mapping[str, Any], ...]
    mechanism_explanation: str
    evidence_refs: tuple[str, ...]
    record_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]


def anatomy_payload(anatomy: LeverEffectAnatomy, *, include_cells: bool = True) -> dict[str, Any]:
    payload = asdict(anatomy)
    if not include_cells:
        for channel in payload["channels"]:
            channel.pop("cells", None)
            channel["detail_query"] = f"virelai('reaction', id={anatomy.entity_id!r})"
    return payload


def compile_effect_anatomy(
    attribution: LeverAttribution,
    *,
    entity_id: str,
    intervention: Mapping[str, Any],
    confirmation_evidence_ref: str,
    dossier_answer_ref: str,
    mask_law_version_id: str | None,
) -> LeverEffectAnatomy:
    """Decompose every non-counter residue cell into exact spatial channels."""
    if not attribution.positive:
        raise G4ReactionError("G4 can bind only a positive G3 lever attribution.")
    entity = str(entity_id or "").strip()
    if not entity:
        raise G4ReactionError("entity_id is required")
    if not intervention:
        raise G4ReactionError("the accepted G3 intervention is required")
    confirmation = str(confirmation_evidence_ref or "").strip()
    dossier_ref = str(dossier_answer_ref or "").strip()
    if not confirmation or not dossier_ref:
        raise G4ReactionError("supported confirmation and accepted dossier references are required")

    changes: dict[Cell, tuple[int | None, int | None]] = {
        (row, col): (before, after)
        for row, col, before, after in attribution.changed_cells
    }
    residue = set(attribution.residue_cells)
    if missing := sorted(residue - set(changes)):
        raise G4ReactionError(f"residue cells lack exact before/after values: {missing!r}")
    if residue & set(attribution.counter_masked_cells):
        raise G4ReactionError("counter cells cannot enter G4 effect anatomy")

    local = set(attribution.local_residue_cells)
    remote = set(attribution.remote_residue_cells)
    if local | remote != residue or local & remote:
        raise G4ReactionError("local and remote residue must form an exact disjoint partition")

    channels: list[EffectChannel] = []
    for locality, scoped_cells in (("LOCAL", local), ("REMOTE", remote)):
        for component in _components(scoped_cells):
            counts: dict[tuple[int | None, int | None], int] = {}
            for cell in component:
                counts[changes[cell]] = counts.get(changes[cell], 0) + 1
            transitions = tuple(
                (before, after, count)
                for (before, after), count in sorted(
                    counts.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))
                )
            )
            transform = "UNIFORM_VALUE_REWRITE" if len(transitions) == 1 else "COORDINATED_VALUE_REWRITE"
            deltas = [
                (after - before) * count
                for before, after, count in transitions
                if before is not None and after is not None
            ]
            signed_delta = sum(deltas) if len(deltas) == len(transitions) else None
            rows = [cell[0] for cell in component]
            cols = [cell[1] for cell in component]
            channel_seed = {
                "entity": entity,
                "locality": locality,
                "cells": component,
                "transitions": transitions,
            }
            channels.append(EffectChannel(
                channel_id="CH-" + hashlib.sha256(_canonical(channel_seed).encode()).hexdigest()[:12],
                locality=locality,
                transform=transform,
                changed_cell_count=len(component),
                cells=component,
                bbox=(min(rows), min(cols), max(rows), max(cols)),
                integer_transitions=transitions,
                signed_integer_delta=signed_delta,
            ))
    channels.sort(key=lambda item: (item.locality, item.bbox, item.channel_id))
    covered = {cell for channel in channels for cell in channel.cells}
    coverage_complete = covered == residue and sum(len(item.cells) for item in channels) == len(residue)
    if not coverage_complete:
        raise G4ReactionError("effect channels do not exactly cover the G3 residue")

    seed = {
        "entity": entity,
        "attribution": attribution.attribution_id,
        "confirmation": confirmation,
        "channels": [asdict(item) for item in channels],
    }
    return LeverEffectAnatomy(
        anatomy_id="G4A-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16],
        entity_id=entity,
        target_member_id=attribution.target_member_id,
        intervention=dict(intervention),
        witness_evidence_ref=attribution.evidence_ref,
        confirmation_evidence_ref=confirmation,
        dossier_answer_ref=dossier_ref,
        attribution_id=attribution.attribution_id,
        mask_law_version_id=mask_law_version_id,
        residue_cell_count=len(residue),
        local_residue_cell_count=len(local),
        remote_residue_cell_count=len(remote),
        channels=tuple(channels),
        coverage_complete=True,
        open_questions=(
            "REPETITION_LAW", "LIMITS_AND_REVERSAL", "CONDITIONS",
            "COUPLINGS", "PROSPECTIVE_MECHANISM_DEMONSTRATION",
        ),
        limitations=(
            "This slice describes the witnessed transition, not a repeated reaction law.",
            "Spatial channels are affected regions; persistent responder identity is not yet claimed.",
            "Movement, growth, shrinkage, toggling, conditions, and reversibility remain unproven.",
        ),
    )


def validate_reaction_answer(raw: Mapping[str, Any], anatomy: LeverEffectAnatomy) -> LeverReactionAnswer:
    """Require Duck to use every exact channel while explaining the observed effect."""
    if str(raw.get("answer_kind") or "").strip().upper() != "LEVER_EFFECT_ANATOMY":
        raise G4ReactionError("answer_kind must be LEVER_EFFECT_ANATOMY")
    if str(raw.get("entity_id") or "").strip() != anatomy.entity_id:
        raise G4ReactionError("entity_id must match the binding G4 lever")
    if _canonical(raw.get("intervention")) != _canonical(anatomy.intervention):
        raise G4ReactionError("intervention must exactly preserve the accepted G3 intervention")

    expected_channels = anatomy_payload(anatomy, include_cells=False)["channels"]
    supplied_channels = raw.get("effect_channels")
    if _canonical(supplied_channels) != _canonical(expected_channels):
        raise G4ReactionError("effect_channels must exactly preserve the controller-compiled anatomy")
    evidence_refs = tuple(str(item) for item in raw.get("evidence_refs") or ())
    expected_evidence = (anatomy.witness_evidence_ref, anatomy.confirmation_evidence_ref)
    if evidence_refs != expected_evidence:
        raise G4ReactionError("evidence_refs must be the witness and confirmation in binding order")
    record_refs = tuple(str(item) for item in raw.get("record_refs") or ())
    if record_refs != (anatomy.dossier_answer_ref, anatomy.anatomy_id):
        raise G4ReactionError("record_refs must preserve the accepted dossier and compiled anatomy")

    explanation = str(raw.get("mechanism_explanation") or raw.get("explanation") or "").strip()
    if len(explanation) < 40:
        raise G4ReactionError("mechanism_explanation must describe the affected regions and exact rewrites")
    lowered = explanation.lower()
    if anatomy.entity_id.lower() not in lowered:
        raise G4ReactionError("mechanism_explanation must name the lever entity")
    for channel in anatomy.channels:
        if channel.channel_id.lower() not in lowered:
            raise G4ReactionError(f"mechanism_explanation must discuss channel {channel.channel_id}")
        for before, after, _count in channel.integer_transitions:
            token = f"{before}->{after}".lower()
            spaced = f"{before} -> {after}".lower()
            if token not in lowered and spaced not in lowered:
                raise G4ReactionError(
                    f"mechanism_explanation must state exact rewrite {before}->{after} for {channel.channel_id}"
                )
    competing = tuple(str(item).strip() for item in raw.get("competing_models") or () if str(item).strip())
    falsifier = str(raw.get("falsifier") or "").strip()
    if not competing or not falsifier:
        raise G4ReactionError("competing_models and falsifier are required")
    limitations = tuple(str(item).strip() for item in raw.get("limitations") or () if str(item).strip())
    answer_id = str(raw.get("answer_id") or "").strip()
    if not answer_id:
        seed = {"anatomy": anatomy.anatomy_id, "explanation": explanation}
        answer_id = "G4-ANSWER-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16]
    return LeverReactionAnswer(
        answer_id=answer_id,
        answer_kind="LEVER_EFFECT_ANATOMY",
        entity_id=anatomy.entity_id,
        target_member_id=anatomy.target_member_id,
        intervention=dict(anatomy.intervention),
        effect_channels=tuple(dict(item) for item in expected_channels),
        mechanism_explanation=explanation,
        evidence_refs=evidence_refs,
        record_refs=record_refs,
        competing_models=competing,
        falsifier=falsifier,
        limitations=limitations,
    )
