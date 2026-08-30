"""V4 routing directive — targeting → strategy contract.

Updated WO-C3-03 (April 2026): schema aligned with targeting/router.py.
The authoritative definition lives in targeting/router.py; this file mirrors
it for any future caller that imports from contracts/ directly.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingDirective:
    """What the targeting layer tells the strategy layer to do.

    Produced by targeting.route() on every frame.
    Consumed by strategy/ (Campaign 4+) to select a GameAction.
    """
    tier:         int    # 1–6 from target priority chain; 0 when all GREEN
    mode:         str    # "PROBE_WORLD_TYPE" | "PROBE_LIFE_COUNTER" |
                         # "PROBE_REACTIVE" | "PROBE_LEVERS" |
                         # "PROBE_LEVER_TYPE" | "PROBE_CAUSAL" |
                         # "EXECUTE" | "IDLE"
    focus:        str    # Human-readable description of what to do next
    ready_to_act: bool   # True only when all tiers GREEN (EXECUTE mode)
