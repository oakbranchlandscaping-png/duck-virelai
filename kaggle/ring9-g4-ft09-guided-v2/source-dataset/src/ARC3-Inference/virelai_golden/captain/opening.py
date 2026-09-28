"""CAPTAIN · opening — the generative opening: touch everything once, exercise every button.

Canon: 03 §5 — "At first contact the library is empty and the captain knows no object. The
opening is generative, not strategic. Touch everything once — each individuated object at its
site, each base action exercised. Exhaustive by enumeration, so the world is forced to reveal
itself and the opening terminates. The systematic input-cycling IS the ego/counter probe."
R-A / 03 §6.1: the captain cannot know how to probe until the ego resolves — so the opening
presses every offered kind and lets the seals read it.

Transcription origin (R-C): virelai_v4/weave/coverage_sweep.py:249-306 `_unpaired`,
`_opening_action` (WO_OPENING_PHASE_01, "The Ego Finds Itself Before It Goes Anywhere") — every
offered non-targeted action pressed TWICE, in CONSECUTIVE pairs, the offered set asked fresh
each frame. What it proved: the paired opening on the embodied canary (harvest 2026-08-28:
presses {1:2, 2:2, 3:2, 4:2}, cost 2 × |offered| and never written down). The "two" is a
cardinality, not a threshold: `EgoMap.bearings` is a ∀ over presses of one button, vacuous
with one press; the second press is the first at which the ∀ means anything. Consecutive, not
interleaved: a pair straddling other presses is not a reproduction.

NEW (labeled, from 03 §5's "each individuated object at its site"): on a world offering the
site-selecting action, click each frame-0 region's anchor ONCE (scan order). One press per site
is the ∃ the pointer seal needs (R-F); no pairing — a click's reproduction is a site question
the lever hunt asks later (R-G).

When the enumeration is exhausted the opening is COMPLETE and the policy returns None: at
Rung 1 the captain has no further lawful question, and `play` stops with that reason stated.
Replaces adapter.CyclePolicy (CYCLE-v0, a scaffold that said so).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from virelai_golden.substrate.grid import settled
from virelai_golden.substrate.scan import scan_grid

RESET = 0
CLICK = 6
Action = Tuple[int, Optional[Tuple[int, int]]]


class Opening:
    """State: presses per non-targeted action, and the frame-0 sites clicked. Derived, no flag."""

    def __init__(self) -> None:
        self.pressed: Dict[int, int] = {}
        self.sites: List[Tuple[int, int]] = []
        self.clicked = 0
        self.complete_reason: Optional[str] = None

    def unpaired(self, available: Sequence[int]) -> Tuple[int, ...]:
        """Offered non-targeted actions pressed at most once, deterministic order."""
        return tuple(sorted(a for a in available if a not in (RESET, CLICK) and self.pressed.get(a, 0) <= 1))

    def next(self, available: Sequence[int], frame0_layers: Any, givens: Any = None) -> Optional[Action]:
        unpaired = self.unpaired(available)
        if unpaired:
            started = tuple(a for a in unpaired if self.pressed.get(a, 0) > 0)
            a = (started or unpaired)[0]           # finish the pair started, else open the next
            self.pressed[a] = self.pressed.get(a, 0) + 1
            return a, None
        if CLICK in available:
            if not self.sites:
                self.sites = [min(r.cells) for r in scan_grid(settled(frame0_layers))]  # NW-most MEMBER cell (G3-03: a bbox corner may be another region's cell)
            if self.clicked < len(self.sites):
                cell = self.sites[self.clicked]
                self.clicked += 1
                return CLICK, cell
        self.complete_reason = (f"OPENING_COMPLETE: {sum(1 for a, n in self.pressed.items() if n >= 2)} "
                                f"button(s) paired, {self.clicked} site(s) clicked once; no further "
                                f"question at Rung 1")
        return None

    def note(self, action: Action) -> str:
        a, cell = action
        if cell is None:
            return f"opening · action {a}, press {self.pressed.get(a, 0)} of its pair"
        return f"opening · click {self.clicked} of {len(self.sites)} frame-0 sites at {cell}"
