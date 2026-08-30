"""WO_WEAVE_W0_STILL_BRIDGE · route still-object Ledger evidence into the role spine.

The smallest gradeable slice of the weave. For every Ledger worldline whose
fingerprint is UNCHANGED across its appearances (a still object), resolve it to
its spawn Slot by the free fingerprint-equality join (bridge audit §4) and emit
its Ledger-accumulated evidence — a STATIC verdict at a coverage-bounded
confidence — for the existing spine ``accumulate_role_evidence``.

Movers are quarantined to W1: a moved object minted new fingerprints (distinct
master-list entries, each seen once); those are excluded, never force-matched.

Discipline:
  - Pure resolver: imports stdlib + the (pure) clay types only. It does NOT
    import ``virelai_v4.library`` (scipy-tangled) or the accumulator — the belief
    write is dependency-injected via ``feed_fn`` so the pure layer stays testable
    and the clay stays sacred (the resolver never writes the Ledger).
  - Free join only: fingerprint equality, never a nearest-match.
  - One role from coverage: STILL ⇒ STATIC. No reactivity/lever/ego here (W1+).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple

from virelai_v4.capture.clay import MasterList

Fingerprint = Tuple[int, "frozenset"]

# W0 emits the role as its NAME (a plain str), decoupled from the scipy-tangled
# ``LibraryRole`` enum; the hook maps it back at the live/Mac site.
STATIC_ROLE = "STATIC"

# A fingerprint must be seen unchanged across at least this many nodes to count
# as still evidence (mirrors the classifier's coverage logic; W1 refines).
_STILL_MIN_SEEN = 2
# Coverage saturation for the confidence ramp (matches role_classifier's /20).
_COVERAGE_FULL = 20.0


@dataclass(frozen=True)
class StillWorldline:
    """A worldline whose fingerprint is invariant across its trail — a still object."""

    fingerprint: Fingerprint
    appearances: Tuple[Any, ...]     # the Ledger master-list trail
    is_still: bool

    @property
    def seen_count(self) -> int:
        return len(self.appearances)


@dataclass(frozen=True)
class FeedReport:
    still: int
    joined: int
    unjoined: int
    skipped_movers: int
    fed: Tuple[Tuple[int, str, float], ...]   # (region_id, role_name, confidence)


def resolve_still_worldlines(master: MasterList) -> Tuple[StillWorldline, ...]:
    """Select the still worldlines from the Ledger master list: fingerprints seen
    unchanged across ≥ _STILL_MIN_SEEN nodes. A moved object appears as distinct
    single-appearance fingerprints — those are excluded (quarantined to W1)."""
    out = []
    for e in master.entries:
        if e.seen_count >= _STILL_MIN_SEEN:
            out.append(StillWorldline(fingerprint=e.fingerprint, appearances=e.trail, is_still=True))
    return tuple(out)


def join_to_slot(still: StillWorldline, slot_fingerprints: Dict[Fingerprint, int]) -> Optional[int]:
    """The free join (bridge audit §4): match the still worldline's
    ``(class_id, cells)`` to a spawn Slot's ``(class_id, obj.cells)`` by EQUALITY
    — same scan_grid partition at spawn, 1:1, no compute. Returns the Slot's
    ``region_id`` or ``None`` (no equal spawn Slot — recorded, never force-matched)."""
    return slot_fingerprints.get(still.fingerprint)


def evidence_for(still: StillWorldline) -> Tuple[str, float]:
    """The Ledger-accumulated evidence for a still object: STILL ⇒ STATIC, at a
    confidence that grows with coverage (nodes seen unchanged). Mirrors the
    classifier's coverage-bounded ramp: min(0.95, 0.55 + 0.40·min(1, seen/20))."""
    coverage = min(1.0, still.seen_count / _COVERAGE_FULL)
    confidence = min(0.95, 0.55 + 0.40 * coverage)
    return STATIC_ROLE, confidence


# ---------------------------------------------------------------------------
# WO_HASH_A · the still-integral rendered as a first-class VIEW (### object).
# Derived over the Ledger + the Slot resolution; stores nothing, writes no
# belief. This is ≈ = ~ (still-only) — the degenerate identity function graded
# green in W0, made visible. Splitting ≈ from ~ (translate, …) is ###-B.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HashObject:
    """A rendered ### row — the still-integral as a view object (not a store)."""

    hash_id: str
    fingerprint: Fingerprint          # the invariant fingerprint (one member, still)
    node_trail: Tuple[int, ...]       # route_positions seen
    seen_count: int
    slot_rid: Optional[int]           # join_to_slot result, or None (unjoined)
    role_name: str                    # evidence_for → "STATIC"; render-only, not fed here
    confidence: float


def _hash_id(fingerprint: Fingerprint) -> str:
    """A stable, legible ### label keyed on class + anchor (min cell) — the same
    fingerprint yields the same id across runs, not a volatile index."""
    cls, cells = fingerprint
    r, c = min(cells) if cells else (-1, -1)
    return f"###-c{cls}-{r}_{c}"


def group_hash_objects(
    master: MasterList, slot_fingerprints: Dict[Fingerprint, int]
) -> Tuple[HashObject, ...]:
    """Derived view: build a ``HashObject`` per still worldline from its
    fingerprint + appearances + join + evidence. PURE — reads the Ledger master
    list and the slot-fingerprint dict, computes, returns. No store, no feed, no
    mutation. Canonical order (class_id, then anchor). Movers excluded."""
    objs = []
    for sw in resolve_still_worldlines(master):
        role, conf = evidence_for(sw)
        objs.append(HashObject(
            hash_id=_hash_id(sw.fingerprint),
            fingerprint=sw.fingerprint,
            node_trail=tuple(a.node_index for a in sw.appearances),
            seen_count=sw.seen_count,
            slot_rid=join_to_slot(sw, slot_fingerprints),
            role_name=role,
            confidence=conf,
        ))
    objs.sort(key=lambda h: (h.fingerprint[0], sorted(h.fingerprint[1])[:1]))
    return tuple(objs)


# WO_HASH_A2: the ### section as a drillable compression-chain tree —
# ### → visual objects → cells + site. Grounded-first (full to cells), unjoined
# summarized. Every grounded ### exposes its two coupling handles: the class
# integer (title) and the site footprint (cells, or the NW anchor when compressed
# past the cap). Both are what actions/### couple to ({class, site}, complete at
# two, per the ontology) — neither is ever dropped. Pure render.

# Cell-display cap: list every cell up to this many; past it, compress to the
# NW-corner anchor + count (still a coupling-keyable site handle, not a flood).
_CELL_CAP = 12


class VisualObject(NamedTuple):
    """A render view of one visual object composing a ### — its class + cells.
    For a still ###, k=1 of these; ###-B (movers) renders k>1, one per position."""

    class_id: int
    cells: "frozenset"


def _cell_display(cells) -> str:
    """The site footprint, legible: list every cell up to _CELL_CAP; past the cap
    compress to '<N> cells · NW anchor (r,c)' — the footprint compressed to its
    addressable corner, never dropped."""
    cells = frozenset(cells)
    if not cells:
        return "(no cells)"
    if len(cells) <= _CELL_CAP:
        return " ".join(f"({r},{c})" for r, c in sorted(cells))
    r, c = min(cells)
    return f"{len(cells)} cells · NW anchor ({r},{c})"


def _render_hash_block(h: HashObject, visual_objects) -> list:
    """Render one grounded ### as a titled tree block. Iterates ``visual_objects``
    as a list (k=1 for still; k>1 when ###-B movers land — extends without a
    render rewrite). Exposes class (title) + site footprint (last line)."""
    cls = h.fingerprint[0]
    trail = h.node_trail
    trail_str = (f"unchanged across #{trail[0]}–#{trail[-1]}" if trail else "(no trail)")
    lines = [
        f"### {h.hash_id} · class {cls} · slot {h.slot_rid} · "
        f"{h.role_name} {h.confidence:.2f} · seen {h.seen_count}× ({trail_str})",
        f"  composed of {len(visual_objects)} visual object(s):",
    ]
    for vo in visual_objects:
        lines.append(f"    ▪ visual object · class {vo.class_id} · {_cell_display(vo.cells)}")
    footprint = frozenset().union(*[vo.cells for vo in visual_objects]) if visual_objects else frozenset()
    lines.append(f"  └ site footprint: {_cell_display(footprint)}")
    return lines


def render_hash_section(hash_objects: Tuple[HashObject, ...]) -> str:
    """The "Persistent (###) Objects" compression-chain tree. Grounded ### render
    full to cells (title → composed-of → site footprint); unjoined are summarized
    to a single count-line. Render-only; no store, no belief write."""
    grounded = [h for h in hash_objects if h.slot_rid is not None]
    unjoined = [h for h in hash_objects if h.slot_rid is None]
    lines = [f"PERSISTENT (###) OBJECTS — {len(grounded)} grounded, "
             f"{len(unjoined)} unjoined (summarized)"]
    for h in grounded:
        cls, cells = h.fingerprint
        # still: one visual object = the invariant fingerprint.
        lines.extend(_render_hash_block(h, [VisualObject(cls, cells)]))
    if unjoined:
        lines.append(f"  + {len(unjoined)} unjoined still-### (post-spawn, no slot)")
    return "\n".join(lines)


def feed_still_evidence(
    master: MasterList,
    slot_fingerprints: Dict[Fingerprint, int],
    feed_fn: Callable[[int, str, float], None],
) -> FeedReport:
    """Resolve still worldlines, join each to its spawn Slot, and feed STATIC
    evidence via ``feed_fn(region_id, role_name, confidence)`` (the caller wires
    this to ``accumulate_role_evidence`` at the live site). Movers are counted as
    skipped and never reach ``feed_fn``. Pure but for the injected sink; the
    Ledger is only read."""
    still = resolve_still_worldlines(master)
    skipped_movers = len(master.entries) - len(still)
    joined = 0
    unjoined = 0
    fed = []
    for sw in still:
        rid = join_to_slot(sw, slot_fingerprints)
        if rid is None:
            unjoined += 1
            continue
        role, conf = evidence_for(sw)
        feed_fn(rid, role, conf)
        joined += 1
        fed.append((rid, role, conf))
    return FeedReport(
        still=len(still), joined=joined, unjoined=unjoined,
        skipped_movers=skipped_movers, fed=tuple(fed),
    )
