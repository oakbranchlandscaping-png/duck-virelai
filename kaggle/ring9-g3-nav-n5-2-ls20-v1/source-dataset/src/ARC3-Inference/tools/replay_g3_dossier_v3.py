#!/usr/bin/env python3
"""Regrade the flawed frozen vc33 v3 M0009 dossier with the typed contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inference.framework.lever_dossier import LeverDossierError, validate_lever_dossier


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _bbox(cells: list[list[int]]) -> list[int] | None:
    if not cells:
        return None
    return [
        min(cell[0] for cell in cells), min(cell[1] for cell in cells),
        max(cell[0] for cell in cells), max(cell[1] for cell in cells),
    ]


def _rejection(payload: dict[str, Any], **kwargs: Any) -> str | None:
    try:
        validate_lever_dossier(payload, **kwargs)
    except LeverDossierError as exc:
        return str(exc)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()
    root = args.artifact_dir.resolve()
    stem = "vc33-5430563c_p0"
    answers = _rows(root / f"{stem}_gate_answers.jsonl")
    events = _rows(root / f"{stem}_gate_events.jsonl")
    probes = _rows(root / f"{stem}_probe_envelopes.jsonl")
    legacy = next(
        row for row in answers
        if row.get("answer_kind") == "LEVER_DOSSIER"
        and row.get("subjects") == ["M0009"]
    )
    witness = next(
        row for row in events
        if row.get("probe_id") == "G3-LEVERS:CLICK:5"
    )
    confirmation = next(
        row for row in events
        if str(row.get("probe_id") or "").startswith("G3-LEVERS:CONFIRM:M0009:")
    )
    probe = next(row for row in probes if row.get("probe_id") == "G3-LEVERS:CLICK:5")
    attribution = witness["attribution"]
    summary = {
        "schema": "virelai-g3-effect-summary-v1",
        "target_member_id": "M0009",
        "witness_evidence_ref": witness["evidence_id"],
        "causal_scope": "NON_COUNTER_RESIDUE_ONLY",
        "counter_treatment": "COUNTER_CHANGES_EXCLUDED_FROM_LEVER_CAUSALITY",
        "local_changed_cell_count": len(attribution["local_residue_cells"]),
        "local_changed_bbox": _bbox(attribution["local_residue_cells"]),
        "remote_changed_cell_count": len(attribution["remote_residue_cells"]),
        "remote_changed_bbox": _bbox(attribution["remote_residue_cells"]),
        "counter_masked_cell_count": len(attribution["counter_masked_cells"]),
    }
    kwargs = {
        "answer_id": "G3-v3-regraded-M0009",
        "target_member_id": "M0009",
        "expected_intervention": probe["actions"][0],
        "expected_effect_summary": summary,
        "required_evidence_refs": (
            witness["evidence_id"], confirmation["evidence_id"]
        ),
    }
    legacy_rejection = _rejection(legacy, **kwargs)
    semantic_candidate = {
        **legacy,
        "target_member_id": "M0009",
        "explanation": legacy["mechanism"],
        "intervention": probe["actions"][0],
        "effect_summary": summary,
        "evidence_refs": [witness["evidence_id"], confirmation["evidence_id"]],
        "competing_models": [
            "An autonomous process coincided with both observed pointer interventions."
        ],
    }
    semantic_rejection = _rejection(semantic_candidate, **kwargs)
    corrected = {
        **semantic_candidate,
        "explanation": (
            "Clicking M0009 produced the admitted remote residue on both trials. "
            "The simultaneous counter bookkeeping change was masked and excluded from lever causality."
        ),
    }
    accepted = validate_lever_dossier(corrected, **kwargs)
    checks = {
        "legacy_dossier_rejected": legacy_rejection is not None,
        "legacy_character_competitors_detected": (
            len(legacy["competing_models"]) > 100
            and all(len(item) == 1 for item in legacy["competing_models"][:20])
        ),
        "legacy_counter_claim_rejected_after_shape_repair": semantic_rejection is not None,
        "typed_corrected_dossier_accepted": accepted.answer_kind == "LEVER_DOSSIER",
        "admitted_remote_count_is_264": summary["remote_changed_cell_count"] == 264,
        "counter_cells_are_excluded": summary["counter_masked_cell_count"] == 2,
    }
    result = {
        "schema": "virelai-g3-v3-dossier-regrade-v1",
        "artifact_dir": str(root),
        "target_member_id": "M0009",
        "legacy_rejection": legacy_rejection,
        "semantic_rejection": semantic_rejection,
        "effect_summary": summary,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
