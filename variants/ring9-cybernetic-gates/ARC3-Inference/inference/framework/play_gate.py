"""Normal play after the gates, and Duck's per-level G4 turn budget (R9-R24, D20 to D22).

Author: Claude (Alpha build seat), 2026-10-04. RULING_G4_CONTROLLER_FIRST_v2_2026-10-04 (Director-ruled):

> "id say per level. we dont want to get to a level that needs the duck and not have it avaialbe. it
> should default to normal play but still have all the data gathered from the gates."

- D20 · Duck's G4-B and G4-C turns share a budget that each level opens fresh
  (``DUCK_G4_TURNS_PER_LEVEL``, one named parameter). Every Duck turn begun on a G4-B or G4-C step
  is charged, whatever the turn does (v7: 95 of 131 such turns were cut off by the turn clock).
- D21 · When the budget is spent, the gate Duck would have been woken for closes UNRESOLVED: a
  declared end with what is certified. It never loops.
- D22 · When a level's gates rest (G4-C closed, or no legal move), Duck plays the level normally:
  one action per turn, any available action, with every certified product on the card. The gates
  keep recording every transition (the G3 entity ledger and the record tier see them as before),
  and a new level opens its own ladder. The transitions are receipted FREE_PLAY (ruling R-2 of
  RULINGS_PORT_AND_PILLARS_v1). R-8: an action that already changed nothing from this exact masked
  board is refused, and the refusal says it comes from the harness, not the game.
"""
from __future__ import annotations

import hashlib
import os
from typing import Any, Mapping, Sequence

from inference.framework.cybernetic_targeting import GateAssessment, GoalContract
from inference.framework.g4_relations import masked_address, masked_changes
from inference.framework.masked_world_state import grids_from_probe_outcome
from inference.framework.virelai_gates import (
    LAW_GATE_ID, PLAY_GATE_ID, RELATION_GATE_ID, SCHEMA_VERSION, GateContractError, ProbeEnvelope, _canonical,
)

DUCK_G4_TURNS_PER_LEVEL = int(os.environ.get("VIRELAI_DUCK_G4_TURNS_PER_LEVEL", "3"))
FREE_PLAY = "FREE_PLAY"


class DuckTurnBudget:
    """D20: Duck's G4-B and G4-C turns on one level (LEVEL tier: each level opens a fresh one)."""

    def __init__(self, limit: int = DUCK_G4_TURNS_PER_LEVEL) -> None:
        self.limit = int(limit)
        self.turns: list[dict[str, Any]] = []

    @property
    def spent(self) -> bool:
        return len(self.turns) >= self.limit

    def charge(self, gate_id: str, transition_id: int) -> bool:
        if self.spent:
            return False
        self.turns.append({"gate_id": gate_id, "at_transition": int(transition_id)})
        return True

    def snapshot(self) -> dict[str, Any]:
        return {"limit": self.limit, "used": len(self.turns), "turns": [dict(item) for item in self.turns]}


def charge_or_close(machine: Any) -> str | None:
    """Before Duck is woken for G4-B or G4-C: charge one turn, or close the gate UNRESOLVED (D21)."""
    gate = machine.gate_id
    if machine.duck_budget.charge(gate, machine.observed_through_step):
        return None
    reason = (f"Duck's G4-B/G4-C budget for this level is spent ({machine.duck_budget.limit} turns); "
              f"{gate} closes UNRESOLVED with what is certified")
    machine._adapters[gate].close_unresolved(reason)
    return reason


def rest_in_play(machine: Any, reason: str) -> None:
    """D22: the level's gates rest without closing (no legal move); play on with what is certified."""
    play = machine._adapters[PLAY_GATE_ID]
    if play.forced is None:
        play.forced = reason
        play.revision += 1


def play_contract() -> GoalContract:
    return GoalContract(
        goal_id="PLAY-NORMAL-v1",
        target_id=PLAY_GATE_ID,
        question="With everything the gates certified on this level, which action wins it?",
        desired_knowledge=("the level's win, observed", "every transition recorded as FREE_PLAY"),
        prerequisites=(LAW_GATE_ID,),
        admissible_probe_kinds=("any one available action Duck chooses",),
        completion_predicate=(
            "None on this level: play continues until the level changes, which opens the next level's "
            "ladder. The gates keep recording."
        ),
        memory_product_type="none",
    )


class PlayTarget:
    TARGET = (
        "Every gate on this level has closed. Play the level to win it, using the certified world "
        "model on this card: the counter and its budget, the levers, their states now, and what each "
        "lever's recorded presses changed. One action per turn: choose any available action "
        "(ACTION6 needs row and col). Everything you do is still recorded."
    )
    RULES = (
        "Act with virelai('next_probe'), then action([one action], decision={'probe_token': ..., 'intent': ...}).",
        "The harness blocks an action that already changed nothing from this exact board, and says so; that refusal comes from the harness, not the game.",
        "Levers' state_now names which recorded content each lever shows now (S0 is the first seen on this level).",
    )

    def __init__(self, machine: Any) -> None:
        self.machine = machine
        self.revision = 1
        self.forced: str | None = None  # why the gates rested without closing (no legal move)
        self._events: list[dict[str, Any]] = []
        self._noops: dict[str, list[int]] = {}  # (action, masked board before) -> transitions that changed nothing
        self._blocked = 0
        self._rest_checked: tuple[str, ...] | None = None

    # ---- gate protocol -----------------------------------------------------------------------

    def _available(self) -> tuple[str, ...]:
        ego = self.machine.ego
        return tuple(sorted(item.action for item in ego.affordances if item.action in ego._currently_available))

    def assess(self) -> GateAssessment:
        disposition = "PROBE_REQUIRED" if self._available() else "UNRESOLVED"
        return GateAssessment(
            target_id=PLAY_GATE_ID, revision=self.revision, disposition=disposition,
            evidence_refs=tuple(item["evidence_id"] for item in self._events[-3:]),
            unmet_requirements=("win the level",), explanation=self.TARGET,
        )

    def next_probe(self) -> ProbeEnvelope | None:
        available = self._available()
        if not available:
            return None
        return ProbeEnvelope(
            probe_id=f"{PLAY_GATE_ID}:{len(self._events) + 1}",
            gate_id=PLAY_GATE_ID,
            purpose="GUIDED_ACTION",
            question=self.TARGET,
            actions=(),
            live_alternatives=("the level is won", "the board changes", "nothing changes", "a life ends"),
            outcome_partition=("recorded",),
            declared_at_transition=self.machine.observed_through_step,
            admissible_actions=available,
            target={"receipt": FREE_PLAY},
        )

    def admit(self, probe: ProbeEnvelope) -> None:
        """R-8: refuse a known no-op from this exact masked board, labelled as the harness's refusal."""
        from inference.framework.card_builder import _current_grid

        grid = _current_grid(self.machine)
        if grid is None:
            return
        earlier = self._noops.get(_canonical([dict(probe.actions[0]), masked_address(grid, self.machine.counter.mask_law)]))
        if earlier:
            self._blocked += 1
            raise GateContractError(
                f"Blocked by the harness, not the game: this action changed nothing on this same board at "
                f"t{', t'.join(str(item) for item in earlier)}. Choose a different action, or change the board first."
            )

    def validate_probe(self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]) -> ProbeEnvelope:
        raise GateContractError("Play acts through virelai('next_probe') and its token; no action is available now.")

    def record_outcome(self, probe: ProbeEnvelope, outcome: Mapping[str, Any]) -> dict[str, Any]:
        grids, law = grids_from_probe_outcome(outcome), self.machine.counter.mask_law
        key = None if grids is None else _canonical([dict(probe.actions[0]), masked_address(grids[0], law)])
        evidence_id = "E-" + hashlib.sha256(_canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()).hexdigest()[:16]
        baseline = self.machine.apply_counter_baseline({**dict(outcome), "evidence_id": evidence_id})
        boundary = outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else {}
        terminal = bool(boundary.get("game_over") or boundary.get("level_completed") or boundary.get("done"))
        changed = None if grids is None else len(masked_changes(grids[0], grids[1], law))
        if changed == 0 and not terminal and key is not None:
            self._noops.setdefault(key, []).append(int(outcome.get("transition_id") or 0))
        event = {
            "schema": SCHEMA_VERSION, "evidence_id": evidence_id, "gate_id": PLAY_GATE_ID, "receipt": FREE_PLAY,
            "probe_id": probe.probe_id, "action": dict(probe.actions[0]), "intent": probe.intent,
            "transition_id": int(outcome.get("transition_id") or 0), "masked_changed_cells": changed,
            "boundary_state": boundary.get("state"), "counter_baseline": baseline,
        }
        self._events.append(event)
        self.revision += 1
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> Any:
        raise GateContractError("Play takes no gate answer: act with virelai('next_probe').")

    def rest_check_due(self) -> bool:
        """The mu return runs once each time the ladder comes to rest on a new set of products (M-4)."""
        signature = tuple(sorted(
            product.product_id for contract in self.machine.target_registry.ordered()
            if (product := self.machine.target_journal.active_product(contract.target_id)) is not None
        ))
        due, self._rest_checked = signature != self._rest_checked, signature
        return due

    # ---- views -------------------------------------------------------------------------------

    def _certified_subject(self) -> dict[str, Any]:
        from inference.framework.g4b_gate import LEVERS_ON_CARD

        relations = self.machine._adapters[RELATION_GATE_ID]
        try:
            levers = relations._lever_rows()[:LEVERS_ON_CARD]
        except GateContractError:  # resting before G4-B could open
            levers = []
        answer = relations._answer
        law = self.machine.target_journal.active_product(LAW_GATE_ID)
        return {
            "levers": levers,
            "lever_relations": None if answer is None else answer.description,
            "lever_law": None if law is None else law.payload.get("status"),
            "open_mystery_objects": [item["entity_id"] for item in self.machine.mu.open_entries()],
        }

    def compact_gate_view(self) -> dict[str, Any]:
        assessment = self.assess()
        return {
            "schema": "virelai-play-card-v1",
            "gate_id": PLAY_GATE_ID,
            "revision": self.revision,
            "status": assessment.disposition,
            "goal_card": self.machine.target_registry.get(PLAY_GATE_ID).goal_card(status=assessment.disposition),
            "target": self.TARGET,
            "rules": list(self.RULES),
            "unmet_requirements": list(assessment.unmet_requirements),
            "why_playing": self.forced or "every gate on this level has closed",
            "subject": self._certified_subject(),
            "progress": {"play_actions": len(self._events), "blocked_no_op_attempts": self._blocked,
                         "duck_g4_turns": self.machine.duck_budget.snapshot()},
            "next_operation": "QUERY_NEXT_PROBE" if assessment.disposition == "PROBE_REQUIRED" else "WAIT_FOR_NEXT_TARGET",
            "expand": [{"label": "lever relations", "query": "virelai('relations')"}],
        }

    def snapshot(self) -> dict[str, Any]:
        return {"schema": "virelai-play-gate-v1", "gate_id": PLAY_GATE_ID, "revision": self.revision,
                "forced": self.forced, "events": list(self._events), "blocked_no_op_attempts": self._blocked}


__all__ = [
    "DUCK_G4_TURNS_PER_LEVEL", "DuckTurnBudget", "FREE_PLAY", "PlayTarget", "charge_or_close", "play_contract", "rest_in_play",
]
