"""WO-R1′-01 · THE ARTIFACT — ``semantic object ← ### ← visual objects``.

The compression trail on one page, traceable to pixels:

    cells → visual objects → ### identity across grids → semantic role

A reader grades this without a key, because the evidence is on the page. That is
the point: the corpus holds exactly ONE hand-authored foundation key, and keys are
ungeneratable by construction (``solver output consulted: NONE`` — WO-UNIFY-00 Q3),
so a mechanical gate cannot scale. A keyless artifact that runs on every world can.

WHAT MAKES IT HONEST — the attribution gate.
Store-A attributes evidence by mapping cells → region through the SPAWN-FROZEN
footprint (``delta_updater._build_cell_to_region:47-54``, used at ``:133-142``;
``:128-130`` notes those regions drive ``reacts_to`` attribution AND the Action
Independence Metric). ``library_sync`` populates objects once at spawn (Mode A,
``:292``) and never relocates ``obj.cells``. So for an object whose footprint
MOVED, Store-A's ``change_count``/``reacts_to`` describe whatever crossed its
frame-1 patch — not the object's own trail.

Therefore every evidence line is gated on footprint-invariance, and the verbs
say it exactly (``edge.py:28-37``):
  * ``STILL``   — "same footprint, same class"    → footprint held → ✓ attributable
  * ``RECOLOR`` — "same footprint, class changed" → footprint held → ✓ attributable
  * ``MOVE`` / ``GROW`` / ``SHRINK`` / ``DEFORM`` / ``BIRTH`` / ``DEATH`` /
    ``AMBIGUOUS`` — the footprint moved or has no stable partner → ⚠ NOT attributable

Note this is NOT ``still_bridge``'s predicate. That one is fingerprint-invariance
``(class_id, cells)``, which excludes RECOLOR. Attribution keys on CELLS ONLY, so
a RECOLOR is attribution-honest even though its fingerprint changes. Using the
fingerprint predicate here would falsely condemn every recolour.

The ⚠ line is not a caveat — it is the deliverable's value. It makes a live
belief defect unignorable on every world, keylessly, without asserting anything
the page cannot show.

PURE READ. Renders belief; writes none. Reuses the existing semantic verdict
(``render_read`` → the Store-A axes) — roles are never re-derived here.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from virelai_v4.diagnostics.store_a_readout import render_read

# The two verbs whose own docstrings say "same footprint" — the exact set for
# which Store-A's cell-keyed attribution still lands on the right object.
_FOOTPRINT_HELD = frozenset({"STILL", "RECOLOR"})

_CELL_CAP = 8


def _verb_name(v: Any) -> str:
    return getattr(v, "value", None) or getattr(v, "name", None) or str(v)


def footprint_held(worldline: Any) -> bool:
    """True when this ### never moved its footprint — the attribution-honesty
    predicate. A worldline with no transitions (seen once) trivially held."""
    return all(_verb_name(v) in _FOOTPRINT_HELD for v in getattr(worldline, "verbs", ()))


def _region_txt(r: Any) -> str:
    a, b = getattr(r, "anchor", None), getattr(r, "bbox", None)
    a_txt = f"@{tuple(a)}" if a else "@?"
    b_txt = f"{b[0]}x{b[1]}" if b else "?x?"
    return (f"class {getattr(r, 'class_id', '?')} {a_txt} {b_txt} "
            f"{getattr(r, 'cell_count', '?')} cells")


def _evidence_txt(obj: Any) -> str:
    """Only what the belief actually carries — absent fields are marked absent,
    never approximated (WO-DOSSIER-00 Q3b: these are aggregate; the per-node
    click list does not exist on the object)."""
    bits: List[str] = []
    cc = getattr(obj, "change_count", 0)
    bits.append(f"self-changed {cc}x" if cc else "no self-change")
    reacts = tuple(getattr(obj, "reacts_to", ()) or ())
    if reacts:
        bits.append("drove " + ", ".join(f"R{r}" for r in reacts))
    fa, la = getattr(obj, "first_active_frame", -1), getattr(obj, "last_active_frame", -1)
    if fa is not None and fa >= 0:
        bits.append(f"active #{fa}-#{la}")
    lp = getattr(obj, "last_probe_frame", -1)
    if lp is not None and lp >= 0:
        bits.append(f"last probed #{lp}")
    return " · ".join(bits) if bits else "(no evidence recorded)"


def _lineage_rows(wl: Any) -> List[str]:
    """One row per node in the trail — every step, not endpoints — each annotated
    with the verb that produced it (``edges[i-1]`` links ``steps[i-1]→steps[i]``)."""
    out: List[str] = []
    steps = tuple(getattr(wl, "steps", ()) or ())
    edges = tuple(getattr(wl, "edges", ()) or ())
    for i, (node_index, region) in enumerate(steps):
        verb = f"   {_verb_name(edges[i - 1].verb)}" if i and i - 1 < len(edges) else ""
        out.append(f"      <- visual object {_region_txt(region)}   node {node_index}{verb}")
    return out


def _wl_header(wl: Any) -> str:
    steps = tuple(getattr(wl, "steps", ()) or ())
    nodes = [n for n, _r in steps]
    span = f"#{nodes[0]}-#{nodes[-1]}" if nodes else "(no trail)"
    kind = "FOOTPRINT-HELD" if footprint_held(wl) else "MOVER"
    return (f"  <- worldline ###{getattr(wl, 'id', '?'):03d}   {kind} · "
            f"seen {len(steps)} nodes ({span})")


def render_lineage(library: Any,
                   worldlines: Iterable[Any],
                   bindings: Dict[int, int]) -> str:
    """``semantic ← ### ← visual objects``, with the evidence line gated on
    footprint-invariance. PURE READ.

    ``bindings`` is ``{worldline_id: region_id}`` from ``bind_worldlines_to_slots``.
    The binding is many-to-one — measured on a live canary at roughly 87 worldlines
    → 37 bound → 32 regions, because re-births across lives share a spawn footprint
    — so a slot lists EVERY ### bound to it, never a dominant pick.
    """
    wl_by_id = {getattr(w, "id", None): w for w in worldlines}
    objects = getattr(library, "objects", {}) or {}

    by_region: Dict[int, List[int]] = {}
    for wid, rid in (bindings or {}).items():
        by_region.setdefault(rid, []).append(wid)

    L: List[str] = []
    L.append("########## SEMANTIC <- ### <- VISUAL OBJECTS  (lineage; pure read) "
             "##########")
    L.append("  cells -> visual objects -> ### identity across grids -> semantic role")
    L.append("")

    slotless: List[int] = []
    for rid in sorted(objects.keys()):
        obj = objects[rid]
        tag, role, loc, _conf = render_read(obj)
        loc_txt = f" · {loc}" if loc else ""
        L.append(f"R{rid} · {tag}·{role or '—'}{loc_txt}          [Store-A verdict]")

        wids = sorted(by_region.get(rid, []))
        if not wids:
            slotless.append(rid)
            L.append("  <- (no ### bound — semantic object with no observed trail)")
            L.append("")
            continue

        for wid in wids:                       # every bound ###, never last-wins
            wl = wl_by_id.get(wid)
            if wl is None:
                continue
            L.append(_wl_header(wl))
            L.extend(_lineage_rows(wl))
            if footprint_held(wl):
                L.append(f"  evidence: OK attributable — {_evidence_txt(obj)}")
                L.append("            (this ### never moved: its frame-1 footprint "
                         "IS its footprint)")
            else:
                L.append("  evidence: !! NOT ATTRIBUTABLE — this ### moved. Store-A "
                         f"keys evidence to R{rid}'s frame-1 footprint")
                L.append("            (delta_updater:47-54,133-142), so "
                         f"R{rid}'s change_count/reacts_to describe whatever crossed")
                L.append("            that patch, not this object's trail.")
        L.append("")

    unbound = [w for w in worldlines if getattr(w, "id", None) not in (bindings or {})]
    L.append(f"### WITH NO SEMANTIC OBJECT — {len(unbound)} of {len(wl_by_id)} "
             "worldlines (mid-run births / transients):")
    if unbound:
        L.append("  (the solver saw these; the semantic layer has no name for them)")
        for wl in unbound:
            L.append(_wl_header(wl).replace("  <- worldline", "  worldline"))
            L.extend(_lineage_rows(wl))
    else:
        L.append("  (none)")
    L.append("")
    L.append(f"SEMANTIC OBJECTS WITH NO ### — {len(slotless)} of {len(objects)}"
             + (": " + ", ".join(f"R{r}" for r in slotless) if slotless else ""))
    return "\n".join(L)
