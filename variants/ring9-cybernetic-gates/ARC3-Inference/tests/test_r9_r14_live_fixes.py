"""R9-R14: the two defects the live G4-B run found (REVIEW_RING9_G4B_FT09_KAGGLE_V1_2026-09-30).

Author: Claude (Alpha build seat), 2026-09-30.

F1: a refusal must reach Duck. Live, the orientation refusal came after the whole card in the reply,
the tool-output limit cut it off, and Duck spent 5 turns without the reason. F2: the machine's
observed step stopped at the last G2 transition (57 of 117), so every later freeze stamp was stale.
"""
from __future__ import annotations

import json

from ft09_world import V1_RECORD
from inference.agent.memory_queries import gated_memory_query
from inference.framework.annotation_lane import orientation_due
from inference.framework.record_replay import load_record, replay
from test_g4b_relations import _predict, start_g4b
from test_memory_m2 import Run

LIVE_NOTES = [  # the live run's first orientation, verbatim in shape
    {"subject": "WORLD", "kind": "NAME", "text": "3x3 grid of pattern blocks; each block is a lever target"},
    {"subject": "E9999", "kind": "PROPOSAL", "text": "press each lever repeatedly to map its orbit"},
]
TOOL_OUTPUT_CHARS = 4 * 1024  # the live tool-output limit, about 1,024 tokens


def test_f1_a_refusal_puts_the_reason_first_and_fits_the_tool_output(tmp_path, monkeypatch):
    run = Run(tmp_path, monkeypatch)
    run.until_duck()
    machine = run.agent._gate_machine
    reply = gated_memory_query(run.agent, run.state_path, machine, "orient", {"notes": LIVE_NOTES})
    printed = json.dumps(reply, indent=2)
    assert list(reply)[:3] == ["schema", "operation", "error"]
    assert "E9999" in reply["error"] and "G4.2-LEVER-ORBITS" in reply["error"]  # says what is allowed
    assert len(printed) < TOOL_OUTPUT_CHARS and printed.index('"error"') < 200
    assert orientation_due(machine)  # refused, nothing stored


def test_f1_the_current_gate_is_a_note_subject(tmp_path, monkeypatch):
    run = Run(tmp_path, monkeypatch)
    run.until_duck()
    machine = run.agent._gate_machine
    notes = [{"subject": machine.gate_id, "kind": "PROPOSAL", "text": "press each lever until it cycles"}]
    reply = gated_memory_query(run.agent, run.state_path, machine, "orient", {"notes": notes})
    assert reply["error"] is None and not orientation_due(machine)


def test_f2_the_observed_step_follows_every_transition():
    record = load_record(V1_RECORD)
    machine = replay(record, measure=False).machine
    assert machine.observed_through_step == max(step["transition_id"] for step in record["steps"])  # 109
    machine, world = start_g4b()
    prediction = _predict(machine, "E0053")
    assert prediction.declared_at_transition == world.transition_id  # frozen now, not at G2's last step
