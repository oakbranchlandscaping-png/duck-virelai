#!/usr/bin/env python3
"""Turn a run's gate artifacts into a replayable record, and optionally replay it.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 stage M-0).

Reads ``{stem}_probe_outcomes.jsonl`` (lossless transitions) and ``{stem}_gate_answers.jsonl``
(accepted answers) from a run's artifacts directory and writes a ``virelai-recorded-world-v1``
fixture: the initial grid, each transition's sparse changes, and only the Duck-written fields of
the G2 and G3 answers (everything the controller derives is re-derived at replay).

Usage:
  python3 tools/record_from_artifacts.py ARTIFACTS_DIR STEM OUT.json.gz [--world ID] [--replay]

With ``--replay`` it replays the record through the current code and prints, per gate, the
number of card samples and the largest binding card in characters, then the final card.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

HEX = "0123456789abcdef"
DUCK_FIELDS = {
    "G2-COUNTER": (
        "answer_kind", "tracked_variable", "mechanism", "bookkeeping_reason", "competing_models",
        "falsifier", "trigger", "conditions", "limitations", "novel_prediction",
    ),
    "G3-LEVERS": ("answer_kind", "explanation", "competing_models", "falsifier", "conditions", "limitations"),
}
PREDICTION_FIELDS = ("action", "predicate", "expected_parameters", "because", "novelty")


def build_record(artifacts: Path, stem: str, world: str | None) -> dict:
    outcomes = [
        json.loads(line)
        for line in (artifacts / f"{stem}_probe_outcomes.jsonl").read_text().splitlines() if line.strip()
    ]
    answers_path = artifacts / f"{stem}_gate_answers.jsonl"
    answers = [
        json.loads(line) for line in answers_path.read_text().splitlines() if line.strip()
    ] if answers_path.exists() else []
    rows, cols = outcomes[0]["shape_before"]
    grid = [[0] * cols for _ in range(rows)]
    for site in outcomes[0]["site_transitions"]:
        grid[site["row"]][site["col"]] = site["before"]
    recorded = []
    for answer in answers:
        fields = DUCK_FIELDS.get(answer.get("gate_id"))
        if fields is None:
            continue
        row = {"gate_id": answer["gate_id"], **{key: answer[key] for key in fields if key in answer}}
        if isinstance(row.get("novel_prediction"), dict):
            row["novel_prediction"] = {
                key: row["novel_prediction"][key] for key in PREDICTION_FIELDS if key in row["novel_prediction"]
            }
        recorded.append(row)
    return {
        "schema": "virelai-recorded-world-v1",
        "source": f"{artifacts}/{stem}_probe_outcomes.jsonl and _gate_answers.jsonl",
        "world": world,
        "valid_actions": sorted({str(o["action"]["action"]) for o in outcomes}),
        "initial_grid": ["".join(HEX[value] for value in row) for row in grid],
        "steps": [
            {
                "transition_id": o["transition_id"],
                "action": o["action"],
                "changed": [[c["row"], c["col"], c["before"], c["after"]] for c in o["changed_cells"]],
                **({"boundary": o["boundary_event"]} if (o.get("boundary_event") or {}).get("state") not in {None, "NOT_FINISHED"} else {}),
            }
            for o in outcomes
        ],
        "answers": recorded,
    }


def write_record(record: dict, out: Path) -> None:
    with out.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as handle:
        handle.write(json.dumps(record, sort_keys=True).encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("stem")
    parser.add_argument("out", type=Path)
    parser.add_argument("--world", default=None)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    record = build_record(args.artifacts, args.stem, args.world)
    write_record(record, args.out)
    print(f"wrote {args.out}: {len(record['steps'])} transitions, {len(record['answers'])} Duck answers")
    if args.replay:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from inference.framework.record_replay import load_record, replay

        result = replay(load_record(args.out))
        by_gate: dict[str, list[int]] = {}
        for sample in result.samples:
            by_gate.setdefault(sample.gate_id, []).append(sample.chars)
        for gate, sizes in by_gate.items():
            print(f"{gate}: {len(sizes)} cards, largest {max(sizes)} characters")
        final = result.samples[-1]
        print(f"final card after transition {final.after_transition}: {final.chars} characters "
              f"({final.gate_id}, {final.status}); stopped: {result.stopped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
