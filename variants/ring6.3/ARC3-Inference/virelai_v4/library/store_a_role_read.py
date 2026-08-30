"""WO-DISPLAY-SOURCE-01 · read the role label from the belief that already
accumulates, instead of re-deriving a snapshot from the one that doesn't.

`WO_GROUNDHOG_DAY_01_AUDIT_RETURN` confirmed two things about this codebase's
two places that hold role belief:

  1. `context.woven_role_verdicts` (`virelai.py::_land_weave_roles`) is
     plain-reassigned (`=`) every life from a deliberately life-windowed weave
     recompute. It holds nothing from any prior life, ever — confirmed both
     by code inspection (exactly one write site, no merge) and empirically
     (traced across a real 5-life recording: a fresh Python object every
     landing, evidence available growing every life, evidence actually used
     staying flat at one life's worth).
  2. Store-A's BBA log-odds axes (`static_log_score` / `reactive_log_score` /
     `ego_log_score` / `counter_log_score` / `lever_log_score`), written
     through `library.log_score_accumulator.accumulate_role_evidence`, DO
     accumulate correctly across lives — confirmed empirically on the same
     real recording: `###004`'s `lever_log_score` climbed
     `0.4055 -> 0.8109 -> 1.2164 -> 1.6219 -> 2.0273`, one clean additive step
     per life, with a COUNTER worldline's evidence correctly staying on its
     own separate axis.

This module reads #2. It is NOT a second accumulator: it calls
`accumulate_role_evidence`, `land_weave_roles`, and `_land_weave_roles` not at
all, and mutates nothing. The mapping from a rendered worldline id to the
Store-A `region_id` it should read is the already-proven, already-used
"Rosetta" (`weave.worldline_binding.bind_worldlines_to_slots` — the same
`(class_id, cells)` free-equality join `_land_weave_roles` and
`_render_lineage` already build `slot_fps` for) — no new identity mapping
invented for this.

Pure function, no `Virelai` / `arcengine` dependency — importable and testable
in any sandbox that has the library and weave packages, matching the
established pattern (`weave/repeated_contact.py`, `weave/action_roster.py`)
of keeping display/derivation logic free of the harness-dependent wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from virelai_v4.library.constants import CONFIRMATION_THRESHOLD
from virelai_v4.weave.role_read import FIRM, OUT_OF_INPUT, PROVISIONAL, RoleVerdict
from virelai_v4.weave.worldline_binding import bind_worldlines_to_slots

# The five BBA Layer One axes (`library/log_score_accumulator.py::_ROLE_TO_AXIS`,
# gate retired — never wired to a LibraryRole, per that module's own comment).
_AXES: tuple = ("ego", "lever", "reactive", "counter", "static")

# sigmoid(0.0) == 0.5 exactly -- the untouched neutral prior every log-score
# axis starts at. An axis that has never received evidence sits here; it must
# never win the argmax, or an unobserved slot would display an arbitrary,
# unearned role name at PROVISIONAL confidence instead of UNKNOWN.
_NEUTRAL_PRIOR: float = 0.5


def store_a_role_verdicts(
    worldlines: Iterable[Any],
    library: Any,
) -> Optional[Dict[int, RoleVerdict]]:
    """`{worldline_id: RoleVerdict}` read from Store-A's already-accumulated
    belief — the exact duck-typed shape (`.role` / `.confidence`)
    `diagnostics.integration_roster.render_integration_roster`'s
    `role_verdicts` parameter already expects, so the render module itself
    needs no change.

    For each worldline bound to a spawn slot (via `bind_worldlines_to_slots`),
    reads all five BBA axes off `library.objects[region_id]`, picks the axis
    with the highest `sigmoid_confidence`, and labels it FIRM (>=
    `CONFIRMATION_THRESHOLD`, the axis-agnostic BBA Layer One confirmation
    bar — `library/constants.py`, explicitly documented as "retained for
    predicates outside the lever category") or PROVISIONAL otherwise. A
    worldline with no axis above the neutral prior reports UNKNOWN /
    OUT_OF_INPUT rather than an arbitrary tied argmax. An unbound worldline
    (no matching spawn slot — a mid-run BIRTH) is honestly omitted, never
    force-matched, matching `bind_worldlines_to_slots`'s own discipline.

    `LEVER_LOCKED_THRESHOLD` (0.6) / `LEVER_TYPED_THRESHOLD` (0.95) were
    considered and rejected for this: both gate the LEVER-specific probe-
    progression pipeline (`SLOT_IS_LEVER_LOCKED` / `LEVER_TYPED`), a
    different mechanism from a generic per-axis display label, and applying
    a lever-only two-stage gate to all five axes would misuse it.

    Returns None when there's no library or no worldlines — the same
    byte-neutral fallback `render_integration_roster` already handles for a
    None `role_verdicts`."""
    wls = list(worldlines) if worldlines else []
    if library is None or not wls:
        return None

    objects = getattr(library, "objects", None) or {}
    slot_fps = {(o.class_id, o.cells): rid for rid, o in objects.items()}
    bindings = bind_worldlines_to_slots(wls, slot_fps).bindings

    verdicts: Dict[int, RoleVerdict] = {}
    for wid, rid in bindings.items():
        obj = objects.get(rid)
        if obj is None:
            continue
        best_axis, best_conf = None, _NEUTRAL_PRIOR
        for axis in _AXES:
            conf = obj.sigmoid_confidence(axis)
            if conf > best_conf:
                best_axis, best_conf = axis, conf
        if best_axis is None:
            verdicts[wid] = RoleVerdict(
                worldline_id=wid, role="UNKNOWN", confidence=OUT_OF_INPUT,
                basis="store_a_accumulated: no axis above the neutral prior")
            continue
        confidence = FIRM if best_conf >= CONFIRMATION_THRESHOLD else PROVISIONAL
        verdicts[wid] = RoleVerdict(
            worldline_id=wid, role=best_axis.upper(), confidence=confidence,
            basis=f"store_a_accumulated: sigmoid_confidence({best_axis})={best_conf:.4f}")
    return verdicts
