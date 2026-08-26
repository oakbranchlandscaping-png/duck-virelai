"""Ring 2.5 -- the light weave: components, the transcribed edge matcher, worldlines,
and the ego seal.

TRANSCRIPTION (R-H1, the one ruled unit; R-C citation): the verb alphabet and the
three-pass matcher cascade below are transcribed from `virelai_v4/weave/edge.py`
(WO_WEAVE_S2_EDGE_MATCHER; proven across the v4 canary corpus and carried into the
golden weave). What it proved: deterministic pairwise correspondence -- SITE footprint
first, CLASS-held single-licensed-transform second, residual BIRTH/DEATH/DEFORM,
contests surfacing as AMBIGUOUS rather than guesses. Reduced here to the minimal
region stand-in; no scipy, no belief, stdlib only. Origin buys attention, never trust:
re-proven by this variant's unit battery.

REBUILT-FRESH around it (cited shapes):
  world type from the action roster ... Director's ruling 2026-08-26; replaces v4
                                        classify_world_type + confidence ratchet
                                        (library_sync.py:564 -- ratchet = banned)
  ego seal, existential + permanent ... the navigation campaign's forall->exists fix
                                        ("one press that moved a worldline in a
                                        direction a button names is a witness,
                                        permanent; a later still press says BLOCKED")
  observed bearing map ................ collide_drive's `EgoMap.observed` shape
  threading across RESET by SITE ...... canon 1 par-2: RESET returns s0 byte-identical,
                                        so identity survives death at the same footprint

Laws: no thresholds (seals are counts/quantifiers); multi-ego is a SET (R3);
CLICK worlds run no ego search (GOD_MODE is a roster derivation, not a discovery);
sealed-counter cells are excluded from components (attribution-quarantine, rider par-C).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

Cell = Tuple[int, int]

DIRECTIONAL = ("UP", "DOWN", "LEFT", "RIGHT")


# ---------------------------------------------------------------------------
# World type -- a derivation over the observed action roster (never a classifier)
# ---------------------------------------------------------------------------

def world_type(roster: frozenset) -> Optional[str]:
    """NAV / CLICK / HYBRID from the union of observed non-RESET labels."""
    labels = {l for l in roster if l != "RESET"}
    has_dir = any(l in labels for l in DIRECTIONAL)
    has_mouse = "MOUSE" in labels
    if has_dir and has_mouse:
        return "HYBRID"
    if has_dir:
        return "NAV"
    if has_mouse:
        return "CLICK"
    return None


def world_type_line(wt: str, roster: frozenset) -> str:
    r = ", ".join(sorted(l for l in roster if l != "RESET"))
    if wt == "NAV":
        return (f"[WORLD] NAV world (roster: {r}): expect an embodied ego -- "
                f"find what moves with your presses, and sweep by colliding.")
    if wt == "CLICK":
        return (f"[WORLD] CLICK world (roster: {r}): GOD_MODE -- there is no avatar; "
                f"your clicks are the hand. Sweep by clicking each object once.")
    return (f"[WORLD] HYBRID world (roster: {r}): directional presses AND clicks -- "
            f"expect an embodied ego and click-targets both.")


# ---------------------------------------------------------------------------
# Regions + components (the minimal RegionClay stand-in)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Region:
    class_id: Any
    cells: FrozenSet[Cell]

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    @property
    def anchor(self) -> Cell:
        return min(self.cells)


def components(grid_cells: dict, exclude: frozenset = frozenset()) -> List[Region]:
    """4-connected same-value components over {(r,c): v}, skipping `exclude` cells."""
    todo = {rc for rc in grid_cells if rc not in exclude}
    out: List[Region] = []
    while todo:
        start = todo.pop()
        v = grid_cells[start]
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in todo and grid_cells[nb] == v:
                    todo.discard(nb)
                    comp.add(nb)
                    stack.append(nb)
        out.append(Region(v, frozenset(comp)))
    return out


# ---------------------------------------------------------------------------
# The transcribed matcher (edge.py: _norm, _translation, cascade)
# ---------------------------------------------------------------------------

def _norm(cells: FrozenSet[Cell]) -> FrozenSet[Cell]:
    if not cells:
        return frozenset()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _translation(prev_cells, now_cells) -> Optional[Cell]:
    prev_cells = frozenset(prev_cells)
    now_cells = frozenset(now_cells)
    if len(prev_cells) != len(now_cells):
        return None
    if _norm(prev_cells) != _norm(now_cells):
        return None
    pr = min(r for r, _ in prev_cells); pc = min(c for _, c in prev_cells)
    nr = min(r for r, _ in now_cells); nc = min(c for _, c in now_cells)
    off = (nr - pr, nc - pc)
    return off if off != (0, 0) else None


def _class_verb(prev: Region, now: Region) -> Optional[str]:
    p, n = prev.cells, now.cells
    if n > p:
        return "GROW"
    if n < p:
        return "SHRINK"
    if _translation(p, n) is not None:
        return "MOVE"
    return None


@dataclass(frozen=True)
class Stitch:
    prev: Optional[Region]
    now: Optional[Region]
    verb: str                    # STILL RECOLOR MOVE GROW SHRINK BIRTH DEATH DEFORM AMBIGUOUS
    delta: Any = None            # MOVE: (dr,dc) . RECOLOR: (c0,c1) . GROW/SHRINK: int


def weave_edge(prev_regions: List[Region], now_regions: List[Region]) -> List[Stitch]:
    """The three-pass cascade, transcribed: SITE -> CLASS -> residual."""
    prevs = sorted(prev_regions, key=lambda r: (r.cell_count, str(r.class_id), r.anchor))
    nows = sorted(now_regions, key=lambda r: (r.cell_count, str(r.class_id), r.anchor))
    consumed: set = set()
    out: List[Stitch] = []

    by_cells: Dict[FrozenSet[Cell], int] = {}
    for i, q in enumerate(nows):
        by_cells.setdefault(q.cells, i)
    unmatched: List[Region] = []
    for p in prevs:
        i = by_cells.get(p.cells)
        if i is not None and i not in consumed:
            q = nows[i]
            consumed.add(i)
            if q.class_id == p.class_id:
                out.append(Stitch(p, q, "STILL"))
            else:
                out.append(Stitch(p, q, "RECOLOR", (p.class_id, q.class_id)))
        else:
            unmatched.append(p)

    by_class: Dict[Any, List[int]] = {}
    for i, q in enumerate(nows):
        by_class.setdefault(q.class_id, []).append(i)
    for p in unmatched:
        pool = [i for i in by_class.get(p.class_id, []) if i not in consumed]
        licensed = [(i, v) for i, v in ((i, _class_verb(p, nows[i])) for i in pool)
                    if v is not None]
        if len(licensed) == 1:
            i, verb = licensed[0]
            q = nows[i]
            consumed.add(i)
            delta = (_translation(p.cells, q.cells) if verb == "MOVE"
                     else q.cell_count - p.cell_count)
            out.append(Stitch(p, q, verb, delta))
        elif len(licensed) >= 2:
            out.append(Stitch(p, None, "AMBIGUOUS"))
        else:
            out.append(Stitch(p, None, "DEFORM" if pool else "DEATH"))

    for i, q in enumerate(nows):
        if i not in consumed:
            out.append(Stitch(None, q, "BIRTH"))
    return out


# ---------------------------------------------------------------------------
# Worldlines + the ego seal
# ---------------------------------------------------------------------------

@dataclass
class Worldline:
    wid: int
    class_id: Any
    cells: FrozenSet[Cell]                       # current footprint
    moves: dict = field(default_factory=dict)    # label -> set of observed (dr,dc)
    move_count: int = 0
    ego: bool = False                            # sealed EGO (permanent)


class Weave:
    """Threads worldlines edge by edge; seals EGO existentially."""

    def __init__(self) -> None:
        self.worldlines: Dict[int, Worldline] = {}
        self._next = 1
        self._by_cells: Dict[FrozenSet[Cell], int] = {}   # current footprint -> wid
        self.notes: List[str] = []
        self._ego_announced: set = set()

    def _mint(self, region: Region) -> Worldline:
        w = Worldline(self._next, region.class_id, region.cells)
        self.worldlines[w.wid] = w
        self._by_cells[region.cells] = w.wid
        self._next += 1
        return w

    def thread(self, prev_regions: List[Region], now_regions: List[Region],
               label: str, site_only: bool = False) -> None:
        """Advance the weave across one edge. `site_only` for the RESET back-edge."""
        stitches = weave_edge(prev_regions, now_regions)
        new_by_cells: Dict[FrozenSet[Cell], int] = {}
        for s in stitches:
            if s.prev is not None and s.now is not None:
                if site_only and s.verb not in ("STILL",):
                    continue
                wid = self._by_cells.get(s.prev.cells)
                w = self.worldlines.get(wid) if wid is not None else None
                if w is None:
                    w = self._mint(s.prev)
                w.cells = s.now.cells
                w.class_id = s.now.class_id
                new_by_cells[s.now.cells] = w.wid
                if s.verb == "MOVE" and label in DIRECTIONAL:
                    w.moves.setdefault(label, set()).add(s.delta)
                    w.move_count += 1
                    self._seal_check(w)
            elif s.now is not None and not site_only:
                w = self._mint(s.now)
                new_by_cells[s.now.cells] = w.wid
        # worldlines with no stitch this edge keep their footprint (STILL by absence
        # is not asserted; they simply were not contradicted). Re-anchor the index:
        for cells, wid in list(self._by_cells.items()):
            if cells not in new_by_cells and wid in self.worldlines:
                w = self.worldlines[wid]
                if w.cells == cells:
                    new_by_cells.setdefault(cells, wid)
        self._by_cells = new_by_cells

    def _seal_check(self, w: Worldline) -> None:
        """EGO seals when MOVEd under >=2 distinct directional labels with >=2
        distinct bearings -- which-action covariance (R-A), existential, permanent."""
        if w.ego:
            return
        labels_moved = {l for l, ds in w.moves.items() if ds}
        bearings = set().union(*w.moves.values()) if w.moves else set()
        if len(labels_moved) >= 2 and len(bearings) >= 2:
            w.ego = True
            if w.wid not in self._ego_announced:
                self._ego_announced.add(w.wid)
                obs = "; ".join(
                    f"{l}->{sorted(ds)[0]}" for l, ds in sorted(w.moves.items()) if ds)
                r0 = min(r for r, _ in w.cells); r1 = max(r for r, _ in w.cells)
                c0 = min(c for _, c in w.cells); c1 = max(c for _, c in w.cells)
                self.notes.append(
                    f"[EGO] sealed: the {len(w.cells)}-cell class-{w.class_id} shape at "
                    f"rows {r0}-{r1} x cols {c0}-{c1} is YOU. Observed: {obs}. A press "
                    f"that does not move you means BLOCKED, not doubt.")

    def egos(self) -> List[Worldline]:
        return [w for w in self.worldlines.values() if w.ego]
