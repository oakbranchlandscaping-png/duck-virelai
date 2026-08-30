"""
virelai_v4/library/lever_dispatch.py — Lever dispatch routing.

WO-CAMPAIGN3-PHASE3-02 Sub-deliverable 1B (Lever Verdict Integration).
Filed: May 3, 2026.

Translates substrate-honest ``LeverMechanism`` verdicts into routing
decisions per the Hybrid option ratified at Step 0 audit Recommendation 1
(Director ratification, May 3, 2026).

V3.5 source: ``Universal_Solver_v3_5/crucible/machine_search.py:200-224``.
V3.5 routing is binary at the dispatch layer:
    - WorldMachine.machine_class == "DIRECTIONAL" → depth sequence bundle
    - else (FINITE_SEARCH or UNKNOWN) → Gray code combo bundle

V4 Hybrid routing (per Step 0 Recommendation 1 ratification):
    | LeverMechanism | DispatchRoute       | Inheritance |
    | TOGGLE         | GRAY_CODE           | PORT V3.5   |
    | CYCLE          | GRAY_CODE           | PORT V3.5   |
    | DIRECTIONAL    | DEPTH_SEQUENCE      | PORT V3.5   |
    | UNKNOWN        | GRAY_CODE           | PORT V3.5 (fallback) |
    | SATURATED      | SKIP_LEVER          | INVENT V4   |
    | None (unprobed)| NEEDS_CYCLE_PROBE   | INVENT V4 (per-call routing) |

INVENT justification for SATURATED → SKIP_LEVER:
V3.5 substrate at the dispatch site (``WorldMachine.machine_class`` string)
could not express per-lever SATURATED status; V3.5 routed all levers via
aggregated machine_class. V4's ``LibraryObject.lever_mechanism`` per-lever
field enables per-lever routing decisions. SATURATED → skip is a V4 design
refinement enabled by substrate honesty; cost ~10 NBLNC; benefit: doesn't
waste cycle probe budget or downstream execution time on levers that have
already saturated.

INVENT justification for None → NEEDS_CYCLE_PROBE:
V3.5 ran cycle probe at world-model build time during DISCOVERY phase;
all levers had a verdict before dispatch ran. V4's per-frame cybernetic
loop means dispatch may encounter unprobed levers; routing them to
"needs probe" is a V4 design pattern enabled by per-call routing.

Per binding methodology #13 (V4 Testability Idiom): class wrapper at top
with lazy imports; free function at bottom takes no inter-module
dependencies, testable in isolation.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from virelai_v4.contracts.lever_mechanism import LeverMechanism

if TYPE_CHECKING:
    from virelai_v4.library.semantic_library import LibraryObject


class DispatchRoute(str, Enum):
    """V4 dispatch routes per Hybrid option (WO-PHASE3-02 ratified May 3, 2026).

    Values:
        GRAY_CODE         — Route to combinatorial Gray code traversal.
                            Used for TOGGLE (period-2 cycles) + CYCLE (multi-step
                            cycles) + UNKNOWN (V3.5 routing fallback).
        DEPTH_SEQUENCE    — Route to depth sequence search.
                            Used for DIRECTIONAL (monotonic-only behavior).
        SKIP_LEVER        — Skip this lever; do not include in active levers.
                            Used for SATURATED (V4 design refinement; V3.5
                            substrate could not express per-lever SATURATED).
        NEEDS_CYCLE_PROBE — This lever has not yet been probed; queue it for
                            cycle probe before downstream dispatch.
                            Used for None mechanism (unprobed levers).
    """

    GRAY_CODE = "GRAY_CODE"
    DEPTH_SEQUENCE = "DEPTH_SEQUENCE"
    SKIP_LEVER = "SKIP_LEVER"
    NEEDS_CYCLE_PROBE = "NEEDS_CYCLE_PROBE"


# ===========================================================================
# Class wrapper — top of module; AST contract pin target per binding
# methodology #13 (V4 Testability Idiom).
# ===========================================================================


class LeverDispatch:
    """V4 lever dispatch — translates substrate-honest LeverMechanism verdicts
    into routing decisions per the Hybrid option (WO-PHASE3-02 ratified).

    Wired in WO-PHASE3-02 Sub-deliverable 1A (cycle probe invocation site at
    ``virelai.py::choose_action`` post-``_record_contact_reactivity``). This
    class produces the route; downstream wires the route to specific
    behavior (Gray code traversal; depth sequence search; cycle probe
    invocation; lever skip).
    """

    def route_lever(self, library_object: "LibraryObject") -> DispatchRoute:
        """Route a lever per its ``lever_mechanism`` field.

        See module docstring for the full Hybrid routing table and INVENT
        justifications for SATURATED and None handling.

        Parameters
        ----------
        library_object : LibraryObject
            A LibraryObject with role == LibraryRole.LEVER. The
            ``lever_mechanism`` field carries the cycle probe verdict
            (or None if unprobed).

        Returns
        -------
        DispatchRoute
            The routing decision; one of GRAY_CODE, DEPTH_SEQUENCE,
            SKIP_LEVER, NEEDS_CYCLE_PROBE.

        Raises
        ------
        ValueError
            If ``library_object.lever_mechanism`` carries an unknown value
            (defensive; shouldn't fire under normal substrate evolution).
        """
        # Lazy import per binding methodology #13 (V4 Testability Idiom).
        from virelai_v4.library.lever_dispatch import _route_lever_impl

        return _route_lever_impl(library_object)


# ===========================================================================
# Free functions — bottom of module; tested in isolation per binding
# methodology #13 (V4 Testability Idiom).
# ===========================================================================


def _route_lever_impl(library_object: "LibraryObject") -> DispatchRoute:
    """Per Hybrid routing (Step 0 Recommendation 1; Director ratified May 3, 2026).

    V3.5 source: ``crucible/machine_search.py:200-224``. V3.5 routing is
    binary; V4 splits into 4-way DispatchRoute per substrate-honest design.

    Routing table:
      - TOGGLE / CYCLE → GRAY_CODE  (PORT V3.5 routing)
      - DIRECTIONAL    → DEPTH_SEQUENCE  (PORT V3.5 routing)
      - UNKNOWN        → GRAY_CODE  (PORT V3.5 fallback per machine_search.py:209)
      - SATURATED      → SKIP_LEVER  (INVENT V4; see module docstring)
      - None           → NEEDS_CYCLE_PROBE  (INVENT V4; per-call routing)
    """
    mechanism = library_object.lever_mechanism

    # WO-E7 (type/condition de-collapse): saturation is a CONDITION on
    # obj.saturated, no longer written into the type field. This route is
    # observability-only (action_selector logs routes; nothing acts on them at
    # Phase 3), but it is re-pointed to read the condition so the dispatch
    # diagnostic stays honest post-de-collapse — a saturated lever still routes
    # SKIP_LEVER from obj.saturated regardless of its (now-real, or None) type.
    # Checked first so it wins over the type-field routes below.
    if getattr(library_object, "saturated", False):
        return DispatchRoute.SKIP_LEVER

    if mechanism is None:
        # V4 INVENT: unprobed levers route to probing. V3.5 ran cycle probe
        # at world-model build time, so this case did not arise in V3.5
        # dispatch.
        return DispatchRoute.NEEDS_CYCLE_PROBE

    if mechanism in (LeverMechanism.TOGGLE, LeverMechanism.CYCLE):
        # PORT V3.5: TOGGLE and CYCLE both route to Gray code (V3.5
        # FINITE_SEARCH path). V3.5 conflated CYCLE into "DIRECTIONAL" via
        # mechanic_class but routed via FINITE_SEARCH machine_class.
        return DispatchRoute.GRAY_CODE

    if mechanism == LeverMechanism.DIRECTIONAL:
        # PORT V3.5: DIRECTIONAL routes to depth sequence search per
        # machine_search.py:206-207.
        return DispatchRoute.DEPTH_SEQUENCE

    if mechanism == LeverMechanism.UNKNOWN:
        # PORT V3.5: UNKNOWN routes to Gray code (FINITE_SEARCH fallback)
        # per machine_search.py:209 ("FINITE_SEARCH (or UNKNOWN falling
        # through to Gray code)").
        return DispatchRoute.GRAY_CODE

    if mechanism == LeverMechanism.SATURATED:
        # V4 INVENT: see module docstring for justification.
        return DispatchRoute.SKIP_LEVER

    raise ValueError(
        f"Unknown LeverMechanism value: {mechanism!r}. "
        f"All LeverMechanism enum values must have explicit dispatch routes "
        f"per WO-PHASE3-02 Hybrid routing table."
    )


__all__ = [
    "DispatchRoute",
    "LeverDispatch",
]
