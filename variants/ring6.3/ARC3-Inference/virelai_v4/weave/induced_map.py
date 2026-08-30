"""WO_INDUCED_MAP · the induced map — the walk merged into a directed state graph.

A pure, offline read over the CAPTURE log. It consumes ``FrameRecordLog.records``
(or any record-like exposing ``.node_index``, ``.layers``, ``.edge``,
``.full_reset``) and induces a directed graph in which:

  - a NODE is one unique SETTLED VISIBLE grid state (keyed on ``layers[-1]``);
  - an EDGE is one walked, directed transition the log actually recorded —
    ``node[i-1] --edge[i]--> node[i]`` for every record that continues a life.

It derives the graph and its geometry (BFS distance-from-root layering, SCC
condensation) and reads its shape (modality statistics). It invents no edge and
reverses none: the only edges are the transitions the recorder wrote.

NODE-KEY — RULING F2 (settled visible grid)
-------------------------------------------
The node is keyed on the SETTLED VISIBLE grid: a sha256 over ``record.layers[-1]``,
the last (settled) layer of the captured stack. ``layered_hash`` is retained on
the record as the future animation-digest source but is NEVER the node key —
keying on it covers the whole sub-frame sequence and so splits visibly-identical
nodes on transient animation (the animation-folding defect this design retires).
The key is injected via ``key_fn`` (default = the settled-grid hash) so a later
ruling remains a one-line change. This is a distinct artifact from
``capture.clay.NodeCut``: clay's ``node_map`` is the visible-address path
substrate; this is the exact-identity walk graph.

Fences (each a build-failure if broken):
  - Interpretation-free / dependency-light: imports STDLIB ONLY. Nothing from
    ``library/`` (incl. ``nav_*``), ``targeting/``, ``captain``, ``perception/``,
    ``scipy``, or ``arcengine``. It reads record-likes; it writes no belief and
    mutates no log.
  - Walked-only edges (I2): an edge is added only for a record that carries a
    real inbound edge and continues a life. Zero phantom, zero inferred-reverse.
  - Settled-grid identity (I1): distinct ``layers[-1]`` ⇒ distinct node;
    re-convergence is visible as an in-degree ≥ 2 hub.
  - Game-free: keys on opaque grid hashes and abstract ``(action_id, target)``
    labels. No world name, color, position, or mechanic has any legal place here.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Tuple

# A node's identity key: the settled-visible-grid hash, opaque. ``str`` by construction.
NodeKey = str
# An edge label is the composite inbound EdgeKey the recorder wrote:
# (action_id, target). ``target`` is None for a keyed action, a coordinate
# (a hashable tuple) for a coordinate action. A walked edge never carries None.
Label = Tuple[int, Any]


def _default_key(record: Any) -> NodeKey:
    """Node identity = the SETTLED VISIBLE grid: a sha256 over ``record.layers[-1]``,
    the last (settled) layer of the captured stack (RULING F2).

    Animation lives in the earlier layers and in the retained ``layered_hash``
    (kept as the future animation-digest source, never the key). Keying on
    ``layered_hash`` covers the whole sub-frame sequence, so it splits
    visibly-identical nodes on transient animation — folding the fork-witness
    into identity. Keying on the settled grid retires that animation-folding
    defect: distinct settled grids ⇒ distinct nodes; identical settled grids ⇒
    one node, whatever animation preceded them."""
    return hashlib.sha256(repr(record.layers[-1]).encode("utf-8")).hexdigest()


def _freeze_label(label: Any) -> Any:
    """Coerce an edge label to a HASHABLE form at the map's OWN boundary — and
    SAY SO WHEN IT FIRES.

    THE ESCALATION THIS DOCSTRING USED TO CARRY IS DISCHARGED. It read:

        "Turning the platform object into a clean (action_id, target) EdgeKey is
         a committed-capture concern (the load_capture <-> _norm_key contract),
         escalated to CE — never done from this seat."

    That diagnosis was exactly right — the mechanism, the dict, the consequence
    ("blows edges.add"), the correct fix, the correct site, the correct owner,
    and the correct altitude. It sat in a docstring for months and never reached
    CE. WO-A2-03 re-derived the whole finding from scratch, by executing
    load_capture against a real recording, and fixed it at the site named here:
    load_capture now routes action_input through _parse_action, so an offline
    edge is an honest (0, None) — typed and natively hashable.

    An escalation that lives only in a docstring is a recorded non-escalation.
    The register is the transport; this text is a pointer to it, never the thing
    itself. See: DEBT_LEDGER_CLEANING_LANE / the A2 returns.

    WHY THIS FUNCTION STAYS, AND WHY IT IS NOW LOUD. Post-A2-03 it should never
    fire: live labels come from ctx.last_action_id (int) or a composite tuple,
    and offline labels are typed by _parse_action. Both are hashable by
    construction. So a fire means an unhashable label reached this layer from a
    source neither path covers — new information, not a nuisance.

    A normalizer that silently repairs its input is the door-swallowing pattern
    at the map layer: it converts "something upstream is wrong" into "the map
    rendered fine." That is what let the dict edge run for months — and it cost
    more than a crash would have. Pre-fix, every offline label froze to
    (("__dict__",), ...), which is not an int, which meant untried_actions'
    `isinstance(e.label[0], int)` filter (:232) matched NOTHING: every declared
    action read as untried, on every offline render, silently. The shim kept the
    map running and hollowed out its edge labels.

    It still freezes — never raise inside an instrument — but it EMITS. Already-
    hashable labels pass byte-identical, so there is no signature drift on the
    directional case and no cost on any path that was already correct."""
    if isinstance(label, dict):
        # LOUD GUARD (WO-A2-06). Unreachable from either committed path; if this
        # prints, the escalation above has a NEW subject and belongs in the
        # register, not in this docstring. Emitted at the BOUNDARY only — the
        # recursion below runs through _freeze, which is silent, so one bad
        # label is one line, not one per nested key.
        print(
            "[induced_map] A2-06 GUARD: an unhashable dict reached the edge "
            "label boundary. Both committed sources are typed by construction "
            "(live: ctx.last_action_id; offline: _parse_action). Freezing to "
            "keep the map running — but the label carries no action information "
            "and untried_actions (:232) will read every action as untried at "
            "this node. Raise it to the register.",
            flush=True,
        )
    return _freeze(label)


def _freeze(label: Any) -> Any:
    """The recursion. Silent by design — _freeze_label owns the emission at the
    boundary so one unhashable label costs one line, not one per nested key."""
    if isinstance(label, dict):
        items = tuple(sorted(
            ((k, _freeze(v)) for k, v in label.items()),
            key=lambda kv: repr(kv[0]),
        ))
        return (("__dict__",), items)
    if isinstance(label, (list, tuple)):
        return tuple(_freeze(x) for x in label)
    return label


# ---------------------------------------------------------------------------
# The graph atoms
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalkedEdge:
    """One directed, traversal-backed transition. Frozen and hashable so the
    edge set dedupes identical re-walked transitions (the ground of I3)."""

    src: NodeKey
    dst: NodeKey
    label: Label   # never None — a walked edge always carries its action


@dataclass
class MapNode:
    """One unique whole-grid state and its walked neighbourhood."""

    key: NodeKey
    first_index: int
    arrivals: List[int] = field(default_factory=list)   # every node_index landing here
    is_root: bool = False                               # ever a life-root (edge=None)
    in_edges: set = field(default_factory=set)          # of WalkedEdge
    out_edges: set = field(default_factory=set)         # of WalkedEdge
    # The platform's DECLARED action set at this node — a GIVEN, not belief (kept
    # belief-free; the floor never reads the library). First-seen at node creation;
    # verified stable across arrivals on real vc33 (CLICK) + ls20 (NAV) recordings.
    available_actions: Tuple[int, ...] = ()

    @property
    def in_degree(self) -> int:
        return len(self.in_edges)

    @property
    def out_degree(self) -> int:
        return len(self.out_edges)

    @property
    def is_hub(self) -> bool:
        """Re-convergence witness (I1): reached by ≥ 2 distinct walked transitions."""
        return self.in_degree >= 2


@dataclass
class InducedMap:
    """The directed walk graph: unique-state nodes, walked-only edges, roots."""

    nodes: Dict[NodeKey, MapNode]
    edges: FrozenSet[WalkedEdge]
    roots: Tuple[NodeKey, ...]
    order: Tuple[NodeKey, ...]          # first-seen order, for stable rendering

    def signature(self) -> Tuple[FrozenSet[NodeKey], FrozenSet[WalkedEdge]]:
        """The graph's identity, independent of arrival counts / indices — the
        (node-set, edge-set) pair. Two logs induce the SAME map iff their
        signatures are equal. This is the object I3 holds invariant."""
        return (frozenset(self.nodes.keys()), self.edges)

    @property
    def hubs(self) -> Tuple[MapNode, ...]:
        return tuple(n for n in self.nodes.values() if n.is_hub)


# ---------------------------------------------------------------------------
# The merge — the one merge
# ---------------------------------------------------------------------------

def build_induced_map(
    records: Iterable[Any], *, key_fn: Callable[[Any], NodeKey] = _default_key
) -> InducedMap:
    """Fold the capture log into the induced map. Deterministic and idempotent
    over the (node, edge) signature: replaying an already-recorded route adds no
    node and no edge, because both are set-keyed on hash / (src, dst, label).

    A record is a LIFE-ROOT iff its ``edge`` is None (the recorder's contract:
    the first node of each life carries edge=None) or it flags ``full_reset``.
    A root has no walked in-edge. Any other record continues its life: it carries
    a real inbound edge, and the walked transition is
    ``prev_node --edge--> this_node`` (I2 — the only edge we ever add)."""
    recs = sorted(records, key=lambda r: int(r.node_index))

    nodes: Dict[NodeKey, MapNode] = {}
    order: List[NodeKey] = []
    edges: set = set()
    roots: List[NodeKey] = []
    root_set: set = set()

    prev_key: Optional[NodeKey] = None

    for r in recs:
        k = key_fn(r)
        node = nodes.get(k)
        if node is None:
            node = MapNode(
                key=k,
                first_index=int(r.node_index),
                # First-seen platform given; stable across arrivals (verified).
                available_actions=tuple(
                    int(a) for a in (getattr(r, "available_actions", ()) or ())
                ),
            )
            nodes[k] = node
            order.append(k)
        node.arrivals.append(int(r.node_index))

        label = r.edge  # (action_id, target) or None
        is_root = label is None or bool(getattr(r, "full_reset", False))

        if is_root:
            node.is_root = True
            if k not in root_set:
                root_set.add(k)
                roots.append(k)
        elif prev_key is not None:
            # A walked transition: previous record's state → this state.
            edge = WalkedEdge(src=prev_key, dst=k, label=_freeze_label(label))  # type: ignore[arg-type]
            edges.add(edge)
            node.in_edges.add(edge)
            nodes[prev_key].out_edges.add(edge)

        prev_key = k

    return InducedMap(
        nodes=nodes,
        edges=frozenset(edges),
        roots=tuple(roots),
        order=tuple(order),
    )


def untried_actions(node: MapNode) -> Tuple[int, ...]:
    """The node's DECLARED actions that were never walked FROM this node — the
    map's half of the frontier tag (``available − observed``). Observed action ids
    are the integer ``label[0]`` of the node's out-edges (a self-edge counts as
    observed — the action was fired, it just returned no delta). Belief-free: reads
    only the platform given and the walked edges. Preserves the declared order."""
    observed = {e.label[0] for e in node.out_edges if isinstance(e.label[0], int)}
    return tuple(a for a in node.available_actions if a not in observed)


# ---------------------------------------------------------------------------
# Route replay — the I3 operator, made explicit
# ---------------------------------------------------------------------------

def replay_route(
    records: Iterable[Any],
    start: int,
    end: int,
    *,
    key_fn: Callable[[Any], NodeKey] = _default_key,
) -> List[Any]:
    """Return ``records`` with the recorded contiguous route ``[start, end]``
    re-walked as a FRESH LIFE appended to the log. This is the literal meaning of
    "re-walk a recorded route": reset, then repeat the same actions producing the
    same states.

    Each replayed step is a ``dataclasses.replace`` copy of the REAL route record,
    so it carries EVERY field — thus any ``key_fn`` (settled-visible-grid or
    otherwise) resolves identically through replay (RULING F2 · key-fn-agnostic).
    The first step is forced to a root (``edge=None``, ``full_reset=True``) — you
    re-enter the route by resetting — and every subsequent step keeps its original
    edge. Because the route was walked contiguously in the original life, every
    replayed transition already exists; the induced map's signature must not
    change (I3).

    ``key_fn`` is accepted for API stability; replay no longer uses it to
    synthesize keys — the replace-copies carry their own identity fields."""
    recs = sorted(records, key=lambda r: int(r.node_index))
    route = recs[start:end + 1]
    if not route:
        return list(recs)

    next_index = max(int(r.node_index) for r in recs) + 1
    appended: List[Any] = list(recs)
    for offset, r in enumerate(route):
        if offset == 0:
            appended.append(replace(r, edge=None, full_reset=True, node_index=next_index))
        else:
            appended.append(replace(r, node_index=next_index + offset))
    return appended


def is_idempotent_under_replay(
    records: Iterable[Any],
    routes: Iterable[Tuple[int, int]],
    *,
    key_fn: Callable[[Any], NodeKey] = _default_key,
) -> bool:
    """I3 grader: for every ``(start, end)`` route, replaying it as a fresh life
    leaves the induced map's signature unchanged. Pure; grades offline over the
    captured log, never a live decision."""
    base = build_induced_map(records, key_fn=key_fn).signature()
    for (start, end) in routes:
        replayed = replay_route(records, start, end, key_fn=key_fn)
        if build_induced_map(replayed, key_fn=key_fn).signature() != base:
            return False
    return True


# ---------------------------------------------------------------------------
# Geometry — BFS layering + SCC condensation (R2)
# ---------------------------------------------------------------------------

# The RESET action is a harness TELEPORT (forced at GAME_OVER or chosen mid-life),
# not a world transition. Its edge carries action_id == GameAction.RESET.value — a
# stable platform constant (== 0; confirmed at the enum and the captain's RESET
# filter). It is passed in as a module constant, NEVER imported: induced_map stays
# game-free and agent-decoupled (no ``import GameAction``, per the decorrelation
# fence). A universal reset back-edge to root would otherwise close every walk into
# one giant SCC and hide the irreversibility skeleton — the exact failure the
# preview #3 directed-state-graph agent (arXiv:2512.24156) lost score to, and the
# one our live ls20 map reproduced (one component, all members).
RESET_ACTION_ID: int = 0


def non_reset_edges(m: "InducedMap", reset_id: int = RESET_ACTION_ID) -> "FrozenSet[WalkedEdge]":
    """The walked edges MINUS the reset teleports (``label[0] == reset_id``). The
    geometry pass runs over this subset so the reset back-edge cannot short-circuit
    the skeleton. ``m.edges`` and the raw grain are untouched — reset stays visible
    there. (Keys on the live log's clean ``(0, target)`` reset label; the abandoned
    recording-file path, whose labels carry an undecoded dict, is out of scope.)"""
    return frozenset(e for e in m.edges if e.label[0] != reset_id)


def _adjacency(m: InducedMap, edges=None) -> Dict[NodeKey, List[NodeKey]]:
    """Adjacency over an edge set (default ``m.edges``). The geometry passes hand
    in ``non_reset_edges(m)``; the raw grain uses the full set via ``m.edges``."""
    adj: Dict[NodeKey, List[NodeKey]] = {k: [] for k in m.nodes}
    for e in (m.edges if edges is None else edges):
        adj[e.src].append(e.dst)
    return adj


def bfs_layers(m: InducedMap, *, edges=None) -> Dict[NodeKey, int]:
    """Distance-from-root layering: multi-source BFS from every life-root. By
    default it runs over the NON-RESET walked edges, so distance measures WALKED
    distance, not teleport distance — a reset back-edge would otherwise place a
    deep node at L1 from root. Roots sit at layer 0. A node unreachable without a
    reset is reported as layer -1 — an honest finding, not a bug. Pass
    ``edges=m.edges`` to include resets."""
    adj = _adjacency(m, non_reset_edges(m) if edges is None else edges)
    layer: Dict[NodeKey, int] = {}
    dq: deque = deque()
    for r in m.roots:
        if r not in layer:
            layer[r] = 0
            dq.append(r)
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in layer:
                layer[v] = layer[u] + 1
                dq.append(v)
    for k in m.nodes:
        layer.setdefault(k, -1)
    return layer


def strongly_connected_components(m: InducedMap, *, edges=None) -> List[FrozenSet[NodeKey]]:
    """Iterative Tarjan over the directed graph. Cycles in the walk — walking
    back and forth between states — surface as multi-member components; acyclic
    exploration yields singletons. Iterative to stay safe on long routes.

    By default it runs over the NON-RESET edges, so a reset teleport back to root
    cannot collapse the whole walk into one component. Pass ``edges=m.edges`` to
    include resets (e.g. to reproduce the pre-filter fold)."""
    adj = _adjacency(m, non_reset_edges(m) if edges is None else edges)
    index_of: Dict[NodeKey, int] = {}
    lowlink: Dict[NodeKey, int] = {}
    on_stack: set = set()
    stack: List[NodeKey] = []
    comps: List[FrozenSet[NodeKey]] = []
    counter = 0

    for root in m.order:
        if root in index_of:
            continue
        # work stack of (node, iterator-position)
        work: List[Tuple[NodeKey, int]] = [(root, 0)]
        while work:
            node, i = work[-1]
            if i == 0:
                index_of[node] = counter
                lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            neighbours = adj[node]
            if i < len(neighbours):
                work[-1] = (node, i + 1)
                w = neighbours[i]
                if w not in index_of:
                    work.append((w, 0))
                elif w in on_stack:
                    lowlink[node] = min(lowlink[node], index_of[w])
            else:
                if lowlink[node] == index_of[node]:
                    members: List[NodeKey] = []
                    while True:
                        w = stack.pop()
                        on_stack.discard(w)
                        members.append(w)
                        if w == node:
                            break
                    comps.append(frozenset(members))
                work.pop()
                if work:
                    parent = work[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[node])
    return comps


@dataclass(frozen=True)
class CondensedNode:
    comp_id: int
    members: FrozenSet[NodeKey]
    is_cycle: bool     # a genuine loop: >1 member, or a single member with a self-edge


@dataclass(frozen=True)
class Condensation:
    components: Tuple[CondensedNode, ...]
    edges: FrozenSet[Tuple[int, int]]        # (src_comp_id, dst_comp_id), self-loops dropped
    member_of: Dict[NodeKey, int]


def condense(m: InducedMap, *, edges=None) -> Condensation:
    """The SCC-condensed DAG: each strongly-connected component becomes one
    super-node; inter-component walked edges become the DAG's edges. Intra-
    component (cycle) edges are absorbed. This is the condensed-geometry grain.

    Reset teleports are excluded by default (the components, the self-loop cycle
    test, and the DAG edges all run over ``non_reset_edges``), so the skeleton is
    the irreversibility structure, not the reset-folded blob. Pass ``edges=m.edges``
    to include resets."""
    e_set = non_reset_edges(m) if edges is None else edges
    comps = strongly_connected_components(m, edges=e_set)
    member_of: Dict[NodeKey, int] = {}
    for cid, members in enumerate(comps):
        for k in members:
            member_of[k] = cid

    self_looped: set = {e.src for e in e_set if e.src == e.dst}
    cnodes = tuple(
        CondensedNode(
            comp_id=cid,
            members=members,
            is_cycle=(len(members) > 1) or bool(members & self_looped),
        )
        for cid, members in enumerate(comps)
    )

    dag_edges: set = set()
    for e in e_set:
        a, b = member_of[e.src], member_of[e.dst]
        if a != b:
            dag_edges.add((a, b))

    return Condensation(components=cnodes, edges=frozenset(dag_edges), member_of=member_of)


# ---------------------------------------------------------------------------
# Modality read (R3) — a read, never a gate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MapStats:
    n_nodes: int
    n_edges: int
    n_roots: int
    n_hubs: int
    max_out_degree: int
    mean_out_degree: float
    distinct_labels: int
    distinct_targets: int          # distinct non-None target values (coordinate space)
    coordinate_targeted: bool      # any edge whose target is not None
    density: float                 # edges / nodes
    n_components: int
    max_layer: int


def map_stats(m: InducedMap) -> MapStats:
    """Shape statistics of the induced map. Game-free by construction — it reads
    degrees, label cardinality, and target cardinality, and never inspects what
    any hash or coordinate *means*. The modality difference (dense/small-fan vs
    wide/sparse) falls out of these numbers; the caller reads it, nothing gates."""
    n_nodes = len(m.nodes)
    n_edges = len(m.edges)
    out_degs = [n.out_degree for n in m.nodes.values()] or [0]
    labels = {e.label for e in m.edges}
    targets = {e.label[1] for e in m.edges if e.label[1] is not None}
    layers = bfs_layers(m)
    comps = strongly_connected_components(m)
    return MapStats(
        n_nodes=n_nodes,
        n_edges=n_edges,
        n_roots=len(m.roots),
        n_hubs=len(m.hubs),
        max_out_degree=max(out_degs),
        mean_out_degree=(sum(out_degs) / len(out_degs)) if out_degs else 0.0,
        distinct_labels=len(labels),
        distinct_targets=len(targets),
        coordinate_targeted=bool(targets),
        density=(n_edges / n_nodes) if n_nodes else 0.0,
        n_components=len(comps),
        max_layer=max(layers.values()) if layers else -1,
    )


# ---------------------------------------------------------------------------
# Renderers — human-legible, two grains (R1)
# ---------------------------------------------------------------------------

def _fmt_label(label: Label) -> str:
    action_id, target = label
    return f"a{action_id}" if target is None else f"a{action_id}@{target}"


def render_raw_grain(m: InducedMap) -> str:
    """Grain 1 — the raw fidelity floor: every unique whole-grid state as its own
    node, every walked edge, nothing collapsed. The exact-identity graph (I1/I2)."""
    layers = bfs_layers(m)
    lines = [
        f"INDUCED MAP · RAW GRAIN (fidelity floor) — {len(m.nodes)} nodes, "
        f"{len(m.edges)} walked edges, {len(m.roots)} root(s), "
        f"{len(m.hubs)} hub(s) (in-degree ≥ 2)"
    ]
    for k in m.order:
        n = m.nodes[k]
        tags = []
        if n.is_root:
            tags.append("root")
        if n.is_hub:
            tags.append(f"HUB×{n.in_degree}")
        tag = f" [{', '.join(tags)}]" if tags else ""
        lines.append(
            f"  node [{k[:8]}] · L{layers.get(k, -1)} · "
            f"in {n.in_degree} / out {n.out_degree} · seen {len(n.arrivals)}×{tag}"
        )
        for e in sorted(n.out_edges, key=lambda x: (x.label[0], str(x.label[1]))):
            lines.append(f"      -{_fmt_label(e.label)}→ [{e.dst[:8]}]")
    return "\n".join(lines)


def render_condensed_grain(m: InducedMap) -> str:
    """Grain 2 — the condensed geometry: SCC super-nodes over BFS layers, the
    walk's skeleton with its cycles absorbed. Root's pocket at the source."""
    cond = condense(m)
    layers = bfs_layers(m)
    comp_layer: Dict[int, int] = {}
    for k, cid in cond.member_of.items():
        lv = layers.get(k, -1)
        if cid not in comp_layer or (lv >= 0 and lv < comp_layer[cid]):
            comp_layer[cid] = lv
    n_cycles = sum(1 for c in cond.components if c.is_cycle)
    lines = [
        f"INDUCED MAP · CONDENSED GRAIN (SCC / geometry) — "
        f"{len(cond.components)} components ({n_cycles} cyclic), "
        f"{len(cond.edges)} DAG edges · reset teleports excluded from geometry"
    ]
    for c in sorted(cond.components, key=lambda c: (comp_layer.get(c.comp_id, -1), c.comp_id)):
        kind = "CYCLE" if c.is_cycle else "state"
        rep = sorted(c.members)[0]
        lines.append(
            f"  C{c.comp_id} · {kind} · L{comp_layer.get(c.comp_id, -1)} · "
            f"{len(c.members)} member(s) · rep [{rep[:8]}]"
        )
    outs: Dict[int, List[int]] = {}
    for (a, b) in sorted(cond.edges):
        outs.setdefault(a, []).append(b)
    for a in sorted(outs):
        lines.append(f"  C{a} → {', '.join('C' + str(b) for b in sorted(outs[a]))}")
    return "\n".join(lines)


def render_stats(s: MapStats) -> str:
    """The modality read block — a read, never a gate."""
    fan = "wide/sparse (coordinate)" if s.coordinate_targeted else "small-fan (keyed)"
    return "\n".join([
        "MODALITY READ (a read, never a gate):",
        f"  nodes {s.n_nodes} · edges {s.n_edges} · density {s.density:.2f} · "
        f"roots {s.n_roots} · hubs {s.n_hubs}",
        f"  out-fan: max {s.max_out_degree} · mean {s.mean_out_degree:.2f}",
        f"  labels: {s.distinct_labels} distinct · targets: {s.distinct_targets} "
        f"distinct coordinate(s) · {fan}",
        f"  geometry: {s.n_components} SCC component(s) · max BFS layer {s.max_layer}",
    ])
