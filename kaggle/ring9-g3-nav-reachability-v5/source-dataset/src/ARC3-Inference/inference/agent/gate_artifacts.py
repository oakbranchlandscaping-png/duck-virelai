"""Gate evidence artifacts: what a run writes when a gate probe executes or an answer is accepted.

Author: Claude (Alpha build seat), 2026-09-29. R9-R08: moved out of ``tool_agent.py`` unchanged, so
Duck's path and the controller executor (``controller_turn.py``) share one recording path.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, load_runtime_state


def record_probe_outcome(
    state_path: Path,
    gate_machine: Any,
    gate_probe: Any,
    normalized_actions: list[dict[str, Any]],
    raw_payload: dict[str, Any],
    probe_before_frame: Any,
    probe_actions_before: list[str],
    current_valid_actions: list[str],
) -> dict[str, Any]:
    """Compile the lossless outcome of an executed gate action and persist its evidence."""
    from inference.framework.probe_evidence import compile_probe_outcome, frame_archive_rows  # cycle

    probe_after_frame, _ = load_runtime_state(state_path)
    after_actions = raw_payload.get("valid_actions")
    if not isinstance(after_actions, list):
        after_actions = list(current_valid_actions)
    transition_id = int(
        raw_payload.get("transition_id")
        or raw_payload.get("action_num")
        or (probe_after_frame.step if probe_after_frame is not None else 0)
        or gate_machine.observed_through_step + 1
    )
    full_outcome = compile_probe_outcome(
        probe_id=gate_probe.probe_id,
        transition_id=transition_id,
        action=normalized_actions[0],
        before_frame=probe_before_frame,
        after_frame=probe_after_frame,
        available_actions_before=probe_actions_before,
        available_actions_after=[str(item).strip() for item in after_actions],
        callback_payload=raw_payload,
    )
    # Keep the lossless H2 outcome visible to the scoped verifier.
    # The gate compacts only the copy stored in its prompt-facing event.
    gate_event = gate_machine.record_outcome(gate_probe, full_outcome)
    full_outcome["evidence_id"] = gate_event["evidence_id"]
    event_path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_gate_events.jsonl")
    )
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(gate_event, sort_keys=True) + "\n")
    outcome_path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_probe_outcomes.jsonl")
    )
    with outcome_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(full_outcome, sort_keys=True) + "\n")
    frame_path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_probe_frames.jsonl")
    )
    with frame_path.open("a", encoding="utf-8") as handle:
        for frame_row in frame_archive_rows(probe_before_frame, probe_after_frame):
            handle.write(json.dumps({
                **frame_row,
                "evidence_id": gate_event["evidence_id"],
                "probe_id": gate_probe.probe_id,
            }, sort_keys=True) + "\n")
    if isinstance(raw_payload.get("valid_actions"), list):
        gate_machine.update_action_metadata(raw_payload["valid_actions"])
    return gate_event



def record_gate_answer(
    state_path: Path, gate_machine: Any, answering_gate_id: str, answer: Any,
    *, executor: str = "DUCK",
) -> None:
    """Persist an accepted gate answer; shared by Duck and the controller executor."""
    answer_path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_gate_answers.jsonl")
    )
    answer_record = {
        "schema": "virelai-cybernetic-gates-v1",
        "gate_id": answering_gate_id,
        "executor": executor,
        **asdict(answer),
    }
    if answering_gate_id == "G1-EGO":
        # Capture the adaptive coverage state and the exact prospective claim at declaration
        # time. These are evaluation evidence, not model-authored semantics.
        ego_snapshot = gate_machine.ego.snapshot()
        answer_record.update({
            "gate_status_after_answer": ego_snapshot["status"],
            "coverage_certificate": ego_snapshot["coverage_certificate"],
            "pending_prediction": ego_snapshot["pending_prediction"],
            "ego_law": ego_snapshot["ego_law"],
        })
    elif answering_gate_id == "G2-COUNTER":
        counter_snapshot = gate_machine.counter.snapshot()
        answer_record.update({
            "gate_status_after_answer": counter_snapshot["status"],
            "counter_candidate": counter_snapshot["candidate"],
            "pending_prediction": counter_snapshot["pending_prediction"],
        })
    with answer_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(answer_record, sort_keys=True) + "\n")


__all__ = ["record_gate_answer", "record_probe_outcome"]
