"""WO-PE-02: the writer-side hooks that feed the schema-v4 provenance chapter.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2`` §5, §8.

Extracted from ``solver.py`` and ``library_census.py`` under the tier ratchet (both files sit above the Green file
band), so the new logic lives here and the two files only call it. Three hooks:

- ``product_answers`` — at census time, each active product's origin and certifying answer references
  (``product_origins``; the target journal is rebuilt per level, so a frozen level's products exist only at its H1
  freeze);
- ``chapter`` — H1 from the writer's memory (no file is read); H2 from one read of the sealed journal;
- ``note_model_not_written`` — Sol's ruling 7: a run that ended before any model was written says so where observer
  context exists.

None of these runs per action. ````note_model_not_written`` never raises; ``chapter``'s H2 read and compilation never raise.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.framework import audit_journal
from inference.framework import product_content as product_content_chapter
from inference.framework import product_origins
from inference.framework import provenance_chapter as pc


def product_answers(machine: Any) -> dict[str, Any]:
    """Each active product's origin and certifying answer references (``product_origins``; revision 2)."""
    refs = {}
    for contract in machine.target_registry.ordered():
        product = machine.target_journal.active_product(contract.target_id)
        if product is not None:
            refs[product.product_id] = product_origins.entry(machine, contract.target_id, product)
    return refs


def product_content(machine: Any) -> dict[str, Any]:
    """WO-PE-03A (schema v5): each active product's exact body and strict digest (``product_content.capture``)."""
    return product_content_chapter.capture(machine)


def gate_answer_records(state_path: Path) -> list[dict[str, Any]] | None:
    """The accepted-answer sidecar beside the runtime state (R7), read once at H2; None when there is none."""
    suffix = f"_{RUNTIME_STATE_FILENAME}"
    if not state_path.name.endswith(suffix):
        return None
    path = state_path.with_name(state_path.name.replace(suffix, "_gate_answers.jsonl"))
    if not path.is_file():
        return None
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _h1(capture: str, enabled: bool, record: Any, prefixes: list) -> dict[str, Any]:
    """H1: the writer's in-memory count and head, labelled WRITER_REPORTED; remembered so H2 can verify the prefix."""
    writer = None
    if enabled:
        writer = (int(record.seq), str(record.head)) if record is not None else (0, audit_journal.GENESIS)
        prefixes.append({"event_count": writer[0], "head_hash": writer[1]})
    return pc.h1(capture=capture, writer=writer)


def _h2(payload: dict[str, Any], *, capture: str, enabled: bool, failed: str, path: Path, state_path: Path,
        prefixes: list) -> dict[str, Any]:
    """H2: the one read of the sealed journal (``play``'s ``finally`` seals before the final write)."""
    data, reason = None, None
    if not enabled:
        reason = "CAPTURE_DISABLED"
    else:
        try:
            data = path.read_bytes()  # the one read: hashed and parsed from this buffer
        except FileNotFoundError:
            reason = "JOURNAL_MISSING"
        except OSError:
            reason = "JOURNAL_UNREADABLE"
    return pc.h2(payload, data=data, sidecar=path.name, capture=capture, writer_failure=failed or None,
                 answer_records=gate_answer_records(state_path), interim_prefixes=list(prefixes),
                 unavailable_reason=reason)


def chapter(payload: dict[str, Any], *, final: bool, analyzer: Any, state_path: Path, prefixes: list,
            warn: Callable[[str, str], None]) -> dict[str, Any]:
    """The chapter for one model write. Never raises: a failure is ``PROVENANCE_CHAPTER_FAILED`` and an UNAVAILABLE
    chapter, because provenance never costs the model."""
    enabled = bool(getattr(analyzer, "_provenance_enabled", False))
    record = getattr(analyzer, "_provenance", None)
    failed = str(getattr(record, "failed", "") or "")
    capture = "DISABLED" if not enabled else "FAILED" if failed else "ENABLED"
    if not final:
        return _h1(capture, enabled, record, prefixes)
    from inference.agent.provenance_capture import journal_path

    path = journal_path(state_path)
    try:
        return _h2(payload, capture=capture, enabled=enabled, failed=failed, path=path, state_path=state_path,
                   prefixes=prefixes)
    except Exception as exc:  # provenance never costs the model
        warn("PROVENANCE_CHAPTER_FAILED", f"{type(exc).__name__}: {exc}")
        return pc.h2(payload, data=None, sidecar=path.name, capture=capture, writer_failure=failed or None,
                     unavailable_reason="CHAPTER_COMPILE_FAILED")


def note_model_not_written(solver: Any, game: Any, pass_index: int, exc: Exception) -> None:
    """Ruling 7: where observer context exists and no model was written, record ``WORLD_MODEL_NOT_WRITTEN``. The run
    roster reports MODEL_MISSING whether or not this could be written."""
    if solver.job_dir is None or solver.virelai_mode == "off":
        return
    try:
        game_id = str(game.game_run.game_id)
        run_stem = solver._run_stem(game_id, pass_index)
        folder = solver.job_dir / "virelai" / run_stem
        if (folder / "world_model.json").exists():
            return
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "observer_warnings.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"schema": "virelai-observer-warning-v1", "event": "WORLD_MODEL_NOT_WRITTEN",
                                     "detail": f"{type(exc).__name__}: {exc}", "game_id": game_id,
                                     "run_stem": run_stem, "through_step": 0}, sort_keys=True) + "\n")
    except Exception:
        return


__all__ = ["chapter", "gate_answer_records", "note_model_not_written", "product_answers"]
