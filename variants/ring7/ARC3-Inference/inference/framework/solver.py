"""TAAF solver adapter for the existing tool-using harness."""

from __future__ import annotations

import asyncio
import contextlib
import copy
import functools
import html
import json
import logging
import os
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import arcengine
import taaf.game
from taaf.solver import Solver

from inference.agent.action_names import (
    to_engine_action,
    to_model_action,
    to_model_actions,
)
from inference.agent.runtime_state import (
    Frame,
    HistoryEntry,
    RUNTIME_STATE_FILENAME,
    write_runtime_state,
)
from inference.agent.tool_agent import ToolAgent
from inference.framework.kaggle import (
    DEFAULT_QWEN_MODEL_DATASET_SOURCE,
    DEFAULT_SERVED_MODEL_NAME,
    DEFAULT_VLLM_MAX_MODEL_LEN,
    DEFAULT_VLLM_PORT,
    DEFAULT_VLLM_TENSOR_PARALLEL_SIZE,
    DEFAULT_VLLM_WHEELHOUSE_DATASET_SOURCE,
    DEFAULT_WHEELHOUSE_STAMP_TEXT,
    DuckKaggleVllmConfig,
    duck_kaggle_dataset_sources,
    duck_kaggle_setup_command,
    duck_kaggle_teardown_command,
)
from inference.utils.viewer_artifacts import (
    append_raw_events_sidecar,
    reset_raw_events_sidecar,
)

AnalyzerFactory = Callable[[taaf.game.Game, int], Any]

ANALYZER_RETRY_BACKOFF_SECONDS = 1.0
DEFAULT_CANCEL_DRAIN_TIMEOUT_SECONDS = 120.0
_LOCAL_SERVER_PROCESS_ENV_KEYS = (
    "LOCAL_ANALYZER_API_KEY",
    "OPENAI_API_KEY",
    "LOCAL_ANALYZER_BASE_URL",
    "OPENAI_BASE_URL",
    "LOCAL_ANALYZER_PROVIDER",
    "OPENAI_PROVIDER",
)


@dataclass
class _LocalServerRuntime:
    index: int
    repo_dir: Path
    api_key_file: Path
    env_overrides: dict[str, str]
    base_url: str
    api_key: str = ""


def _analyzer_reported_tokens(analyzer: Any) -> int:
    value = (
        getattr(analyzer, "generated_tokens", None)
        if hasattr(analyzer, "generated_tokens")
        else getattr(analyzer, "total_tokens", 0)
    )
    return max(0, int(value or 0))


def artifact_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _grid_from_state(state: taaf.game.GameState | None) -> tuple[tuple[int, ...], ...]:
    if state is None:
        return ()
    data = state.frame.data
    rows = data.tolist() if hasattr(data, "tolist") else data
    return tuple(tuple(int(cell) for cell in row) for row in rows)


def _level_number(game: taaf.game.Game) -> int:
    state = game.current_state
    completed = int(state.levels_completed)
    if state.won:
        return max(1, int(game.number_of_levels))
    return max(1, min(int(game.number_of_levels), completed + 1))


logger = logging.getLogger(__name__)

from inference.framework.virelai_handoff_v63 import (
    fingerprint_text,
    locations_as_dicts,
    payload_report_locations,
)


def _atomic_write_text(path: Path, text: str) -> None:
    """Write exact UTF-8 text without adding or normalizing whitespace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
    )
    try:
        with temporary.open("w", encoding="utf-8", newline="") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    _atomic_write_text(path, rendered + "\n")


import re as _re6

# (older) render path and require a literal plural "cells" that a 1-cell
# target's "1 cell" would not match.
_RING6_COUNT_RE = _re6.compile(
    r"^\s*(TOUCHED|NOT REACHED|NEVER ATTEMPTED|UNREACHABLE|queued)\s+(\d+)")
_RING6_TARGET_RE = _re6.compile(
    r"^\s*#\d+\s+\((\d+),\s*(\d+)\)\s+class\s+\d+\s+(\d+)\s+cells?\s+.{1,3}\s+(.+?)\s*$")
_RING6_COUNT_KEY = {"TOUCHED": "touched", "NOT REACHED": "not_reached",
                    "NEVER ATTEMPTED": "never", "UNREACHABLE": "unreachable",
                    "queued": "queued"}


def _ring6_worldline_rows(ctx, worldlines=None, verdicts=None, mechanism_results=None):
    """ctx.woven_worldlines/woven_role_verdicts -> (the card's `worldlines`
    list, X) where X is the total distinct visual-object count across every
    ### (LIST 1's X -- the sum of len(collapse_fingerprints(...)) per
    worldline, matching diagnostics/integration_roster.py's own grain).
    See the module comment above for the exact sourcing."""
    from virelai_v4.capture.clay import collapse_fingerprints

    worldlines = worldlines if worldlines is not None else (ctx.woven_worldlines or [])
    if hasattr(worldlines, "values"):
        worldlines = list(worldlines.values())
    verdicts = verdicts if verdicts is not None else (ctx.woven_role_verdicts or {})
    mechanism_results = (mechanism_results if mechanism_results is not None
                         else (getattr(ctx, "mechanism_probe_results", None) or {}))

    rows = []
    total_visual_objects = 0
    for wl in worldlines:
        members = [(node_index, "", region) for (node_index, region) in wl.steps]
        entries = collapse_fingerprints(members)
        if not entries:
            continue
        total_visual_objects += len(entries)
        counts = [e.cell_count for e in entries]

        # Settled/flash/tick over this ###'s distinct visual-object members --
        # transcribed from diagnostics/integration_roster.py:_member_spans
        # (WO-MERGE-01), same computation, kept local so this function's only
        # import is collapse_fingerprints.
        at = {ap.node_index: e.fingerprint for e in entries for ap in e.trail}
        settled = flash = tick = 0
        for e in entries:
            nodes = [ap.node_index for ap in e.trail]
            if len(nodes) > 1:
                settled += 1
                continue
            n = nodes[0]
            before = at.get(n - 1)
            if before is not None and before == at.get(n + 1) and before != e.fingerprint:
                flash += 1
            else:
                tick += 1

        v = verdicts.get(wl.id)
        role = getattr(v, "role", None) if v else None
        seal = getattr(v, "confidence", None) if v else None
        fields = []
        if v is not None and getattr(v, "ground", False):
            fields.append("GROUND")
        if v is not None and getattr(v, "wall", False):
            fields.append("WALL")

        first_region = wl.first_region
        all_cells = [cell for entry in entries for cell in entry.fingerprint[1]]
        bbox = None
        if all_cells:
            rs = [cell[0] for cell in all_cells]
            cs = [cell[1] for cell in all_cells]
            bbox = (min(rs), min(cs), max(rs), max(cs))
        rows.append({
            "id": f"###{wl.id}",
            "_wid": int(wl.id),
            "cells": (min(counts), max(counts)),
            "anchor": getattr(first_region, "anchor", (0, 0)),
            "bbox": bbox,
            "role": role,
            "seal": seal,
            "fields": tuple(fields),
            "cov": int(getattr(v, "band1_coverage", 0) or 0) if v is not None else 0,
            "revisit": (int(getattr(v, "band1_revisits", 0) or 0)
                        if v is not None else None),
            "ticks": tick,
            "multi": settled if settled >= 2 else 0,
            "basis": getattr(v, "basis", "") if v is not None else "",
            "parallax": getattr(v, "parallax", "") if v is not None else "",
            "band1": getattr(v, "band1", "") if v is not None else "",
        })

    # Convert the weave's causal findings into firewall-safe spatial effects.
    # Internal ### ids are used only for the join and never rendered.
    by_wid = {row["_wid"]: row for row in rows}
    partner_re = _re6.compile(r"###(\d{3})")
    for row in rows:
        if row.get("role") != "LEVER":
            continue
        lever_wid = row["_wid"]
        mechanisms = dict(mechanism_results.get(lever_wid, {}) or {})
        partner_ids = set(mechanisms)
        partner_ids.update(int(value) for value in partner_re.findall(row.get("basis") or ""))
        partner_ids.discard(lever_wid)
        effects = []
        for partner_id in sorted(partner_ids):
            partner = by_wid.get(partner_id)
            if partner is None:
                continue
            effects.append({
                "anchor": partner.get("anchor"),
                "bbox": partner.get("bbox"),
                "cells": (partner.get("cells") or (0, 0))[1],
                "mechanism": mechanisms.get(partner_id, "UNKNOWN"),
            })
        row["effects"] = effects
    return rows, total_visual_objects


def _ring6_ego_dict(ctx, node_actions, worldlines=None, verdicts=None, cuts=None):
    """role=="EGO" worldlines' footprint/anchor (solid), plus the per-button
    bearing table (KNOWN GAP -- see module comment). Never raises; a failure
    on the bearing table leaves `model`/`observed` absent and the card's own
    fallback sentence renders instead (virelai_field_card_v6's designed
    behaviour for missing data, exercised by DESIGN.md SS4 fixture F5)."""
    worldlines = worldlines if worldlines is not None else (ctx.woven_worldlines or [])
    if hasattr(worldlines, "values"):
        worldlines = list(worldlines.values())
    verdicts = verdicts if verdicts is not None else (ctx.woven_role_verdicts or {})
    sealed_ids = [wid for wid, v in verdicts.items()
                  if getattr(v, "role", None) == "EGO"]

    ego = {}
    if not sealed_ids:
        return ego
    ego["sealed"] = [f"###{wid}" for wid in sealed_ids]
    by_id = {w.id: w for w in worldlines}
    wl0 = by_id.get(sealed_ids[0])
    if wl0 is not None:
        ego["footprint"] = wl0.first_region.cell_count
        ego["anchor"] = wl0.first_region.anchor

    cuts = (cuts if cuts is not None else
            (getattr(ctx, "coverage_hold_cuts", None)
             or getattr(ctx, "weave_sweep_cuts", None)))
    if node_actions and worldlines and cuts:
        try:
            from virelai_v4.weave.ego_read import action_bearings
            from virelai_v4.weave.action_roster import life_boundary_edges
            boundaries = life_boundary_edges(cuts)
            emap_by_id = action_bearings(worldlines, node_actions, boundaries)
            m = emap_by_id.get(sealed_ids[0])
            if m is not None:
                ego["model"] = {ab.action: tuple(ab.bearing) for ab in m.bearings}
                ego["observed"] = sorted({ao.action for ao in m.observed}, key=str)
        except Exception:
            pass  # KNOWN GAP -- named in the module comment above.
    return ego


def _ring6_frontier_dict(ctx):
    """Calls the live weave.collide_drive.coverage_roster(ctx) renderer and
    parses its own text -- the renderer is the single producer of this fact
    (WO-COVERAGE-ROSTER-01); this is not a read of a log file."""
    from virelai_v4.weave.collide_drive import coverage_roster

    text = coverage_roster(ctx)
    f = {}
    targets = []
    for line in text.splitlines():
        m = _RING6_COUNT_RE.match(line)
        if m:
            f[_RING6_COUNT_KEY[m.group(1)]] = int(m.group(2))
            continue
        m = _RING6_TARGET_RE.match(line)
        if m:
            targets.append({
                "anchor": (int(m.group(1)), int(m.group(2))),
                "cells": int(m.group(3)),
                "state": m.group(4),
            })
    f["targets"] = targets
    return f


def _ring6_node_actions(ctx):
    """captain.ctx.frame_record_log -> the (action_id, target_cell) list
    action_bearings/infer_roles consume. The ruled reader
    (capture/ledger_build.py:258, load_node_actions_from_log) called on the
    log -- the SAME call Virelai's own _land_weave_roles (virelai.py:2069)
    and _land_weave_repeated_contact (virelai.py:1986) make, confirmed at
    both file:lines this session. Not a live collection: the retired sidecar
    readers this replaced lost 1222/1366 rows on the live canary
    (ledger_build.py's own retirement note) -- the log is the one dense,
    correctly-indexed source."""
    from virelai_v4.capture.ledger_build import load_node_actions_from_log

    log = getattr(ctx, "frame_record_log", None)
    if log is None or len(log) == 0:
        return []
    return load_node_actions_from_log(log)


def _card_dict_from_captain(captain, *, live: bool = False):
    """The one function WO-RING6-01 Phase B.4 charters: live virelai_v4
    captain state -> the dict virelai_field_card_v6.render_field_card reads.
    Never raises past itself -- each section is independently best-effort so
    one missing field costs that field, never the whole card (matching
    render_field_card's own per-section fallback discipline)."""
    ctx = captain.ctx
    d = {"hud": None, "win_seen": False}

    live_cuts = None
    live_node_actions = None
    live_worldlines = None
    live_verdicts = None
    if live:
        try:
            from virelai_v4.weave.coverage_sweep import compute_current_weave_state
            log = getattr(ctx, "frame_record_log", None)
            (live_cuts, live_node_actions,
             live_worldlines, live_verdicts) = compute_current_weave_state(log)
            if not live_worldlines:
                live_cuts = live_node_actions = live_worldlines = live_verdicts = None
        except Exception:
            live_cuts = live_node_actions = live_worldlines = live_verdicts = None

    d["game_id"] = getattr(captain, "game_id", "")
    d["level"] = getattr(ctx, "last_level_seen", 0)
    d["lives"] = getattr(ctx, "lives_used", 0)
    d["actions"] = getattr(captain, "action_counter", 0)

    header = getattr(getattr(ctx, "semantic_library", None), "header", None)
    if header is not None:
        d["world_type"] = getattr(header, "world_type", "")
        d["ego_mode"] = getattr(header, "ego_mode", "")

    spawn_grid = getattr(ctx, "spawn_grid", None)
    if spawn_grid is not None:
        try:
            shape = getattr(spawn_grid, "shape", None)
            d["grid"] = ((int(shape[0]), int(shape[1])) if shape is not None
                         else (len(spawn_grid), len(spawn_grid[0])))
        except Exception:
            pass

    try:
        d["worldlines"], d["visual_objects"] = _ring6_worldline_rows(
            ctx, worldlines=live_worldlines, verdicts=live_verdicts,
            mechanism_results=getattr(ctx, "mechanism_probe_results", None),
        )
    except Exception:
        d["worldlines"], d["visual_objects"] = [], None

    try:
        d["frontier"] = _ring6_frontier_dict(ctx)
    except Exception:
        d["frontier"] = {}

    try:
        node_actions = (live_node_actions if live_node_actions is not None
                        else _ring6_node_actions(ctx))
    except Exception:
        node_actions = []

    try:
        d["ego"] = _ring6_ego_dict(
            ctx, node_actions, worldlines=live_worldlines,
            verdicts=live_verdicts, cuts=live_cuts,
        )
    except Exception:
        d["ego"] = {}
    if d["ego"].get("model") or d["ego"].get("observed"):
        d["roster"] = sorted(
            set(d["ego"].get("model") or ()) | set(d["ego"].get("observed") or ()),
            key=str)

    if d["ego"].get("sealed"):
        verdicts = live_verdicts if live_verdicts is not None else (ctx.woven_role_verdicts or {})
        first_wid = int(d["ego"]["sealed"][0].removeprefix("###"))
        v = verdicts.get(first_wid)
        d["ego_seal"] = getattr(v, "confidence", None) if v is not None else None

    return d


def _engine_action_names(game: taaf.game.Game) -> list[str]:
    names: list[str] = []
    for action_id in game.current_state.available_actions:
        try:
            name = arcengine.GameAction.from_id(int(action_id)).name
        except Exception:
            continue
        if name == "RESET":
            continue
        if name not in names:
            names.append(name)
    return names


def _model_mouse_action_data(
    action_data: dict[str, Any] | None = None,
) -> dict[str, int]:
    data = action_data or {}
    return {"row": int(data.get("y", 0)), "col": int(data.get("x", 0))}


def _format_action_display(
    action_name: str, action_data: dict[str, Any] | None = None
) -> str:
    if action_name == "ACTION6":
        data = _model_mouse_action_data(action_data)
        return f"MOUSE(row={data['row']}, col={data['col']})"
    return to_model_action(action_name)


def _is_engine_game_over(game: taaf.game.Game) -> bool:
    return game.current_state.raw.state == arcengine.GameState.GAME_OVER


def _is_run_complete(game: taaf.game.Game) -> bool:
    return game.current_state.raw.state == arcengine.GameState.WIN


def _write_transcript_html(transcript_path: Path, html_path: Path, title: str) -> None:
    if not transcript_path.exists():
        return
    html_path.parent.mkdir(parents=True, exist_ok=True)
    text = transcript_path.read_text(encoding="utf-8")
    body = (
        '<!doctype html>\n<html><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        "<style>"
        "body{background:#1e1e1e;color:#e0e0e0;font-family:-apple-system,system-ui,sans-serif;"
        "padding:20px;max-width:1100px;margin:0 auto;line-height:1.4;}"
        "h1{color:#fff;}pre{white-space:pre-wrap;background:#111;padding:16px;border-radius:6px;"
        "border:1px solid #333;overflow:auto;}"
        "</style></head><body>"
        f"<h1>{html.escape(title)}</h1><pre>{html.escape(text)}</pre>"
        "</body></html>\n"
    )
    html_path.write_text(body, encoding="utf-8")


@dataclass
class _HarnessGameSession:
    solver: "HarnessSolver"
    game: taaf.game.Game
    analyzer: Any
    game_index: int
    pass_index: int
    state_path: Path
    transcript_path: Path
    analysis_html_relpath: str
    stop_event: threading.Event
    viewer_data_path: Path
    started_at: float = field(default_factory=time.monotonic)
    history_entries: list[HistoryEntry] = field(default_factory=list)
    viewer_events: list[dict[str, Any]] = field(default_factory=list)
    analysis_step: int = 0
    last_engine_action: str | None = None
    token_baseline: int = 0
    _viewer_events_flushed: int = field(default=0, init=False, repr=False)

    def current_frame(self) -> Frame:
        return Frame(
            grid=_grid_from_state(self.game.current_state),
            step=self.action_count,
            level=_level_number(self.game),
        )

    def write_runtime_state(self) -> None:
        write_runtime_state(
            self.state_path,
            current_frame=self.current_frame(),
            history=self.history_entries,
        )

    def seed_initial_history(self) -> None:
        if not self.history_entries:
            self.history_entries.append(
                HistoryEntry(action="", frame=self.current_frame())
            )

    @property
    def action_count(self) -> int:
        run = self.game.game_run
        return len(run.history) if run is not None else 0

    def runtime_limit_reached(self) -> bool:
        if self.solver.max_runtime_s_per_game is None:
            return False
        return (
            time.monotonic() - self.started_at
        ) >= self.solver.max_runtime_s_per_game

    def timing_payload(self) -> dict[str, float | None]:
        elapsed = max(0.0, time.monotonic() - self.started_at)
        if self.solver.max_runtime_s_per_game is None:
            remaining = None
        else:
            remaining = max(0.0, self.solver.max_runtime_s_per_game - elapsed)
        return {"run_elapsed_seconds": elapsed, "time_remaining_seconds": remaining}

    def request_timeout_seconds(self) -> float | None:
        candidates: list[float] = []
        configured = getattr(self.analyzer, "_timeout", None)
        try:
            if configured is not None:
                candidates.append(float(configured))
        except (TypeError, ValueError):
            pass
        if self.solver.max_runtime_s_per_game is not None:
            remaining = self.timing_payload()["time_remaining_seconds"]
            if remaining is not None:
                candidates.append(float(remaining))
        soft_remaining = self.solver.soft_time_remaining_seconds()
        if soft_remaining is not None:
            candidates.append(soft_remaining)
        if not candidates:
            return None
        return max(0.1, min(candidates))

    def should_stop(self) -> bool:
        run = self.game.game_run
        if run is None or run.state != "playing":
            return True
        if self.stop_event.is_set():
            return True
        if _is_run_complete(self.game):
            return True
        if self.runtime_limit_reached():
            return True
        if (
            self.solver.max_actions_per_game is not None
            and self.action_count >= self.solver.max_actions_per_game
        ):
            return True
        return False

    def _ring6_marker(self, event: str, **fields: Any) -> None:
        """Write one machine-readable probe marker to both durable artifacts.

        Marker lines are operational evidence, not model conversation history.
        Ring 6.3 request markers may be written from the guarded observer while
        an analyzer turn is active; their event names describe completed facts.
        """
        payload = {"event": event, **fields}
        line = "RING6_%s %s" % (event, json.dumps(payload, sort_keys=True, default=str))
        try:
            with self.transcript_path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
        except OSError:
            pass
        try:
            frame = self.current_frame()
            self.viewer_events.append({
                **self._base_viewer_event(frame),
                "type": "probe",
                "title": "Ring 6 %s" % event.replace("_", " ").title(),
                "analysis_step": 0,
                "action_num": self.action_count,
                "actor": "captain",
                **fields,
            })
            self.write_viewer_payload()
        except Exception:
            pass
        logger.info("%s", line)


    def _ring63_run_root(self) -> Path:
        if self.solver.job_dir is not None:
            return self.solver.job_dir
        # transcript_path is normally <job>/transcripts/<run_stem>.txt.
        return self.transcript_path.parent.parent


    def _ring63_run_stem(self) -> str:
        return self.transcript_path.stem


    def _ring63_append_audit(self, record: dict[str, Any]) -> None:
        path = (
            self._ring63_run_root()
            / "handoff_audit"
            / f"{self._ring63_run_stem()}.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as file:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")


    def _ring63_finalize_report(
        self,
        *,
        game_id: str,
        snapshots: int,
        fallback: bool,
        captain_fault: bool,
    ) -> None:
        """Fingerprint and persist the exact report without risking gameplay."""
        report = str(getattr(self, "_virelai_card", "") or "")
        fingerprint = fingerprint_text(report)
        relative_path = Path("captain_reports") / f"{self._ring63_run_stem()}.txt"
        report_path = self._ring63_run_root() / relative_path
        self._ring63_report_meta = {
            "schema": "ring6.3-handoff-v1",
            "game_id": game_id,
            "pass_index": self.pass_index,
            "report_path": relative_path.as_posix(),
            "report_sha256": fingerprint.sha256,
            "report_characters": fingerprint.characters,
            "report_utf8_bytes": fingerprint.utf8_bytes,
            "snapshots": int(snapshots),
            "fallback": bool(fallback),
            "captain_fault": bool(captain_fault),
        }
        self._ring6_marker("REPORT_RENDERED", **self._ring63_report_meta)
        try:
            _atomic_write_text(report_path, report)
            persisted = fingerprint_text(report_path.read_text(encoding="utf-8"))
            if persisted != fingerprint:
                raise RuntimeError("persisted report fingerprint mismatch")
            self._ring63_report_persisted = True
            self._ring6_marker("REPORT_PERSISTED", **self._ring63_report_meta)
        except Exception as exc:
            self._ring63_report_persisted = False
            self._ring6_marker(
                "REPORT_PERSIST_FAILED",
                **self._ring63_report_meta,
                error_type=type(exc).__name__,
                error_detail=str(exc).strip()[:240],
            )


    def _ring63_request_observer(self, event: str, record: dict[str, Any]) -> None:
        """Audit the detached provider payload.  This callback is no-throw."""
        if not isinstance(getattr(self, "_ring63_report_meta", None), dict):
            # No probe report was finalized (e.g. the VIRELAI_RING6=0 control
            # arm).  A handoff that never existed must not emit attachment
            # markers, failure markers, or audit records.
            return
        try:
            request_id = str(record.get("request_id", "") or "unknown")
            base = {
                "schema": "ring6.3-handoff-v1",
                "event": event,
                "game_id": (
                    self._ring63_report_meta.get("game_id")
                    if isinstance(getattr(self, "_ring63_report_meta", None), dict)
                    else str(self.game_index)
                ),
                "pass_index": self.pass_index,
                "request_id": request_id,
                "analysis_step": record.get("analysis_step"),
                "analysis_invocation": record.get("analysis_invocation"),
                "request_index_within_turn": record.get("request_index_within_turn"),
                "global_action_count": record.get("action_num"),
                "display_action_num": record.get("display_action_num"),
            }
            report = str(getattr(self, "_virelai_card", "") or "")
            report_meta = dict(getattr(self, "_ring63_report_meta", {}) or {})

            if event == "prepared":
                provider_payload = record.get("provider_payload")
                payload = provider_payload if isinstance(provider_payload, dict) else {}
                all_locations = payload_report_locations(payload, report)
                user_locations = payload_report_locations(payload, report, roles={"user"})
                prepared_count = int(getattr(self, "_ring63_prepared_count", 0)) + 1
                self._ring63_prepared_count = prepared_count
                audit = {
                    **base,
                    **report_meta,
                    "prepared_sequence": prepared_count,
                    "exact_occurrences": len(all_locations),
                    "user_exact_occurrences": len(user_locations),
                    "locations": locations_as_dicts(all_locations),
                }
                current_fingerprint = fingerprint_text(report)
                fingerprint_matches = bool(report_meta) and all((
                    report_meta.get("report_sha256") == current_fingerprint.sha256,
                    report_meta.get("report_characters") == current_fingerprint.characters,
                    report_meta.get("report_utf8_bytes") == current_fingerprint.utf8_bytes,
                ))
                audit["fingerprint_matches"] = fingerprint_matches
                self._ring63_append_audit(audit)

                verified = (
                    bool(report)
                    and len(user_locations) == 1
                    and fingerprint_matches
                )
                verified_ids = getattr(self, "_ring63_verified_request_ids", None)
                if verified_ids is None:
                    verified_ids = set()
                    self._ring63_verified_request_ids = verified_ids
                if verified:
                    verified_ids.add(request_id)
                    if not getattr(self, "_ring63_payload_saved", False):
                        handoff_path = (
                            self._ring63_run_root()
                            / "handoff_requests"
                            / f"{self._ring63_run_stem()}.json"
                        )
                        _atomic_write_json(
                            handoff_path,
                            {**audit, "provider_payload": payload},
                        )
                        self._ring63_payload_saved = True
                    if not getattr(self, "_ring63_attachment_marked", False):
                        self._ring63_attachment_marked = True
                        self._ring6_marker(
                            "REPORT_ATTACHED",
                            request_id=request_id,
                            analysis_step=record.get("analysis_step"),
                            global_action_count=record.get("action_num"),
                            exact_occurrences=len(all_locations),
                            user_exact_occurrences=len(user_locations),
                            **report_meta,
                        )

                first_request_failed = prepared_count == 1 and not verified
                duplicate_failed = len(user_locations) > 1
                if first_request_failed or duplicate_failed:
                    self._ring6_marker(
                        "REPORT_ATTACH_FAILED",
                        request_id=request_id,
                        reason=(
                            "first_request_missing_or_nonunique"
                            if first_request_failed else "duplicate_user_reports"
                        ),
                        exact_occurrences=len(all_locations),
                        user_exact_occurrences=len(user_locations),
                        **report_meta,
                    )
                return

            audit = {
                **base,
                **report_meta,
                **{
                    key: record.get(key)
                    for key in ("status_code", "finish_reason", "error_type", "error_detail")
                    if record.get(key) is not None
                },
            }
            self._ring63_append_audit(audit)
            verified_ids = getattr(self, "_ring63_verified_request_ids", set())
            if event == "completed" and request_id in verified_ids:
                if not getattr(self, "_ring63_request_accepted_marked", False):
                    self._ring63_request_accepted_marked = True
                    self._ring6_marker(
                        "REPORT_REQUEST_ACCEPTED",
                        request_id=request_id,
                        status_code=record.get("status_code"),
                        finish_reason=record.get("finish_reason"),
                        **report_meta,
                    )
            elif event == "failed" and request_id in verified_ids:
                self._ring6_marker(
                    "REPORT_REQUEST_FAILED",
                    request_id=request_id,
                    error_type=record.get("error_type"),
                    error_detail=record.get("error_detail"),
                    **report_meta,
                )
        except Exception as exc:
            try:
                self._ring6_marker(
                    "REPORT_AUDIT_FAULT",
                    error_type=type(exc).__name__,
                    error_detail=str(exc).strip()[:240],
                )
            except Exception:
                pass


    def _frame_data(self):
        """arcengine FrameDataRaw -> FrameData. Transcribed (R-C: origin cited,
        not copied) from the golden harness's own agents/agent.py:142-152
        _convert_raw_frame_data, confirmed verbatim at that file:line this
        session (WO-RING6-01 Phase B.1). The two models differ in one field
        only -- `frame` as nested lists vs ndarrays."""
        raw = self.game.current_state.raw
        return arcengine.FrameData(
            game_id=raw.game_id, frame=[a.tolist() for a in raw.frame],
            state=raw.state, levels_completed=raw.levels_completed,
            win_levels=raw.win_levels, guid=raw.guid,
            full_reset=raw.full_reset, available_actions=raw.available_actions)


    def _virelai_opening(self) -> None:
        """Ring 6 (WO-RING6-01), the one variable: the golden captain probes
        before the model's first token, then stops for good. Presses go
        through _execute_action with generated_tokens=0 -- the shape
        _execute_auto_reset already uses (this file, ~line 685-687) -- so they
        cost no model tokens and land in the duck's own ledger with no new
        plumbing.

        `act` -- captain.choose_action's return -- IS the arcengine GameAction
        id (an enum member), not a wrapper carrying a separate `.id`; this
        file's own _execute_auto_reset (~line 686) already passes a bare
        GameAction as ActionInput's `id=`, confirmed at that line this
        session. Ring 6.2 does not forward the enum member's engine-owned
        model verbatim: arcengine includes an internal `game_id` field which
        TAAF rejects on simple actions. `captain_action_data` is the explicit
        compatibility boundary: `{}` for simple actions, public x/y only for
        the complex mouse action.

        node_actions for the card (Phase B.4) is read AFTER the loop, from
        captain.ctx.frame_record_log via the ledger's own reader -- see
        _ring6_node_actions, never collected live here: the log is the
        established single source (virelai.py:1986, 2069 both read it the
        same way before calling action_bearings/infer_roles).

        VIRELAI_RING6=0 disables this entirely (the control arm, one variable
        vs ring5). A captain fault costs only the card (its fallback
        sentences render); it never costs the game -- which requires the
        captain's own import and construction to be inside the same guard as
        the probing loop, not top-level statements ahead of it (the defect a
        live Kaggle run caught 2026-08-29: a bare top-level import, executed
        before any try/except, propagated a ModuleNotFoundError out of this
        function and crashed the whole game instead of degrading to the
        fallback card)."""
        # A usable fallback exists before any optional import.  This method's
        # contract is stronger than "the probe loop is guarded": no failure in
        # setup, reporting or rendering may prevent Duck from taking control.
        run = self.game.game_run
        game_id = str(run.game_id if run is not None else self.game_index)
        self._virelai_card = (
            "=== CAPTAIN PROBE REPORT — %s ===\n"
            "The Captain report is unavailable because the bounded probe phase did not "
            "produce a readable record. Treat every world-specific role as unknown.\n"
            "=== END CAPTAIN PROBE REPORT ===" % game_id
        )
        if os.environ.get("VIRELAI_RING6", "1") == "0":
            return

        max_lives = int(os.environ.get("VIRELAI_RING6_LIVES", "2"))
        max_actions = int(os.environ.get("VIRELAI_RING6_MAX_ACTIONS", "320"))
        max_seconds = float(os.environ.get("VIRELAI_RING6_MAX_SECONDS", "480"))
        # Explicit assignment is intentional: stale outer V4 testing values
        # must not silently change Ring 6's experimental variable.
        os.environ["VIRELAI_MAX_LIVES"] = str(max_lives)
        os.environ["VIRELAI_MAX_ACTIONS"] = str(max_actions)
        os.environ["VIRELAI_QUIET"] = "1"

        captain = None
        frames = []
        snapshots: list[dict[str, Any]] = []
        stop_reason = "UNKNOWN"
        fault = ""
        fault_detail = ""
        started = time.monotonic()
        last_payload: dict[str, Any] | None = None
        self._ring6_probe_active = True
        self._ring6_marker(
            "PROBE_START", lives=max_lives, action_cap=max_actions,
            seconds_cap=max_seconds,
        )

        def snapshot(reason: str, transition: dict[str, Any] | None = None) -> None:
            if captain is None:
                return
            try:
                card = _card_dict_from_captain(captain, live=True)
                if transition:
                    card["observed_transition"] = dict(transition)
                    card["win_seen"] = True
                level = int((transition or {}).get("from_level") or
                            (getattr(captain.ctx, "last_level_seen", 0) + 1))
                life = int(getattr(captain.ctx, "lives_used", 0) + 1)
                key = (reason, level, life, int(captain.action_counter))
                if snapshots and snapshots[-1].get("key") == key:
                    return
                snapshots.append({
                    "key": key, "reason": reason, "level": level,
                    "life": life, "card": card,
                })
                self._ring6_marker(
                    "LEVEL_SNAPSHOT", reason=reason, level=level, life=life,
                    captain_actions=int(captain.action_counter),
                )
            except Exception as exc:
                logger.warning("ring6 snapshot failed: %s", type(exc).__name__)

        try:
            from virelai_v4.virelai import Virelai
            from inference.framework.virelai_field_card_v6 import render_probe_report
            from inference.framework.virelai_probe_contract import (
                ProbeLimits, captain_action_data, level_boundary,
                probe_stop_reason,
            )

            captain = Virelai(game_id=game_id)
            limits = ProbeLimits(max_lives, max_actions, max_seconds)
            frames = [self._frame_data()]
            while True:
                latest = frames[-1]
                state = latest.state
                ctx = captain.ctx

                # A newly returned level frame has not yet been consumed by
                # V4.  Snapshot the old level now, before V4's lawful level
                # reset clears its level-scoped record.
                boundary = level_boundary(latest.levels_completed, ctx.last_level_seen)
                if boundary == "ADVANCE":
                    transition = {
                        "from_level": int(ctx.last_level_seen) + 1,
                        "to_level": int(latest.levels_completed) + 1,
                        "action": (last_payload or {}).get("action_display", "an action"),
                    }
                    snapshot("LEVEL_ADVANCE", transition)
                    self._ring6_marker("LEVEL_TRANSITION", **transition)
                elif boundary == "DESCENT":
                    # Death on a later level can return the run to an earlier
                    # level.  This is a boundary observation, never a win.
                    snapshot("LEVEL_DESCENT")
                    self._ring6_marker(
                        "LEVEL_DESCENT",
                        from_level=int(ctx.last_level_seen) + 1,
                        to_level=int(latest.levels_completed) + 1,
                    )

                classified_stop = probe_stop_reason(
                    state_name=getattr(state, "name", str(state)),
                    environment_terminal=bool(getattr(ctx, "env_terminated", False)),
                    lives_used=int(ctx.lives_used),
                    actions_used=int(captain.action_counter),
                    elapsed_seconds=time.monotonic() - started,
                    limits=limits,
                    harness_stop=self.should_stop(),
                )
                if classified_stop is not None:
                    if classified_stop not in ("TWO_LIVES_USED", "LIFE_CAP"):
                        snapshot(classified_stop)
                    stop_reason = classified_stop
                    break

                # Capture the completed life's live scratch before
                # choose_action processes GAME_OVER and resets it.
                if state is arcengine.GameState.GAME_OVER:
                    snapshot("LIFE_END")

                act = captain.choose_action(frames, latest)
                if act is None:
                    raise RuntimeError("Captain returned no action")
                action_data = captain_action_data(act)
                last_payload = self._execute_action(
                    arcengine.ActionInput(id=act, data=action_data),
                    batch_index=1, batch_size=1, generated_tokens=0,
                )
                captain.action_counter += 1
                self._ring6_marker(
                    "PROBE_ACTION", captain_action=int(captain.action_counter),
                    action=last_payload.get("action_display"),
                    level=last_payload.get("level"),
                    game_over=bool(last_payload.get("game_over")),
                    level_completed=bool(last_payload.get("level_completed")),
                )
                frames.append(self._frame_data())

            if not snapshots:
                snapshot("HANDOFF")
        except Exception as exc:          # captain fault costs the card, never the game
            fault = type(exc).__name__
            fault_detail = str(exc).strip()[:240]
            stop_reason = "CAPTAIN_FAULT"
            logger.exception(
                "virelai opening halted: %s: %s", fault,
                fault_detail or "(no detail)",
            )
            snapshot("CAPTAIN_FAULT")
        finally:
            self._ring6_probe_active = False

        report = {
            "game_id": game_id,
            "snapshots": [{k: v for k, v in s.items() if k != "key"} for s in snapshots],
            "actions": int(getattr(captain, "action_counter", 0) or 0),
            "lives": int(getattr(getattr(captain, "ctx", None), "lives_used", 0) or 0),
            "stop_reason": stop_reason,
            "fault": fault,
            "fault_detail": fault_detail,
        }
        self._ring6_marker(
            "PROBE_END", stop_reason=stop_reason, actions=report["actions"],
            lives=report["lives"], snapshots=len(snapshots), fault=fault,
            fault_detail=fault_detail,
        )
        rendered = False
        try:
            from inference.framework.virelai_field_card_v6 import render_probe_report
            self._virelai_card = render_probe_report(report, game_id=game_id)
            rendered = True
        except Exception as exc:
            logger.warning("virelai report render failed: %s", type(exc).__name__)
            # Honest fallback: transport must still deliver something true.
            # The game is tagged fallback=True and is excluded from
            # substantive-card Duck-use grading.
            self._virelai_card = (
                "=== CAPTAIN PROBE REPORT — %s ===\n" % game_id
                + "REPORT UNAVAILABLE: the automated probe ran but its report "
                + "could not be rendered (%s).\n" % type(exc).__name__
                + "Probe summary: %d actions taken, %d lives used, %d snapshots, "
                  "stop reason %s.\n"
                % (report["actions"], report["lives"], len(snapshots), stop_reason)
                + "Treat the world as unexplored beyond this summary.\n"
                + "=== END CAPTAIN PROBE REPORT ==="
            )
        self._ring63_finalize_report(
            game_id=game_id,
            snapshots=len(snapshots),
            fallback=bool(fault) or not rendered,
            captain_fault=bool(fault),
        )
        if _is_run_complete(self.game):
            self._ring6_marker("HANDOFF_NOT_REQUIRED", reason="GAME_WON")


    def play(self) -> None:
        run = self.game.game_run
        assert run is not None, "TAAF starts games before invoking the solver."
        run.solver_analysis_html = self.analysis_html_relpath
        self.transcript_path.parent.mkdir(parents=True, exist_ok=True)
        self.transcript_path.touch(exist_ok=True)
        self.token_baseline = _analyzer_reported_tokens(self.analyzer)
        self.seed_initial_history()
        self.write_runtime_state()
        self._append_initial_viewer_event()
        self.write_viewer_payload()
        try:
            # Ring 7: the golden Captain probes before the model's first
            # call, inside the same outer failure boundary as the model
            # loop.  The method is independently no-throw.
            self._virelai_opening()
            retry_analysis_step: int | None = None
            while not self.should_stop():
                if (
                    _is_engine_game_over(self.game)
                    and self.last_engine_action != "RESET"
                ):
                    self._execute_auto_reset()
                    continue

                if retry_analysis_step is None:
                    self.analysis_step += 1
                    analysis_step = self.analysis_step
                else:
                    analysis_step = retry_analysis_step

                self.write_runtime_state()
                transcript_before = self._read_transcript_bytes()
                try:
                    result = self.analyzer.analyze(
                        self.state_path,
                        self.action_count,
                        valid_actions=_engine_action_names(self.game),
                        step_env=self.step_env,
                        transcript_path=self.transcript_path,
                        analysis_step=analysis_step,
                        request_timeout_seconds=self.request_timeout_seconds(),
                        should_stop=self.should_stop,
                        # Ring 7 handshake (proven in ring 6.3): the field
                        # card reaches the model on analysis step 1 only;
                        # retries of step 1 re-send idempotently.
                        virelai_card=(
                            getattr(self, "_virelai_card", None)
                            if analysis_step == 1 else None
                        ),
                        # Ring 6.3 proof boundary observer: detached copy of
                        # the provider payload after build_chat_payload().
                        request_observer=self._ring63_request_observer,
                    )
                finally:
                    transcript_delta = self._transcript_delta_since(transcript_before)
                    if transcript_delta.strip():
                        self._append_analysis_viewer_event(
                            analysis_step, transcript_delta
                        )
                        self.write_viewer_payload()
                if result is None:
                    raise RuntimeError("Analyzer did not return a result.")
                if result.retryable_failure:
                    retry_analysis_step = analysis_step
                    if self.should_stop():
                        break
                    time.sleep(ANALYZER_RETRY_BACKOFF_SECONDS)
                    continue

                retry_analysis_step = None
                if getattr(result, "yielded_control", False):
                    retry_analysis_step = analysis_step
                    continue
                if not result.step_executed:
                    continue
        except Exception as exc:
            if run.final_score is None:
                run.solver_note = f"error: {type(exc).__name__}: {exc}"
                if run.state == "playing":
                    run.state = "crashed"
                self._finish_if_needed()
        finally:
            total_tokens = _analyzer_reported_tokens(self.analyzer)
            if run.solver_note is None:
                run.solver_note = f"tokens={total_tokens}"
            self._finish_if_needed()
            self.state_path.unlink(missing_ok=True)
            self._write_analysis_html()
            self.write_viewer_payload()

    def _finish_if_needed(self) -> None:
        run = self.game.game_run
        if run is not None and run.final_score is None:
            if self.stop_event.is_set() and run.state == "playing":
                run.state = "cancelled"
            self.game.finish_game()

    def _write_analysis_html(self) -> None:
        if self.solver.job_dir is None:
            return
        _write_transcript_html(
            self.transcript_path,
            self.solver.job_dir / self.analysis_html_relpath,
            f"{self.game.game_run.game_id if self.game.game_run else self.game_index} analysis",
        )

    def _read_transcript_bytes(self) -> bytes:
        try:
            return self.transcript_path.read_bytes()
        except OSError:
            return b""

    def _transcript_delta_since(self, previous_transcript: bytes) -> str:
        try:
            current_size = self.transcript_path.stat().st_size
            previous_size = len(previous_transcript)
            with self.transcript_path.open("rb") as file:
                if current_size >= previous_size:
                    current_prefix = file.read(previous_size)
                    if current_prefix == previous_transcript:
                        return file.read().decode("utf-8", errors="replace").strip()
                    file.seek(0)
                return file.read().decode("utf-8", errors="replace").strip()
        except OSError:
            return ""

    def _base_viewer_event(self, frame: Frame) -> dict[str, Any]:
        run = self.game.game_run
        raw_state = self.game.current_state.raw.state
        return {
            "board": [list(row) for row in frame.grid],
            "board_ascii": frame.ascii,
            "score": int(self.game.current_state.levels_completed),
            "state": raw_state.name,
            "level": frame.level,
            "run_status": run.state if run is not None else "playing",
        }

    def _append_initial_viewer_event(self) -> None:
        if self.viewer_events:
            return
        frame = self.current_frame()
        self.viewer_events.append(
            {
                **self._base_viewer_event(frame),
                "type": "initial",
                "title": "Initial State",
                "action_num": self.action_count,
                "analysis_step": None,
                "action_display": "RESET",
                "reward": 0.0,
            }
        )

    def _append_analysis_viewer_event(
        self, analysis_step: int, transcript: str
    ) -> None:
        frame = self.current_frame()
        self.viewer_events.append(
            {
                **self._base_viewer_event(frame),
                "type": "analysis",
                "title": f"Analysis Step {analysis_step}",
                "action_num": self.action_count,
                "analysis_step": analysis_step,
                "transcript": transcript,
            }
        )

    def _append_action_viewer_event(
        self, payload: dict[str, Any], frame: Frame
    ) -> None:
        self.viewer_events.append(
            {
                **self._base_viewer_event(frame),
                "type": "action",
                "title": f"Action {int(payload.get('action_num') or self.action_count)}",
                "action_num": int(payload.get("action_num") or self.action_count),
                "analysis_step": self.analysis_step,
                "action_name": payload.get("action_name"),
                "action_display": payload.get("action_display"),
                "reward": payload.get("reward"),
                "board_changed": payload.get("board_changed"),
                "done": payload.get("done"),
                "level_completed": payload.get("level_completed"),
                "game_over": payload.get("game_over"),
                "run_complete": payload.get("run_complete"),
                "batch_index": payload.get("batch_index"),
                "batch_size": payload.get("batch_size"),
            }
        )

    def write_viewer_payload(self) -> None:
        if self.solver.job_dir is None:
            return
        self.viewer_data_path.parent.mkdir(parents=True, exist_ok=True)
        run = self.game.game_run
        last_event_source = next(
            (
                event
                for event in reversed(self.viewer_events)
                if event.get("type") == "action"
            ),
            self.viewer_events[-1] if self.viewer_events else {},
        )
        last_event = dict(last_event_source)
        last_event.pop("board", None)
        last_event.pop("board_ascii", None)
        last_event.pop("transcript", None)
        payload = {
            "game_id": run.game_id if run is not None else str(self.game_index),
            "agent_name": self.solver.label,
            "status": run.state if run is not None else "playing",
            "pass_index": self.pass_index,
            "pass_label": str(self.pass_index),
            "eventCount": len(self.viewer_events),
            "lastEvent": last_event,
            "viewer_steps": [],
            "replay_url": self.analysis_html_relpath,
        }
        if run is not None:
            payload.update(
                {
                    "levels_completed": run.levels_completed,
                    "total_levels": run.number_of_levels,
                    "actions_per_level": list(run.actions_per_level),
                    "final_score": run.final_score,
                }
            )
        if self._viewer_events_flushed == 0:
            reset_raw_events_sidecar(self.viewer_data_path)
        append_raw_events_sidecar(
            self.viewer_data_path, self.viewer_events[self._viewer_events_flushed :]
        )
        self._viewer_events_flushed = len(self.viewer_events)
        tmp_path = self.viewer_data_path.with_suffix(
            f"{self.viewer_data_path.suffix}.tmp"
        )
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.viewer_data_path)

    def _normalize_actions(
        self, arguments: dict[str, Any]
    ) -> tuple[list[arcengine.ActionInput] | None, str | None]:
        has_single = bool(str(arguments.get("action", "")).strip())
        has_batch = arguments.get("actions") is not None
        if has_single and has_batch:
            return None, "Use either `action` or `actions`, not both."

        if has_batch:
            raw_actions = arguments.get("actions")
            if not isinstance(raw_actions, list):
                return None, "`actions` must be a JSON array of action objects."
            if not raw_actions:
                return None, "`actions` must contain at least one action."
        else:
            if not has_single:
                return None, "step_env requires `action` or `actions`."
            raw_actions = [
                {
                    "action": arguments.get("action"),
                    "row": arguments.get("row"),
                    "col": arguments.get("col"),
                }
            ]

        actions: list[arcengine.ActionInput] = []
        for index, raw_action in enumerate(raw_actions, start=1):
            if not isinstance(raw_action, dict):
                return None, f"Action {index} must be a JSON object."
            action_name = to_engine_action(raw_action.get("action"))
            if not action_name:
                return (
                    None,
                    f"Unknown action at index {index}: {raw_action.get('action')!r}",
                )
            action_id = arcengine.GameAction.from_name(action_name)
            data: dict[str, Any] = {}
            if action_id == arcengine.GameAction.ACTION6:
                try:
                    row = max(0, min(63, int(raw_action["row"])))
                    column = max(0, min(63, int(raw_action["col"])))
                    data = {
                        "x": column,
                        "y": row,
                    }
                except (KeyError, TypeError, ValueError):
                    return (
                        None,
                        f"MOUSE action at index {index} requires integer row and col arguments.",
                    )
            actions.append(arcengine.ActionInput(id=action_id, data=data))
        return actions, None

    def _error_payload(self, message: str) -> dict[str, Any]:
        return {
            "executed": False,
            "error": message,
            "valid_actions": to_model_actions(_engine_action_names(self.game)),
            **self.timing_payload(),
        }

    def _terminal_payload(
        self, requested_actions: list[arcengine.ActionInput]
    ) -> dict[str, Any]:
        raw_state = self.game.current_state.raw.state
        is_game_over = raw_state == arcengine.GameState.GAME_OVER
        is_win = raw_state == arcengine.GameState.WIN
        requested = [
            _format_action_display(action.id.name, dict(action.data))
            for action in requested_actions
        ]
        stop_reason = (
            "run_complete" if is_win else "game_over" if is_game_over else "stopped"
        )
        return {
            "executed": False,
            "error": "No action was executed because the current game state is terminal or stopping.",
            "action_num": self.action_count,
            "level": _level_number(self.game),
            "score": int(self.game.current_state.levels_completed),
            "state": raw_state.name,
            "valid_actions": [],
            "board_changed": False,
            "done": is_win,
            "level_completed": False,
            "game_over": is_game_over,
            "run_complete": is_win,
            "batched": len(requested_actions) > 1,
            "requested_count": len(requested_actions),
            "executed_count": 0,
            "requested_actions": requested,
            "executed_actions": [],
            "stopped_early": True,
            "stop_reason": stop_reason,
            **self.timing_payload(),
        }

    def step_env(self, arguments: dict[str, Any]) -> dict[str, Any]:
        requested_actions, error = self._normalize_actions(arguments)
        if error is not None or requested_actions is None:
            return self._error_payload(error or "Could not parse action request.")
        if self.should_stop() or _is_engine_game_over(self.game):
            return self._terminal_payload(requested_actions)

        executed_payloads: list[dict[str, Any]] = []
        total_reward = 0.0
        stop_reason: str | None = None
        batch_size = len(requested_actions)
        requested_displays = [
            _format_action_display(action.id.name, dict(action.data))
            for action in requested_actions
        ]

        for batch_index, action in enumerate(requested_actions, start=1):
            if self.should_stop():
                stop_reason = "stopped"
                break
            if action.id.value not in self.game.current_state.available_actions:
                message = f"{_format_action_display(action.id.name, dict(action.data))} is not valid right now."
                if executed_payloads:
                    stop_reason = "invalid_action"
                    break
                return self._error_payload(message)

            try:
                payload = self._execute_action(
                    action,
                    batch_index=batch_index,
                    batch_size=batch_size,
                    flush_viewer_payload=False,
                )
            except Exception as exc:
                if executed_payloads:
                    stop_reason = "action_error"
                    break
                return self._error_payload(f"{type(exc).__name__}: {exc}")
            executed_payloads.append(payload)
            total_reward += float(payload.get("reward", 0.0) or 0.0)

            if payload.get("run_complete"):
                stop_reason = "run_complete"
                break
            if payload.get("game_over"):
                stop_reason = "game_over"
                break
            if payload.get("level_completed"):
                stop_reason = "level_completed"
                break

        if not executed_payloads:
            return self._error_payload("No action was executed.")

        final_payload = dict(executed_payloads[-1])
        final_payload["reward"] = total_reward
        final_payload["last_reward"] = executed_payloads[-1].get("reward", 0.0)
        final_payload["batched"] = batch_size > 1
        final_payload["requested_count"] = batch_size
        final_payload["executed_count"] = len(executed_payloads)
        final_payload["requested_actions"] = requested_displays
        final_payload["executed_actions"] = [
            str(item.get("action_display") or item.get("action_name") or "")
            for item in executed_payloads
        ]
        final_payload["board_changed"] = any(
            bool(item.get("board_changed")) for item in executed_payloads
        )
        final_payload["stopped_early"] = len(executed_payloads) < batch_size
        if stop_reason is not None:
            final_payload["stop_reason"] = stop_reason
        self.write_viewer_payload()
        return final_payload

    def _execute_auto_reset(self) -> None:
        action = arcengine.ActionInput(id=arcengine.GameAction.RESET, data={})
        self._execute_action(action, batch_index=1, batch_size=1, generated_tokens=0)

    def _execute_action(
        self,
        action: arcengine.ActionInput,
        *,
        batch_index: int,
        batch_size: int,
        generated_tokens: int | None = None,
        flush_viewer_payload: bool = True,
    ) -> dict[str, Any]:
        previous_grid = _grid_from_state(self.game.current_state)
        previous_completed = int(self.game.current_state.levels_completed)
        if generated_tokens is None:
            current_tokens = _analyzer_reported_tokens(self.analyzer)
            generated_tokens = max(0, current_tokens - self.token_baseline)
            self.token_baseline = current_tokens

        new_state = self.game.execute_action(
            action, generated_tokens=generated_tokens, uncached_input_tokens=0
        )
        self.last_engine_action = action.id.name
        action_display = _format_action_display(action.id.name, dict(action.data))
        current_frame = Frame(
            grid=_grid_from_state(new_state),
            step=self.action_count,
            level=_level_number(self.game),
        )
        self.history_entries.append(
            HistoryEntry(action=action_display, frame=current_frame)
        )
        self.write_runtime_state()

        completed = int(new_state.levels_completed)
        reward = float(completed - previous_completed) / max(
            1.0, float(self.game.number_of_levels)
        )
        raw_state = new_state.raw.state
        board_changed = previous_grid != _grid_from_state(new_state)
        level_completed = bool(
            new_state.just_won_level and raw_state != arcengine.GameState.WIN
        )
        payload = {
            "executed": True,
            "action_num": self.action_count,
            "level": _level_number(self.game),
            "score": completed,
            "reward": reward,
            "state": raw_state.name,
            "valid_actions": to_model_actions(_engine_action_names(self.game)),
            "board_changed": board_changed,
            "done": raw_state == arcengine.GameState.WIN,
            "level_completed": level_completed,
            "game_over": raw_state == arcengine.GameState.GAME_OVER,
            "run_complete": raw_state == arcengine.GameState.WIN,
            "action_name": action.id.name,
            "action_data": (
                _model_mouse_action_data(action.data)
                if action.id == arcengine.GameAction.ACTION6
                else dict(action.data)
            ),
            "action_display": action_display,
            "batch_index": batch_index,
            "batch_size": batch_size,
            **self.timing_payload(),
        }
        self._append_action_viewer_event(payload, current_frame)
        if (not getattr(self, "_ring6_probe_active", False)
                and self.analysis_step > 0
                and not getattr(self, "_ring6_duck_action_marked", False)):
            self._ring6_duck_action_marked = True
            self._ring6_marker(
                "DUCK_FIRST_ACTION", action=action_display,
                action_num=self.action_count, level=payload["level"], actor="duck",
            )
        if flush_viewer_payload:
            self.write_viewer_payload()
        return payload


@dataclass
class HarnessSolver(Solver):
    """Run the existing tool-using harness as a TAAF ``Solver``."""

    label: str = "HarnessSolver"
    model: str = ""
    analyzer_timeout: float | None = 120.0
    max_actions_per_game: int | None = None
    max_runtime_s_per_game: float | None = None
    concurrency: int = 16
    save_request_logs: bool = False
    start_local_server: bool = False
    local_server_config: str = ""
    local_server_api_key_file: str = ""
    local_server_repo_dir: str = ""
    local_server_port: int | None = None
    local_server_tensor_parallel_size: int | None = None
    local_server_count: int = 1
    kaggle_enable_vllm: bool = field(default=True, repr=False)
    kaggle_wheelhouse_dataset_source: str = field(
        default=DEFAULT_VLLM_WHEELHOUSE_DATASET_SOURCE, repr=False
    )
    kaggle_model_dataset_source: str = field(
        default=DEFAULT_QWEN_MODEL_DATASET_SOURCE, repr=False
    )
    kaggle_served_model_name: str = field(default=DEFAULT_SERVED_MODEL_NAME, repr=False)
    kaggle_vllm_port: int = field(default=DEFAULT_VLLM_PORT, repr=False)
    kaggle_vllm_max_model_len: int = field(
        default=DEFAULT_VLLM_MAX_MODEL_LEN, repr=False
    )
    kaggle_vllm_tensor_parallel_size: int = field(
        default=DEFAULT_VLLM_TENSOR_PARALLEL_SIZE, repr=False
    )
    kaggle_wheelhouse_stamp_text: str = field(
        default=DEFAULT_WHEELHOUSE_STAMP_TEXT, repr=False
    )
    cancel_drain_timeout_s: float = DEFAULT_CANCEL_DRAIN_TIMEOUT_SECONDS
    analyzer_factory: AnalyzerFactory | None = field(
        default=None, repr=False, compare=False
    )
    _stop_event: threading.Event = field(
        default_factory=threading.Event, init=False, repr=False
    )
    _local_server_started: bool = field(
        default=False, init=False, repr=False, compare=False
    )
    _local_server_env_overrides: dict[str, str] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )
    _local_server_cwd: str = field(default="", init=False, repr=False, compare=False)
    _local_server_api_key: str = field(
        default="", init=False, repr=False, compare=False
    )
    _local_server_base_url: str = field(
        default="", init=False, repr=False, compare=False
    )
    _local_servers: list[_LocalServerRuntime] = field(
        default_factory=list, init=False, repr=False, compare=False
    )
    _local_server_original_env: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    # Custom pool sized to self.concurrency: asyncio.to_thread routes onto
    # Python's default executor, capped at min(32, cpu+4) — which would
    # silently cap real concurrency below self.concurrency.
    _worker_pool: ThreadPoolExecutor | None = field(default=None, init=False, repr=False, compare=False)

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state["analyzer_factory"] = None
        state.pop("_stop_event", None)
        state.pop("_local_server_started", None)
        state.pop("_local_server_env_overrides", None)
        state.pop("_local_server_cwd", None)
        state.pop("_local_server_api_key", None)
        state.pop("_local_server_base_url", None)
        state.pop("_local_servers", None)
        state.pop("_local_server_original_env", None)
        state.pop("_worker_pool", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._stop_event = threading.Event()
        self._local_server_started = False
        self._local_server_env_overrides = {}
        self._local_server_cwd = ""
        self._local_server_api_key = ""
        self._local_server_base_url = ""
        self._local_servers = []
        self._local_server_original_env = {}
        self._worker_pool = None

    def __deepcopy__(self, memo: dict[int, Any]) -> "HarnessSolver":
        cls = type(self)
        new = cls.__new__(cls)
        memo[id(self)] = new
        for key, value in self.__dict__.items():
            if key == "_stop_event":
                object.__setattr__(new, key, threading.Event())
            elif key == "analyzer_factory":
                object.__setattr__(new, key, value)
            elif key == "_local_servers":
                object.__setattr__(new, key, [])
            elif key == "_local_server_original_env":
                object.__setattr__(new, key, {})
            elif key == "_worker_pool":
                object.__setattr__(new, key, None)
            else:
                object.__setattr__(new, key, copy.deepcopy(value, memo))
        return new

    @property
    def kaggle_dataset_sources(self) -> list[str]:
        if not self.kaggle_enable_vllm:
            return []
        return duck_kaggle_dataset_sources(self._kaggle_vllm_config())

    @property
    def kaggle_setup_commands(self) -> list[str]:
        if not self.kaggle_enable_vllm:
            return []
        return [duck_kaggle_setup_command(self._kaggle_vllm_config())]

    @property
    def kaggle_teardown_commands(self) -> list[str]:
        if not self.kaggle_enable_vllm:
            return []
        return [duck_kaggle_teardown_command()]

    def _kaggle_vllm_config(self) -> DuckKaggleVllmConfig:
        return DuckKaggleVllmConfig(
            wheelhouse_dataset_source=self.kaggle_wheelhouse_dataset_source,
            model_dataset_source=self.kaggle_model_dataset_source,
            served_model_name=self.kaggle_served_model_name,
            vllm_port=self.kaggle_vllm_port,
            max_model_len=self.kaggle_vllm_max_model_len,
            tensor_parallel_size=self.kaggle_vllm_tensor_parallel_size,
            wheelhouse_stamp_text=self.kaggle_wheelhouse_stamp_text,
        )

    def _setup(self) -> None:
        if self.start_local_server:
            self._start_local_servers()
        self._worker_pool = ThreadPoolExecutor(
            max_workers=max(1, int(self.concurrency)),
            thread_name_prefix="harness-game",
        )

    def _teardown(self) -> None:
        if self._local_server_started:
            self._stop_local_servers()
        if self._worker_pool is not None:
            self._worker_pool.shutdown(wait=False)
            self._worker_pool = None

    async def _run_games(self, games: list[taaf.game.Game]) -> None:
        self._stop_event.clear()
        semaphore = asyncio.Semaphore(max(1, int(self.concurrency)))
        pass_indices_by_game_id: dict[str, int] = {}
        loop = asyncio.get_running_loop()
        pool = self._worker_pool

        async def run_one(index: int, pass_index: int, game: taaf.game.Game) -> None:
            async with semaphore:
                args = (game, index, pass_index, self._local_server_for_game_index(index))
                if pool is not None:
                    await loop.run_in_executor(pool, functools.partial(self._play_one, *args))
                else:
                    # _setup wasn't called (direct test invocation).
                    await asyncio.to_thread(self._play_one, *args)

        tasks: list[asyncio.Task[None]] = []
        for index, game in enumerate(games):
            game_id = game.game_run.game_id if game.game_run is not None else str(index)
            pass_index = pass_indices_by_game_id.get(game_id, 0)
            pass_indices_by_game_id[game_id] = pass_index + 1
            tasks.append(asyncio.create_task(run_one(index, pass_index, game)))
        try:
            await asyncio.gather(
                *(asyncio.shield(task) for task in tasks), return_exceptions=True
            )
        except asyncio.CancelledError:
            self._stop_event.set()
            await self._drain_game_tasks(tasks)
            self._finish_remaining(games)
            raise

    async def _drain_game_tasks(self, tasks: list[asyncio.Task[None]]) -> None:
        if not tasks:
            return
        timeout = max(0.0, float(self.cancel_drain_timeout_s))
        if timeout == 0.0:
            return
        done, _pending = await asyncio.wait(tasks, timeout=timeout)
        if done:
            await asyncio.gather(*done, return_exceptions=True)

    def _start_local_servers(self) -> None:
        server_count = self._resolved_local_server_count()
        started: list[_LocalServerRuntime] = []
        self._capture_local_server_process_env()
        try:
            for server_index in range(server_count):
                runtime = self._local_server_settings(
                    server_index=server_index, server_count=server_count
                )
                print(
                    "Starting local inference server inside solver setup "
                    f"(server {server_index + 1}/{server_count})"
                )
                subprocess.run(
                    ["make", "server"],
                    cwd=runtime.repo_dir,
                    env=self._local_server_env(runtime.env_overrides),
                    check=True,
                )
                if runtime.api_key_file.is_file():
                    runtime.api_key = runtime.api_key_file.read_text(
                        encoding="utf-8"
                    ).strip()
                started.append(runtime)
        except Exception:
            self._local_servers = started
            self._local_server_started = bool(started)
            with contextlib.suppress(Exception):
                self._stop_local_servers()
            raise

        self._local_servers = started
        self._local_server_started = bool(started)
        if started:
            first = started[0]
            self._local_server_cwd = str(first.repo_dir)
            self._local_server_env_overrides = first.env_overrides
            self._local_server_api_key = first.api_key
            self._local_server_base_url = first.base_url
            if first.api_key:
                os.environ["LOCAL_ANALYZER_API_KEY"] = first.api_key
                os.environ["OPENAI_API_KEY"] = first.api_key
            if first.base_url:
                os.environ["LOCAL_ANALYZER_BASE_URL"] = first.base_url
                os.environ["OPENAI_BASE_URL"] = first.base_url
                os.environ["LOCAL_ANALYZER_PROVIDER"] = "vllm"
                os.environ["OPENAI_PROVIDER"] = "vllm"

    def _stop_local_servers(self) -> None:
        runtimes = list(reversed(self._local_servers))
        if not runtimes and self._local_server_env_overrides:
            repo_dir = (
                Path(self._local_server_cwd)
                if self._local_server_cwd
                else self._local_server_repo_dir()
            )
            runtimes = [
                _LocalServerRuntime(
                    index=0,
                    repo_dir=repo_dir,
                    api_key_file=Path(
                        self._local_server_env_overrides.get("SERVER_API_KEY_FILE", "")
                    ),
                    env_overrides=self._local_server_env_overrides,
                    base_url=self._local_server_base_url,
                    api_key=self._local_server_api_key,
                )
            ]
        try:
            for runtime in runtimes:
                subprocess.run(
                    ["make", "stop-server"],
                    cwd=runtime.repo_dir,
                    env=self._local_server_env(runtime.env_overrides),
                    check=False,
                )
        finally:
            self._local_servers = []
            self._local_server_started = False
            self._restore_local_server_process_env()

    def _capture_local_server_process_env(self) -> None:
        self._local_server_original_env = {
            key: os.environ.get(key) for key in _LOCAL_SERVER_PROCESS_ENV_KEYS
        }

    def _restore_local_server_process_env(self) -> None:
        if not self._local_server_original_env:
            return
        for key, value in self._local_server_original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._local_server_original_env = {}

    def _local_server_settings(
        self, *, server_index: int, server_count: int
    ) -> _LocalServerRuntime:
        config_path = self.local_server_config.strip()
        if not config_path:
            raise ValueError(
                "local_server_config is required when start_local_server is enabled."
            )

        repo_dir = self._local_server_repo_dir()
        run_dir = (self.job_dir or Path.cwd()).resolve()
        api_key_file = self._local_server_api_key_path(
            server_index=server_index,
            server_count=server_count,
            run_dir=run_dir,
        )
        pid_path = run_dir / (
            "server.pid" if server_count <= 1 else f"server-{server_index}.pid"
        )
        log_path = run_dir / (
            "server.log" if server_count <= 1 else f"server-{server_index}.log"
        )
        port = self._local_server_port(server_index=server_index)
        base_url = f"http://127.0.0.1:{port}/v1" if port is not None else ""
        env_overrides = {
            "CONFIG_PATH": config_path,
            "SERVER_API_KEY_FILE": str(api_key_file),
            "SERVER_PID": str(pid_path),
            "SERVER_LOG": str(log_path),
            "SERVER_TAIL_ON_WAIT": "true",
            "UV_PROJECT_ENVIRONMENT": str(repo_dir / ".venv"),
        }
        venv_python = self._local_server_venv_python(repo_dir)
        if venv_python is not None:
            env_overrides["SERVER_VENV_PYTHON"] = str(venv_python)
            env_overrides["PYTHON"] = str(venv_python)
        if port is not None:
            env_overrides.update(
                {
                    "SERVER_PORT": str(port),
                    "LOCAL_ANALYZER_BASE_URL": base_url,
                    "OPENAI_BASE_URL": base_url,
                    "LOCAL_ANALYZER_PROVIDER": "vllm",
                    "OPENAI_PROVIDER": "vllm",
                }
            )
        if self.local_server_tensor_parallel_size is not None:
            env_overrides["SERVER_TENSOR_PARALLEL_SIZE"] = str(
                int(self.local_server_tensor_parallel_size)
            )
        if server_count > 1:
            env_overrides["CUDA_VISIBLE_DEVICES"] = (
                self._cuda_visible_device_for_server(server_index)
            )
        return _LocalServerRuntime(
            index=server_index,
            repo_dir=repo_dir,
            api_key_file=api_key_file,
            env_overrides=env_overrides,
            base_url=base_url,
        )

    def _resolved_local_server_count(self) -> int:
        if not self.start_local_server:
            return 0
        return max(1, int(self.local_server_count or 1))

    def _local_server_port(self, *, server_index: int) -> int | None:
        if self.local_server_port is None:
            return None
        return int(self.local_server_port) + int(server_index)

    def _local_server_api_key_path(
        self, *, server_index: int, server_count: int, run_dir: Path
    ) -> Path:
        default_name = (
            "server-api-key" if server_count <= 1 else f"server-{server_index}-api-key"
        )
        base_path = self._resolve_local_server_path(
            self.local_server_api_key_file, default=run_dir / default_name
        )
        if server_count <= 1 or not str(self.local_server_api_key_file or "").strip():
            return base_path
        suffix = base_path.suffix
        stem = base_path.name[: -len(suffix)] if suffix else base_path.name
        return base_path.with_name(f"{stem}-{server_index}{suffix}")

    def _cuda_visible_device_for_server(self, server_index: int) -> str:
        visible_devices = [
            device.strip()
            for device in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
            if device.strip()
        ]
        if server_index < len(visible_devices):
            return visible_devices[server_index]
        return str(server_index)

    def _local_server_repo_dir(self) -> Path:
        repo_dir = (
            Path(self.local_server_repo_dir).expanduser()
            if self.local_server_repo_dir
            else Path(__file__).parents[2]
        )
        repo_dir = repo_dir.resolve()
        if not repo_dir.is_dir():
            raise ValueError(f"local_server_repo_dir does not exist: {repo_dir}")
        return repo_dir

    def _local_server_venv_python(self, repo_dir: Path) -> Path | None:
        repo_venv_python = repo_dir / ".venv" / "bin" / "python"
        if repo_venv_python.is_file():
            return repo_venv_python
        return None

    def _resolve_local_server_path(self, raw_value: str, *, default: Path) -> Path:
        raw = str(raw_value or "").strip()
        if not raw:
            return default.resolve()
        path = Path(raw).expanduser()
        if path.is_absolute():
            return path
        return (self._local_server_repo_dir() / path).resolve()

    def _local_server_env(
        self, overrides: dict[str, str] | None = None
    ) -> dict[str, str]:
        env = os.environ.copy()
        env.update(overrides or self._local_server_env_overrides)
        return env

    def soft_time_remaining_seconds(self) -> float | None:
        if self.soft_end_time is None:
            return None
        now = (
            datetime.now(self.soft_end_time.tzinfo)
            if self.soft_end_time.tzinfo
            else datetime.now()
        )
        return max(0.0, (self.soft_end_time - now).total_seconds())

    def _local_server_for_game_index(
        self, game_index: int
    ) -> _LocalServerRuntime | None:
        if not self._local_servers:
            return None
        return self._local_servers[int(game_index) % len(self._local_servers)]

    def _make_analyzer(
        self,
        game: taaf.game.Game,
        index: int,
        local_server: _LocalServerRuntime | None = None,
    ) -> Any:
        if self.analyzer_factory is not None:
            return self.analyzer_factory(game, index)
        return ToolAgent(
            model=self.model,
            timeout=self.analyzer_timeout,
            save_request_logs=self.save_request_logs,
            api_key=(
                local_server.api_key
                if local_server is not None
                else self._local_server_api_key
            )
            or None,
            base_url=(
                local_server.base_url
                if local_server is not None
                else self._local_server_base_url
            )
            or None,
            provider="vllm" if local_server is not None else None,
        )

    def _play_one(
        self,
        game: taaf.game.Game,
        index: int,
        pass_index: int,
        local_server: _LocalServerRuntime | None = None,
    ) -> None:
        try:
            assert game.game_run is not None
            run = game.game_run
            run_stem = self._run_stem(run.game_id, pass_index)
            state_path = self._artifacts_dir() / f"{run_stem}_{RUNTIME_STATE_FILENAME}"
            viewer_data_path = self._artifacts_dir() / f"{run_stem}_viewer_data.json"
            transcript_path = self._transcripts_dir() / f"{run_stem}.txt"
            analysis_relpath = f"solver_analysis/{run_stem}.html"
            analyzer = self._make_analyzer(game, index, local_server)
            session = _HarnessGameSession(
                solver=self,
                game=game,
                analyzer=analyzer,
                game_index=index,
                pass_index=pass_index,
                state_path=state_path,
                transcript_path=transcript_path,
                analysis_html_relpath=analysis_relpath,
                stop_event=self._stop_event,
                viewer_data_path=viewer_data_path,
            )
            session.play()
        except Exception as exc:
            self._finish_after_error(game, exc)

    def _artifacts_dir(self) -> Path:
        root = self.job_dir or Path.cwd() / "taaf_harness_artifacts"
        path = root / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _transcripts_dir(self) -> Path:
        root = self.job_dir or Path.cwd() / "taaf_harness_artifacts"
        path = root / "transcripts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _run_stem(self, game_id: str, index: int) -> str:
        return f"{artifact_stem(game_id)}_p{index}"

    def _finish_remaining(self, games: list[taaf.game.Game]) -> None:
        for game in games:
            run = game.game_run
            if run is not None and run.final_score is None:
                try:
                    if self._stop_event.is_set() and run.state == "playing":
                        run.state = "cancelled"
                    game.finish_game()
                except Exception:
                    pass

    def _finish_after_error(self, game: taaf.game.Game, exc: Exception) -> None:
        run = game.game_run
        if run is None or run.final_score is not None:
            return
        run.solver_note = f"error: {type(exc).__name__}: {exc}"
        if run.state == "playing":
            run.state = "crashed"
        with contextlib.suppress(Exception):
            game.finish_game()
        if run.final_score is None:
            with contextlib.suppress(Exception):
                run.final_score = run._compute_final_score()
