"""The life record: every recorded transition knows its life and level; a harness reset is a row.

Author: Claude (Alpha build seat), 2026-10-01. R9-R16 (MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4, D1,
D2 and D4; Director rulings 2026-10-01: life record first, carry hypotheses only).

Ported from two precedents, never from either's world content:

- golden's whole-game record (``golden/substrate/record.py``): the record is never wiped inside a
  game, and every node carries its ``life``;
- virelai_v4's Groundhog Day (``virelai_v4/context.py``): one context lives for the whole game and
  each field is declared in a persistence tier, so what a death forgets is a written decision.

A death forgets nothing here: the gate machine lives for the whole game, and a reset only adds a
row and opens the next life. A level change freezes the LEVEL tier into the level's model and
rebuilds it for the next level (R9-R17, ``CyberneticGateMachine._build_level``).
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework.g4_guided import level_changed

GAME, LEVEL, TRANSIENT = "GAME", "LEVEL", "TRANSIENT"

# Every attribute of the gate machine and its gate targets, by how long it is true (D4).
# GAME: the whole game, across lives and levels. LEVEL: one level, across its lives; frozen as the
# level's model when the level ends (R9-R17), carried to the next only as hypotheses (ruling
# 2026-10-01). TRANSIENT: an in-flight probe or answer, resolved by its own outcome or boundary.
PERSISTENCE: dict[str, dict[str, str]] = {
    "CyberneticGateMachine": {
        "_capability_secret": GAME, "_consumed_capabilities": GAME, "protocol": GAME,
        "transition_index": GAME, "lives": GAME, "levels": GAME, "_adapters": LEVEL, "_issued_capabilities": LEVEL,
        "target_registry": LEVEL, "target_router": LEVEL, "target_journal": LEVEL, "carry": LEVEL,
        "annotations": LEVEL, "_g0": LEVEL, "ego": LEVEL, "counter": LEVEL, "mu": LEVEL,
        "_counter_prepared_from_ego": LEVEL,
    },
    "_ActionSurfaceTarget": {"machine": GAME, "answer": LEVEL, "revision": LEVEL},
    "_EgoTarget": {"machine": GAME},
    "_CounterTarget": {"machine": GAME},
    "_LeverTarget": {
        "machine": GAME, "revision": LEVEL, "entity_ledger": LEVEL, "evidence": LEVEL,
        "lifecycle_journal": LEVEL, "_bounded_ambiguities": LEVEL, "_bounded_coverage_answer": LEVEL,
        "_complete_reason": LEVEL, "_confirmation_records": LEVEL, "_deferred_observations": LEVEL,
        "_repeat_readings": LEVEL, "_mu_revisit": LEVEL,
        "_dossier_answers": LEVEL, "_eligible_frontier": LEVEL, "_excluded_frontier": LEVEL,
        "_frontier_mask_version": LEVEL, "_inheritance": LEVEL, "_inventory_answer": LEVEL,
        "_navigation_limit": LEVEL, "_observed_transition_ids": LEVEL, "_target_index": LEVEL,
        "_phase": LEVEL, "_probe_serial": LEVEL, "_navigation_steps": TRANSIENT,
        "_pending_confirmation": TRANSIENT, "_pending_dossier": TRANSIENT,
    },
    "_ReactionTarget": {
        "machine": GAME, "revision": LEVEL, "_anatomies": LEVEL, "_answers": LEVEL, "_ordered_entities": LEVEL,
        "_seeded_from": LEVEL,
    },
    "_LeverStudyTarget": {
        "machine": GAME, "revision": LEVEL, "_action_count": LEVEL, "_answers": LEVEL, "_completed": LEVEL,
        "_events": LEVEL, "_interruptions": LEVEL, "_interventions": LEVEL, "_level_closed": LEVEL,
        "_life_restudies": LEVEL, "_ordered_entities": LEVEL, "_runs": LEVEL, "_active_run": TRANSIENT,
        "_seeded_from": LEVEL,
    },
    "LeverRelationsTarget": {
        "machine": GAME, "revision": LEVEL, "_answer": LEVEL, "_events": LEVEL, "_level_closed": LEVEL,
        "_predictions": LEVEL, "_record": LEVEL, "_regions": LEVEL, "_reopened": LEVEL, "_pending": TRANSIENT,
    },
    "LeverLawTarget": {
        "machine": GAME, "revision": LEVEL, "_certified": LEVEL, "_events": LEVEL, "_level_closed": LEVEL,
        "_tests": LEVEL, "_pending": TRANSIENT,
    },
}


class LifeRecord:
    """Lives and levels over the whole game; the machine's high-water transition (R9-R14, F2)."""

    def __init__(self) -> None:
        self.life = 1
        self.level: int | None = 1  # a game starts on level 1; a boundary's level_before overrides it
        self.high_step = 0
        self._resets: set[int] = set()
        self.lives: list[dict[str, Any]] = [_life(1, 1)]

    def tag(self, row: dict[str, Any], outcome: Mapping[str, Any]) -> dict[str, Any]:
        """Stamp a recorded transition with its life and level; note a death or a level change."""
        transition_id = int(outcome.get("transition_id") or 0)
        self.high_step = max(self.high_step, transition_id)
        boundary = outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else {}
        if boundary.get("level_before") is not None and boundary["level_before"] != self.level:
            self.level = self.lives[-1]["level"] = int(boundary["level_before"])
        current = self.lives[-1]
        current["first_transition"] = current["first_transition"] or transition_id
        current["last_transition"], current["transitions"] = transition_id, current["transitions"] + 1
        row.update(kind="PROBE", life=self.life, level=self.level)
        if boundary.get("game_over"):
            current["ended_by"] = "GAME_OVER"
        if level_changed(boundary) and boundary.get("level_after") is not None:
            current.setdefault("level_changes", []).append(transition_id)
            self.level = int(boundary["level_after"])
        return row

    def reset(self, outcome: Mapping[str, Any], gate_id: str) -> dict[str, Any] | None:
        """A harness reset ends this life and opens the next; ``None`` if it is already recorded."""
        transition_id = int(outcome.get("transition_id") or 0)
        if transition_id in self._resets:
            return None
        self._resets.add(transition_id)
        self.high_step = max(self.high_step, transition_id)
        ended = self.lives[-1]
        ended["ended_by"] = ended["ended_by"] or "RESET"
        ended["reset_transition"] = transition_id
        self.life += 1
        self.lives.append(_life(self.life, self.level))
        changed = [
            [int(cell["row"]), int(cell["col"]), cell.get("before"), cell.get("after")]
            for cell in outcome.get("changed_cells") or () if isinstance(cell, Mapping)
        ]
        return {
            "transition_id": transition_id, "kind": "RESET", "gate_id": gate_id, "probe_id": None,
            "evidence_id": None, "action": {"action": "RESET"}, "acted_site": None, "changed": changed,
            "boundary_state": "RESET", "disposition": None, "life": self.life, "level": self.level,
        }

    def summary(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.lives]


def _life(number: int, level: int | None) -> dict[str, Any]:
    return {"life": number, "level": level, "first_transition": None, "last_transition": None,
            "transitions": 0, "ended_by": None, "reset_transition": None}


def undeclared(owner: Any) -> list[str]:
    """Attributes of a gate machine or target with no declared persistence tier (D4)."""
    declared = PERSISTENCE.get(type(owner).__name__)
    if declared is None:
        return [f"{type(owner).__name__} (no tier table)"]
    return sorted(name for name in vars(owner) if name not in declared)


__all__ = ["GAME", "LEVEL", "LifeRecord", "PERSISTENCE", "TRANSIENT", "undeclared"]
