"""WO-FRAME-P2-02: Novel State Tracking — cybernetic consumer.

After every action, hash the current grid state and check against a visited set.
Track novel vs repeated states. Detect oscillation traps (consecutive repeated
states). Persist through Groundhog Day so Life 2 knows what Life 1 already saw.

The Virelai State Space Theorem in code: the win state is always an unseen
configuration. Novel states are progress. Repeated states are waste.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


def compute_state_signature(grid: np.ndarray) -> str:
    """Compute a deterministic signature for a grid state.

    Uses SHA-256 truncated to 16 hex chars. Deterministic across
    sessions and lives. Collision probability negligible at <10,000 states.
    """
    return hashlib.sha256(grid.tobytes()).hexdigest()[:16]


# WO-R4 (True Edges): the composite edge key. A directional/simple action keys on
# (action_id, None); a complex action keys on (action_id, target) where target is
# an opaque token (region_id). Bare ints normalize to (int, None) so directional
# callers are byte-unchanged and the amendment is additive.
EdgeKey = Tuple[int, Optional[Any]]


def _norm_key(action_id, target=None) -> "EdgeKey":
    """Normalize to a composite EdgeKey. A bare int → (int, None); an
    already-composite (action_id, target) tuple passes through unchanged."""
    if isinstance(action_id, tuple):
        return action_id
    return (action_id, target)


@dataclass
class StateTracker:
    """Tracks novel vs repeated grid states across a solver life.

    Accumulates across actions. Seeded from persisted state on Life 2+.
    Read-only consumer of observation memory — no side effects on execution.
    """

    visited: Dict[str, int] = field(default_factory=dict)  # signature → first_seen_step
    novel_count: int = 0
    repeated_count: int = 0
    consecutive_repeated: int = 0  # oscillation detection
    _last_signature: Optional[str] = None

    # WO-CP1-FIX-A: the instrument's live-region calibration. Set once when the
    # live regions become known (COUNTER detected / ctx.hud_mask built);
    # record() masks internally so EVERY record call site is fixed at once.
    # Runtime calibration of the instrument, not belief — not serialized.
    _live_hud_mask: Optional[np.ndarray] = None
    _live_lc_region: Optional[tuple] = None

    # WO-PUSH-P1-R1 (OG-4 retention): the value side of the map. Additive —
    # the `visited` seen-set above and every metric off it are untouched. These
    # retain the transition the two record sites already assemble and discard.
    #   edges  : from_sig → {action_id → to_sig}     (successor edges)
    #   tried  : from_sig → {action_id, …}           (per-state actions taken)
    #   alarms : (from_sig, action_id, expected_to, got_to, step)
    #            — hidden-state tripwire: same (state, action), different
    #            successor. On a history-deterministic world that is a real
    #            latent, not noise.
    edges: Dict[str, Dict[int, str]] = field(default_factory=dict)
    tried: Dict[str, Set[int]] = field(default_factory=dict)
    alarms: List[Tuple[str, int, str, str, int]] = field(default_factory=list)

    # WO-PUSH-R2 (the frontier value-side): the legal action set observed at a
    # state's first-seen. `untried(sig) = legal[sig] - tried[sig]`; a sig with
    # non-empty untried is an OPEN frontier node. Captured at first-seen only,
    # never overwritten. Additive — no floor metric reads it.
    legal: Dict[str, Set[int]] = field(default_factory=dict)

    # WO-PUSH-R3′ (the re-home plan): a persisted, progress-verified replay plan
    # so re-home is one bounded RESET + a recorded-edge walk to the frontier —
    # never a per-frame bare RESET loop. `_plan` is the remaining
    # (action_id, expected_to_sig) steps; `_awaiting_landing` marks the frame
    # after the single RESET, before the landing is observed. Additive — no floor
    # metric reads them; inert until begin_rehome().
    _plan: Optional[List[Tuple[int, str]]] = None
    _awaiting_landing: bool = False

    def set_live_masks(
        self,
        hud_mask: Optional[np.ndarray] = None,
        lc_region: Optional[tuple] = None,
    ) -> None:
        """Calibrate the live-region mask (WO-CP1-FIX-A). Without it the live
        counter makes every frame hash novel — the WO-DIAG-CP1 instrument lie
        ("100% exploration" through a death-spiral)."""
        if hud_mask is not None:
            self._live_hud_mask = hud_mask
        if lc_region is not None:
            self._live_lc_region = lc_region

    def _mask(self, grid: np.ndarray) -> np.ndarray:
        """Apply the live-region mask (WO-CP1-FIX-A) if calibrated. The single
        masking site shared by record() and signature() — one hash path."""
        if self._live_hud_mask is not None or self._live_lc_region is not None:
            from virelai_v4.perception.live_region_mask import mask_live_regions
            grid = mask_live_regions(
                grid,
                hud_mask=self._live_hud_mask,
                lc_region=self._live_lc_region,
            )
        return grid

    def signature(self, grid: np.ndarray) -> str:
        """Masked state signature — the SAME hash path record() writes into
        `visited`. Callers use this to compute a from_sig that is key-consistent
        with the seen-set, so edges/tried never key off a second hashing path
        (WO-PUSH-P1-R1: no parallel store, no drift)."""
        return compute_state_signature(self._mask(grid))

    def record(
        self,
        grid: np.ndarray,
        step: int,
        action_id: Optional[int] = None,
        from_sig: Optional[str] = None,
        legal_actions: Optional[Set] = None,
        target: Optional[Any] = None,
    ) -> bool:
        """Record a state observation. Returns True if novel, False if repeated.

        WO-CP1-FIX-A: when calibrated, hashes mask_live_regions(grid) — live
        regions (counter/HUD) are zeroed before signing, so a counter tick no
        longer reads as a novel world state. Uncalibrated behavior unchanged.

        WO-PUSH-P1-R1 (OG-4 retention): when ``action_id`` and an originating
        state are both known, the transition is retained additively into
        ``edges`` / ``tried`` (with the hidden-state alarm on a divergent
        successor). ``from_sig`` names the originating state; when omitted it
        defaults to the previous recorded state (the sequential walk). Both the
        default and any explicit ``from_sig`` are produced by ``signature()``,
        so retention keys live in the same keyspace as ``visited``. The
        ``visited`` write and the ``novel`` return are byte-identical to the
        pre-retention behavior — passing no action args reproduces it exactly."""
        to_sig = self.signature(grid)

        # --- OG-4 retention (additive; keyed on the originating state) ---
        # WO-R4: the retention key is the composite EdgeKey (action_id, target).
        origin = from_sig if from_sig is not None else self._last_signature
        if action_id is not None and origin is not None:
            key = _norm_key(action_id, target)
            self.tried.setdefault(origin, set()).add(key)
            prior = self.edges.get(origin, {}).get(key)
            if prior is not None and prior != to_sig:
                self.alarms.append((origin, key[0], prior, to_sig, step))
            else:
                self.edges.setdefault(origin, {})[key] = to_sig

        # --- FLOOR: visited seen-set + novelty metrics (unchanged) ---
        if to_sig not in self.visited:
            # WO-PUSH-R2: capture the legal set at FIRST-SEEN only (never
            # overwrite). WO-R4: each candidate normalizes to an EdgeKey — a bare
            # int → (int, None), a composite (id, token) passes through.
            if legal_actions is not None:
                self.legal[to_sig] = {_norm_key(a) for a in legal_actions}
            self.visited[to_sig] = step
            self.novel_count += 1
            self.consecutive_repeated = 0
            self._last_signature = to_sig
            return True
        else:
            self.repeated_count += 1
            self.consecutive_repeated += 1
            self._last_signature = to_sig
            return False

    # ── WO-PUSH-R2 · the frontier value-side (open-set / re-homing) ───────────

    def untried(self, sig: str) -> Set[int]:
        """Legal actions at ``sig`` not yet taken from it: legal − tried.
        Per G5, an invalid action recorded as a self-loop is in ``tried`` and so
        is excluded here — invalids mint no frontier."""
        return set(self.legal.get(sig, set())) - set(self.tried.get(sig, set()))

    def open_set(self) -> Set[str]:
        """The frontier: every seen sig with a non-empty untried set. A node
        enters at first-seen (once its legal set is captured) and leaves exactly
        when its untried empties; it never re-enters absent a falsifying alarm."""
        return {sig for sig in self.legal if self.untried(sig)}

    def target_try_count(self, target) -> int:
        """WO-R4 (target diversity): the global try-count of a target — how many
        tried EdgeKeys across all origins carry it. DERIVED from ``tried`` at call
        time; no stored counter, no second writable surface (the lock pattern
        applied to ordering)."""
        return sum(
            1
            for keys in self.tried.values()
            for k in keys
            if (k[1] if isinstance(k, tuple) else None) == target
        )

    def order_untried(self, keys) -> "List[EdgeKey]":
        """WO-R4 diversity-first ordering: least-globally-tried target first, then
        ``(action_id, str(target))`` — the determinism floor. Simple ``(id, None)``
        edges share ``target=None``, so their relative order stays
        ``(action_id, token)`` — directional byte-identity (G6d), killing the
        deterministic-min-by-token monorail without touching selection lawfulness."""
        def _sort_key(k):
            nk = _norm_key(k)
            return (self.target_try_count(nk[1]), nk[0],
                    "" if nk[1] is None else str(nk[1]))
        return sorted(keys, key=_sort_key)

    def replay_record(
        self, from_sig: str, action_id: int, grid: np.ndarray, step: int,
        target: Optional[Any] = None,
    ) -> str:
        """Gate-B replay writer: the edge is always keyed on an EXPLICIT
        ``from_sig`` — the previous-recorded-state default must never be
        exercised across a reset jump. ``from_sig is None`` is loudly fatal.
        WO-R4: the edge keys on the composite (action_id, target). Extract-then-
        call: routes the retention through ``record``; returns the successor sig."""
        if from_sig is None:
            raise ValueError(
                "replay_record requires an explicit from_sig (Gate-B fence): "
                "the previous-state default is never exercised across a jump."
            )
        self.record(grid, step, action_id=action_id, from_sig=from_sig, target=target)
        return self.signature(grid)

    def rehome(self, landing_sig: str, step: int) -> str:
        """Reset-then-observe (G1/G4): the replay origin is the OBSERVED
        post-reset landing signature, never a stored root constant. A hash-novel
        landing enters the map as first-seen; a known landing mints no novelty.
        Returns the landing sig as the origin to replay from."""
        if landing_sig not in self.visited:
            self.visited[landing_sig] = step
            self.novel_count += 1
            self.consecutive_repeated = 0
        self._last_signature = landing_sig
        return landing_sig

    def nearest_open(self, origin: str) -> Optional[str]:
        """The open-set node nearest ``origin`` by minimal recorded-path length
        (BFS over committed ``edges``), ties broken by smallest sig — nearest
        frontier, coverage-ordered (G6). None when no open node is reachable."""
        open_nodes = self.open_set()
        seen = {origin}
        current = [origin]
        while current:
            here = sorted(s for s in current if s in open_nodes)
            if here:
                return here[0]
            nxt: List[str] = []
            for s in current:
                for to_sig in self.edges.get(s, {}).values():
                    if to_sig not in seen:
                        seen.add(to_sig)
                        nxt.append(to_sig)
            current = nxt
        return None

    # ── WO-PUSH-R3′ · the re-home plan (bounded, progress-verified) ──────────

    def plan_to_frontier(self, from_sig: str) -> Optional[List[Tuple[int, str]]]:
        """The recorded-edge path from ``from_sig`` to the NEAREST open node, as
        ``(action_id, expected_to_sig)`` steps. BFS over committed ``edges`` only
        (never an untracked transition), min edge-hops, ties by smallest sig —
        the same traversal ``nearest_open`` uses, extended to return the route.
        ``None`` when no open node is reachable."""
        open_nodes = self.open_set()
        seen = {from_sig}
        current: List[Tuple[str, List[Tuple[int, str]]]] = [(from_sig, [])]
        while current:
            # a node is a valid target only if reached by a non-empty path
            reached = sorted(s for s, path in current if path and s in open_nodes)
            if reached:
                for s, path in current:
                    if s == reached[0]:
                        return path
            nxt: List[Tuple[str, List[Tuple[Any, str]]]] = []
            for s, path in current:
                # WO-R4: edge keys are composite EdgeKeys; sort None-safe by
                # (action_id, str(target)) for determinism. Steps carry the EdgeKey.
                for key, to_sig in sorted(
                    self.edges.get(s, {}).items(),
                    key=lambda it: (it[0][0], "" if it[0][1] is None else str(it[0][1])),
                ):
                    if to_sig not in seen:
                        seen.add(to_sig)
                        nxt.append((to_sig, path + [(key, to_sig)]))
            current = nxt
        return None

    def begin_rehome(self) -> None:
        """Fire-frame: the single RESET has been chosen; mark awaiting-landing and
        clear any stale plan. The plan binds next frame to the observed landing."""
        self._plan = None
        self._awaiting_landing = True

    def bind_plan(self, landing_sig: str) -> bool:
        """Reset-then-observe: bind the plan to the recorded-edge path from the
        OBSERVED landing to the nearest open node. True iff a non-empty path
        exists; a False (decline) clears the awaiting state — never a second
        RESET."""
        self._awaiting_landing = False
        path = self.plan_to_frontier(landing_sig)
        if path:
            self._plan = list(path)
            return True
        self._plan = None
        return False

    def next_plan_step(self) -> Optional[Tuple[int, str]]:
        """Peek the head ``(action_id, expected_to_sig)`` of the active plan."""
        return self._plan[0] if self._plan else None

    def verify_step(self, observed_sig: str) -> bool:
        """Gate B: the prior step's observed successor must equal its recorded
        ``expected_to_sig``. Match → pop (progress), True. Mismatch → abort the
        plan and append a hidden-state alarm (same step, different successor),
        False."""
        if not self._plan:
            return False
        key, expected_to = self._plan[0]           # WO-R4: key is a composite EdgeKey
        if observed_sig == expected_to:
            self._plan.pop(0)
            if not self._plan:
                self._plan = None
            return True
        aid = key[0] if isinstance(key, tuple) else key
        self.alarms.append((expected_to, aid, expected_to, observed_sig, -1))
        self.abort_plan()
        return False

    def abort_plan(self) -> None:
        """Clear all plan state (mismatch or teardown)."""
        self._plan = None
        self._awaiting_landing = False

    @property
    def plan_active(self) -> bool:
        return bool(self._plan)

    @property
    def awaiting_landing(self) -> bool:
        return self._awaiting_landing

    @property
    def total_observations(self) -> int:
        return self.novel_count + self.repeated_count

    @property
    def exploration_efficiency(self) -> float:
        """Ratio of novel states to total observations. 1.0 = perfect exploration."""
        if self.total_observations == 0:
            return 1.0
        return self.novel_count / self.total_observations

    @property
    def is_oscillating(self) -> bool:
        """True if the solver has produced N consecutive repeated states."""
        return self.consecutive_repeated >= 3
