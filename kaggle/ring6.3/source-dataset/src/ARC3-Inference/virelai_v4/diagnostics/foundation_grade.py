"""
virelai_v4/diagnostics/foundation_grade.py — WO_DD_G6_CORRECTNESS_GRADE.

A pure-read grading LENS. Given the dossier's per-object structural read
(render_read → tag/role/locality, plus anchor/bbox/cell_count geometry) and an
EXTERNAL foundation key (human-observed tag/role/locality per object, provenance
solver-output-NONE), it produces the campaign's CORRECTNESS column: the solver's
belief graded against reality.

It writes nothing. It reads only the dossier objects passed in and the key dict.
The solver never sees the key (§2 HALT: any grading path that would touch belief
state is illegal here). This module is a consumer of the belief, never a writer.

Two structural facts the key-vs-canary read must handle:
  1. Individuation grain differs — the key groups where the solver splits (the
     bordered surround is one 576-cell key object vs the solver's fill+corners;
     a glyph tile is one 6x6 key object vs the solver's sub-color regions). Hence
     EXACT / COMPOSITE / UNMATCHED mappings, not one-to-one.
  2. Evidence bases differ, and the asymmetry rules the verdict. Key STATIC-
     untested vs solver REACTIVE-witnessed is a KEY_COVERAGE_GAP (the solver
     clicked a tile the human never did — not a solver miss). Key REACTIVE-
     certain vs solver STATIC is a genuine solver MISS. Key UNKNOWN roles grade
     NOT_GRADED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

FOUNDATION_KEY_TYPE = "FOUNDATION_TAG_ROLE"

# Verdict vocabulary (per graded column).
MATCH = "MATCH"
MISS = "MISS"
NOT_GRADED = "NOT_GRADED"
KEY_COVERAGE_GAP = "KEY_COVERAGE_GAP"

# Mapping outcome vocabulary (key object → solver region set).
EXACT = "EXACT"
COMPOSITE = "COMPOSITE"
UNMATCHED = "UNMATCHED"


# ---------------------------------------------------------------------------
# Key type dispatch — the foundation key rides the SAME --axiom-key arg as the
# world-axioms key; the two are told apart by key_type. A world-axioms key
# carries no key_type, so is_foundation_key is False for it (the existing
# WORLD AXIOMS grader is untouched).
# ---------------------------------------------------------------------------

def is_foundation_key(key: Optional[Dict[str, Any]]) -> bool:
    return isinstance(key, dict) and key.get("key_type") == FOUNDATION_KEY_TYPE


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def _pair(v: Any) -> Optional[Tuple[int, int]]:
    """A usable (a, b) geometry pair, or None when the field is absent/Excluded."""
    if isinstance(v, (list, tuple)) and len(v) == 2:
        try:
            return (int(v[0]), int(v[1]))
        except (TypeError, ValueError):
            return None
    return None


def _rect(anchor: Tuple[int, int], bbox: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Inclusive (r0, c0, r1, c1) from anchor=(min_row, min_col) and
    bbox=(height, width) — the SAME conventions dossier._anchor / _bbox emit."""
    r0, c0 = anchor
    h, w = bbox
    return (r0, c0, r0 + h - 1, c0 + w - 1)


def _within(inner: Tuple[int, int, int, int], outer: Tuple[int, int, int, int]) -> bool:
    return (outer[0] <= inner[0] and outer[1] <= inner[1]
            and inner[2] <= outer[2] and inner[3] <= outer[3])


@dataclass
class SolverRegion:
    rid: int
    anchor: Tuple[int, int]
    bbox: Tuple[int, int]
    cells: int
    tag: Any
    role: Any
    locality: Any


@dataclass
class Mapping:
    key_index: int
    key_obj: Dict[str, Any]
    outcome: str                       # EXACT / COMPOSITE / UNMATCHED
    members: List[int] = field(default_factory=list)   # solver region ids
    reads: List[SolverRegion] = field(default_factory=list)


def _solver_regions(objects: List[Dict[str, Any]]) -> List[SolverRegion]:
    out: List[SolverRegion] = []
    for o in objects:
        a = _pair(o.get("anchor"))
        b = _pair(o.get("bbox"))
        if a is None or b is None:
            continue  # geometry not carried — cannot map; honestly skipped
        out.append(SolverRegion(
            rid=o["region_id"], anchor=a, bbox=b,
            cells=int(o.get("cell_count", 0)),
            tag=o.get("tag"), role=o.get("role"), locality=o.get("locality"),
        ))
    return out


def map_foundation(objects: List[Dict[str, Any]],
                   fkey: Dict[str, Any]) -> List[Mapping]:
    """Map each key object to the solver region(s) that realize it.

    Pass 1 EXACT — a single solver region whose (anchor, bbox, cell_count) all
      equal the key object's. Cell-count is the disambiguator: it stops an
      annulus FILL (same anchor+bbox as the surround, fewer cells) from falsely
      matching the whole surround.
    Pass 2 COMPOSITE — for each still-unmatched key object (processed smallest
      bbox first, so a nested glyph claims its sub-regions before the enclosing
      surround can absorb them), gather the unclaimed solver regions whose bbox
      lies within the key object's, and accept them as members iff their
      cell-counts sum EXACTLY to the key object's cells. No subset guessing: an
      inexact sum leaves the key object UNMATCHED (honest, not forced).
    Pass 3 UNMATCHED — everything else.
    """
    key_objs: List[Dict[str, Any]] = list(fkey.get("objects", []))
    solver = _solver_regions(objects)
    by_rid = {s.rid: s for s in solver}
    claimed: set = set()
    mappings: List[Optional[Mapping]] = [None] * len(key_objs)

    # Pass 1 — EXACT
    for i, k in enumerate(key_objs):
        ka = _pair(k.get("anchor"))
        kb = _pair(k.get("bbox"))
        kc = k.get("cells")
        if ka is None or kb is None:
            continue
        for s in solver:
            if s.rid in claimed:
                continue
            if s.anchor == ka and s.bbox == kb and (kc is None or s.cells == kc):
                claimed.add(s.rid)
                mappings[i] = Mapping(i, k, EXACT, [s.rid], [s])
                break

    # Pass 2 — COMPOSITE (smallest key bbox first)
    pending = [i for i in range(len(key_objs)) if mappings[i] is None]

    def _area(i: int) -> int:
        kb = _pair(key_objs[i].get("bbox"))
        return (kb[0] * kb[1]) if kb else 0

    for i in sorted(pending, key=_area):
        k = key_objs[i]
        ka = _pair(k.get("anchor"))
        kb = _pair(k.get("bbox"))
        kc = k.get("cells")
        if ka is None or kb is None:
            continue
        krect = _rect(ka, kb)
        members = [s for s in solver
                   if s.rid not in claimed and _within(_rect(s.anchor, s.bbox), krect)]
        if members and (kc is None or sum(s.cells for s in members) == kc):
            for s in members:
                claimed.add(s.rid)
            rids = sorted(s.rid for s in members)
            mappings[i] = Mapping(i, k, COMPOSITE, rids, [by_rid[r] for r in rids])

    # Pass 3 — UNMATCHED
    for i, k in enumerate(key_objs):
        if mappings[i] is None:
            mappings[i] = Mapping(i, k, UNMATCHED, [], [])

    return [m for m in mappings if m is not None]


# ---------------------------------------------------------------------------
# Grading — the CORRECTNESS column
# ---------------------------------------------------------------------------

def _consensus(vals: List[Any]) -> Any:
    """The shared value across solver members, or 'MIXED' when they disagree,
    or None when there are no members (UNMATCHED)."""
    s = {v for v in vals}
    if not s:
        return None
    if len(s) == 1:
        return next(iter(s))
    return "MIXED"


def _is_untested(key_obj: Dict[str, Any]) -> bool:
    return "untested" in str(key_obj.get("tag_coverage", "")).lower()


def grade_tag(key_obj: Dict[str, Any], solver_tag: Any) -> str:
    """Key STATIC-untested vs solver REACTIVE-witnessed = KEY_COVERAGE_GAP (the
    solver observed a change the human never triggered). All other divergences,
    including key REACTIVE vs solver STATIC (a real solver miss), are MISS."""
    kt = key_obj.get("tag")
    if solver_tag is None:
        return NOT_GRADED  # unmatched — nothing to grade against
    if solver_tag == "MIXED":
        return MISS
    if kt == solver_tag:
        return MATCH
    if kt == "STATIC" and _is_untested(key_obj) and solver_tag == "REACTIVE":
        return KEY_COVERAGE_GAP
    return MISS


def grade_role(key_obj: Dict[str, Any], solver_role: Any) -> str:
    """Key UNKNOWN roles grade NOT_GRADED (the human never resolved them). Any
    other divergence is a MISS; agreement is a MATCH."""
    kr = key_obj.get("role")
    if kr in (None, "UNKNOWN"):
        return NOT_GRADED
    if solver_role is None or solver_role == "MIXED":
        return NOT_GRADED if solver_role is None else MISS
    return MATCH if kr == solver_role else MISS


def grade_locality(key_obj: Dict[str, Any], solver_loc: Any) -> str:
    """Locality graded only where the key resolved it (LOCAL/REMOTE). Key
    locality null → NOT_GRADED. A key LOCAL vs a solver REMOTE (or no derived
    locality) is a MISS — the locality-derivation column the WO exists to catch."""
    kl = key_obj.get("locality")
    if kl is None:
        return NOT_GRADED
    if solver_loc is None:
        return MISS  # key resolved a locality the solver did not derive
    if solver_loc == "MIXED":
        return MISS
    return MATCH if kl == solver_loc else MISS


@dataclass
class GradedRow:
    mapping: Mapping
    solver_tag: Any
    solver_role: Any
    solver_locality: Any
    tag_verdict: str
    role_verdict: str
    locality_verdict: str


def grade_foundation(objects: List[Dict[str, Any]],
                     fkey: Dict[str, Any]) -> Tuple[List[GradedRow], Dict[str, Dict[str, int]]]:
    """Grade every key object against the solver's structural read. Returns the
    per-object rows plus summary counts (per mapping-outcome and per column)."""
    mappings = map_foundation(objects, fkey)
    rows: List[GradedRow] = []
    counts = {
        "outcome": {EXACT: 0, COMPOSITE: 0, UNMATCHED: 0},
        "tag": {MATCH: 0, MISS: 0, NOT_GRADED: 0, KEY_COVERAGE_GAP: 0},
        "role": {MATCH: 0, MISS: 0, NOT_GRADED: 0, KEY_COVERAGE_GAP: 0},
        "locality": {MATCH: 0, MISS: 0, NOT_GRADED: 0, KEY_COVERAGE_GAP: 0},
    }
    for m in mappings:
        counts["outcome"][m.outcome] += 1
        s_tag = _consensus([r.tag for r in m.reads])
        s_role = _consensus([r.role for r in m.reads])
        s_loc = _consensus([r.locality for r in m.reads])
        tv = grade_tag(m.key_obj, s_tag)
        rv = grade_role(m.key_obj, s_role)
        lv = grade_locality(m.key_obj, s_loc)
        counts["tag"][tv] += 1
        counts["role"][rv] += 1
        counts["locality"][lv] += 1
        rows.append(GradedRow(m, s_tag, s_role, s_loc, tv, rv, lv))
    return rows, counts


# ---------------------------------------------------------------------------
# Render — the FOUNDATION GRADE block appended to the dossier
# ---------------------------------------------------------------------------

def _v(x: Any) -> str:
    return "—" if x is None else str(x)


def _rids(members: List[int]) -> str:
    return ", ".join(f"R{r}" for r in members) if members else "—"


def render_foundation_grade(objects: List[Dict[str, Any]],
                            fkey: Dict[str, Any]) -> List[str]:
    """The correctness column, appended verbatim to the dossier overview when a
    foundation key is supplied. Pure text over the graded rows."""
    rows, counts = grade_foundation(objects, fkey)
    game = _v(fkey.get("game"))
    level = _v(fkey.get("level"))
    L: List[str] = []
    L.append(f" FOUNDATION GRADE · {game} L{level}   "
             "FIDELITY: structural (render_read) · CORRECTNESS: vs key")
    L.append("   key object                         → mapping    solver          "
             "tag / role / locality")
    for gr in rows:
        m = gr.mapping
        k = m.key_obj
        ka = _v(k.get("anchor"))
        ktrl = f"{_v(k.get('tag'))}·{_v(k.get('role'))}·{_v(k.get('locality'))}"
        left = f"@{ka} {ktrl}"
        outcome = m.outcome
        solver_read = (f"{_v(gr.solver_tag)}·{_v(gr.solver_role)}·{_v(gr.solver_locality)}"
                       if m.reads else "—")
        verdicts = f"tag:{gr.tag_verdict} role:{gr.role_verdict} loc:{gr.locality_verdict}"
        L.append(f"   {left:<34} → {outcome:<10} {_rids(m.members):<14} "
                 f"{solver_read:<18} {verdicts}")
    L.append("   ── summary ──")
    oc = counts["outcome"]
    L.append(f"   mappings   EXACT {oc[EXACT]} · COMPOSITE {oc[COMPOSITE]} · "
             f"UNMATCHED {oc[UNMATCHED]}")
    for col in ("tag", "role", "locality"):
        c = counts[col]
        L.append(f"   {col:<9}  MATCH {c[MATCH]} · MISS {c[MISS]} · "
                 f"KEY_COVERAGE_GAP {c[KEY_COVERAGE_GAP]} · NOT_GRADED {c[NOT_GRADED]}")
    return L
