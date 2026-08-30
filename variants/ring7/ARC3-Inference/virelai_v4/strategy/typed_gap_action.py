"""
virelai_v4/strategy/typed_gap_action.py — deterministic typed-gap action logic.

WO-FM11-FIX-B (behavioral leg of Apex Ruling B). When the Registry resolves a
substantive cell to a `TypedGap` (no primitive built yet — WO-PRIMITIVES owns
it), the selector must emit a **deterministic, logged, gap-aware** action rather
than fall through to `random_probe`. This module holds the *pure* logic so it is
testable in the sandbox without `arcengine` (the action wrapper that builds the
GameAction lives in `action_selector.py`, which is arcengine-gated).

Constitutional posture:
  - FM-10: no module-level state, no counters, no caches. Pure over read-only
    inputs.
  - Law 10 ("Every Available Action Has a Use"): the gap routes to a legal
    available action, never a no-op.
  - SR boundary with WO-PRIMITIVES: this is a *placeholder* action — it writes
    no classification and runs no probe strategy. It only picks a legal action
    deterministically so the gap frame is auditable and reproducible.

Determinism: the chosen action is a pure function of `(available_actions,
frame)`. Variation across distinct frames keys ONLY on the read-only frame
content (via a process-stable `hashlib` digest — never Python's randomized
`hash()`), so the gap does not lock-step on a changing world yet is identical
for identical inputs across repeated calls and across a fresh process.
"""

from __future__ import annotations

import hashlib
import logging
import os
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# WO-LOGGING-CARDINALITY: per-session tally of TYPED_GAP gap-cell hits, keyed
# by (world_type, attribute_type_name). Reset at agent init via
# reset_typed_gap_tally(); summarized at end-of-life via flush_typed_gap_tally().
# Module-level (not context) because the emission sites are pure strategy
# functions without context access; the agent lifecycle drives reset/flush.
_typed_gap_tally: Dict[Tuple[str, str], int] = defaultdict(int)


def _quiet() -> bool:
    """Match the established VIRELAI_QUIET idiom (virelai.py:159)."""
    return os.environ.get("VIRELAI_QUIET", "0") == "1"

# RESET is never a probe action (excluded from gap selection, as in
# random_probe_tool).
_RESET_ACTION_ID = 0


def stable_frame_int(frame: Optional[np.ndarray]) -> int:
    """A process-stable integer derived from read-only frame content.

    Uses hashlib (NOT the built-in `hash()`, which is per-process randomized) so
    the value is identical across a fresh process — the determinism the gap
    action requires. `None`/empty frame → 0 (still deterministic)."""
    if frame is None:
        return 0
    arr = np.asarray(frame)
    if arr.size == 0:
        return 0
    digest = hashlib.sha256(arr.tobytes()).digest()
    return int.from_bytes(digest[:8], "big")


def select_typed_gap_action_id(
    available_actions: List[int],
    frame: Optional[np.ndarray],
) -> int:
    """Pick a legal action id for a typed-gap frame — deterministic, no rng, no
    state. Excludes RESET. Frame-keyed so it varies as the world changes.

    Falls back to the first available action only in the degenerate case where
    the only available action is RESET (or the list is otherwise all-RESET);
    returns RESET only if that is genuinely all that is offered."""
    legal = sorted(a for a in available_actions if a != _RESET_ACTION_ID)
    if not legal:
        return available_actions[0] if available_actions else _RESET_ACTION_ID
    return legal[stable_frame_int(frame) % len(legal)]


def gap_click_coords(
    frame: Optional[np.ndarray],
    grid_rows: int,
    grid_cols: int,
) -> Tuple[int, int]:
    """Deterministic (x, y) within grid bounds for an ACTION6 gap click —
    frame-keyed, pure. Mirrors random_probe_tool's coordinate need but is
    reproducible."""
    rows = max(1, int(grid_rows))
    cols = max(1, int(grid_cols))
    s = stable_frame_int(frame)
    x = s % cols
    y = (s // cols) % rows
    return (x, y)


def _typed_levers(library) -> List[Tuple[int, FrozenSet[Tuple[int, int]]]]:
    """(region_id, cells) for TYPED levers (role LEVER and lever_mechanism
    committed), in canonical region-id order. Empty list when library is None
    or no typed lever exists. Pure read — no mutation of library state.

    WO-FALLBACK-LEVER-ROTATION / -ATTRIBUTION. Imports are function-local so
    this module stays standalone-importable in the sandbox (library/ pulls
    scipy via its package __init__; strategy never imports it at module load).
    library/ does not import strategy/ (library_sync.py:13), so no circular
    import is created.
    """
    if library is None:
        return []
    from virelai_v4.library.library_roles import LibraryRole
    # WO_CAPTAIN_READS_TAPE D4: target the DERIVED lever, not the Store-B
    # categorical — a categorical LEVER without its axis (a one-sided write) is
    # not a real lever to anchor a gap click on.
    from virelai_v4.library.nested_read import derived_role
    out: List[Tuple[int, FrozenSet[Tuple[int, int]]]] = []
    for region_id in sorted(library.objects.keys()):
        obj = library.objects[region_id]
        # WO-E7 (type/condition de-collapse): "characterized" = type-known OR
        # condition-known. A saturated lever's type field no longer reads
        # SATURATED (it's on obj.saturated), but the lever is still
        # characterized and must stay in the typed-lever rotation — without the
        # OR, de-collapse would silently drop saturated levers from this live
        # action-selection path (select_anchored_lever).
        if (derived_role(obj) == LibraryRole.LEVER.value
                and (obj.lever_mechanism is not None
                     or getattr(obj, "saturated", False))
                and obj.cells):
            out.append((region_id, frozenset(obj.cells)))
    return out


def select_anchored_lever(
    frame: Optional[np.ndarray],
    library,
) -> Optional[Tuple[int, FrozenSet[Tuple[int, int]]]]:
    """Hash-select one TYPED lever → (region_id, cells), or None when none
    exists. The SINGLE source of the fallback's lever choice: both the click
    coordinate (gap_click_coords_lever_anchored) and the press-attribution
    metadata (WO-FALLBACK-LEVER-ATTRIBUTION) derive from this call, so they
    cannot diverge. Deterministic (stable_frame_int), read-only.
    """
    typed = _typed_levers(library)
    if not typed:
        return None
    return typed[stable_frame_int(frame) % len(typed)]


def gap_click_coords_lever_anchored(
    frame: Optional[np.ndarray],
    library,
    grid_rows: int,
    grid_cols: int,
) -> Tuple[int, int]:
    """Hash-indexed ACTION6 (x, y) over the TYPED-lever set when typed levers
    exist; otherwise fall through to the board-hash gap_click_coords.

    WO-FALLBACK-LEVER-ROTATION — the degenerate floor of Blueprint §5.4 directed
    deepen. Same frame-keyed determinism as gap_click_coords (reuses
    stable_frame_int); the only change is WHICH coordinate the post-walk fallback
    clicks: a known typed lever instead of a hash-derived board cell. Stateless,
    read-only against library.

    Coordinate derivation mirrors the real lever-press primitive exactly
    (tier4_click.py:58-60): representative_coordinate(cells) returns (row, col)
    guaranteed in-cell, and the ACTION6 payload is (x=col, y=row).
    """
    selected = select_anchored_lever(frame, library)
    if selected is None:
        return gap_click_coords(frame, grid_rows, grid_cols)
    from virelai_v4.library.region_geometry import representative_coordinate
    row, col = representative_coordinate(set(selected[1]))
    return (col, row)   # (x, y) — x=col, y=row, matching tier4_click


def gap_notice(world_type: str, attribute_type_name: str) -> str:
    """The one-line audit notice naming the gap cell. Pure string builder."""
    return (
        f"[TYPED_GAP] ({world_type}, {attribute_type_name}) -> deterministic "
        f"action; primitive pending WO-PRIMITIVES"
    )


def emit_typed_gap_warning(world_type: str, attribute_type_name: str) -> None:
    """Emit a TYPED_GAP notice with first-occurrence-only semantics + silent
    tally (WO-LOGGING-CARDINALITY, closes F-1 flood + F-2 quiet-suppression).

    Non-quiet: the first hit of each (world, probe) tuple emits one WARNING;
    subsequent hits are silently tallied (the end-of-session summary reports
    totals via flush_typed_gap_tally). This collapses the per-action flood
    (2000+ on ft09) to once-per-tuple + one summary.

    Quiet (VIRELAI_QUIET=1): routes to DEBUG (suppressed by the root-WARNING
    handler virelai.py sets) and still tallies — F-2's intent that quiet
    suppress TYPED_GAP. The deliberate pre-WO "survives quiet" behavior was
    exactly F-2's complaint.
    """
    key = (world_type, attribute_type_name)
    is_first = key not in _typed_gap_tally
    _typed_gap_tally[key] += 1
    msg = gap_notice(world_type, attribute_type_name)
    if _quiet():
        logger.debug(msg)
        return
    if is_first:
        logger.warning(
            "%s (first occurrence; subsequent suppressed — see end-of-session "
            "[TYPED_GAP TALLY])", msg)
    # subsequent non-quiet hits: silently tallied, no emission.


def flush_typed_gap_tally() -> None:
    """Emit the end-of-session tally summary, then reset. Called from the
    agent's end-of-life diagnostic. No-op on empty tally. Quiet: reset only,
    no summary (F-2)."""
    if not _typed_gap_tally:
        return
    if _quiet():
        _typed_gap_tally.clear()
        return
    lines = ["[TYPED_GAP TALLY] (session totals):"]
    for (world, probe), count in sorted(_typed_gap_tally.items()):
        lines.append(f"  ({world}, {probe}): {count} occurrence(s)")
    logger.warning("\n".join(lines))
    _typed_gap_tally.clear()


def reset_typed_gap_tally() -> None:
    """Reset tally at agent init / new-session boundary (no cross-game leak)."""
    _typed_gap_tally.clear()


def stamp_silence_emitter(context, label: str) -> None:
    """WO_PUSH_SILENCE_LABEL_COVERAGE: stamp the emitter provenance for a
    silence-class emission — the single site that can't forget. Unconditional on
    action kind: a directional (non-click) typed-gap / random-fallback emission
    must be as visible to the Push trigger as a click one (Capsule-42 fixed the
    ``value == 6`` gate that made NAV worlds mute). No-op when context is None."""
    if context is not None:
        context.last_emitter_path = label


__all__ = [
    "stable_frame_int",
    "select_typed_gap_action_id",
    "gap_click_coords",
    "gap_notice",
    "emit_typed_gap_warning",
    "flush_typed_gap_tally",
    "reset_typed_gap_tally",
    "stamp_silence_emitter",
]
