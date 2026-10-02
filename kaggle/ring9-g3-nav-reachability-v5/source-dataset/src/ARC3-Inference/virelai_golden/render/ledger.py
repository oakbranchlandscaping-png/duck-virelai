"""RENDER · the ledger verdict block. Formats only.

Transcription origin (R-C): virelai_v4/capture/ledger.py:83-99 `format_pristine` — the
PRISTINE line kept verbatim so it diffs against v4's seal-site print. The conservation and
distinct-object lines are golden's own (labeled).
"""
from __future__ import annotations

from typing import Dict, Sequence

from virelai_golden.substrate.ledger import PristineVerdict, Transition


def render_pristine(v: PristineVerdict) -> str:
    if v.passed:
        return f"SIGHTING-LEDGER PRISTINE: {v.n_nodes} nodes, {v.n_pass} round-trip PASS"
    node, cells = v.first_fail if v.first_fail else (-1, ())
    shown = ", ".join(f"({r},{c})" for r, c in cells[:8])
    more = " …" if len(cells) > 8 else ""
    return (f"SIGHTING-LEDGER PRISTINE: FAIL at node {node} — cells {{{shown}{more}}} "
            f"({v.n_pass}/{v.n_nodes} nodes passed)")


def render_conservation(transitions: Sequence[Transition]) -> str:
    n = len(transitions)
    closed = sum(1 for t in transitions if t.closes)
    held = sum(1 for t in transitions if t.changed_cells == 0)
    open_edges = [t.after for t in transitions if not t.closes]
    line = (f"CONSERVATION: {n} transitions, {closed} close exactly (Σ_c Δ_c = 0) · "
            f"{held} held the board (no cell changed class)")
    if open_edges:
        line += f" · OPEN at nodes {open_edges[:8]}{' …' if len(open_edges) > 8 else ''}"
    return line


def render_distinct(per_life: Dict[int, int]) -> str:
    parts = " · ".join(f"life {life}: {n}" for life, n in per_life.items())
    return f"DISTINCT VISUAL OBJECTS (fingerprint = class × cells): {parts}"
