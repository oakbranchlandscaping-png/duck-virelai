#!/usr/bin/env python3
"""Compile the G4.0/G4.1 anatomy from immutable vc33 v8 G3 artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inference.framework.g4_reactions import anatomy_payload, compile_effect_anatomy
from inference.framework.lever_attribution import LeverAttribution


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifacts = args.run_dir / "artifacts"
    event_path = next(artifacts.glob("*_gate_events.jsonl"))
    answer_path = next(artifacts.glob("*_gate_answers.jsonl"))
    events = rows(event_path)
    answers = rows(answer_path)

    inventory = next(item for item in answers if item.get("answer_kind") == "LEVER_INVENTORY")
    partition = inventory["novel_prediction"]
    dossiers = {
        str(item["target_member_id"]): item
        for item in answers if item.get("answer_kind") == "LEVER_DOSSIER"
    }
    confirmations = {
        str(item["confirmation"]["witness_evidence_ref"]): item["confirmation"]
        for item in events if isinstance(item.get("confirmation"), dict)
        and item["confirmation"].get("status") == "SUPPORTED"
    }
    witness_events = {
        str(item.get("evidence_id")): item
        for item in events if isinstance(item.get("attribution"), dict)
        and item["attribution"].get("disposition") in {
            "LOCAL_LEVER_WITNESS", "REMOTE_LEVER_WITNESS", "LOCAL_AND_REMOTE_LEVER_WITNESS"
        }
    }

    compiled = []
    for entity_id in partition["lever_entities"]:
        confirmation = next(
            item for item in confirmations.values() if item.get("entity_id") == entity_id
        )
        witness_ref = str(confirmation["witness_evidence_ref"])
        event = witness_events[witness_ref]
        member_id = str(event["attribution"]["target_member_id"])
        dossier = dossiers[member_id]
        raw = dict(event["attribution"])
        for field in (
            "changed_cells", "counter_masked_cells", "ego_motion_cells", "ego_confounded_cells",
            "ground_exchange_cells", "residue_cells", "local_residue_cells", "remote_residue_cells",
            "limitations",
        ):
            raw[field] = tuple(tuple(item) if isinstance(item, list) else item for item in raw[field])
        attribution = LeverAttribution(**raw)
        anatomy = compile_effect_anatomy(
            attribution,
            entity_id=entity_id,
            intervention=dossier["intervention"],
            confirmation_evidence_ref=str(confirmation["confirmation_evidence_ref"]),
            dossier_answer_ref=str(dossier["answer_id"]),
            mask_law_version_id="FROZEN-VC33-V8-G2-MASK",
        )
        compiled.append(anatomy_payload(anatomy))

    result = {
        "schema": "virelai-g4-v8-frozen-replay-v1",
        "source_run": str(args.run_dir),
        "source_kind": "IMMUTABLE_EXECUTION_ARTIFACT_REPLAY",
        "new_live_execution": False,
        "lever_entities": list(partition["lever_entities"]),
        "scoped_null_entities": list(partition["clean_null_entities"]),
        "ambiguous_entities": list(partition["ambiguous_entities"]),
        "anatomies": compiled,
        "checks": {
            "exactly_two_levers": len(compiled) == 2,
            "expected_levers": [item["entity_id"] for item in compiled] == ["E0004", "E0005"],
            "eight_scoped_nulls_excluded": len(partition["clean_null_entities"]) == 8,
            "zero_ambiguous_entities": not partition["ambiguous_entities"],
            "all_coverage_complete": all(item["coverage_complete"] for item in compiled),
            "no_counter_cells_in_channels": all(
                sum(channel["changed_cell_count"] for channel in item["channels"])
                == item["residue_cell_count"] for item in compiled
            ),
            "binding_refs_complete": all(
                item["witness_evidence_ref"] and item["confirmation_evidence_ref"]
                and item["dossier_answer_ref"] for item in compiled
            ),
        },
    }
    result["passed"] = all(result["checks"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": result["passed"],
        "lever_entities": result["lever_entities"],
        "scoped_null_count": len(result["scoped_null_entities"]),
        "residue_counts": {item["entity_id"]: item["residue_cell_count"] for item in compiled},
        "channel_counts": {item["entity_id"]: len(item["channels"]) for item in compiled},
        "output": str(args.output),
    }, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
