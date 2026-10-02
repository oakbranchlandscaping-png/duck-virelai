#!/usr/bin/env python3
"""Pre-flight for a packaged source: replay a live record past its level change and report level entry.

Author: Claude (Alpha build seat), 2026-10-02. R9-R20 (REVIEW_RING9_CARRY_VC33_V2_KAGGLE_2026-10-02.md).

Replays RECORD through whatever ``inference`` is first on PYTHONPATH (point it at a package's
``source-dataset/src``), applies the live post-action metadata refresh after the last (level-ending)
action, then lets the controller take level 2's entry: answers until it owns an action or hands the
step to Duck. ring9-carry-vc33-v2's source hands G1 to Duck with "offers no probe and no answer"
(the live deadlock); a fixed source answers G0 and G1 and takes G2's first click.

Usage:
  PYTHONPATH=PKG/source-dataset/src/ARC3-Inference:PKG/source-dataset/src/tufa-arc-agi-framework/src \
      python3 tools/check_level_entry_from_record.py RECORD.json.gz
"""
import json
import sys

from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import load_record, replay

machine = replay(load_record(sys.argv[1]), measure=False).machine
machine.update_action_metadata(["ACTION6"])  # the live refresh after the winning action (idempotent)
steps = []
for _ in range(4):
    step = next_owned_step(machine)
    steps.append((step.owner, step.kind, machine.gate_id))
    if step.owner != "CONTROLLER" or step.kind != "ANSWER":
        break
    machine.submit_answer(json.loads(json.dumps(step.answer)))
print(json.dumps({"level": machine.lives.level, "steps": steps, "gate": machine.gate_id,
                  "legal": machine.legal_move_status().get("legal"), "reason": step.reason}))
sys.exit(0 if (machine.gate_id, step.owner, step.kind) == ("G2-COUNTER", "CONTROLLER", "ACTION") else 1)
