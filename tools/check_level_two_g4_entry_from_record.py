#!/usr/bin/env python3
"""Pre-flight for a packaged source: replay the v4 live record past level 2's G3 and report where it rests.

Author: Claude (Alpha build seat), 2026-10-03. R9-R22 (DIAGNOSTIC_G3_G4_LEVER_TYPING_BOUNDARY_v1_2026-10-03.md).

The v5 pre-flight (check_level_two_g3_from_record.py) stopped at "the coverage report is accepted" and never
asked what the gate does next; live, the ladder then waited at G3 for hours. This one keeps going. It
replays RECORD through whatever ``inference`` is first on PYTHONPATH (point it at a package's
``source-dataset/src``): level 1 as recorded, then level 2 as live (the controller's own answers, every
recorded action through a freshly issued capability, recorded like live), then every answer the controller
owns after the last action. It reports the gate the machine rests at, who owns the next step, the A2
legal-move status, G3's inventory and G4-A's lever queue with each lever's G3 repeat press.

Pass (exit 0): the machine rests at G4-A, the state is legal, and G4-A studies every lever G3 certified.
ring9-carry-vc33-v5's source fails (rests at G3: bounded coverage). R9-R22 passes with all four levers.

Usage:
  PYTHONPATH=PKG/source-dataset/src/ARC3-Inference:PKG/source-dataset/src/tufa-arc-agi-framework/src \
      python3 tools/check_level_two_g4_entry_from_record.py RECORD.json.gz
"""
import json
import sys

from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import load_record, lossless_outcome, replay
from inference.framework.virelai_gates import GateContractError

ORBITS = "G4.2-LEVER-ORBITS"


def controller_answers(machine, report):
    owned = next_owned_step(machine)
    while owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
        try:
            machine.submit_answer(json.loads(json.dumps(owned.answer)))
        except GateContractError as exc:
            report["controller_answer_refused"] = f"{machine.gate_id}: {str(exc)[:160]}"
            break
        owned = next_owned_step(machine)
    return owned


record = load_record(sys.argv[1])
result = replay(record, max_steps=26, measure=False)
machine, grid, report = result.machine, result.grid, {}
for step in record["steps"][26:]:
    controller_answers(machine, report)
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
    grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"])
    machine.record_outcome(probe, outcome)
    machine.update_action_metadata(["ACTION6"])  # the live post-action refresh (gate_artifacts)
owned = controller_answers(machine, report)
inventory = machine.target_journal.active_product("G3-LEVERS")
g3_levers = sorted((inventory.payload.get("lever_entities") or ()) if inventory else ())
report.update(
    level=machine.lives.level, gate=machine.gate_id, owner=owned.owner, reason=owned.reason[:160],
    legal_move=machine.legal_move_status(), g3_levers=g3_levers,
    g3_ambiguous=sorted((inventory.payload.get("ambiguous_entities") or ()) if inventory else ()),
)
studied = []
if machine.gate_id == ORBITS:
    orbits = machine._adapters[ORBITS]
    pairs = orbits.g3_pairs() if hasattr(orbits, "g3_pairs") else {}
    studied = sorted(orbits._ordered_entities)
    report["g4a_levers"] = {item: (pairs.get(item) or {}).get("repeat_disposition") for item in studied}
print(json.dumps(report, indent=1))
passed = machine.gate_id == ORBITS and report["legal_move"].get("legal") and studied == g3_levers
sys.exit(0 if passed else 1)
