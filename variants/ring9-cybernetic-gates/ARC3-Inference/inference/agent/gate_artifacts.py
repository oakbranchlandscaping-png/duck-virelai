"""Gate evidence artifacts: what a run writes when a gate probe executes or an answer is accepted.

Author: Claude (Alpha build seat), 2026-09-29. R9-R08: moved out of ``tool_agent.py`` unchanged, so
Duck's path and the controller executor (``controller_turn.py``) share one recording path.

G3 target-ledger extension: Sol (Alpha build seat), 2026-10-03.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, load_runtime_state


def _write_g3_target_ledger(state_path: Path, gate_machine: Any) -> None:
    """Write one current, complete object roster instead of requiring trace reconstruction."""
    items, world_type = _g3_target_items(gate_machine)
    ledger_path = state_path.with_name(
        state_path.name.replace(
            f"_{RUNTIME_STATE_FILENAME}", "_g3_target_ledger.json"
        )
    )
    ledger_path.write_text(json.dumps({
        "schema": "virelai-g3-target-execution-ledger-v1",
        "gate_id": "G3-LEVERS",
        "world_type": world_type,
        "roster_populated_before_execution": True,
        "item_count": len(items),
        "items": items,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _g3_target_items(gate_machine: Any) -> tuple[list[dict[str, Any]], Any]:
    """Return the exported roster used by both the ledger and bounded-run audit."""
    items: list[dict[str, Any]] = []
    offset = 0
    world_type = None
    while True:
        page = gate_machine.inventory_view(offset=offset, limit=25)
        world_type = world_type or page.get("world_type")
        items.extend(page.get("items") or ())
        next_offset = (page.get("page") or {}).get("next_offset")
        if next_offset is None:
            break
        offset = int(next_offset)
    return items, world_type


def flush_g3_selection_events(state_path: Path, gate_machine: Any) -> None:
    """WO-G3-DIRECTED (Sol's review, 2026-10-11): every G3 choice event (admitted, refused, handoff, coverage
    resumed, stale, finished) is appended once to ``{stem}_g3_selection_events.jsonl``, so a rehearsal can
    measure choices and declined handoffs, including those that executed no action."""
    events = getattr(gate_machine, "g3_selection_events", None)
    if not events or gate_machine.g3_selection_flushed >= len(events):
        return
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_g3_selection_events.jsonl"))
    with path.open("a", encoding="utf-8") as handle:
        for row in events[gate_machine.g3_selection_flushed:]:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    gate_machine.g3_selection_flushed = len(events)


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
    flush_g3_selection_events(state_path, gate_machine)
    full_outcome["evidence_id"] = gate_event["evidence_id"]
    event_path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_gate_events.jsonl")
    )
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(gate_event, sort_keys=True) + "\n")
    if gate_event.get("gate_id") == "G3-LEVERS":
        _write_g3_target_ledger(state_path, gate_machine)
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
    if answering_gate_id == "G3-LEVERS":
        _write_g3_target_ledger(state_path, gate_machine)
        # The machine has advanced only after the aggregate answer is accepted;
        # capture the hand-off while the G3 journal remains available through
        # its adapter.  G4 is legal only from this explicit product.
        record_g3_run_outcome(
            state_path,
            gate_machine,
            "G3_COMPLETE",
            detail="the complete eligible roster was accepted by the G3 inventory contract",
        )


def _g3_adapter_snapshot(gate_machine: Any) -> Mapping[str, Any]:
    adapter = getattr(gate_machine, "_adapters", {}).get("G3-LEVERS")
    if adapter is None:
        return {}
    try:
        snapshot = adapter.snapshot()
    except Exception:
        return {}
    return snapshot if isinstance(snapshot, Mapping) else {}


def _g3_outcome_path(state_path: Path) -> Path:
    return state_path.with_name(
        state_path.name.replace(
            f"_{RUNTIME_STATE_FILENAME}", "_g3_run_outcome.json"
        )
    )


def load_g3_run_outcome(state_path: Path) -> dict[str, Any] | None:
    """Load the current explicit G3 product without reconstructing trace state."""
    path = _g3_outcome_path(state_path)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def record_g3_run_outcome(
    state_path: Path,
    gate_machine: Any,
    product_type: str,
    *,
    detail: str = "",
) -> dict[str, Any] | None:
    """Persist one explicit G3 run product.

    This is deliberately a product of the controller state, not a Duck claim.
    It may be called at a bounded runtime stop, so incomplete work remains
    visible and cannot be mistaken for a successful G3-to-G4 transition.
    """
    product = str(product_type or "").strip().upper()
    allowed = {
        "G3_COMPLETE", "G3_BUDGET_STOPPED", "G3_SEMANTIC_RETRY_EXHAUSTED",
        "G3_ROUTE_RETRY_EXHAUSTED", "G3_BOUNDARY_DEFERRED",
    }
    if product not in allowed:
        raise ValueError(f"unknown G3 run product: {product_type!r}")
    snapshot = _g3_adapter_snapshot(gate_machine)
    journal = snapshot.get("lifecycle_journal") if isinstance(snapshot, Mapping) else {}
    journal = journal if isinstance(journal, Mapping) else {}
    entities = journal.get("entities") if isinstance(journal, Mapping) else {}
    entities = entities if isinstance(entities, Mapping) else {}
    state_counts = journal.get("state_counts") if isinstance(journal, Mapping) else {}
    state_counts = state_counts if isinstance(state_counts, Mapping) else {}
    try:
        roster_items, _world_type = _g3_target_items(gate_machine)
    except Exception:
        roster_items = []
    eligible_items = [
        item for item in roster_items
        if isinstance(item, Mapping) and item.get("kind") == "ELIGIBLE_TARGET"
    ]
    pending_target: dict[str, Any] | None = None
    try:
        capability = gate_machine.next_probe_capability()
    except Exception:
        capability = None
    if isinstance(capability, Mapping):
        target = capability.get("target")
        if isinstance(target, Mapping):
            pending_target = {
                key: target[key] for key in (
                    "rank", "entity_id", "member_id", "integer", "shape_family",
                ) if key in target
            }
    scheduler = snapshot.get("scheduler") if isinstance(snapshot, Mapping) else {}
    scheduler = scheduler if isinstance(scheduler, Mapping) else {}
    if pending_target is None:
        pending = next(
            (
                scheduler.get(name)
                for name in ("pending_reachability", "pending_dossier", "pending_confirmation")
                if isinstance(scheduler.get(name), Mapping)
            ),
            None,
        )
        if isinstance(pending, Mapping):
            pending_target = {
                "entity_id": pending.get("target_entity_id"),
                "member_id": pending.get("target_member_id"),
            }
            matched = next(
                (
                    item for item in eligible_items
                    if (
                        not pending_target.get("entity_id")
                        or item.get("entity_id") == pending_target["entity_id"]
                    )
                    and (
                        not pending_target.get("member_id")
                        or item.get("target_member_id") == pending_target["member_id"]
                    )
                ),
                None,
            )
            if isinstance(matched, Mapping):
                visual = matched.get("visual_type")
                visual = visual if isinstance(visual, Mapping) else {}
                pending_target.update({
                    "rank": matched.get("eligible_rank"),
                    "integer": visual.get("integer"),
                    "shape_family": visual.get("shape_family"),
                })
            pending_target = {
                key: value for key, value in pending_target.items() if value is not None
            } or None
    last_evidence: dict[str, Any] | None = None
    last_event_serial = -1
    for entity_id, row in sorted(entities.items()):
        if not isinstance(row, Mapping):
            continue
        event = row.get("last_event")
        if not isinstance(event, Mapping):
            events = row.get("events")
            if isinstance(events, (list, tuple)) and events:
                event = events[-1]
        if isinstance(event, Mapping):
            event_id = str(event.get("event_id") or "")
            try:
                event_serial = int(event_id.rsplit("-", 1)[-1])
            except ValueError:
                event_serial = last_event_serial
            if event_serial >= last_event_serial:
                last_event_serial = event_serial
                last_evidence = {
                    "entity_id": str(entity_id),
                    "event_id": event.get("event_id"),
                    "to_state": event.get("to_state"),
                    "evidence_ref": event.get("evidence_ref"),
                    "reason": event.get("reason"),
                }
    gate_after = str(getattr(gate_machine, "gate_id", ""))
    g4_ids = {"G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"}
    record = {
        "schema": "virelai-g3-run-outcome-v1",
        "product": product,
        "detail": str(detail or ""),
        "gate_at_emit": gate_after,
        "g4_legal_open": bool(product == "G3_COMPLETE" and gate_after in g4_ids),
        "pending_target": pending_target,
        "last_accepted_evidence": last_evidence,
        "remaining_roster_counts": {
            str(key): int(value) for key, value in sorted(state_counts.items())
            if isinstance(value, (int, float))
        },
        "eligible_roster_count": len(eligible_items),
        "scheduler": dict(scheduler),
    }
    path = _g3_outcome_path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    history_path = path.with_name(path.stem + "_history.jsonl")
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


__all__ = [
    "load_g3_run_outcome", "record_gate_answer", "record_g3_run_outcome",
    "record_probe_outcome",
]
