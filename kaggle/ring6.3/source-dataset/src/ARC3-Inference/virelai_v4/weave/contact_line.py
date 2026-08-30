"""WO_CONTACT_LINE_01 · what the ego actually touched — a RENDER, not a belief.

One line per press, read off the same edge `collide_drive._arrival` reads, naming every
worldline that gave cells to a sealed ego and whether it was the one being pursued.

**IT WRITES NOTHING.** No belief, no verdict, no retirement, no budget reset, no target
change. Every function here returns a string or a tuple and touches no context field. The
fence is structural: this module imports nothing that can write and holds no assignment to
any `context` attribute — asserted by AST in `tests/weave/test_contact_line.py`.

WHY IT EXISTS
    The board reports a plan returned on most presses, pursuits running their full budget,
    and `ARRIVED 0`. Three explanations could not be separated offline, because
    `recordings/*.recording.jsonl` carry action id `0` on every press. This renders the
    one fact that separates them — *did the thing we were pursuing ever give us cells* —
    onto the note the NAV arm already emits, so the Director's live run answers it.

BOTH EGO COLUMNS, AND WHY
    `RULING_EGO_WORLDLINE_v1:30` §4: *"All downstream consumers must accept a set of ego
    worldlines. Any code or contract assuming one ego is stale as of this ruling."*
    `arrived` takes ONE id and is stale by that ruling. **This rung does not fix it.** It
    renders what the committed single-ego test says beside what the whole sealed set says,
    so the gap is visible on the board and counted rather than argued about.

INTENTIONAL vs INCIDENTAL
    A giver that IS the held target is `INTENTIONAL` — we pursued it and it gave. Any
    other giver is `INCIDENTAL` — we touched something we were not aiming at. Offline the
    second happened on 92 presses and the first on none; that measurement could not see
    actions, and this line is how the board checks it.

GAME-FREE. Worldlines render as `###NNN`; the only magnitudes are cell COUNTS of what
crossed, which are a property of the exchange and not a footprint size.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.weave.collide_drive import arrived, driving_worldline
from virelai_v4.weave.provenance import owner_edge
from virelai_v4.weave.role_read import EGO, verdict_egos

INTENTIONAL = "INTENTIONAL"   # the giver was the held target — we pursued it
INCIDENTAL = "INCIDENTAL"     # a giver we were not aiming at
NOTHING = "nothing gained"    # no worldline gave cells to any sealed ego


def gains(edge, egos) -> Tuple[Tuple[int, int], ...]:
    """`((giver_id, cells_given), …)` for every non-ego worldline that gave cells to a
    sealed ego across this edge, ascending by giver.

    An ego giving to an ego is not contact with the board and is excluded — the same
    direction rule `arrived` states: *the ego GAINING from the target is arrival; the ego
    giving to it is the target moving over the ego.*"""
    counts: Dict[int, int] = {}
    for (_cell, giver, receiver) in edge.exchanges:
        if giver in egos or receiver not in egos:
            continue
        counts[giver] = counts.get(giver, 0) + 1
    return tuple(sorted(counts.items()))


def render(edge, verdicts, held: Optional[int]) -> str:
    """The contact line for one press. Pure — reads, formats, returns.

    Renders BOTH readings: `any-ego` is whether the held target gave to any sealed ego,
    `committed` is `arrived(edge, driving_worldline(verdicts), held)` — the test as it
    stands. **A disagreement between them is the gap the ruling already named**, and it
    is printed as `DISAGREE` rather than reconciled here."""
    egos = verdict_egos(verdicts)
    ego = driving_worldline(verdicts)
    got = gains(edge, egos)
    who = "  ".join(
        f"###{g:03d}×{n}{'*' if held is not None and g == held else ''}" for g, n in got)
    stamp = (INTENTIONAL if held is not None and any(g == held for g, _n in got)
             else (INCIDENTAL if got else NOTHING))
    any_ego = held is not None and any(g == held for g, _n in got)
    # The OLD single-id question, asked through the NEW set function — the driving
    # ego alone. Not a re-implementation: one set of one member is exactly what
    # `arrived` used to test, so the AGREE/DISAGREE column keeps its meaning after
    # `WO-EGO-SET-01` widened the committed test.
    committed = (arrived(edge, (ego,), held)
                 if (ego is not None and held is not None) else False)
    agree = "AGREE" if any_ego == committed else "DISAGREE"
    return (f"contact · {stamp} · held {'###%03d' % held if held is not None else 'none'}"
            f" · egos {'/'.join('###%03d' % e for e in egos) or 'none'}"
            f" · driving {'###%03d' % ego if ego is not None else 'none'}"
            f" · gave-to-ego [{who or '—'}]"
            f" · any-ego {int(any_ego)} committed {int(committed)} {agree}")


def contact_note(cuts, worldlines, verdicts, held: Optional[int]) -> str:
    """The line, or an honest statement of why there is none.

    **THE EDGE IS READ HERE AND NOWHERE ELSE IN THIS MODULE.** `owner_edge` raises on a
    window it cannot bridge — the same condition `_arrival`'s committed `except` absorbs —
    and an edge that cannot be read renders as `unreadable`, never as *nothing gained*.
    Those are two different absences and collapsing them is the failure this campaign has
    corrected five times."""
    if len(cuts) < 2:
        return "contact · no edge yet — fewer than two cuts"
    try:
        edge = owner_edge(cuts[-2], cuts[-1], worldlines)
    except Exception:
        return "contact · edge unreadable — the window is not a disjoint partition"
    return render(edge, verdicts, held)
