"""WO_WEAVE_S3_THREAD_AND_WEAVE · thread edges into ### worldlines.

Consumes the pairwise ``weave_edge`` verdicts and threads them into persistent
``Worldline`` objects (the ### objects): a visual object followed across a window
by its continue-verb stitches. This is R2a's synthesis — visual objects woven into
persistent ### by cell-delta, verbs on every stitch, residuals honest.

Pure over the atoms + ``edge.py``: stdlib only. No perception, no belief, no scored
contest resolution and no SPLIT/MERGE (Step 4) — a split terminates a worldline as
AMBIGUOUS and its products start as BIRTH worldlines.

Determinism: worldlines seed and number from the visual-object sort, so the woven
set (and the ### numbers) are independent of each node's region list order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple

from virelai_v4.weave.edge import weave_edge, Verb, WeaveEdge

# Verbs that continue an existing worldline (prev extends to now).
_CONTINUE = frozenset({Verb.STILL, Verb.RECOLOR, Verb.MOVE, Verb.GROW, Verb.SHRINK})


@dataclass(frozen=True)
class Worldline:
    """One persistent ### object: an ordered trail of (node_index, region) states
    and the stitch-verbs between them. ``id`` is the ###NNN number."""

    id: int
    steps: Tuple[Tuple[int, Any], ...]      # ((node_index, RegionClay), …)
    edges: Tuple[WeaveEdge, ...]            # one per step transition (len = len(steps)-1)

    @property
    def first_node(self) -> int:
        return self.steps[0][0]

    @property
    def first_region(self) -> Any:
        return self.steps[0][1]

    @property
    def verbs(self) -> Tuple[Verb, ...]:
        return tuple(e.verb for e in self.edges)


def region_at(worldline: Worldline, node_index: int):
    """The ``RegionClay`` this worldline holds AT ``node_index`` — the region in the
    step whose ``node_index`` matches — or ``None`` if the ### is not present at that
    node. Keys off the requested frame, NEVER ``first_region`` (which would print the
    footprint from wherever the ### first appeared). ``None`` is an honest signal, not
    a fallback."""
    for (n, region) in worldline.steps:
        if n == node_index:
            return region
    return None


def _visual_order(regions) -> List[Any]:
    return sorted(regions, key=lambda r: (r.cell_count, r.class_id, r.anchor))


class _Builder:
    __slots__ = ("steps", "edges")

    def __init__(self, node_index, region):
        self.steps = [(node_index, region)]
        self.edges = []


def weave_window(cuts_in_window) -> List[Worldline]:
    """Thread the window's cuts into numbered ### worldlines.

    Window-start regions each seed a worldline (initial state, not BIRTH). Across
    each adjacent pair, continue-verb edges extend the prev's worldline to now;
    BIRTH seeds a new worldline mid-window; DEATH/DEFORM/AMBIGUOUS terminate (no
    continuation). Numbered by first-appearance node ascending, ties by the
    visual-object sort — stable across the window.
    """
    if not cuts_in_window:
        return []

    builders: List[_Builder] = []
    c0 = cuts_in_window[0]
    active = {}                                  # region@current-node -> builder
    for r in _visual_order(c0.regions):
        b = _Builder(c0.node_index, r)
        builders.append(b)
        active[r] = b

    for t in range(len(cuts_in_window) - 1):
        ct, cn = cuts_in_window[t], cuts_in_window[t + 1]
        next_active = {}
        for e in weave_edge(ct.regions, cn.regions):
            if e.verb in _CONTINUE:
                b = active.get(e.prev)
                if b is None:                    # defensive: prev not tracked
                    b = _Builder(ct.node_index, e.prev)
                    builders.append(b)
                b.steps.append((cn.node_index, e.now))
                b.edges.append(e)
                next_active[e.now] = b
            elif e.verb is Verb.BIRTH:
                b = _Builder(cn.node_index, e.now)
                builders.append(b)
                next_active[e.now] = b
            # DEATH / DEFORM / AMBIGUOUS: terminate — no continuation.
        active = next_active

    # NUMBERING — first-appearance node asc, ties by (|cells|, class_id, anchor).
    ordered = sorted(
        builders,
        key=lambda b: (b.steps[0][0], b.steps[0][1].cell_count,
                       b.steps[0][1].class_id, b.steps[0][1].anchor),
    )
    return [
        Worldline(id=i + 1, steps=tuple(b.steps), edges=tuple(b.edges))
        for i, b in enumerate(ordered)
    ]


def window_edges(cuts_in_window) -> List[Tuple[int, int, WeaveEdge]]:
    """Flatten every ``weave_edge`` verdict across the window as
    ``(from_node, to_node, edge)`` — the substrate for residual/decorrelation
    reporting. BIRTH is located at ``to_node``; DEATH/DEFORM/AMBIGUOUS at
    ``from_node``."""
    out: List[Tuple[int, int, WeaveEdge]] = []
    for t in range(len(cuts_in_window) - 1):
        ct, cn = cuts_in_window[t], cuts_in_window[t + 1]
        for e in weave_edge(ct.regions, cn.regions):
            out.append((ct.node_index, cn.node_index, e))
    return out
