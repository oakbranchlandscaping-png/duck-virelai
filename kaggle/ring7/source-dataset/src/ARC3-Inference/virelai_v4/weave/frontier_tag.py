"""WO_FRONTIER_TAG · B2 — the frontier labeler (the first weave module that reads belief).

A PURE RECOMPUTE over ``(InducedMap, library-belief)``. Per node, it produces the
two-axis edge labels — observed|predicted × delta|no-delta, plus ``open`` — and the
node tag ``OPEN | SEALED{confirmed | provisional + debt}`` (governing ruling: SEALED
is basis-carrying; the map REPRESENTS the audit debt and never fires).

Recompute, never stored (ruling): the labeler stores nothing on the map, mutates
nothing, writes no belief. When the library changes, re-invoking yields changed
tags — the tag is derived, not a field. The recompute test is the ruling's proof.

Belief is INJECTED as ``belief_of: Callable[[int], Optional[str]]`` returning the
action's ``OperationalBelief`` NAME (``"INERT"`` / ``"EFFECTIVE_CONDITIONAL"`` /
``"EFFECTIVE_UNCONDITIONAL"`` / ``"UNTESTED"``) or ``None`` when the library has no
``SDKAction`` for that id. This keeps the labeler decoupled from the scipy-tangled
``library`` (independently testable) while still reading the library's prediction —
the live site wires::

    belief_of = lambda aid: (lib.sdk_actions[aid].operational_belief.value
                             if aid in lib.sdk_actions else None)

The floor (``induced_map``) stays belief-free; belief enters ONLY here, above it.

Scope (ruling): KEYED/NAV, action grain. A CLICK coordinate action carries ONE
``operational_belief`, so it is tagged at whole-action grain — per-coordinate debt
is a named later rung and is never attempted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from virelai_v4.weave.induced_map import InducedMap, MapNode, NodeKey

BeliefReader = Callable[[int], Optional[str]]

# Edge-label vocabulary — the two axes plus the unpredicted frontier.
OBSERVED_DELTA = "observed-delta"          # fired here, changed the world
OBSERVED_NO_DELTA = "observed-no-delta"    # fired here, returned no delta (a self-edge)
PREDICTED_NO_DELTA = "predicted-no-delta"  # untried here; library predicts INERT (a prune)
PREDICTED_DELTA = "predicted-delta"        # untried here; library predicts EFFECTIVE (a lead)
OPEN_LABEL = "open"                        # untried here; library has no prediction (frontier)

_INERT = "INERT"
_EFFECTIVE = ("EFFECTIVE_CONDITIONAL", "EFFECTIVE_UNCONDITIONAL")


@dataclass(frozen=True)
class ActionLabel:
    action_id: int
    label: str


@dataclass(frozen=True)
class NodeTag:
    key: NodeKey
    tag: str                       # OPEN | SEALED
    basis: Optional[str]           # confirmed | provisional (None when OPEN)
    debt: Tuple[int, ...]          # untried predicted-no-delta ids a provisional seal rests on
    labels: Tuple[ActionLabel, ...]


def _observed_axes(node: MapNode) -> Dict[int, str]:
    """Per observed action id → ``'delta'`` if any out-edge left the node, else
    ``'no-delta'`` (only self-edges). A real move overrides a self-edge for the
    same action. Belief-free — reads the walked edges only."""
    axes: Dict[int, str] = {}
    for e in node.out_edges:
        a = e.label[0]
        if not isinstance(a, int):
            continue                          # non-int label (dict-frozen) — out of KEYED scope
        if e.dst != node.key:
            axes[a] = "delta"
        else:
            axes.setdefault(a, "no-delta")    # self-edge; do not overwrite an existing 'delta'
    return axes


def label_action(node: MapNode, action_id: int, belief_of: BeliefReader) -> str:
    """The five-way label for one available action at one node (observed axes from
    the map; prediction from the injected library read)."""
    observed = _observed_axes(node)
    if action_id in observed:
        return OBSERVED_DELTA if observed[action_id] == "delta" else OBSERVED_NO_DELTA
    belief = belief_of(action_id)
    if belief == _INERT:
        return PREDICTED_NO_DELTA
    if belief in _EFFECTIVE:
        return PREDICTED_DELTA
    return OPEN_LABEL                          # UNTESTED / None → unpredicted frontier


def tag_node(node: MapNode, belief_of: BeliefReader) -> NodeTag:
    """The node's frontier tag. OPEN if any available action is a lead
    (``predicted-delta``) or unpredicted (``open``). Otherwise SEALED —
    ``confirmed`` if every available action was observed here, else ``provisional``
    carrying the exact ``debt`` of untried ``predicted-no-delta`` action ids."""
    labels = tuple(
        ActionLabel(a, label_action(node, a, belief_of)) for a in node.available_actions
    )
    kinds = {lab.label for lab in labels}
    if OPEN_LABEL in kinds or PREDICTED_DELTA in kinds:
        return NodeTag(node.key, "OPEN", None, (), labels)
    debt = tuple(lab.action_id for lab in labels if lab.label == PREDICTED_NO_DELTA)
    return NodeTag(node.key, "SEALED", "confirmed" if not debt else "provisional", debt, labels)


def tag_map(m: InducedMap, belief_of: BeliefReader) -> Dict[NodeKey, NodeTag]:
    """Pure recompute over ``(map, belief)`` — one ``NodeTag`` per node, in
    first-seen order. Stores nothing; mutates neither map nor library."""
    return {k: tag_node(m.nodes[k], belief_of) for k in m.order}


# ---------------------------------------------------------------------------
# Map-level read (a read, never a gate)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FrontierSummary:
    n_nodes: int
    n_open: int
    n_sealed_confirmed: int
    n_sealed_provisional: int
    total_debt_edges: int
    n_lead: int = 0        # untried edges the library predicts EFFECTIVE (exploration points here)
    n_pruned: int = 0      # untried edges the library predicts INERT (belief let us skip)


def summarize(tags: Dict[NodeKey, NodeTag]) -> FrontierSummary:
    vals = list(tags.values())
    labels = [lab.label for t in vals for lab in t.labels]
    return FrontierSummary(
        n_nodes=len(vals),
        n_open=sum(1 for t in vals if t.tag == "OPEN"),
        n_sealed_confirmed=sum(1 for t in vals if t.tag == "SEALED" and t.basis == "confirmed"),
        n_sealed_provisional=sum(1 for t in vals if t.tag == "SEALED" and t.basis == "provisional"),
        total_debt_edges=sum(len(t.debt) for t in vals),
        n_lead=labels.count(PREDICTED_DELTA),
        n_pruned=labels.count(PREDICTED_NO_DELTA),
    )


_MODALITY_NOTE = (
    "KEYED/NAV, action grain. CLICK coordinate actions are tagged at whole-action "
    "grain — per-coordinate debt is a later rung, not represented."
)


def render_frontier(m: InducedMap, belief_of: BeliefReader) -> str:
    """The map-level frontier read: OPEN / SEALED-confirmed / SEALED-provisional
    counts + outstanding debt. all-confirmed = closed-and-checked-under-belief;
    all-SEALED-with-provisional = closed-under-belief + named backlog."""
    s = summarize(tag_map(m, belief_of))
    if s.n_open == 0 and s.n_sealed_provisional == 0:
        read = "world closed AND checked under current belief (zero unwalked belief)"
    elif s.n_open == 0:
        read = "closed under belief + named audit backlog (provisional seals carry debt)"
    else:
        read = "frontier open — exploration points at the OPEN nodes"
    return "\n".join([
        f"FRONTIER TAG — {s.n_nodes} nodes: {s.n_open} OPEN, "
        f"{s.n_sealed_confirmed} SEALED/confirmed, {s.n_sealed_provisional} SEALED/provisional "
        f"· {s.total_debt_edges} outstanding debt edge(s)",
        f"  prediction: {s.n_lead} predicted-delta (lead — exploration points here) · "
        f"{s.n_pruned} predicted-no-delta (pruned — belief let us skip)",
        f"  read: {read}",
        f"  scope: {_MODALITY_NOTE}",
    ])
