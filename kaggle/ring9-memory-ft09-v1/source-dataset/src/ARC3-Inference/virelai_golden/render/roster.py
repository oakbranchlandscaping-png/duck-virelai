"""RENDER · the integration roster — LIST 1 (distinct visual objects) and LIST 2 (### worldlines).

Formats only; computes nothing but the read-time collapse over the worldlines it is handed.
Canon: 02 §5 — a visual object is a distinct (class, cells) fingerprint; a STILL object is ONE
visual object with many appearances; an ACTIVE one mints a new visual object per delta.

Transcription origin (R-C): virelai_v4/diagnostics/integration_roster.py:44-114 (`COLOR_NAMES`,
`_color`, `_location`, `_object_line`, `_y_label`, `_class_field`) and :586-694 (LIST 1, LIST 2,
X→Y) @ oracle-v4; the collapse from capture/clay.py `collapse_fingerprints`. What it proved:
the rosters of both golden ls20 logs (2026-09-05). Format kept byte-identical so the Rung 0
unlock — golden LIST 1/2 ≡ v4's — is a `diff`.

NOT transcribed: the role column (`_role_label`, `_role_bucket`, `_label_fields`), LIST 3, the
CLOSING SUMMARY, the repeated-contact suffix — all read roles, which Rung 0 does not have (R-E).
The `########## INTEGRATION ROSTER … ##########` banner and `END ROSTER` line are omitted here
and emitted by the CLI, since they name v4's WO.

The palette is the platform's universal 0–15 render map (arc_agi/rendering.py COLOR_MAP),
mirrored as v4 did: a render label only, never a belief and never read by the solver. The
firewall (00) is intact: names are attached at the render site, downstream of every decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.worldline import Worldline

COLOR_NAMES = {0: "White", 1: "Off-white", 2: "Neutral-light", 3: "Neutral", 4: "Off-black",
               5: "Black", 6: "Magenta", 7: "Magenta-light", 8: "Red", 9: "Blue", 10: "Blue-light",
               11: "Yellow", 12: "Orange", 13: "Maroon", 14: "Green", 15: "Purple"}


@dataclass(frozen=True)
class Entry:
    """One distinct visual object with its appearance trail (node, NW-member cell)."""

    value: int
    cells: frozenset
    trail: Tuple[int, ...]  # node indices, ascending


def collapse(members: Iterable[Tuple[int, "object"]]) -> Tuple[Entry, ...]:
    """Group (node, region) sightings by fingerprint; entries ordered by (class, sorted cells),
    trails by node — clay.collapse_fingerprints' order, kept."""
    trails: Dict[Tuple[int, frozenset], List[int]] = {}
    for node, region in members:
        trails.setdefault(region.fingerprint, []).append(node)
    return tuple(Entry(k[0], k[1], tuple(sorted(v)))
                 for k, v in sorted(trails.items(), key=lambda kv: (kv[0][0], sorted(kv[0][1]))))


def color(value: int) -> str:
    name = COLOR_NAMES.get(value)
    return f"**{name if name is not None else f'c{value}'} ({value})**"


def location(cells: Iterable[Cell]) -> Cell:
    """The NW-most MEMBER cell (min by (row, col)) — not the bbox anchor."""
    cs = list(cells)
    return min(cs, key=lambda c: (c[0], c[1])) if cs else (-1, -1)


def object_line(e: Entry, verbose: bool = False) -> str:
    lr, lc = location(e.cells)
    span = f"{e.trail[0]}–{e.trail[-1]}" if e.trail else "?"
    line = (f"{color(e.value)} · {len(e.cells)} cells · NW ({lr},{lc}) · "
            f"{len(e.trail)} appearance(s) · nodes {span}")
    if verbose:
        line += " · cells [" + " ".join(f"({r},{c})" for r, c in sorted(e.cells)) + "]"
    return line


def y_label(y: int, lives_observed: Optional[int]) -> str:
    return f"Y={y} (last life; {lives_observed} lives observed)" if lives_observed else f"Y={y} (last life)"


def class_field(classes: Sequence[int]) -> str:
    if len(classes) == 1:
        return color(classes[0])
    if len(classes) == 2:
        return f"{color(classes[0])}→{color(classes[1])}"
    return "**MIXED**"


def render_lists(worldlines: Sequence[Worldline], verbose: bool = False,
                 lives_observed: Optional[int] = None) -> str:
    """LIST 1 + LIST 2 + the X→Y line, v4's format without the role column."""
    wls = list(worldlines)
    lines: List[str] = []
    if not wls:
        lines.append("  (no woven worldlines retained — empty window)")
        lines.append(f"  X→Y ── X=0 distinct visual objects → {y_label(0, lives_observed)} · compression n/a")
        return "\n".join(lines)
    list1 = collapse((n, r) for w in wls for n, r in w.steps)
    x = len(list1)
    total_app = sum(len(e.trail) for e in list1)
    y = len(wls)
    lines.append(f"── LIST 1 · VISUAL OBJECTS (X={x} distinct · {total_app} appearances total) ──")
    for e in list1:
        lines.append("  " + object_line(e, verbose))
    lines.append(f"── LIST 2 · ### WORLDLINES — {y_label(y, lives_observed)} "
                 f"— each ###'s distinct visual objects ──")
    for w in sorted(wls, key=lambda w: w.id):
        entries = collapse(w.steps)
        distinct = len(entries)
        app = sum(len(e.trail) for e in entries)
        classes = sorted({e.value for e in entries})
        ccs = sorted({len(e.cells) for e in entries})
        cc = f"{ccs[0]}" if len(ccs) == 1 else f"{ccs[0]}–{ccs[-1]}"
        hlr, hlc = location(c for e in entries for c in e.cells)
        activity = "STATIC" if distinct == 1 else "ACTIVE"
        lines.append(f"  ###{w.id:03d} · {class_field(classes)} · {cc} cells · NW ({hlr},{hlc}) · "
                     f"{distinct} visual object(s) · {app} appearance(s) · {activity}")
        for e in entries:
            lines.append("      ▪ " + object_line(e, verbose))
    ratio = (x / y) if y else 0.0
    lines.append(f"── X→Y ── X={x} distinct visual objects → {y_label(y, lives_observed)} · X/Y = {ratio:.2f} ──")
    return "\n".join(lines)


# ── LIST 3 (G1-03) ─────────────────────────────────────────────────────────────────────────
# Transcription origin (R-C): virelai_v4/diagnostics/integration_roster.py:426-546 — the row
# format `###id · class · B1 STATE(cov n[, revisit k]) · B2 ROLE` and the "one row per ###, one
# producer" rule. NOT carried: the `/CONF` suffix (R-K: no strength), the `contact` column (Rung 3),
# the shared-parallax header (v4's `_L3_SHARED_PARALLAX_MIN` is a chosen number). NEW: the EGO
# block — one line per composite ego naming its kind and members (R-F, R-L), with the bearing
# table (Unlock 1's observable); the GROUND block (G3-01, R-M) — one line per fold naming its
# fragments and the per-button exchange table, the inverse of the bearing table.

def _b1_cell(v) -> str:
    if not v.band1:
        return "(not observed)"
    show = v.revisits and v.band1 != "STATIC"
    return f"{v.band1}(cov {v.coverage}{f', revisit {v.revisits}' if show else ''})"


def render_list3(read, worldlines: Sequence[Worldline]) -> str:
    """LIST 3: one row per ###; then the EGO block — exactly one line per sealed ego."""
    lines: List[str] = [
        "── LIST 3 · ### SEMANTIC ROLE — one row per ###, single producer: roles.infer.infer_roles ──",
        f"   B1 = did this ### ever change, over its coverage · B2 = the role, ∅ = none earned · typed: {read.typed}",
    ]
    for w in sorted(worldlines, key=lambda w: w.id):
        v = read.verdicts[w.id]
        entries = collapse(w.steps)
        cf = class_field(sorted({e.value for e in entries}))
        if v.band2 is None:
            b2 = "∅"
        elif v.band2 == "EGO":
            b2 = f"{v.band2}({v.ego_kind})" + (
                f" ⊂ {'+'.join(f'###{m:03d}' for m in v.members)}" if len(v.members) > 1 else "")
        elif v.band2 == "GROUND":
            b2 = "GROUND" + (f" ⊂ fold of {len(v.members)}" if len(v.members) > 1 else "")
        else:
            b2 = v.band2
        lines.append(f"  ###{w.id:03d} · {cf} · B1 {_b1_cell(v)} · B2 {b2}")
    ground = getattr(read, "ground", None)
    if ground is not None and (ground.verdicts or not read.bodies):
        lines.append("── GROUND · the fold, read off the sealed ego (R-M); exact exchange, no number ──")
        if not ground.verdicts:
            lines.append(f"  none — {ground.typed}")
        for gv in ground.verdicts:
            lines.append(f"  GROUND · {'+'.join(f'###{m:03d}' for m in gv.members)} · {gv.basis}")
            lines.append(f"      parallax: {gv.parallax}")
    walls = getattr(read, "walls", None)
    if walls is not None and read.bodies:
        lines.append("── WALL · the refused transition on a single-fingerprint worldline (R-I); egos and ground excluded ──")
        lines.append(f"  {walls.typed}")
        for wid, wv in sorted(walls.verdicts.items()):
            lines.append(f"  WALL · ###{wid:03d} · {wv.basis}")
            lines.append(f"      parallax: {wv.parallax}")
        if walls.changing_blockers:
            lines.append("  changing blocker(s), not WALL: " + ", ".join(f"###{w:03d}" for w in walls.changing_blockers))
    counters = getattr(read, "counters", None) or {}
    if counters:
        lines.append("── COUNTER · ticks on every un-targeted press (channel b); the fill and the empty both seal ──")
        for wid, cv in sorted(counters.items()):
            lines.append(f"  COUNTER · ###{wid:03d} · {cv.basis}")
            lines.append(f"      parallax: {cv.parallax}")
    levers = getattr(read, "levers", None)
    if levers is not None and read.typed != "nothing: action-blind record":
        lines.append("── LEVER · a press attributed to it changed a third worldline, after the ego's and the counter's cells (R-G) ──")
        lines.append(f"  {levers.typed}")
        for wid, lv in sorted(levers.verdicts.items()):
            lines.append(f"  LEVER · ###{wid:03d} · {lv.basis}")
            lines.append(f"      parallax: {lv.parallax}")
        for p in levers.unattributed_residue:
            own = ", ".join(f"###{w:03d}×{n}" for w, n in sorted(p.partners.items())) or "cells of no surviving owner"
            lines.append(f"  unattributed residue · press {p.left}→{p.right} · A{p.action} · {len(p.residue)} cell(s) on {own}")
    lines.append("── EGO · one line per sealed ego (R-F: one kind per world; R-L: lockstep members fold) ──")
    if not read.bodies and read.pointer is None:
        lines.append("  none sealed — " + read.typed)
    for ev in read.bodies:
        lines.append(f"  EGO(BODY) · {'+'.join(f'###{m:03d}' for m in ev.members)} · {ev.basis}")
        lines.append(f"      parallax: {ev.parallax}")
    if read.pointer is not None:
        p = read.pointer
        lines.append(f"  EGO(POINTER) · god mode · no footprint · {p.basis}")
        lines.append(f"      parallax: {p.parallax}")
    return "\n".join(lines)
