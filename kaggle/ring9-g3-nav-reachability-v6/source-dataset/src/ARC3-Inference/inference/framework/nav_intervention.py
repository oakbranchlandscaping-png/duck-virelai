"""Branch-neutral intervention identities and NAV contact epochs.

The final movement token is not a NAV lever identity: many targets can share
it.  These immutable records bind evidence to the target and keep approach
transitions separate from the terminal contact transition.

Author: Sol (Alpha build seat), 2026-10-01.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


def _id(prefix: str, value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return prefix + hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class InterventionRef:
    kind: str
    entity_id: str
    action: tuple[tuple[str, Any], ...] = ()
    procedure_id: str | None = None

    @classmethod
    def click(cls, entity_id: str, action: Mapping[str, Any]) -> "InterventionRef":
        return cls("CLICK", str(entity_id), tuple(sorted(action.items())))

    @classmethod
    def nav(cls, entity_id: str, procedure_id: str) -> "InterventionRef":
        return cls("NAV", str(entity_id), procedure_id=str(procedure_id))

    def payload(self) -> dict[str, Any]:
        if self.kind == "CLICK":
            return {"kind": self.kind, "entity_id": self.entity_id, "action": dict(self.action)}
        return {"kind": self.kind, "entity_id": self.entity_id, "procedure_id": self.procedure_id}


@dataclass(frozen=True)
class ContactProcedure:
    procedure_id: str
    target_entity_id: str
    ego_entity_ids: tuple[str, ...]
    target_cells: tuple[tuple[int, int], ...]
    allowed_actions: tuple[str, ...]
    level: int
    life: int

    @classmethod
    def create(cls, *, target_entity_id: str, ego_entity_ids=(), target_cells=(),
               allowed_actions=(), level=1, life=1) -> "ContactProcedure":
        seed = {
            "target": target_entity_id, "ego": sorted(ego_entity_ids),
            "cells": sorted(tuple(map(int, cell)) for cell in target_cells),
            "actions": sorted(map(str, allowed_actions)), "level": level, "life": life,
        }
        return cls(_id("NAVP-", seed), str(target_entity_id), tuple(sorted(map(str, ego_entity_ids))),
                   tuple(seed["cells"]), tuple(seed["actions"]), int(level), int(life))

    @property
    def intervention(self) -> InterventionRef:
        return InterventionRef.nav(self.target_entity_id, self.procedure_id)


@dataclass(frozen=True)
class ContactEpoch:
    epoch_id: str
    procedure_id: str
    target_entity_id: str
    route_evidence_refs: tuple[str, ...]
    contact_evidence_ref: str
    final_action: str
    stand: tuple[int, int] | None
    outcome: str
    before_world_address: str | None = None
    after_world_address: str | None = None

    @classmethod
    def create(cls, *, procedure: ContactProcedure, route_evidence_refs=(),
               contact_evidence_ref: str, final_action: str, stand, outcome: str,
               before_world_address=None, after_world_address=None) -> "ContactEpoch":
        seed = {"procedure": procedure.procedure_id, "contact": contact_evidence_ref}
        return cls(_id("NAVE-", seed), procedure.procedure_id, procedure.target_entity_id,
                   tuple(map(str, route_evidence_refs)), str(contact_evidence_ref), str(final_action),
                   None if stand is None else tuple(map(int, stand)), str(outcome),
                   before_world_address, after_world_address)

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["ContactEpoch", "ContactProcedure", "InterventionRef"]
