"""
virelai_v4/library/field_card.py — Natural language projection of the library.

The field card is a VIEW, not data. It reads the library. It does not modify it.
It produces a string. The string is not stored in the library.

Seven sections rendered in order:
    1. SITUATION — one-line summary
    2. OBJECTS — classified objects grouped by role
    3. UNKNOWNS — summary of unclassified objects by zone
    4. ACTIONS — SDK action status
    5. EXPLORATION — state space metrics
    6. CAUSAL MAP — known causal links
    7. GAPS — what the library still doesn't know

Import sovereignty: reads from library types (same package) only.
No imports from targeting/, strategy/, or memory/.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import (
    LibraryObject,
    SDKAction,
    SemanticLibrary,
)

if TYPE_CHECKING:
    from virelai_v4.library.plan import PlanBase


# ---------------------------------------------------------------------------
# Role display order
# ---------------------------------------------------------------------------

_ROLE_ORDER = [
    LibraryRole.EGO,
    LibraryRole.REACTIVE,
    LibraryRole.LEVER,
    LibraryRole.TARGET,
    LibraryRole.COUNTER,
    LibraryRole.SIGNAL,
    LibraryRole.STATIC,
]

_ACTION_NAMES = {
    0: "RESET",
    1: "ACTION1",
    2: "ACTION2",
    3: "ACTION3",
    4: "ACTION4",
    5: "ACTION5",
    6: "ACTION6",
    7: "ACTION7",
}


# ---------------------------------------------------------------------------
# Section 1: SITUATION
# ---------------------------------------------------------------------------

def _render_situation(
    lib: SemanticLibrary,
    levels_completed: Optional[int] = None,
    lives_used: Optional[int] = None,
) -> str:
    h = lib.header
    # WO-SP4-FIELD-CARD-LEVEL-DISPLAY: read level/life from per-frame engine
    # state when supplied; fall back to library header defaults otherwise.
    # levels_completed counts COMPLETED levels; current level = completed + 1.
    # lives_used counts lives already consumed; current life = used + 1.
    level = (levels_completed + 1) if levels_completed is not None else h.level
    life = (lives_used + 1) if lives_used is not None else h.life
    world_str = (
        f"{h.world_type} ({h.world_type_confidence:.2f})"
        if h.world_type_confidence > 0.0
        else h.world_type
    )
    # WO-04c: show ego object detail when confirmed (multi-class support)
    if h.ego_confirmed and h.ego_object_ids:
        region_str = "+".join(f"R{rid}" for rid in sorted(h.ego_object_ids))
        classes_str = "{" + ",".join(str(v) for v in sorted(h.ego_value_set)) + "}"
        ego_str = f"{h.ego_mode} ({region_str} cls{classes_str}, conf {h.ego_confidence:.2f})"
    elif h.ego_confidence > 0.0:
        ego_str = f"{h.ego_mode} ({h.ego_confidence:.2f})"
    else:
        ego_str = h.ego_mode
    return (
        f"Game: {h.game_id} | Life {life} | Level {level} | "
        f"Actions: {h.actions_taken} | World: {world_str} | Ego: {ego_str}"
    )


# ---------------------------------------------------------------------------
# Section 2: OBJECTS (classified, non-UNKNOWN)
# ---------------------------------------------------------------------------

def _render_attempted_flags(obj: LibraryObject, sdk_action_ids: List[int]) -> str:
    """WO-OCD-FLAGS-CLICK — render per-action attempt suffix.

    Iterates the available SDK action IDs (sorted ASC) and emits Y for
    actions present in obj.actions_attempted, _ for actions never tried.
    Returns the inline suffix `" | tried=[N:Y/_,...]"` or empty string when
    sdk_action_ids is empty (defensive — no available actions to display).
    """
    if not sdk_action_ids:
        return ""
    parts = [
        f"{aid}:{'Y' if obj.actions_attempted.get(aid) else '_'}"
        for aid in sdk_action_ids
    ]
    return " | tried=[" + ",".join(parts) + "]"


def _format_lever_effect(effect) -> str:
    """Render one LeverEffect entry (WO1 rigid + WO3 non-rigid).

    RIGID (vector set): "region X displaced (+a,+b), N obs".
    NON_RIGID (vector None): "region X reshaped +/-N cells, M obs".
    """
    if effect.vector is not None:
        vec = f"({effect.vector[0]:+.0f},{effect.vector[1]:+.0f})"
        return (f"region {effect.subject_region_id} displaced {vec}, "
                f"{effect.observation_count} obs")
    delta = effect.cell_count_delta if effect.cell_count_delta is not None else 0
    return (f"region {effect.subject_region_id} reshaped {delta:+d} cells, "
            f"{effect.observation_count} obs")


def _render_object_line(obj: LibraryObject, sdk_action_ids: List[int]) -> str:
    """Render one classified object as a single line.

    Appends [ai=N.NN] action-independence annotation when actions_observed >= 3.
    This annotation is the primary LC detection signal (WO-C5-01):
      near 1.0 → LC candidate; between → lever; near 0.0 → background.

    Appends a per-action attempt-flags suffix (WO-OCD-FLAGS-CLICK):
    " | tried=[6:Y,1:_,...]" — Y if the action ID has been deliberately
    attempted on this object, _ otherwise. Universal across all roles.
    """
    flag_suffix = _render_attempted_flags(obj, sdk_action_ids)
    # Action Independence annotation — suffix appended to the first line of each role.
    ai_ann = (
        f"  [ai={obj.action_independence_ratio:.2f}]"
        if obj.actions_observed >= 3
        else ""
    )

    base = (
        f"  Region {obj.region_id} (class {obj.class_id}, "
        f"{obj.cell_count} cells)"
    )

    if obj.role == LibraryRole.EGO:
        return f"{base} -- conf {obj.confidence:.2f}{ai_ann}{flag_suffix}"

    if obj.role == LibraryRole.REACTIVE:
        change_str = f"{obj.change_count} delta cells" if obj.change_count else "no deltas yet"
        active_ann = (
            f" | is_active=True | active_frames={obj.active_frame_count}"
            f" | first={obj.first_active_frame} | last={obj.last_active_frame}"
        )
        return f"{base} -- {change_str}, conf {obj.confidence:.2f}{active_ann}{ai_ann}{flag_suffix}"

    if obj.role == LibraryRole.LEVER:
        # WO-CAMPAIGN3-PHASE3-04 post-canary surgical update (May 5, 2026):
        # surface lever_mechanism (Phase 3 cycle probe verdict) in field card
        # so canary observers can see substrate behavior. The legacy
        # ``reaction_type`` field (Phase 2 free-form contact-reactivity tag)
        # remains on the dataclass + serializer for round-trip persistence;
        # the LEVER renderer prefers ``lever_mechanism`` (Phase 3 typed enum)
        # because it is the authoritative cycle probe verdict.
        mechanism = obj.lever_mechanism
        # WO-EFFECT-ROSTER-TRUTH: the LEVER headline reflects BOTH axes — the DIVE
        # typing verdict (lever_mechanism) AND the effect-band state — so a lever
        # that is typing-UNDETERMINED but effect-characterized no longer prints
        # "probe pending" on line one while its effects block sits directly below.
        # Effect-fill is computed from the SAME terminal criterion (the predicate
        # reads only the slot, so no library is needed here): agreement (dominant
        # observation_count >= threshold) vs exhaustion (total presses >= cap).
        from virelai_v4.library.predicate_evaluators import (
            _EFFECT_AGREEMENT_THRESHOLD,
            _EFFECT_PROBE_CAP,
        )
        _effs = obj.lever_effects or ()
        _dominant = max((e.observation_count for e in _effs), default=0)
        _total = sum(e.observation_count for e in _effs) + (obj.effect_null_presses or 0)
        _eff_characterized = _dominant >= _EFFECT_AGREEMENT_THRESHOLD
        _eff_exhausted = (not _eff_characterized) and _total >= _EFFECT_PROBE_CAP
        _eff_touched = bool(_effs) or (obj.effect_null_presses or 0) > 0

        if mechanism is None:
            if _eff_characterized:
                mech_str = "effect-characterized (typing: UNDETERMINED)"
            elif _eff_exhausted:
                mech_str = "EFFECT_UNDETERMINED (typing: UNDETERMINED)"
            elif _eff_touched:
                mech_str = f"effect probe in progress ({_total} obs)"
            else:
                mech_str = "uncharacterized (probe pending)"
        elif mechanism.name == "CYCLE":
            cycle_len = obj.cycle_length
            mech_str = (
                f"CYCLE (length: {cycle_len})" if cycle_len > 0 else "CYCLE"
            )
        elif mechanism.name == "DIRECTIONAL":
            label = obj.direction_label or "?"
            mech_str = f"DIRECTIONAL ({label})"
        elif mechanism.name == "UNKNOWN":
            mech_str = "UNKNOWN (probe complete; classification unachievable)"
        else:
            # TOGGLE, SATURATED, or any future enum value: display the name.
            mech_str = mechanism.name
        # For a TYPED lever, append the effect-axis state so a typed-and-effect-
        # filled lever shows both axes on the headline.
        if mechanism is not None and _eff_touched:
            _eff_tag = (
                "effect-characterized" if _eff_characterized
                else "EFFECT_UNDETERMINED" if _eff_exhausted
                else "effect in progress"
            )
            mech_str = f"{mech_str}; {_eff_tag}"
        line = f"{base} -- {mech_str}, conf {obj.confidence:.2f}{ai_ann}{flag_suffix}"
        # WO-EFFECT-STORE-RIGID (WO1): measured per-subject effects are the
        # authoritative "what does this lever do" surface, rendered FIRST. The
        # legacy region-set `causes` line is kept (Strangler Fig coexistence)
        # but explicitly marked [legacy]; retirement is Sub-Phase 5.
        if obj.lever_effects:
            line += "\n    effects:"
            for effect in obj.lever_effects:
                line += "\n      " + _format_lever_effect(effect)
        if obj.causes:
            line += f"\n    [legacy] causes: regions {list(obj.causes)}"
        return line

    if obj.role == LibraryRole.TARGET:
        line = f"{base} -- conf {obj.confidence:.2f}{ai_ann}{flag_suffix}"
        if obj.caused_by:
            line += f"\n    caused_by: regions {list(obj.caused_by)}"
        return line

    if obj.role == LibraryRole.COUNTER:
        budget = f"~{obj.lc_budget_est}" if obj.lc_budget_est >= 0 else "unknown"
        return (
            f"  Region {obj.region_id} (class {obj.class_id}, "
            f"{obj.cell_count} cells) -- "
            f"rate {obj.lc_rate:.1f}/action, budget {budget}{ai_ann}{flag_suffix}"
        )

    if obj.role == LibraryRole.SIGNAL:
        return f"{base} -- {obj.change_count} changes{ai_ann}{flag_suffix}"

    if obj.role == LibraryRole.STATIC:
        # WO-RM-02: STATIC objects annotated with observation frame count.
        static_ann = f" | is_active=False | observed={obj.actions_observed} frames"
        return f"  Region {obj.region_id} (class {obj.class_id}, {obj.cell_count} cells){static_ann}{ai_ann}{flag_suffix}"

    return f"{base}{ai_ann}{flag_suffix}"


def _render_objects(lib: SemanticLibrary) -> Optional[str]:
    """Render classified objects in canonical region_id order (WO-OCD-DISPLAY).

    No role-based grouping; row position == canonical order from
    library construction (WO-OCD-CANONICAL: cell count ASC, class value
    ASC, emission order final tiebreaker). Roles are still rendered
    inline as a property of each object via _render_object_line.
    """
    classified = [o for o in lib.objects.values() if o.role != LibraryRole.UNKNOWN]
    unknown_count = len(lib.objects) - len(classified)

    if not classified:
        return None

    lines = [f"=== OBJECTS ({len(classified)} classified, {unknown_count} unknown) ==="]
    # library.objects is already in canonical order (WO-OCD-CANONICAL); preserve
    # the dict insertion order — equivalently region_id ASC. Available SDK
    # action IDs (sorted ASC) determine the per-row attempt-flag slots
    # (WO-OCD-FLAGS-CLICK).
    sdk_action_ids = sorted(lib.sdk_actions.keys())
    for obj in classified:
        lines.append(_render_object_line(obj, sdk_action_ids))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 3: UNKNOWNS
# ---------------------------------------------------------------------------

def _render_unknowns(lib: SemanticLibrary) -> Optional[str]:
    """Render a flat aggregate summary of all UNKNOWN objects.
    No zone grouping — zone is not a classification input (WO-06a)."""
    unknowns = [o for o in lib.objects.values() if o.role == LibraryRole.UNKNOWN]
    if not unknowns:
        return None

    total_cells = sum(o.cell_count for o in unknowns)
    class_ids = sorted(set(o.class_id for o in unknowns))
    lines = [
        f"=== UNKNOWNS ({len(unknowns)} remaining) ===",
        f"  {len(unknowns)} objects ({total_cells} cells) -- classes: {class_ids}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 3b: BACKGROUND (WO-C5-05)
# ---------------------------------------------------------------------------

def _render_background(lib: SemanticLibrary) -> Optional[str]:
    """Render confirmed-ignore objects grouped in their own section.

    Only shows objects where is_background=True. Each line shows the ignore
    score and the channel abbreviation string so the reason is auditable.
    """
    bg = [o for o in lib.objects.values() if o.is_background]
    if not bg:
        return None

    lines = [f"=== BACKGROUND ({len(bg)} confirmed ignore) ==="]
    for obj in sorted(bg, key=lambda o: o.ignore_score, reverse=True):
        channel_str = f" [{obj.ignore_channels}]" if obj.ignore_channels else ""
        lines.append(
            f"  Region {obj.region_id} (class {obj.class_id}, "
            f"{obj.cell_count} cells) -- ignore {obj.ignore_score:.2f}{channel_str}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 4: ACTIONS
# ---------------------------------------------------------------------------

def _render_actions(lib: SemanticLibrary) -> Optional[str]:
    if not lib.sdk_actions:
        return None

    lines = ["=== ACTIONS ==="]
    for aid in sorted(lib.sdk_actions):
        sdk = lib.sdk_actions[aid]
        name = _ACTION_NAMES.get(aid, f"ACTION{aid}")
        if sdk.status == "LIVE":
            detail = f"LIVE (delta {sdk.delta_cells} cells)"
        elif sdk.status == "NOOP":
            detail = "NOOP"
        elif sdk.status == "DEAD":
            detail = "DEAD"
        else:
            detail = "UNTESTED"
        if sdk.notes:
            detail += f" {sdk.notes}"
        lines.append(f"  {name}: {detail}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 5: EXPLORATION
# ---------------------------------------------------------------------------

def _render_exploration(lib: SemanticLibrary) -> Optional[str]:
    exp = lib.exploration
    if exp.actions_monitored == 0 and exp.unique_states == 0:
        return None

    lines = [
        "=== EXPLORATION ===",
        f"  States: {exp.unique_states} unique / {exp.repeated_states} repeated "
        f"(efficiency: {exp.efficiency:.1%})",
    ]
    if exp.consecutive_repeated > 0:
        lines.append(f"  Consecutive repeated: {exp.consecutive_repeated}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 6: CAUSAL MAP
# ---------------------------------------------------------------------------

def _render_captain_target(lib: SemanticLibrary) -> Optional[str]:
    """WO-LGTD-AGG: render the captain_target derived read — the SAME read the
    Form B walk consumes (captain.compute_captain_target), so this line cannot
    diverge from actual dispatch. Lazy captain import (display-time only)."""
    try:
        from virelai_v4.captain import compute_captain_target
        target = compute_captain_target(lib)
    except Exception:
        return None
    if target is None:
        return "CAPTAIN TARGET: None (no library-grounded open question)"
    slot, attribute_type, region_id = target
    return (
        f"CAPTAIN TARGET: rid={region_id} ({slot.role.value}) -> "
        f"{attribute_type.name}"
    )


def _render_causal_map(lib: SemanticLibrary) -> Optional[str]:
    # WO-EFFECT-STORE-RIGID (WO1): gate on EITHER measured effects (new,
    # authoritative) OR legacy `causes` (Strangler Fig coexistence). Effects
    # render first per lever; the legacy region-set line is marked [legacy].
    levers = [o for o in lib.objects.values()
              if o.role == LibraryRole.LEVER and (o.lever_effects or o.causes)]
    if not levers:
        return None

    lines = ["=== CAUSAL MAP ==="]
    for lev in sorted(levers, key=lambda o: o.region_id):
        for effect in lev.lever_effects:
            if effect.vector is not None:
                vec_str = f"({effect.vector[0]:+.0f},{effect.vector[1]:+.0f})"
                lines.append(
                    f"  Region {lev.region_id} -> Region "
                    f"{effect.subject_region_id} displaced {vec_str} "
                    f"({effect.observation_count} obs)"
                )
            else:  # WO3 non-rigid
                delta = (effect.cell_count_delta
                         if effect.cell_count_delta is not None else 0)
                lines.append(
                    f"  Region {lev.region_id} -> Region "
                    f"{effect.subject_region_id} reshaped {delta:+d} cells "
                    f"({effect.observation_count} obs)"
                )
        if lev.causes:
            obs = lev.causal_observation_count
            agr = lev.causal_agreement
            lines.append(
                f"  [legacy] Region {lev.region_id} -> Regions "
                f"{list(lev.causes)} ({obs} observations, agreement {agr:.0%})"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 7: GAPS
# ---------------------------------------------------------------------------

def _render_gaps(lib: SemanticLibrary) -> str:
    gaps: List[str] = []
    h = lib.header

    if h.world_type == "UNKNOWN":
        gaps.append("World type: UNKNOWN")
    if h.ego_mode == "UNKNOWN":
        gaps.append("Ego: UNKNOWN")

    # Count all unclassified objects (zone is not a classification input — WO-06a)
    unknown_count = sum(1 for o in lib.objects.values() if o.role == LibraryRole.UNKNOWN)
    if unknown_count > 0:
        gaps.append(f"{unknown_count} objects unclassified")

    # Count untested SDK actions
    untested = sum(1 for s in lib.sdk_actions.values() if s.status == "UNTESTED")
    if untested > 0:
        gaps.append(f"{untested} SDK actions untested")

    if not gaps:
        return "=== GAPS ===\n  No gaps."

    lines = ["=== GAPS ==="]
    for g in gaps:
        lines.append(f"  - {g}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _render_plan_status(plan: "PlanBase") -> str:
    """Render a one-line PLAN STATUS section for an active plan.

    WO-CAMPAIGN2-02 — once-per-render summary of the active plan. NOT
    a per-action diagnostic (per-action visibility is what
    VIRELAI_QUIET=1 silences; the field card render is the
    once-per-life summary point).

    Format examples:
      "Active: NavPlan target=(32,18) cursor=3/7 stuck=0 hyp=lever_R12"
      "Active: CycleProbePlan lever=(15,30) cursor=2/4 sat=0 hyp=probe_L4"
      "Active: TraversalPlan combo=0b1010 cursor=5 skipped=2 hyp=enum_T7"

    Per WO-CAMPAIGN2-02 scope, only NavPlan is fully formatted; the
    other plan types receive a generic line until Campaign 3 wires
    their construction.
    """
    plan_type = type(plan).__name__
    cursor = plan.cursor
    hyp = plan.source_hypothesis_id

    # NavPlan-specific format
    if hasattr(plan, "actions") and hasattr(plan, "target"):
        n = len(plan.actions)
        target = plan.target
        stuck = getattr(plan, "stuck_counter", 0)
        return (
            f"Active: {plan_type} target={target} cursor={cursor}/{n} "
            f"stuck={stuck} hyp={hyp}"
        )

    # Generic format (CycleProbePlan / TraversalPlan, until Campaign 3)
    return f"Active: {plan_type} cursor={cursor} hyp={hyp}"


def render_field_card(
    library: SemanticLibrary,
    hud_mask: Optional[object] = None,
    lc_only_delta_count: int = 0,
    ego_mask: Optional[object] = None,
    current_plan: Optional["PlanBase"] = None,
    levels_completed: Optional[int] = None,
    lives_used: Optional[int] = None,
) -> str:
    """Render the library's current state as a natural language field card.

    Pure function. No side effects. Does not modify the library.
    Returns a multi-line string suitable for terminal display.

    hud_mask: numpy bool array or None (WO-C5-03). When provided, shows HUD mask
    status in the situation header (cell count and LC-only delta count).
    lc_only_delta_count: count of LC-only deltas observed so far (WO-C5-03).
    ego_mask: numpy bool array or None (WO-02). When provided, shows ego mask status.
    current_plan: PlanBase or None (WO-CAMPAIGN2-02). When provided and
        not None, an "=== PLAN STATUS ===" section renders showing the
        active plan's type, target/cursor/etc. summary line. When None,
        no PLAN STATUS section appears (consistent with the field card's
        existing behavior of omitting empty sections).
    levels_completed: int or None (WO-SP4-FIELD-CARD-LEVEL-DISPLAY). Pass
        ctx.levels_completed so the header shows the current level
        (levels_completed + 1). When None, falls back to library.header.level.
    lives_used: int or None (WO-SP4-FIELD-CARD-LEVEL-DISPLAY). Pass
        ctx.lives_used so the header shows the current life (lives_used + 1).
        When None, falls back to library.header.life.
    """
    sections: List[str] = []

    # 1. SITUATION (always present)
    sections.append(_render_situation(library, levels_completed=levels_completed,
                                      lives_used=lives_used))

    # HUD mask status line (WO-C5-03) — shown immediately after situation
    if hud_mask is not None:
        try:
            import numpy as _np
            masked_cells = int(_np.sum(hud_mask))
        except Exception:
            masked_cells = -1
        if masked_cells >= 0:
            sections.append(
                f"HUD mask: active ({masked_cells} cells masked, "
                f"{lc_only_delta_count} LC-only deltas)"
            )
        else:
            sections.append(
                f"HUD mask: active ({lc_only_delta_count} LC-only deltas)"
            )
    else:
        sections.append("HUD mask: not yet established")
    _ct_line = _render_captain_target(library)
    if _ct_line is not None:
        sections.append(_ct_line)

    # Ego mask status line (WO-02) — shown on same line if space allows, otherwise below
    ego_mask_str = ""
    if ego_mask is not None:
        try:
            import numpy as _np
            ego_cells = int(_np.sum(ego_mask))
        except Exception:
            ego_cells = -1
        if ego_cells >= 0:
            ego_mask_str = f"| Ego mask: active ({ego_cells} cells)"
        else:
            ego_mask_str = "| Ego mask: active"
    elif library.header.ego_mode == "EMBODIED":
        ego_mask_str = "| Ego mask: not yet computed"
    else:
        ego_mask_str = f"| Ego mask: inactive ({library.header.ego_mode} world)"

    if ego_mask_str:
        sections[-1] += "  " + ego_mask_str

    # PLAN STATUS section (WO-CAMPAIGN2-02) — only renders when a plan
    # is active. Once-per-render summary, not per-action diagnostic.
    if current_plan is not None:
        sections.append("")
        sections.append("=== PLAN STATUS ===")
        sections.append("  " + _render_plan_status(current_plan))

    sections.append("")  # blank separator

    # 2-7. Optional sections (omitted if empty)
    for renderer in (
        _render_objects,
        _render_unknowns,
        _render_background,
        _render_actions,
        _render_exploration,
        _render_causal_map,
    ):
        result = renderer(library)
        if result is not None:
            sections.append(result)
            sections.append("")

    # 7. GAPS (always present)
    sections.append(_render_gaps(library))

    return "\n".join(sections)
