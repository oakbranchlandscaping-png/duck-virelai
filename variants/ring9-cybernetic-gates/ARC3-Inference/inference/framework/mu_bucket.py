"""The mu bucket: objects that stump a gate, kept so they never stop the ladder (R9-R23).

Author: Claude (Alpha build seat), 2026-10-03. RULING_MU_BUCKET_v1_2026-10-03 (Director-ruled).

A mu entry is an open question, not a verdict: no role tag, no inertness claim. It records why a gate
could not answer, the evidence, the counter-masked board it was tried on, and what would justify a
retry. Gates close PARTIAL around mu entries (M-2). When the ladder is otherwise stuck, the controller
returns to the bucket, but only to entries whose board has changed since every earlier try (M-4): a
changed board is the new information; an unchanged one would spend a scored action to learn nothing.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

OPEN = "OPEN"
RESOLVED_LEVER = "RESOLVED_LEVER"
RESOLVED_NULL = "RESOLVED_NULL_AT_STATE"
ABSENT = "ABSENT"  # the object no longer occupies any cell: nothing left to retry


class MuBucket:
    """One level's mystery objects (LEVEL tier; frozen into the level's model when the level ends)."""

    def __init__(self) -> None:
        self.entries: dict[str, dict[str, Any]] = {}

    def file(self, record: Mapping[str, Any], *, gate_id: str, tried_address: str | None,
             transition_id: int, clicked_owner: str | None = None) -> dict[str, Any]:
        """Put a stumping object in the bucket, or add one more try to its entry."""
        entity_id = str(record["entity_id"])
        entry = self.entries.setdefault(entity_id, {
            "schema": "virelai-mu-entry-v1", "entity_id": entity_id, "gate_id": gate_id,
            "member_id": record.get("target_member_id"), "status": OPEN, "tries": [],
            "inertness_claim_permitted": False, "retry_condition": record.get("retry_condition"),
        })
        entry["status"] = OPEN
        entry["tries"].append({
            "transition_id": int(transition_id), "evidence_ref": record.get("evidence_ref"),
            "disposition": record.get("disposition"), "reason": record.get("reason"),
            "tried_address": tried_address, "clicked_owner": clicked_owner,
        })
        return entry

    def open_entries(self) -> list[dict[str, Any]]:
        return [entry for entry in self.entries.values() if entry["status"] == OPEN]

    def revisitable(self, address: str | None) -> list[dict[str, Any]]:
        """Open entries never tried on this board (M-4); none when the board cannot be read."""
        if address is None:
            return []
        return [
            entry for entry in self.open_entries()
            if all(item.get("tried_address") != address for item in entry["tries"])
        ]

    def settle(self, entity_id: str, status: str, note: str) -> None:
        entry = self.entries.get(entity_id)
        if entry is not None and entry["status"] == OPEN:
            entry["status"], entry["settled_because"] = status, note

    def snapshot(self) -> list[dict[str, Any]]:
        return [dict(entry, tries=[dict(item) for item in entry["tries"]]) for entry in self.entries.values()]

    def entity_ids(self, statuses: Iterable[str] = (OPEN,)) -> list[str]:
        wanted = set(statuses)
        return [entity for entity, entry in self.entries.items() if entry["status"] in wanted]


__all__ = ["ABSENT", "MuBucket", "OPEN", "RESOLVED_LEVER", "RESOLVED_NULL"]
