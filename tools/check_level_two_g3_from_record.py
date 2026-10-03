#!/usr/bin/env python3
"""Pre-flight for a packaged source: replay the v4 live record through level 2's G3 and report the end.

Author: Claude (Alpha build seat), 2026-10-03. R9-R21 (REVIEW_RING9_CARRY_VC33_V4_KAGGLE_2026-10-03.md).

Replays RECORD through whatever ``inference`` is first on PYTHONPATH (point it at a package's
``source-dataset/src``): level 1 as recorded, then level 2 as live (the controller's own answers, every
recorded action through a freshly issued capability, recorded like live). At the end it reports who owns
G3's step, whether the state is legal (axiom A2), and whether the gate's own template is accepted.
ring9-carry-vc33-v4's source: the controller's inventory is refused and the state is called legal (the
live stall). A fixed source: the coverage report is Duck's, legal, and accepted.

Usage:
  PYTHONPATH=PKG/source-dataset/src/ARC3-Inference:PKG/source-dataset/src/tufa-arc-agi-framework/src \
      python3 tools/check_level_two_g3_from_record.py RECORD.json.gz
"""
import json
import sys

from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import load_record, lossless_outcome, replay
from inference.framework.virelai_gates import GateContractError

record = load_record(sys.argv[1])
result = replay(record, max_steps=26, measure=False)
machine, grid = result.machine, result.grid
for step in record["steps"][26:]:
    owned = next_owned_step(machine)
    while owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
        machine.submit_answer(json.loads(json.dumps(owned.answer)))
        owned = next_owned_step(machine)
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
    grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"])
    machine.record_outcome(probe, outcome)
    machine.update_action_metadata(["ACTION6"])  # the live post-action refresh (gate_artifacts)
report = {"level": machine.lives.level, "gate": machine.gate_id}
owned = next_owned_step(machine)
if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
    try:
        machine.submit_answer(json.loads(json.dumps(owned.answer)))
    except GateContractError as exc:
        report["controller_answer_refused"] = str(exc)[:160]
    owned = next_owned_step(machine)
report.update(owner=owned.owner, reason=owned.reason, legal=machine.legal_move_status().get("legal"))
accepted = False
if owned.owner == "DUCK" and report["legal"]:
    try:
        machine.submit_answer(dict(machine.gate_view()["answer_template"]))
        accepted = True
    except GateContractError as exc:
        report["duck_template_refused"] = str(exc)[:160]
report["coverage_accepted"] = accepted
print(json.dumps(report))
sys.exit(0 if accepted else 1)
