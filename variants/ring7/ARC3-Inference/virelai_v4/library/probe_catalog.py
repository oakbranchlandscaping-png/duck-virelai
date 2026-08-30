"""virelai_v4/library/probe_catalog.py — Affordance Layer Entry B.

Per Library Blueprint Section 5.2.2 (Probe Catalog). Filed under
WO-LGTD-02 Phase 2 of the Library-Grounded Tool Dispatch Campaign.

Declares V4's static inventory of investigative operations. Each probe
is identified by name and carries:
  - required_actions: action IDs whose declaration is necessary
  - discovery_type:   the investigative purpose
  - operational_preconditions: library-state predicate names whose truth
                               gates probe availability beyond action
                               declaration

The catalog is immutable at runtime (frozen dataclasses, tuple container).
The Available Probes view (Section 5.2.3) reads this catalog and
computes which probes are currently runnable.

Discovery types per Section 5.2.2.1: seven members. STATE_REVERSAL
explicitly NOT declared (no V4 UNDO probe exists; Section 5.2.2.1 defers).

The catalog reflects V4 probes as of WO-LGTD-02 Phase 2 (May 28, 2026)
per WO-00 Scope B inventory. The six emission probes:
  - stride_probe          (library/stride_probe.py)
  - tier1_channel_probe   (strategy/action_selector.py::tier1_probe_tool)
  - click_probe           (strategy/tier4_click.py::emit_click_at_region
                           + the captain's FIRST_TOUCH_PROBE dispatch)
  - cycle_probe           (library/cycle_probe.py + captain Mode A)
  - contact_probe         (perception/contact_detector.py-driven NAV approach)
  - tier3_nav_probe       (strategy/tier3_nav.py)

Observer paths (probe_outcome_processor, lever_evidence_recorder,
contact_detector outcome recording) are NOT catalog entries — they record
outcomes but do not emit actions with investigative intent. The catalog
is an emission inventory.

Import sovereignty: stdlib + affordance_belief only. No imports from
SemanticLibrary or other library modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from virelai_v4.library.semantic_library import SemanticLibrary
    from virelai_v4.library.affordance_belief import OperationalBelief


# ---------------------------------------------------------------------------
# DiscoveryType — Section 5.2.2.1 enum (seven members; STATE_REVERSAL absent)
# ---------------------------------------------------------------------------

class DiscoveryType(Enum):
    """Investigative purpose served by a probe primitive.

    Per Section 5.2.2.1. Seven members. STATE_REVERSAL is not declared
    because V4 has no UNDO probe; adding it would require ACTION7
    infrastructure (substrate, dispatcher, outcome processor) that
    Phase 1 of this campaign does not build.
    """
    EGO_IDENTIFICATION = "EGO_IDENTIFICATION"
    LEVER_DISCOVERY = "LEVER_DISCOVERY"
    LEVER_TYPING = "LEVER_TYPING"
    CLASS_TRANSITION_DETECTION = "CLASS_TRANSITION_DETECTION"
    TRAVERSABILITY_MAPPING = "TRAVERSABILITY_MAPPING"
    CONTACT_REACTIVITY = "CONTACT_REACTIVITY"
    MODAL_INTERACTION = "MODAL_INTERACTION"


# ---------------------------------------------------------------------------
# ProbeDeclaration — frozen dataclass; one row per probe
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProbeDeclaration:
    """One row in the Probe Catalog.

    Immutable at runtime. The catalog is declared in code; the substrate
    and captain read it but do not write it.

    probe_name:                Stable identifier; unique across the catalog.
    required_actions:          Tuple of action IDs whose DECLARED status is
                               necessary for the probe to execute.
                               Empty tuple means "no specific action required"
                               — the precondition layer handles the
                               availability check (e.g. tier1_channel_probe
                               uses the `any_action_declared` precondition).
    discovery_type:            One DiscoveryType.
    operational_preconditions: Tuple of predicate names referencing
                               functions in probe_preconditions.py.
    """
    probe_name: str
    required_actions: Tuple[int, ...]
    discovery_type: DiscoveryType
    operational_preconditions: Tuple[str, ...]


# ---------------------------------------------------------------------------
# PROBE_CATALOG — the V4 emission probe inventory (WO-LGTD-02 Phase 2)
# ---------------------------------------------------------------------------
#
# Each entry maps to a specific emission site in the code:
#
#   stride_probe         → library/stride_probe.py:run_stride_probe_step
#   tier1_channel_probe  → strategy/action_selector.py:tier1_probe_tool
#   click_probe          → strategy/tier4_click.py:emit_click_at_region
#                          (captain DISPATCH_TABLE for
#                          ("CLICK", FIRST_TOUCH_PROBE))
#   cycle_probe          → library/cycle_probe.py + captain Mode A dispatch
#                          (("CLICK", CYCLE_PERIOD_DETECTION_PROBE))
#   contact_probe        → contact_detector + Tier-3-NAV approach gate
#   tier3_nav_probe      → strategy/tier3_nav.py:_select_tier3_nav_action
#
# Preconditions are stubbed in Phase 2 (probe_preconditions.py returns
# False from each); Phase 3 implements the real predicate logic and
# wires available_probes() on SemanticLibrary.

PROBE_CATALOG: Tuple[ProbeDeclaration, ...] = (
    ProbeDeclaration(
        probe_name="stride_probe",
        required_actions=(1, 2, 3, 4),
        discovery_type=DiscoveryType.EGO_IDENTIFICATION,
        operational_preconditions=("ego_candidate_exists",),
    ),
    ProbeDeclaration(
        probe_name="tier1_channel_probe",
        required_actions=(),
        discovery_type=DiscoveryType.EGO_IDENTIFICATION,
        operational_preconditions=("any_action_declared",),
    ),
    ProbeDeclaration(
        probe_name="click_probe",
        required_actions=(6,),
        discovery_type=DiscoveryType.LEVER_DISCOVERY,
        operational_preconditions=("unprobed_target_available",),
    ),
    ProbeDeclaration(
        probe_name="cycle_probe",
        required_actions=(6,),
        discovery_type=DiscoveryType.LEVER_TYPING,
        operational_preconditions=("lever_confirmed", "not_yet_saturated"),
    ),
    # WO-EFFECT-DISPATCH-FIX-2 (Option B, June 11 2026): the effect-
    # characterization band's affordance. Precondition is "lever_confirmed"
    # ALONE — it must hold in the POST-typing effect phase, so (unlike
    # cycle_probe) it deliberately omits "not_yet_saturated" (False once typed).
    # This replaces WO2's reuse of "click_probe", whose precondition
    # "unprobed_target_available" is False post-coverage and nulled the dispatch
    # (DIAG-DISPATCH-WO2). discovery_type reuses LEVER_TYPING (descriptive tag;
    # not functionally routed).
    ProbeDeclaration(
        probe_name="effect_probe",
        required_actions=(6,),
        discovery_type=DiscoveryType.LEVER_TYPING,
        operational_preconditions=("lever_confirmed",),
    ),
    ProbeDeclaration(
        probe_name="contact_probe",
        required_actions=(1, 2, 3, 4),
        discovery_type=DiscoveryType.CONTACT_REACTIVITY,
        operational_preconditions=("ego_candidate_exists",),
    ),
    ProbeDeclaration(
        probe_name="tier3_nav_probe",
        required_actions=(1, 2, 3, 4),
        discovery_type=DiscoveryType.TRAVERSABILITY_MAPPING,
        operational_preconditions=("ego_candidate_exists",),
    ),
)


# ---------------------------------------------------------------------------
# AvailableProbe — Affordance Layer Entry C (Phase 3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AvailableProbe:
    """One row in the Available Probes derived view (Section 5.2.3).

    Returned by SemanticLibrary.available_probes(). Represents a probe
    from PROBE_CATALOG whose required_actions are all DECLARED and whose
    operational_preconditions all hold against current library state.

    probe_name:        Echoes the PROBE_CATALOG entry's name.
    discovery_type:    Echoes the PROBE_CATALOG entry's discovery_type.
    target_list:       For target-typed probes (click_probe, cycle_probe),
                       a tuple of region_ids the probe could target. None
                       for untyped probes (stride_probe sweep,
                       tier1_channel_probe).
    operational_state: Aggregate OperationalBelief across the probe's
                       required actions, computed by
                       aggregate_operational_belief. None when the probe
                       has empty required_actions (e.g.
                       tier1_channel_probe).
    """
    probe_name: str
    discovery_type: DiscoveryType
    target_list: Optional[Tuple[int, ...]]
    operational_state: Optional["OperationalBelief"]


# ---------------------------------------------------------------------------
# Operational belief aggregation across a probe's required actions
# ---------------------------------------------------------------------------

def aggregate_operational_belief(
    states: List["OperationalBelief"],
) -> "OperationalBelief":
    """Aggregate per-action OperationalBelief into a probe-level state.

    Priority (most-effective wins):
      EFFECTIVE_UNCONDITIONAL > EFFECTIVE_CONDITIONAL > UNTESTED > INERT

    A probe with one EFFECTIVE_UNCONDITIONAL required action is overall
    EFFECTIVE_UNCONDITIONAL even if other required actions are UNTESTED:
    the probe can produce effects through the proven channel.

    A probe whose required actions are ALL INERT is itself INERT — the
    probe has no live channel to operate through.

    Empty input is a programmer error; callers must filter empty inputs
    before invoking. The function raises ValueError on empty input rather
    than returning a sentinel because there is no defensible default
    aggregation for an empty channel set.
    """
    from virelai_v4.library.affordance_belief import OperationalBelief

    if not states:
        raise ValueError(
            "aggregate_operational_belief requires non-empty states; "
            "callers must filter empty inputs"
        )
    if any(s == OperationalBelief.EFFECTIVE_UNCONDITIONAL for s in states):
        return OperationalBelief.EFFECTIVE_UNCONDITIONAL
    if any(s == OperationalBelief.EFFECTIVE_CONDITIONAL for s in states):
        return OperationalBelief.EFFECTIVE_CONDITIONAL
    if all(s == OperationalBelief.INERT for s in states):
        return OperationalBelief.INERT
    return OperationalBelief.UNTESTED


# ---------------------------------------------------------------------------
# Target list and operational state computation per probe
# ---------------------------------------------------------------------------

def compute_target_list(
    probe_decl: ProbeDeclaration,
    library: "SemanticLibrary",
) -> Optional[Tuple[int, ...]]:
    """Compute the target region_id list for a target-typed probe.

    Returns:
      Tuple of region_ids for target-typed probes (click_probe,
      cycle_probe).
      None for untyped / sweep probes (stride_probe,
      tier1_channel_probe, contact_probe, tier3_nav_probe — these
      operate on the world rather than on a specific region).

    Read-only.
    """
    from virelai_v4.library.library_roles import LibraryRole

    if probe_decl.probe_name == "click_probe":
        # Plausible click targets: any unprobed object whose role is not
        # EGO. STATIC is intentionally NOT excluded — it is a hypothesis
        # the Coverage pass TESTS via FIRST_TOUCH_PROBE (see
        # captain.py:271-276 and unprobed_target_available's docstring).
        # WO-LGTD-02-FIX-01 Phase 3: aligned with the precondition's
        # post-Fix-B semantic. Excluding STATIC here would produce an
        # AvailableProbe with target_list that diverges from the
        # precondition's truth — the captain reads the Form B walk's
        # region_id for dispatch but the target_list is the chamber-
        # facing readout; the two must agree.
        return tuple(
            sorted(
                rid for rid, obj in library.objects.items()
                if obj.probe_count == 0
                and obj.role != LibraryRole.EGO
            )
        )
    if probe_decl.probe_name == "cycle_probe":
        # Plausible cycle-probe targets: confirmed levers not yet typed
        from virelai_v4.contracts.lever_mechanism import LeverMechanism
        unknown_sentinel = getattr(LeverMechanism, "UNKNOWN", None)
        targets: List[int] = []
        for rid, obj in library.objects.items():
            if not obj.lever_locked:
                continue
            mechanism = obj.lever_mechanism
            if mechanism is None:
                targets.append(rid)
            elif unknown_sentinel is not None and mechanism == unknown_sentinel:
                targets.append(rid)
        return tuple(sorted(targets))
    # Untyped / sweep / channel probes: no target list
    return None


def compute_operational_state(
    probe_decl: ProbeDeclaration,
    library: "SemanticLibrary",
) -> Optional["OperationalBelief"]:
    """Compute the probe-level operational state across required_actions.

    Returns None for probes with empty required_actions
    (tier1_channel_probe), since there is no fixed channel set to
    aggregate over.
    """
    if not probe_decl.required_actions:
        return None
    states = [
        library.sdk_actions[aid].operational_belief
        for aid in probe_decl.required_actions
        if aid in library.sdk_actions
    ]
    if not states:
        return None
    return aggregate_operational_belief(states)


__all__ = [
    "DiscoveryType",
    "ProbeDeclaration",
    "PROBE_CATALOG",
    "AvailableProbe",
    "aggregate_operational_belief",
    "compute_target_list",
    "compute_operational_state",
]
