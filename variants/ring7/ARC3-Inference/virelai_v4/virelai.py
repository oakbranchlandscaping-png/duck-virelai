"""
Virelai V4 — Phase 0 Agent + WO-03 Perception + WO-04 Library Sync

The simplest correct agent that houses the Virelai architecture.
Lives natively inside the framework's choose_action loop.
No spine. No bridge. No daemon thread. No phases.

The six-step choose_action pipeline:
  1. Parse — extract grid, game state, available actions
  2. Perceive — FrameDelta, CellHistory, StateTracker (WO-03)
  3. Sync Library — GridScan → objects, FrameDelta → change counts (WO-04)
  4. Target — (Campaign 3: routing directives)
  5. Strategize — (Campaign 4+: action selection)
  6. Return — random legal action (placeholder for priority stack)
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import sys
import time
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

import numpy as np

from arcengine import FrameData, GameAction, GameState

from virelai_v4._agent_stub import Agent
from virelai_v4.context import VirelaiContext
from virelai_v4.lifecycle import (
    env_cap_reached,
    is_terminal_none_frame_error,
    should_stop,
)
from virelai_v4.cybernetic.frame_delta import compute_frame_delta
from virelai_v4.cybernetic.cell_history import CellHistory, update_cell_history
from virelai_v4.cybernetic.state_tracker import StateTracker
from virelai_v4.cybernetic.push_fallback import (
    should_fire as push_should_fire,
    is_pull_silent as push_is_pull_silent,
    can_issue_reset as push_can_issue_reset,
    is_believed_inert as push_is_believed_inert,
    representative_cell as push_representative_cell,
    candidates_from_roster as push_candidates_from_roster,
    render_push_verdict as push_render_verdict,
    PushStats,
    render_push_stats,
)
from virelai_v4.library.library_sync import sync_library
from virelai_v4.library.cell_transition_view import TotalCellTransitions  # WO-W1-02a
from virelai_v4.library.counter_march import confirm_counter_on_death  # WO-E14 D3
from virelai_v4.library.semantic_library import (
    SemanticLibrary, LibraryHeader, LibraryExploration,
)
from virelai_v4.library.ego_mask import compute_ego_mask
from virelai_v4.targeting import assess_target_state, route
from virelai_v4.strategy.action_selector import select_action
from virelai_v4.library.diagnostics import (
    render_end_of_life_report,
    render_terminal_summary,
)
from virelai_v4.library.field_card import render_field_card
# WO-EYE-01 (The Eyes front end): animation perception emit. Pure read,
# diag-gated, writes no belief. Reads the interior frame layers on the DISJOINT
# animation path (WO-EYE-00); the persistent path's frame[-1] source is untouched.
from virelai_v4.perception.animation import emit_animation_turn_diag

logger = logging.getLogger(__name__)


# Choke-point observability write — implementation lives in
# virelai_v4/observability_choke_point.py so unit tests in
# tests/test_virelai.py can import it without the arcengine dep that
# this module's top-level imports drag in. The write site remains
# semantically a single choke-point (Virelai.choose_action is the only
# production caller). See WO-OCD-CHOKE-POINT Step 4 build report.
from virelai_v4.observability_choke_point import record_action_at_choke_point

# WO-OCD-CAPTAIN-IMPLEMENTATION — captain dispatch. Runs before the
# legacy tier dispatch (_dispatch_action); if it returns a GameAction,
# that action is final for the frame. If None, _dispatch_action runs.
# See virelai_v4/captain.py for the cursor and dispatch table.
# WO-OCD-CAPTAIN-ORDERING-FIX — captain_preconditions_met gates the
# invocation on library readiness. Helper lives in captain.py (not
# virelai.py) so unit tests in tests/test_captain.py can import it
# without the arcengine top-import that virelai.py drags in. The
# gate site itself is at virelai.py:choose_action; the helper is
# the implementation.
from virelai_v4.captain import captain_preconditions_met, run_captain

# WO-XLEVEL-02a — the §2.8.5 level-advance hook (snapshot + rescan + discard).
# Called from the level-advance block in choose_action, between
# reset_for_new_level() and _sync_library() (the trace-f71b507 seam).
from virelai_v4.library.substrate.level_advance import run_level_advance_rebuild


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _emitted_cell(action: Any) -> Optional[Tuple[int, int]]:
    """WO-R1-02c — the ``(row, col)`` an emitted action acted on, or None.

    Reads the coordinate off the action's own ``action_data`` — the same source
    the observability choke point reads (``{"x": col, "y": row}``, set by every
    coordinate emitter) — so ONE site covers every emitter, not just the push
    path. A non-coordinate action (directional, RESET) has no data → None.

    Pure: reads the action, returns a tuple. Never raises into the hot path.
    """
    try:
        data = getattr(action, "action_data", None)
        if data is None:
            return None
        _d = data.model_dump()
        x, y = _d.get("x"), _d.get("y")
        if x is None or y is None:
            return None
        return (int(y), int(x))          # (row, col) — SPEC_WEAVE convention
    except Exception:                    # pragma: no cover - defensive
        return None


def _previous_settled_grid(log) -> Optional[list[list[int]]]:
    """The settled grid of the node BEFORE the one just appended, or ``None``.

    WO-DELIVERY-CLASS-02. The capture append records the current node first, so the
    predecessor is the second-to-last record. **`None` is a supplied answer** — *there is no
    predecessor* — and is not the same absence as a caller that did not look; the classifier
    keeps the two apart by signature."""
    records = getattr(log, "records", ()) if log is not None else ()
    if len(records) < 2:
        return None
    return log.reconstruct(records[-2].node_index)[-1]


def _grid_from_frame(frame: FrameData) -> Optional[list[list[int]]]:
    """Extract the current 2D grid from a FrameData.

    frame.frame is 3D: list of layers. We use the last layer (frame[-1])
    which is the current grid, matching the SDK convention.
    """
    if frame.frame:
        return frame.frame[-1]
    return None


def _hash_grid(grid: list[list[int]]) -> bytes:
    """Fast content hash of a 2D grid. Returns raw bytes for set storage."""
    h = hashlib.md5()
    for row in grid:
        h.update(bytes(row))
    return h.digest()


def _changed_cells(
    prev_grid: Optional[np.ndarray], curr_grid: np.ndarray,
) -> FrozenSet[Tuple[int, int]]:
    """WO-W1b-02: the frame's changed-set, computed once here and threaded
    to _sync_library -> sync_library -> compute_world_delta, mirroring
    world_delta_computer.py's Step 2 exactly — same two grids, same
    try/except, same honest-empty fallback on either a None prior grid or
    an unexpected comparison failure. Extracted to a single pure function
    (rather than inlined at the call site) so the construction remains one
    assignment statement in choose_action, matching the "one birthplace"
    pin's shape for _cell_transitions (TotalCellTransitions is likewise a
    single call whose own None-tolerance lives inside the class, not
    branched at the call site).

    Does NOT touch cybernetic/frame_delta.py's independent diff — see the
    PARALLAX FENCE at this function's call site in choose_action.
    """
    if prev_grid is None:
        return frozenset()
    try:
        changed_mask = (prev_grid != curr_grid)
        return frozenset((int(r), int(c)) for r, c in np.argwhere(changed_mask))
    except Exception:
        return frozenset()


def _legal_actions(available_ids: list[int], exclude_reset: bool = True) -> list[int]:
    """Filter available action IDs, optionally excluding RESET."""
    if exclude_reset:
        return [aid for aid in available_ids if aid != GameAction.RESET.value]
    return list(available_ids)


def _compute_ego_pos_from_grid(
    np_grid: np.ndarray,
    ego_value_set: frozenset,
) -> Optional[Tuple[int, int]]:
    """
    Derive current ego centroid directly from raw pixel values.
    Used for ego mask computation — runs BEFORE _sync_library so must
    not read library state.

    Known limitation: on games where ego pixel classes are shared with
    world objects (e.g. ls20 class 9), the centroid is slightly biased
    by non-ego same-class cells. Error is bounded and acceptable for
    mask computation purposes. A future work order may add radius-
    clamping to improve accuracy.
    """
    if not ego_value_set:
        return None
    rows, cols = np.where(np.isin(np_grid, list(ego_value_set)))
    if len(rows) == 0:
        return None
    return (int(round(float(rows.mean()))), int(round(float(cols.mean()))))


# ---------------------------------------------------------------------------
# The Agent
# ---------------------------------------------------------------------------

class Virelai(Agent):
    """Virelai V4 — Phase 0 + WO-03 Perception + WO-04 Library Sync.

    Implements choose_action with:
    - Typed VirelaiContext persisting between calls
    - Strict available_actions enforcement
    - Distinct WIN / GAME_OVER / NOT_PLAYED handling
    - Frame delta detection via FrameDelta (WO-03)
    - CellHistory per-cell behavioral accumulator (WO-03)
    - StateTracker novel/repeated state tracking (WO-03)
    - Library sync: GridScan → objects, FrameDelta → change counts (WO-04)
    - Lightweight MD5 visited set (Phase 0 tracker — parallel to StateTracker)
    - Random legal action selection (placeholder for priority stack)
    """

    MAX_ACTIONS: int = sys.maxsize

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.ctx = VirelaiContext()
        self._rng = random.Random(
            int(time.time() * 1_000_000) + hash(self.game_id) % 1_000_000
        )
        self._quiet = os.environ.get("VIRELAI_QUIET", "0") == "1"
        if self._quiet:
            logging.getLogger().setLevel(logging.WARNING)
        # WO-LOGGING-CARDINALITY: clear the per-session TYPED_GAP tally at agent
        # init so counts never leak across games.
        from virelai_v4.strategy.typed_gap_action import reset_typed_gap_tally
        reset_typed_gap_tally()
        # WO-PHASE1-DIAG-DUMP (NR-01 Phase 1): open the read-only per-frame
        # physics dump file when VIRELAI_DIAG_DUMP=1; no-op otherwise.
        from virelai_v4.diagnostics.frame_dump import init_dump_file
        init_dump_file()
        self._log(f"Virelai V4 initialized for {self.game_id}", always=True)

    # ------------------------------------------------------------------
    # Centralized log (WO-C3-04a)
    # ------------------------------------------------------------------

    def _log(self, msg: str, always: bool = False) -> None:
        """Route all solver diagnostic output through one function.

        In quiet mode (VIRELAI_QUIET=1), the root logger is set to WARNING,
        silencing all INFO output from both our agent and the framework.
        always=True messages bypass the logger and go directly to stdout,
        ensuring diagnostic blocks and lifecycle events are always visible.
        """
        if always:
            print(msg)
        elif not self._quiet:
            logger.info(msg)

    # ------------------------------------------------------------------
    # Framework contract
    # ------------------------------------------------------------------

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when game is won or operator-set bounds reached.

        Competition mode (no VIRELAI_MAX_* env vars set):
            Only WIN terminates. Platform wall-clock and rate-limit
            decide the rest.

        Testing mode (VIRELAI_MAX_LIVES and/or VIRELAI_MAX_ACTIONS set):
            WIN, operator life cap, or operator action cap terminates.

        WO-GAME-OVER-DETECTION: also stops when the environment has signalled
        terminal (ctx.env_terminated, set by take_action when arc_env.step
        returns no frame). This is "the game tells us when to stop" — it
        preserves the no-self-cap captain ruling: the captain never caps
        itself; the environment's end-of-game is the cap.
        """
        return should_stop(
            self.ctx.env_terminated,
            latest_frame.state is GameState.WIN,
            self.ctx.lives_used,
            self.action_counter,
        )

    def take_action(self, action):
        """Submit the action; treat an empty environment response as terminal.

        WO-GAME-OVER-DETECTION: the framework's `_convert_raw_frame_data`
        raises `ValueError("Received None frame data ...")` when `arc_env.step`
        returns no frame — the environment has ended the game and has no frame
        to return. Rather than crash the agent loop, we mark the environment
        terminal (so the next `is_done()` exits) and return None, which the
        main loop's `if frame := self.take_action(...)` walrus already handles
        (it skips append). All other ValueErrors propagate unchanged.
        """
        try:
            return super().take_action(action)
        except ValueError as exc:
            if is_terminal_none_frame_error(exc):
                self.ctx.env_terminated = True
                self._log(
                    "Environment returned no frame — game terminal; stopping.",
                    always=True,
                )
                return None
            raise

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        """One frame in, one action out.

        The three-step loop that will become Virelai's cognitive core:
        1. Observe  — what changed? (FrameDelta, CellHistory, StateTracker)
        2. Update   — what does the library now know?
        3. Decide   — what's the single best action?
        """
        state = latest_frame.state
        available = latest_frame.available_actions

        # WO-OCD-ACTIONLOG — populate the sidecar action-log path lazily on
        # the first frame after start_recording() ran. The agent base class
        # creates self.recorder before choose_action is first called; the
        # filename is then derivable. The path persists for the rest of the
        # game (PERSIST_LIVES_AND_LEVELS). Defensive: if no recorder exists
        # (unit tests, custom harnesses), action_log_path stays None and
        # the emitter sites silently skip the sidecar write.
        if self.ctx.action_log_path is None and hasattr(self, "recorder"):
            from agents.recorder import derive_action_log_path
            self.ctx.action_log_path = derive_action_log_path(self.recorder.filename)

        # ---- Capture (WO-CC-S1) — the lossless given, before any perception ----
        # Append-only, interpretation-free record of what the platform handed
        # this node: all layers of latest_frame (not frame[-1]), its identity
        # fields, and the inbound composite edge — the previous issued action
        # (self.ctx.last_action_id, self.ctx.last_action_target), normalized in
        # the capture module via the real _norm_key. Node 0 (no prior action)
        # records edge=None. Runs on EVERY entry, including WIN/GAME_OVER — it
        # logs what arrived, whatever the state. Read sidecar: this writes only
        # self.ctx.frame_record_log and no belief surface.
        _inbound_edge = (
            (self.ctx.last_action_id, self.ctx.last_action_target)
            if self.ctx.last_action_id is not None
            else None
        )
        self.ctx.frame_record_log.append(
            latest_frame, action=_inbound_edge, frames_len=len(frames),
            # WO-R1-02c: the cell that produced this node — the same channel and
            # lifecycle as the edge's action_id above. Completes the record.
            acted_cell=self.ctx.last_action_cell,
        )

        # ---- Observe ----
        grid = _grid_from_frame(latest_frame)
        np_grid = None   # WO-PUSH-R2-FIX1: bound on every path; only set live below
        is_novel = False

        if grid is not None:
            grid_hash = _hash_grid(grid)

            # Phase 0 lightweight visited tracking (MD5, kept parallel to StateTracker)
            if grid_hash in self.ctx.visited:
                self.ctx.repeated_count += 1
            else:
                self.ctx.visited.add(grid_hash)
                self.ctx.novel_count += 1
                is_novel = True

            # Spawn capture
            if self.ctx.spawn_grid is None and state is GameState.NOT_FINISHED:
                self.ctx.spawn_grid = grid

        # WO-EYE-01 (The Eyes front end): per-turn animation perception.
        # Pure read, diag-gated (VIRELAI_DIAG_DUMP), writes no belief. Reads the
        # interior frame layers on the DISJOINT animation path (WO-EYE-00) — the
        # persistent path's independent frame[-1] re-extraction at :737 and the
        # grid= source are NOT touched. No-op unless diagnosing.
        # WO-DELIVERY-CLASS-02 · **THE SAME PREDECESSOR THE WEAVE-SIDE CLASS USES.** The
        # capture append above has already recorded THIS node, so the previous node's
        # settled grid is the second-to-last record. Both producers now ask one question and
        # cannot drift; `None` on the first node says a predecessor does not exist.
        emit_animation_turn_diag(latest_frame, turn_index=self.ctx.step_count,
                                 previous=_previous_settled_grid(self.ctx.frame_record_log))

        # WO-04c: capture pre-action grid for ego displacement detection.
        # _perceive() overwrites ctx.prev_grid with the current frame, so this
        # must be saved before _perceive runs.
        prev_grid_for_ego = self.ctx.prev_grid  # None on first frame; np.ndarray thereafter

        # WO-03 perception — only on NOT_FINISHED frames
        if state is GameState.NOT_FINISHED and grid is not None:
            self.ctx.is_death_frame = False  # Clear death-frame flag (WO-C5-01 FLAG-017)
            np_grid = np.array(grid, dtype=np.int32)
            # WO-W1b-01: one birthplace. Constructed once, here, before either
            # consumer (_perceive below; _sync_library at the second
            # NOT_FINISHED guard, ~89 lines down — the two guards share this
            # exact condition, textually identical and provably co-entailed:
            # neither `state` nor `grid` is reassigned between them and there
            # is no early return in between, so entering this block guarantees
            # the second guard is entered too, later in this same call).
            # Threaded as an explicit parameter to both; stored nowhere on
            # self.ctx — a context field is the stale-read hazard WO-W1-02
            # found with context.world_delta. None-tolerant by construction
            # (library/cell_transition_view.py's TotalCellTransitions): on the
            # first frame of a life self.ctx.prev_grid is None and this is an
            # empty, still-Mapping-conforming view — both consumers already
            # handle that case exactly as they did before this WO.
            _cell_transitions = TotalCellTransitions(self.ctx.prev_grid, np_grid)
            # WO-W1b-02: birth the changed-set beside the catalog, same
            # guard, same two grids — matches world_delta_computer.py's
            # Step 2 exactly (this is the lift, not a new computation).
            # Assigned once, here, before _perceive is called.
            # WO-W1b-03 UPDATE: now referenced at BOTH _perceive and
            # _sync_library (superseding W1b-02's "never passed into
            # _perceive" note) — _perceive's own cell-history-update gate
            # and loop migrate to read this canonical changed-set instead of
            # delta.changed_cells (RULING_OBSERVERS_INTEGRATOR_v1 Clause A:
            # consumers-of-record read the canonical record; the observer,
            # compute_frame_delta, is retained for D-3 grading only).
            # PARALLAX FENCE: cybernetic/frame_delta.py is NOT touched and
            # does not read this value. compute_frame_delta keeps computing
            # its own independent diff — that redundancy is the instrument
            # the D-3 check grades (RULING_OBSERVERS_INTEGRATOR_v1 §1, §3);
            # collapsing it here would make D-3 a tautology.
            _raw_cells = _changed_cells(self.ctx.prev_grid, np_grid)
            # WO-W1b-03: the same two identity facts the observer
            # (compute_frame_delta, called inside _perceive below) carries
            # for this frame — born here, beside raw_cells, from the exact
            # same source expressions _perceive's own compute_frame_delta
            # call uses (self.ctx.step_count; self.ctx.last_action_id or 0),
            # confirmed unchanged between this point and that call (§0.2).
            # Threaded to both _perceive and _sync_library, mirroring
            # _cell_transitions' dual-threaded pattern, not raw_cells'
            # single-threaded one.
            _step = self.ctx.step_count
            _action_id = self.ctx.last_action_id or 0
            self._perceive(
                np_grid,
                cell_transitions=_cell_transitions,
                raw_cells=_raw_cells,
                step=_step,
                action_id=_action_id,
            )
            self.ctx.actions_this_life += 1
            # WO-R4 D2: legal capture relocated to AFTER _sync_library (below) so
            # it reads the FRESH roster, not the one-sync-stale one.

            # --- Ego mask (WO-02) ---
            # Save previous ego position before anything updates it
            self.ctx.prev_ego_pos = self.ctx.ego_current_pos

            # Derive current ego position from raw pixels (Frame Sovereignty — must run before _sync_library)
            _lib = self.ctx.semantic_library
            if _lib is not None:
                _ego_mode = getattr(_lib.header, 'ego_mode', None)
                _ego_value_set = getattr(_lib.header, 'ego_value_set', frozenset()) or frozenset()
                _ego_body_cells = getattr(_lib.header, 'ego_body_cells', frozenset()) or frozenset()
                _grid_shape = np_grid.shape[:2]  # (rows, cols)

                if _ego_mode == "EMBODIED":  # NAV world — use exact string found in codebase
                    _current_pos = _compute_ego_pos_from_grid(np_grid, _ego_value_set)
                    self.ctx.ego_mask = compute_ego_mask(
                        ego_body_cells=_ego_body_cells,
                        current_pos=_current_pos,
                        prev_pos=self.ctx.prev_ego_pos,
                        grid_shape=_grid_shape,
                    )
                else:
                    # CLICK world or not yet classified — no embodied ego
                    self.ctx.ego_mask = np.zeros(_grid_shape, dtype=bool)

        # Derive grid_changed from FrameDelta (supersedes Phase 0 list comparison)
        grid_changed = (
            self.ctx.frame_delta is not None
            and self.ctx.frame_delta.total_changed > 0
        )

        # Level advance
        # WO-LB-01 — THE TWO-WAY TRIGGER. The gate compares the platform's raw
        # level against a TRUE LAST-SEEN cursor with `!=`, not the old monotone
        # `>` against a high-water max. The game descends (a life lost at level 2
        # returns to level 0), and the old `>` never fired on the way down — so
        # every PERSIST_LIVES_RESET_LEVEL field (frame_record_log, spawn_grid,
        # grid_scan, the sweep) carried higher-level state into the lower level
        # silently (WO_LB_00 Q3). `!=` fires on BOTH boundaries; the descent runs
        # the SAME coupled block (reset -> spawn_grid -> rebuild -> sync) as the
        # ascent — one code path, not a copy. The cursor survives reset_for_new_life
        # (PERSIST_LIVES_AND_LEVELS), so a death that descends is seen on the very
        # next NOT_FINISHED frame — a separate frame from the GAME_OVER life-reset,
        # so the two resets never collide (frame-separation determinacy, WO_LB_01 §3).
        if latest_frame.levels_completed != self.ctx.last_level_seen:
            self.ctx.last_level_seen = latest_frame.levels_completed
            # WO-MINE-03: clear level-scoped knowledge (PERSIST_LIVES_RESET_LEVEL
            # + PER_LIFE_SCRATCHPAD). Preserves PERSIST_LIVES_AND_LEVELS (library,
            # visited, lifecycle counters) and PERSIST_LEVELS_RESET_LIFE
            # (actions_this_life, which spans levels within a life).
            # WO-PHASE4-01 (OTA-04): reset MUST run before spawn_grid is set —
            # spawn_grid is a PERSIST_LIVES_RESET_LEVEL field, so reset clears
            # it. Setting before reset made the assignment dead.
            self.ctx.reset_for_new_level()
            if grid is not None:
                self.ctx.spawn_grid = grid  # New level = new spawn
            self._log(f"Level boundary → {self.ctx.last_level_seen}", always=True)
            # WO-XLEVEL-02a (§2.8.5 hook, Shape 2 — seam per trace f71b507):
            # snapshot ghost priors by TypeSignature, rescan the L(N+1) spawn,
            # discard the Level-N ghosts, repopulate fresh slots. Runs BEFORE
            # _sync_library, so fresh slots carry previous_class_signature=None
            # and the first Mode B pass initializes signatures WITHOUT revoking
            # (library_sync.py:177-180) — the stale-library spasm stops here.
            # The snapshot is stored for WO-XLEVEL-02b (type-match + inherit);
            # 02a captures only, it does not apply.
            if grid is not None and self.ctx.semantic_library is not None:
                self.ctx.xlevel_prior_snapshot = run_level_advance_rebuild(
                    self.ctx,
                    self.ctx.semantic_library,
                    grid,
                    list(latest_frame.available_actions),
                )
                self._log(
                    f"[XLEVEL-02a] rebuilt library for level "
                    f"{self.ctx.last_level_seen}: "
                    f"{len(self.ctx.semantic_library.objects)} fresh slots, "
                    f"{len(self.ctx.xlevel_prior_snapshot)} type-priors captured",
                    always=True,
                )

        if latest_frame.win_levels:
            self.ctx.win_levels = latest_frame.win_levels

        # ---- Update (Step 3 — Library Sync, WO-04) ----
        if state is GameState.NOT_FINISHED and grid is not None:
            # WO-W1b-01: `_cell_transitions` is the SAME object constructed
            # once above, before _perceive — not a second, independently
            # built copy. Reachable here by ordinary function-level scoping;
            # safe because this guard and the one guarding _cell_transitions'
            # construction are provably co-entailed (see the comment there).
            self._sync_library(
                latest_frame,
                prev_grid=prev_grid_for_ego,
                cell_transitions=_cell_transitions,
                raw_cells=_raw_cells,
                step=_step,
                action_id=_action_id,
            )
            # WO-R4 D2: legal capture now runs here — AFTER the sync — so the
            # complex-action roster is fresh (census S1 freshness gap closed).
            self._capture_legal_at_first_seen(np_grid, available)

        # ---- Update ego position (WO-03 NAV) ----
        if (state is GameState.NOT_FINISHED
                and self.ctx.semantic_library is not None
                and self.ctx.semantic_library.header.world_type == "NAV"
                and self.ctx.semantic_library.header.ego_confirmed):
            self._update_ego_position(library=self.ctx.semantic_library)

        # ---- Update NavAtlas substrate (WO-CAMPAIGN3-PHASE1-04) ----
        # After ego position has been updated for this frame, record the
        # previous action's move into nav_atlas so walkable_classes /
        # blocked_classes / visited_cells stay current as the ego moves.
        # Suppressed when nav_atlas is None (stride probe still in progress;
        # probe owns substrate-bootstrap per WO-03).
        if state is GameState.NOT_FINISHED and grid is not None:
            self._record_nav_move(
                current_grid=np_grid,
                prev_grid=prev_grid_for_ego,
            )

        # ---- Phase 2 contact reactivity (WO-CAMPAIGN3-PHASE2-01) ----
        # After Phase 1 substrate update, detect lever activations via
        # pixel-budget excess. Lever evidence writes to NavAtlas
        # (nav_lever_candidates, contacted_sites, mutation_targets) and
        # transitions library role to LEVER if a containing object exists
        # (orphan tally otherwise). Gated on substrate readiness +
        # NAV-only + cardinal action per WO-PHASE2-00 §10.1.
        if state is GameState.NOT_FINISHED and grid is not None:
            self._record_contact_reactivity(
                current_grid=np_grid,
                prev_grid=prev_grid_for_ego,
            )

        # ---- Target (Step 4 — Targeting, WO-C3-03) ----
        if state is GameState.NOT_FINISHED and self.ctx.semantic_library is not None:
            target_state = assess_target_state(self.ctx.semantic_library)
            self.ctx.target_state = target_state
            self.ctx.routing_directive = route(target_state)

        # ---- Decide ----
        # WO-OCD-CHOKE-POINT (Step 2): lifecycle dispatch extracted to
        # _dispatch_action. The helper returns the selected GameAction for
        # any state (terminal RESET branches included). Compensating
        # extraction offsets the choke-point write block added in Step 3.
        # Step 4: reset the per-frame emitter provenance tag before
        # dispatch so each frame's tag reflects only its own emitter (no
        # stale carryover from prior-frame ACTION6 emissions).
        self.ctx.last_emitter_path = None
        self.ctx.last_action_target = None   # WO-R4: reset beside the emitter tag
        # WO-WEAVE-SWEEP-01 Phase 1 — checked BEFORE the captain branch below,
        # so exactly one path ever produces this frame's action (never both;
        # same exclusivity shape the single-actor doctrine already enforces
        # between the captain and legacy dispatch). If the weave coverage
        # sweep is active and unterminated, it owns this frame outright and
        # the captain is never even asked — a severed feed per
        # RULING_GOLDEN_RUN_v1, not a modification to any legacy file
        # (captain.py, targeting/dispatch_registry.py, strategy/tier4_click.py,
        # strategy/typed_gap_action.py, strategy/click_sweep.py are untouched
        # by this branch's existence). See weave/coverage_sweep.py and
        # _maybe_weave_sweep_action's own docstring for the read-only-boundary
        # and cadence constraints this build is bound by
        # (WO-WEAVE-SWEEP-01 Phase 0 §0.3, §0.2).
        #
        # DELIBERATE DEVIATION FROM THE WO'S SUGGESTED if/elif/else SHAPE:
        # an elif here would nest the captain If as a descendant of this
        # branch's If node (Python represents `elif` as `orelse=[If(...)]`).
        # tests/test_choose_action_contracts.py's
        # TestCaptainRoutingGatedToNotFinished walks EVERY ast.If node's full
        # subtree looking for the first one whose subtree calls run_captain,
        # then asserts THAT node's own `.test` mentions
        # `captain_preconditions_met`/`NOT_FINISHED`/`state` — an elif nesting
        # makes the OUTER (weave-sweep) If the one it finds, since
        # run_captain is still reachable in that outer node's subtree via the
        # nested elif, and that outer node's own test does not mention
        # captain_preconditions_met — a false regression on an existing,
        # real contract (WO-E06 terminal-misroute guard), not a behavior
        # change. Three independent, sequential, top-level If statements
        # with an explicit `_action_decided` flag give the IDENTICAL
        # exclusivity guarantee (exactly one branch ever sets `action`)
        # while leaving the captain If's own `.test` expression exactly as
        # it was — a real top-level statement, not nested inside another.
        _weave_action = self._maybe_weave_sweep_action(state, grid_changed)
        _action_decided = _weave_action is not None
        if _action_decided:
            action = _weave_action

        # WO-SOV-01 Step 2 — Single-actor entrypoint.
        # Captain precondition check (Approach 2A, Apex-confirmed): the
        # Tiers 1+2 GREEN gate remains here, BEFORE the captain call.
        # When preconditions are met, the captain is the sole actor for
        # this frame via run_captain. The legacy_dispatch_fn callable
        # gates _dispatch_action through captain authority — captain
        # calls it internally when Form B has no target or dispatch
        # returns None (Approach 1A: captain_is_active becomes vacuously
        # True; SOV-03 retires). When preconditions are NOT met, substrate
        # dispatch (_dispatch_action) handles the frame unchanged.
        # WO-WEAVE-SWEEP-01: `not _action_decided and` is the only addition
        # to this condition versus pre-WO HEAD — everything after it is
        # byte-identical to the original guard.
        if not _action_decided and state is GameState.NOT_FINISHED and captain_preconditions_met(self.ctx.target_state):
            _legacy_fn = lambda: self._dispatch_action(state, latest_frame, available)
            action = run_captain(
                self.ctx,
                self.ctx.semantic_library,
                legacy_dispatch_fn=_legacy_fn,
            )
            _action_decided = True

        if not _action_decided:
            action = self._dispatch_action(state, latest_frame, available)

        # Push fallback (WO-PUSH-R2) — fires ONLY into Pull silence; seam routes,
        # logic lives in _maybe_push / _push_fallback_action. FIX1 (F6): gated on
        # the live-decide condition — perception bound np_grid, so terminal /
        # GAME_OVER frames (np_grid is None) never reach the Push. `and`
        # short-circuits, so np_grid is never read on the terminal path.
        if state is GameState.NOT_FINISHED and np_grid is not None:
            action = self._maybe_push(action, state, np_grid, available)

        # WO-LGTD-02 Phase 5 (6.1 / GAP-2): Section 3.8 emission validation.
        # Secondary guard against emitting actions not in the platform's
        # declared set. The primary guard is the Affordance Layer — a probe
        # whose required actions are not DECLARED never enters
        # available_probes(), so the captain never selects a tool that
        # would emit an unavailable action. This catches the case where a
        # primary guard miss slips through (bug, race, stale read).
        action = self._validate_emission(action, latest_frame)

        # ---- Observability choke-point (WO-OCD-CHOKE-POINT Step 3) ----
        # Single consolidated write site for ACTION6 emissions. Replaces
        # per-emitter actions_attempted writes (WO-OCD-FLAGS-CLICK) and
        # per-emitter append_action_record calls (WO-OCD-ACTIONLOG) that
        # previously lived in tier4_click.py and action_selector.py.
        # Implementation lives in module-level record_action_at_choke_point
        # so integration tests can invoke the same code path. Run BEFORE
        # step_count++ so global_action_idx matches the historical
        # per-emitter format (pre-increment).
        record_action_at_choke_point(self.ctx, action)

        # ---- Record ----
        self.ctx.last_action_id = action.value if hasattr(action, 'value') else None
        # WO-R1-02c: complete the record — carry the cell we acted on, on the same
        # per-frame channel as last_action_id (set here at emission; read by the
        # next frame's frame_record_log.append as that node's inbound coordinate).
        # Read off the emitted action's own data, so EVERY coordinate emitter is
        # covered at this one consolidated site — not just the push path. None for
        # non-coordinate actions (directionals, RESET).
        self.ctx.last_action_cell = _emitted_cell(action)
        self.ctx.step_count += 1
        directive_focus = (
            self.ctx.routing_directive.focus
            if self.ctx.routing_directive is not None
            else "no directive"
        )
        action.reasoning = {
            "step": self.ctx.step_count,
            "levels": self.ctx.last_level_seen,
            "lives": self.ctx.lives_used,
            "novel": self.ctx.novel_count,
            "repeated": self.ctx.repeated_count,
            "grid_changed": grid_changed,
            "is_novel": is_novel,
            "directive": directive_focus,
        }

        return action

    # ------------------------------------------------------------------
    # Weave coverage sweep (WO-WEAVE-SWEEP-01 Phase 1)
    # ------------------------------------------------------------------

    def _maybe_weave_sweep_action(
        self, state: GameState, grid_changed: bool
    ) -> Optional[GameAction]:
        """Produce this frame's action via the weave coverage sweep, or
        return ``None`` if the sweep is not active this frame (in which case
        the caller falls through to the captain / legacy dispatch —
        exclusivity is the caller's responsibility, per WO-WEAVE-SWEEP-01
        Phase 1 §0.2.6).

        WO-SWEEP-FORK-01 · THE WORLD-TYPE GATE IS NOW A FORK. It read:

            if lib is None or lib.header.world_type != "CLICK":
                return None

        with the stated reason "there is no clicking question to answer in a
        NAV world". **That is correct about the EMITTER and wrong about the
        READ.** ``compute_current_weave_roles`` consults no ``world_type``
        anywhere in its chain — the verdicts are world-agnostic; only the
        action is not. On a NAV world the wall meant the golden read never ran
        at all and the frame fell entirely to legacy dispatch.

        The fork keeps the CLICK path byte-identical and adds a NAV path that
        does the same read, applies the same candidate policy, **emits no
        action, tags no emitter path, and advances no sweep state**, recording
        WHY on the context: the navigation primitive that would drive the ego
        to a selected target is not built. ``strategy/collide_sweep.py`` is
        coverage POLICY only by its own charter and names the missing half in
        its own docstring. **A stated absence in the run, rather than a stale
        premise in a comment.** An unknown world type, or an absent library
        (``world_type`` is unknown before the first sync), returns ``None`` as
        before.

        READ-ONLY BOUNDARY (binding, WO Phase 0 §0.3): calls only
        ``weave.coverage_sweep.compute_current_weave_roles``, which is built
        exclusively from the read-only prefix of the landing chain
        (``ledger_from_capture`` -> ``weave_window``/``re_join`` ->
        ``infer_roles``). Never calls ``self._land_weave_roles()`` or
        ``land_weave_roles(...)`` — see that module's own docstring for why.

        CADENCE (binding, WO Phase 0 §0.2): role verdicts are recomputed at
        most once every ``WEAVE_SWEEP_RECOMPUTE_INTERVAL`` actions
        (fixed-interval — see the Phase 1 WO return for the reasoning versus
        an event-triggered alternative); the cached
        ``self.ctx.weave_sweep_worldlines`` / ``weave_sweep_verdicts`` are
        reused on frames between recomputes. Per-frame contact (selecting
        and emitting a click) is not throttled — only the expensive
        full-log-rescan recompute is.

        Provenance (WO Phase 0 §0.4 adjacent caution): tags
        ``self.ctx.last_emitter_path = "weave_sweep"`` on every action this
        method emits — confirmed (Phase 1 §0.1 premise re-check) NOT one of
        ``cybernetic.push_fallback._SILENCE_LABELS`` (``typed_gap`` /
        ``random_fallback``), so ``_maybe_push`` will not treat a weave-sweep
        frame as Pull-silent and will not override it.
        """
        if state is not GameState.NOT_FINISHED:
            return None
        if self.ctx.weave_sweep_complete:
            return None
        # An absent library reads as an absent world type, which is in neither arm — the
        # two returns the guard used to spell out, folded because this rung owed the
        # ratchet lines and this is an honest place to find them.
        _world = getattr(getattr(self.ctx.semantic_library, "header", None),
                         "world_type", None)
        if _world not in ("CLICK", "NAV"):
            return None

        from virelai_v4.library.region_geometry import representative_coordinate
        from virelai_v4.weave.coverage_sweep import (
            advance_sweep_state,
            nav_drive_step,
            select_weave_sweep_probe,
        )

        # The cadence gate, the outcome attribution, and the CLICK-only rule that governs
        # it all live in `coverage_sweep` — this seam only says which arm it is.
        advance_sweep_state(self.ctx, grid_changed, self.ctx.frame_record_log,
                            emitting=_world == "CLICK")

        # WO-SWEEP-FORK-01 · the NAV arm. Same verdicts, same candidate policy,
        # no action. `select_weave_sweep_probe` is deliberately NOT called: it
        # advances the candidate index and can enter the mechanism-probe
        # detour, and neither may happen on a frame where nothing is emitted.
        # `last_emitter_path` is left alone for the same reason — tagging a
        # path this method did not emit on would make a Pull-silent frame read
        # as a weave-sweep frame to `_maybe_push`.
        # WO-COLLIDE-GOLDEN-01 · the NAV arm walks. `nav_drive_step` returns an ACTION
        # ID, never a `GameAction` — `weave/` stays stdlib-only and this seam owns the
        # platform type. When it returns None the note carries WHY, which the arm still
        # renders on change. **WO-NAV-CLEANUP-01 · this line said `note_nav_sweep` was
        # retained for the frames the drive is not reached at all. There are no such
        # frames and there was no such caller** — this seam calls `nav_drive_step` and
        # nothing else on the NAV arm, and the pair is deleted. The absence is stated by
        # `drive_absence` through the same return, with its cause read off the board.
        if _world != "CLICK":
            _step, _note = nav_drive_step(self.ctx)
            if _note:
                logger.info("[WEAVE-SWEEP] %s", _note)
            if _step is not None:
                self.ctx.last_emitter_path = "weave_collide"
                return GameAction.from_id(_step.action)
            return None

        result = select_weave_sweep_probe(
            self.ctx,
            self.ctx.weave_sweep_worldlines or [],
            self.ctx.weave_sweep_verdicts or {},
            self.ctx.frame_record_log,
        )
        if result is None:
            return None   # terminated this call, or nothing eligible yet

        _wid, wl = result
        region = wl.steps[-1][1]
        row, col = representative_coordinate(set(region.cells))
        action = GameAction.ACTION6
        action.set_data({"x": col, "y": row})
        self.ctx.last_emitter_path = "weave_sweep"
        return action

    # ------------------------------------------------------------------
    # Lifecycle dispatch (WO-OCD-CHOKE-POINT Step 2)
    # ------------------------------------------------------------------

    def _dispatch_action(
        self,
        state: GameState,
        latest_frame: FrameData,
        available: list[int],
    ) -> GameAction:
        """Lifecycle dispatch — convert GameState to a chosen GameAction.

        Extracted from choose_action in WO-OCD-CHOKE-POINT (Step 2) as the
        compensating extraction for the consolidated choke-point write
        added in Step 3. Owns the side effects associated with terminal
        states (death-frame flag, life-counter advance, life reset,
        terminal summaries) and delegates NOT_FINISHED frames to
        select_action with the routing directive.

        The boundary is exact: every branch in the original `if state in
        (NOT_PLAYED, GAME_OVER) / elif WIN / elif NOT_FINISHED / else`
        ladder maps to one branch here. No semantic change.
        """
        if state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            if state is GameState.GAME_OVER:
                self.ctx.is_death_frame = True  # FLAG-017: mark death frame (WO-C5-01)
                # WO-E14 D3: death-confirm re-wire. The confirmer was dead in
                # sync_library (NOT_FINISHED-gated, is_death_frame always False).
                # Here is_death_frame is true. Additive corroboration only — does
                # NOT touch the lives_used/reset_for_new_life/RESET sequence below.
                if self.ctx.semantic_library is not None:
                    confirm_counter_on_death(self.ctx.semantic_library, True)
                self._fire_diagnostic(latest_frame, "GAME_OVER")
                # WO-MINE-03: Harvest for observability (vestigial in current V4 but
                # preserved for future serialization / logging; no behavioral
                # dependency — the harvest is not re-injected because the same
                # VirelaiContext instance is retained across lives).
                _persistent = self.ctx.harvest_persistent_state()
                # Lifecycle counter (V3.5 pattern)
                self.ctx.lives_used += 1
                # WO-R1-01b Part 1 (cadence D): land the weave's role verdicts in
                # Store-A at the END-OF-LIFE boundary, while the life's capture is
                # complete and BEFORE reset_for_new_life(). The library and
                # frame_record_log are PERSIST_LIVES tiers, so the landed belief
                # carries into the next life via Groundhog-Day Mode C — which is
                # what makes this cadence meaningful. O(N) once per life; no
                # hot-path change. Guarded — never perturbs the loop.
                # CADENCE LIVES HERE, IN THE CALLER (note §4): the Step-2
                # incremental engine re-points this at a per-move site without
                # touching land_weave_roles.
                # WO-B2-05 §23 — THE SWALLOW SPEAKS. This catch ate the weave
                # landing, the pristinity check, and LIB-5 SILENTLY for three
                # sealed rungs (WO-B2-04). A guard that never perturbs the loop is
                # right; a guard that never SAYS what it caught is the doctrine's
                # named failure — the honesty layer dying inside a silent except.
                # It still never raises past itself; it now announces.
                try:
                    self._land_weave_roles()
                except Exception as _exc:
                    self._log(f"WEAVE-LAND-ERROR | {_exc!r}", always=True)
                # WO-R1′-01: the artifact — semantic <- ### <- visual objects.
                # A SEPARATE hook from the landing, deliberately: the landing
                # writes belief and windows to the current life; this is a pure
                # read over the whole level's weave and must not inherit the
                # landing's window (or its carried off-by-one, which returns
                # before the landing body runs). Render-only; own gate; guarded.
                try:
                    self._render_lineage()
                except Exception as _exc:               # WO-B2-05 §23 — loud, not silent
                    self._log(f"LINEAGE-ERROR | {_exc!r}", always=True)
                # WO-COMPOUND-ROLE-01: the independent repeated-contact
                # confirmation. A second, separately-sourced fact alongside the
                # landing's correlation-based role — must run before
                # reset_for_new_life() clears the PER_LIFE_SCRATCHPAD fields
                # (weave_sweep_*) the read below does not touch but the same
                # window discipline requires reading while THIS life's capture
                # is still whole. Guarded — never perturbs the loop.
                try:
                    self._record_repeated_contact_confirmation()
                except Exception as _exc:                # WO-B2-05 §23 — loud, not silent
                    self._log(f"REPEATED-CONTACT-ERROR | {_exc!r}", always=True)
                # WO-ROSTER-HOLD-01 · HOLD THE COVERAGE ROSTER'S SIX INPUTS BEFORE THE
                # RESET TAKES THEM. `coverage_roster` runs at `cleanup()`, and the call
                # three lines below empties every `PER_LIFE_SCRATCHPAD` field it reads —
                # so the roster rendered *no queue* about a life it had just watched.
                # **The same pattern, the same tier and the same discipline as
                # `woven_worldlines` at the landing above**: plain assignment, no mutation,
                # no belief-write, no role. This is the only site that clears them, so it
                # is the only site that needs to hold them; the roster prefers the LIVE
                # fields and falls back here, which is what makes a WIN or a life-cap exit
                # render its own life rather than the last one that died.
                try:
                    self.ctx.coverage_hold_cuts = self.ctx.weave_sweep_cuts
                    self.ctx.coverage_hold_worldlines = self.ctx.weave_sweep_worldlines
                    self.ctx.coverage_hold_verdicts = self.ctx.weave_sweep_verdicts
                    self.ctx.coverage_hold_reached = set(self.ctx.collide_drive_reached)
                    self.ctx.coverage_hold_not_reached = set(self.ctx.collide_drive_not_reached)
                    self.ctx.coverage_hold_unreachable = set(self.ctx.collide_drive_unreachable)
                except Exception as _exc:               # WO-B2-05 §23 — loud, not silent
                    self._log(f"COVERAGE-HOLD-ERROR | {_exc!r}", always=True)
                # Reset into new life — clears PER_LIFE_SCRATCHPAD and
                # PERSIST_LEVELS_RESET_LIFE; preserves PERSIST_LIVES_* tiers
                # (library, visited, lifecycle counters, level-scoped memory).
                # prev_grid, frame_delta, and actions_this_life are handled by
                # this call via the _PERSISTENCE_TIERS dict.
                self.ctx.reset_for_new_life()
                self._log(f"Life lost (lives used: {self.ctx.lives_used})", always=True)
                # Terminal summary if operator life cap reached
                max_lives_env = os.environ.get("VIRELAI_MAX_LIVES")
                if max_lives_env is not None and self.ctx.lives_used >= int(max_lives_env):
                    self._fire_terminal_summary(latest_frame, "lives_exhausted")
            return GameAction.RESET

        if state is GameState.WIN:
            self._fire_diagnostic(latest_frame, "WIN")
            self._fire_terminal_summary(latest_frame, "win")
            return GameAction.RESET  # Safety — is_done should catch this

        if state is GameState.NOT_FINISHED:
            # Step 5 — Strategize: directive-driven action selection (WO-02)
            return select_action(
                directive=self.ctx.routing_directive,
                library=self.ctx.semantic_library,
                available_actions=available,
                rng=self._rng,
                probe_history=self.ctx.probe_history,
                context=self.ctx,
            )

        self._log(f"Unknown state: {state}", always=True)
        return GameAction.RESET

    # ------------------------------------------------------------------
    # Perception (WO-03)
    # ------------------------------------------------------------------

    def _perceive(
        self,
        grid: np.ndarray,
        cell_transitions: Mapping[Tuple[int, int], Tuple[int, int]],
        raw_cells: FrozenSet[Tuple[int, int]],
        step: int,
        action_id: int,
    ) -> None:
        """Step 1: Perceive. Compute delta, update cell history, track state.

        Runs on every NOT_FINISHED frame, before action selection.
        Does NOT run on NOT_PLAYED, WIN, or GAME_OVER frames.
        Does NOT consume an action or influence what action is selected.

        CellHistory and StateTracker persist across lives (Groundhog Day).
        prev_grid and frame_delta reset on GAME_OVER (per-life fields).

        cell_transitions: WO-W1b-01 — the frame's one cell-transitions
        catalog, constructed once by the caller (choose_action, before this
        call) from the same two grids (self.ctx.prev_grid, grid) already in
        scope there. Required, not optional: this method has no caller
        besides choose_action's single call site, and no fallback
        construction remains here (that construction has moved to the
        caller — see the caller's own comment for why).

        raw_cells, step, action_id: WO-W1b-03 — RULING_OBSERVERS_INTEGRATOR_v1
        Clause A: the canonical changed-set and the frame's identity facts,
        born at the same birth site as cell_transitions and threaded here
        too. The cell-history-update gate/loop below reads these instead of
        `delta.changed_cells`/`delta.step`/`delta.action_id` — `delta` (this
        method's own compute_frame_delta call, a few lines below) is still
        computed, unchanged, independently: that redundancy is the D-3
        grading instrument (RULING_OBSERVERS_INTEGRATOR_v1 §1, §3;
        PARALLAX FENCE), not a value this method may stop computing.
        Required, not optional — same reasoning as cell_transitions above.
        """
        # Initialize perception on first call (lazy, Groundhog Day safe)
        if self.ctx.cell_history is None:
            self.ctx.cell_history = {}  # Dict[Tuple[int, int], CellHistory]
        if self.ctx.state_tracker is None:
            self.ctx.state_tracker = StateTracker()

        # Compute frame delta against previous grid
        if self.ctx.prev_grid is not None:
            # WO-PHASE4-01 (OTA-02): pass the action that produced this delta.
            # last_action_id is set at the end of the prior choose_action call
            # (see "# ---- Record ----" block) so it is populated whenever
            # prev_grid is non-None. `or 0` is a defensive fallback for the
            # very first delta of a life if the attribute were ever None.
            delta = compute_frame_delta(
                pre_grid=self.ctx.prev_grid,
                post_grid=grid,
                action_id=self.ctx.last_action_id or 0,
                step=self.ctx.step_count,
            )
            self.ctx.frame_delta = delta

            # Feed delta into CellHistory for every changed cell
            # WO-W1b-03: the gate and loop read the canonical changed-set
            # (raw_cells, born at choose_action's birth site from the same
            # two grids `delta` was just computed from — content-identical
            # to delta.changed_cells, proven in this WO's own tests) instead
            # of delta.changed_cells. RULING_OBSERVERS_INTEGRATOR_v1 Clause
            # A: consumers-of-record read the canonical record; `delta`
            # above remains the observer, retained for D-3 grading only —
            # PARALLAX FENCE, unchanged.
            if raw_cells:
                cell_hist: Dict[Tuple[int, int], CellHistory] = self.ctx.cell_history
                # WO-W1b-01: the view is no longer built here. It is the
                # `cell_transitions` parameter passed in by the caller — the
                # SAME object `_sync_library` (89 lines below) threads into
                # `compute_world_delta`. One construction per frame, at the
                # top of choose_action, not one per consumer (WO-W1-02a's own
                # documented trade-off — two constructions of the same pure
                # function per frame — is closed by this WO, not carried
                # forward).
                for cell in raw_cells:
                    key = (cell[0], cell[1])
                    if key not in cell_hist:
                        cell_hist[key] = CellHistory(row=key[0], col=key[1])
                    update_cell_history(
                        cell_hist[key],
                        delta,
                        pre_grid=self.ctx.prev_grid,
                        post_grid=grid,
                        view=cell_transitions,
                        # WO-W1b-03: canonical record, not the observer.
                        step=step,
                        action_id=action_id,
                        raw_cells=raw_cells,
                    )

        # Update StateTracker with current grid.
        # WO-PUSH-P1-R1 (OG-4 retention): feed the triple already in hand so the
        # (from, action) → to edge and the per-state tried-set are retained, not
        # dropped. prev_grid (from-state) and last_action_id (action) are the
        # same values fed to the frame delta above. from_sig uses the tracker's
        # own hash path (key-consistent with `visited`). On a life's first frame
        # prev_grid is None → from_sig is None → retention simply skips.
        _from_sig = (
            self.ctx.state_tracker.signature(self.ctx.prev_grid)
            if self.ctx.prev_grid is not None else None
        )
        self.ctx.state_tracker.record(
            grid,
            self.ctx.step_count,
            action_id=self.ctx.last_action_id,
            from_sig=_from_sig,
            target=self.ctx.last_action_target,   # WO-R4 D1: composite edge on a Push click
        )

        # Store current grid for next frame's delta
        self.ctx.prev_grid = grid.copy()

    # ------------------------------------------------------------------
    # Ego Position Tracking (WO-03 NAV)
    # ------------------------------------------------------------------

    def _update_ego_position(self, library: Optional[object] = None) -> None:
        """Update ego_current_pos based on displacement from frame delta.

        Runs on every NOT_FINISHED frame after _perceive() completes.
        Uses ego_centroid from library header (available after first displacement).
        Updates ego_current_pos when displacement is detected; leaves it unchanged on wall collision.
        Resets to spawn on RESET (handled in choose_action).

        If library is not None and ego_centroid is available, initialize ego_current_pos
        from it (first confirmed displacement). Otherwise, update based on displacement.
        """
        # Skip if no frame delta (first frame)
        if self.ctx.frame_delta is None:
            return

        # Initialize from library ego_centroid if not yet set
        if self.ctx.ego_current_pos is None and library is not None:
            if hasattr(library, 'header') and hasattr(library.header, 'ego_centroid'):
                ego_centroid = library.header.ego_centroid
                if ego_centroid is not None:
                    self.ctx.ego_current_pos = (round(ego_centroid[0]), round(ego_centroid[1]))

        # If still None, nothing to update
        if self.ctx.ego_current_pos is None:
            return

        # Check if displacement occurred this frame (nonzero world_changed)
        # WO-W1b-03 HALT (item 3, this WO's own review): NOT migrated to
        # WorldDelta.world_cells. In the live path (hud_mask never passed to
        # compute_frame_delta here), frame_delta.world_changed == total_changed
        # — ANY changed cell, ego movement included. WorldDelta.world_cells is
        # the ego/hud-EXCLUDED partition (world_cells = raw_cells - ego_cells
        # - hud_cells) — ego displacement's own changed cells land in
        # ego_cells (compute_ego_mask covers exactly the vacated/arrived ego
        # footprint), not world_cells. Substituting world_cells here would
        # make this displacement gate see ~zero on ordinary ego movement — a
        # real regression to ego-position tracking. See this WO's return,
        # HALT section. Left reading frame_delta.world_changed unchanged,
        # pending Alpha Coder's ruling.
        if self.ctx.frame_delta.world_changed > 0 and self.ctx.last_action_id in {1, 2, 3, 4}:
            # Re-read ego_centroid from library to get the latest displacement
            if library is not None and hasattr(library, 'header'):
                ego_centroid = library.header.ego_centroid
                if ego_centroid is not None:
                    # Update position and reset stuck count
                    self.ctx.ego_current_pos = (round(ego_centroid[0]), round(ego_centroid[1]))
                    self.ctx.nav_stuck_count = 0
                    self.ctx.nav_last_nav_action = self.ctx.last_action_id
        elif self.ctx.last_action_id in {1, 2, 3, 4}:
            # Directional action but no displacement (wall or no ego delta) — increment stuck count
            if self.ctx.last_action_id == self.ctx.nav_last_nav_action:
                self.ctx.nav_stuck_count += 1
            else:
                # Different action — reset stuck count
                self.ctx.nav_stuck_count = 1
            self.ctx.nav_last_nav_action = self.ctx.last_action_id


    # ------------------------------------------------------------------
    # NavAtlas substrate update (WO-CAMPAIGN3-PHASE1-04)
    # ------------------------------------------------------------------

    def _record_contact_reactivity(
        self,
        current_grid: np.ndarray,
        prev_grid: Optional[np.ndarray],
    ) -> None:
        """Phase 2 cybernetic loop integration: detect lever via
        pixel-budget excess; record candidate to NavAtlas; transition
        library role to LEVER (or increment orphan counter).

        Thin wrapper around
        ``library.contact_reactivity_integration.maybe_record_contact_reactivity``
        — the V4 testability idiom (per Phase 1 pattern firing #11) keeps the
        gating + V3.5 invocation logic in an arcengine-independent free
        function so the substrate-update logic can be unit-tested without
        constructing a Virelai instance.

        Called from ``choose_action`` after ``_record_nav_move`` and
        before the target/route block. Phase 2 substrate writes are
        field-isolated from Phase 1 substrate writes (per WO-PHASE2-00
        §7.4) — record_move populates walkable/blocked/visited;
        contact_reactivity populates nav_lever_candidates/contacted/mutation
        with library role transition.
        """
        from virelai_v4.library.contact_reactivity_integration import (
            maybe_record_contact_reactivity,
        )
        maybe_record_contact_reactivity(
            context=self.ctx,
            library=self.ctx.semantic_library,
            current_grid=current_grid,
            prev_grid=prev_grid,
        )

    def _record_nav_move(
        self,
        current_grid: np.ndarray,
        prev_grid: Optional[np.ndarray],
    ) -> None:
        """Record the previous action's move into ``nav_atlas`` substrate.

        Thin wrapper around ``library.nav_substrate_update.maybe_record_move``
        — the gating logic + record_move call live in that free function so
        they can be unit-tested without constructing a Virelai instance
        (which requires arcengine; see ``tests/test_choose_action_contracts.py``
        for the V4 precedent on Virelai-class testability).

        Called from ``choose_action`` after ``_update_ego_position`` runs
        and before the target/route block.
        """
        from virelai_v4.library.nav_substrate_update import maybe_record_move
        maybe_record_move(
            nav_atlas=self.ctx.nav_atlas,
            last_action_id=self.ctx.last_action_id,
            prev_ego_pos=self.ctx.prev_ego_pos,
            ego_current_pos=self.ctx.ego_current_pos,
            current_grid=current_grid,
            prev_grid=prev_grid,
        )

    # ------------------------------------------------------------------
    # Library Sync (WO-04 — Step 3)
    # ------------------------------------------------------------------

    def _sync_library(
        self,
        latest_frame: FrameData,
        prev_grid: Optional[np.ndarray] = None,
        cell_transitions: Optional[Mapping[Tuple[int, int], Tuple[int, int]]] = None,
        raw_cells: Optional[FrozenSet[Tuple[int, int]]] = None,
        step: Optional[int] = None,
        action_id: Optional[int] = None,
    ) -> None:
        """Step 3 — Feed perception evidence into the semantic library.

        Initializes the library on first call. Runs sync_library which
        handles spawn population (Mode A), delta updates (Mode B), and
        Groundhog Day restore (Mode C) internally.

        prev_grid: the grid from the frame BEFORE the last action, captured
        before _perceive() overwrites ctx.prev_grid.  Used by the
        displacement-based ego detector (WO-04c).

        cell_transitions: WO-W1b-01 — the same catalog object passed to
        _perceive this frame, threaded down to sync_library ->
        compute_world_delta. Optional (default None), matching prev_grid's
        own existing style on this method; this method's one call site
        (choose_action) always supplies the real object, never None.

        raw_cells: WO-W1b-02 — the same changed-set built beside
        cell_transitions this frame, threaded down to sync_library ->
        compute_world_delta. Optional (default None), same style as
        cell_transitions; this method's one call site always supplies the
        real object, never None.

        step, action_id: WO-W1b-03 — the same frame-identity facts born at
        the birth site, threaded down to sync_library -> compute_world_delta
        alongside raw_cells. Same optional-default style; this method's one
        call site always supplies real values.
        """
        grid = np.array(latest_frame.frame[-1], dtype=np.int32)

        # Initialize library if needed
        if self.ctx.semantic_library is None:
            self.ctx.semantic_library = SemanticLibrary(
                header=LibraryHeader(game_id=latest_frame.game_id),
                objects={},
                sdk_actions={},
                lever_actions={},
                exploration=LibraryExploration(),
            )
            # WO-C5-05: Initialize background_class_votes once per game (not per life).
            # Lives within a game share one accumulator — Groundhog Day persistence is free.
            self.ctx.background_class_votes = {}

        grid_scan, new_hud_mask, lc_only, new_spawn_freqs = sync_library(
            library=self.ctx.semantic_library,
            grid=grid,
            frame_delta=self.ctx.frame_delta,
            state_tracker=self.ctx.state_tracker,
            last_action_id=self.ctx.last_action_id,
            available_actions=list(latest_frame.available_actions),
            game_id=latest_frame.game_id,
            context=self.ctx,
            cell_history=self.ctx.cell_history,
            spawn_grid=self.ctx.spawn_grid,
            prev_grid=prev_grid,                # WO-04c: displacement-based ego detection
            is_death_frame=self.ctx.is_death_frame,  # FLAG-017 (WO-C5-01)
            hud_mask=self.ctx.hud_mask,         # WO-C5-03: current mask (None until COUNTER detected)
            spawn_class_frequencies=self.ctx.spawn_class_frequencies,  # WO-C5-05: Channel 3
            background_class_votes=self.ctx.background_class_votes,    # WO-C5-05: Channel 4
            interior_layers=latest_frame.frame,  # WO_AR D2: animation witness (interior planes)
            cell_transitions=cell_transitions,   # WO-W1b-01: one birthplace
            raw_cells=raw_cells,                 # WO-W1b-02: birth the changed-set
            step=step,                           # WO-W1b-03: record identity
            action_id=action_id,                 # WO-W1b-03: record identity
        )

        # Store GridScan on context if one was computed (spawn frame)
        if grid_scan is not None:
            self.ctx.grid_scan = grid_scan

        # WO-C5-05: Store spawn class frequencies (write-once from Mode A)
        if new_spawn_freqs is not None and self.ctx.spawn_class_frequencies is None:
            self.ctx.spawn_class_frequencies = new_spawn_freqs

        # WO-C5-03: Store newly built HUD mask (write-once — never overwrite existing mask)
        if new_hud_mask is not None and self.ctx.hud_mask is None:
            self.ctx.hud_mask = new_hud_mask
            # WO-CP1-FIX-A: calibrate the novelty instrument the moment the
            # live regions are known — the StateTracker masks counter/HUD
            # pixels before hashing, ending the "every counter tick is a novel
            # state" instrument lie (WO-DIAG-CP1 D-3).
            if self.ctx.state_tracker is not None:
                _arr = getattr(self.ctx, "action_reality_report", None)
                self.ctx.state_tracker.set_live_masks(
                    hud_mask=self.ctx.hud_mask,
                    lc_region=getattr(_arr, "life_counter_region", None),
                )

        # WO-C5-03: Increment LC-only delta counter
        if lc_only:
            self.ctx.lc_only_delta_count += 1

        # Per-action field card — suppressed in quiet mode via _log default
        lib = self.ctx.semantic_library
        at = lib.header.actions_taken
        if at <= 3 or at % 20 == 0:
            self._log("=== FIELD CARD ===\n%s" % render_field_card(
                lib,
                hud_mask=self.ctx.hud_mask,
                lc_only_delta_count=self.ctx.lc_only_delta_count,
                ego_mask=self.ctx.ego_mask,
                current_plan=self.ctx.current_plan,  # WO-CAMPAIGN2-02
                levels_completed=self.ctx.last_level_seen,
                lives_used=self.ctx.lives_used,
            ))

    # ------------------------------------------------------------------
    # End-of-life diagnostic (WO-C3-04)
    # ------------------------------------------------------------------

    def _fire_diagnostic(self, latest_frame: FrameData, state_label: str) -> None:
        """Print the end-of-life diagnostic block.

        Guards against None library / target_state / routing_directive —
        if they are not yet initialised (very early termination), skip.
        Always fires (always=True) — end-of-life blocks are the grading
        artifact, not per-action noise.
        """
        lib = self.ctx.semantic_library
        if lib is None:
            return
        if self.ctx.target_state is None or self.ctx.routing_directive is None:
            return

        # Emit field card at end-of-life with always=True so it shows in quiet mode.
        # This surfaces HUD mask status, COUNTER rate/budget, and tier gaps even
        # when per-action field cards are suppressed by VIRELAI_QUIET=1.
        self._log("=== FIELD CARD (end-of-life) ===\n%s" % render_field_card(
            lib,
            hud_mask=self.ctx.hud_mask,
            lc_only_delta_count=self.ctx.lc_only_delta_count,
            ego_mask=self.ctx.ego_mask,
            current_plan=self.ctx.current_plan,  # WO-CAMPAIGN2-02
            levels_completed=self.ctx.last_level_seen,
            lives_used=self.ctx.lives_used,
        ), always=True)
        _max_lives_env = os.environ.get("VIRELAI_MAX_LIVES")
        _max_lives_display = int(_max_lives_env) if _max_lives_env is not None else None
        report = render_end_of_life_report(
            game_id=self.game_id,
            life=self.ctx.lives_used + 1,          # +1: lives_used increments after this call
            max_lives=_max_lives_display,
            actions_this_life=self.ctx.actions_this_life,
            total_actions=self.ctx.step_count,
            levels_completed=latest_frame.levels_completed,
            state=state_label,
            library=lib,
            field_card_text="",                     # inventory table replaces field card section
            target_state=self.ctx.target_state,
            routing_directive=self.ctx.routing_directive,
        )
        self._log("\n" + report, always=True)
        # WO-OCD-05.2: post-outcome keystone roster dump. At end-of-life the
        # library is settled (every probe outcome has been processed), so this
        # surfaces the Evidence Asymmetry Engine's ACCUMULATED belief per object —
        # unlike the [CHOKE] line, which samples at emission (pre-outcome) and so
        # shows once-swept objects as 0/0/False. Reads existing fields, writes
        # nothing; env-guarded on VIRELAI_DIAG_DUMP (silent in normal runs).
        if os.environ.get("VIRELAI_DIAG_DUMP") and lib is not None:
            for _rid in sorted(lib.objects.keys()):
                _o = lib.objects[_rid]
                self._log(
                    f"[OCD05-ROSTER] rid={_rid} "
                    f"role={getattr(_o.role, 'name', _o.role)} "
                    f"probe_count={_o.probe_count} inert_pc={_o.inert_probe_count} "
                    f"inert_cov={_o.inert_coverage} ever_react={_o.ever_reactive} "
                    f"needs_reinv={_o.needs_reinvestigation}",
                    always=True,
                )
        # WO-EFFECT-01.1: per-LEVER effect observability — surfaces the (already-
        # built) effect classification the pass-3 band populates so the canary can
        # grade it: locality (LOCAL/REMOTE), the causal-edge targets (causes), the
        # measured effects (subject:observation_count), and whether the effect
        # terminal LEVER_EFFECT_CHARACTERIZED has fired. Reads existing fields,
        # writes nothing; env-guarded on VIRELAI_DIAG_DUMP.
        if os.environ.get("VIRELAI_DIAG_DUMP") and lib is not None:
            from virelai_v4.contracts.completion_predicate import CompletionPredicate
            from virelai_v4.library.predicate_evaluators import evaluate_completion
            for _rid in sorted(lib.objects.keys()):
                _o = lib.objects[_rid]
                if getattr(_o.role, "name", _o.role) != "LEVER":
                    continue
                _effs = ",".join(
                    f"{e.subject_region_id}x{e.observation_count}"
                    f":{e.operation_kind}"
                    f":{e.vector if e.vector is not None else e.cell_count_delta}"
                    for e in getattr(_o, "lever_effects", ())
                ) or "-"
                try:
                    _charac = evaluate_completion(
                        CompletionPredicate.LEVER_EFFECT_CHARACTERIZED, {}, lib, slot=_o
                    )
                except Exception:
                    _charac = "?"
                self._log(
                    f"[EFFECT] rid={_rid} "
                    f"locality={getattr(_o, 'lever_locality', None)} "
                    f"mechanism={getattr(_o, 'lever_mechanism', None)} "
                    f"causes={tuple(getattr(_o, 'causes', ()))} "
                    f"disregarded={tuple(getattr(_o, 'disregarded_live_region_ids', ()))} "
                    f"effects={_effs} null={getattr(_o, 'effect_null_presses', 0)} "
                    f"characterized={_charac}",
                    always=True,
                )
        # WO-LOGGING-CARDINALITY: emit the end-of-session TYPED_GAP tally
        # summary (non-quiet) and reset. Replaces the per-action flood with
        # one totals line per (world, probe) tuple.
        from virelai_v4.strategy.typed_gap_action import flush_typed_gap_tally
        flush_typed_gap_tally()

    # ------------------------------------------------------------------
    # Push fallback (WO-PUSH-R2) — the second propulsion
    # ------------------------------------------------------------------

    def _capture_legal_at_first_seen(self, np_grid, available) -> None:
        """Capture the legal EdgeKey set at first-seen (setdefault → never
        overwritten). WO-R4 capture-full: a simple action → ``(id, None)``; a
        complex action expands to ``(id, region_id)`` over the FULL capture-time
        roster — unknowns included, believed-inert pruning deferred to read time;
        a degenerate empty roster → ``(id, None)``. RESET (0) excluded. The
        capture roster is one sync stale (census S1); accepted per ruling 2."""
        tracker = self.ctx.state_tracker
        if tracker is None:
            return
        sig = tracker.signature(np_grid)
        if sig in tracker.legal:
            return
        keys = set()
        for a in (available or []):
            aid = int(getattr(a, "value", a))
            if aid == 0:
                continue
            if GameAction.from_id(aid).is_complex():
                tokens = self._roster_tokens()
                if tokens:
                    keys.update((aid, tok) for tok in tokens)
                else:
                    keys.add((aid, None))            # degenerate: empty roster
            else:
                keys.add((aid, None))
        tracker.legal[sig] = keys

    def _roster_tokens(self):
        """Region-id tokens of the capture-time roster — capture-full (no inert
        prune here). Stale-by-one-sync per census S1; accepted per ruling 2."""
        lib = self.ctx.semantic_library
        if lib is None or not hasattr(lib, "objects"):
            return []
        # WO-R4 gospel (ruling): the Push's edge vocabulary is exactly the library's
        # ASSERTED LEVER set — lever role or sub-role. `candidates_from_roster`
        # (pure, assertion-only) selects them; we return their tokens.
        rows = []
        for region_id, obj in lib.objects.items():
            cells = getattr(obj, "cells", None)
            if not cells:
                continue
            role = getattr(getattr(obj, "role", None), "name", getattr(obj, "role", None))
            sub = str(getattr(obj, "sub_role", "") or "")
            is_lever = (role == "LEVER") or ("lever" in sub.lower())
            rows.append((region_id, cells, is_lever))
        return [tok for tok, _cell in push_candidates_from_roster(rows)]

    def _push_stats(self) -> PushStats:
        """The per-life Push witness, lazily created (R3′ — replaces the four
        ad-hoc _push_* counters with one object)."""
        if not hasattr(self, "_push_stats_obj"):
            self._push_stats_obj = PushStats()
        return self._push_stats_obj

    def _maybe_push(self, action, state, np_grid, available):
        """Route to the Push only into Pull silence on an unwon level. R3′: the
        silence is the take-over label set (typed_gap / random_fallback), read via
        is_pull_silent — the retired-label trigger is re-bound at the seam only.
        Never overrides a tape-driven action, never touches the tier ladder (F4),
        never suppresses the typed-gap diagnostic already emitted upstream (its
        tally write precedes this seam — census 0.4). Returns the Push action when
        it fires, else the captain's action unchanged; a fired-then-empty trigger
        is recorded as a decline (the S5a witness)."""
        if state is not GameState.NOT_FINISHED:
            return action
        # FIX1 belt (secondary to the live-decide gate at the call site): decline
        # if perception did not bind the grid or the legal set is absent.
        if np_grid is None or available is None:
            return action
        pull_silent = push_is_pull_silent(self.ctx.last_emitter_path)
        if not push_should_fire(pull_silent, level_won=False):
            return action
        push_action = self._push_fallback_action(np_grid, available)
        if push_action is None:
            self._push_stats().declines += 1   # fired trigger, no lawful action
            return action
        self.ctx.last_emitter_path = "push_frontier"
        return push_action

    def _push_action_from_id(self, key, np_grid):
        """Build an issuable GameAction for a composite EdgeKey (WO-R4). Simple →
        ``from_id``. Complex → click the target object's representative cell from
        the FRESH roster — the one-field PORT of ``cycle_probe.py:530``
        (``set_data`` x=col, y=row). If the target's object is absent from the
        fresh roster at emission → return None (decline this edge; identity
        discontinuity is not a crash). A degenerate ``(id, None)`` complex → seed
        coordinates. Returns the action, or None to decline."""
        aid, target = key if isinstance(key, tuple) else (key, None)
        action = GameAction.from_id(aid)
        if action.is_complex():
            cell = self._target_cell(target, np_grid)
            if cell is None:
                return None
            row, col = cell
            action.set_data({"x": int(col), "y": int(row)})
            # WO-R4 D1: plumb the emitted target so next frame's record keys the
            # edge on (aid, region_id), not (aid, None) — the monorail's fuel cut.
            self.ctx.last_action_target = target
        return action

    def _target_cell(self, target, np_grid):
        """Representative cell for a complex action's target. ``target is None``
        → seed coordinates (degenerate). Otherwise the fresh-roster object's
        ``representative_cell`` (lex-min), or None if the object has vanished."""
        if target is None:
            import random as _random
            rng = _random.Random(self.ctx.step_count)
            rows, cols = int(np_grid.shape[-2]), int(np_grid.shape[-1])
            return (rng.randint(0, rows - 1), rng.randint(0, cols - 1))
        lib = self.ctx.semantic_library
        if lib is not None and hasattr(lib, "objects"):
            obj = lib.objects.get(target)
            cells = getattr(obj, "cells", None) if obj is not None else None
            if cells:
                return push_representative_cell(cells)
        return None

    def _prune_inert(self, keys):
        """Read-time prune (WO-R4 ruling 3): keep EdgeKeys whose target is not
        believed inert per the FRESH roster. ``target is None`` is always kept; a
        vanished target is pruned (can't click a gone object). Library reads live
        here at the seam — the tracker stays opaque."""
        lib = self.ctx.semantic_library
        out = set()
        for k in keys:
            aid, target = k if isinstance(k, tuple) else (k, None)
            if target is None:
                out.add(k)
                continue
            obj = (lib.objects.get(target)
                   if (lib is not None and hasattr(lib, "objects")) else None)
            if obj is None:
                continue                                 # target gone → prune
            role = getattr(getattr(obj, "role", None), "name", getattr(obj, "role", None))
            belief = getattr(obj, "operational_belief", None)
            if push_is_believed_inert(role, belief):
                continue                                 # believed inert → prune
            out.add(k)
        return out

    def _push_fallback_action(self, np_grid, available):
        """One lawful Push action for a Pull-silent frame, or None (decline).

        Plan-based re-home (WO-PUSH-R3′): the reset-then-observe replay is DATA on
        the tracker, consumed one action per frame — never a per-frame bare RESET.
        Order: (1) active plan → Gate-B verify the prior step, emit the next; (2)
        awaiting-landing → bind the plan to the observed landing, emit its first
        step (never RESET) or decline; (3) no plan → extend the current node if it
        has untried; else re-home with a SINGLE RESET only when the loop invariant
        (can_issue_reset) permits and a frontier exists — else decline.
        ``_last_push_reset`` gates the invariant, so consecutive Push RESETs are
        unreachable. Fully guarded: any error returns None (the captain's action
        stands)."""
        try:
            tracker = self.ctx.state_tracker
            if tracker is None or np_grid is None:
                return None
            sig = tracker.signature(np_grid)
            stats = self._push_stats()

            # (1) Active plan — Gate-B verify the prior step's landing, emit next.
            if tracker.plan_active:
                if not tracker.verify_step(sig):
                    return None                          # mismatch → aborted+alarmed → decline
                step = tracker.next_plan_step()
                if step is not None:
                    self._last_push_reset = False
                    stats.fires += 1
                    return self._push_action_from_id(step[0], np_grid)
                # plan complete → fall through to extend the arrived node

            # (2) Awaiting landing after the single RESET — bind the plan.
            if tracker.awaiting_landing:
                if tracker.bind_plan(sig):
                    step = tracker.next_plan_step()
                    self._last_push_reset = False
                    stats.fires += 1
                    stats.rehomes += 1                   # a bound plan = one re-home (plans, not resets)
                    return self._push_action_from_id(step[0], np_grid)
                return None                              # no path → decline (awaiting cleared)

            # (3) No plan — extend the current node if it has an actionable untried
            # candidate. WO-R4: read-time prune inert targets against the FRESH
            # roster (ruling 3); pick the deterministic-min EdgeKey; skip any whose
            # target has vanished (emit returns None).
            untried = tracker.untried(sig)
            if untried:
                for key in tracker.order_untried(self._prune_inert(untried)):
                    action = self._push_action_from_id(key, np_grid)
                    if action is not None:
                        self._last_push_reset = False
                        stats.fires += 1
                        stats.extensions += 1
                        if key in tracker.tried.get(sig, set()):
                            stats.repeat_visit_violations += 1   # never, by construction
                        return action
                # all untried inert-pruned or target-gone → fall through to re-home/decline

            # Current exhausted: re-home with ONE RESET only if the invariant
            # permits and a frontier exists; else decline (loop-free).
            if push_can_issue_reset(getattr(self, "_last_push_reset", False),
                                    tracker.plan_active, tracker.awaiting_landing) \
                    and tracker.open_set():
                tracker.begin_rehome()
                self._last_push_reset = True
                stats.fires += 1
                return GameAction.RESET                  # the ONE bounded re-home RESET

            # WO-R4 D4: exhaustion verdict — the asserted-lever edge space is empty
            # across all known states and the level is unwon. Render ONCE; a
            # recorded observation only (no belief write; single-writer spine).
            if not tracker.open_set() and not getattr(self, "_push_verdict_rendered", False):
                line = push_render_verdict(True, False)
                if line:
                    self._log(line, always=True)
                    self._push_verdict_rendered = True
            return None
        except Exception:
            return None

    def _render_push_stats(self) -> str:
        """One terminal-readable line of Push activity for the canary (D4).
        R3′: delegates to the pure render over the PushStats object; open_set_size
        is populated at render from the live tracker."""
        stats = self._push_stats()
        tracker = self.ctx.state_tracker
        stats.open_set_size = len(tracker.open_set()) if tracker is not None else 0
        return render_push_stats(stats)

    def _fire_terminal_summary(self, latest_frame: FrameData, cause: str) -> None:
        """Print the V3.5-style terminal summary at game end."""
        won = latest_frame.state is GameState.WIN
        summary = render_terminal_summary(
            game_id=self.game_id,
            terminal_cause=cause,
            levels_completed=latest_frame.levels_completed,
            total_actions=self.ctx.step_count,
            won=won,
        )
        self._log("\n" + summary, always=True)
        self._log(self._render_push_stats(), always=True)   # WO-PUSH-R2 D4

    def cleanup(self, scorecard=None):
        """WO-PUSH-R3′ D4 (terminal rider): render PUSH_STATS on EVERY teardown,
        including the no-frame-terminal exit (``ctx.env_terminated``) where
        ``_fire_terminal_summary`` is never reached — so a platform-refusal death
        can no longer hide the counters. Solver-side only; the framework's
        ``Agent.cleanup`` runs after the loop regardless of exit reason. Guarded —
        never perturbs teardown."""
        try:
            self._log(self._render_push_stats(), always=True)
        except Exception:
            pass
        # WO_INDUCED_MAP_LIVE_RENDER_HOOK: opt-in, run-end only. Render the
        # two-grain induced map from the faithful live capture log and persist a
        # re-renderable artifact. Guarded — never perturbs teardown.
        try:
            self._render_induced_map()
        except Exception:
            pass
        # WO_FRONTIER_LIVE_HOOK: opt-in, run-end only. Print the frontier read
        # (OPEN / SEALED-confirmed / SEALED-provisional + debt) over the live map,
        # tagged against the live library's beliefs. Guarded — never perturbs teardown.
        try:
            self._render_frontier_map()
        except Exception:
            pass
        # WO_WORLD_GRAIN_IDENTITY: opt-in, run-end only. Print the raw→world node
        # collapse, masking instrument cells by the live classifier's ctx.hud_mask.
        # Guarded — never perturbs teardown.
        try:
            self._render_world_grain()
        except Exception:
            pass
        # WO_CLAIM_DECOMPOSER: opt-in, run-end only. Emit the human-gradable audit
        # sheet (fork claims + contact sheets, mask overlaid, grade columns empty).
        # Guarded — never perturbs teardown.
        try:
            self._render_claim_audit()
        except Exception:
            pass
        # WO-R0-01b (W13): opt-in, run-end only. Self-grade at the ordinary
        # teardown — FIDELITY roster (no key) / CORRECTNESS mappings (key present).
        # Guarded — never perturbs teardown.
        try:
            self._render_foundation_grade()
        except Exception:
            pass
        # WO-B3-R1a: opt-in (VIRELAI_INTEGRATION_ROSTER), run-end only. Render the
        # integration roster — Lists 1 & 2 (every visual object; each ### with its
        # members) + X→Y — from the retained woven worldline set. Pure read; lands
        # no role, writes no belief. Guarded — never perturbs teardown.
        try:
            self._render_integration_roster()
        except Exception:
            pass
        super().cleanup(scorecard)

    def _render_induced_map(self) -> None:
        """WO_INDUCED_MAP_LIVE_RENDER_HOOK — opt-in (``VIRELAI_RENDER_MAP``),
        run-end only. Renders the two-grain induced map from the faithful live
        ``ctx.frame_record_log`` (real ``(action_id, target)`` labels + ``edge=None``
        roots — unlike the action-blind ``.recording.jsonl``) to stdout, and
        persists the raw records to ``recordings/<guid>.inducedmap.json`` for
        offline re-render through the same ``render_capture_log`` core (never the
        broken ``log_io``).

        Pure read over ``ctx.frame_record_log``: writes no belief, mutates no log,
        touches no ``capture/``. Off the hot path — ``choose_action`` never reaches
        here. Imports are deferred so ``virelai``'s import surface is unchanged when
        the flag is off. Idempotent: ``cleanup`` can fire more than once per run
        (e.g. terminal summary + framework teardown), so the render latches after
        its first firing and every later call is a no-op — the map prints once."""
        if getattr(self, "_induced_map_rendered", False):
            return
        if not os.environ.get("VIRELAI_RENDER_MAP"):
            return
        log = getattr(self.ctx, "frame_record_log", None)
        if log is None or len(log) == 0:
            return

        import json
        from dataclasses import asdict

        from virelai_v4.weave.render_from_recording import render_capture_log

        print(render_capture_log(log))

        records = log.records
        last = records[-1]
        guid = getattr(last, "guid", None) or getattr(last, "game_id", None) or "run"
        out_dir = "recordings"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{guid}.inducedmap.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump({"records": [asdict(r) for r in records]}, fh)
        print(f"[induced-map] {len(records)} records -> {out_path}")
        self._induced_map_rendered = True

    def _render_frontier_map(self) -> None:
        """WO_FRONTIER_LIVE_HOOK / WO_FRONTIER_OVER_WORLD_MAP — opt-in
        (``VIRELAI_RENDER_FRONTIER``), run-end only. Wires the LIVE semantic library
        into the belief-injected frontier labeler and prints the frontier read
        (OPEN / SEALED-confirmed / SEALED-provisional + debt) over BOTH grains.

        Pure read over ``ctx.frame_record_log`` + ``ctx.semantic_library``: writes
        no belief, mutates nothing. Off the hot path; idempotent (latches after the
        first firing). Imports deferred so the flag-off import surface is unchanged.
        The library may be absent (``None``) — then every action reads as no-belief
        (frontier OPEN), which is the honest early-run state, not an error."""
        if getattr(self, "_frontier_rendered", False):
            return
        if not os.environ.get("VIRELAI_RENDER_FRONTIER"):
            return
        log = getattr(self.ctx, "frame_record_log", None)
        if log is None or len(log) == 0:
            return

        from virelai_v4.weave.frontier_tag import render_frontier
        from virelai_v4.weave.induced_map import build_induced_map

        lib = getattr(self.ctx, "semantic_library", None)

        def belief_of(action_id):
            # Reads SDKAction.operational_belief.value from the LIVE library, or
            # None when the library / SDKAction is absent (→ unpredicted frontier).
            if lib is None:
                return None
            sdk = getattr(lib, "sdk_actions", {}).get(action_id)
            if sdk is None:
                return None
            return getattr(getattr(sdk, "operational_belief", None), "value", None)

        from virelai_v4.weave.world_grain import build_world_map

        # WO_FRONTIER_OVER_WORLD_MAP: read the frontier over BOTH grains. The raw
        # read is known-degenerate on HUD worlds (each fuel variant is a seen-once
        # node with untried keys → ~all OPEN); the world read computes over
        # re-converged rooms, where loop closure unifies action sets and real
        # SEALED/provisional structure appears. Both are printed and labeled so the
        # world read is never mistaken for the raw one. (Ruling gate B2: raw kept,
        # not silently dropped — CE may trim to world-only.)
        mask = getattr(self.ctx, "hud_mask", None)
        if mask is not None:
            arr = np.asarray(mask, dtype=bool)
            hud_cells = frozenset((int(r), int(c)) for r, c in np.argwhere(arr))
        else:
            hud_cells = frozenset()

        raw_map = build_induced_map(log.records)
        world_map = build_world_map(log.records, hud_cells)
        print(f"[frontier · RAW map · {len(raw_map.nodes)} full-grid nodes]")
        print(render_frontier(raw_map, belief_of))
        print(f"[frontier · WORLD map · {len(world_map.nodes)} re-converged nodes]")
        print(render_frontier(world_map, belief_of))
        self._frontier_rendered = True

    def _render_world_grain(self) -> None:
        """WO_WORLD_GRAIN_IDENTITY — opt-in (``VIRELAI_RENDER_FRONTIER``), run-end
        only. Reads the classifier's accumulated HUD mask (``ctx.hud_mask``, a numpy
        bool array; ``None`` until COUNTER is first detected), converts it to a cell
        set, and prints the raw→world node collapse — the HUD-inflated map collapsing
        toward the true room count as fuel levels unify.

        Pure read; the sealed full-grid identity is untouched (this is a second
        grain). Idempotent; off the hot path; imports deferred. An absent/None mask
        yields an empty mask → world grain equals raw grain (honest, not an error)."""
        if getattr(self, "_world_grain_rendered", False):
            return
        if not os.environ.get("VIRELAI_RENDER_FRONTIER"):
            return
        log = getattr(self.ctx, "frame_record_log", None)
        if log is None or len(log) == 0:
            return

        from virelai_v4.weave.world_grain import render_world_grain

        mask = getattr(self.ctx, "hud_mask", None)
        if mask is not None:
            arr = np.asarray(mask, dtype=bool)
            hud_cells = frozenset((int(r), int(c)) for r, c in np.argwhere(arr))
        else:
            hud_cells = frozenset()

        print(render_world_grain(log.records, hud_cells))
        self._world_grain_rendered = True

    def _render_claim_audit(self) -> None:
        """WO_CLAIM_DECOMPOSER — opt-in (``VIRELAI_RENDER_AUDIT``), run-end only.
        Emits the human-gradable audit sheet: fork claims (transition claims) and
        contact sheets (identity claims), with the recorded HUD mask overlaid and
        every FIDELITY/CORRECTNESS column empty. The code surfaces claims; the
        chamber grades them. Pure read; idempotent; off the hot path; imports
        deferred. Mask access inlined (no self-method call → safe as an unbound
        call in tests)."""
        if getattr(self, "_claim_audit_rendered", False):
            return
        if not os.environ.get("VIRELAI_RENDER_AUDIT"):
            return
        log = getattr(self.ctx, "frame_record_log", None)
        if log is None or len(log) == 0:
            return

        from virelai_v4.weave.claim_decomposer import render_audit_sheet
        from virelai_v4.weave.induced_map import build_induced_map
        from virelai_v4.weave.world_grain import build_world_map

        mask = getattr(self.ctx, "hud_mask", None)
        if mask is not None:
            arr = np.asarray(mask, dtype=bool)
            hud_cells = frozenset((int(r), int(c)) for r, c in np.argwhere(arr))
        else:
            hud_cells = frozenset()

        records = log.records
        raw_map = build_induced_map(records)
        world_map = build_world_map(records, hud_cells)
        print(render_audit_sheet(raw_map, world_map, records, hud_cells))
        self._claim_audit_rendered = True

    def _render_lineage(self) -> None:
        """WO-R1′-01 — THE ARTIFACT: ``semantic <- ### <- visual objects``.

        Opt-in (``VIRELAI_LINEAGE``), run-end. The keyless page the Director
        grades: the compression trail on one page, traceable to pixels, with every
        evidence line gated on footprint-invariance so a mover's misattributed
        evidence is marked rather than presented as fact.

        Deliberately its OWN hook, not nested in ``_land_weave_roles``: the
        landing writes belief and windows to the current life; this is a pure read
        over the WHOLE level's weave (more informative — every ### the level
        produced), and it must not inherit the landing's window or its carried
        off-by-one. Writes no belief. Imports deferred."""
        if not os.environ.get("VIRELAI_LINEAGE"):
            return
        log = getattr(self.ctx, "frame_record_log", None)
        lib = getattr(self.ctx, "semantic_library", None)
        if log is None or len(log) == 0 or lib is None:
            print("########## LINEAGE — no capture or no library, nothing to render "
                  "##########")
            return

        from virelai_v4.capture.ledger_build import ledger_from_capture
        from virelai_v4.diagnostics.lineage import render_lineage
        from virelai_v4.weave.rejoin import re_join
        from virelai_v4.weave.worldline import weave_window
        from virelai_v4.weave.worldline_binding import bind_worldlines_to_slots

        cuts = ledger_from_capture(log)
        worldlines = re_join(weave_window(cuts), cuts=cuts)
        slot_fps = {(o.class_id, o.cells): rid for rid, o in lib.objects.items()}
        report = bind_worldlines_to_slots(worldlines, slot_fps)
        print(render_lineage(lib, worldlines, report.bindings))
        print(f"[lineage] bind-rate {report.bound}/{report.total} worldlines bound "
              f"to a spawn slot ({report.unbound} unbound — never a spawn object; "
              f"honest)")

    def _record_repeated_contact_confirmation(self) -> None:
        """WO-COMPOUND-ROLE-01 — the independent repeated-contact confirmation.

        FOUNDATIONAL_ARCHETYPES_v2 §3: STATIC (what an object's own pixels do)
        and LEVER (what clicking it causes elsewhere) are true answers to two
        different questions, not competing answers to one. ``infer_roles``
        already answers the correlation question inside ``_land_weave_roles``;
        this hook answers a second, independently-sourced question — how many
        times, within THIS life, was this worldline the RESOLVED target of a
        real recorded action (``weave.action_roster.acted_on``, the same
        primitive ``weave/acted_on_render.py``'s render already calls) — and
        stores the confirmed set for the teardown roster to display alongside
        whatever role ``infer_roles`` separately assigned. Decides nothing
        (RULING_OBSERVERS_INTEGRATOR_v1 — the integrator's role verdict stays
        the sole decider); lands no belief; writes no ``RoleVerdict``.

        Deliberately its OWN hook, not folded into ``_land_weave_roles``:
        mirrors ``_render_lineage``'s independent-re-derivation pattern —
        its own read of the log, its own windowing via
        ``_current_life_start``, imports deferred so the import surface is
        unchanged when the weave is absent. Pure, additive, read-only."""
        log = getattr(self.ctx, "frame_record_log", None)
        if log is None or len(log) == 0:
            return

        from virelai_v4.capture.ledger_build import (
            ledger_from_capture,
            load_node_actions_from_log,
        )
        from virelai_v4.weave.rejoin import re_join
        from virelai_v4.weave.repeated_contact import confirmed_by_repeated_contact
        from virelai_v4.weave.worldline import weave_window

        cuts = ledger_from_capture(log)
        node_actions = load_node_actions_from_log(log)
        # Same windowing as _land_weave_roles: THIS life's cuts only, node_actions
        # stays full-length and absolutely indexed (see _land_weave_roles's own
        # note — slicing the action array would shift it by `lo` and reintroduce
        # exactly the index-space misalignment that WO exists to remove).
        lo = self._current_life_start(cuts)
        cuts = [c for c in cuts if c.node_index >= lo]
        if not cuts:
            return
        worldlines = re_join(weave_window(cuts), cuts=cuts)
        self.ctx.woven_repeated_contact = confirmed_by_repeated_contact(
            cuts, worldlines, node_actions
        )

    @staticmethod
    def _current_life_start(cuts) -> int:
        """WO-R1-02c C4 — the node_index the current life begins at.

        The log accumulates across lives within a level (tier
        PERSIST_LIVES_RESET_LEVEL). A life boundary is a record that
        ``full_reset``s or reads ``GAME_OVER`` — the same predicate the weave's
        own ``action_roster.is_boundary_pre`` uses. The current life starts at the
        node AFTER the last such boundary; with no boundary (life 1) it starts at
        the log's first node.

        WO-B2-05 — THE OFF-BY-ONE, PAID. The landing runs AT the boundary: on the
        GAME_OVER frame, that terminal record is the LAST cut (the capture append
        runs on every frame, virelai.py:320). The old scan iterated ALL cuts and
        set ``start = terminal.node_index + 1`` — one past the end — so the window
        emptied and ``_land_weave_roles`` silently returned before landing, EVERY
        life. Zero WEAVE-LAND across four canaries against nonzero "Life lost"
        proved it (WO-B2-04). The current life's death is NOT a boundary that
        starts a NEW life; exclude the terminal cut from the scan. (Respawn frames
        carry ``full_reset=False`` — verified on a real multi-life recording,
        0 of 10358 framed nodes — so the spawn is never a boundary and stays
        in-window: the weave keeps its
        ``first_region``. Excluding the last cut is safe at any cadence: a
        non-terminal last cut is not a boundary anyway.)

        Pure read over the cuts. Returns an absolute node_index.
        """
        start = cuts[0].node_index if cuts else 0
        for c in cuts[:-1]:   # exclude this life's own terminal — it starts no new life
            if bool(getattr(c, "full_reset", False)) or getattr(c, "state", "") == "GAME_OVER":
                start = c.node_index + 1
        return start

    def _land_weave_roles(self) -> None:
        """WO-R1-01b Part 1 (W13/BR) — the accumulator confluence, at cadence D.

        Stands the weave up at the END-OF-LIFE boundary and lands its role
        verdicts in Store-A through ``accumulate_role_evidence`` (one witness, one
        writer — the accumulator owns the axis write; this method performs no
        field-write). Runs ONCE PER LIFE: O(N), no hot-path change, no per-sync
        re-weave.

        THIS METHOD IS THE CADENCE (note §4). ``land_weave_roles`` is pure and
        cadence-agnostic; Step 2's incremental every-move engine replaces THIS
        caller — computing verdicts per-move — without touching the landing.
        End-of-loop is not load-bearing anywhere below.

        Assembly is the proven live pattern (``render_stages.py:346-349``):
        ``ledger_from_capture`` → ``re_join(weave_window(...))`` →
        ``load_node_actions_from_sidecar`` (missing sidecar → all-None actions →
        the weave honestly yields no verdicts → nothing lands). Imports deferred
        so the import surface is unchanged when the weave is absent."""
        log = getattr(self.ctx, "frame_record_log", None)
        lib = getattr(self.ctx, "semantic_library", None)
        if log is None or len(log) == 0 or lib is None:
            return

        from virelai_v4.capture.ledger_build import (
            ledger_from_capture,
            load_node_actions_from_log,
        )
        from virelai_v4.library.weave_role_landing import land_weave_roles
        from virelai_v4.weave.rejoin import re_join
        from virelai_v4.weave.role_read import infer_roles
        from virelai_v4.weave.worldline import weave_window

        # WO-R1-02c C2: the intake reads the LOG, not the click-only sidecar —
        # dense over every action type, aligned by construction (entry t IS node t).
        cuts = ledger_from_capture(log)
        node_actions = load_node_actions_from_log(log)

        # WO-R1-02c C4 (idempotency): land only THIS life's window. The log resets
        # at LEVEL (tier) and accumulates across lives within it, so without this
        # each life would re-weave and re-land every prior life — and
        # accumulate_role_evidence is pure addition (no dedupe), so life 2 would
        # double life 1's contribution. Windowing makes the lives disjoint, so the
        # landing is idempotent BY CONSTRUCTION rather than by bookkeeping. The
        # window is the caller's job (note §4) — the landing stays cadence-agnostic.
        # NOTE: node_actions stays FULL-LENGTH and absolutely indexed. The weave
        # indexes it by absolute node_index (role_read.py:59,71; acted_on), so
        # slicing it alongside cuts would shift it by `lo` — reintroducing exactly
        # the index-space misalignment this WO exists to remove. Slice the cuts;
        # never the action array.
        lo = self._current_life_start(cuts)
        cuts = [c for c in cuts if c.node_index >= lo]
        if not cuts:
            # WO-B2-05 §23 — loud, not silent. Post-fix this is nearly
            # unreachable (the off-by-one that emptied the window is paid); it
            # remains as defense, and if it ever fires it must SAY so — the empty
            # window is what voided every live landing before B2-05.
            self._log(
                f"WEAVE-LAND | life={self.ctx.lives_used} EMPTY-WINDOW "
                f"(no cuts at/after node {lo}) — nothing landed",
                always=True,
            )
            return

        # WO-A3-01 — THE LIVE PRISTINITY PROOF. grade_pristine certifies the
        # disjoint ∧ covering invariant provenance.py depends on (its comment
        # names grade_pristine but nothing enforced it — the invariant was
        # assumed on the live path, never checked). Run it on THIS life's window,
        # the same `cuts` the landing consumes. On failure: log loudly and store
        # the verdict; NEVER raise — this runs inside the guarded try/except at
        # the GAME_OVER boundary (virelai.py caller), and a teardown must not die
        # on a grading failure. Cost (a second reconstruct pass, once per life,
        # cold path) is accepted by ruling. The verdict is stored for the future
        # RND-2 friction to stamp; it is not rendered here.
        try:
            from virelai_v4.capture.ledger import grade_pristine, format_pristine
            _verdict = grade_pristine(cuts, log)
            self.ctx.last_pristine_verdict = _verdict
            if _verdict.first_fail is not None:
                self._log("PRISTINE-FAIL | " + format_pristine(_verdict), always=True)
            else:
                self._log("PRISTINE-OK | " + format_pristine(_verdict), always=True)
        except Exception as _exc:
            self._log(f"PRISTINE-ERROR | {_exc!r}", always=True)

        worldlines = re_join(weave_window(cuts), cuts=cuts)
        # WO-B3-R1a — retain the woven worldline set for the teardown integration
        # roster (Lists 1 & 2). Diagnostic hold on ctx (PERSIST_LIVES_RESET_LEVEL,
        # the same tier as frame_record_log it derives from); read by
        # _render_integration_roster at cleanup. Plain assignment — no mutation of
        # the worldlines, no belief-write, no role. It cannot raise; it rides
        # inside the landing's own guarded try/except at the GAME_OVER call site.
        self.ctx.woven_worldlines = worldlines
        verdicts = infer_roles(worldlines, cuts, node_actions)
        # WO-B3-R1b — retain the weave verdicts for the roster's LIST 3 (role per
        # ###). Same display discipline as woven_worldlines: plain assignment, no
        # belief-write, lands no role (the role does not yet reach the belief ### —
        # the belief-rebind is halted architecturally; see the R1b build return).
        self.ctx.woven_role_verdicts = verdicts

        # The spawn-partition slot fingerprints the R1-01a binding joins against.
        slot_fps = {(o.class_id, o.cells): rid for rid, o in lib.objects.items()}

        # WO-R1-01b Part 3: the weave↔A divergence map — R1's pacing instrument.
        # Rendered from the SAME weave read, BEFORE the landing mutates the axes,
        # so the map compares the weave against Store-A's pre-landing belief (the
        # honest comparison; landing first would grade the weave against itself).
        # Env-gated render; pure read, never perturbs the loop.
        if os.environ.get("VIRELAI_WEAVE_DIVERGENCE"):
            try:
                from virelai_v4.diagnostics.store_a_readout import (
                    render_weave_a_divergence,
                )
                from virelai_v4.library.weave_role_landing import (
                    weave_bind_rate,
                    weave_region_verdicts,
                    weave_roles_by_region,
                )

                print(render_weave_a_divergence(
                    lib,
                    weave_roles_by_region(verdicts, worldlines, slot_fps),
                    bind_rate=weave_bind_rate(worldlines, slot_fps),
                    region_verdicts=weave_region_verdicts(
                        verdicts, worldlines, slot_fps),
                ))
            except Exception:
                pass

        report = land_weave_roles(verdicts, worldlines, slot_fps, lib)
        self._log(
            f"WEAVE-LAND | life={self.ctx.lives_used} verdicts={report.total} "
            f"landed={report.landed} unbound={report.skipped_unbound} "
            f"skipped_role={report.skipped_role} "
            f"skipped_conf={report.skipped_confidence}",
            always=True,
        )

        # WO-B3-01 STAGE A · the unbound diagnostic (loud, always, pure read).
        # Measures WHY the spawn-geometry bind left verdicts unbound — MISMATCH
        # (same-class slot exists, cells drifted: a worldline-identity bind WOULD
        # recover it) vs BIRTH (no same-class slot: an honest mid-run birth). That
        # split is the number that grades the Stage-B rebind. No belief write, no
        # bind-logic change — reuses the LIB-5 keyspace classifier. On failure it
        # SAYS so (§23) and moves on; never perturbs the loop.
        if report.skipped_unbound:
            try:
                from virelai_v4.diagnostics.store_a_readout import (
                    unbound_reason_line,
                )
                self._log(
                    unbound_reason_line(
                        worldlines, slot_fps, self.ctx.lives_used),
                    always=True,
                )
            except Exception as _exc:
                self._log(f"WEAVE-LAND-UNBOUND-ERROR | {_exc!r}", always=True)

        # WO-B2-01 MOVE 1 · LIB-5 — the keyspace divergence map, the re-plumb's
        # pacing instrument. Rendered from the SAME join already computed above:
        # worldline first_region fingerprints vs the roster's slot_fps. It exists
        # BEFORE the key moves so Moves 2/3 are measured against its emptiness.
        # EMPTY == FINGERPRINT-MISMATCH empty (the keyspace-integrity invariant).
        # Gate: VIRELAI_STORE_DIVERGENCE_DUMP (the real name, WO-B2-00 §3). Pure
        # read, guarded — never perturbs the loop.
        if os.environ.get("VIRELAI_STORE_DIVERGENCE_DUMP", "0") == "1":
            try:
                from virelai_v4.diagnostics.store_a_readout import (
                    render_keyspace_divergence,
                )
                from virelai_v4.weave.worldline_binding import (
                    bind_worldlines_to_slots,
                )
                _wl_fps = {
                    w.id: (w.first_region.class_id, w.first_region.cells)
                    for w in worldlines
                }
                _bindings = bind_worldlines_to_slots(worldlines, slot_fps).bindings
                print(render_keyspace_divergence(_wl_fps, slot_fps, _bindings))
            except Exception:
                pass

    def _render_foundation_grade(self) -> None:
        """WO-R0-01b (W13) — opt-in (``VIRELAI_GRADE``), run-end only. Self-grade
        at the ordinary ``Virelai.cleanup`` teardown (not only under
        ``render_stages``). Two legs, keyed by whether a foundation key is
        supplied: FIDELITY (no key) emits the keyless belief-roster
        (OBJECT LIST / OBJECT ROSTER over ``d.objects``) — a coherence self-check
        that runs on every world, no oracle; CORRECTNESS (``VIRELAI_GRADE_KEY``
        → a foundation key) emits the ``render_foundation_grade`` mappings/summary
        block graded against the key. Pure read off ``self.ctx``: writes no
        belief, mutates nothing; ``choose_action`` never reaches here. Imports
        deferred so the flag-off import surface is unchanged. Idempotent — latches
        after the first firing (``cleanup`` can fire more than once per run)."""
        if getattr(self, "_foundation_grade_rendered", False):
            return
        if not os.environ.get("VIRELAI_GRADE"):
            return

        from virelai_v4.diagnostics.dossier import (
            _object_list_block,
            _object_roster_block,
            build_dossier,
            load_axiom_key,
        )
        from virelai_v4.diagnostics.foundation_grade import (
            is_foundation_key,
            render_foundation_grade,
        )

        d = build_dossier(self.ctx)

        fkey = None
        key_path = os.environ.get("VIRELAI_GRADE_KEY")
        if key_path:
            loaded = load_axiom_key(key_path)
            fkey = loaded if is_foundation_key(loaded) else None

        if fkey is not None:
            lines = render_foundation_grade(d.objects, fkey)          # CORRECTNESS
        else:
            lines = _object_list_block(d) + _object_roster_block(d)   # FIDELITY

        print("\n".join(lines))
        self._foundation_grade_rendered = True

    def _store_a_role_verdicts(self, worldlines) -> Optional[Dict[int, Any]]:
        """WO-DISPLAY-SOURCE-01 — the roster's role label, read from the belief
        that already accumulates instead of re-derived from the one that
        doesn't.

        `WO_GROUNDHOG_DAY_01_AUDIT_RETURN` confirmed two things: (1)
        `ctx.woven_role_verdicts` (`_land_weave_roles`, ``virelai.py:2059-2065``)
        is plain-reassigned from a life-windowed weave recompute every life —
        it holds nothing from any prior life, ever; (2) Store-A's BBA log-odds
        axes, written through `accumulate_role_evidence`, already accumulate
        correctly across lives (`###004`'s `lever_log_score` climbed
        `0.4055 -> 0.8109 -> 1.2164 -> 1.6219 -> 2.0273` over 5 real lives,
        one clean additive step per life). This reads THAT belief instead.

        Thin wrapper — all logic lives in `library.store_a_role_read.
        store_a_role_verdicts`, a pure function with no `Virelai`/`arcengine`
        dependency (testable standalone, matching the established
        `weave/repeated_contact.py` pattern). NOT a second accumulator: that
        function calls `_land_weave_roles` / `land_weave_roles` /
        `accumulate_role_evidence` / the windowing logic not at all."""
        lib = getattr(self.ctx, "semantic_library", None)
        if lib is None:
            return None
        from virelai_v4.library.store_a_role_read import store_a_role_verdicts
        return store_a_role_verdicts(worldlines, lib)

    def _render_integration_roster(self) -> None:
        """WO-B3-R1a — opt-in (``VIRELAI_INTEGRATION_ROSTER``), run-end only.
        Render the integration roster (Lists 1 & 2 + X→Y) from
        ``ctx.woven_worldlines`` — the weave window retained at the landing. Pure
        read off ``self.ctx``: writes no belief, mutates nothing, lands no role
        (roles are R1b). Deferred import so the flag-off import surface is
        unchanged. Idempotent — latches after the first firing (``cleanup`` can
        fire more than once per run)."""
        if getattr(self, "_integration_roster_rendered", False):
            return
        if not os.environ.get("VIRELAI_INTEGRATION_ROSTER"):
            return
        from virelai_v4.diagnostics.integration_roster import (
            render_delivery_roster,
            render_integration_roster,
        )
        # WO-ANIMATION-01 · the delivery roster rides the same gate and the same teardown
        # as the integration roster. **The caller computes and the renderer formats** —
        # `integration_roster` is fenced to stdlib plus `capture.clay` so it runs where
        # scipy is absent, and the producer imports scipy through `grid_scan`.
        from virelai_v4.capture.ledger_build import deliveries_of
        _dlog = getattr(self.ctx, "frame_record_log", None)
        print(render_delivery_roster(deliveries_of(_dlog), len(_dlog) if _dlog else 0))
        worldlines = getattr(self.ctx, "woven_worldlines", None)
        # WO-B3-R1a-2: default = one line per ### at the distinct-visual-object
        # grain; VIRELAI_INTEGRATION_ROSTER_VERBOSE appends each ###'s full
        # fingerprint trail. lives_used labels Y as last-life (Ruling 2).
        # WO-ROSTER-SEVER-01 · THE LEGACY ROLE SOURCE IS SEVERED FROM THIS RENDER.
        #
        # This site read `self._store_a_role_verdicts(...)` — `library/store_a_role_read`
        # — from WO-DISPLAY-SOURCE-01 until now, on a CE ruling that the crossing was an
        # authorized bridge. That ruling is REVERSED. `RULING_GOLDEN_RUN_v1`'s method is
        # locate → label → port → ISOLATE, and labelling a legacy read does not make it
        # legal to GRADE against it.
        #
        # The measurement that decided it: Store-A argmaxes over
        # `(ego, lever, reactive, counter, static)` — Band-2 archetypes mixed with
        # Band-1 self-state names — so 7 of the 8 disagreements LIST 3 flagged on the
        # primary canary were a Band-1 statement compared against a Band-2 slot, and two
        # real conflicts went unmarked. The column is also unprovenanced: legacy
        # `cycle_probe` writes those axes at confidence 1.0 while the weave writes at
        # 0.60 once per life, and Store-A records no writer.
        #
        # The role source is now `ctx.woven_role_verdicts` — `_land_weave_roles`'s own
        # `infer_roles` output (virelai.py:2065), read here and not recomputed.
        #
        # THE COST, STATED: that field is plain-reassigned every life, so the roster
        # shows LAST-LIFE verdicts. At one life — how we grade — nothing. Across lives,
        # accumulation is lost, and that cost is now load-bearing for exactly one thing:
        # the weave's own belief home, which is where the argument belonged.
        #
        # THE WRITE SIDE IS UNTOUCHED. `_land_weave_roles` still lands weave evidence
        # into Store-A and legacy classifiers still write beside it. This severs the
        # READ, not the write; the pollution persists there, invisible now because no
        # golden-run rendering path reads it. `_store_a_role_verdicts` below is left in
        # place, uncalled and unread — deleting it is not this rung's, and
        # `library/store_a_role_read.py` is neither deleted nor edited.
        # WO-COMPOUND-ROLE-01: repeated_contact still reads ctx.woven_repeated_
        # contact. NOT redirected: WO-DISPLAY-SOURCE-01's own A.5 found no
        # Store-A field means the same thing this signal means (Store-A's
        # actions_attempted is an unthresholded any-click-ever boolean written
        # by the CAPTAIN's own emitter choice; probe_confirmation_count is
        # driven by the deliberate cycle_probe pipeline, not by the weave's
        # passive real-click tally) — redirecting would silently swap in a
        # different claim under the same label. Left as-is; the narrower
        # per-life-only limitation stays, flagged, rather than papered over.
        print(render_integration_roster(
            worldlines,
            verbose=bool(os.environ.get("VIRELAI_INTEGRATION_ROSTER_VERBOSE")),
            lives_observed=getattr(self.ctx, "lives_used", None),
            role_verdicts=getattr(self.ctx, "woven_role_verdicts", None),
            repeated_contact=getattr(self.ctx, "woven_repeated_contact", None),
        ))
        # WO-COVERAGE-ROSTER-01 · THE FIFTH LIST, BESIDE THE THREE. The Director reads
        # the integration roster here; the coverage roster answers the question those
        # three cannot — *was every visual object targeted, and graded touched or not
        # reached.* Same flag, same run-end firing, same pure read off `self.ctx`; the
        # derivation is `visual_targets`' own, so there is no second producer of the queue.
        #
        # **GATED ON THE ARM, AND THAT WAS CAUGHT RATHER THAN DESIGNED IN.** The first
        # wiring printed unconditionally. The sweep runs on BOTH arms, so
        # `weave_sweep_cuts` exists on a click world too and the roster would have rendered
        # a full queue of NEVER ATTEMPTED there — output where there was none, and a claim
        # about a drive that never ran. **The predicate is the one the NAV arm already uses
        # at this file's own dispatch seam**, not a second reading of the world, and it
        # names no world's contents.
        _roster_world = getattr(getattr(self.ctx.semantic_library, "header", None),
                                "world_type", None)
        if _roster_world != "CLICK":
            from virelai_v4.weave.collide_drive import coverage_roster
            print(coverage_roster(self.ctx))
        self._integration_roster_rendered = True

    # ------------------------------------------------------------------
    # Emission validation guard (WO-LGTD-02 Phase 5 — Section 3.8)
    # ------------------------------------------------------------------

    def _validate_emission(
        self,
        action: GameAction,
        latest_frame: FrameData,
    ) -> GameAction:
        """Section 3.8 emission validation per Library Blueprint.

        Secondary guard against emitting actions not in the platform's
        declared set. The primary guard is the Affordance Layer's
        available_probes() — a probe whose required actions are not
        DECLARED never appears in the view, so a captain reading the
        view never selects such a tool. This method exists to catch
        the case where a primary-guard miss slips through (bug, race,
        stale read).

        On pass:  return the action unchanged.
        On miss:  log the unavailability via _record_unavailable_action_attempt
                  and dispatch the out-of-tape fallback.

        Defensive cases:
          - RESET (id=0) always passes (lifecycle action, not a probe).
          - Actions without a .value attribute pass (non-int dispatch).
        """
        action_id = action.value if hasattr(action, "value") else None
        if action_id is None or action_id == 0:
            return action
        if action_id in latest_frame.available_actions:
            return action
        self._record_unavailable_action_attempt(action_id, latest_frame)
        return self._out_of_tape_fallback(latest_frame)

    def _record_unavailable_action_attempt(
        self,
        action_id: int,
        latest_frame: FrameData,
    ) -> None:
        """Diagnostic log entry for an emission that bypassed the primary
        guard. Not a halt condition — the fallback handles the emission.
        The log surfaces the miss to the chamber for follow-up.
        """
        self._log(
            f"[EMISSION-GUARD] Action {action_id} not in "
            f"available_actions={list(latest_frame.available_actions)}; "
            f"falling back. Primary guard (Affordance Layer) may have "
            f"missed this case.",
            always=False,
        )

    def _out_of_tape_fallback(self, latest_frame: FrameData) -> GameAction:
        """Emit a safe action when the primary selection was unavailable.

        Strategy: first declared action from frame.available_actions.
        If no actions are declared (degenerate case), emit RESET.
        """
        if latest_frame.available_actions:
            return GameAction.from_id(latest_frame.available_actions[0])
        return GameAction.RESET

    # ------------------------------------------------------------------
    # Action selection (fallback — random legal)
    # ------------------------------------------------------------------

    def _random_action(self, available_ids: list[int]) -> GameAction:
        """Pick a random legal action from available_actions.

        Kept as a named fallback. select_action() from strategy/ is the
        live path for all NOT_FINISHED frames (WO-02). This method mirrors
        the fallback logic inside select_action for edge-case callers.
        """
        playable = _legal_actions(available_ids)
        if not playable:
            return GameAction.RESET

        chosen_id = self._rng.choice(playable)
        action = GameAction.from_id(chosen_id)

        if action.is_complex():
            action.set_data({
                "x": self._rng.randint(0, 63),
                "y": self._rng.randint(0, 63),
            })

        return action
