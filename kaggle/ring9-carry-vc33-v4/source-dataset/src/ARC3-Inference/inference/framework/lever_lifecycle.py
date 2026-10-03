"""Per-entity G3 lifecycle journal.

The journal records who changed an entity's state and why.  Positive witnesses
are append-only; explanations and laws are versioned outside this state log.
No null observation can create an inertness claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


PRIMARY_STATES = frozenset({
    "UNTOUCHED", "ATTEMPTED", "RESPONDED", "NO_RESPONSE_YET",
    "WITNESSED", "G3-CLOSED", "G4-READY",
})
SIDE_STATES = frozenset({"AMBIGUOUS", "FILED_TO_G5", "BUDGET_STOPPED", "REOPENED"})
ALL_STATES = PRIMARY_STATES | SIDE_STATES

_ALLOWED = {
    "UNTOUCHED": frozenset({"ATTEMPTED", "AMBIGUOUS", "BUDGET_STOPPED"}),
    "ATTEMPTED": frozenset({"RESPONDED", "NO_RESPONSE_YET", "AMBIGUOUS", "FILED_TO_G5", "BUDGET_STOPPED"}),
    "RESPONDED": frozenset({"WITNESSED", "AMBIGUOUS", "FILED_TO_G5", "BUDGET_STOPPED"}),
    "NO_RESPONSE_YET": frozenset({"ATTEMPTED", "G3-CLOSED", "AMBIGUOUS", "BUDGET_STOPPED"}),
    "WITNESSED": frozenset({"G3-CLOSED", "AMBIGUOUS", "FILED_TO_G5", "BUDGET_STOPPED"}),
    "G3-CLOSED": frozenset({"G4-READY", "REOPENED"}),
    "G4-READY": frozenset({"REOPENED"}),
    "AMBIGUOUS": frozenset({"REOPENED", "ATTEMPTED", "BUDGET_STOPPED"}),
    "FILED_TO_G5": frozenset({"REOPENED"}),
    "BUDGET_STOPPED": frozenset({"REOPENED"}),
    "REOPENED": frozenset({"ATTEMPTED", "AMBIGUOUS", "BUDGET_STOPPED"}),
}


class LifecycleError(ValueError):
    """A lifecycle transition violates the per-entity contract."""


@dataclass(frozen=True)
class LifecycleEvent:
    event_id: str
    entity_id: str
    from_state: str
    to_state: str
    evidence_ref: str
    actor: str
    reason: str


@dataclass
class EntityLifecycle:
    entity_id: str
    state: str = "UNTOUCHED"
    events: list[LifecycleEvent] = field(default_factory=list)
    witness_refs: list[str] = field(default_factory=list)
    answer_refs: list[str] = field(default_factory=list)
    law_version_ids: list[str] = field(default_factory=list)


class LifecycleJournal:
    """Append-only state journal with entity-local reopening."""

    def __init__(self, entity_ids: Iterable[str] = ()) -> None:
        self.entities: dict[str, EntityLifecycle] = {}
        self._serial = 0
        for entity_id in entity_ids:
            self.register(entity_id)

    def register(self, entity_id: str) -> EntityLifecycle:
        normalized = str(entity_id or "").strip()
        if not normalized:
            raise LifecycleError("entity_id is required")
        return self.entities.setdefault(normalized, EntityLifecycle(normalized))

    def transition(
        self,
        entity_id: str,
        to_state: str,
        *,
        evidence_ref: str,
        actor: str,
        reason: str,
    ) -> LifecycleEvent:
        entity = self.register(entity_id)
        target = str(to_state or "").strip().upper()
        if target not in ALL_STATES:
            raise LifecycleError(f"unknown lifecycle state: {to_state!r}")
        if not str(evidence_ref or "").strip():
            raise LifecycleError("every lifecycle transition requires evidence_ref")
        if not str(actor or "").strip() or not str(reason or "").strip():
            raise LifecycleError("every lifecycle transition requires actor and reason")
        if target not in _ALLOWED[entity.state]:
            raise LifecycleError(f"illegal transition {entity.state} -> {target} for {entity_id}")
        self._serial += 1
        event = LifecycleEvent(
            event_id=f"LC-{self._serial:05d}",
            entity_id=entity.entity_id,
            from_state=entity.state,
            to_state=target,
            evidence_ref=str(evidence_ref),
            actor=str(actor),
            reason=str(reason),
        )
        entity.events.append(event)
        entity.state = target
        return event

    def attempt(self, entity_id: str, *, evidence_ref: str, actor: str = "G3_ROUTER") -> LifecycleEvent:
        return self.transition(entity_id, "ATTEMPTED", evidence_ref=evidence_ref, actor=actor, reason="authorized target attempt")

    def response(self, entity_id: str, *, positive: bool, evidence_ref: str, actor: str = "G3_OBSERVER") -> LifecycleEvent:
        return self.transition(
            entity_id,
            "RESPONDED" if positive else "NO_RESPONSE_YET",
            evidence_ref=evidence_ref,
            actor=actor,
            reason="attributed response" if positive else "scoped null observation",
        )

    def witness(self, entity_id: str, *, witness_ref: str, actor: str = "G3_ATTRIBUTOR") -> LifecycleEvent:
        entity = self.register(entity_id)
        if entity.state != "RESPONDED":
            raise LifecycleError("only a responded entity can receive a G3 witness")
        entity.witness_refs.append(str(witness_ref))
        return self.transition(entity_id, "WITNESSED", evidence_ref=witness_ref, actor=actor, reason="immutable positive lever witness")

    def close(self, entity_id: str, *, evidence_ref: str, actor: str = "G3_ROUTER") -> LifecycleEvent:
        entity = self.register(entity_id)
        if entity.state not in {"WITNESSED", "NO_RESPONSE_YET"}:
            raise LifecycleError("G3 closes only after a witness or scoped no-response observation")
        return self.transition(entity_id, "G3-CLOSED", evidence_ref=evidence_ref, actor=actor, reason="entity G3 obligations complete")

    def ready_for_g4(self, entity_id: str, *, evidence_ref: str) -> LifecycleEvent:
        entity = self.register(entity_id)
        if entity.state != "G3-CLOSED" or not entity.witness_refs or not entity.answer_refs:
            raise LifecycleError(
                "G4 readiness requires a closed positive witness and an evidence-bound G3 answer"
            )
        return self.transition(entity_id, "G4-READY", evidence_ref=evidence_ref, actor="G3_ROUTER", reason="G3 dossier handed to causal expansion")

    def answer(self, entity_id: str, *, answer_ref: str) -> None:
        entity = self.register(entity_id)
        normalized = str(answer_ref or "").strip()
        if not normalized:
            raise LifecycleError("answer_ref is required")
        if normalized not in entity.answer_refs:
            entity.answer_refs.append(normalized)

    def reopen(self, entity_id: str, *, evidence_ref: str, reason: str) -> LifecycleEvent:
        return self.transition(entity_id, "REOPENED", evidence_ref=evidence_ref, actor="CONTRADICTION_MONITOR", reason=reason)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "virelai-g3-lifecycle-journal-v1",
            "entity_count": len(self.entities),
            "state_counts": {
                state: sum(item.state == state for item in self.entities.values())
                for state in sorted(ALL_STATES)
            },
            "entities": {
                entity_id: {
                    "state": item.state,
                    "witness_refs": list(item.witness_refs),
                    "answer_refs": list(item.answer_refs),
                    "law_version_ids": list(item.law_version_ids),
                    "events": [asdict(event) for event in item.events],
                }
                for entity_id, item in sorted(self.entities.items())
            },
        }


__all__ = ["ALL_STATES", "EntityLifecycle", "LifecycleError", "LifecycleEvent", "LifecycleJournal"]
