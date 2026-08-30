"""WO-PUSH-R2/R3′ · the Push fallback gate + witness.

Pure, stateless helpers for the Push. No action selection, no arcengine — the
frontier logic lives on ``StateTracker`` and the routing at the choose-action
seam.

R2 law — **fallback-not-override**: the Push fires only into Pull silence and
never after a win (``should_fire``).

R3′ take-over — the silence is the ``typed_gap`` / ``random_fallback`` arms of the
no-primitive/no-key branch (the frames where nothing principled chose), not the
retired ``random_fallback`` label alone. ``is_pull_silent`` names that set; the
seam binds ``should_fire``'s first argument through it. Plus the decline witness
(``PushStats`` / ``render_push_stats``) that distinguishes never-triggered from
triggered-and-declined — the S5a blind spot that cost R2 its FIX1.
"""

from __future__ import annotations

from dataclasses import dataclass


# The two arms of the no-primitive/no-key branch — the Pull-silent labels the
# Push may take over (census WO_PUSH_R3P_EMITTER_PRECEDENCE_CENSUS_RETURN_v1).
# Deliberate emitters (captain / tier1 / cycle_probe), the untagged
# captain_legacy_fallback, None, and unknown labels are NOT silence.
_SILENCE_LABELS = frozenset({"typed_gap", "random_fallback"})


def should_fire(pull_silent: bool, level_won: bool) -> bool:
    """True iff the Push may act this frame: the Pull was silent AND the level is
    not already won. Signature unchanged from R2 (the 22 stay binding)."""
    return bool(pull_silent) and not bool(level_won)


def can_issue_reset(
    last_push_emission_was_reset: bool,
    plan_active: bool,
    awaiting_landing: bool,
) -> bool:
    """The structural loop invariant (WO-PUSH-R3′): a RESET may be emitted only
    when the last Push emission was NOT a RESET, no plan is active, and we are not
    already awaiting a landing. This makes consecutive Push RESETs unreachable —
    the reset-loop is impossible by construction, not by discouragement."""
    return (
        not last_push_emission_was_reset
        and not plan_active
        and not awaiting_landing
    )


def is_believed_inert(role, operational_belief) -> bool:
    """WO-R4 · pure believed-inert predicate. An object is believed inert when its
    derived role is STATIC/INERT (`library_roles`: "INERT" → STATIC branch) or its
    operational belief is INERT (`affordance_belief.OperationalBelief.INERT`).
    Pure over stringable inputs — no library import (tracker/fallback
    library-independence); the seam supplies role/belief as data."""
    r = "" if role is None else str(getattr(role, "name", role)).upper()
    b = "" if operational_belief is None else str(
        getattr(operational_belief, "name", operational_belief)).upper()
    return r in {"STATIC", "INERT"} or b == "INERT"


def representative_cell(cells):
    """WO-R4 · the object's representative cell = lexicographic ``min`` of its
    cells (a determinism floor, ruling 4)."""
    return min(cells)


def candidates_from_roster(rows):
    """WO-R4 · turn a roster into Push click candidates. ``rows`` is an iterable of
    ``(token, cells, is_lever)``. GOSPEL (Director ruling, ratified G4 re-pin):
    **assertion-only** — a candidate is exactly an object the library asserts as a
    lever; unknowns and everything else are out. The Push's edge vocabulary is the
    asserted lever set; exhaustion-without-win is a falsification verdict, not a
    failure. Deterministic — token-sorted ``[(token, representative_cell(cells))]``."""
    out = [
        (token, representative_cell(cells))
        for token, cells, is_lever in rows
        if is_lever
    ]
    out.sort(key=lambda tc: tc[0])
    return out


def render_push_verdict(exhausted: bool, won: bool):
    """WO-R4 D4 · the terminal-readable exhaustion verdict — a recorded observation
    only (no belief write; the single-writer spine is untouched). Returns the line
    when the asserted-lever edge space is exhausted across all known states and the
    level is unwon; None otherwise."""
    if exhausted and not won:
        return "PUSH_VERDICT: EXHAUSTED_WITHOUT_WIN — asserted-lever walk complete"
    return None


def is_pull_silent(label) -> bool:
    """True iff ``label`` is one of the Pull-silent emitter arms
    (``typed_gap`` / ``random_fallback``). Default-false for every other label,
    incl. ``None``, deliberate emitters, ``captain_legacy_fallback``, and any
    unknown future emitter (not silence until ruled)."""
    return label in _SILENCE_LABELS


@dataclass
class PushStats:
    """Per-life Push activity witness. ``declines`` distinguishes a fired-then-
    declined frame (trigger True, no lawful action) from never-triggered."""
    fires: int = 0
    extensions: int = 0
    rehomes: int = 0
    declines: int = 0
    repeat_visit_violations: int = 0
    open_set_size: int = 0


def render_push_stats(stats: PushStats) -> str:
    """The terminal-readable ``PUSH_STATS |`` line — R2's format plus ``declines=``."""
    return (
        "PUSH_STATS | "
        f"fires={stats.fires} "
        f"extensions={stats.extensions} "
        f"rehomes={stats.rehomes} "
        f"declines={stats.declines} "
        f"repeat_visit_violations={stats.repeat_visit_violations} "
        f"open_set_size={stats.open_set_size}"
    )
