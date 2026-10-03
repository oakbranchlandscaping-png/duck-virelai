"""Exact actor-independent records of observed ARC level-win boundaries."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

WIN_CAPSULE_SCHEMA = "virelai-win-capsule-v1"


@dataclass(frozen=True)
class FrameLayerRef:
    node_index: int
    layer_index: int
    rows: int
    cols: int
    sha256: str


@dataclass(frozen=True)
class WinCapsule:
    schema: str
    game_id: str
    completed_level: int
    actor: str
    transition_id: int
    action_id: int
    action_name: str
    acted_cell: tuple[int, int] | None
    level_root_ref: FrameLayerRef | None
    attempt_root_ref: FrameLayerRef | None
    pre_win_ref: FrameLayerRef | None
    winning_render_ref: FrameLayerRef | None
    successor_spawn_ref: FrameLayerRef | None
    terminal: bool
    outgoing_worldlines: dict[str, Any]
    evidence_friction: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return asdict(self)


def frame_layer_ref(record: Any, layer_index: int = -1) -> FrameLayerRef | None:
    """Reference one literal archived layer by location, geometry, and content hash."""
    layers = tuple(getattr(record, "layers", ()) or ())
    if not layers:
        return None
    normalized = layer_index if layer_index >= 0 else len(layers) + layer_index
    if normalized < 0 or normalized >= len(layers):
        return None
    descriptor = layers[normalized]
    payload = record.layer_bytes(normalized)
    digest = hashlib.sha256()
    digest.update(f"{descriptor.rows}x{descriptor.cols}:".encode("ascii"))
    digest.update(payload)
    return FrameLayerRef(
        node_index=int(record.node_index),
        layer_index=normalized,
        rows=int(descriptor.rows),
        cols=int(descriptor.cols),
        sha256=digest.hexdigest(),
    )


def build_win_capsule(
    *,
    game_id: str,
    before: Any,
    after: Any,
    transition: Any,
    level_root_ref: FrameLayerRef | None,
    attempt_root_ref: FrameLayerRef | None,
) -> WinCapsule | None:
    """Compile only a directly observed level/game win; infer no winning cause."""
    if not (transition.level_completed or transition.run_complete):
        return None

    friction: list[str] = []
    pre_win = frame_layer_ref(before)
    if pre_win is None:
        friction.append("MISSING_PRE_WIN_RENDER")

    terminal = bool(transition.run_complete)
    if terminal:
        winning_render = frame_layer_ref(after)
        successor = None
    else:
        winning_render = frame_layer_ref(after, len(after.layers) - 2) if len(after.layers) >= 2 else None
        successor = frame_layer_ref(after)
        if winning_render is None:
            friction.append("MISSING_OUTGOING_WIN_RENDER")
        if successor is None:
            friction.append("MISSING_SUCCESSOR_SPAWN")
    if level_root_ref is None:
        friction.append("MISSING_LEVEL_ROOT")
    if attempt_root_ref is None:
        friction.append("MISSING_ATTEMPT_ROOT")

    level = int(transition.level_before)
    return WinCapsule(
        schema=WIN_CAPSULE_SCHEMA,
        game_id=str(game_id),
        completed_level=level,
        actor=str(transition.actor),
        transition_id=int(transition.transition_id),
        action_id=int(transition.action_id),
        action_name=str(transition.action_name),
        acted_cell=transition.acted_cell,
        level_root_ref=level_root_ref,
        attempt_root_ref=attempt_root_ref,
        pre_win_ref=pre_win,
        winning_render_ref=winning_render,
        successor_spawn_ref=successor,
        terminal=terminal,
        outgoing_worldlines={
            "artifact": "continuity_tracks.json",
            "level": level,
            "status": "resolved_at_flush",
        },
        evidence_friction=tuple(friction),
    )


__all__ = [
    "FrameLayerRef",
    "WIN_CAPSULE_SCHEMA",
    "WinCapsule",
    "build_win_capsule",
    "frame_layer_ref",
]
