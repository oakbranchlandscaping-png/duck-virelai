"""G3's repeat press: graded against its frozen prediction, then read as typing evidence (R9-R22, D7).

Author: Claude (Alpha build seat), 2026-10-03. DIAGNOSTIC_G3_G4_LEVER_TYPING_BOUNDARY_v1.

After a positive witness, G3 presses the same click once more and predicts the witness's cells. The
grading is kept exactly as before (SUPPORTED / CONTRADICTED / BOUNDARY_DEFERRED): it is an honest record
of a frozen prediction. What changed is what the grade decides. G3 discovers levers and G4 types them
(FOUNDATIONAL_ARCHETYPES_v2 §3: the repetition law and saturation are subtree questions;
lever_attribution: silence never retracts an earlier witness). So in the click lane a repeat press
outside a boundary certifies the lever, and its outcome is read in G4-A's own orbit vocabulary over the
attributed residue cells (counter-masked, ego excluded):

- NULL_AT_OBSERVED_STATE: the repeat changed nothing; the lever moved, then held.
- OBSERVED_STATE_RECURRENCE: the repeat exactly undid the witness; the board returned (period 2).
- NOVEL_STATE_REVEALED: the repeat changed the board again, to a third state.
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework.lever_attribution import LeverAttribution


def grade_confirmation(
    pending: Mapping[str, Any] | None,
    attribution: LeverAttribution,
    *,
    evidence_id: str,
    target_member_id: str,
    entity_id: str | None,
    transition_id: int,
) -> dict[str, Any]:
    """The confirmation record: the frozen prediction and its grade (moved unchanged from G3, R9-R22)."""
    local = set(pending["local_cells"]) if pending else set()
    remote = set(pending["remote_cells"]) if pending else set()
    supported = attribution.positive and bool(
        set(attribution.local_residue_cells) & local or set(attribution.remote_residue_cells) & remote
    )
    return {
        "witness_evidence_ref": pending["witness_evidence_ref"] if pending else None,
        "confirmation_evidence_ref": evidence_id,
        "target_member_id": target_member_id,
        "entity_id": entity_id,
        "declared_at_transition": int(pending["declared_at_transition"]) if pending else None,
        "graded_at_transition": int(transition_id),
        "frozen_target": dict(pending["target"]) if pending else {},
        "predicted_local_cells": [list(cell) for cell in pending["local_cells"]] if pending else [],
        "predicted_remote_cells": [list(cell) for cell in pending["remote_cells"]] if pending else [],
        "status": (
            "SUPPORTED" if supported
            else "BOUNDARY_DEFERRED" if attribution.boundary_state
            else "CONTRADICTED"
        ),
    }


def _residue_changes(attribution: LeverAttribution) -> dict[tuple[int, int], tuple[Any, Any]]:
    residue = set(attribution.residue_cells)
    return {
        (int(row), int(col)): (before, after)
        for row, col, before, after in attribution.changed_cells
        if (int(row), int(col)) in residue
    }


def repeat_disposition(witness: LeverAttribution, repeat: LeverAttribution) -> str:
    """The orbit step the repeat press took, from the witness's after-state."""
    again = _residue_changes(repeat)
    if not again:
        return "NULL_AT_OBSERVED_STATE"
    first = _residue_changes(witness)
    undone = again.keys() == first.keys() and all(
        again[cell] == (after, before) for cell, (before, after) in first.items()
    )
    return "OBSERVED_STATE_RECURRENCE" if undone else "NOVEL_STATE_REVEALED"


def repeat_reading(
    record: Mapping[str, Any], witness: LeverAttribution, repeat: LeverAttribution
) -> dict[str, Any]:
    """One lever's witness and repeat press, kept as typing evidence for G4-A."""
    return {
        "witness_evidence_ref": record["witness_evidence_ref"],
        "confirmation_evidence_ref": record["confirmation_evidence_ref"],
        "repeat_disposition": repeat_disposition(witness, repeat),
        "prediction_status": record["status"],
    }


def certified(record: Mapping[str, Any], readings: Mapping[str, Mapping[str, Any]]) -> bool:
    """Whether this confirmation record certified its lever: supported, or read as a repeat (D7)."""
    reading = readings.get(str(record.get("entity_id") or "")) or {}
    ref = record.get("confirmation_evidence_ref")
    return record.get("status") == "SUPPORTED" or (bool(ref) and reading.get("confirmation_evidence_ref") == ref)


__all__ = ["certified", "grade_confirmation", "repeat_disposition", "repeat_reading"]
