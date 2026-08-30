"""WO_VERB_STREAM_01 · the shared verb-stream renderer — rung four made visible.

The single home of the verb-stream block, lifted out of ``dossier/canary_dossier.py``
so both the offline dossier and the live ``render_stages`` final artifact render it
ONCE. Mirrors ``weave/acted_on_render.py``, which records the same lift for the same
reason: one renderer, two callers, no second implementation.

WEAVE-SOURCED ONLY: renders over the weave ``###`` roster — worldlines (their edges
and verbs) plus the flattened window cascade from ``worldline.window_edges``. NO Slot,
NO belief, NO context, NO perception. Reads nothing, writes nothing. Game-free.

TWO POPULATIONS, NEVER ONE (SPEC_LEXICON_LIBRARY_v1 §5) — this is the block's whole
honesty argument, and it is structural, not stylistic:

  · THE PER-WORLDLINE STREAM comes from ``Worldline.verbs``, whose alphabet is the
    five ``_CONTINUE`` verbs (STILL · RECOLOR · MOVE · GROW · SHRINK) plus DEFORM.
    ``BIRTH`` seeds a worldline rather than extending one; ``DEATH``/``DEFORM``/
    ``AMBIGUOUS`` terminate with no edge appended (``worldline.py`` threader loop).
    So ``AMBIGUOUS`` can NEVER appear in a worldline's stream, and every ``DEFORM``
    that does appear is the bridge ``rejoin._merge`` manufactures across a re-join —
    not a cascade verdict. A per-worldline residual line would therefore read
    ``AMBIGUOUS 0`` on every worldline, always: a coverage claim true by construction
    is a lie in the spec's format, and worse than no reading at all.

  · THE WINDOW RESIDUAL CENSUS comes from ``window_edges``, which flattens EVERY
    cascade verdict including the terminating ones the worldlines drop. This is the
    only population in which BIRTH / DEATH / AMBIGUOUS are countable, and therefore
    the only honest coverage reading.

Behaviour is byte-identical to the ``canary_dossier`` original at the default call —
that identity is the lift's own correctness proof, pinned by
``tests/weave/test_verb_stream_render.py``. The one added parameter,
``max_stream``, is OFF by default and follows ``render_acted_on_block``'s
``footprint_key`` precedent (WO-W2-D-01: a real instrument for a real audience, behind
a switch, never deleted): the offline dossier renders a pinned 7-node window, while the
live ``--dossier-final`` path renders a full run of ~1300 nodes, where one unbounded
line per worldline is not an artifact anyone can read. Truncation states its own count,
so a truncated stream never reads as a complete one.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from virelai_v4.weave.edge import Verb

# The census population, in report order. These are exactly the verbs the threader
# drops (BIRTH seeds elsewhere; DEATH/DEFORM/AMBIGUOUS terminate), which is why the
# census — not the per-worldline stream — is where they must be counted.
RESIDUAL_KINDS: Tuple[Verb, ...] = (Verb.BIRTH, Verb.DEATH, Verb.DEFORM, Verb.AMBIGUOUS)


def _verb_token(edge) -> str:
    v = edge.verb
    if v is Verb.RECOLOR:
        return f"RECOLOR{edge.delta}"
    if v is Verb.GROW:
        return f"GROW(+{edge.delta})"
    if v is Verb.SHRINK:
        return f"SHRINK({edge.delta})"
    if v is Verb.MOVE:
        return f"MOVE{edge.delta}"
    if v is Verb.STILL:
        return "STILL"
    return v.name          # DEFORM (R2c re-join bridge), etc. — labelled honestly


def _stream_str(wl, max_stream: Optional[int]) -> str:
    """The dot-joined verb stream. ``max_stream=None`` renders every edge — the
    byte-identical original. An int caps the rendered tokens and STATES the count it
    withheld, so a bounded stream is never mistaken for a complete one."""
    if not wl.edges:
        return "—(no transitions)"
    total = len(wl.edges)
    if max_stream is None or total <= max_stream:
        return "·".join(_verb_token(e) for e in wl.edges)
    shown = "·".join(_verb_token(e) for e in wl.edges[:max_stream])
    return f"{shown}· … (+{total - max_stream} more of {total} edges)"


def _marginal_str(panel, wid) -> str:
    """`` · indep=X depend=Y (t/u/l)`` for one worldline, from the PanelRow the acted-on
    block already built.

    WO-MARGINAL-CHANNEL-01 computed these every run and rendered them nowhere, which is
    why its CORRECTNESS grade stood ungraded rather than passed. `indep` is the rate at
    which this worldline moved on presses that targeted SOMETHING ELSE; `depend` the rate
    on presses that targeted IT. Together they separate a clock from a lever, and until
    now a reader had to take that separation on trust.

    THREE DISTINCT ABSENCES, THREE DISTINCT MARKERS — never a zero. A missing number
    rendering as `0.00` is exactly the failure the marginal itself carried before it was
    fixed (a count-invariant worldline could only ever read `0.000`, and that structural
    zero was indistinguishable from a measured one). So:

      ``marginal unavailable``  — no panel at all; the fenced coupling read raised.
      ``not in panel``          — panel exists, this worldline absent from it.
      ``n/a``                   — the rate itself is -1.0, `_action_marginal`'s own honest
                                  signal for an empty denominator (no presses of that kind).
    """
    if panel is None:
        return " · marginal unavailable"
    row = panel.get(wid)
    if row is None:
        return " · marginal: not in panel"
    def _r(v):
        return "n/a" if v is None or v < 0 else f"{v:.2f}"
    return (f" · indep={_r(row.action_independence)} depend={_r(row.action_dependence)}"
            f" (t={row.targeted_presses} u={row.untargeted_presses} live={row.live_presses})")


def _worldline_line(wl, max_stream: Optional[int] = None, panel=None) -> str:
    anchors = {e.anchor.value for e in wl.edges}
    tag = next(iter(anchors)).lower() if len(anchors) == 1 else ("--" if not anchors else "mixed")
    stream = _stream_str(wl, max_stream)
    cls = wl.first_region.class_id
    return (f"###{wl.id:03d} [{tag}] c{cls} @node{wl.first_node} "
            f"(seen {len(wl.steps)}) : {stream}{_marginal_str(panel, wl.id) if panel is not None else ''}")


def render_verb_stream_block(worldlines, edges_ctx, a: int, b: int,
                             *, max_stream: Optional[int] = None, panel=None) -> str:
    """The verb-stream block: per-worldline streams, then the window residual census.

    ``worldlines`` — the re-joined ``###`` roster; ``edges_ctx`` — ``window_edges``
    output, ``(from_node, to_node, edge)`` over the whole window. ``a``/``b`` name the
    window for the header only.

    ``max_stream`` is OFF by default so the offline dossier's rendered bytes are
    unchanged by this module's existence (see module docstring).

    ``panel`` (WO-SPLIT-AND-SHOW-01) — the ``{wid: PanelRow}`` mapping the acted-on block
    already built, threaded in rather than recomputed. When given, each worldline's line
    carries its action marginal beside its verb-stream: what it did each press, next to
    whether it moved when touched versus untouched. When ``None`` (the offline dossier,
    and every caller predating this WO) no marginal is rendered at all and the block is
    byte-identical to before — the same switched-instrument discipline as ``max_stream``.
    """
    lines: List[str] = [f"WORLDLINES (window {a}..{b}) · {len(worldlines)} ### objects"]
    for wl in worldlines:
        lines.append("  " + _worldline_line(wl, max_stream, panel))

    counts = {k: [] for k in RESIDUAL_KINDS}
    recolor = 0
    for from_node, to_node, e in edges_ctx:
        if e.verb is Verb.RECOLOR:
            recolor += 1
        if e.verb in counts:
            if e.verb is Verb.BIRTH:
                r = e.now
                counts[e.verb].append((to_node, r.class_id, r.cell_count))
            else:
                r = e.prev
                counts[e.verb].append((from_node, r.class_id, r.cell_count))

    lines.append("RESIDUALS: " + " · ".join(
        f"{k.value} {len(counts[k])}" for k in RESIDUAL_KINDS))
    for k in RESIDUAL_KINDS:
        for (node, cls, ncells) in counts[k]:
            lines.append(f"    {k.value} @node{node} c{cls} ({ncells} cells)")
    lines.append(f"DECORRELATION: RECOLOR count = {recolor}   "
                 f"(must be 0 on vc33)")
    return "\n".join(lines)
