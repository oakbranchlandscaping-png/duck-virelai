"""WO_VERB_FROM_TRANSITIONS_01 · the transition signature — rung four's arithmetic.

Extracted verbatim from ``weave/edge.py`` by WO-SPLIT-AND-SHOW-01. That module's own
docstring calls it "the pairwise edge-matcher"; the arithmetic that NAMES an edge is a
different concern from the geometry that JOINS one, and after the verb rung landed both
lived in the same file. The split is now structural as well as functional. Nothing here
computes differently than it did in ``edge.py`` — this file is a move, and
``tests/weave/test_split_and_show.py`` pins the rendered output byte-identical across it.

WO-VERB-FROM-TRANSITIONS-01 · the transition signature — rung four's arithmetic

The concept is already specified in-tree, verbatim, in
`weave/coupling.py::_change_magnitude`'s docstring: "the symmetric difference of the
class-labelled cell sets, {(cell, class_id)} ... A plain cell symmetric difference is 0
under RECOLOR (same footprint => empty difference), reproducing `cell_count`'s blindness
sideways. Labelling by the region's class makes a recoloured cell differ from itself."
That docstring then says "Closed form, so no set is built" and computes cardinalities
per verb. THIS IS THAT OBJECT, BUILT. PORT, not INVENT — the derivation was specified;
only its materialization was missing.

MEMBERS, NOT COUNTS. Counts are derivable from members; members are not recoverable
from counts — the same reasoning `WorldDelta.transition_index` was ruled on
(RULING_OBSERVERS_INTEGRATOR_v1 Clause A). `SPEC_LEXICON_LIBRARY` §5's growth rule
("a residual recurring with a stable signature earns a named verb") cannot fire on a
count; it needs a pattern.

THE HONEST LIMIT (carried into this WO's return, §9.1): this is DERIVED over one pair's
own cells, NOT a read of `SPEC_DELTA_LEDGER`'s canonical catalog. A vacated cell records
`(c -> None)` — the signature cannot see what took the site, so departure and occlusion
are indistinguishable to it. `WorldDelta` is confirmed unreachable from `weave/` (this
WO's premise P6: no weave file imports it; `ledger_from_capture` builds none; `NodeCut`
carries `regions` and no transitions; it is constructed only in `library/`). The limit is
structural at this rung, not an oversight, and `None` is the honest unknown — never an
invented destination.

Stdlib only. No perception, no belief, no library, no context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

from virelai_v4.weave.edge import Verb

Cell = Tuple[int, int]


@dataclass(frozen=True)
class TransitionSignature:
    """What one matched pair's own cells did across one edge, class-labelled.

    Four groups, each mapping a transition key to its MEMBER CELLS:

      held     ``{class_id: cells}``        — in both footprints, class unchanged
      changed  ``{(c, d): cells}``          — in both footprints, class c -> d
      vacated  ``{(c, None): cells}``       — in prev only; destination unknowable here
      claimed  ``{(None, d): cells}``       — in now only; origin unknowable here

    Deterministic: every group is ordered by transition key, and each member set is a
    ``frozenset`` compared by value — two builds over one pair are equal objects."""

    held: "Mapping[int, FrozenSet[Cell]]"
    changed: "Mapping[Tuple[int, int], FrozenSet[Cell]]"
    vacated: "Mapping[Tuple[int, Any], FrozenSet[Cell]]"
    claimed: "Mapping[Tuple[Any, int], FrozenSet[Cell]]"

    def __eq__(self, other) -> bool:
        if not isinstance(other, TransitionSignature):
            return NotImplemented
        return (dict(self.held) == dict(other.held)
                and dict(self.changed) == dict(other.changed)
                and dict(self.vacated) == dict(other.vacated)
                and dict(self.claimed) == dict(other.claimed))

    def __hash__(self) -> int:
        return hash((tuple(sorted(self.held.items())),
                     tuple(sorted(self.changed.items())),
                     tuple(sorted(self.vacated.items())),
                     tuple(sorted(self.claimed.items()))))

    @property
    def magnitude(self) -> int:
        """|{(cell, class_id)} symmetric difference| — the cardinality
        `coupling.py::_change_magnitude`'s docstring specifies. A changed cell contributes
        BOTH labels (it differs from itself); a vacated or claimed cell contributes one;
        a held cell contributes none."""
        return (2 * sum(len(c) for c in self.changed.values())
                + sum(len(c) for c in self.vacated.values())
                + sum(len(c) for c in self.claimed.values()))


def transition_signature(prev: Any, now: Any) -> Optional[TransitionSignature]:
    """The signature of one matched pair, or ``None`` when either endpoint is absent.

    A residual verb (BIRTH/DEATH, and the AMBIGUOUS/DEFORM `weave_edge` emits) carries one
    endpoint only, so a two-sided signature is structurally impossible for it. ``None`` is
    the honest answer; an empty signature would read as "nothing happened," which is a
    different and false claim."""
    if prev is None or now is None:
        return None
    pc, nc = prev.class_id, now.class_id
    pcells, ncells = frozenset(prev.cells), frozenset(now.cells)
    both = pcells & ncells

    held: Dict[int, FrozenSet[Cell]] = {}
    changed: Dict[Tuple[int, int], FrozenSet[Cell]] = {}
    if both:
        if pc == nc:
            held[pc] = both
        else:
            changed[(pc, nc)] = both

    vacated: Dict[Tuple[int, Any], FrozenSet[Cell]] = {}
    lost = pcells - ncells
    if lost:
        vacated[(pc, None)] = lost

    claimed: Dict[Tuple[Any, int], FrozenSet[Cell]] = {}
    gained = ncells - pcells
    if gained:
        claimed[(None, nc)] = gained

    # Ordered by transition key — determinism is a §5 constraint, not a nicety.
    return TransitionSignature(
        held=dict(sorted(held.items())),
        changed=dict(sorted(changed.items())),
        vacated=dict(sorted(vacated.items())),
        claimed=dict(sorted(claimed.items())),
    )


def verb_from_signature(sig: Optional[TransitionSignature]) -> Optional[Verb]:
    """Name a two-endpoint edge from what its cells did, not from the geometry that
    licensed the join.

    This is the split `edge.py`'s own docstring names as one act ("match + classify as one
    act"): the matcher still chooses WHICH regions join, by the same three passes in the
    same order. Only the NAME becomes a reading. The vocabulary does not change.

    The readings, in the order the cascade itself licenses them:

      no vacated, no claimed, no changed  -> STILL     (footprint held, class held)
      no vacated, no claimed, changed     -> RECOLOR   (footprint held, class moved)
      vacated and claimed                 -> MOVE      (footprint traded on both sides)
      claimed only                        -> GROW      (footprint gained, none lost)
      vacated only                        -> SHRINK    (footprint lost, none gained)

    Returns ``None`` for a ``None`` signature (a residual verb), which the caller must
    handle rather than defaulting — §5's no-catch-all discipline, inherited from
    `_change_magnitude`'s own ("a default is what shipped WO-W2-B-02's regression").

    NOTE the deliberate asymmetry with the cascade: MOVE here is any two-sided footprint
    trade, whereas the matcher licenses MOVE only under translation-equality and calls
    anything else DEFORM. That is exactly the disagreement this rung exists to make
    visible, and it is a finding to report — never a reason to tune either side to match
    the other. `weave_edge` therefore keeps the cascade's verb as the emitted one and
    carries the signature beside it; a reader that wants the arithmetic name asks for it."""
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
