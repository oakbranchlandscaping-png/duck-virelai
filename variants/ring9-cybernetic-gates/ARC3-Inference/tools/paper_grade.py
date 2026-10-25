#!/usr/bin/env python3
"""Grade one world's paper evidence against its answer key (WO-PE-03C/D).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §3-§4.

    python tools/paper_grade.py PAPER_EVIDENCE.json KEY.json --dir DIR [--repo REPO --evidence-commit SHA]

The steps run in order, and each stops the run with a non-zero exit while a human still owes something:
1. Validate the key (formal: a synthetic test key is refused unless ``--synthetic``). With ``--repo``, check that the
   key's freezing commit is an ancestor of the evidence commit.
2. Write ``DIR/mapping_sheet.json`` if absent. Every non-EXACT row must be confirmed by a person (``confirmed``: a list
   of solver subjects, or an empty list for none). Exit 3 while any row is unconfirmed.
3. Grade. Write ``DIR/verdict_sheet.json`` with every in-coverage proposition the join could not settle. Exit 4 while
   any verdict is owed.
4. When complete: write ``DIR/grade_report.json`` and the graded ``DIR/paper_report.md``. Exit 0.

The grade report is also written while incomplete, marked ``complete: false``, so progress is visible.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.framework import strict_json  # noqa: E402
from inference.paper_evidence import grader, keys, mapping, paper_report  # noqa: E402


def _write(path: Path, value) -> None:
    path.write_text(strict_json.canonical_json(value) + "\n")


def _key(args) -> dict | None:
    raw = json.loads(args.key.read_text())
    try:
        key = keys.validate(raw, formal=not args.synthetic)
    except keys.KeyError_ as exc:
        print("KEY REFUSED:\n  " + "\n  ".join(exc.reasons), file=sys.stderr)
        return None
    if args.repo and not keys.commit_is_ancestor(args.repo, key["construction"]["commit"], args.evidence_commit):
        print("KEY REFUSED: the key's freezing commit is not an ancestor of the evidence commit", file=sys.stderr)
        return None
    return key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("evidence", type=Path)
    parser.add_argument("key", type=Path)
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--evidence-commit")
    parser.add_argument("--synthetic", action="store_true", help="accept a SYNTHETIC_TEST key (code tests only)")
    args = parser.parse_args(argv)
    packet, key = json.loads(args.evidence.read_text()), _key(args)
    if key is None:
        return 2
    args.dir.mkdir(parents=True, exist_ok=True)
    sheet_path, verdict_path = args.dir / "mapping_sheet.json", args.dir / "verdict_sheet.json"
    if not sheet_path.exists():
        _write(sheet_path, mapping.propose(packet, key))
    sheet = json.loads(sheet_path.read_text())
    verdicts = json.loads(verdict_path.read_text()) if verdict_path.exists() else None
    report = grader.grade(packet, key, sheet, verdicts)
    _write(args.dir / "grade_report.json", report)
    if report["unconfirmed_mappings"]:
        print(f"{report['unconfirmed_mappings']} mapping rows await confirmation in {sheet_path}", file=sys.stderr)
        return 3
    if report["owed_verdicts"]:
        if verdicts is None:
            _write(verdict_path, grader.verdict_sheet(packet, key, report))
        print(f"{report['owed_verdicts']} verdicts are owed in {verdict_path}", file=sys.stderr)
        return 4
    grades = {row["assertion_id"]: row["grade"] for row in report["claims"]}
    (args.dir / "paper_report.md").write_text(paper_report.render(packet, grades))
    print(json.dumps({"game_id": report["game_id"],
                      **{k: report["tables"][k] for k in ("propositions", "proposition_bases", "audits", "items")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
