"""WO_WEAVE_S1_PIN_AND_SEE · the raw dossier runner — RENDER's left column.

Resolves a pinned canary session, builds the Sighting Ledger over it, grades it
PRISTINE, and renders a self-naming raw dossier: a header carrying the pin
(game · hash · session basename · nodes · verdict) and, for a route_position
window, each node's object-list read straight from ``cut.regions``.

Raw only: no worldlines, no verbs, no matching (those are Weave Steps 2-3). The
per-node rows are sorted by the visual-object rule — ``|cells|`` ascending, then
``class_id`` ascending — so the smallest, most-legible objects read first.

Layering (locked by tests/dossier/test_dossier_fence.py): may import ``capture``
(ledger_build, clay, ledger) + ``canary_pins``; imports NO interpretation module
(library / captain / nested_read / render_read / classification / targeting).
"""

from __future__ import annotations

import argparse
from typing import List, Optional, Tuple

from virelai_v4.capture.canary_pins import (
    CANARY_PINS, resolve, session_basename,
)
from virelai_v4.capture.ledger_build import load_capture, ledger_from_capture
from virelai_v4.capture.ledger import grade_pristine
from virelai_v4.weave.worldline import weave_window, window_edges
from virelai_v4.weave.rejoin import re_join
from virelai_v4.weave.verb_stream_render import render_verb_stream_block


def _verdict_line(verdict) -> str:
    """Compress a ``PristineVerdict`` to one legible line."""
    if verdict.first_fail is None and verdict.n_pass == verdict.n_nodes:
        return f"PRISTINE: {verdict.n_pass}/{verdict.n_nodes} round-trip PASS"
    node, cells = verdict.first_fail if verdict.first_fail else (-1, [])
    shown = ", ".join(f"({r},{c})" for r, c in list(cells)[:8])
    more = " …" if len(cells) > 8 else ""
    return (f"DIVERGENCE at node {node} — cells {{{shown}{more}}} "
            f"({verdict.n_pass}/{verdict.n_nodes} passed)")


def _sorted_regions(cut):
    """Visual-object order: |cells| ascending, then class_id ascending."""
    return sorted(cut.regions, key=lambda r: (r.cell_count, r.class_id))


def _region_row(r) -> str:
    return f"    [class {r.class_id} | {r.cell_count} cells | anchor ({r.anchor[0]},{r.anchor[1]})]"


def render_from_cuts(game: str, cuts, verdict,
                     window: Optional[Tuple[int, int]] = None) -> str:
    """Pure renderer: build the self-naming dossier from already-assembled
    ``cuts`` + a ``PristineVerdict``. Header metadata (hash, session basename,
    default window) is read from the committed ``CANARY_PINS`` — no file access,
    so this is fixture-free and CI-safe. ``render_raw`` wraps it with the on-disk
    resolve + load + build + grade."""
    pin = CANARY_PINS[game]
    a, b = tuple(window) if window is not None else tuple(pin["window"])
    a = max(0, int(a))
    b = min(len(cuts) - 1, int(b))

    lines: List[str] = []
    # HEADER — the pin is on the artifact.
    lines.append(
        f"CANARY DOSSIER (raw) · {game} · hash {pin['hash']} · "
        f"{session_basename(game)} · nodes {len(cuts)} · {_verdict_line(verdict)}"
    )
    lines.append(f"WINDOW route_position [{a}..{b}]  (visual order: |cells| asc, class_id asc)")

    sample_done = False
    for k in range(a, b + 1):
        cut = cuts[k]
        regions = _sorted_regions(cut)
        lines.append(f"--- node {cut.node_index} ({len(regions)} objects) ---")
        for r in regions:
            lines.append(_region_row(r))
        # full cells for ONE sample region (the first row of the first node) —
        # counts everywhere else.
        if not sample_done and regions:
            s = regions[0]
            lines.append(
                f"    · sample full cells — class {s.class_id}, {s.cell_count} cells: "
                f"{sorted(s.cells)}"
            )
            sample_done = True

    return "\n".join(lines)


def render_raw(game: str, window: Optional[Tuple[int, int]] = None) -> str:
    """Render the self-naming raw dossier for a pinned canary ``game`` from disk:
    resolve the pin (loud FileNotFoundError if the gitignored session is absent),
    load the capture, build the ledger, grade PRISTINE, then render. ``window`` is
    an inclusive ``(a, b)`` route_position range; defaults to the pin's window."""
    pin = resolve(game)
    log = load_capture(pin["session"])
    cuts = ledger_from_capture(log)
    verdict = grade_pristine(cuts, log)
    return render_from_cuts(game, cuts, verdict, window)


# ---------------------------------------------------------------------------
# WOVEN — the RIGHT column: ### worldlines, residuals, decorrelation line.
# render_raw is unchanged; render_woven = raw LEFT + woven RIGHT.
#
# WO-VERB-STREAM-01: the three renderers that lived here (_verb_token,
# _worldline_line, _render_worldlines) were LIFTED VERBATIM to
# weave/verb_stream_render.py so the live --dossier-final path renders the same
# block from the same code, following weave/acted_on_render.py's precedent. This
# module's rendered bytes are unchanged by the lift; tests/weave/
# test_verb_stream_render.py pins that identity on both pinned canaries.
# ---------------------------------------------------------------------------


def render_woven(game: str, window=None) -> str:
    """Full woven dossier: the self-naming header + raw LEFT (unchanged) + the
    woven RIGHT (### worldlines, residuals, decorrelation line)."""
    pin = resolve(game)
    log = load_capture(pin["session"])
    cuts = ledger_from_capture(log)
    verdict = grade_pristine(cuts, log)

    a, b = tuple(window) if window is not None else tuple(pin["window"])
    a = max(0, int(a))
    b = min(len(cuts) - 1, int(b))
    window_cuts = cuts[a:b + 1]

    worldlines = re_join(weave_window(window_cuts), cuts=window_cuts)   # R2c: swept ground
    edges_ctx = window_edges(window_cuts)

    left = render_from_cuts(game, cuts, verdict, (a, b))
    right = render_verb_stream_block(worldlines, edges_ctx, a, b)
    return left + "\n\n" + right


# ---------------------------------------------------------------------------
# PROVENANCE — the OWNER-grain layer beneath the weave: cell -> (owner@t, owner@t+1),
# reactive-complement verdicts, count-grain self-check. render_woven is unchanged.
# ---------------------------------------------------------------------------

def _render_provenance(worldlines, window_cuts, a: int, b: int) -> str:
    from virelai_v4.weave.provenance import (
        owner_edge, complement_verdict, cell_owners, worldline_owner_index, is_total,
    )
    idx = worldline_owner_index(worldlines)
    cls = {wl.id: wl.first_region.class_id for wl in worldlines}
    lines: List[str] = [f"OWNER-PROVENANCE (window {a}..{b}) · every cell an owner, quiet earned per edge"]

    total_ok = all(is_total(cell_owners(c, idx), c) for c in window_cuts)
    lines.append(f"  TOTALITY: every cell owned at every node — {'YES' if total_ok else 'NO'}")

    complements, loud = [], []
    for i in range(len(window_cuts) - 1):
        ct, cn = window_cuts[i], window_cuts[i + 1]
        e = owner_edge(ct, cn, worldlines)
        exch_cells = sum(1 for (_, g, r) in e.exchanges if g in e.continuing and r in e.continuing)
        intr_cells = len(e.exchanges) - exch_cells
        lines.append(f"  edge {e.prev_node}->{e.now_node}: {exch_cells} exchanged, {intr_cells} intrinsic")
        for wl in worldlines:
            v = complement_verdict(wl, e)
            if not (v.exchange_cells or v.intrinsic_cells):
                continue
            parts = " ".join(f"->###{p:03d}:{len(c)}" for p, c in sorted(v.partners.items()))
            lines.append(
                f"      ###{wl.id:03d} c{cls[wl.id]}: exch {len(v.exchange_cells)} "
                f"[{parts}] · intrinsic {len(v.intrinsic_cells)}"
                f"{'  ⟵ REACTIVE-COMPLEMENT' if v.is_reactive_complement else ''}")
            if v.is_reactive_complement:
                complements.append((e.now_node, wl.id, cls[wl.id]))
            elif v.intrinsic_cells:
                loud.append((e.now_node, wl.id, cls[wl.id], len(v.intrinsic_cells)))

    lines.append("COMPLEMENT VERDICT:")
    lines.append("  reactive-complements (all churn exchange, quiet): " +
                 (", ".join(f"###{w:03d}(c{c})@n{n}" for (n, w, c) in complements) or "none"))
    lines.append("  loud (intrinsic residual): " +
                 (", ".join(f"###{w:03d}(c{c})@n{n}:{k}" for (n, w, c, k) in loud) or "none"))
    lines.append(f"CROSS-CHECK (count-grain): owner exchange totals balance (out==in), "
                 f"conserved-transfer parallel enforced in tests/weave/test_provenance.py::C3")
    return "\n".join(lines)


def render_provenance(game: str, window=None) -> str:
    """The woven dossier (unchanged) + the OWNER-PROVENANCE / reactive-complement layer."""
    pin = resolve(game)
    log = load_capture(pin["session"])
    cuts = ledger_from_capture(log)
    a, b = tuple(window) if window is not None else tuple(pin["window"])
    a = max(0, int(a))
    b = min(len(cuts) - 1, int(b))
    window_cuts = cuts[a:b + 1]
    worldlines = re_join(weave_window(window_cuts), cuts=window_cuts)   # R2c: swept ground
    prov = _render_provenance(worldlines, window_cuts, a, b)
    acted = _render_acted_on(game, pin, window_cuts, worldlines, a)
    return render_woven(game, (a, b)) + "\n\n" + prov + "\n\n" + acted


def _render_acted_on(game, pin, window_cuts, worldlines, a: int) -> str:
    """WO-A2-04 / RULING_A2_COMPLETION §1 — a TYPED FRICTION, not an acted-on block.

    This renderer previously loaded the sidecar-sourced per-node actions and
    rendered the block. Both halves of that are now gone:

      - The sidecar is retired as an action source. Its rows keyed on
        ``frame_index`` (== ``ctx.actions_this_life``, PERSIST_LEVELS_RESET_LIFE)
        while the node array is ``ctx.frame_record_log``
        (PERSIST_LIVES_RESET_LEVEL). No field in the record sits at the node
        array's lifetime tier — one key resets too often, the other never resets.
        Ruled on the live canary: 1222 of 1366 rows destroyed by last-write-wins,
        1265 of 1322 nodes wrong under BOTH candidate keys.

      - The log cannot substitute HERE. This is the OFFLINE path: its capture is
        loaded from a ``.recording.jsonl``, whose ``action_input`` is a harness
        placeholder (``id: 0``) on every framed line, by design. No recording
        carries the action taken. ``virelai.py`` already names it action-blind.

    So the offline acted-on oracle has no source, and the honest act is to SAY
    so. Silence is typed: an instrument that renders nothing is indistinguishable
    from one that ran and found nothing — the exact shape that let 89% record
    destruction run unnoticed for months.
    """
    return (
        "ACTED-ON — unavailable. This capture is action-blind by construction: the\n"
        "recording's action_input is a harness placeholder (id: 0), not the action taken.\n"
        "No index key reconciles the sidecar to the node array (RULING_A2_COMPLETION §1).\n"
        "The live acted-on render is available at render_stages --dossier-final."
    )


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m virelai_v4.dossier.canary_dossier",
        description="Render a self-naming raw canary dossier (per-node object-lists).",
    )
    p.add_argument("game", help="pinned canary game key (e.g. vc33, ls20)")
    p.add_argument("--window", nargs=2, type=int, metavar=("A", "B"),
                   help="inclusive route_position window; defaults to the pin's window")
    p.add_argument("--weave", action="store_true",
                   help="also thread the window into ### worldlines (woven dossier)")
    p.add_argument("--provenance", action="store_true",
                   help="also account cell ownership per edge (owner-provenance + reactive-complement)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    window = tuple(args.window) if args.window else None
    if args.provenance:
        render = render_provenance
    elif args.weave:
        render = render_woven
    else:
        render = render_raw
    print(render(args.game, window))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
