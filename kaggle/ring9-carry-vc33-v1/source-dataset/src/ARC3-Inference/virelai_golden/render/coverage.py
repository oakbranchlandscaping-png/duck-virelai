"""RENDER · coverage — TOUCHED / NOT REACHED / NEVER ATTEMPTED / GROUND-disregarded / UNREACHABLE, whole game.

Canon: 03 §5 (exhaustive by enumeration — the roster is the proof the enumeration terminated);
R-H (whole-game: a worldline attempted in life 1 is attempted; nothing resets); 02 §6.3 GROUND
exclusion discipline — "disregarded as a walk-to target and never masked — it stays in the
roster with its basis and its per-site entry count, and every queue entry it removes is
printed". Unlock 3 (LADDER_v1): NEVER ATTEMPTED 0 across lives; one role per line.

Transcription origin (R-C): virelai_v4/weave/collide_drive.py:1680-1744 `coverage_roster` (the
five statuses and the one-line-per-worldline form). What it proved: `NEVER ATTEMPTED 0` on the
click canary, 2026-09-05. Golden's statuses, derived from the record and the role read:
    TOUCHED          attempted at least once (a targeted press resolved to it, or — body worlds,
                     G3-04 — the ego made contact); the count travels
    NOT REACHED      never attempted and NOT present at the final node: it went away before its turn
    NEVER ATTEMPTED  never attempted and present at the final node — the sweep stopped early
    GROUND           a sealed GROUND member: disregarded as a target, printed, never masked
    UNREACHABLE      nav's verdict on a walked-out route (G3-04b) — NOT_MEASURED until it lands
Egos are listed under their role and count in no bucket (the self is not a target).
Computes nothing new: reads `roles.infer` and `captain.sweep_click.attempted`.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

from virelai_golden.captain.sweep_click import attempted
from virelai_golden.render.roster import class_field, collapse
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.weave.worldline import Worldline, region_at


def coverage_rows(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline], read) -> List[str]:
    done = attempted(record, window, worldlines)
    now = window[-1].node
    ego = {m for v in read.bodies for m in v.members}
    ground = {m for v in read.ground.verdicts for m in v.members} if read.ground else set()
    rows: List[str] = []
    tally: Dict[str, int] = {"TOUCHED": 0, "NOT REACHED": 0, "NEVER ATTEMPTED": 0, "GROUND": 0, "EGO": 0}
    for w in sorted(worldlines, key=lambda w: w.id):
        v = read.verdicts[w.id]
        role = v.band2 or "∅"
        present = region_at(w, now) is not None
        if w.id in ego:
            status = "EGO"
        elif w.id in ground:
            status = "GROUND"
        elif w.id in done:
            status = "TOUCHED"
        elif present:
            status = "NEVER ATTEMPTED"
        else:
            status = "NOT REACHED"
        tally[status] += 1
        cf = class_field(sorted({e.value for e in collapse(w.steps)}))
        extra = f" ×{done[w.id]}" if w.id in done else ""
        rows.append(f"  ###{w.id:03d} · {cf} · {status}{extra} · role {role} · "
                    f"{'present' if present else 'absent'} at node {now}")
    return [f"── COVERAGE · whole game (R-H) · nodes {window[0].node}–{now} · "
            f"TOUCHED {tally['TOUCHED']} · NOT REACHED {tally['NOT REACHED']} · NEVER ATTEMPTED {tally['NEVER ATTEMPTED']} · "
            f"GROUND-disregarded {tally['GROUND']} · EGO {tally['EGO']} · UNREACHABLE NOT_MEASURED (G3-04b) ──"] + rows


def render_coverage(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline], read) -> str:
    return "\n".join(coverage_rows(record, window, worldlines, read))
