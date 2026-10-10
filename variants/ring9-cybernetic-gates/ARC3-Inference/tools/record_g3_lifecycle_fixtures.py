#!/usr/bin/env python3
"""Build the k008 and k013 replay records for the G3 lifecycle slice from the v2 rehearsal artifacts.

Author: Claude (Alpha build seat), 2026-10-10. The G3 lifecycle slice (ruling 23, reassigned by the
Director). Built on ``record_from_artifacts.build_record``, with three additions the two saved sequences need:
- Only gate-machine probes (G1, G2 and G3) are kept, and each probe outcome is aligned with its own envelope.
  The run files an envelope for the probe it was about to record when it crashed, and for PLAY-NORMAL steps.
- k008: transition 61 (the GAME_OVER that raised) never became a probe outcome, so its board comes from the
  event log.
- k013: Duck's reachability answer was refused by a hidden error, so it is taken from the transcript
  (analysis step 396).

Usage: python3 tools/record_g3_lifecycle_fixtures.py ARTIFACTS_DIR OUT_DIR
ARTIFACTS_DIR holds the v2 rehearsal's ``k008_p0_*`` and ``k013_p0_*`` files.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE / "tools"))
from record_from_artifacts import build_record, write_record  # noqa: E402

ART = Path(".")
GAME_PROBES = ("G1-EGO", "G2-COUNTER", "G3-LEVERS")


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _aligned_dir(stem: str) -> Path:
    """A scratch artifacts dir holding the gate-machine probes and one envelope per probe outcome."""
    outcomes = [o for o in _rows(ART / f"{stem}_probe_outcomes.jsonl") if o["probe_id"].startswith(GAME_PROBES)]
    envelopes = _rows(ART / f"{stem}_probe_envelopes.jsonl")
    aligned, cursor = [], 0
    for outcome in outcomes:
        while envelopes[cursor]["probe_id"] != outcome["probe_id"]:
            cursor += 1
        aligned.append(envelopes[cursor])
        cursor += 1
    tmp = Path(tempfile.mkdtemp())
    (tmp / f"{stem}_probe_outcomes.jsonl").write_text("".join(json.dumps(o) + "\n" for o in outcomes))
    (tmp / f"{stem}_probe_envelopes.jsonl").write_text("".join(json.dumps(e) + "\n" for e in aligned))
    shutil.copy(ART / f"{stem}_gate_answers.jsonl", tmp / f"{stem}_gate_answers.jsonl")
    return tmp


def _grid_after(record: dict) -> list[list[int]]:
    hexd = "0123456789abcdef"
    grid = [[hexd.index(ch) for ch in row] for row in record["initial_grid"]]
    for step in record["steps"]:
        for r, c, _b, a in step["changed"]:
            grid[r][c] = a
    return grid


def k008() -> dict:
    record = build_record(_aligned_dir("k008_p0"), "k008_p0", "k008")
    # Action 61 crashed inside record_outcome, so no probe outcome was filed; the board is in the event log.
    final = [e for e in _rows(ART / "k008_p0_events.jsonl") if e.get("type") == "action"][-1]
    assert final["action_num"] == 61 and final["game_over"] and final["action_name"] == "ACTION1"
    before = _grid_after(record)
    changed = [
        [r, c, before[r][c], final["board"][r][c]]
        for r in range(len(before)) for c in range(len(before[0]))
        if before[r][c] != final["board"][r][c]
    ]
    record["steps"].append({
        "transition_id": record["steps"][-1]["transition_id"] + 1,
        "action": {"action": "ACTION1"},
        "changed": changed,
        "decision": {"pilot_intent": "APPROACH"},
        "boundary": {
            "done": False, "game_over": True, "level_after": 1, "level_before": 1,
            "level_completed": False, "run_complete": False, "state": "GAME_OVER",
        },
    })
    record["source"] = "kaggle-ring9-submission-v2 k008_p0 probe outcomes, envelopes, answers; action 61 from the event log"
    return record


def k013() -> dict:
    record = build_record(_aligned_dir("k013_p0"), "k013_p0", "k013")
    # Duck's reachability answer (transcript k013_p0.txt, analysis step 396): the run hid its error.
    record["answers"].append({
        "gate_id": "G3-LEVERS",
        "answer_kind": "TARGET_REACHABILITY",
        "meaning": "NO_CONTACT_PATH_IN_CURRENT_MAPPED_COMPONENT",
        "not_proven": "INERT_OR_PERMANENTLY_UNREACHABLE",
        "reopen_if": "RELEVANT_REACHABILITY_INPUT_CHANGES",
        "explanation": (
            "The target lies outside the ego's reachable component; 2 refused edges block all routes. "
            "It may not be inert if terrain changes, new anchors appear, or previously refused edges yield."
        ),
    })
    record["source"] = "kaggle-ring9-submission-v2 k013_p0 gate probes (PLAY-NORMAL excluded); reachability answer from the transcript"
    return record



def main() -> int:
    global ART
    ART, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for name, builder in (("k008", k008), ("k013", k013)):
        record = builder()
        path = out / f"ring9_v2_{name}_g3_lifecycle_record.json.gz"
        write_record(record, path)
        print(f"wrote {path}: {len(record['steps'])} steps, {len(record['answers'])} written answers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
