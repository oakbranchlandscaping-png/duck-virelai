"""virelai_v4/strategy/collide_sweep.py — NAV collide-with-everything coverage driver.

The NAV / embodied-ego analog of the CLICK sweep (``strategy/click_sweep.py``):
where CLICK clicks each eligible object once — the K=1 Coverage pass
(``captain._dispatch_first_touch_click``) — NAV must navigate the ego to COLLIDE
with each eligible object once. This module owns the *coverage policy*: which
object to collide with next, in what order, and when the sweep is complete — the
systematic object-by-object enumeration the reactive Tier-3 NAV navigation lacks
(``FOUNDATIONAL_LOOP_RECONCILIATION`` §3.2: "no systematic all-objects NAV
collision probe exists").

PORT-default. ``build_collide_list`` mirrors ``click_sweep.build_sweep_list``'s
eligibility (exclude EGO / COUNTER / BACKGROUND-tagged) and ranking
(``rank_unattributed_objects``, REACTIVE-boosted). ``select_collide_target``
mirrors ``select_click_sweep_probe``'s one-target-at-a-time advance and its
K-consecutive-inert termination floor.

SCOPE — RUNG 1 (this module): the coverage POLICY only. Pure — reads the library,
emits NO ``GameAction``, writes NO belief. The navigation primitive that drives
the ego to the selected target (BFS via ``nav_atlas`` / dominant-axis stepping via
``tier3_nav``), the collision-detection evidence, and the
``(NAV, FIRST_TOUCH_PROBE)`` dispatch re-point (today → ``TIER3_NAV``) are the
action-substrate rung (rung 2 — canary-before-closure binding), deliberately not
built here.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Set

# Consecutive inert collisions before the sweep gives up — mirrors CLICK's
# CLICK_SWEEP_K_CONSECUTIVE_INERTS = 8 (an object that changes nothing on
# collision, K times running, stops the coverage; the black-swan reopen is a
# later probe-strategy concern, not this coverage floor).
COLLIDE_SWEEP_K_CONSECUTIVE_INERTS: int = 8


def build_collide_list(library, arena_filter=None) -> List[int]:
    """Ordered ``region_id``s to collide with — the NAV coverage list.

    Mirrors ``click_sweep.build_sweep_list``: excludes EGO / COUNTER / BACKGROUND,
    keeps REACTIVE / STATIC / UNKNOWN, orders by ``rank_unattributed_objects``
    (highest priority first) with eligible-but-unranked objects appended in
    ``region_id`` order. Reads the library; writes nothing, emits nothing."""
    from virelai_v4.library.library_roles import LibraryRole
    from virelai_v4.library.priority_aggregation import rank_unattributed_objects

    eligible: Dict[int, object] = {}
    for rid, obj in library.objects.items():
        if getattr(obj, "role", None) in (LibraryRole.EGO, LibraryRole.COUNTER):
            continue
        if getattr(obj, "is_background", False):
            continue
        if arena_filter is not None and not arena_filter(rid, obj):
            continue
        eligible[rid] = obj
    if not eligible:
        return []

    ranked = [(rid, s) for rid, s in rank_unattributed_objects(library)
              if rid in eligible]
    ordered = [rid for rid, _ in ranked]
    ranked_set = {rid for rid, _ in ranked}
    ordered.extend(sorted(rid for rid in eligible if rid not in ranked_set))
    return ordered


def select_collide_target(
    collide_list: Sequence[int],
    collided: Set[int],
    consecutive_inert: int = 0,
    k_inert: int = COLLIDE_SWEEP_K_CONSECUTIVE_INERTS,
) -> Optional[int]:
    """The coverage driver: the next ``region_id`` to collide with, or ``None``
    when the sweep is complete. PURE — no library, no ``GameAction``, no belief.

    Returns ``None`` (done) iff the inert floor tripped
    (``consecutive_inert >= k_inert``) OR every list member is already in
    ``collided`` (exhaustion). Otherwise the FIRST list member not yet collided —
    systematic, in list order (the list's own priority)."""
    if consecutive_inert >= k_inert:
        return None
    for rid in collide_list:
        if rid not in collided:
            return rid
    return None


# ── RUNG 2 · the collide drive (env-gated, observable, PORTs the nav stepper) ──
#
# Priority (Director): seeing INTENT is what matters — like a click-with-everything
# run, this is gradeable on a live replay by watching the ego walk into each
# object. Navigation PORTs the committed dominant-axis stepper
# (tier3_nav._compute_navigation_action_for_target); collision is the Director's
# definition — the ego's cells occupy the target object's cell-site footprint.
# No belief write, no role evidence (that is rung 3 — the collide analog of
# lever_evidence); this rung is the observable drive only.

# Frames spent navigating toward one target before it is declared unreachable and
# the sweep moves on — keeps the intent legible (it visibly advances) rather than
# hanging on an object the reactive stepper cannot reach.
COLLIDE_MAX_FRAMES_PER_TARGET: int = 12


def target_centroid(cells) -> Tuple[float, float]:
    """The (row, col) centroid of a cell-set — where the nav stepper aims. Empty
    → (-1.0, -1.0)."""
    cs = list(cells)
    if not cs:
        return (-1.0, -1.0)
    return (sum(r for r, _ in cs) / len(cs), sum(c for _, c in cs) / len(cs))


def ego_current_cells(ego_body_cells, ego_centroid) -> "frozenset":
    """The ego's footprint translated from its spawn position to its CURRENT
    centroid — mirrors ego_mask's spawn→current translation. Empty inputs →
    empty set."""
    cs = list(ego_body_cells)
    if not cs or not ego_centroid:
        return frozenset()
    spawn_r = sum(r for r, _ in cs) / len(cs)
    spawn_c = sum(c for _, c in cs) / len(cs)
    dr = int(round(ego_centroid[0] - spawn_r))
    dc = int(round(ego_centroid[1] - spawn_c))
    return frozenset((r + dr, c + dc) for r, c in cs)


def collision_detected(ego_cells, target_cells) -> bool:
    """Director's definition: a collision is when the ego's cells OCCUPY the cell-
    site footprint of the targeted object — i.e. the two cell-sets overlap."""
    return bool(frozenset(ego_cells) & frozenset(target_cells))


def collide_sweep_action(library, available_actions, rng, context):
    """RUNG 2 driver — one collide step per frame, or None to fall through.

    Env-gated by the caller (``VIRELAI_COLLIDE_SWEEP``). Reads the confirmed ego
    (``library.header.ego_centroid`` / ``ego_body_cells``) and drives the
    systematic sweep: pick the next uncollided target (rung 1), and either mark it
    COLLIDED when the ego footprint occupies it, or step the ego toward it with the
    committed dominant-axis stepper. Loud per-frame logging makes the intent
    gradeable on the replay + the log. Returns a directional ``GameAction`` while
    sweeping, or ``None`` when the sweep is done / no ego / no directional — the
    caller then falls through to the committed nav path. Writes no belief."""
    from arcengine import GameAction
    from virelai_v4.strategy.tier3_nav import _compute_navigation_action_for_target

    header = library.header
    if not getattr(header, "ego_confirmed", False) or not getattr(header, "ego_centroid", ()):
        return None

    st = getattr(context, "collide_sweep_state", None)
    if not st:
        st = {"list": build_collide_list(library), "collided": set(),
              "target": None, "frames": 0}
        context.collide_sweep_state = st

    ego_centroid = tuple(header.ego_centroid)
    ego_pos = (int(round(ego_centroid[0])), int(round(ego_centroid[1])))
    ego_cells = ego_current_cells(getattr(header, "ego_body_cells", frozenset()), ego_centroid)

    target = select_collide_target(st["list"], st["collided"])
    if target is None:
        _log(context, "COLLIDE-SWEEP | sweep complete — all "
             f"{len(st['collided'])} eligible objects collided/skipped")
        return None

    obj = library.objects.get(target)
    if obj is None:
        st["collided"].add(target)          # target vanished — count it done
        return collide_sweep_action(library, available_actions, rng, context)

    if collision_detected(ego_cells, obj.cells):
        st["collided"].add(target)
        st["frames"] = 0
        _log(context, f"COLLIDE-SWEEP | COLLIDED ###{target:03d} "
             f"ego@{ego_pos} occupies footprint")
        return collide_sweep_action(library, available_actions, rng, context)

    st["frames"] += 1
    if st["frames"] > COLLIDE_MAX_FRAMES_PER_TARGET:
        st["collided"].add(target)          # unreachable — move on, keep intent legible
        st["frames"] = 0
        _log(context, f"COLLIDE-SWEEP | SKIPPED ###{target:03d} (unreached in "
             f"{COLLIDE_MAX_FRAMES_PER_TARGET} frames)")
        return collide_sweep_action(library, available_actions, rng, context)

    tc = target_centroid(obj.cells)
    stuck = getattr(context, "nav_stuck_count", 0)
    action_id = _compute_navigation_action_for_target(
        ego_pos, tc, list(available_actions), rng, stuck)
    if action_id == 0:
        return None                         # no directional — fall through
    _log(context, f"COLLIDE-SWEEP | target=###{target:03d} ego@{ego_pos} "
         f"→ toward {(round(tc[0]),round(tc[1]))} action={action_id} "
         f"(frame {st['frames']}/{COLLIDE_MAX_FRAMES_PER_TARGET})")
    return GameAction.from_id(action_id)


def _log(context, msg: str) -> None:
    """Loud, replay-gradeable trace — via the context logger if present, else print."""
    logf = getattr(context, "_log", None)
    if callable(logf):
        logf(msg)
    else:
        print(msg)
