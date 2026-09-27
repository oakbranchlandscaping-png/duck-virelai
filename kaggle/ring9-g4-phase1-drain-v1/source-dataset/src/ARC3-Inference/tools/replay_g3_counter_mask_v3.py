#!/usr/bin/env python3
"""Replay the frozen vc33 v3 counter-mask failure against current G3 source."""
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


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()
    artifact_dir = args.artifact_dir.resolve()
    stem = "vc33-5430563c_p0"
    outcomes = _rows(artifact_dir / f"{stem}_probe_outcomes.jsonl")
    events = _rows(artifact_dir / f"{stem}_gate_events.jsonl")
    if len(outcomes) != len(events) or len(outcomes) < 11:
        raise SystemExit("unexpected or incomplete v3 artifact set")

    first_sites = outcomes[0]["site_transitions"]
    rows, cols = outcomes[0]["shape_before"]
    initial = [[0 for _ in range(cols)] for _ in range(rows)]
    for site in first_sites:
        initial[int(site["row"])][int(site["col"])] = int(site["before"])

    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=initial)
    machine.submit_answer({
        "answer_id": "G0-v3-replay",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-v3-replay",
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
        product_id="COUNTER-v3-replay",
        product_type="CounterGateProduct",
        target_id="G2-COUNTER",
        revision=1,
        payload={
            "counter_model": events[2]["counter_model"],
            "mask_law": asdict(mask),
            "ranked_object_frontier": {"schema": "virelai-ranked-object-frontier-v1"},
        },
        dependencies=("G1-EGO",),
    ))

    lever = machine._adapters["G3-LEVERS"]
    frontier = lever._frontier_snapshot()
    ledger = lever._ensure_entity_ledger()
    for outcome in outcomes[3:10]:
        lever.observe_transition(outcome)
    entities_before_counter_loop = len(ledger.entities)
    for outcome in outcomes[10:]:
        lever.observe_transition(outcome)
    entities_after_counter_loop = len(ledger.entities)

    excluded = frontier["excluded_candidates"]
    result = {
        "schema": "virelai-g3-v3-counter-mask-replay-v1",
        "artifact_dir": str(artifact_dir),
        "mask_law_version_id": mask.law_version_id,
        "mask_cell_count": len(mask.cells),
        "original_candidate_count": frontier["original_candidate_count"],
        "eligible_candidate_count": frontier["candidate_count"],
        "excluded_candidates": excluded,
        "eligible_source_ranks": [row["source_rank"] for row in frontier["candidates"]],
        "next_source_rank_after_v3_levers": next(
            row["source_rank"] for row in frontier["candidates"]
            if int(row["source_rank"]) > 5
        ),
        "entities_before_counter_loop": entities_before_counter_loop,
        "entities_after_counter_loop": entities_after_counter_loop,
        "counter_loop_transition_count": len(outcomes[10:]),
        "ledger_limitations": list(ledger.limitations),
        "checks": {
            "source_rank_6_counter_excluded": any(
                row["source_rank"] == 6
                and row["member_id"] == "M0001"
                and row["disposition"] == "COUNTER_ROLE_EXCLUDED"
                for row in excluded
            ),
            "next_target_is_source_rank_7": next(
                row["source_rank"] for row in frontier["candidates"]
                if int(row["source_rank"]) > 5
            ) == 7,
            "counter_loop_created_no_entities": (
                entities_before_counter_loop == entities_after_counter_loop
            ),
            "lossless_frame_chain_accepted": not ledger.limitations,
        },
    }
    result["status"] = (
        "PASS" if all(result["checks"].values()) else "FAIL"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
