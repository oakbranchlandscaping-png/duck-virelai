"""
virelai_v4/targeting/router.py — Routing Directive Production.

Pure function: route(target_state) → RoutingDirective.
Zero side effects. Zero mutations. TargetState is the sole input.

The router translates the assessor's tier grading into a vocabulary that
Campaign 4's strategy layer can consume. It asks: "given what the library
currently knows, what should the solver be doing?"

The assessor grades. The router directs.

Import sovereignty: imports from contracts/, targeting/, and stdlib only.
Contracts is the lowest-level V4 package and a standard dependency.
No imports from library/, perception/, strategy/, or memory/.
"""

from __future__ import annotations

from virelai_v4.contracts.routing_directive import RoutingDirective
from virelai_v4.targeting.assessor import TargetState


# ---------------------------------------------------------------------------
# Mode map — tier number → probe mode string
# ---------------------------------------------------------------------------

_MODE_MAP: dict[int, str] = {
    1: "PROBE_WORLD_TYPE",
    2: "PROBE_LIFE_COUNTER",
    3: "PROBE_REACTIVE",
    4: "PROBE_LEVERS",
    5: "PROBE_LEVER_TYPE",
    6: "PROBE_CAUSAL",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def route(target_state: TargetState) -> RoutingDirective:
    """Translate a TargetState into a RoutingDirective.

    Pure function. Reads target_state. Returns a frozen RoutingDirective.
    The TargetState is the sole input — no library access, no side effects.

    If all tiers are GREEN, returns an EXECUTE directive.
    Otherwise maps the current_tier to the appropriate PROBE mode.
    """
    if target_state.ready_to_act:
        return RoutingDirective(
            tier=0,
            mode="EXECUTE",
            focus="All tiers GREEN — execute toward win condition",
            ready_to_act=True,
        )

    tier = target_state.current_tier

    # Defensive fallback: current_tier should always be 1–6 when not ready_to_act,
    # but guard against degenerate TargetState from tests or future callers.
    if tier < 1 or tier > 6:
        return RoutingDirective(
            tier=tier,
            mode="IDLE",
            focus=f"Tier {tier} out of range — no directive available",
            ready_to_act=False,
        )

    assessment = target_state.tiers[tier - 1]   # tiers is 0-indexed, tier numbers are 1-indexed
    mode  = _MODE_MAP[tier]
    focus = f"Tier {tier} — {assessment.name}: {assessment.gap}"

    return RoutingDirective(
        tier=tier,
        mode=mode,
        focus=focus,
        ready_to_act=False,
    )
