"""
memory/lever_combination_memory.py

LeverCombinationMemory — session-scoped state for FORGE-05 machine-aware
lever enumeration.

Persists across lives within a session.  Uses Gray code traversal so that
each consecutive configuration differs by exactly one lever toggle.  Cost:
1 targeted click per configuration transition (no resets between configs
within a life).

Gray code ordering
──────────────────
The Gray code sequence for n levers enumerates all 2^n configurations such
that neighbouring entries differ by exactly one bit.  This means each
transition from config[i] to config[i+1] = toggle exactly one lever.

Cross-life continuity
─────────────────────
At the start of Life 2+, the physical state is reset to spawn (config 0).
`reposition_clicks()` returns the ordered list of lever indices to click to
navigate from spawn back to the last tested position in the sequence.  The
reposition costs at most n_levers clicks and re-enters the sequence without
retesting already-recorded configurations.

Design rules
────────────
• No external dependencies beyond stdlib + typing.
• Mutable (needs gray_index and tested_configs to update across steps).
• Iteration order is deterministic: Gray code sequence, physically traversing
  already-tested configs to maintain state continuity.
• `next_transition()` returns None when all 2^n configs have been tested OR
  when win_config is banked.
• `next_untested()` returns the next untested config (or None) — used by
  CRUCIBLE gate to check if enumeration should continue.
• Thread-safety is not required (single-threaded solver).

WO-FORGE-EXEC-01 — replaces WO-FORGE-05 popcount ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product as _itertools_product
from typing import Dict, List, Optional, Set, Tuple


# ── Gray code helpers ──────────────────────────────────────────────────────────

def gray_code_sequence(n_bits: int) -> List[int]:
    """Generate the standard reflected Gray code sequence for n_bits.

    Each consecutive pair of entries differs by exactly one bit.
    Length = 2^n_bits.  First entry is always 0 (spawn state).

    Example (3 bits):
        [0, 1, 3, 2, 6, 7, 5, 4]
    Binary: 000, 001, 011, 010, 110, 111, 101, 100
    Each step flips exactly one bit.
    """
    if n_bits <= 0:
        return [0]
    return [i ^ (i >> 1) for i in range(1 << n_bits)]


def gray_code_transition(current_config: int, next_config: int) -> int:
    """Return the lever index (bit position) that differs between two Gray
    code neighbours.

    XOR gives the single differing bit; bit_length()-1 converts to position.
    Caller must ensure current_config and next_config are genuine Gray code
    neighbours (differ by exactly one bit).

    Returns the 0-based bit position of the toggled lever.
    """
    diff = current_config ^ next_config
    # diff must be a power of 2 for genuine Gray code neighbours
    return diff.bit_length() - 1


# ── Sub-record (kept for backward compatibility) ──────────────────────────────

@dataclass(frozen=True)
class LeverSubsetRecord:
    """Outcome of a single lever-subset attempt.  Kept for backward compat."""
    subset_mask: int        # bitmask encoding which levers were activated
    won: bool               # True if environment signalled terminal win
    tension_delta: float    # pixel-tension change (positive = state changed)
    pixels_changed: int     # number of pixels that changed during play


# ── LeverCombinationMemory ─────────────────────────────────────────────────────

@dataclass
class LeverCombinationMemory:
    """
    Session-scoped enumeration memory for a FINITE_SEARCH machine.

    Uses Gray code traversal: each transition costs exactly one lever toggle
    (one targeted click).  Within a single life, approximately budget/1
    configurations can be tested.  Across lives, `reposition_clicks()` gives
    the minimal click sequence to re-enter the sequence from spawn.

    Parameters
    ──────────
    lever_ids : List[str]
        Ordered lever IDs (e.g. ['LEVER_CLICK_9_38_38', ...]).
        Bit i of a configuration integer corresponds to lever_ids[i].
    n_levers : int
        len(lever_ids). Derived at construction; stored for convenience.
    gray_sequence : List[int]
        Precomputed Gray code sequence (length 2^n_levers).
        gray_sequence[0] = 0 (spawn state).
    gray_index : int
        Current position in gray_sequence.  0 = at spawn, not yet tested
        anything.  Advances on each next_transition() call.
    tested_configs : Set[int]
        Gray code integers that have been physically tested (env stepped).
    win_config : Optional[int]
        Gray code integer of the configuration that produced a win.
        None until a win is recorded.
    current_config : int
        Current physical configuration (last config after any transition).

    Public API
    ──────────
    next_transition() -> Optional[Tuple[int, int]]
        Returns (lever_index, next_config) for the next step, or None if
        all configs tested or win already banked.  Always advances through
        the Gray code sequence one step at a time (including already-tested
        configs) to maintain physical state continuity.
    next_untested() -> Optional[int]
        Returns the next untested config integer (for CRUCIBLE gate check),
        or None if exhausted / win banked.  Does NOT advance gray_index.
    record_config(config, won) -> None
        Records the outcome of one physical step.
    reposition_clicks() -> List[int]
        Lever indices to click from spawn to reach gray_sequence[gray_index].
    record_attempt(subset, won, tension_delta, pixels_changed) -> None
        Backward-compat wrapper — delegates to record_config().
    to_lever_ids(config) -> List[str]
        Converts a config integer to the list of toggled lever IDs.
    to_bitmask(lever_id_list) -> int
        Converts a list of lever IDs to a config integer.
    exhausted : bool (property)
        True when all non-zero configurations have been tested.
    tested_count : int (property)
        Number of configurations tested so far.
    win_subset : Optional[int] (property)
        Alias for win_config (backward compatibility with CRUCIBLE/tests).
    """

    lever_ids: List[str]
    n_levers: int
    gray_sequence: List[int] = field(default_factory=list)
    gray_index: int = 0
    tested_configs: Set[int] = field(default_factory=set)
    win_config: Optional[int] = None
    current_config: int = 0

    # ── Construction helper ──────────────────────────────────────────────────

    @classmethod
    def from_lever_ids(cls, lever_ids: List[str]) -> "LeverCombinationMemory":
        """Create a fresh memory for the given ordered lever list."""
        n = len(lever_ids)
        return cls(
            lever_ids=list(lever_ids),
            n_levers=n,
            gray_sequence=gray_code_sequence(n),
            gray_index=0,
            tested_configs=set(),
            win_config=None,
            current_config=0,
        )

    # ── Gray code traversal ───────────────────────────────────────────────────

    def next_transition(self) -> Optional[Tuple[int, int]]:
        """
        Return (lever_index, next_config) for the next step in the Gray code
        sequence and advance gray_index by one.

        Always advances exactly one step — even if that step leads to an
        already-tested config (physical state continuity requires traversing
        the full sequence).  The caller must check whether the returned config
        is in tested_configs if it wants to skip recording.

        Returns None when:
          • win_config is already banked, or
          • gray_index is at the last position in the sequence (exhausted).
        """
        if self.win_config is not None:
            return None
        if self.gray_index >= len(self.gray_sequence) - 1:
            return None

        next_idx = self.gray_index + 1
        next_config = self.gray_sequence[next_idx]
        lever_index = gray_code_transition(
            self.gray_sequence[self.gray_index],
            next_config,
        )
        self.gray_index = next_idx
        return (lever_index, next_config)

    def next_untested(self) -> Optional[int]:
        """
        Return the next untested config integer (for CRUCIBLE gate check).

        Does NOT advance gray_index.  Returns None if win_config banked or
        all non-zero configs in the sequence have been tested.
        """
        if self.win_config is not None:
            return None
        if self.exhausted:
            return None
        # Walk the sequence from current position to find the next untested
        for i in range(self.gray_index + 1, len(self.gray_sequence)):
            config = self.gray_sequence[i]
            if config not in self.tested_configs:
                return config
        return None

    def reposition_clicks(self) -> List[int]:
        """
        Return lever indices to click (in order) to navigate from spawn
        (config 0) to gray_sequence[gray_index].

        Used at the start of Life 2+ to re-enter the sequence from spawn
        without retesting already-recorded configurations.

        Cost: popcount(gray_sequence[gray_index]) clicks (at most n_levers).
        """
        target = self.gray_sequence[self.gray_index]
        return [i for i in range(self.n_levers) if target & (1 << i)]

    # ── Mutation ──────────────────────────────────────────────────────────────

    def record_config(
        self,
        config: int,
        won: bool,
    ) -> None:
        """
        Record the outcome of one physical configuration test.

        If won=True, banks win_config; subsequent next_transition() returns None.
        """
        self.tested_configs.add(config)
        self.current_config = config
        if won:
            self.win_config = config

    def record_attempt(
        self,
        subset: int,
        won: bool,
        tension_delta: float = 0.0,
        pixels_changed: int = 0,
    ) -> None:
        """
        Backward-compatibility wrapper: delegates to record_config().

        tension_delta and pixels_changed are accepted but not stored
        (Gray code traversal does not use subset-level metrics).
        """
        self.record_config(subset, won)

    # ── Bitmask ↔ lever_id helpers ────────────────────────────────────────────

    def to_lever_ids(self, config: int) -> List[str]:
        """Convert a config integer to the ordered list of lever_id strings."""
        return [
            self.lever_ids[i]
            for i in range(self.n_levers)
            if config & (1 << i)
        ]

    def to_bitmask(self, lever_id_list: List[str]) -> int:
        """Convert a list of lever_id strings to a config integer."""
        index = {lid: i for i, lid in enumerate(self.lever_ids)}
        mask = 0
        for lid in lever_id_list:
            i = index.get(lid)
            if i is not None:
                mask |= (1 << i)
        return mask

    # ── Diagnostics ───────────────────────────────────────────────────────────

    @property
    def win_subset(self) -> Optional[int]:
        """Backward-compat alias for win_config."""
        return self.win_config

    @property
    def tested_count(self) -> int:
        return len(self.tested_configs)

    @property
    def total_non_empty(self) -> int:
        return max(0, (1 << self.n_levers) - 1)

    @property
    def exhausted(self) -> bool:
        """True when every non-zero config in the sequence has been tested."""
        return self.tested_count >= self.total_non_empty

    def __repr__(self) -> str:
        return (
            f"LeverCombinationMemory("
            f"n_levers={self.n_levers}, "
            f"tested={self.tested_count}/{self.total_non_empty}, "
            f"gray_index={self.gray_index}, "
            f"win_config={self.win_config!r})"
        )


# ── Depth sequence helpers ─────────────────────────────────────────────────────

def depth_sequence_order(n_levers: int, max_depth: int) -> List[Tuple[int, ...]]:
    """Generate all non-zero depth sequences ordered by total clicks ascending.

    Each sequence is a tuple of click counts (d0, d1, ..., d_{n-1}), where
    di ∈ {0, ..., max_depth}.  The all-zeros tuple is excluded (spawn state
    requires no clicks and is tested implicitly by default).

    Ordering: ascending total clicks, then lexicographic within same total.

    Example (2 levers, max_depth=2):
        [(1,0), (0,1), (2,0), (1,1), (0,2)]

    The resulting list is precomputed at construction and stored in
    DepthSequenceMemory.sequence_order.
    """
    if n_levers <= 0 or max_depth <= 0:
        return []
    all_seqs = list(_itertools_product(range(max_depth + 1), repeat=n_levers))
    # Exclude the all-zero sequence (spawn state)
    non_zero = [s for s in all_seqs if any(d > 0 for d in s)]
    # Sort: ascending total clicks, then lexicographic tiebreak
    non_zero.sort(key=lambda s: (sum(s), s))
    return non_zero


# ── DepthSequenceMemory ────────────────────────────────────────────────────────

@dataclass
class DepthSequenceMemory:
    """
    Session-scoped enumeration memory for DIRECTIONAL lever machines.

    WO-FORGE-GATE-02: replaces Gray code (LeverCombinationMemory) when the
    world machine is DIRECTIONAL (levers are PROVISIONAL_DRIFT / multi-step).

    Each life tests ONE depth sequence: click lever_ids[i] exactly sequence[i]
    times from spawn.  Sequences are ordered by ascending total clicks (singles
    first, then pairs, then triples…).

    Persists across lives via state["depth_sequence_memory"].

    Parameters
    ──────────
    lever_ids : List[str]
        Ordered lever IDs (e.g. ['LEVER_CLICK_9_38_38', ...]).
    n_levers : int
        len(lever_ids). Derived at construction; stored for convenience.
    max_depth : int
        Maximum clicks per lever observed from cycle probe (default 4).
    sequence_order : List[Tuple[int, ...]]
        Precomputed ordered list of all non-zero depth tuples (length
        (max_depth+1)^n_levers - 1).
    sequence_index : int
        Next index in sequence_order to try. Advances past tested sequences.
    tested_sequences : Set[Tuple[int, ...]]
        Sequences that have been physically executed.
    win_sequence : Optional[Tuple[int, ...]]
        The sequence that produced a win. None until a win is recorded.
    """

    lever_ids: List[str]
    n_levers: int
    max_depth: int
    sequence_order: List[Tuple[int, ...]] = field(default_factory=list)
    sequence_index: int = 0
    tested_sequences: Set[Tuple[int, ...]] = field(default_factory=set)
    win_sequence: Optional[Tuple[int, ...]] = None

    # ── Construction ──────────────────────────────────────────────────────────

    @classmethod
    def from_lever_ids(
        cls,
        lever_ids: List[str],
        max_depth: int = 4,
    ) -> "DepthSequenceMemory":
        """Create a fresh memory for the given lever list and probe depth."""
        n = len(lever_ids)
        order = depth_sequence_order(n, max_depth)
        return cls(
            lever_ids=list(lever_ids),
            n_levers=n,
            max_depth=max_depth,
            sequence_order=order,
            sequence_index=0,
            tested_sequences=set(),
            win_sequence=None,
        )

    # ── Traversal API ─────────────────────────────────────────────────────────

    def next_untested(self) -> Optional[Tuple[int, ...]]:
        """Return the next untested sequence, or None if win banked or exhausted.

        Does NOT advance sequence_index.  Callers use this to peek at what
        will be executed; record_sequence() advances the index.
        """
        if self.win_sequence is not None:
            return None
        for seq in self.sequence_order[self.sequence_index:]:
            if seq not in self.tested_sequences:
                return seq
        return None

    def record_sequence(self, sequence: Tuple[int, ...], won: bool) -> None:
        """Record the outcome of one depth sequence execution.

        Advances sequence_index past any already-tested sequences so that
        next_untested() returns the correct next item.
        """
        self.tested_sequences.add(sequence)
        if won:
            self.win_sequence = sequence
        # Advance index past tested sequences
        while (
            self.sequence_index < len(self.sequence_order)
            and self.sequence_order[self.sequence_index] in self.tested_sequences
        ):
            self.sequence_index += 1

    # ── Conversion helpers ────────────────────────────────────────────────────

    def to_lever_clicks(
        self, sequence: Tuple[int, ...]
    ) -> List[Tuple[str, int]]:
        """Convert a depth sequence to [(lever_id, click_count), ...] pairs.

        Zero-depth levers are omitted (no clicks needed for them).
        """
        return [
            (self.lever_ids[i], d)
            for i, d in enumerate(sequence)
            if d > 0
        ]

    # ── Diagnostics ───────────────────────────────────────────────────────────

    @property
    def tested_count(self) -> int:
        return len(self.tested_sequences)

    @property
    def total_sequences(self) -> int:
        return len(self.sequence_order)

    @property
    def exhausted(self) -> bool:
        return self.tested_count >= self.total_sequences

    @property
    def win_subset(self) -> Optional[Tuple[int, ...]]:
        """Alias for win_sequence — consistent API with LeverCombinationMemory."""
        return self.win_sequence

    def __repr__(self) -> str:
        return (
            f"DepthSequenceMemory("
            f"n_levers={self.n_levers}, "
            f"max_depth={self.max_depth}, "
            f"tested={self.tested_count}/{self.total_sequences}, "
            f"win_sequence={self.win_sequence!r})"
        )


__all__ = [
    "LeverSubsetRecord",
    "LeverCombinationMemory",
    "DepthSequenceMemory",
    "gray_code_sequence",
    "gray_code_transition",
    "depth_sequence_order",
]
