"""A stress world and a card-only simulated Duck, for memory stage M-1 (R9-R07).

Author: Claude (Alpha build seat), 2026-09-29.

The stress world is synthetic and game-free: N small lever tiles that recolour themselves when
clicked, a few inert blocks, and a bookkeeping bar that ticks on every effective click. N is the
dial: the card must not grow with it (memory law M4).

The simulated Duck reads **only the card** — the exact payload the production prompt carries — and
answers or acts from it. If a gate needed something the card does not show, this Duck could not
finish; that is the point (M5: the present is never hidden).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from inference.framework.annotation_lane import submit_notes
from inference.framework.card_builder import CERTIFIED, build_card
from inference.framework.record_replay import click_world_machine, lossless_outcome

SIZE = 64
BAR_ROW = 63
BAR, BAR_SPENT = 12, 11
LEVER_ON, LEVER_OFF = 9, 8
INERT = 3
COUNTER_WORDS = "the bar counter changes were excluded by the mask as bookkeeping"


@dataclass
class StressWorld:
    levers: int
    inert: int = 4
    wide_last: bool = False  # the last lever is 2x3 instead of 2x2: one differing signature
    grid: list[list[int]] = field(default_factory=list)
    anchors: list[tuple[int, int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        for col in range(SIZE):
            self.grid[BAR_ROW][col] = BAR
        for index in range(self.levers):
            row, col = 2 + (index // 10) * 5, 2 + (index % 10) * 5
            self.anchors.append((row, col))
            for r in range(row, row + 2):
                for c in range(col, col + self._width(index)):
                    self.grid[r][c] = LEVER_ON
        for index in range(self.inert):
            row, col = 40, 2 + index * 6
            for r in range(row, row + 3):
                for c in range(col, col + 3):
                    self.grid[r][c] = INERT

    def _width(self, index: int) -> int:
        return 3 if self.wide_last and index == self.levers - 1 else 2

    def lever_at(self, row: int, col: int) -> tuple[int, int] | None:
        for index, (r0, c0) in enumerate(self.anchors):
            if r0 <= row < r0 + 2 and c0 <= col < c0 + self._width(index):
                return r0, c0
        return None

    def changes(self, action: dict[str, Any]) -> list[list[int]]:
        hit = self.lever_at(int(action["row"]), int(action["col"]))
        if hit is None:
            return []
        r0, c0 = hit
        width = self._width(self.anchors.index(hit))
        before = self.grid[r0][c0]
        after = LEVER_OFF if before == LEVER_ON else LEVER_ON
        changed = [[r, c, before, after] for r in range(r0, r0 + 2) for c in range(c0, c0 + width)]
        remaining = sorted(c for c in range(SIZE) if self.grid[BAR_ROW][c] == BAR)[-2:]
        return changed + [[BAR_ROW, c, BAR, BAR_SPENT] for c in remaining]


def _g2_answer(card: dict[str, Any], world: StressWorld, clicked: set[tuple[int, int]]) -> dict[str, Any]:
    template = card["answer_template"]
    subject = card.get("subject") or {}
    trigger = (subject.get("record_trigger") or {}).get("admissible_claims") or [template.get("trigger")]
    candidate = subject.get("counter_candidate") or {}
    amount = max(candidate.get("amount_per_transition") or [2])
    target = next((anchor for anchor in world.anchors if anchor not in clicked), world.anchors[0])
    return {
        **template,
        "trigger": trigger[0],
        "tracked_variable": "a bar that counts board-changing clicks",
        "mechanism": "bar cells rewrite on each click that changes the board",
        "bookkeeping_reason": "the bar changes identically for different clicked objects",
        "competing_models": ["the bar is a remote effect of particular objects"],
        "falsifier": "an effective click leaves the bar unchanged",
        "novel_prediction": {
            **template["novel_prediction"],
            "action": {"action": "ACTION6", "row": target[0], "col": target[1]},
            "predicate": "COUNTER_REWRITE",
            "expected_parameters": {"rewrite": candidate.get("rewrite"), "amount": amount},
            "because": "the bar has rewritten on every effective click so far",
            "novelty": "a click on an object not yet clicked",
        },
    }


def _answer(card: dict[str, Any], world: StressWorld, clicked: set[tuple[int, int]]) -> dict[str, Any]:
    gate = card["gate_id"]
    template = dict(card["answer_template"])
    if gate == "G2-COUNTER":
        return _g2_answer(card, world, clicked)
    if gate == "G3-LEVERS":
        return {
            **template,
            "explanation": f"Clicking this object rewrites its own cells in place; {COUNTER_WORDS}.",
            "competing_models": ["a hidden process changed the object at the same moment"],
            "falsifier": "a repeat click leaves the object unchanged",
        }
    if gate == "G4-REACTIONS":
        lever = (card.get("subject") or {}).get("current_lever") or {}
        channels = lever.get("channels") or []
        phrases = ", ".join(
            f"{channel['channel_id']} rewrites "
            + ", ".join(f"{a}->{b}" for a, b, _n in channel.get("integer_transitions") or [])
            for channel in channels
        )
        return {
            **template,
            "mechanism_explanation": f"Lever {template.get('entity_id')}: {phrases} in its local region.",
            "competing_models": ["a hidden event coincided with the click"],
            "falsifier": "the same intervention produces a different exact residue",
        }
    if gate == "G4-B-LEVER-RELATIONS":
        return _g4b_answer(card, template)
    if gate == "G4-C-LEVER-LAW":  # test relation 0 on the board as it is now
        relation = card["subject"]["relations"][0]
        rows = {item["entity_id"]: item for item in card["subject"]["levers"]}
        lever = rows.get(relation["levers"][0]) or card["subject"]["levers"][0]
        return {**template, "from_relations": [relation["number"]], "action": lever["click"],
                "expected": {lever["entity_id"]: "STEPS"}, "elsewhere": "NO_CHANGE",
                "because": f"relation {relation['number']} says {lever['entity_id']} changes only its own tile"}
    return {
        **template,
        "mechanism_explanation": "Consecutive presses toggled this object between two states and back.",
        "competing_models": ["the lever may respond differently from another world state"],
        "falsifier": "a repeat from this exact masked state later behaves differently",
    }


def _g4b_answer(card: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """G4-B from the card alone: press each unpressed lever predicting it steps alone, then describe."""
    if template["answer_kind"] == "LEVER_PREDICTION":
        lever = next(item for item in card["subject"]["levers"] if not item["pressed"])
        return {**template, "action": lever["click"], "expected": {lever["entity_id"]: "STEPS"},
                "elsewhere": "NO_CHANGE",
                "because": f"if the levers are independent, pressing {lever['entity_id']} steps only its own tile"}
    recent = [item for item in card["progress"]["progress"]["recent"] if item["status"] == "SUPPORTED"]
    return {
        **template,
        "description": (
            "Each lever is a tile that its own click steps between its recorded states; pressing one "
            "lever left every other lever and the rest of the board unchanged in every graded test."
        ),
        "relations": [{"levers": [item["acted_lever"]], "prediction_refs": [item["prediction_id"]],
                       "claim": f"pressing {item['acted_lever']} changed only its own tile"} for item in recent],
        "competing_models": ["a lever may depend on another lever's state on boards not tested"],
        "falsifier": "a later press of one lever changes another lever's tile",
    }


def _orientation_notes(card: dict[str, Any]) -> list[dict[str, str]]:
    """Name what the certified world model shows, from the card alone."""
    return [
        {"subject": "G3-LEVERS", "kind": "NAME", "text": "the levers are small tiles that recolour themselves"},
        {"subject": "WORLD", "kind": "PROPOSAL", "text": "study each lever's repeated presses first"},
    ]


def _choose(card: dict[str, Any]) -> dict[str, Any]:
    probe = card["current_probe"]
    if probe.get("purpose") != "GUIDED_ACTION":
        return probe["actions"][0]
    target = probe.get("target") or {}
    if target.get("receipt") == "FREE_PLAY":  # R9-R24 D22: normal play; press the first lever on the card
        return (card.get("subject") or {}).get("levers", [{}])[0].get("click") or {"action": "ACTION6", "row": 0, "col": 0}
    levers = target.get("levers")
    if levers:  # the controller's own study order (a re-study after a death comes before a new lever)
        from inference.framework.controller_executor import STUDY_ORDER

        unfinished = sorted(
            (item for item in levers if item.get("status") in STUDY_ORDER),
            key=lambda item: STUDY_ORDER.index(item["status"]),
        )
        return (unfinished or levers)[0]["click"]
    anchors = probe.get("untried_object_anchors") or target.get("untried_object_anchors") or []
    first = anchors[0]
    anchor = first.get("anchor") if isinstance(first, dict) else first
    return {"action": "ACTION6", "row": int(anchor[0]), "col": int(anchor[1])}


@dataclass
class LadderRun:
    machine: Any
    world: StressWorld
    actions: int = 0
    largest: dict[str, int] = field(default_factory=dict)
    over_budget: set[str] = field(default_factory=set)
    gates: list[str] = field(default_factory=list)
    stopped: str = ""


def run_ladder(levers: int, *, max_steps: int = 2_000, wide_last: bool = False) -> LadderRun:
    """Drive a stress world from G2 to a satisfied G4-A with a Duck that reads only the card."""
    world = StressWorld(levers=levers, wide_last=wide_last)
    machine = click_world_machine(world.grid, ["ACTION6"])
    run = LadderRun(machine=machine, world=world)
    clicked: set[tuple[int, int]] = set()
    grid = [row[:] for row in world.grid]
    transition_id = 0
    for _ in range(max_steps):
        card_obj = build_card(machine)
        card = card_obj.payload
        size = len(card_obj.render())
        run.largest[machine.gate_id] = max(run.largest.get(machine.gate_id, 0), size)
        run.over_budget.update(card_obj.over_budget)
        if machine.gate_id not in run.gates:
            run.gates.append(machine.gate_id)
        if machine.gate_id == "PLAY-NORMAL":  # R9-R24 D22: the ladder is closed; the stress ladder ends here
            run.stopped = "PLAY-NORMAL"
            return run
        if card["next_operation"] == "SUBMIT_ORIENTATION":
            submit_notes(machine, _orientation_notes(card), source="ORIENTATION")
            continue
        if "answer_template" in card:
            machine.submit_answer(json.loads(json.dumps(_answer(card, world, clicked))))
            continue
        capability = card.get("current_probe")
        if card["next_operation"] == "CONTROLLER_TAKES_PREDICTION":  # G4-B: the controller's action
            capability = machine.next_probe_capability()
        if capability is None:
            run.stopped = f"{machine.gate_id} {card.get('status')} {card.get('next_operation')}"
            return run
        action = _choose({**card, "current_probe": capability})
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [action])
        transition_id += 1
        changes = world.changes(action)
        world.grid, outcome = lossless_outcome(world.grid, transition_id, action, changes)
        grid = world.grid
        machine.record_outcome(probe, outcome)
        hit = world.lever_at(int(action["row"]), int(action["col"]))
        if hit is not None:
            clicked.add(hit)
        run.actions += 1
    run.stopped = "max_steps"
    del grid
    return run


__all__ = ["CERTIFIED", "StressWorld", "run_ladder"]
