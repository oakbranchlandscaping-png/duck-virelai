"""OG-1 · Reset-Fidelity Audit instrument (WO_PUSH_OG1_HARNESS_BUILD_v1).

Diagnostic question: does issuing a reset return the harness to the state it
started from? Its live verdict (Director-run, post-commit) selects Rung 2's
re-homing mechanism.

Design (mirrors ``diagnostics/render_stages.py`` — the V4 diagnostic idiom):

  * The verdict logic is pure and SDK-free (``compute_verdict`` /
    ``count_mask_folded`` / ``CycleResult``) so it imports and unit-tests in the
    sandbox without arcengine. This is what D2 grades.
  * The live agent (``_OG1ResetFidelityMixin`` over ``Virelai``) and every
    heavy/SDK import are DEFERRED into ``build_og1_agent`` / ``run`` — so
    ``import virelai_v4.diagnostics.og1_reset_fidelity`` stays sandbox-safe
    (import-smoke, D-return).
  * Zero solver files modified. New file only. The instrument scripts a fixed
    walk then issues ``GameAction.RESET`` — the sanctioned reset path
    (``virelai.py`` returns ``GameAction.RESET`` itself); no lifecycle bypass.

Two-channel comparison (CE ruling, this rung):
  * SIG — the map's OWN ``state_tracker.signature()`` (masked if live masks are
    calibrated). Key-consistency law: the audit hashes through the identical
    path the Push navigates by, never a second hashing route.
  * RAW — an independent bytes hash of the unmasked grid.
  SIG-match with RAW-mismatch is not a failure; it is the finding "the mask
  already folds this state variable," reported (``MASK_FOLDED_DELTA``), never
  judged.

Live run is the Director's, as a capsule after the Mac gate and commit. Expected
command (pre-registered):

    VIRELAI_MAX_LIVES=<n> python -m virelai_v4.diagnostics.og1_reset_fidelity \
        --game <id> --cycles 5 --walk-depths 3,8,15,5,11 --max-frames 400
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Pure, SDK-free core — the graded surface (D2). No arcengine, no Virelai here.
# ---------------------------------------------------------------------------

CLEAN = "CLEAN"
DIRTY_DETERMINISTIC = "DIRTY-DETERMINISTIC"
DIRTY_VARIABLE = "DIRTY-VARIABLE"

_AGENT_KEY = "virelai_og1_reset_fidelity"
_RESET_ID = 0  # GameAction.RESET value (arcengine/enums.py)


@dataclass
class CycleResult:
    """One reset cycle: root captured, walk of ``depth`` actions, reset, post."""
    k: int
    depth: int
    root_sig: str
    post_sig: str
    root_raw: str
    post_raw: str

    @property
    def sig_match(self) -> bool:
        return self.root_sig == self.post_sig

    @property
    def raw_match(self) -> bool:
        return self.root_raw == self.post_raw

    @property
    def mask_folded(self) -> bool:
        """SIG says 'same state' while RAW says the bytes differ — the mask
        absorbed the delta. The lens-divergence finding (reported, not judged)."""
        return self.sig_match and not self.raw_match

    def line(self) -> str:
        return (
            f"CYCLE {self.k} | depth={self.depth} "
            f"| SIG_MATCH={self.sig_match} | RAW_MATCH={self.raw_match} "
            f"| root={self.root_sig[:8]} post={self.post_sig[:8]}"
        )


def compute_verdict(cycles: Sequence[CycleResult]) -> str:
    """Mechanical Gate-A verdict — no interpretation lives here.

    * every cycle's SIG matches its root                 -> CLEAN
    * SIG never all-match, but every post-sig is equal
      to the others and differs from the first root      -> DIRTY-DETERMINISTIC
    * otherwise                                          -> DIRTY-VARIABLE
    """
    if not cycles:
        return DIRTY_VARIABLE
    if all(c.sig_match for c in cycles):
        return CLEAN
    post_sigs = {c.post_sig for c in cycles}
    if len(post_sigs) == 1 and next(iter(post_sigs)) != cycles[0].root_sig:
        return DIRTY_DETERMINISTIC
    return DIRTY_VARIABLE


def operative_root(cycles: Sequence[CycleResult]) -> Optional[str]:
    """The consistent post-reset sig when the verdict is DIRTY-DETERMINISTIC —
    the candidate operative root the Push would re-home to. None otherwise."""
    if compute_verdict(cycles) == DIRTY_DETERMINISTIC:
        return cycles[0].post_sig
    return None


def count_mask_folded(cycles: Sequence[CycleResult]) -> int:
    """Number of cycles where SIG matched but RAW did not (mask folded a delta)."""
    return sum(1 for c in cycles if c.mask_folded)


def render_report(cycles: Sequence[CycleResult]) -> str:
    """Assemble the full instrument output: one line per cycle, one verdict line,
    and (if any) the mask-fold count. Pure — used by both live and tests."""
    lines = [c.line() for c in cycles]
    verdict = compute_verdict(cycles)
    if verdict == DIRTY_DETERMINISTIC:
        lines.append(f"VERDICT: {verdict} | operative_root={operative_root(cycles)[:8]}")
    else:
        lines.append(f"VERDICT: {verdict}")
    folded = count_mask_folded(cycles)
    if folded:
        lines.append(f"MASK_FOLDED_DELTA={folded}")
    return "\n".join(lines)


def raw_hash(grid: np.ndarray) -> str:
    """Independent RAW channel — bytes hash of the UNMASKED grid (16 hex),
    deliberately NOT routed through the tracker's signature()."""
    return hashlib.sha256(np.ascontiguousarray(grid).tobytes()).hexdigest()[:16]


def parse_walk_depths(spec: str) -> List[int]:
    """`"3,8,15"` -> [3, 8, 15]. Fixed schedule; no game mechanic encoded."""
    return [int(tok) for tok in spec.split(",") if tok.strip() != ""]


def _entry_action_id(entry) -> int:
    """Int action id for an available_actions entry — a bare int, or an
    enum-typed member exposing ``.value``. Used only to select and to route
    through the enum's sanctioned ``from_id``; never to reconstruct via the
    int constructor."""
    return int(getattr(entry, "value", entry))


def resolve_walk_action(available, rng, rows, cols, game_action_cls=None):
    """Map an available-action set to a fully-issuable walk action (RESET excluded).

    PORT, not invention — mirrors the solver's proven construction verbatim
    (``strategy/action_selector.py:random_probe_tool`` :113–126 and
    ``virelai.py:_random_action`` :979–985):

      * pick a legal id, then build the action via ``GameAction.from_id`` — NOT
        ``GameAction(int(...))``. The enum's members are declared with tuple args
        and ``ACTION6`` is complex; the int constructor raises
        ``"6 is not a valid GameAction"`` (the Capsule-8 fault at :228).
        ``from_id`` iterates members matching the id — the sanctioned path.
      * for a complex action (``ACTION6``), set fixed-seed, grid-bounds
        coordinates via ``set_data`` — zero game knowledge; x∈[0,cols-1],
        y∈[0,rows-1] derive only from grid dims and the seed.

    ``game_action_cls`` is injected (defaults to the live ``GameAction``) so the
    resolution unit-tests in the sandbox without the ARC SDK. ``rng`` follows the
    ``random.Random`` interface the ported sites use (``choice``, ``randint``
    inclusive)."""
    if game_action_cls is None:
        from arcengine import GameAction as game_action_cls  # lazy — live only
    ids = [_entry_action_id(a) for a in available]
    playable = [i for i in ids if i != _RESET_ID]
    if not playable:
        return game_action_cls.from_id(_RESET_ID)
    chosen_id = rng.choice(playable)
    action = game_action_cls.from_id(chosen_id)
    if action.is_complex():
        action.set_data({"x": rng.randint(0, cols - 1), "y": rng.randint(0, rows - 1)})
    return action


# ---------------------------------------------------------------------------
# CLI parser — SDK-free, so it parses/tests in the sandbox.
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="virelai_v4.diagnostics.og1_reset_fidelity",
        description="OG-1 reset-fidelity audit: does a reset return the harness "
                    "to the state it started from? Prints per-cycle SIG/RAW "
                    "matches and a mechanical CLEAN/DIRTY verdict.",
    )
    p.add_argument("--game", required=True, help="Game id, forwarded to the harness (game-free code).")
    p.add_argument("--cycles", type=int, default=5, help="Number of reset cycles (default 5).")
    p.add_argument("--walk-depths", type=str, default="3,8,15,5,11",
                   help="Comma-separated walk depths, cycled (default 3,8,15,5,11).")
    p.add_argument("--max-frames", type=int, default=None,
                   help="Hard guard on total frames driven (safety).")
    p.add_argument("--seed", type=int, default=0, help="Fixed seed for walk-action choice.")
    return p


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# Live agent + harness driving — ALL DEFERRED (pull the ARC SDK; live-run only).
# ---------------------------------------------------------------------------

# SDK indirections — lazy, and monkeypatchable so the mixin can be driven under
# fakes in the sandbox (the render_stages `_get_grid` idiom). Nothing here runs
# at import; import-smoke stays SDK-free.

def _frame_grid(latest_frame):
    """Grid for a frame via the agent module's extractor. Lazy (pulls the ARC
    SDK); tests monkeypatch this symbol to drive choose_action SDK-free."""
    from virelai_v4.virelai import _grid_from_frame
    return _grid_from_frame(latest_frame)


def _reset_action(game_action_cls=None):
    """The RESET action (id 0) via the sanctioned constructor `from_id`. Lazy;
    tests pass a fake enum through game_action_cls."""
    if game_action_cls is None:
        from arcengine import GameAction as game_action_cls  # lazy — live only
    return game_action_cls.from_id(_RESET_ID)


# The scripted-walk mixin — MODULE-LEVEL (WO-FIX2) so it is constructable over a
# fake base in the sandbox: the grader now drives `choose_action` itself. Touches
# the ARC SDK only through the two indirections above and an injectable
# `_game_action_cls`, never at import or class-definition time.

class _OG1ResetFidelityMixin:
    """Scripts a fixed walk then issues RESET, capturing SIG (via the agent's OWN
    state_tracker.signature) and RAW (independent) each cycle. Delegates to
    super().choose_action first so the agent perceives and its state_tracker
    calibrates — then substitutes the scripted action. Writes no solver state."""

    # class-level config, set by run() before the harness builds the agent
    _cycles: int = 5
    _walk_depths: List[int] = None            # type: ignore[assignment]
    _max_frames: Optional[int] = None
    _seed: int = 0
    _game_action_cls = None                   # injected in tests; None -> live GameAction

    def _reset(self):
        """Single RESET-construction point — the sanctioned channel, injectable."""
        return _reset_action(self._game_action_cls)

    def _og1_init(self) -> None:
        self._og1_results: List[CycleResult] = []
        # random.Random — the rng interface the ported action_selector uses.
        self._og1_rng = random.Random(self._seed)
        self._og1_frame_count = 0
        self._og1_cycle = 0
        self._og1_phase = "capture_root"       # capture_root | walking | await_return
        self._og1_steps_left = 0
        self._og1_depth = 0
        self._og1_root_sig: Optional[str] = None
        self._og1_root_raw: Optional[str] = None
        self._og1_done = False
        self._og1_reported = False

    def _og1_depth_for(self, cycle: int) -> int:
        depths = self._walk_depths or [3, 8, 15, 5, 11]
        return depths[cycle % len(depths)]

    def _og1_walk_action(self, latest_frame):
        """The ONE walk-action derivation point (WO-FIX2 — single signature, so
        no call site can under-supply). Derives grid dims internally and ports the
        solver construction via resolve_walk_action. Fixed-seed; no mechanic."""
        np_grid = np.asarray(_frame_grid(latest_frame))
        rows, cols = int(np_grid.shape[-2]), int(np_grid.shape[-1])
        available = list(getattr(latest_frame, "available_actions", []) or [])
        return resolve_walk_action(available, self._og1_rng, rows, cols,
                                   self._game_action_cls)

    def _og1_finish(self) -> None:
        if not self._og1_reported:
            print(render_report(self._og1_results))
            self._og1_reported = True
        self._og1_done = True

    def choose_action(self, frames, latest_frame):
        # let the agent perceive normally (calibrates state_tracker); action discarded
        _ = super().choose_action(frames, latest_frame)

        if not hasattr(self, "_og1_results"):
            self._og1_init()

        self._og1_frame_count += 1
        if self._og1_max_exceeded():
            self._og1_finish()
            return self._reset()

        grid = _frame_grid(latest_frame)
        if grid is None:
            return self._reset()
        np_grid = np.asarray(grid)
        sig = self.ctx.state_tracker.signature(np_grid)
        raw = raw_hash(np_grid)

        if self._og1_done:
            return self._reset()

        if self._og1_phase == "capture_root":
            self._og1_root_sig, self._og1_root_raw = sig, raw
            self._og1_depth = self._og1_depth_for(self._og1_cycle)
            self._og1_steps_left = self._og1_depth
            self._og1_phase = "walking"
            if self._og1_steps_left <= 0:
                self._og1_phase = "await_return"
                return self._reset()
            self._og1_steps_left -= 1
            return self._og1_walk_action(latest_frame)

        if self._og1_phase == "walking":
            if self._og1_steps_left > 0:
                self._og1_steps_left -= 1
                return self._og1_walk_action(latest_frame)
            self._og1_phase = "await_return"
            return self._reset()

        # await_return: this frame is the post-reset frame
        self._og1_results.append(CycleResult(
            k=self._og1_cycle, depth=self._og1_depth,
            root_sig=self._og1_root_sig, post_sig=sig,
            root_raw=self._og1_root_raw, post_raw=raw,
        ))
        print(self._og1_results[-1].line())
        self._og1_cycle += 1
        if self._og1_cycle >= self._cycles:
            self._og1_finish()
            return self._reset()
        # the post-reset frame is the next cycle's root — reuse it
        self._og1_root_sig, self._og1_root_raw = sig, raw
        self._og1_depth = self._og1_depth_for(self._og1_cycle)
        self._og1_steps_left = self._og1_depth
        self._og1_phase = "walking"
        if self._og1_steps_left <= 0:
            self._og1_phase = "await_return"
            return self._reset()
        self._og1_steps_left -= 1
        return self._og1_walk_action(latest_frame)

    def _og1_max_exceeded(self) -> bool:
        return (self._max_frames is not None
                and self._og1_frame_count > self._max_frames)

    def cleanup(self, scorecard=None):
        # Print whatever cycles completed, even on an early/max-frames stop.
        if not getattr(self, "_og1_reported", False) and getattr(self, "_og1_results", None):
            print(render_report(self._og1_results))
            self._og1_reported = True
        super().cleanup(scorecard)


def build_og1_agent() -> type:
    """Compose the module-level walk mixin onto the production Virelai agent.

    Deferred: importing Virelai pulls the live ARC SDK. Import order mirrors
    render_stages.build_observer_agent — initialize `agents` FIRST (the harness's
    own cycle-resolution order), then import Virelai. No edit to any solver file.
    """
    import agents  # noqa: F401 — initialize the package first (cycle order)
    from virelai_v4.virelai import Virelai
    return type("VirelaiOG1ResetFidelity", (_OG1ResetFidelityMixin, Virelai), {})


def run(argv: Optional[Sequence[str]] = None) -> None:
    """Configure the walk, register the agent, delegate to the harness entry.
    Heavy/SDK imports deferred here so module import stays sandbox-light."""
    args = parse_args(argv)
    agent_cls = build_og1_agent()
    agent_cls._cycles = args.cycles
    agent_cls._walk_depths = parse_walk_depths(args.walk_depths)
    agent_cls._max_frames = args.max_frames
    agent_cls._seed = args.seed

    import agents
    agents.AVAILABLE_AGENTS[_AGENT_KEY] = agent_cls

    import main as harness_main  # deferred: pulls requests/dotenv
    sys.argv = ["main", "--agent", _AGENT_KEY, "--game", args.game]
    harness_main.main()


if __name__ == "__main__":
    run()
