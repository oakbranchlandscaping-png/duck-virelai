"""WEAVE · verbs — the verb alphabet and the transition signature (rung 4's arithmetic).

Canon: 02 §6 the verb alphabet; the Grounding Law (00) — every verb is a pattern over
(site, before, after). A verb names what a matched pair's own cells did; it never names why.

Transcription origin (R-C): virelai_v4/weave/edge.py:27-45 `Verb` @ oracle-v4 and
virelai_v4/weave/transition_signature.py (169 lines, read whole) — `TransitionSignature`,
`transition_signature`, `verb_from_signature`. What it proved: the class-labelled symmetric
difference is the one magnitude blind to nothing (RECOLOR included); byte-pinned across the
WO-SPLIT-AND-SHOW-01 move. The honest limit is kept verbatim: a vacated cell is `(c → None)` —
the signature of ONE pair cannot see what took the site, so departure and occlusion are
indistinguishable here. `None` is the unknown, never an invented destination.

Note the deliberate asymmetry the origin reports: `verb_from_signature` reads MOVE for any
two-sided footprint trade; the matcher (edge.py) licenses MOVE only under translation-equality
and calls the rest DEFORM. The two names are carried side by side; neither is tuned to the other.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

from virelai_golden.substrate.scan import Cell, Region


class Verb(enum.Enum):
    STILL = "STILL"          # same footprint, same class
    RECOLOR = "RECOLOR"      # same footprint, class changed
    MOVE = "MOVE"            # same class, same shape, translated
    GROW = "GROW"            # same class, now ⊃ prev
    SHRINK = "SHRINK"        # same class, now ⊂ prev
    BIRTH = "BIRTH"          # residual now-region, no prev partner
    DEATH = "DEATH"          # prev-region, no same-class partner at all
    DEFORM = "DEFORM"        # same-class partner exists but no single licensed verb
    AMBIGUOUS = "AMBIGUOUS"  # ≥2 licensed same-class candidates — a contest, handed up


@dataclass(frozen=True, eq=False)
class TransitionSignature:
    """What one matched pair's own cells did across one edge, class-labelled.

    held     {class: cells}          in both footprints, class unchanged
    changed  {(c, d): cells}         in both footprints, class c → d
    vacated  {(c, None): cells}      in prev only; destination unknowable here
    claimed  {(None, d): cells}      in now only; origin unknowable here
    """

    held: Mapping[int, FrozenSet[Cell]]
    changed: Mapping[Tuple[int, int], FrozenSet[Cell]]
    vacated: Mapping[Tuple[int, Any], FrozenSet[Cell]]
    claimed: Mapping[Tuple[Any, int], FrozenSet[Cell]]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransitionSignature):
            return NotImplemented
        return (dict(self.held) == dict(other.held) and dict(self.changed) == dict(other.changed)
                and dict(self.vacated) == dict(other.vacated)
                and dict(self.claimed) == dict(other.claimed))

    def __hash__(self) -> int:
        return hash((tuple(sorted(self.held.items())), tuple(sorted(self.changed.items())),
                     tuple(sorted(self.vacated.items())), tuple(sorted(self.claimed.items()))))

    @property
    def magnitude(self) -> int:
        """|{(cell, class)} symmetric difference|: a changed cell counts twice, a vacated or
        claimed cell once, a held cell not at all."""
        return (2 * sum(len(c) for c in self.changed.values())
                + sum(len(c) for c in self.vacated.values())
                + sum(len(c) for c in self.claimed.values()))


def transition_signature(prev: Optional[Region], now: Optional[Region]) -> Optional[TransitionSignature]:
    """The signature of one matched pair, or None when either endpoint is absent — a
    residual verb has one endpoint, so a two-sided signature is structurally impossible and
    an empty one would falsely read "nothing happened"."""
    if prev is None or now is None:
        return None
    pc, nc = prev.value, now.value
    both = prev.cells & now.cells
    held: Dict[int, FrozenSet[Cell]] = {}
    changed: Dict[Tuple[int, int], FrozenSet[Cell]] = {}
    if both:
        if pc == nc:
            held[pc] = both
        else:
            changed[(pc, nc)] = both
    vacated: Dict[Tuple[int, Any], FrozenSet[Cell]] = {}
    lost = prev.cells - now.cells
    if lost:
        vacated[(pc, None)] = lost
    claimed: Dict[Tuple[Any, int], FrozenSet[Cell]] = {}
    gained = now.cells - prev.cells
    if gained:
        claimed[(None, nc)] = gained
    return TransitionSignature(held=dict(sorted(held.items())), changed=dict(sorted(changed.items())),
                               vacated=dict(sorted(vacated.items())), claimed=dict(sorted(claimed.items())))


def verb_from_signature(sig: Optional[TransitionSignature]) -> Optional[Verb]:
    """Name a two-endpoint edge from what its cells did. None for None (a residual verb):
    the caller handles it, never defaults it."""
    if sig is None:
        return None
    if sig.vacated and sig.claimed:
        return Verb.MOVE
    if sig.claimed:
        return Verb.GROW
    if sig.vacated:
        return Verb.SHRINK
    if sig.changed:
        return Verb.RECOLOR
    return Verb.STILL
