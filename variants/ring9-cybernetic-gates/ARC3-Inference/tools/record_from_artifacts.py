#!/usr/bin/env python3
"""Turn a run's gate artifacts into a replayable record, and optionally replay it.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 stage M-0).

Reads ``{stem}_probe_outcomes.jsonl`` (lossless transitions) and ``{stem}_gate_answers.jsonl``
(accepted answers) from a run's artifacts directory and writes a ``virelai-recorded-world-v1``
fixture: the initial grid, each transition's sparse changes, only the written fields of the G2 and
G3 answers (everything the controller derives is re-derived at replay), and the recording protocol
stamped on the run's probe envelopes (R9-R08; absent before, which means the pre-D5 protocol).

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
    "G0-ACTION-METADATA": ("action_metadata", "semantic_claims", "epistemic_limit"),
    "G1-EGO": (
        "answer_kind", "subjects", "mechanism", "action_laws", "conditions", "constraints",
        "competing_models", "falsifier", "limitations", "novel_prediction",
    ),
    "G2-COUNTER": (
        "answer_kind", "tracked_variable", "mechanism", "bookkeeping_reason", "competing_models",
        "falsifier", "trigger", "conditions", "limitations", "novel_prediction",
    ),
    "G3-LEVERS": (
        "answer_kind", "explanation", "mechanism", "competing_models", "falsifier", "conditions",
        "limitations", "novel_prediction",
    ),
    "G4-REACTIONS": ("answer_kind", "mechanism_explanation", "competing_models", "falsifier", "limitations"),
    "G4.2-LEVER-ORBITS": (
        "answer_kind", "entity_id", "mechanism_explanation", "competing_models", "falsifier", "limitations",
    ),
    "G4-B-LEVER-RELATIONS": (
        "answer_kind", "action", "expected", "named", "elsewhere", "because", "description", "relations",
        "open_conditions", "competing_models", "falsifier", "limitations",
    ),
    "G4-C-LEVER-LAW": ("answer_kind", "action", "expected", "named", "elsewhere", "because", "from_relations"),
}
PREDICTION_FIELDS = (
    "action", "scope", "predicate", "expected_parameters", "because", "novelty",
    "status", "target_entity_id", "move_to_next_target",
)


def build_record(
    artifacts: Path, stem: str, world: str | None, *, legacy_g3_confirmation: bool = False,
) -> dict:
    outcomes = [
        json.loads(line)
        for line in (artifacts / f"{stem}_probe_outcomes.jsonl").read_text().splitlines() if line.strip()
    ]
    answers_path = artifacts / f"{stem}_gate_answers.jsonl"
    answers = [
        json.loads(line) for line in answers_path.read_text().splitlines() if line.strip()
    ] if answers_path.exists() else []
    envelopes_path = artifacts / f"{stem}_probe_envelopes.jsonl"
    envelopes = [
        json.loads(line) for line in envelopes_path.read_text().splitlines() if line.strip()
    ] if envelopes_path.exists() else []
    first_envelope = envelopes[0] if envelopes else {}
    if envelopes and len(envelopes) != len(outcomes):
        raise ValueError(f"probe envelope/outcome count differs: {len(envelopes)} != {len(outcomes)}")
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
        if isinstance(row.get("expected"), dict) and "named" in row:  # only what Duck wrote (G4-B, G4-C)
            named = row.pop("named")
            row["expected"] = {key: row["expected"][key] for key in named if key in row["expected"]}
        if isinstance(row.get("novel_prediction"), dict):
            row["novel_prediction"] = {
                key: row["novel_prediction"][key] for key in PREDICTION_FIELDS if key in row["novel_prediction"]
            }
        recorded.append(row)
    return {
        "schema": "virelai-recorded-world-v1",
        "source": f"{artifacts}/{stem}_probe_outcomes.jsonl and _gate_answers.jsonl",
        "world": world,
        "protocol": {
            "g3_inherits_g2_nulls": bool((first_envelope.get("protocol") or {}).get("g3_inherits_g2_nulls")),
            "replay_from_g0": True,
            "legacy_g3_confirmation_replay": bool(legacy_g3_confirmation),
        },
        "valid_actions": sorted({str(o["action"]["action"]) for o in outcomes}),
        "initial_grid": ["".join(HEX[value] for value in row) for row in grid],
        "steps": _steps(outcomes, grid, envelopes),
        "answers": recorded,
    }


def _experiment(envelope: dict) -> dict:
    """WO-G4-DOSSIER-B3: a G4-B limits experiment's step names its experiment, so a replay takes it before any
    answer due and admits Duck's choice again (``lever_experiments.replay_choice``)."""
    if envelope.get("purpose") != "LIMITS_EXPERIMENT":
        return {}
    target = envelope.get("target") or {}
    return {"experiment": {"probe_id": envelope.get("probe_id"), "question_id": target.get("question_id"),
                           "selected_by": target.get("selected_by")}}


def _steps(
    outcomes: list[dict], grid: list[list[int]], envelopes: list[dict] | None = None,
) -> list[dict]:
    """Each probe transition, with the harness RESET a probe record leaves out restored (R9-R12).

    A reset is not a probe, so it is not in ``probe_outcomes``. It shows as a gap: the next probe's
    board differs from the last probe's. The gap is recorded as a ``RESET`` step with its changes.
    """
    grid = [row[:] for row in grid]
    steps: list[dict] = []
    for index, o in enumerate(outcomes):
        before = [row[:] for row in grid]
        for site in o["site_transitions"]:
            before[site["row"]][site["col"]] = site["before"]
        jump = [[r, c, grid[r][c], before[r][c]] for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != before[r][c]]
        if jump:
            steps.append({"transition_id": int(o["transition_id"]) - 1, "kind": "RESET",
                          "action": {"action": "RESET"}, "changed": jump})
        changed = [[c["row"], c["col"], c["before"], c["after"]] for c in o["changed_cells"]]
        envelope = (envelopes or [{}] * len(outcomes))[index]
        decision = {
            key: envelope[key] for key in ("intent", "pilot_intent") if envelope.get(key) is not None
        }
        steps.append({
            "transition_id": o["transition_id"],
            "action": o["action"],
            "changed": changed,
            **({"decision": decision} if decision else {}),
            **_experiment(envelope),
            **({"boundary": o["boundary_event"]} if _boundary_kept(o.get("boundary_event") or {}) else {}),
        })
        grid = before
        for r, c, _b, a in changed:
            grid[r][c] = a
    return steps


def _boundary_kept(event: dict) -> bool:
    """A finished state, or a level change: a completed level reports NOT_FINISHED (R9-R15, F-R1)."""
    level_changed = event.get("level_before") is not None and event.get("level_before") != event.get("level_after")
    return event.get("state") not in {None, "NOT_FINISHED"} or bool(event.get("level_completed")) or level_changed


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
    parser.add_argument("--legacy-g3-confirmation", action="store_true")
    args = parser.parse_args()
    record = build_record(
        args.artifacts, args.stem, args.world,
        legacy_g3_confirmation=args.legacy_g3_confirmation,
    )
    write_record(record, args.out)
    print(f"wrote {args.out}: {len(record['steps'])} transitions, {len(record['answers'])} written answers")
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
