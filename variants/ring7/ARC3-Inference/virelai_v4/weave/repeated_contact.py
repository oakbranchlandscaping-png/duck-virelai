"""WO-COMPOUND-ROLE-01 · repeated real contact as an independent LEVER confirmation.

FOUNDATIONAL_ARCHETYPES_v2 §3: a remote lever is STATIC (it never changes; its
effects land elsewhere) -- self-delta is irrelevant to lever-ness. STATIC (what
an object's own pixels do) and LEVER (what clicking it causes elsewhere) are true
answers to two different questions, not competing answers to one. This module
answers the second question from a source `infer_roles`'s own correlation branch
does not read: how many times, within this life, was this specific worldline the
resolved target of a real recorded action -- the canonical capture record `acted_on`
(weave/action_roster.py) already resolves against, not a correlation over deltas.

Deliberately separate from `weave/role_read.py`: this module imports nothing from
it, is imported by nothing in it, and changes no line of its existing correlation
logic. It reuses ONLY the lower-level, already-committed wiring-law resolver
`weave.action_roster.acted_on` -- the same primitive `weave/acted_on_render.py`'s
render already calls, so "which worldline was acted on" has one definition, not two.

THE THRESHOLD: reused, not invented. `weave/role_read.py:472` already gates its own
LEVER confidence on `len(wl_clicks) >= 2` -- the established evidentiary bar this
codebase already uses for "confidently, repeatedly, deliberately targeted." This
module's `REPEATED_CONTACT_THRESHOLD` is that same number, cited, not re-derived.

Pure, read-only, additive: writes no belief, decides nothing about which tag is
"correct" (RULING_OBSERVERS_INTEGRATOR_v1 -- the integrator's role verdict stays
the sole decider), lands nothing on `RoleVerdict`. Its caller renders this as a
second, independently-labelled fact alongside whatever `infer_roles` already said.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set, Tuple

from virelai_v4.weave.action_roster import acted_on, RESOLVED

# weave/role_read.py:472 -- `conf = FIRM if len(wl_clicks) >= 2 else PROVISIONAL`,
# infer_roles's own LEVER confidence gate. Reused verbatim, not a new number.
REPEATED_CONTACT_THRESHOLD = 2


def count_acted_on_by_worldline(
    window_cuts: Iterable[Any],
    worldlines: Iterable[Any],
    node_actions: List[Tuple[Any, Any]],
) -> Dict[int, int]:
    """How many times each worldline was the RESOLVED target of a real action,
    across ``window_cuts`` (one life's window, by convention -- this function
    takes whatever window it is given and does not itself apply any life
    boundary). Mirrors ``weave/acted_on_render.py::render_acted_on_block``'s own
    per-node resolution loop exactly (same ``cut_by_idx``, same absolute
    ``node_actions[t]`` indexing, same ``acted_on`` call) but returns a plain
    tally instead of a rendered block -- no game-specific knowledge, no
    footprint bookkeeping, nothing this function does not need.

    Only ``RESOLVED`` resolutions count. ``EMPTY`` (unowned click), ``NON_TARGETED``
    (directional/no-coordinate action) and ``OUT_OF_WINDOW`` never attribute to a
    worldline -- counting them would silently manufacture contact that was never
    resolved to an object, exactly the "snap to nearest" dishonesty
    ``weave/action_roster.py`` itself refuses to do."""
    cut_by_idx = {c.node_index: c for c in window_cuts}
    counts: Dict[int, int] = {}
    for t in cut_by_idx:
        aid, target = node_actions[t] if 0 <= t < len(node_actions) else (None, None)
        res = acted_on(t, aid, target, cut_by_idx, worldlines)
        if res.status == RESOLVED:
            counts[res.worldline_id] = counts.get(res.worldline_id, 0) + 1
    return counts


def confirmed_by_repeated_contact(
    window_cuts: Iterable[Any],
    worldlines: Iterable[Any],
    node_actions: List[Tuple[Any, Any]],
) -> Set[int]:
    """Worldline ids independently confirmed as LEVER by real, repeated contact
    within this window -- ``count_acted_on_by_worldline`` thresholded at
    ``REPEATED_CONTACT_THRESHOLD``. Does not read or write any ``RoleVerdict``;
    additive to whatever role(s) `infer_roles` separately assigns the same
    worldline."""
    counts = count_acted_on_by_worldline(window_cuts, worldlines, node_actions)
    return {wid for wid, n in counts.items() if n >= REPEATED_CONTACT_THRESHOLD}
