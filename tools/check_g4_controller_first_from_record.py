#!/usr/bin/env python3
"""Pre-flight for a packaged source: does G4-B come from the record, with lever states named? (R9-R24)

Author: Claude (Alpha build seat), 2026-10-04. RULING_G4_CONTROLLER_FIRST_v2_2026-10-04 (Director-ruled).

Replays RECORD through whatever ``inference`` is first on PYTHONPATH (point it at a package's
``source-dataset/src``), as live, up to the transition before G4-B's first probe (G4B_FIRST). Duck's
recorded G4-B and G4-C answers are withheld: under the ruling the record answers G4-B. It then asks
the controller for G4-B's step and reports the owner, the certified relations, the lever states the
card shows, where the ladder goes next, and Duck's per-level G4 budget.

Pass (exit 0): the controller owns G4-B, its answer is accepted (certified_by RECORD), no lever state
reads UNRECORDED, and the ladder moves to G4-C with Duck's budget untouched. On the v7 record (G4B_FIRST
141), source ec8554d fails: Duck owns G4-B and every state reads UNRECORDED.

Usage:
  PYTHONPATH=PKG/source-dataset/src/ARC3-Inference:PKG/source-dataset/src/tufa-arc-agi-framework/src \\
      python3 tools/check_g4_controller_first_from_record.py RECORD.json.gz G4B_FIRST
"""
import json
import sys

from inference.framework.annotation_lane import orientation_due, submit_notes
from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import (
    _answer_index, click_world_machine, decode_grid, load_record, lossless_outcome, merge_recorded_answer,
    record_like_live, record_protocol,
)

RELATIONS, LAW = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
record, g4b_first = load_record(sys.argv[1]), int(sys.argv[2])
grid = decode_grid(record["initial_grid"])
machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
pending = {}
for answer in record["answers"]:
    if answer["gate_id"] not in (RELATIONS, LAW):
        pending.setdefault(answer["gate_id"], []).append(answer)


def answers():
    while True:
        owned = next_owned_step(machine)
        if owned.owner == "CONTROLLER" and owned.kind == "ANSWER" and machine.gate_id != RELATIONS:
            machine.submit_answer(json.loads(json.dumps(owned.answer)))
            continue
        view = machine.gate_view()
        template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
        due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
        ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
        if template and (ready or (due and owned.owner == "DUCK" and queue)):
            machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
            continue
        return


for step in record["steps"]:
    if step["transition_id"] >= g4b_first:
        break
    answers()
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
    grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"))
    record_like_live(machine, probe, outcome, record["valid_actions"])
answers()
if orientation_due(machine):  # live, Duck oriented; a record keeps no orientation answer
    submit_notes(machine, [{"subject": "WORLD", "kind": "NAME", "text": "pre-flight orientation"}], source="ORIENTATION")
report = {"level": machine.lives.level, "gate": machine.gate_id}
step = next_owned_step(machine)
report["g4b_owner"], report["g4b_reason"] = step.owner, step.reason
states = {row["entity_id"]: row["state_now"] for row in machine._adapters[RELATIONS]._lever_rows()} if machine.gate_id == RELATIONS else {}
report["lever_states"] = states
if step.owner == "CONTROLLER" and step.kind == "ANSWER":
    machine.submit_answer(json.loads(json.dumps(step.answer)))
    product = machine.target_journal.active_product(RELATIONS).payload
    report["g4b_certified_by"] = product.get("certified_by")
    report["description"] = product["from_record"]["description"]
report["gate_after"] = machine.gate_id
report["duck_budget"] = machine.duck_budget.snapshot() if hasattr(machine, "duck_budget") else None
print(json.dumps(report, indent=1))
ok = (report.get("g4b_certified_by") == "RECORD" and states and "UNRECORDED" not in states.values()
      and report["gate_after"] == LAW and report["duck_budget"]["used"] == 0)
sys.exit(0 if ok else 1)
