"""WO-PE-02: the run roster — for every run that should exist, whether its model and journal do, and what they say.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2`` §8; Sol's ruling 7:
"The run-roster checker must report MODEL_MISSING whether or not an observer warning could be written."

Offline only: it reads files after a job and is never called during play. The caller names the runs it expected
(the harness's game list), because a run that crashed before its session existed leaves no file to discover; runs
found on disk but not expected are reported too.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from inference.framework import audit_journal

FINAL = frozenset({"RUN_END", "BUDGET_STOP", "CONTROLLED_STOP", "CRASH", "CANCELLED"})


def _discovered(job_dir: Path) -> set[str]:
    stems = {path.name for path in (job_dir / "virelai").glob("*") if path.is_dir()}
    stems |= {path.name[: -len("_provenance.jsonl")] for path in (job_dir / "artifacts").glob("*_provenance.jsonl")}
    return stems


def _model_status(folder: Path) -> tuple[str, dict[str, Any] | None]:
    path = folder / "world_model.json"
    if not path.is_file():
        return "MODEL_MISSING", None
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "MODEL_UNREADABLE", None
    reason = (model.get("manifest") or {}).get("persist_reason")
    return ("FINAL" if reason in FINAL else "INTERIM_ONLY"), model


def _warnings(folder: Path) -> list[str]:
    path = folder / "observer_warnings.jsonl"
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(str(json.loads(line).get("event")))
        except ValueError:
            events.append("UNREADABLE_WARNING")
    return events


def check_runs(job_dir: str | Path, expected_run_stems: Iterable[str]) -> dict[str, dict[str, Any]]:
    """One entry per expected or discovered run stem: model, journal, warnings and the chapter's verdict."""
    root = Path(job_dir)
    expected = list(dict.fromkeys(expected_run_stems))
    report: dict[str, dict[str, Any]] = {}
    for stem in expected + sorted(_discovered(root) - set(expected)):
        folder = root / "virelai" / stem
        status, model = _model_status(folder)
        journal = root / "artifacts" / f"{stem}_provenance.jsonl"
        journal_status = audit_journal.read_journal(journal).status if journal.is_file() else "ABSENT"
        chapter = (model or {}).get("provenance") or {}
        report[stem] = {"expected": stem in expected, "model": status, "schema": (model or {}).get("schema"),
                        "journal": journal_status, "warnings": _warnings(folder),
                        "completeness": chapter.get("completeness"), "reasons": chapter.get("reasons")}
    return report


__all__ = ["check_runs"]
