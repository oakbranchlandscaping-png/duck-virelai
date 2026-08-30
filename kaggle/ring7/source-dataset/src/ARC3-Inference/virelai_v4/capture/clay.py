"""WO-CC-S2-CLAY · the offline clay compiler — cut every node, compile three views.

The data-collection layer over the sealed Stage-1 capture record. It reads
per-node partitions (already computed by the caller via ``scan_grid`` — kept
out of this module so the compile logic is pure and scipy-free) and compiles
three raw views:

  1. per-node present list — this node's detected objects, geometry only;
  2. object master list — every distinct ``(class, cell-set)`` fingerprint,
     append-only, each carrying its node-address trail;
  3. node / configuration map — every distinct grid-state (``node_hash``),
     with every arrival and its edge-path from the last full_reset.

It decides nothing and infers nothing. No weave, no roles, no continuity, no
Slots, no masking, no "same node modulo counter." A counter tick is a distinct
grid state and is recorded as such — over-distinguishing is recording reality;
the counter's resolution is a later inference over the values captured here.

Fences (WO-CC-S2-CLAY §3): imports stdlib only — nothing from ``library/``,
``captain``, ``targeting``, ``nested_read``, ``render_read``, ``classification``,
``grid_scan``, or ``scipy``. The two geometry helpers are inlined (min/max over
cells) rather than imported from ``dossier`` (which pulls belief deps + scipy).
Objects carry geometry only — no role/tag/Slot/region_id. The fingerprint is
``(class_id, frozenset(cells))``, renumber-independent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

Cell = Tuple[int, int]
CellSet = "frozenset[Cell]"
Edge = Optional[Tuple[int, Any]]


def _hash_visible(grid: Any) -> str:
    """SHA-256 over the VISIBLE (single-layer) 2D grid — the atom's addressing
    hash (WO_SIGHTING_LEDGER §1). A pure sibling of ``frame_record._hash_layers``;
    the Ledger computes this from ``reconstruct(i)[-1]`` rather than importing
    ``virelai._hash_grid`` (which is arcengine-tangled). This says "the same
    visible grid appeared here" — an address, never an identity verdict."""
    norm = [[int(c) for c in row] for row in (grid or [])]
    digest = hashlib.sha256()
    digest.update(repr(norm).encode("utf-8"))
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Inlined geometry (min/max over cells) — NOT imported from dossier, which
# would pull belief deps + scipy and break the interpretation-free fence.
# ---------------------------------------------------------------------------

def _anchor(cells) -> Tuple[int, int]:
    """Top-left (min_row, min_col) of a cell-set. () -> (-1, -1) sentinel."""
    if not cells:
        return (-1, -1)
    return (min(r for r, _ in cells), min(c for _, c in cells))


def _bbox(cells) -> Tuple[int, int]:
    """(height, width) of a cell-set's bounding box. () -> (0, 0)."""
    if not cells:
        return (0, 0)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)


# ---------------------------------------------------------------------------
# Input units — geometry only
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegionClay:
    """One detected visual object, geometry only. No role/tag/Slot/region_id —
    region_id is renumber-unstable and belief-adjacent; the identity is the
    fingerprint ``(class_id, cells)``."""

    class_id: int
    cells: "frozenset[Cell]"
    cell_count: int
    anchor: Tuple[int, int]
    bbox: Tuple[int, int]

    @staticmethod
    def from_cells(class_id: int, cells) -> "RegionClay":
        cells = frozenset((int(r), int(c)) for r, c in cells)
        return RegionClay(
            class_id=int(class_id),
            cells=cells,
            cell_count=len(cells),
            anchor=_anchor(cells),
            bbox=_bbox(cells),
        )

    @property
    def fingerprint(self) -> Tuple[int, "frozenset[Cell]"]:
        """This object's IDENTITY, as this class's own docstring defines it.

        **ONE PRODUCER, AND IT IS WHY THIS IS A PROPERTY RATHER THAN A TUPLE SPELLED AT
        EACH READER.** `worldline_binding._first_region_fingerprint` and
        `still_bridge`'s `slot_fingerprints` both build this pair by hand, and
        `WO-BUDGET-OUT-01` needed a third reader in the weave layer. A pair spelled in
        three places is how two readings drift.

        **IT ALSO KEEPS THE CLASS TERM OUT OF THE WEAVE.** `test_collide_drive`'s
        world-term fence bans `class_id` from the drive's modules by name, and it is
        right to: a class is a world's content and the drive may not reason about one.
        Asking whether a fingerprint is PRESENT needs no such reasoning, and through this
        property the drive never names the term."""
        return (self.class_id, self.cells)

    @property
    def shape(self) -> Tuple[int, "frozenset[Cell]"]:
        """This object's identity, NORMALISED BY ITS OWN ANCHOR — the same pair as
        `fingerprint`, translated to the origin.

        **A PROPERTY FOR THE REASON `fingerprint` IS ONE.** That docstring: *"a pair
        spelled in three places is how two readings drift"* and *"through this property
        the drive never names the term."* `test_collide_drive`'s world-term fence bans the
        class term from the drive's modules by NAME, so a reader that built this pair by
        hand could not legally exist there. The drive compares two opaque values.

        **TRANSLATION ONLY, AND THE OMISSION IS THE RULING.** `library/cross_level_identity
        .scale_normalized_shape` is the prior art and it normalises scale as well, so a
        four-cell square and a one-cell square canonicalise together. For a rigid body that
        is strictly wrong: it widens ambiguity for no gain. `_anchor` is the top-left
        `(min_row, min_col)`, which is the anchor `METHOD_LEGACY_TO_GOLDEN_PORT_v1` §4 names
        in place of the centroid every prior generation used.

        **AN EMPTY REGION HAS NO SHAPE.** `_anchor` answers `(-1, -1)` for the empty set;
        normalising by a sentinel would mint a shape for a thing that has none, so the
        empty case is absence and is answered as `None`."""
        cls, cells = self.fingerprint
        if not cells:
            return None
        r0, c0 = self.anchor
        return (cls, frozenset((r - r0, c - c0) for r, c in cells))

    @staticmethod
    def from_region(region: Any) -> "RegionClay":
        """Build from a GridScan ``Region`` (duck-typed: ``.value`` + ``.cells``).
        Reads geometry only; imports nothing from perception/library."""
        return RegionClay.from_cells(getattr(region, "value"), getattr(region, "cells"))


@dataclass(frozen=True)
class NodeId:
    """The v3 atom address: a visible-grid hash + the record-pointer. Raw
    addressing — "the same visible grid appeared at this route position" — never
    an identity verdict. Sameness is the weave's later ruling."""

    visible_grid_hash: str
    route_position: int


@dataclass(frozen=True)
class NodeCut:
    """One node's partition plus its v3 addressing, geometry only.

    ``node_hash`` is the VISIBLE-grid hash (the atom address, WO_SIGHTING_LEDGER
    §1). ``layered_hash`` is the full-stack hash, DEMOTED from the atom key to a
    carried record field — the weave's fork-witness, never the identity key."""

    node_index: int
    node_hash: str                       # visible-grid hash — the atom address
    edge: Edge
    full_reset: bool
    state: str
    available_actions: Tuple[int, ...]
    regions: Tuple[RegionClay, ...]
    layered_hash: str = ""               # carried full-stack hash — NOT the key
    grid_shape: Tuple[int, int] = (0, 0)  # (H, W) of the visible grid
    # WO-ANIMATION-01 · THE DELIVERY'S STRUCTURE, CARRIED — AND IT IS NOT AN OUTCOME.
    #
    # The platform may hand one turn several grids; the settled board is the last, and
    # `ledger_build` takes it one line before this atom is built. These three fields say
    # what the delivery LOOKED LIKE — how many grids arrived, which of the classifier's
    # three shapes they formed, and how many cells moved between them. **`layered_hash`
    # above witnesses THAT a full stack existed; these say WHAT it was.**
    #
    # **THE NAMES ARE `delivery_*` AND THAT IS LOAD-BEARING.** `classify_press` returns
    # `SILENT` whenever `len(layers) <= 1` — before comparing anything to a prior board —
    # and `_endpoints_differ` compares the first and last layer of ONE delivery and never
    # sees the previous node. **A single-layer turn that plainly changed the world reads
    # `SILENT`.** So no field here may be read as a world fact, and none is named as one.
    #
    # **THE DEFAULTS MEAN NOT OBSERVED**, and no real value can collide with them: a length
    # and a count are non-negative, and the classifier's three names are all non-empty.
    # A caller that did not look is distinguishable from one that looked and saw one layer.
    #
    # **CARRIED, NEVER JUDGED.** No seal, role, verdict, belief write or worldline field
    # reads any of this — asserted exhaustively in `tests/capture/test_delivery.py`.
    delivery_layers: int = -1            # grids in the turn's delivery; -1 = not observed
    delivery_class: str = ""             # the classifier's shape name; "" = not observed
    delivery_magnitude: int = -1         # interior cells moved; -1 = not observed

    @property
    def node_id(self) -> NodeId:
        return NodeId(visible_grid_hash=self.node_hash, route_position=self.node_index)

    @staticmethod
    def from_record(
        record: Any,
        regions: Tuple[RegionClay, ...],
        *,
        visible_hash: str,
        grid_shape: Tuple[int, int],
        delivery_layers: int = -1,
        delivery_class: str = "",
        delivery_magnitude: int = -1,
    ) -> "NodeCut":
        """Assemble from a ``CaptureRecord`` + pre-cut regions. The address is the
        caller-computed ``visible_hash`` (from ``reconstruct(i)[-1]``), NOT the
        record's full-stack ``layered_hash`` — that is carried as a field."""
        return NodeCut(
            node_index=int(record.node_index),
            node_hash=str(visible_hash),
            edge=record.edge,
            full_reset=bool(record.full_reset),
            state=str(record.state),
            available_actions=tuple(record.available_actions),
            regions=tuple(regions),
            layered_hash=str(record.layered_hash),
            grid_shape=(int(grid_shape[0]), int(grid_shape[1])),
            # WO-ANIMATION-01 · **THE CALLER COMPUTES; THIS MODULE ONLY CARRIES.** The same
            # keyword pattern `visible_hash` and `grid_shape` already use — `clay.py` is
            # stdlib-only and its own locking test forbids `grid_scan`, which
            # `perception.animation` imports. No new precedent and no new import.
            delivery_layers=int(delivery_layers),
            delivery_class=str(delivery_class),
            delivery_magnitude=int(delivery_magnitude),
        )


# ---------------------------------------------------------------------------
# Master list — fingerprint trail
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Appearance:
    node_index: int
    node_hash: str
    anchor: Tuple[int, int]


@dataclass(frozen=True)
class FingerprintEntry:
    fingerprint: Tuple[int, "frozenset[Cell]"]     # (class_id, cells)
    cell_count: int
    bbox: Tuple[int, int]
    seen_count: int
    trail: Tuple[Appearance, ...]


@dataclass(frozen=True)
class MasterList:
    entries: Tuple[FingerprintEntry, ...]


# ---------------------------------------------------------------------------
# Node map — arrival paths
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Arrival:
    node_index: int
    inbound_edge: Edge
    path_from_root: Tuple[Edge, ...]
    reset_rooted: bool
    layered_hash: str = ""      # full-stack fork-witness — recorded, never judged


@dataclass(frozen=True)
class NodeEntry:
    node_hash: str
    arrivals: Tuple[Arrival, ...]


@dataclass(frozen=True)
class NodeMap:
    entries: Tuple[NodeEntry, ...]


# ---------------------------------------------------------------------------
# 1 · per-node present list
# ---------------------------------------------------------------------------

def _region_row(r: RegionClay) -> str:
    return (f"  class {r.class_id:>2} · {r.cell_count:>4} cells · "
            f"bbox {r.bbox[0]}x{r.bbox[1]} · anchor ({r.anchor[0]},{r.anchor[1]})")


def present_list(cut: NodeCut) -> str:
    """This node's detected objects, geometry only, canonical order
    (class_id, then anchor). The genuine per-node cut — this node's partition."""
    ordered = sorted(cut.regions, key=lambda r: (r.class_id, r.anchor))
    header = (f"NODE #{cut.node_index} [{cut.node_hash[:8]}] "
              f"state={cut.state} reset={cut.full_reset} "
              f"actions={list(cut.available_actions)} · {len(ordered)} objects")
    return "\n".join([header] + [_region_row(r) for r in ordered])


# ---------------------------------------------------------------------------
# 2 · object master list
# ---------------------------------------------------------------------------

def collapse_fingerprints(
    members: "Iterable[Tuple[int, str, RegionClay]]",
) -> Tuple[FingerprintEntry, ...]:
    """The ``(class_id, cells)``-dedup collapse core — SPEC_SIGHTING_LEDGER §5
    ``master`` / SPEC_WEAVE §1 spatial identity ``~``. Takes ``(node_index,
    node_hash, region)`` member sightings — each region carrying
    ``class_id / cells / cell_count / bbox / anchor`` — groups them by the
    immortal fingerprint ``(class_id, cells)``, and returns the
    ``FingerprintEntry`` list: a STILL object collapses to ONE entry with many
    appearances; a MOVED object mints a new fingerprint per delta. ONE primitive,
    two callers — ``master_object_list`` (whole stream) and the integration roster
    (per-``###`` over ``Worldline.steps``). §8: a read-time view over
    already-recorded sightings, never a second stored accumulator. Ordering
    (first-appearance for each trail, then ``(class_id, cells)`` for the entries)
    is identical to the pre-extraction behavior — the extraction is byte-neutral."""
    order: List[Tuple[int, "frozenset[Cell]"]] = []
    trails: Dict[Tuple[int, "frozenset[Cell]"], List[Appearance]] = {}
    geom: Dict[Tuple[int, "frozenset[Cell]"], Tuple[int, Tuple[int, int]]] = {}
    for (node_index, node_hash, r) in members:
        key = (r.class_id, r.cells)
        if key not in trails:
            trails[key] = []
            geom[key] = (r.cell_count, r.bbox)
            order.append(key)
        trails[key].append(Appearance(node_index, node_hash, r.anchor))

    entries = []
    for key in sorted(order, key=lambda k: (k[0], sorted(k[1]))):
        cell_count, bbox = geom[key]
        appearances = tuple(sorted(trails[key], key=lambda a: a.node_index))
        entries.append(FingerprintEntry(
            fingerprint=key, cell_count=cell_count, bbox=bbox,
            seen_count=len(appearances), trail=appearances,
        ))
    return tuple(entries)


def master_object_list(cuts: List[NodeCut]) -> MasterList:
    """Accumulate over all nodes, keyed on the immortal fingerprint
    ``(class_id, frozenset(cells))``. A still object collapses to one entry with
    many appearances; a moved object mints new fingerprints (flipbook). Dedup on
    the fingerprint, never region_id. Thin wrapper over ``collapse_fingerprints``
    (WO-B3-R1a-2 §1 extraction — behavior-neutral; output byte-identical)."""
    members = (
        (cut.node_index, cut.node_hash, r)
        for cut in sorted(cuts, key=lambda c: c.node_index)
        for r in cut.regions
    )
    return MasterList(entries=collapse_fingerprints(members))


# ---------------------------------------------------------------------------
# 3 · node / configuration map
# ---------------------------------------------------------------------------

def node_map(cuts: List[NodeCut]) -> NodeMap:
    """Keyed on ``node_hash`` (the grid-state address). Records every arrival and
    its edge-path from the most recent full_reset (or index 0). Multi-path
    arrivals — the same hash reached by distinct paths — are surfaced as-is; no
    judgment about whether they are "really the same node" (that is the weave's
    call over this data). This is the path-dependence substrate."""
    order: List[str] = []
    arrivals: Dict[str, List[Arrival]] = {}

    current_path: List[Edge] = []
    reset_rooted = False
    first = True

    for cut in sorted(cuts, key=lambda c: c.node_index):
        if cut.full_reset:
            current_path = []
            reset_rooted = True
        elif first:
            current_path = []
            reset_rooted = False
        else:
            current_path = current_path + [cut.edge]
        first = False

        if cut.node_hash not in arrivals:
            arrivals[cut.node_hash] = []
            order.append(cut.node_hash)
        arrivals[cut.node_hash].append(Arrival(
            node_index=cut.node_index,
            inbound_edge=cut.edge,
            path_from_root=tuple(current_path),
            reset_rooted=reset_rooted,
            layered_hash=cut.layered_hash,
        ))

    entries = tuple(
        NodeEntry(node_hash=h, arrivals=tuple(arrivals[h])) for h in order
    )
    return NodeMap(entries=entries)


# ---------------------------------------------------------------------------
# Renderers — geometry-and-address only, human-legible
# ---------------------------------------------------------------------------

def _fmt_edge(edge: Edge) -> str:
    return "root" if edge is None else f"{edge[0]}@{edge[1]}"


def _fmt_path(path: Tuple[Edge, ...]) -> str:
    return "·".join(_fmt_edge(e) for e in path) if path else "(root)"


def render_master_list(ml: MasterList) -> str:
    lines = [f"OBJECT MASTER LIST — {len(ml.entries)} distinct fingerprints "
             "(class, cell-set), append-only"]
    for e in ml.entries:
        cls, cells = e.fingerprint
        lines.append(
            f"  class {cls:>2} · {e.cell_count:>4} cells · bbox {e.bbox[0]}x{e.bbox[1]} "
            f"· seen {e.seen_count}x"
        )
        trail = " → ".join(
            f"#{a.node_index}[{a.node_hash[:6]}]@({a.anchor[0]},{a.anchor[1]})"
            for a in e.trail
        )
        lines.append(f"      trail: {trail}")
    return "\n".join(lines)


def render_node_map(nm: NodeMap) -> str:
    multipath = sum(
        1 for e in nm.entries
        if len({a.path_from_root for a in e.arrivals}) > 1
    )
    lines = [f"NODE / CONFIGURATION MAP — {len(nm.entries)} distinct grid-states "
             f"· {multipath} reached by multiple paths"]
    for e in nm.entries:
        lines.append(f"  [{e.node_hash[:8]}] · {len(e.arrivals)} arrival(s)")
        # fork-witness: distinct full-stack hashes under one visible address are
        # recorded (a fork), never judged "same" or "different" node.
        forks = len({a.layered_hash for a in e.arrivals if a.layered_hash})
        fork_note = f" · {forks} full-stack variant(s)" if forks > 1 else ""
        lines[-1] += fork_note
        for a in e.arrivals:
            root = " (reset-rooted)" if a.reset_rooted else ""
            fw = f" · fs[{a.layered_hash[:6]}]" if a.layered_hash else ""
            lines.append(
                f"      #{a.node_index} via {_fmt_edge(a.inbound_edge)} "
                f"· path {_fmt_path(a.path_from_root)}{root}{fw}"
            )
    return "\n".join(lines)
