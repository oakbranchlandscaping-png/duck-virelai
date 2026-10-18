"""The no-choice G4 trace: the controller's ladder through G4.1, G4-A, G4-B and G4-C (WO-G4-DOSSIER-B, B2).

Author: Claude (Alpha build seat), 2026-10-18. Sol's ruling 7 and the plan's Stage 2 exit evidence: "a no-choice
golden" — with no choice made, the G4 ladder is byte-identical to the one before library-selected study.

Two traces, each recorded by ``tools/record_g4_no_choice_golden.py`` from ``0119a74`` code before any B2 edit
(``tests/fixtures/g4_no_choice_golden.json``):

* ``ft09_controller``: the ft09 v1 record replayed to G4.1's opening (t75), then **driven by the controller**
  (``controller_executor.next_owned_step``) on the offline ft09 world. Duck's only turns are the orientation and
  each confirmed run's explanation, answered with the record's own G4-A answers. Every owned step is traced: its
  owner, kind, gate and reason, the probe id, a hash of the full admitted probe envelope and the evidence id; then
  every active product, the G4-A events and the transition index. This is the path a choice changes.
* ``ft09_record``: the whole ft09 v1 record replayed through the production gate path (``record_replay.replay``),
  as the G3 golden does for its records.

``drive`` is shared with the B2 tests: ``choose`` (a callable) is consulted on each of Duck's explanation turns, so
a test can make a choice exactly where Duck already holds the turn (ruling 7). The golden is the drive with none.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from ft09_world import V1_RECORD, Ft09World

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = FIXTURES / "g4_no_choice_golden.json"
MAX_STEPS = 160
ORBITS = "G4.2-LEVER-ORBITS"


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


class Drive:
    """The controller-driven G4 ladder on the offline ft09 world, from G4.1's opening."""

    def __init__(self) -> None:
        import dossier_fixtures as fx
        from inference.framework.record_replay import load_record

        self.record = load_record(V1_RECORD)
        self.result = fx.ft09_anatomy(0)
        self.machine = self.result.machine
        self.world = Ft09World(self.record)
        self.world.grid = [row[:] for row in self.result.grid]
        self.world.transition_id = max(int(row["transition_id"]) for row in self.machine.transition_index)
        self.orbit_answers = [item for item in self.record["answers"] if item["gate_id"] == ORBITS]
        self.steps: list[dict[str, Any]] = []

    def act(self, step: Any) -> dict[str, Any]:
        from inference.framework.record_replay import record_like_live

        probe = self.machine.validate_probe({"probe_token": step.probe_token, **(step.decision or {})}, [step.action])
        outcome = self.world.step(step.action)
        record_like_live(self.machine, probe, outcome, self.world.valid_actions)
        return {"probe_id": probe.probe_id, "probe_sha": _sha(asdict(probe)),
                "evidence_id": self.machine.transition_index[-1].get("evidence_id")}

    def duck_turn(self, choose: Callable[[Any], None] | None) -> bool:
        """Duck's turn: orient, or explain the confirmed run with the record's answer (after ``choose``)."""
        from inference.framework.annotation_lane import orientation_due, submit_notes
        from inference.framework.record_replay import merge_recorded_answer

        machine = self.machine
        if orientation_due(machine):
            submit_notes(machine, [{"subject": "WORLD", "kind": "NAME", "text": "eight tiles"}], source="ORIENTATION")
            return True
        template = machine.gate_view().get("answer_template") or {}
        queue = [item for item in self.orbit_answers if item.get("entity_id") == template.get("entity_id")]
        if not template or not queue:
            return False
        if choose is not None:
            choose(self)
        machine.submit_answer(merge_recorded_answer(template, queue[0]))
        self.orbit_answers.remove(queue[0])
        return True

    def run(self, choose: Callable[[Any], None] | None = None, *, max_steps: int = MAX_STEPS) -> "Drive":
        from inference.framework.controller_executor import next_owned_step

        for _ in range(max_steps):
            machine = self.machine
            step = next_owned_step(machine)
            row = {"gate_id": machine.gate_id, "owner": step.owner, "kind": step.kind, "reason": step.reason}
            if step.owner == "CONTROLLER" and step.kind == "ANSWER":
                machine.submit_answer(json.loads(json.dumps(step.answer)))
            elif step.owner == "CONTROLLER" and step.kind == "ACTION":
                row.update(self.act(step))
            elif not self.duck_turn(choose):
                self.steps.append(row)
                break
            self.steps.append(row)
        return self


def _products(machine: Any) -> list[dict[str, Any]]:
    return [
        {"target_id": contract.target_id, "product_id": product.product_id, "product_type": product.product_type,
         "revision": product.revision, "payload_sha": _sha(product.payload)}
        for contract in machine.target_registry.ordered()
        if (product := machine.target_journal.active_product(contract.target_id)) is not None
    ]


def controller_trace() -> dict[str, Any]:
    drive = Drive().run()
    machine = drive.machine
    return {"steps": drive.steps, "products": _products(machine), "gate": machine.gate_id,
            "orbit_events_sha": _sha(machine._adapters[ORBITS]._events),
            "transition_index_sha": _sha(machine.transition_index), "frozen_levels_sha": _sha(machine.levels)}


def record_trace() -> dict[str, Any]:
    from g3_no_choice_trace import no_choice_trace

    return no_choice_trace(V1_RECORD)


def traces() -> dict[str, Any]:
    return {"ft09_controller": controller_trace(), "ft09_record": record_trace()}


__all__ = ["Drive", "GOLDEN", "controller_trace", "record_trace", "traces"]
