#!/usr/bin/env python3
"""Pre-flight for a packaged source: replay a live vc33 record to its end and report where the ladder rests.

Author: Claude (Alpha build seat), 2026-10-03. R9-R23 (RULING_MU_BUCKET_v1_2026-10-03).

Replays RECORD through whatever ``inference`` is first on PYTHONPATH (point it at a package's
``source-dataset/src``), as live: the controller's own answers, Duck's recorded answers only where the
gate asks Duck, every recorded action through a freshly issued capability. Then it reports the level, the
gate the machine rests at, the A2 legal-move status, G3's inventory closure and the mu bucket.

Pass (exit 0): the machine rests on a legal move, and if G3 holds bounded ambiguities beside certified
levers, it closed PARTIAL with them in the mu bucket. On the v6 record R9-R23 rests at G4-A on level 3 with
7 levers and E0028 in mu; source 8656839 (v6) rests at G3, illegal (the live stall).

Usage:
  PYTHONPATH=PKG/source-dataset/src/ARC3-Inference:PKG/source-dataset/src/tufa-arc-agi-framework/src \
      python3 tools/check_mu_partial_close_from_record.py RECORD.json.gz
"""
import json
import sys

from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import (
    _answer_index, click_world_machine, decode_grid, load_record, lossless_outcome, merge_recorded_answer,
    record_like_live, record_protocol,
)

record = load_record(sys.argv[1])
grid = decode_grid(record["initial_grid"])
machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
pending = {}
for answer in record["answers"]:
    pending.setdefault(answer["gate_id"], []).append(answer)


def answers():
    while True:
        owned = next_owned_step(machine)
        if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
            machine.submit_answer(json.loads(json.dumps(owned.answer)))
            continue
        view = machine.gate_view()
        template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
        due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
        ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
        if template and (ready or (due and owned.owner == "DUCK" and queue)):
            machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
            continue
        return owned


for step in record["steps"]:
    answers()
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
    grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"))
    record_like_live(machine, probe, outcome, record["valid_actions"])
owned = answers()
inventory = machine.target_journal.active_product("G3-LEVERS")
payload = inventory.payload if inventory is not None else {}
mu = getattr(machine, "mu", None)
report = {
    "level": machine.lives.level, "gate": machine.gate_id, "owner": owned.owner, "reason": owned.reason[:160],
    "legal_move": machine.legal_move_status(), "g3_closure": payload.get("closure"),
    "g3_levers": list(payload.get("lever_entities") or ()), "g3_ambiguous": list(payload.get("ambiguous_entities") or ()),
    "mu": None if mu is None else [
        {"entity_id": item["entity_id"], "status": item["status"], "tries": len(item["tries"]),
         "clicked_owner": item["tries"][-1].get("clicked_owner")} for item in mu.snapshot()
    ],
}
print(json.dumps(report, indent=1))
partial_ok = not payload.get("ambiguous_entities") or payload.get("closure") == "PARTIAL"
sys.exit(0 if report["legal_move"].get("legal") and inventory is not None and partial_ok else 1)
