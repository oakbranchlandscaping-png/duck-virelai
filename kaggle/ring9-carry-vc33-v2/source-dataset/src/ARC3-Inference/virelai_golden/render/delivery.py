"""RENDER · the DELIVERY ROSTER and the record header. Formats only; computes nothing.

Transcription origin (R-C): virelai_v4/diagnostics/integration_roster.py:549-585
`render_delivery_roster` @ oracle-v4 — line format kept byte-identical so a golden roster can be
diffed against the v4 logs of 2026-09-05. What it proved: printed on both golden ls20 runs.

Note on node numbering, measured: v4's live log numbered the harness recording's line k as
node k+1 in run 1 (its node 0 was the reset frame the harness never wrote) and as node k−32 in
run 2 (its log restarted after the level-up at line 31). Golden numbers the recording's lines
from 0, whole game. Diff against v4 after shifting.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from virelai_golden.substrate.delivery import Delivery
from virelai_golden.substrate.record import Record


def _actions_line(record: Record) -> str:
    if record.action_channel.startswith("BLIND"):
        return (f"  actions: {record.action_channel} — the harness placeholder; what was pressed "
                f"is not in this record")
    counts = Counter(n.action[0] for n in record.nodes if n.action is not None)
    per = " ".join(f"A{a}:{c}" for a, c in sorted(counts.items()))
    return f"  actions: {record.action_channel} · {per}"


def render_record_header(record: Record, skipped: int) -> str:
    n = record.nodes
    lines = [
        f"########## RECORD · {record.game_id} ##########",
        f"  nodes {len(n)} · lives {record.lives} · deaths at {list(record.deaths)} · "
        f"level-ups at {list(record.level_ups)} · multi-grid at {list(record.multi_grid)}",
        f"  origin: {record.origin}",
        _actions_line(record),
        f"  skipped lines: {skipped}",
        f"  grid {n[0].settled.shape[0]}x{n[0].settled.shape[1]} · win_levels {n[0].win_levels} · "
        f"available {list(n[0].available_actions)}",
    ]
    return "\n".join(lines)


def render_delivery_roster(rows: Sequence[Delivery], nodes: int) -> str:
    out = ["########## DELIVERY ROSTER · what the platform handed, per turn ##########",
           "  (a DELIVERY fact, never an outcome — a single-grid turn reads SILENT "
           "however much the world moved)"]
    if not nodes:
        out.append("  no capture record — absence, not a run without animation.")
        out.append("########## END DELIVERY ROSTER ##########")
        return "\n".join(out)
    multi = [r for r in rows if r.layer_count > 1]
    for r in multi:
        out.append(f"  node {r.node}  {r.layer_count} grids  {r.klass}  "
                   f"interior cells moved {r.magnitude}")
    if not multi:
        out.append("  every turn delivered a single grid — no animation in this record.")
    out.append(f"  multi-grid deliveries  {len(multi)} of {nodes}")
    out.append("########## END DELIVERY ROSTER ##########")
    return "\n".join(out)
