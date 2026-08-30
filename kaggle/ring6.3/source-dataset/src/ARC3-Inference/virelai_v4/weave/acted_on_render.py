"""WO_ACTED_ON_FINAL_RENDER_HOOK + WO_ACTED_ON_FOOTPRINT_KEY · the shared acted-on renderer.

The single home of the acted-on block, lifted out of ``dossier/canary_dossier.py`` so
both the offline dossier and the live ``render_stages`` final artifact render it ONCE.

WEAVE-SOURCED ONLY (Director ruling 2026-07-12): renders over the weave ``###`` roster —
cuts + worldlines + the sidecar-sourced per-node actions. NO Slot, NO belief, NO context.
Each captain action resolves against ``cut[t-1]`` (the wiring law). Game-free; no
is_background, no label, no snapping.

TWO-GRADE (SPEC_WEAVE §6): the block is human-gradable against the replay `.json`:
  · a COMPACT INLINE locator per node (class · bbox · cell_count at t-1), and
  · a FOOTPRINT KEY APPENDIX: per distinct acted-on ###, its FULL cell footprint AT t-1
    (raw grid coords — they match the replay grid directly, no transform), with the
    clicked cell marked ``*(r,c)*``. Re-clicks of the same ### at the same footprint are
    deduped; a ### clicked at DIFFERENT footprints (it moved between clicks) lists EACH
    distinct ``(t-1 node, footprint)`` — never collapsed to one (that would be a false key).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.weave.action_roster import (
    acted_on, is_boundary_pre, format_resolution, RESOLVED, EMPTY, OUT_OF_WINDOW, NON_TARGETED,
)
from virelai_v4.weave.worldline import region_at


def _bbox_str(region) -> str:
    (r0, c0) = region.anchor
    (h, w) = region.bbox
    return f"r[{r0}-{r0 + h - 1}] c[{c0}-{c0 + w - 1}]"


def _footprint_str(region, clicked_cells) -> str:
    """Full sorted cell list at t-1; every clicked cell marked ``*(r,c)*``."""
    clicked = set(clicked_cells or ())
    parts = []
    for cell in sorted(region.cells):
        parts.append(f"*({cell[0]}, {cell[1]})*" if cell in clicked else f"({cell[0]}, {cell[1]})")
    return " ".join(parts)


# --- WO-W2-D-01 · RND-2 frictions, and the empty/failed distinction ----------
#
# The coupling and role reads are fenced so they can never perturb the artifact. That
# fence stays. What it used to swallow was the REASON — `except Exception: pass` left a
# blank that read identically to "nothing to say", and a reader could not tell a crashed
# instrument from a clean board. Per RND-2: C1 state it · C2 the mechanism, not the
# symptom · C4 a PRESENT sentence where the block would be · C5 every noun a real
# artifact. The friction replaces the SILENCE, not the fence.

def _friction(subject: str, mechanism: str, exc: BaseException) -> str:
    """A typed friction: what is unavailable, which named artifact failed, and how."""
    return (f"FRICTION · {subject} UNAVAILABLE — {mechanism} raised "
            f"{type(exc).__name__}: {exc}. The read is fenced so it cannot perturb the "
            f"artifact; this line replaces the silence, not the fence.")


def _nothing_to_measure(subject: str) -> str:
    """An empty result is a finding, not a failure — and must not read as one."""
    return (f"{subject}: no worldlines in this window — nothing to measure. "
            f"An empty result is a finding, not a failure.")


def render_acted_on_block(window_cuts, worldlines,
                          node_actions: List[Tuple[Any, Any]],
                          *, footprint_key: bool = False,
                          panel_sink: Optional[Dict[str, Any]] = None) -> str:
    """The acted-on block: compact inline per node, plus the footprint-key appendix when
    ``footprint_key`` is set.

    WO-W2-D-01 — the appendix is OFF by default. It is a real instrument for a real
    audience (machine cross-check of the t-1 footprints against the replay ``.json``), and
    that audience is not in the room: it was 557 of the block's 703 lines on the last
    canary. Labeled and consciously ignored, behind a switch — never deleted.

    WO-SPLIT-AND-SHOW-01 — ``panel_sink``: an optional caller-supplied dict this function
    fills with ``{"panel": <PanelRow mapping or None>}``. The coupling report built below
    was previously used once and discarded; the verb-stream block needs its action
    marginals, and building a second report would be a second full computation of the
    same thing. A sink rather than a changed return type so EVERY existing caller is
    byte-neutral — the return stays ``str``, and a caller that passes nothing sees no
    difference at all. ``panel`` is left ``None`` when the fenced coupling read raises, so
    an absent reading is renderable as an absence rather than as a zero."""
    cut_by_idx = {c.node_index: c for c in window_cuts}
    wl_by_id = {wl.id: wl for wl in worldlines}
    lo = min(cut_by_idx) if cut_by_idx else 0
    hi = max(cut_by_idx) if cut_by_idx else 0
    lines: List[str] = [
        f"ACTED-ON (nodes {lo}..{hi} · weave ### roster · resolved against cut[t-1])"]
    n_res = n_empty = n_non = n_oow = 0
    # appendix accumulator keyed by (wl_id, footprint frozenset) -> distinct-footprint entry
    appendix: Dict[Tuple[int, frozenset], Dict[str, Any]] = {}

    for cut in window_cuts:
        t = cut.node_index
        aid, target = node_actions[t] if 0 <= t < len(node_actions) else (None, None)
        boundary = " ⚠(t-1 life boundary)" if is_boundary_pre(cut_by_idx, t) else ""
        res = acted_on(t, aid, target, cut_by_idx, worldlines)

        if res.status == RESOLVED:
            n_res += 1
            wl = wl_by_id.get(res.worldline_id)
            region = region_at(wl, t - 1) if wl is not None else None
            if region is None:
                # D-D: honest — never fall back to first_region / fabricate
                lines.append(f"  node {t}: action {aid} @({target[0]},{target[1]}) → "
                             f"acted on ###{res.worldline_id:03d} · footprint unavailable @ t-1 node {t-1}")
            else:
                lines.append(
                    f"  node {t}: action {aid} @({target[0]},{target[1]}) → acted on "
                    f"###{res.worldline_id:03d} · class {region.class_id} · bbox {_bbox_str(region)} "
                    f"· {region.cell_count} cells{boundary}")
                key = (res.worldline_id, frozenset(region.cells))
                entry = appendix.setdefault(key, {
                    "wl_id": res.worldline_id, "cls": region.class_id, "region": region,
                    "t1_nodes": set(), "clicked": set()})
                entry["t1_nodes"].add(t - 1)
                entry["clicked"].add(target)
        elif res.status == EMPTY:
            n_empty += 1
            lines.append("  " + format_resolution(t, res))
        elif res.status == OUT_OF_WINDOW:
            n_oow += 1
            lines.append("  " + format_resolution(t, res))
        else:
            n_non += 1
            lines.append("  " + format_resolution(t, res))

    lines.append(f"  summary: {n_res} acted-on-###, {n_empty} EMPTY (out-of-bounds), "
                 f"{n_non} non-targeted, {n_oow} out-of-window")

    # --- COUPLING DETECTOR (weave-native, derived-not-stored, dossier-only; R1) ---
    #
    # WO-SPLIT-AND-SHOW-01: the `PanelRow` mapping built here is now CAPTURED rather than
    # discarded, so the verb-stream block can render each worldline's action marginal
    # beside its stream. NO SECOND `build_coupling` CALL — this is the same single build
    # this function has always performed, in the same try/except, at the same cadence;
    # only its lifetime changes. (`infer_roles` performs its own separate build; that
    # duplication is a real finding and is out of this fence.)
    #
    # It stays inside the fence: if the coupling read raises, `panel` remains None and the
    # verb-stream renderer prints an explicit absence marker. A failed read must never
    # reach a reader as a zero — that is precisely the failure the action marginal itself
    # carried before WO-MARGINAL-CHANNEL-01.
    panel = None
    try:
        from virelai_v4.weave.coupling import build_coupling, render_coupling_block
        report = build_coupling(worldlines, window_cuts, node_actions)
        panel = report.panel
        lines.append("")
        if report.pairs or report.panel:
            lines.append(render_coupling_block(report, worldlines))
        else:
            lines.append(_nothing_to_measure("COUPLING"))
    except Exception as exc:   # the coupling read never perturbs the artifact
        lines.append("")
        lines.append(_friction(
            "COUPLING PANEL",
            "weave/coupling.py::build_coupling / render_coupling_block", exc))

    # --- ROLE INFERENCE (weave-native, derived-not-stored, dossier-only) ---
    try:
        from virelai_v4.weave.role_read import infer_roles, render_roles_block
        verdicts = infer_roles(worldlines, window_cuts, node_actions)
        lines.append("")
        if verdicts:
            lines.append(render_roles_block(verdicts, worldlines))
        else:
            lines.append(_nothing_to_measure("ROLE INFERENCE"))
    except Exception as exc:   # the role read never perturbs the artifact
        lines.append("")
        lines.append(_friction(
            "ROLE INFERENCE",
            "weave/role_read.py::infer_roles / render_roles_block", exc))

    # --- the FOOTPRINT KEY appendix (WO-W2-D-01: switched, never deleted) ---
    if footprint_key and appendix:
        lines.append("")
        lines.append("ACTED-ON FOOTPRINT KEY (cells at t-1 · raw grid coords · * = clicked cell) "
                     "— cross-check vs .json")
        for (_, _), e in sorted(appendix.items(), key=lambda kv: (kv[1]["wl_id"], sorted(kv[1]["t1_nodes"]))):
            nodes = ",".join(str(n) for n in sorted(e["t1_nodes"]))
            marked = e["clicked"] & set(e["region"].cells)   # clicked cells inside this footprint
            lines.append(
                f"  ###{e['wl_id']:03d} @ t-1 node {nodes} · class {e['cls']} · "
                f"{e['region'].cell_count} cells: [{_footprint_str(e['region'], marked)}]")
    if panel_sink is not None:
        panel_sink["panel"] = panel

    return "\n".join(lines)
