"""G3's roster accounting for an inventory: which entities are levers, clean nulls and mu (R9-R23).

Author: Claude (Alpha build seat), 2026-10-03. Moved unchanged out of ``_LeverTarget._submit_inventory``
(ratchet compensation for R9-R23); RULING_MU_BUCKET_v1 makes the ambiguous class the level's mu objects.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping


def check_inventory_claims(
    raw: Mapping[str, Any],
    journal: Any,
    expected_entities: Iterable[str],
    bounded: Mapping[str, Mapping[str, Any]],
    known_refs: set[str],
    strings: Callable[..., list[str]],
    error: type[Exception],
) -> tuple[list[str], list[str], list[str], set[str], set[str], set[str], list[str]]:
    """The claimed classes must equal the journal's, and the evidence must cover each exactly."""
    expected = tuple(expected_entities)
    lever_entities = strings(raw.get("lever_entities", []), "lever_entities", required=False)
    clean_null_entities = strings(raw.get("clean_null_entities", []), "clean_null_entities", required=False)
    ambiguous_entities = strings(raw.get("ambiguous_entities", []), "ambiguous_entities", required=False)
    witnessed = {entity_id for entity_id in expected if journal.entities[entity_id].state == "G4-READY"}
    clean_null = {
        entity_id for entity_id in expected
        if journal.entities[entity_id].state == "G3-CLOSED" and not journal.entities[entity_id].witness_refs
    }
    ambiguous = {
        entity_id for entity_id in expected
        if journal.entities[entity_id].state in {"AMBIGUOUS", "BUDGET_STOPPED"}
    }
    if set(lever_entities) != witnessed:
        raise error("lever_entities must exactly match the witnessed, explained G4-ready entities.")
    if set(clean_null_entities) != clean_null:
        raise error("clean_null_entities must exactly match entities closed by scoped null evidence.")
    if set(ambiguous_entities) != ambiguous:
        raise error("ambiguous_entities must exactly match explicitly bounded unresolved entities.")
    if not witnessed and not ambiguous:
        raise error(
            "The completed interaction record contains no witnessed lever; G3 remains unanswered "
            "and the probe roster, contact execution, or attribution must be repaired."
        )
    explanation = str(raw.get("explanation") or raw.get("mechanism") or "").strip()
    evidence_refs = strings(raw.get("evidence_refs"), "evidence_refs")
    if not explanation or not evidence_refs or not strings(raw.get("competing_models"), "competing_models") \
            or not str(raw.get("falsifier") or "").strip():
        raise error("LeverInventory requires explanation, evidence_refs, competing_models, and falsifier.")
    required = {ref for entity_id in witnessed for ref in journal.entities[entity_id].witness_refs} | {
        journal.entities[entity_id].events[-1].evidence_ref
        for entity_id in clean_null if journal.entities[entity_id].events
    } | {bounded[entity_id]["evidence_ref"] for entity_id in ambiguous}
    if set(evidence_refs) != required or not set(evidence_refs) <= (known_refs | required):
        raise error(
            "G3 inventory evidence_refs must exactly cover positive witnesses, scoped nulls, "
            "and bounded ambiguities."
        )
    return lever_entities, clean_null_entities, ambiguous_entities, witnessed, clean_null, ambiguous, evidence_refs


__all__ = ["check_inventory_claims"]
