#!/usr/bin/env python3
"""Replay the completed vc33 v6 G3 trace against the current delivery layer."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine


STEM = "vc33-5430563c_p0"


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _initial_grid(first_outcome: dict[str, Any]) -> list[list[int]]:
    rows, cols = first_outcome["shape_before"]
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for site in first_outcome["site_transitions"]:
        grid[int(site["row"])][int(site["col"])] = int(site["before"])
    return grid


def _prepare_machine(
    outcomes: list[dict[str, Any]], events: list[dict[str, Any]]
) -> CyberneticGateMachine:
    machine = CyberneticGateMachine(
        valid_actions=["ACTION6"],
        initial_grid=_initial_grid(outcomes[0]),
    )
    machine.submit_answer({
        "answer_id": "G0-v6-replay",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-v6-replay",
        product_type="EgoLaw",
        target_id="G1-EGO",
        revision=1,
        payload={"mode": "POINTER_GOD_MODE"},
        dependencies=("G0-ACTION-METADATA",),
    ))
    mask_payload = events[2]["mask_law"]
    mask = MaskLaw(
        law_id=str(mask_payload["law_id"]),
        law_version_id=str(mask_payload["law_version_id"]),
        revision=int(mask_payload["revision"]),
        status=str(mask_payload["status"]),
        cells=tuple(tuple(cell) for cell in mask_payload["cells"]),
        rewrite=str(mask_payload["rewrite"]),
        witness_evidence_refs=tuple(mask_payload["witness_evidence_refs"]),
        demonstration_ref=str(mask_payload["demonstration_ref"]),
        reversibility=str(mask_payload["reversibility"]),
    )
    machine.counter.mask_law = mask
    machine.counter._lossless_outcomes = [dict(item) for item in outcomes[:3]]
    machine.target_journal.put(MemoryProduct(
        product_id="COUNTER-v6-replay",
        product_type="CounterGateProduct",
        target_id="G2-COUNTER",
        revision=1,
        payload={
            "counter_model": events[2]["counter_model"],
            "mask_law": asdict(mask),
            "ranked_object_frontier": machine.counter.sweep_frontier(),
        },
        dependencies=("G1-EGO",),
    ))
    return machine


def _inventory_payload(answer: dict[str, Any]) -> dict[str, Any]:
    partition = answer["novel_prediction"]
    return {
        "answer_kind": "LEVER_INVENTORY",
        "lever_entities": partition["lever_entities"],
        "clean_null_entities": partition["clean_null_entities"],
        "ambiguous_entities": partition["ambiguous_entities"],
        "explanation": answer["mechanism"],
        "evidence_refs": answer["evidence_refs"],
        "competing_models": answer["competing_models"],
        "falsifier": answer["falsifier"],
        "conditions": answer.get("conditions", []),
        "limitations": answer.get("limitations", []),
    }


def replay(artifact_dir: Path) -> dict[str, Any]:
    outcomes = _rows(artifact_dir / f"{STEM}_probe_outcomes.jsonl")
    events = _rows(artifact_dir / f"{STEM}_gate_events.jsonl")
    answers = _rows(artifact_dir / f"{STEM}_gate_answers.jsonl")
    if len(outcomes) != 15 or len(events) != 15:
        raise ValueError("expected the completed 15-transition vc33 v6 trace")
    machine = _prepare_machine(outcomes, events)
    dossier_by_member = {
        str(answer["target_member_id"]): answer
        for answer in answers
        if answer.get("answer_kind") == "LEVER_DOSSIER"
    }
    replayed_probe_ids: list[str] = []
    for outcome in outcomes[3:]:
        replay_outcome = {
            key: value for key, value in outcome.items() if key != "evidence_id"
        }
        capability = machine.next_probe_capability()
        if capability is None:
            raise ValueError(f"replay had no capability for {outcome['probe_id']}")
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        if probe.probe_id != outcome["probe_id"]:
            raise ValueError(
                f"probe mismatch: expected {outcome['probe_id']}, got {probe.probe_id}"
            )
        machine.record_outcome(probe, replay_outcome)
        replayed_probe_ids.append(probe.probe_id)
        lever = machine._adapters["G3-LEVERS"]
        if lever._pending_dossier is not None:
            member_id = str(lever._pending_dossier["target_member_id"])
            machine.submit_answer(dossier_by_member[member_id])

    if machine.next_probe_capability() is not None:
        raise ValueError("v6 replay did not exhaust the G3 roster")
    final_answer = next(
        answer for answer in answers
        if answer.get("answer_kind") == "G3_BOUNDED_COVERAGE_REPORT"
    )
    accepted = machine.submit_answer(_inventory_payload(final_answer))
    snapshot = machine.snapshot()
    former_working_view = machine._adapters["G3-LEVERS"]._working_gate_view()
    card = machine.gate_view()
    inventory = machine.inventory_view(offset=0, limit=25)
    full_chars = len(json.dumps(snapshot, sort_keys=True))
    former_working_chars = len(json.dumps(former_working_view, sort_keys=True))
    card_chars = len(json.dumps(card, sort_keys=True))
    checks = {
        "all_v6_probes_replayed": replayed_probe_ids == [
            outcome["probe_id"] for outcome in outcomes[3:]
        ],
        "bounded_report_accepted": accepted.answer_kind == "G3_BOUNDED_COVERAGE_REPORT",
        "lossless_snapshot_exceeds_old_guard": full_chars > 24_000,
        "former_working_view_reproduces_overflow": former_working_chars > 24_000,
        "completion_card_under_half_guard": card_chars < 12_000,
        "completion_card_is_index": (
            card.get("schema") == "virelai-g3-completion-card-v1"
            and "entity_ledger" not in card
            and "inherited_frontier" not in card
        ),
        "inventory_is_fully_retrievable": (
            inventory["page"]["total"] == 11
            and inventory["page"]["returned"] == 11
            and inventory["truncated"] is False
        ),
        "v6_partition_preserved": (
            card["confirmed_levers"]["total"] == 2
            and card["scoped_nulls"]["total"] == 5
            and card["bounded_unknowns"]["total"] == 3
            and card["completion"]["counter_excluded_count"] == 1
        ),
    }
    return {
        "schema": "virelai-g3-v6-completion-replay-v1",
        "artifact_dir": str(artifact_dir),
        "full_snapshot_chars": full_chars,
        "former_working_view_chars": former_working_chars,
        "completion_card_chars": card_chars,
        "replayed_probe_count": len(replayed_probe_ids),
        "completion": card["completion"],
        "partition": {
            "confirmed_levers": card["confirmed_levers"]["total"],
            "scoped_nulls": card["scoped_nulls"]["total"],
            "bounded_unknowns": card["bounded_unknowns"]["total"],
            "counter_exclusions": card["completion"]["counter_excluded_count"],
        },
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()
    result = replay(args.artifact_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
