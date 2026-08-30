"""WO-DECLARE-INTENT-01 · the solver says what it is going to do, then what it did.

**PARITY WITH THE CLICK BRANCH, AND THAT IS THE WHOLE ARTIFACT.** On a click world a run
is readable: here is the list of objects, here is the log of clicks, one per object, in
order. The NAV arm had aggregates and no account — *four pursuits ended out of forty-nine
queued, ninety-seven notes reading `none retired yet`*, and nothing said why.

Three blocks, joined to the note the arm already emits:

  BLOCK 1  THE EGO      — once, when the drive first has one: which worldlines are the
                          body, whether measured co-motion licensed them as ONE body, and
                          the action→bearing model bought before it moved.
  BLOCK 2  THE LIST     — once, at formation: every non-ego visual object in the order the
                          cursor will walk it, one line each. **No cap** — v3.5's silent
                          eight is the failure this refuses to repeat.
  BLOCK 3  THE PURSUIT  — streamed, one line at each retirement, never accumulated.

**A RENDER. IT DECIDES NOTHING AND WRITES NOTHING.** No attribute of any object is
assigned anywhere in this module — asserted by AST, the discipline `contact_line` set. It
reads the context; it never mutates it. Every value it prints was already computed by the
code that made the decision, and nothing here is a second derivation of any of them.

**WHY THERE IS NO PURSUIT COUNTER.** `#N` as a running total would be a field with a
lifetime, and `WO-OUT-OF-REACH-01` spent a rung on how a lifetime becomes a bug. The
ordinal printed is the CURSOR'S — how many sites it has offered in the current pass — a
number the drive already keeps for its own reasons. It resets when a pass completes, and
that reset is information rather than a defect: a new pass is a new walk of the list.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

from virelai_v4.weave.collide_drive import (ARRIVED, _boundaries, _map_str, bearing_map,
                                            driving_worldline)
from virelai_v4.weave.collide_plan import _co_moves, body_cells
from virelai_v4.weave.collide_tags import _region_at_last
from virelai_v4.weave.ego_read import action_bearings
from virelai_v4.weave.role_read import verdict_egos

_NONE = "none"


def before_step(context) -> Tuple[Any, int, bool]:
    """The three readings that must be taken BEFORE `drive_step`, and why each must.

    `_pass_over` clears the frame count and overwrites the outcome, so a pursuit's press
    total and the fact that a retirement happened at all are both unreadable afterwards.

    **WO-SEEK-THE-SMALLEST-01 · THE THIRD READING IS THE EMPTY SLOT, NOT THE CURSOR'S
    SIZE.** It was `len(collide_drive_offered)`, and *the set was empty before this press*
    was what made a new pass recognisable without a flag. That rung deletes the cursor —
    **there are no passes** — so the reading it stood on is gone with it. What replaces it
    is the fact the render actually wants and that was always there beside it: **the target
    slot was empty and the step filled it.** That is a pursuit FORMING, which is the moment
    *the intention, declared before the walk* belongs at, and it needs no field either.

    The block now recurs once per PURSUIT rather than once per pass. With the cursor gone a
    pass is not a thing, and a pursuit is; re-declaring the list each time the drive picks
    up a new one is the same guarantee against the unit that still exists.

    **A TUPLE HANDED BACK TO THE CALLER, NEVER A FIELD.** The caller holds it for the
    length of one press, which is exactly the lifetime the fact has."""
    return (context.collide_drive_outcome,
            int(context.collide_drive_frames),
            context.collide_drive_target is None)


def _ego_block(cuts, worldlines, verdicts, node_actions) -> str:
    """BLOCK 1 — the body, its licence, and the model it bought before it moved."""
    egos = verdict_egos(verdicts)
    ego = driving_worldline(verdicts)
    if ego is None:
        return "  ego            none typed yet"
    by_id = {w.id: w for w in worldlines}
    cells, excluded = body_cells(by_id, ego, egos)
    base = by_id.get(ego)
    members = [w for w in egos if w in by_id and w != ego
               and _co_moves(base, by_id[w])] if base is not None else []
    emap = action_bearings(worldlines, node_actions,
                           _boundaries(cuts, node_actions, worldlines, verdicts)).get(ego)
    strip = len(_region_at_last(base).cells) if base is not None else 0
    lines = [
        f"  ego            sealed {' '.join(f'###{w:03d}' for w in egos) or _NONE}"
        f" · steering by ###{ego:03d}",
        f"  body           {len(members) + 1} worldline(s) joined by MEASURED co-motion"
        f" · footprint {len(cells)} cell(s), {len(cells) / strip:.2f}x the elected tone"
        if strip else "  body           the elected tone alone",
        f"  excluded       {' '.join(f'###{w:03d}' for w in excluded) or _NONE}"
        "   (sealed EGO, but its displacement disagreed)",
        f"  model          {_map_str(emap) if emap else _NONE}"
        f" · {len(bearing_map(emap)) if emap else 0} action(s) with a measured bearing",
    ]
    return "\n".join(lines)


def _list_block(candidates: Sequence[Any]) -> str:
    """BLOCK 2 — the declared intention, in the order the cursor will walk it.

    **THE ORDER IS `visual_targets`' OWN AND IT IS RANKED.** `collide_drive.py:708` sorts
    on `_order_key` — *newly-appeared, then smallest footprint, then lowest class, then
    first appearance* — which is R-3's ruling and the Director's reason: *small rare
    things are usually important, so we start there.* `_next_target` adds no second rule;
    it walks this list front to back, skipping what the cursor has already offered.

    **TWO HONEST DIVERGENCES, DECLARED HERE RATHER THAN DISCOVERED LATER.** A site nothing
    currently holds is passed over for that frame without being recorded, and a later
    first appearance appends. So this is the INTENT and Block 3 is the walk; where they
    differ, the difference is the finding."""
    out = [f"  targets        {len(candidates)} visual object(s), "
           "ranked newly-appeared / smallest footprint / lowest class / first appearance",
           "                 #   site            class   cells"]
    for i, t in enumerate(candidates, 1):
        cls, cells = t.key
        out.append(f"                {i:>3}   {str(t.site):<14}  {cls:>4}   {len(cells):>5}")
    return "\n".join(out)


def pursuit_line(context, before: Tuple[Any, int, int]) -> Optional[str]:
    """BLOCK 3 — one line, and only when a retirement actually happened this press.

    **THE NINETY-SEVEN `none retired yet` FRAMES MUST NOT BECOME NINETY-SEVEN LINES.**
    A retirement is recognised by `collide_drive_outcome` differing from the value bound
    before the step — `_pass_over` is reached at most once per press, so the comparison is
    exact and needs nothing accumulated.

    **THE PRESS COUNT IS EXACT, AND THE TWO PATHS DIFFER BY ONE.** `_arrival` runs at
    `drive_step:1090`, BEFORE `collide_drive_frames += 1` at `:1153`; every other
    retirement runs at `:1163`, after it. So an `ARRIVED` pursuit's total is the count as
    it stood before this press, and any other outcome's is one more. Derived from the
    outcome the drive itself recorded — never re-counted."""
    was, frames, offered = before
    now = context.collide_drive_outcome
    if now is None or now is was:
        return None
    target, outcome = now
    spent = frames if outcome == ARRIVED else frames + 1
    return (f"  pursuit #{offered:<3} → ###{target:03d} · {spent} press"
            f"{'' if spent == 1 else 'es'} · {outcome}")


def intent_note(context, cuts, worldlines, verdicts, node_actions,
                candidates, before: Tuple[Any, int, int]) -> str:
    """The blocks due on THIS press, joined — or an empty string, which the caller drops.

    **FORMATION IS RECOGNISED WITHOUT A FLAG.** The opening blocks are due on the press
    where the cursor's offered set goes from empty to non-empty, which is the first target
    selection of a life. It recurs whenever the drive picks up a new pursuit and refills
    the slot — and printing the list again there is correct: a new pursuit is a new walk,
    and the list is re-derived every frame, so its order can genuinely have changed.

    A once-per-life guarantee independent of that would need a field, and this rung is
    forbidden one. **The recurrence is stated rather than suppressed.**"""
    parts = []
    _was, _frames, was_empty = before
    if was_empty and context.collide_drive_target is not None:
        parts.append("· THE EGO ·")
        parts.append(_ego_block(cuts, worldlines, verdicts, node_actions))
        parts.append("· THE LIST — the intention, declared before the walk ·")
        parts.append(_list_block(candidates))
    line = pursuit_line(context, before)
    if line is not None:
        parts.append(line)
    return "\n" + "\n".join(parts) if parts else ""


__all__ = ["before_step", "intent_note", "pursuit_line"]
