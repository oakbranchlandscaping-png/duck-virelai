"""WO-DESC-B: ``world_report.md``, the semantic library report of one sealed schema-v3 world model.

The report is a rendering of ``world_description.describe_world`` and of stored receipts, nothing more:

* **Pure and deterministic.** No timestamps, no free text from the run, no conclusion the view does not hold.
  The first line embeds the model's full ``content_sha256``; every claim line ends in resolvable refs (stored ids,
  view pattern and question ids, ``manifest``, canonical JSON paths, transition ranges), so each line resolves back
  to the ledger. It is the semantic library report, not the paper's graded report (no executor provenance yet).
* **One writer, after the model.** ``write_world_report`` refuses a ``LIVE_VIEW`` model and an unsealed one,
  renders first, then writes a unique sibling and replaces the report atomically. On any failure it removes an
  existing ``world_report.md``: a report that exists always describes the model beside it.

``world_model_v2.write_canonical`` gains no Markdown. The solver calls ``write_world_report`` only after the
canonical write succeeded, and records a failure as the observer warning ``WORLD_REPORT_WRITE_FAILED``.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.framework import world_description, world_model_v2

REPORT_NAME = "world_report.md"


@dataclass(frozen=True)
class ReportResult:
    ok: bool
    path: str
    content_sha256: str | None
    error: str | None = None


# ---- rendering ------------------------------------------------------------------------------------------------
#
# Every bullet and numbered claim ends in ``; refs: a, b, ...``. A reference is a stored id (track, event, product,
# evidence, entity), a pattern or question id of the view (the appendix lists each pattern's events), ``manifest``
# or a top-level key for run metadata, a canonical JSON path into the model (``levels[0].gaps[3]``), or a transition
# range ``tA-tB`` for an aggregate over the record.

def _ids(values: Sequence[Any]) -> str:
    return ", ".join(str(value) for value in values) if values else "none"


def _claim(text: str, refs: Sequence[Any]) -> str:
    return f"{text}; refs: {', '.join(str(ref) for ref in refs)}"


def _verified_span(level: Mapping[str, Any]) -> list[str]:
    ids = [record["transition_id"] for record in level["description"]["transitions"]
           if record["record_status"] == "VERIFIED"]
    return [f"t{min(ids)}-t{max(ids)}"] if ids else []


# The validator requires only the status and the persist reason; a field the manifest lacks is omitted, never "None".
MANIFEST_FIELDS = (("persist_reason", "persist reason"), ("status", "status"), ("journal_check", "journal check"),
                   ("actions_executed", "actions executed"))


def _header(model: Mapping[str, Any]) -> list[str]:
    manifest = model.get("manifest") or {}
    return [
        f"# Semantic library report {model['content_sha256']}",
        "",
        _claim(f"- game: {model.get('game_id')}; run: {model.get('run_stem')}; schema: {model.get('schema')}",
               ["game_id", "run_stem", "schema"]),
        _claim("- " + "; ".join(f"{label}: {manifest[key]}" for key, label in MANIFEST_FIELDS if key in manifest),
               ["manifest"]),
        _claim(f"- view: {world_description.VIEW_SCHEMA}; levels: {len(model['levels'])}", ["levels"]),
        "",
    ]


def _scene_basis(level: Mapping[str, Any], at: str) -> tuple[str, list[str]]:
    """Where the scene stands, and what it rests on (revision 3). With no verified action it is the level's entry
    board, cited as such with no range. After actions it cites the entry board and only this level's own
    transitions: ``t{entry_node + 1}-t{last verified}``. Never ``t0``: the entry board is not a transition."""
    as_of = level["description"]["scene"]["as_of_transition"]
    refs = [f"{at}.entry", f"{at}.description.scene"]
    if as_of is None:
        return "as of level entry", refs
    return f"as of transition {as_of}", [*refs, f"t{int(level['description']['basis']['entry_node']) + 1}-t{as_of}"]


def _scene_lines(view: Mapping[str, Any], level: Mapping[str, Any], at: str) -> list[str]:
    scene = view["scene"]
    mismatch = scene["record_mismatch"]
    stated = f"at t{mismatch['transition_id']} ({mismatch['reason']})" if mismatch else "none"
    basis, refs = _scene_basis(level, at)
    lines = [
        "### Scene",
        "",
        _claim(f"- {basis}, life {scene['life']}; integrity {scene['integrity']}; record mismatch: {stated}",
               [*refs[:2], f"{at}.description.integrity", *refs[2:]]),
        _claim(f"- objects present {scene['objects_present']}, departed {scene['objects_departed']}, "
               f"unverified {scene['unverified_objects']}", refs),
        "",
    ]
    for item in view["objects"]:
        roles = _ids([role.get("role") if isinstance(role, Mapping) else role for role in item["roles"]])
        lines.append(_claim(f"- [{item['handle']}] {item['name']}; class {item['class']}, anchor {tuple(item['anchor'])}, "
                            f"{item['cell_count']} cells; roles: {roles}", [item["track_id"]]))
    return lines + [""]


def _dossier_lines(view: Mapping[str, Any], level: Mapping[str, Any], at: str) -> list[str]:
    """WO-G4-DOSSIER-A: each stored dossier, chapter by chapter, rendered from the same rows as its retrieval page."""
    if "lever_dossiers" not in level:
        return []
    lines = ["### Lever dossiers", ""]
    for row in view["dossiers"]:
        lines.append(_claim(f"- dossier {row['id']}: {row['status']}; witnesses {len(row['witnesses'])}",
                            [f"{at}.lever_dossiers", row["id"], *row["witnesses"]]))
        observed = world_description.dossier_observations(level, row["id"])  # B1: the record-derived observations
        if observed is not None:
            path = f"{at}.lever_dossiers[{row['id']}].observations"  # revision 2: the observations themselves
            lines.append(_claim(f"  - dossier {row['id']} observations: {observed['text']}",
                                [row["id"], path, *observed["refs"]]))
        for chapter in world_description.dossier_chapters(level, row["id"]):
            refs = [row["id"], *([chapter["product_id"]] if chapter["product_id"] else []), *chapter["evidence_refs"][:3]]
            lines.append(_claim(f"  - dossier {row['id']} {chapter['chapter']}: {chapter['status']} ({chapter['basis']}); "
                                f"source {chapter['source'] or 'none'}; {chapter['summary']}; evidence "
                                f"{len(chapter['evidence_refs'])}", refs))
            if chapter["chapter"] == "anatomy":  # revision 2: each channel's affected subject and observed events
                lines.extend(_claim(f"  - dossier {row['id']} anatomy channel {item['text']}", [row["id"], *item["refs"]])
                             for item in world_description.dossier_channels(chapter["facts"]))
    return lines + [""]


def _law_lines(view: Mapping[str, Any]) -> list[str]:
    lines = ["### Certified products and laws", ""]
    for row in view["laws"]:
        law = row["structured_law"]
        stated = (f"mask {law['cell_count']} cells {law['cell_runs']}, rewrite {law['rewrite']['from']}"
                  f"->{law['rewrite']['to']}") if law else row["note"]
        refs = [row["product_id"], row["payload_sha256"], law["law_version_id"] if law else None]
        mode = f" mode {row['mode']}" if row["mode"] else ""
        lines.append(_claim(f"- {row['gate_id']} {row['product_type']} r{row['revision']}{mode}: {stated}; "
                            f"evidence refs {len(row['evidence_refs'])}", [ref for ref in refs if ref]))
    for row in view["dossiers"]:
        if row["status"] == "NOT_BUILT":  # a v3-v5 level: the stub, until a stored dossier replaces it
            lines.append(_claim(f"- dossier {row['id']}: {row['status']}; witnesses {len(row['witnesses'])}",
                                [row["id"], *row["witnesses"]]))
    return lines + [""]


def _pattern_lines(view: Mapping[str, Any]) -> list[str]:
    lines = ["### Transformation patterns", ""]
    for pattern in view["patterns"]:
        pid = pattern["pattern_id"]
        explained = _ids([f"{basis} x{count}" for basis, count in sorted(pattern["explanations"].items())])
        types = _ids([f"{item['track_id']} {item['type']} ({item['status']})" for item in pattern["observed_effect_type"]])
        mirrored = _ids([f"{basis} x{count}" for basis, count in sorted(pattern["mirror_basis"].items())])
        lines.append(_claim(f"{pattern['rank']}. `{pid}` {pattern['sentence']}", [pid]))
        lines.append(_claim(f"   - explanations: {explained}; observed effect type: {types}", [pid]))
        lines.append(_claim(f"   - folded mirrors: {len(pattern['mirrors'])} ({mirrored})", [pid]))
    return lines + [""]


def _question_lines(view: Mapping[str, Any], at: str) -> list[str]:
    lines = ["### Open questions", ""]
    for question in view["questions"]:
        lines.append(_claim(f"{question['rank']}. `{question['question_id']}` {question['text']} "
                            f"Last transition {question['last_transition']}",
                            [question["question_id"], question["pattern_id"], *(f"{at}.gaps[{g}]" for g in question["gaps"])]))
    for index, item in enumerate(view["open_identity"]):
        lines.append(_claim(f"- open identity: {item['role']} ({item['gate_id']}); gaps {_ids(item['gaps'])}",
                            [f"{at}.description.scene.open_identity[{index}]", *(f"{at}.gaps[{g}]" for g in item["gaps"])]))
    return lines + [""]


def _gap_lines(level: Mapping[str, Any], at: str) -> list[str]:
    """Typed gaps by index, reason and chapter: the stored free text stays in the model, one path away."""
    lines = ["### Typed gaps", ""]
    for index, gap in enumerate(level.get("gaps") or ()):
        typed = "".join(f"; {name} {gap[name]}" for name in ("subject", "chapter") if gap.get(name) is not None)
        lines.append(_claim(f"- gap {index}: {gap.get('reason')}{typed}", [f"{at}.gaps[{index}]"]))
    return lines + [""]


def _census_lines(view: Mapping[str, Any], level: Mapping[str, Any], at: str) -> list[str]:
    census = view["census"]
    refs = [f"{at}.description.transitions", *_verified_span(level)]
    return [
        "### Record census",
        "",
        _claim(f"- verbs: {_ids([f'{verb} x{count}' for verb, count in census['verbs'].items()])}", refs),
        _claim(f"- explanations: {_ids([f'{basis} x{count}' for basis, count in census['explanations'].items()])}", refs),
        _claim(f"- primary {census['primary']}, folded {census['folded']}, still omitted {census['still_omitted']}", refs),
        "",
    ]


def _appendix_lines(view: Mapping[str, Any]) -> list[str]:
    lines = [f"### Appendix, level {view['level']}: folds and evidence index", ""]
    for fold in view["folds"]:
        lines.append(_claim(f"- fold t{fold['transition_id']} {fold['event_id']} ({fold['basis']}, "
                            f"{fold['explanation']['status']}): mirror of {_ids(fold['mirror_of'])}; track {fold['track_id']}",
                            [fold["event_id"], *fold["mirror_of"], fold["track_id"]]))
    for pattern in view["patterns"]:
        lines.append(_claim(f"- {pattern['pattern_id']}: {len(pattern['events'])} events", pattern["events"]))
    return lines + [""]


def render_world_report(model: Mapping[str, Any]) -> str:
    """The deterministic report of a sealed model. Pure: the same model always renders the same text."""
    view = world_description.describe_world(model)
    lines = _header(model)
    for index, (level, level_view) in enumerate(zip(model["levels"], view["levels"])):
        at = f"levels[{index}]"
        lines += [f"## Level {level_view['level']}", ""]
        for section in (_scene_lines(level_view, level, at), _law_lines(level_view), _dossier_lines(level_view, level, at),
                        _pattern_lines(level_view),
                        _question_lines(level_view, at), _gap_lines(level, at), _census_lines(level_view, level, at)):
            lines += section
    for level_view in view["levels"]:
        lines += _appendix_lines(level_view)
    return "\n".join(lines).rstrip("\n") + "\n"


# ---- writing ---------------------------------------------------------------------------------------------------

def _require_sealed(model: Mapping[str, Any]) -> str:
    stamp = model.get("content_sha256")
    if not stamp or stamp != world_model_v2.content_sha256(model):
        raise world_model_v2.WorldModelV2Error("the report is written only from a sealed model")
    if (model.get("manifest") or {}).get("persist_reason") == world_model_v2.LIVE_VIEW:
        raise world_model_v2.WorldModelV2Error("a live view is never written as a report")
    world_model_v2.validate(model)
    return str(stamp)


def _replace(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{REPORT_NAME}.", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def write_world_report(sealed: Mapping[str, Any], directory: str | Path) -> ReportResult:
    """Render, then replace ``world_report.md`` atomically. Never raises; on failure no stale report remains."""
    target = Path(directory) / REPORT_NAME
    stamp = sealed.get("content_sha256") if isinstance(sealed, Mapping) else None
    try:
        stamp = _require_sealed(sealed)
        _replace(target, render_world_report(sealed))
        return ReportResult(True, str(target), stamp)
    except Exception as exc:  # noqa: BLE001 - a failed report is reported, never raised into the solver
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        return ReportResult(False, str(target), stamp, f"{type(exc).__name__}: {exc}")


__all__ = ["REPORT_NAME", "ReportResult", "render_world_report", "write_world_report"]
