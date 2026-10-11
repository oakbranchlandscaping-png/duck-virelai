"""Passive whole-game Virelai evidence runtime for Ring 8."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from inference.framework.virelai_clock import compile_clock_patterns
from inference.framework.virelai_continuity import ContinuityCompiler
from inference.framework.virelai_win_capsule import (
    FrameLayerRef,
    WinCapsule,
    build_win_capsule,
    frame_layer_ref,
)
from inference.framework.virelai_lessons import (
    LevelLesson,
    bind_lesson_to_current,
    compile_level_lesson,
    enrich_lesson,
)
from inference.framework.virelai_memory_card import build_memory_card
from inference.framework.virelai_physics_manual import physics_manual, render_physics_manual
from inference.framework.virelai_world_model import (
    canonical_bytes,
    from_semantic_library,
    query_world_model,
    transition_briefing,
    with_clock_patterns,
    with_level_lessons,
)

QUERY_SCHEMA = "virelai-query-v2"
EVENT_SCHEMA = "virelai-evidence-v3"
FRAME_SCHEMA = "virelai-frames-v1"
MAX_QUERY_ITEMS = 50
MAX_CHANGED_CELLS = 64
MAX_RECENT_CELL_DELTAS = 32
MAX_EFFECT_RANKING_ITEMS = 3
MAX_EFFECT_ENTRIES = 12
CAPTURE_P95_BUDGET_MS = 25.0
CAPTURE_BREACH_MS = 50.0
RAW_QUERY_P95_BUDGET_MS = 25.0
RAW_QUERY_BREACH_MS = 50.0


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "game"))


def _append_jsonl(path: Path | None, payload: dict[str, Any]) -> bool:
    if path is None:
        return True
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
            handle.write("\n")
        return True
    except OSError:
        return False


def _state_str(state: Any) -> str:
    if state is None:
        return ""
    return str(getattr(state, "value", None) or getattr(state, "name", None) or state)


def _nearest_rank(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, (percentile * len(ordered) + 99) // 100 - 1))
    return ordered[index]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def verify_frame_archive(artifact_dir: Path) -> dict[str, Any]:
    """Verify offsets, geometry, lengths, hashes, and full binary coverage."""
    root = Path(artifact_dir)
    index_path = root / "frames.jsonl"
    binary_path = root / "frames.bin"
    failures: list[str] = []
    if not index_path.is_file():
        failures.append("missing frames.jsonl")
    if not binary_path.is_file():
        failures.append("missing frames.bin")
    if failures:
        return {"passed": False, "failures": failures, "frames": 0, "archive_bytes": 0}
    try:
        records = _read_jsonl(index_path)
        binary = binary_path.read_bytes()
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "passed": False,
            "failures": [f"archive read failed: {type(exc).__name__}: {exc}"],
            "frames": 0,
            "archive_bytes": 0,
        }
    expected_offset = 0
    for expected_node, record in enumerate(records):
        if record.get("schema") != FRAME_SCHEMA:
            failures.append(f"unexpected frame schema at node {expected_node}")
            break
        if record.get("node_index") != expected_node:
            failures.append(f"node index discontinuity at node {expected_node}")
            break
        if record.get("archive_offset") != expected_offset:
            failures.append(f"archive offset discontinuity at node {expected_node}")
            break
        layers = record.get("layers") or []
        layer_bytes = 0
        for layer_index, layer in enumerate(layers):
            rows = int(layer.get("rows", -1))
            cols = int(layer.get("cols", -1))
            byte_offset = int(layer.get("byte_offset", -1))
            byte_length = int(layer.get("byte_length", -1))
            if rows < 0 or cols < 0 or byte_length != rows * cols:
                failures.append(
                    f"invalid layer geometry at node {expected_node}, layer {layer_index}"
                )
                break
            if byte_offset != layer_bytes:
                failures.append(
                    f"layer offset discontinuity at node {expected_node}, layer {layer_index}"
                )
                break
            layer_bytes += byte_length
        if failures:
            break
        archive_length = int(record.get("archive_length", -1))
        if archive_length != layer_bytes:
            failures.append(f"frame length mismatch at node {expected_node}")
            break
        payload = binary[expected_offset : expected_offset + archive_length]
        if len(payload) != archive_length:
            failures.append(f"short frame payload at node {expected_node}")
            break
        digest = hashlib.sha256()
        for layer in layers:
            digest.update(f"{layer['rows']}x{layer['cols']}:".encode("ascii"))
        digest.update(payload)
        if digest.hexdigest() != record.get("layered_hash"):
            failures.append(f"frame hash mismatch at node {expected_node}")
            break
        expected_offset += archive_length
    if expected_offset != len(binary):
        failures.append(
            f"archive size mismatch: indexed {expected_offset}, binary {len(binary)}"
        )
    return {
        "passed": not failures,
        "failures": failures,
        "frames": len(records),
        "archive_bytes": len(binary),
    }


@dataclass(frozen=True)
class LayerDescriptor:
    rows: int
    cols: int
    byte_offset: int
    byte_length: int


@dataclass(frozen=True)
class CompactFrameRecord:
    """One immutable frame stored as uint8 bytes plus portable metadata."""

    node_index: int
    game_id: str
    guid: str | None
    state: str
    available_actions: tuple[int, ...]
    full_reset: bool
    levels_completed: int
    win_levels: int
    layers: tuple[LayerDescriptor, ...]
    payload: bytes
    frames_len: int
    layered_hash: str
    action_id: int | None
    acted_cell: tuple[int, int] | None

    @staticmethod
    def from_frame(
        frame: Any,
        *,
        node_index: int,
        frames_len: int,
        action_id: int | None,
        acted_cell: tuple[int, int] | None,
    ) -> "CompactFrameRecord":
        payload = bytearray()
        descriptors: list[LayerDescriptor] = []
        for raw_layer in getattr(frame, "frame", ()) or ():
            rows = list(raw_layer)
            row_count = len(rows)
            col_count = len(rows[0]) if rows else 0
            if any(len(row) != col_count for row in rows):
                raise ValueError("ARC frame layers must be rectangular")
            offset = len(payload)
            for row in rows:
                for raw_cell in row:
                    cell = int(raw_cell)
                    if not 0 <= cell <= 255:
                        raise ValueError(f"frame cell outside uint8 range: {cell}")
                    payload.append(cell)
            descriptors.append(
                LayerDescriptor(row_count, col_count, offset, row_count * col_count)
            )
        frozen = bytes(payload)
        digest = hashlib.sha256()
        for descriptor in descriptors:
            digest.update(f"{descriptor.rows}x{descriptor.cols}:".encode("ascii"))
        digest.update(frozen)
        return CompactFrameRecord(
            node_index=node_index,
            game_id=str(getattr(frame, "game_id", "") or ""),
            guid=getattr(frame, "guid", None),
            state=_state_str(getattr(frame, "state", None)),
            available_actions=tuple(
                int(action) for action in (getattr(frame, "available_actions", ()) or ())
            ),
            full_reset=bool(getattr(frame, "full_reset", False)),
            levels_completed=int(getattr(frame, "levels_completed", 0) or 0),
            win_levels=int(getattr(frame, "win_levels", 0) or 0),
            layers=tuple(descriptors),
            payload=frozen,
            frames_len=int(frames_len),
            layered_hash=digest.hexdigest(),
            action_id=action_id,
            acted_cell=acted_cell,
        )

    def layer_bytes(self, index: int) -> bytes:
        descriptor = self.layers[index]
        start = descriptor.byte_offset
        return self.payload[start : start + descriptor.byte_length]

    def reconstruct_frame(self) -> list[list[list[int]]]:
        result: list[list[list[int]]] = []
        for index, descriptor in enumerate(self.layers):
            data = self.layer_bytes(index)
            result.append(
                [
                    list(data[row * descriptor.cols : (row + 1) * descriptor.cols])
                    for row in range(descriptor.rows)
                ]
            )
        return result

    def archive_index(self, archive_offset: int) -> dict[str, Any]:
        return {
            "schema": FRAME_SCHEMA,
            "node_index": self.node_index,
            "game_id": self.game_id,
            "guid": self.guid,
            "state": self.state,
            "available_actions": self.available_actions,
            "full_reset": self.full_reset,
            "levels_completed": self.levels_completed,
            "win_levels": self.win_levels,
            "frames_len": self.frames_len,
            "layered_hash": self.layered_hash,
            "action_id": self.action_id,
            "acted_cell": self.acted_cell,
            "archive_offset": archive_offset,
            "archive_length": len(self.payload),
            "layers": [asdict(layer) for layer in self.layers],
        }


class CompactFrameJournal:
    """Whole-game append-only journal with O(1) indexed access."""

    def __init__(self) -> None:
        self._records: list[CompactFrameRecord] = []

    def append(
        self,
        frame: Any,
        *,
        action_id: int | None,
        frames_len: int,
        acted_cell: tuple[int, int] | None,
    ) -> CompactFrameRecord:
        record = CompactFrameRecord.from_frame(
            frame,
            node_index=len(self._records),
            frames_len=frames_len,
            action_id=action_id,
            acted_cell=acted_cell,
        )
        self._records.append(record)
        return record

    def record_at(self, node_index: int) -> CompactFrameRecord:
        record = self._records[node_index]
        if record.node_index != node_index:
            raise RuntimeError("journal index invariant violated")
        return record

    @property
    def latest(self) -> CompactFrameRecord:
        return self._records[-1]

    def iter_records(self) -> Iterable[CompactFrameRecord]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)


def _visible_state_key(record: CompactFrameRecord) -> str:
    """Hash the observed final layer plus level progress, never hidden state."""
    digest = hashlib.sha256()
    digest.update(str(record.levels_completed).encode("ascii"))
    if record.layers:
        descriptor = record.layers[-1]
        digest.update(f"{descriptor.rows}x{descriptor.cols}:".encode("ascii"))
        digest.update(record.layer_bytes(-1))
    return digest.hexdigest()[:16]


def _visible_shape(record: CompactFrameRecord) -> tuple[int, int] | None:
    if not record.layers:
        return None
    layer = record.layers[-1]
    return (layer.rows, layer.cols)


@dataclass(frozen=True)
class CellDelta:
    """One literal rewrite in the final visible layer."""

    row: int
    col: int
    before_class: int
    after_class: int


def _cell_deltas(
    before: CompactFrameRecord,
    after: CompactFrameRecord,
) -> tuple[CellDelta, ...]:
    if not before.layers or not after.layers:
        return ()
    left_shape = before.layers[-1]
    right_shape = after.layers[-1]
    left = before.layer_bytes(-1)
    right = after.layer_bytes(-1)
    if (left_shape.rows, left_shape.cols) != (right_shape.rows, right_shape.cols):
        return ()
    return tuple(
        CellDelta(
            row=index // left_shape.cols,
            col=index % left_shape.cols,
            before_class=left_cell,
            after_class=right_cell,
        )
        for index, (left_cell, right_cell) in enumerate(zip(left, right))
        if left_cell != right_cell
    )


@dataclass(frozen=True)
class TransitionRecord:
    transition_id: int
    from_node: int
    to_node: int
    game_id: str
    level_before: int
    level_after: int
    actor: str
    action_id: int
    action_name: str
    acted_cell: tuple[int, int] | None
    before_visible_state: str
    after_visible_state: str
    before_hash: str
    after_hash: str
    geometry_changed: bool
    before_shape: tuple[int, int] | None
    after_shape: tuple[int, int] | None
    visible_self_loop: bool
    target_seen_before: bool
    target_first_seen: bool
    cell_delta_count: int
    cell_deltas: tuple[CellDelta, ...]
    level_completed: bool
    game_over: bool
    run_complete: bool

    def canonical(self) -> dict[str, Any]:
        """Complete persisted view. Canonical evidence is never truncated."""
        return asdict(self)

    def query_view(self, *, include_cell_deltas: bool = False) -> dict[str, Any]:
        """Bounded model-facing view of the canonical record."""
        payload = asdict(self)
        deltas = list(payload.pop("cell_deltas"))
        payload["cell_deltas"] = (
            deltas[:MAX_CHANGED_CELLS] if include_cell_deltas else []
        )
        payload["cell_deltas_included"] = include_cell_deltas
        payload["cell_deltas_truncated"] = (
            include_cell_deltas and len(deltas) > MAX_CHANGED_CELLS
        )
        return payload

    def recent_view(self) -> dict[str, Any]:
        """Small literal view for the first live memory capability."""
        deltas = [
            [item.row, item.col, item.before_class, item.after_class]
            for item in self.cell_deltas
        ]
        return {
            "transition_id": self.transition_id,
            "actor": self.actor,
            "action_id": self.action_id,
            "action_name": self.action_name,
            "acted_cell": self.acted_cell,
            "level_before": self.level_before,
            "level_after": self.level_after,
            "before_shape": self.before_shape,
            "after_shape": self.after_shape,
            "geometry_changed": self.geometry_changed,
            "visible_grid_changed": self.geometry_changed or bool(deltas),
            "visible_self_loop": self.visible_self_loop,
            "cell_delta_count": len(deltas),
            "cell_delta_fields": ["row", "col", "before_class", "after_class"],
            "cell_deltas": deltas[:MAX_RECENT_CELL_DELTAS],
            "cell_deltas_returned": min(len(deltas), MAX_RECENT_CELL_DELTAS),
            "cell_deltas_truncated": len(deltas) > MAX_RECENT_CELL_DELTAS,
            "level_completed": self.level_completed,
            "game_over": self.game_over,
            "run_complete": self.run_complete,
        }


class VirelaiRuntime:
    """Per-game passive evidence store and bounded raw query endpoint."""

    def __init__(
        self,
        *,
        game_id: str,
        run_stem: str | None = None,
        artifact_root: Path | None = None,
    ) -> None:
        self.game_id = str(game_id)
        self.run_stem = _safe_stem(run_stem or self.game_id)
        self.journal = CompactFrameJournal()
        self.capture = self.journal  # temporary compatibility name
        self.transitions: list[TransitionRecord] = []
        self._state_visits: dict[str, int] = {}
        self._state_actions: dict[str, dict[str, set[str]]] = {}
        self._state_action_attempts: dict[str, dict[str, int]] = {}
        self._effect_ledger: dict[tuple[int, str], dict[str, Any]] = {}
        self._current_visible_state_key: str | None = None
        self._lock = threading.RLock()
        self._query_sequence = 0
        self._capture_timings_ms: list[float] = []
        self._query_timings_ms: list[float] = []
        self._failures: list[dict[str, Any]] = []
        self._artifact_dir = (
            Path(artifact_root) / self.run_stem if artifact_root is not None else None
        )
        self._events_path = self._artifact_dir / "events.jsonl" if self._artifact_dir else None
        self._queries_path = self._artifact_dir / "queries.jsonl" if self._artifact_dir else None
        self._frames_path = self._artifact_dir / "frames.bin" if self._artifact_dir else None
        self._frame_index_path = self._artifact_dir / "frames.jsonl" if self._artifact_dir else None
        self._archive_offset = 0
        self.continuity = ContinuityCompiler(
            game_id=self.game_id,
            artifact_dir=self._artifact_dir,
        )
        self._continuity_summary: dict[str, Any] | None = None
        self._semantic_compiler: Any | None = None
        self._semantic_summary: dict[str, Any] | None = None
        if os.environ.get("VIRELAI_SEMANTIC_SHADOW", "0").strip() == "1":
            from inference.framework.virelai_semantic import SemanticLibraryCompiler

            self._semantic_compiler = SemanticLibraryCompiler(artifact_dir=self._artifact_dir)
        self.win_capsules: list[WinCapsule] = []
        self._level_root_refs: dict[int, FrameLayerRef] = {}
        self._attempt_root_refs: dict[int, FrameLayerRef] = {}
        self._win_capsules_path = (
            self._artifact_dir / "win_capsules.jsonl" if self._artifact_dir else None
        )
        self.level_lessons: list[LevelLesson] = []
        self._lesson_enrichments: dict[int, dict[str, Any]] = {}
        self._lesson_enrichment_futures: dict[int, Future[dict[str, Any]]] = {}
        self._lesson_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="virelai-lesson")
        self._level_lessons_path = (
            self._artifact_dir / "level_lessons.jsonl" if self._artifact_dir else None
        )
        self._experiment_intent = None
        self._experiment_count = 0
        self._experiment_results = []
        self._experiments_path = self._artifact_dir / "experiments.jsonl" if self._artifact_dir else None
        self._world_model_cache_step = -1
        self._world_model_cache: Any | None = None
        # WO-L2a: world_model.json belongs to the v2 canonical writer alone. This observer model is an
        # in-memory query cache; it is persisted only on explicit opt-in, and never at the canonical path.
        self._world_model_path = (
            self._artifact_dir / "world_model_legacy_v1.json"
            if self._artifact_dir and os.environ.get("VIRELAI_LEGACY_WORLD_MODEL_FILE", "0").strip() == "1"
            else None
        )
        self._controller_outcomes: list[dict[str, Any]] = []
        self._controller_revisions: list[dict[str, Any]] = []
        self._controller_outcomes_path = (
            self._artifact_dir / "outcome_comparisons.jsonl" if self._artifact_dir else None
        )
        self._controller_revisions_path = (
            self._artifact_dir / "revision_events.jsonl" if self._artifact_dir else None
        )

    @property
    def through_step(self) -> int:
        return len(self.transitions)

    def _persist_frame(self, record: CompactFrameRecord) -> bool:
        if self._frames_path is None or self._frame_index_path is None:
            return True
        try:
            self._artifact_dir.mkdir(parents=True, exist_ok=True)
            with self._frames_path.open("ab") as handle:
                offset = handle.tell()
                handle.write(record.payload)
                self._archive_offset = handle.tell()
            if not _append_jsonl(self._frame_index_path, record.archive_index(offset)):
                raise OSError("failed to append frame index")
            return True
        except OSError as exc:
            self.record_failure(
                "FRAME_ARCHIVE_WRITE_FAILED",
                f"{type(exc).__name__}: {exc}",
                through_step=max(0, record.node_index - 1),
            )
            return False

    def _record_capture_timing(self, started: float, node_index: int) -> None:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self._capture_timings_ms.append(elapsed_ms)
        if elapsed_ms > CAPTURE_BREACH_MS:
            _append_jsonl(
                self._events_path,
                {
                    "schema": EVENT_SCHEMA,
                    "event": "CAPTURE_BUDGET_BREACH",
                    "game_id": self.game_id,
                    "node_index": node_index,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "breach_ms": CAPTURE_BREACH_MS,
                },
            )

    def record_failure(self, event: str, detail: str, *, through_step: int | None = None) -> None:
        payload = {
            "schema": EVENT_SCHEMA,
            "event": str(event),
            "game_id": self.game_id,
            "through_step": self.through_step if through_step is None else through_step,
            "detail": str(detail),
        }
        self._failures.append(payload)
        _append_jsonl(self._events_path, payload)

    def observe_initial(self, frame: Any) -> None:
        started = time.perf_counter()
        with self._lock:
            if len(self.journal):
                return
            record = self.journal.append(frame, action_id=None, frames_len=1, acted_cell=None)
            self._persist_frame(record)
            self.continuity.submit(
                record,
                level=max(1, record.levels_completed + 1),
            )
            initial_level = max(1, record.levels_completed + 1)
            initial_ref = frame_layer_ref(record)
            if initial_ref is not None:
                self._level_root_refs[initial_level] = initial_ref
                self._attempt_root_refs[initial_level] = initial_ref
            state_key = _visible_state_key(record)
            self._current_visible_state_key = state_key
            self._state_visits[state_key] = 1
            if not _append_jsonl(
                self._events_path,
                {
                    "schema": EVENT_SCHEMA,
                    "event": "INITIAL_FRAME",
                    "game_id": self.game_id,
                    "node_index": record.node_index,
                    "visible_state_key": state_key,
                    "state_key_kind": "visible_observation_hash",
                    "levels_completed": record.levels_completed,
                    "state": record.state,
                    "layered_hash": record.layered_hash,
                },
            ):
                self._failures.append({"event": "JOURNAL_EVENT_WRITE_FAILED", "through_step": 0})
            self._record_capture_timing(started, record.node_index)

    def observe_transition(
        self,
        *,
        frame: Any,
        action_id: int,
        action_name: str,
        acted_cell: tuple[int, int] | None,
        actor: str,
        result: dict[str, Any],
    ) -> None:
        started = time.perf_counter()
        with self._lock:
            if not len(self.journal):
                raise RuntimeError("observe_initial must precede transitions")
            before = self.journal.latest
            after = self.journal.append(
                frame,
                action_id=int(action_id),
                frames_len=len(self.journal) + 1,
                acted_cell=acted_cell,
            )
            self._persist_frame(after)
            before_shape = _visible_shape(before)
            after_shape = _visible_shape(after)
            geometry_changed = before_shape != after_shape
            deltas = _cell_deltas(before, after)
            before_key = _visible_state_key(before)
            after_key = _visible_state_key(after)
            target_seen_before = after_key in self._state_visits
            transition = TransitionRecord(
                transition_id=len(self.transitions) + 1,
                from_node=before.node_index,
                to_node=after.node_index,
                game_id=self.game_id,
                level_before=max(1, before.levels_completed + 1),
                level_after=max(1, int(result.get("level") or (after.levels_completed + 1))),
                actor=str(actor or "UNKNOWN").upper(),
                action_id=int(action_id),
                action_name=str(action_name),
                acted_cell=acted_cell,
                before_visible_state=before_key,
                after_visible_state=after_key,
                before_hash=before.layered_hash,
                after_hash=after.layered_hash,
                geometry_changed=geometry_changed,
                before_shape=before_shape,
                after_shape=after_shape,
                visible_self_loop=before_key == after_key,
                target_seen_before=target_seen_before,
                target_first_seen=not target_seen_before,
                cell_delta_count=len(deltas),
                cell_deltas=deltas,
                level_completed=bool(result.get("level_completed")),
                game_over=bool(result.get("game_over")),
                run_complete=bool(result.get("run_complete")),
            )
            self.transitions.append(transition)
            capsule = build_win_capsule(
                game_id=self.game_id,
                before=before,
                after=after,
                transition=transition,
                level_root_ref=self._level_root_refs.get(transition.level_before),
                attempt_root_ref=self._attempt_root_refs.get(transition.level_before),
            )
            if capsule is not None:
                self.win_capsules.append(capsule)
                if not _append_jsonl(self._win_capsules_path, capsule.canonical()):
                    self._failures.append(
                        {"event": "WIN_CAPSULE_WRITE_FAILED", "through_step": transition.transition_id}
                    )
                lesson = compile_level_lesson(
                    capsule=capsule,
                    journal=self.journal,
                    transitions=self.transitions,
                )
                self.level_lessons.append(lesson)
                self._lesson_enrichment_futures[lesson.completed_level] = (
                    self._lesson_executor.submit(
                        enrich_lesson, lesson, self.journal, tuple(self.transitions))
                )
                if not _append_jsonl(self._level_lessons_path, lesson.canonical()):
                    self._failures.append(
                        {"event": "LEVEL_LESSON_WRITE_FAILED", "through_step": transition.transition_id}
                    )
                if capsule.successor_spawn_ref is not None:
                    self._level_root_refs[transition.level_after] = capsule.successor_spawn_ref
                    self._attempt_root_refs[transition.level_after] = capsule.successor_spawn_ref
            elif (
                transition.game_over
                or after.full_reset
                or transition.action_name.upper() == "RESET"
                or transition.actor == "SYSTEM_RESET"
            ):
                reset_ref = frame_layer_ref(after)
                if reset_ref is not None:
                    self._attempt_root_refs[transition.level_after] = reset_ref
            self.continuity.submit(
                after,
                level=transition.level_after,
                life_ended=transition.game_over,
            )
            if transition.actor == "DUCK":
                ledger_key = (transition.level_before, transition.action_name)
                effect = self._effect_ledger.setdefault(
                    ledger_key,
                    {
                        "presses": 0,
                        "changed": 0,
                        "unchanged": 0,
                        "cell_counts": [],
                        "pre_states": set(),
                        "state_outcomes": {},
                        "steps": [],
                    },
                )
                changed = transition.geometry_changed or transition.cell_delta_count > 0
                effect["presses"] += 1
                effect["changed" if changed else "unchanged"] += 1
                effect["cell_counts"].append(transition.cell_delta_count)
                effect["pre_states"].add(transition.before_visible_state)
                effect["state_outcomes"].setdefault(
                    transition.before_visible_state, set()
                ).add("changed" if changed else "unchanged")
                effect["steps"].append(transition.transition_id)
            self._current_visible_state_key = after_key
            self._state_visits[after_key] = self._state_visits.get(after_key, 0) + 1
            self._state_actions.setdefault(before_key, {}).setdefault(str(action_name), set()).add(after_key)
            attempts = self._state_action_attempts.setdefault(before_key, {})
            attempts[str(action_name)] = attempts.get(str(action_name), 0) + 1
            if not _append_jsonl(
                self._events_path,
                {"schema": EVENT_SCHEMA, "event": "TRANSITION", **transition.canonical()},
            ):
                self._failures.append(
                    {"event": "JOURNAL_EVENT_WRITE_FAILED", "through_step": transition.transition_id}
                )
            if self._experiment_intent is not None:
                from inference.framework.virelai_experiments import evaluate
                feedback = evaluate(self._experiment_intent, transition)
                self._experiment_results.append(feedback)
                self._experiment_results = self._experiment_results[-50:]
                if not _append_jsonl(self._experiments_path, {"event": "OUTCOME", **feedback}):
                    self._failures.append({"event": "EXPERIMENT_WRITE_FAILED", "through_step": transition.transition_id})
                self._experiment_intent = None
            self._record_capture_timing(started, after.node_index)

    def _transition_by_selector(self, selector: Any) -> TransitionRecord | None:
        if not self.transitions:
            return None
        if selector in (None, "last", "latest"):
            return self.transitions[-1]
        try:
            value = int(selector)
        except (TypeError, ValueError):
            return None
        index = len(self.transitions) + value if value < 0 else value - 1
        return self.transitions[index] if 0 <= index < len(self.transitions) else None

    @staticmethod
    def _timing_summary(values: list[float], budget_ms: float, breach_ms: float) -> dict[str, Any]:
        breaches = sum(value > breach_ms for value in values)
        return {
            "samples": len(values),
            "total_ms": round(sum(values), 3),
            "p50_ms": round(_nearest_rank(values, 50), 3),
            "p95_ms": round(_nearest_rank(values, 95), 3),
            "max_ms": round(max(values, default=0.0), 3),
            "budget_ms": budget_ms,
            "breach_ms": breach_ms,
            "breaches": breaches,
            "breach_ratio": round(breaches / len(values), 6) if values else 0.0,
        }

    def _overview(self) -> dict[str, Any]:
        current = self.journal.latest if len(self.journal) else None
        return {
            "mode": "PASSIVE_RAW_EVIDENCE",
            "game_id": self.game_id,
            "run_stem": self.run_stem,
            "frames": len(self.journal),
            "transitions": len(self.transitions),
            "visited_visible_states": len(self._state_visits),
            "current_visible_state": self._current_visible_state_key,
            "current_level": max(1, current.levels_completed + 1) if current else None,
            "deaths": sum(item.game_over for item in self.transitions),
            "level_wins": sum(item.level_completed for item in self.transitions),
            "game_wins": sum(item.run_complete for item in self.transitions),
            "win_capsules": len(self.win_capsules),
            "level_lessons": len(self.level_lessons),
            "actors": sorted({item.actor for item in self.transitions}),
            "evidence_failures": len(self._failures),
            "capture_performance": self._timing_summary(
                self._capture_timings_ms, CAPTURE_P95_BUDGET_MS, CAPTURE_BREACH_MS
            ),
            "naming_rule": "No object, region, weave, or semantic identifiers are exposed.",
            "visible_state_limit": (
                "Visible-state keys hash the final observed layer plus level progress. "
                "They do not identify hidden or semantic world state."
            ),
            "semantic_status": "Semantic compilation is not exposed in Ring 8.0B.",
            "continuity_shadow": (
                self._continuity_summary or self.continuity.snapshot()
            ),
        }

    def _state(self, selector: Any) -> dict[str, Any] | None:
        key = (
            self._current_visible_state_key
            if selector in (None, "current", "here")
            else str(selector)
        )
        if key not in self._state_visits:
            return None
        actions = self._state_actions.get(key, {})
        attempts = self._state_action_attempts.get(key, {})
        return {
            "visible_state_key": key,
            "key_kind": "visible_observation_hash",
            "visits": self._state_visits[key],
            "actions": {
                action: {
                    "attempts": attempts.get(action, 0),
                    "outcomes": sorted(outcomes),
                    "distinct_outcomes": len(outcomes),
                }
                for action, outcomes in sorted(actions.items())
            },
            "current": key == self._current_visible_state_key,
            "hidden_state_detected": False,
        }

    def _states(self, offset: int, limit: int) -> tuple[list[dict[str, Any]], bool]:
        keys = list(self._state_visits)
        selected = keys[offset : offset + limit]
        return (
            [state for key in selected if (state := self._state(key)) is not None],
            offset + limit < len(keys),
        )

    def _help(self) -> dict[str, Any]:
        return {
            "purpose": "Observation queries and separate experiment-intent records; no environment actions.",
            "operations": {
                "agenda": "Current evidence-grounded questions and last experiment feedback.",
                "question": "One agenda question; id required.",
                "intent": "Record a proposal for the next action, not a fact. Requires OPEN question_id and the same named action dictionary used by action(), for example action={'action':'UP'} or action={'action':'MOUSE','row':r,'col':c}. The action must be currently offered. Optional prediction CHANGED/UNCHANGED/UNKNOWN and scope_cell.",
                "experiments": "Latest five observed experiment outcomes; no semantic closure implied.",
                "overview": "Literal record counts, boundaries, failures, and timing.",
                "recent": "Recent raw transitions; optional limit=1..50.",
                "effects": "Observed current-level outcomes grouped by Duck action.",
                "clock": "Repeated action-independent visible process on this level.",
                "transition": "One raw transition; step='last' or a 1-based integer.",
                "state": "Current or named visible-observation hash and tried actions.",
                "states": "Bounded visible-observation map; optional offset and limit=1..50.",
                "wins": "Exact observed level/game-winning transitions.",
                "lessons": "Small index of completed-level lessons.",
                "lesson": "Short index of focused knowledge available for one completed level.",
                "mechanics": "Compact observed controls and effects for a completed level.",
                "win": "Compact observed winning edge and contrast with earlier failures.",
                "carry": "Compact untested control correspondences at the next-level spawn.",
                "evidence": "One exact raw transition referenced by a lesson; transition_id required.",
                "gaps": "Capture failures and incomplete action coverage only.",
                "world": "Canonical persistent world-model overview.",
                "diff": "Canonical structural changes between observed levels.",
                "object": "Canonical object record; optional id.",
                "mechanic": "Canonical witnessed action/effect rule; optional id.",
                "model_evidence": "Canonical claim and its evidence; optional id.",
                "physics": "Compact current or named-level physics grammar. Optional level and limit; fresh=True forces compilation through the latest transition. Responses state compiled and pending steps. Expand a listed handle with mechanic.",
                "card": "Compact new-level memory index with focused expansion handles.",
                "briefing": "Compatibility alias for the compact new-level memory card.",
            },
            "naming_rule": "Raw responses contain no object, region, or weave identifiers.",
        }

    def _gaps(self) -> dict[str, Any]:
        return {
            "evidence_failures": list(self._failures[-MAX_QUERY_ITEMS:]),
            "states_with_no_tried_actions": sum(
                not self._state_actions.get(key) for key in self._state_visits
            ),
            "note": (
                "Raw evidence cannot enumerate unseen states or semantic unknowns. "
                "Action coverage is reported only from observed attempts."
            ),
        }

    @staticmethod
    def _median(values: list[int]) -> int | float:
        ordered = sorted(values)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[middle]
        total = ordered[middle - 1] + ordered[middle]
        return total // 2 if total % 2 == 0 else total / 2

    def _effect_entry(
        self, *, level: int, action: str, effect: dict[str, Any]
    ) -> dict[str, Any]:
        counts = list(effect["cell_counts"])
        steps = list(effect["steps"])
        witnesses = steps[:2]
        if steps and steps[-1] not in witnesses:
            witnesses.append(steps[-1])
        max_count = max(counts, default=0)
        if counts:
            max_step = steps[counts.index(max_count)]
            if max_step not in witnesses:
                witnesses.append(max_step)
        return {
            "action": action,
            "level": level,
            "presses": effect["presses"],
            "changed": effect["changed"],
            "unchanged": effect["unchanged"],
            "distinct_pre_states": len(effect["pre_states"]),
            "cells_changed": {
                "min": min(counts, default=0),
                "median": self._median(counts) if counts else 0,
                "max": max_count,
            },
            "mixed_outcomes": bool(effect["changed"] and effect["unchanged"]),
            "same_visible_state_divergences": sum(
                len(outcomes) > 1 for outcomes in effect["state_outcomes"].values()
            ),
            "first_step": steps[0] if steps else None,
            "last_step": steps[-1] if steps else None,
            "witness_steps": sorted(witnesses),
            "kind": "observation",
        }

    def _effects(self) -> dict[str, Any]:
        current_level = (
            max(1, self.journal.latest.levels_completed + 1)
            if len(self.journal)
            else 1
        )
        entries = [
            self._effect_entry(level=level, action=action, effect=effect)
            for (level, action), effect in self._effect_ledger.items()
            if level == current_level
        ]
        by_action = {entry["action"]: entry for entry in entries}

        def top(key: Any, *, eligible: Any = lambda item: True) -> list[str]:
            return [
                entry["action"]
                for entry in sorted(
                    (item for item in entries if eligible(item)),
                    key=key,
                    reverse=True,
                )[
                    :MAX_EFFECT_RANKING_ITEMS
                ]
            ]

        rankings = {
            "largest_effects": top(
                lambda item: (
                    item["cells_changed"]["max"],
                    item["cells_changed"]["median"],
                    item["presses"],
                ),
                eligible=lambda item: item["cells_changed"]["max"] > 0,
            ),
            "most_unchanged": top(
                lambda item: (item["unchanged"], item["presses"]),
                eligible=lambda item: item["unchanged"] > 0,
            ),
            "most_attempted": top(lambda item: item["presses"]),
            "mixed_outcomes": [
                item["action"]
                for item in sorted(
                    (entry for entry in entries if entry["mixed_outcomes"]),
                    key=lambda item: item["presses"],
                    reverse=True,
                )[:MAX_EFFECT_RANKING_ITEMS]
            ],
        }
        selected_actions: list[str] = []
        for names in rankings.values():
            for action in names:
                if action not in selected_actions:
                    selected_actions.append(action)
        selected_actions = selected_actions[:MAX_EFFECT_ENTRIES]
        return {
            "level": current_level,
            "scope": "current_level",
            "total_action_keys": len(entries),
            "entries_returned": len(selected_actions),
            "entries_truncated": len(selected_actions) < len(entries),
            "rankings": rankings,
            "entries": [by_action[action] for action in selected_actions],
            "note": (
                "Counts of observed visible outcomes, not verdicts. An action that "
                "was unchanged in recorded states may change in another state."
            ),
        }

    def _clock(self) -> dict[str, Any]:
        current_level = (
            max(1, self.journal.latest.levels_completed + 1)
            if len(self.journal)
            else 1
        )
        patterns = compile_clock_patterns(
            self.transitions,
            self.journal.latest if len(self.journal) else None,
            level=current_level,
        )
        return {
            "level": current_level,
            "scope": "current_level",
            "candidates": patterns,
            "candidate_count": len(patterns),
            "note": (
                "Candidates are repeated action-independent visible processes, "
                "not proven timers, objectives, causes, or hidden-state measurements."
            ),
        }

    def _lesson_bundle(self, requested_level: int) -> tuple[LevelLesson | None, dict[str, Any] | None]:
        lesson = next((item for item in reversed(self.level_lessons)
                       if item.completed_level == requested_level), None)
        if lesson is None:
            return None, None
        if requested_level not in self._lesson_enrichments:
            future = self._lesson_enrichment_futures.get(requested_level)
            self._lesson_enrichments[requested_level] = (
                future.result() if future is not None
                else enrich_lesson(lesson, self.journal, tuple(self.transitions))
            )
        return lesson, self._lesson_enrichments[requested_level]

    def _observer_world_model(self) -> Any:
        """The observer's v1 model for queries, compiled once per journal boundary (in memory; WO-L2a)."""
        if self._world_model_cache_step == self.through_step and self._world_model_cache is not None:
            return self._world_model_cache
        from inference.framework.virelai_semantic.compiler import compile_semantic_library

        library = compile_semantic_library(self.journal)
        model = from_semantic_library(library)
        current_level = max(1, self.journal.latest.levels_completed + 1)
        model = with_clock_patterns(
            model,
            compile_clock_patterns(
                self.transitions, self.journal.latest, level=current_level
            ),
        )
        model = with_level_lessons(
            model, (lesson.canonical() for lesson in self.level_lessons)
        )
        self._world_model_cache = model
        self._world_model_cache_step = self.through_step
        if self._world_model_path is not None:
            try:
                self._world_model_path.parent.mkdir(parents=True, exist_ok=True)
                self._world_model_path.write_bytes(canonical_bytes(model))
            except OSError as exc:
                self.record_failure("WORLD_MODEL_WRITE_FAILED", f"{type(exc).__name__}: {exc}")
        return model

    @staticmethod
    def _focused_mechanics(level: int, enrichment: dict[str, Any]) -> dict[str, Any]:
        grammar = enrichment.get("physics_grammar") or {}
        controls = []
        for item in grammar.get("self_reactive_controls", []):
            rule = item.get("observed_rule") or {}
            controls.append({"name": item.get("name"), "kind": "SELF_REACTIVE",
                             "location": item.get("location"),
                             "integer_classes": item.get("current_integer_classes", []),
                             "mechanism": rule.get("mechanism"), "period": rule.get("period"),
                             "observations": rule.get("observations", 0)})
        for item in grammar.get("remote_levers", []):
            effects = list(item.get("effects", []))
            effect_types = sorted({
                str(effect.get("type") or "UNKNOWN") for effect in effects
            })
            directions = sorted({
                str(effect.get("direction") or "UNKNOWN") for effect in effects
            })
            controls.append({"name": item.get("name"), "kind": "REMOTE_LEVER",
                             "location": item.get("location"),
                             "integer_classes": item.get("current_integer_classes", []),
                             "mechanism": (
                                 "remote effects: types=" + ",".join(effect_types)
                                 + "; directions=" + ",".join(directions)
                             ),
                             "affected_regions": [effect.get("region") for effect in effects],
                             "periods": sorted({
                                 int(effect["period"]) for effect in effects
                                 if effect.get("period") is not None
                             }),
                             "presentation_ready": bool(
                                 item.get("location") is not None and effects
                             ),
                             "observations": sum(effect.get("observations", 0)
                                                 for effect in effects)})
        shared = [{"kind": item.get("kind"),
                   "controls": [item.get("lever_a"), item.get("lever_b")],
                   "relationship": "opposing controls reverse common visible effects",
                   "affected_regions": [effect.get("region") for effect in item.get("effects", [])],
                   "effects": list(item.get("effects", []))[:4]}
                  for item in grammar.get("shared_control_relations", [])]
        return {"completed_level": level, "world_mode": grammar.get("world_mode"),
                "controls": controls[:12], "controls_truncated": len(controls) > 12,
                "controls_total": len(controls),
                "shared_mechanics": shared[:6],
                "shared_mechanics_truncated": len(shared) > 6,
                "shared_mechanics_total": len(shared),
                "independent_process_observed": grammar.get("independent_process_observed", False),
                "status": "OBSERVED_MECHANICS", "basis": enrichment.get("semantic_basis")}

    @staticmethod
    def _focused_win(lesson: LevelLesson, enrichment: dict[str, Any]) -> dict[str, Any]:
        explanation = enrichment.get("observed_win_explanation") or {}
        conditions = [{"region": item.get("bbox"),
                       "winning_pre_state": item.get("winning_pre_state"),
                       "distinct_failed_pre_states": len(item.get("failed_pre_states", []))}
                      for item in explanation.get("distinguishing_conditions", [])]
        return {"completed_level": lesson.completed_level,
                "winning_action": lesson.boundary.get("winning_action"),
                "acted_cell": lesson.boundary.get("acted_cell"),
                "status": explanation.get("status", "UNMEASURED"),
                "earlier_same_action_failures": explanation.get("earlier_same_action_failures", 0),
                "distinguishing_conditions": conditions,
                "causal_limit": explanation.get("causal_limit"),
                "evidence_transition_ids": [item["transition_id"]
                                            for item in lesson.evidence_refs[-4:]]}

    @staticmethod
    def _focused_carry(level: int, enrichment: dict[str, Any]) -> dict[str, Any]:
        return {"completed_level": level, "new_level": level + 1,
                "candidate_controls": enrichment.get("new_level_type_correspondences", []),
                "carry_rule": enrichment.get("carry_rule"),
                "status": "UNTESTED_CROSS_LEVEL_HYPOTHESES"}

    def query(self, operation: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        params = dict(parameters or {})
        op = str(operation or "").strip().lower()
        with self._lock:
            self._query_sequence += 1
            error: str | None = None
            data: Any = None
            truncated = False
            if op == "help":
                data = self._help()
            elif op == "overview":
                data = self._overview()
            elif op == "recent":
                item = self.transitions[-1] if self.transitions else None
                if item is None:
                    error = "no completed transition observed"
                else:
                    data = item.recent_view()
                    truncated = bool(data["cell_deltas_truncated"])
            elif op == "effects":
                data = self._effects()
                truncated = bool(data["entries_truncated"])
            elif op == "clock":
                data = self._clock()
            elif op == "transition":
                item = self._transition_by_selector(params.get("step", "last"))
                if item is None:
                    error = "transition not found"
                else:
                    data = item.query_view(include_cell_deltas=True)
                    truncated = bool(data.get("cell_deltas_truncated"))
            elif op == "state":
                data = self._state(params.get("key", "current"))
                if data is None:
                    error = "state not found"
            elif op == "states":
                try:
                    offset = max(0, int(params.get("offset", 0)))
                    limit = max(1, min(MAX_QUERY_ITEMS, int(params.get("limit", 25))))
                except (TypeError, ValueError):
                    offset, limit = 0, 25
                data, truncated = self._states(offset, limit)
            elif op == "wins":
                wins = [
                    item for item in self.transitions if item.level_completed or item.run_complete
                ]
                selected = wins[-MAX_QUERY_ITEMS:]
                data = [item.query_view(include_cell_deltas=True) for item in selected]
                truncated = len(wins) > len(selected) or any(
                    item.get("cell_deltas_truncated") for item in data
                )
            elif op == "lessons":
                data = [
                    {
                        "completed_level": lesson.completed_level,
                        "compiled_at_transition": lesson.compiled_at_transition,
                        "winning_action": lesson.boundary["winning_action"],
                        "hypothesis_count": len(lesson.hypotheses),
                        "status": "AVAILABLE",
                    }
                    for lesson in self.level_lessons[-MAX_QUERY_ITEMS:]
                ]
                truncated = len(self.level_lessons) > MAX_QUERY_ITEMS
            elif op == "intent":
                from dataclasses import asdict
                from inference.framework.virelai_agenda import compile_agenda
                from inference.framework.virelai_experiments import make_intent
                agenda = compile_agenda(self._observer_world_model())
                try:
                    intent = make_intent(params, agenda, self._experiment_count + 1)
                except (ValueError, TypeError) as exc:
                    error = str(exc)
                    data = {"accepted": False, "reason": error}
                else:
                    replaced = self._experiment_intent.id if self._experiment_intent else None
                    self._experiment_count += 1
                    self._experiment_intent = intent
                    data = {"accepted": True, "intent": asdict(intent), "replaced_intent": replaced,
                            "scope": "next executed transition only; submit after navigation"}
                    if not _append_jsonl(self._experiments_path, {"event": "INTENT", **data}):
                        self._failures.append({"event": "EXPERIMENT_WRITE_FAILED", "through_step": self.through_step})
            elif op == "experiments":
                data = self._experiment_results[-5:]
            elif op in {"agenda", "question"}:
                from inference.framework.virelai_agenda import compile_agenda, render_agenda
                # Automatic context amortizes full semantic compilation. Explicit queries
                # and intents always compile the current prefix. Never conceal freshness.
                cached = self._world_model_cache
                fresh_boundary = any(t.level_completed or t.game_over or t.action_id == 0
                                     for t in self.transitions[max(0, self._world_model_cache_step):])
                reuse = (op == "agenda" and params.get("automatic") is True and cached is not None
                         and self.through_step >= 8
                         and self.through_step - self._world_model_cache_step < 8
                         and not fresh_boundary)
                agenda = compile_agenda(cached if reuse else self._observer_world_model())
                agenda["journal_through_step"] = self.through_step
                agenda["pending_transitions"] = self.through_step - agenda["observed_through_step"]
                if op == "question":
                    data = next((q for q in agenda["questions"] if q["id"] == params.get("id")), None)
                    if data is None:
                        error = "question not found"
                else:
                    limit = max(1, min(50, int(params.get("limit", 12))))
                    data = {**agenda, "text": render_agenda(agenda), "total_questions": len(agenda["questions"])}
                    data["experiment_feedback"] = self._experiment_results[-2:]
                    if agenda["pending_transitions"]:
                        data["text"] += f"\nJournal through step {self.through_step}; {agenda['pending_transitions']} newer transitions await model refresh. Inspect current observations; virelai('agenda') refreshes now."
                    if self._experiment_results:
                        latest = self._experiment_results[-1]
                        data["text"] += f"\nLast experiment {latest['intent_id']} at transition {latest['transition_id']}: {latest['outcome']}; {latest.get('observed_summary', latest.get('observed', latest.get('reason', '')))} This does not close a semantic question. Inspect virelai('experiments')."
                    data["questions"] = agenda["questions"][:limit]
                    truncated = len(agenda["questions"]) > limit
            elif op == "controller":
                from dataclasses import asdict
                from inference.framework.virelai_controller import build_controller_snapshot
                model = self._observer_world_model()
                data = asdict(build_controller_snapshot(model))
            elif op == "controller_outcome":
                from dataclasses import asdict
                from inference.framework.virelai_controller import (
                    build_controller_snapshot,
                    compare_outcome,
                    decision_envelope_from_dict,
                    revise_rule,
                )
                if not self.transitions:
                    error = "no executed transition is available for comparison"
                elif not isinstance(params.get("decision"), dict):
                    error = "controller outcome requires the prospective decision"
                else:
                    decision_payload = dict(params["decision"])
                    if params.get("decision_id"):
                        decision_payload["decision_id"] = params["decision_id"]
                    try:
                        envelope = decision_envelope_from_dict(
                            decision_payload,
                            actions=params.get("actions") or (),
                            declared_at_transition=max(0, self.through_step - 1),
                        )
                        transition = self.transitions[-1]
                        comparison = compare_outcome(envelope, transition)
                        snapshot = build_controller_snapshot(self._observer_world_model())
                        claim_id = envelope.prediction.claim_id if envelope.prediction else None
                        parent = next(
                            (rule for rule in snapshot.rule_versions if rule.rule_version_id == claim_id),
                            None,
                        )
                        resulting, revision = revise_rule(parent, envelope, comparison)
                    except (TypeError, ValueError) as exc:
                        error = str(exc)
                    else:
                        comparison_row = asdict(comparison)
                        revision_row = asdict(revision)
                        self._controller_outcomes.append(comparison_row)
                        self._controller_revisions.append(revision_row)
                        if not _append_jsonl(
                            self._controller_outcomes_path,
                            {"schema": "virelai-outcome-comparison-v1", **comparison_row},
                        ):
                            self._failures.append({"event": "CONTROLLER_OUTCOME_WRITE_FAILED", "through_step": self.through_step})
                        if not _append_jsonl(
                            self._controller_revisions_path,
                            {
                                "schema": "virelai-revision-event-v1",
                                **revision_row,
                                "resulting_rule": asdict(resulting) if resulting else None,
                            },
                        ):
                            self._failures.append({"event": "CONTROLLER_REVISION_WRITE_FAILED", "through_step": self.through_step})
                        data = {
                            "comparison": comparison_row,
                            "revision": revision_row,
                            "resulting_rule": asdict(resulting) if resulting else None,
                        }
            elif op == "controller_history":
                limit = max(1, min(MAX_QUERY_ITEMS, int(params.get("limit") or 5)))
                data = {
                    "outcomes": self._controller_outcomes[-limit:],
                    "revisions": self._controller_revisions[-limit:],
                    "outcomes_total": len(self._controller_outcomes),
                    "revisions_total": len(self._controller_revisions),
                }
                truncated = len(self._controller_outcomes) > limit or len(self._controller_revisions) > limit
            elif op in {"world", "diff", "object", "mechanic", "model_evidence"}:
                force_fresh = params.get("fresh") is True
                model = (
                    self._world_model_cache
                    if self._world_model_cache is not None and not force_fresh
                    else self._observer_world_model()
                )
                compiled_step = self._world_model_cache_step
                canonical_op = "evidence" if op == "model_evidence" else op
                result = query_world_model(
                    model,
                    canonical_op,
                    identifier=params.get("id"),
                    limit=int(params.get("limit") or 12),
                )
                data = result.get("data")
                error = result.get("error")
                truncated = bool(result.get("truncated"))
                if isinstance(data, dict):
                    data = {
                        **data,
                        "compiled_through_step": compiled_step,
                        "journal_through_step": self.through_step,
                        "pending_transitions": max(0, self.through_step - compiled_step),
                    }
            elif op == "physics":
                try:
                    requested_level = (
                        int(params["level"]) if params.get("level") is not None else None
                    )
                    limit = max(1, min(MAX_QUERY_ITEMS, int(params.get("limit") or 8)))
                except (TypeError, ValueError):
                    requested_level, limit = None, 8
                force_fresh = params.get("fresh") is True
                cached = self._world_model_cache
                cached_step = self._world_model_cache_step
                pending = max(0, self.through_step - cached_step)
                boundary_pending = any(
                    transition.level_completed
                    or transition.game_over
                    or transition.run_complete
                    or transition.action_id == 0
                    for transition in self.transitions[max(0, cached_step):]
                )
                reuse = (
                    cached is not None
                    and not force_fresh
                    and pending < 8
                    and not boundary_pending
                )
                model = cached if reuse else self._observer_world_model()
                if requested_level is None:
                    requested_level = model.current_level
                compiled_step = self._world_model_cache_step
                manual = physics_manual(model, level=requested_level)
                total = len(manual["mechanics"])
                truncated = total > limit
                data = {
                    **manual,
                    "mechanics": manual["mechanics"][:limit],
                    "mechanics_total": total,
                    "mechanics_returned": min(total, limit),
                    "compiled_through_step": compiled_step,
                    "journal_through_step": self.through_step,
                    "pending_transitions": max(0, self.through_step - compiled_step),
                }
                data["text"] = render_physics_manual(data)
            elif op in {"card", "briefing"}:
                model = self._observer_world_model()
                entered_level = int(params.get("level") or model.current_level)
                completed_level = entered_level - 1 if entered_level > 1 else None
                lesson, enrichment = self._lesson_bundle(completed_level or -1)
                mechanics_view = (
                    self._focused_mechanics(completed_level, enrichment or {})
                    if lesson and completed_level is not None else None
                )
                data = build_memory_card(
                    entered_level=entered_level,
                    completed_level=completed_level if lesson else None,
                    world_mode=(mechanics_view or {}).get("world_mode") or model.world_mode,
                    win=self._focused_win(lesson, enrichment or {}) if lesson else None,
                    mechanics=mechanics_view,
                    carry=(
                        self._focused_carry(completed_level, enrichment or {})
                        if lesson and completed_level is not None else None
                    ),
                )
            elif op in {"lesson", "mechanics", "win", "carry"}:
                try:
                    requested_level = int(params.get("level", self.level_lessons[-1].completed_level))
                except (TypeError, ValueError, IndexError):
                    requested_level = -1
                lesson, enrichment = self._lesson_bundle(requested_level)
                if lesson is None:
                    error = "level lesson not found; lessons exist only after an observed win"
                elif op == "mechanics":
                    data = self._focused_mechanics(requested_level, enrichment or {})
                elif op == "win":
                    data = self._focused_win(lesson, enrichment or {})
                elif op == "carry":
                    data = self._focused_carry(requested_level, enrichment or {})
                elif str(params.get("detail", "index")).lower() == "full":
                    data = lesson.model_view(bind_lesson_to_current(lesson, self.journal.latest))
                    data.update(enrichment or {})
                else:
                    data = {
                        "completed_level": requested_level,
                        "winning_action_kind": str(lesson.boundary["winning_action"]).split("(", 1)[0],
                        "win_explanation_status": (enrichment or {}).get(
                            "observed_win_explanation", {}).get("status"),
                        "available": [
                            {"query": f"virelai('mechanics', level={requested_level})",
                             "provides": "observed controls and effects"},
                            {"query": f"virelai('win', level={requested_level})",
                             "provides": "winning edge and contrast with earlier failures"},
                            {"query": f"virelai('carry', level={requested_level})",
                             "provides": "possible control counterparts in the new level"},
                        ],
                        "full_archive_query": (
                            f"virelai('lesson', level={requested_level}, detail='full')")
                    }
            elif op == "evidence":
                item = self._transition_by_selector(params.get("transition_id"))
                if item is None:
                    error = "evidence transition not found"
                else:
                    data = item.query_view(include_cell_deltas=True)
                    truncated = bool(data.get("cell_deltas_truncated"))
            elif op == "gaps":
                data = self._gaps()
            else:
                error = f"unknown operation: {op or '<empty>'}"

            compute_latency_ms = (time.perf_counter() - started) * 1000.0
            response = {
                "schema": (
                    "virelai-recent-v1"
                    if op == "recent"
                    else "virelai-effects-v1"
                    if op == "effects"
                    else "virelai-clock-v1"
                    if op == "clock"
                    else QUERY_SCHEMA
                ),
                "query_id": self._query_sequence,
                "operation": op,
                "game_id": self.game_id,
                "observed_through_step": self.through_step,
                "compiled_through_step": None,
                "freshness": "raw-current",
                "data": data,
                "error": error,
                "truncated": truncated,
                "compute_latency_ms": round(compute_latency_ms, 3),
            }
            if op == "agenda" and isinstance(data, dict):
                response["compiled_through_step"] = data.get("observed_through_step")
                response["freshness"] = "model-prefix" if data.get("pending_transitions") else "model-current"
            elif op in {"physics", "world", "diff", "object", "mechanic", "model_evidence"} and isinstance(data, dict):
                response["compiled_through_step"] = data.get("compiled_through_step")
                response["freshness"] = "model-prefix" if data.get("pending_transitions") else "model-current"
            _append_jsonl(self._queries_path, {**response, "parameters": params})
            latency_ms = (time.perf_counter() - started) * 1000.0
            self._query_timings_ms.append(latency_ms)
            response["latency_ms"] = round(latency_ms, 3)
            response["budget_breached"] = latency_ms > RAW_QUERY_BREACH_MS
            if latency_ms > RAW_QUERY_BREACH_MS:
                _append_jsonl(
                    self._events_path,
                    {
                        "schema": EVENT_SCHEMA,
                        "event": "RAW_QUERY_BUDGET_BREACH",
                        "game_id": self.game_id,
                        "query_id": self._query_sequence,
                        "operation": op,
                        "elapsed_ms": round(latency_ms, 3),
                    },
                )
            return response

    def flush(self) -> None:
        self._lesson_executor.shutdown(wait=True)
        if self._continuity_summary is None:
            try:
                self._continuity_summary = self.continuity.close()
            except Exception as exc:
                self.record_failure(
                    "CONTINUITY_CLOSE_FAILED",
                    f"{type(exc).__name__}: {exc}",
                )
        if self._semantic_compiler is not None and self._semantic_summary is None:
            try:
                self._semantic_summary = self._semantic_compiler.close(self.journal)
            except Exception as exc:
                self.record_failure(
                    "SEMANTIC_LIBRARY_CLOSE_FAILED",
                    f"{type(exc).__name__}: {exc}",
                )
        if self._artifact_dir is None:
            return
        with self._lock:
            try:
                self._artifact_dir.mkdir(parents=True, exist_ok=True)
                summary = self._overview()
                summary["raw_query_performance"] = self._timing_summary(
                    self._query_timings_ms, RAW_QUERY_P95_BUDGET_MS, RAW_QUERY_BREACH_MS
                )
                summary["archive"] = {
                    "frame_schema": FRAME_SCHEMA,
                    "frames_file": "frames.bin",
                    "index_file": "frames.jsonl",
                    "encoding": "uint8",
                    "bytes": self._archive_offset,
                }
                summary["win_capsule_archive"] = {
                    "schema": "virelai-win-capsule-v1",
                    "file": "win_capsules.jsonl",
                    "records": len(self.win_capsules),
                    "actor_independent": True,
                    "model_exposed": False,
                }
                summary["level_lesson_archive"] = {
                    "schema": "virelai-level-lesson-v1",
                    "file": "level_lessons.jsonl",
                    "records": len(self.level_lessons),
                    "actor_independent": True,
                    "model_exposed_after_win_only": True,
                }
                summary["semantic_library_shadow"] = {
                    "enabled": self._semantic_compiler is not None,
                    "summary": self._semantic_summary,
                    "file": "semantic_library.json",
                    "model_exposed": False,
                }
                target = self._artifact_dir / "summary.json"
                temporary = target.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
                temporary.replace(target)
            except OSError as exc:
                self.record_failure("JOURNAL_CHECKPOINT_FAILED", f"{type(exc).__name__}: {exc}")


__all__ = [
    "CAPTURE_BREACH_MS",
    "CAPTURE_P95_BUDGET_MS",
    "CellDelta",
    "CompactFrameJournal",
    "CompactFrameRecord",
    "EVENT_SCHEMA",
    "FRAME_SCHEMA",
    "MAX_RECENT_CELL_DELTAS",
    "QUERY_SCHEMA",
    "RAW_QUERY_BREACH_MS",
    "RAW_QUERY_P95_BUDGET_MS",
    "TransitionRecord",
    "VirelaiRuntime",
    "verify_frame_archive",
]
