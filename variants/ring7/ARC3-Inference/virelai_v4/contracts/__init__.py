"""
contracts/ — V4 frozen artifact chain definitions.

All public types re-exported here. Downstream modules import from virelai_v4.contracts.

WO-HOUSEKEEPING-01-SOFT-RETIRE (Director ratification May 21, 2026):
17 contracts soft-retired to `contracts/_retired/` (preserved, not deleted).
The 14 zombie contracts (FLAG-MINE-02) plus the 3 WO-01.A PORT_AS_IS ports
(directives, motion_model, spatial_utils) had no production readers; their
test files moved to `tests/_retired/contracts/`. Reversal is a single
git mv per restoration; the retirement manifest at
`docs/inheritance/RETIRED_CONTRACTS_MANIFEST.md` records the full move set
and reversal instructions.

KEEP rationale for the two non-retired contracts in this surface:
  - action_reality_report.py: production reader via getattr at
    library/cycle_probe_invocation.py:184 + direct field access at
    library/cycle_probe.py:352, 443 (FM 1 Hidden Coupling).
  - nav_lever.py: production reader at
    library/contact_reactivity_integration.py:50 (active reader chain
    into virelai.py:596).
"""

from .action_reality_report import ActionRealityReport
from .nav_lever import NavLeverCandidate

# V4 new contracts
from .routing_directive import RoutingDirective

# library_types removed in WO-CLEAN-09-PHASE-1 (vestigial; canonical types
# live in virelai_v4.library.semantic_library — no consumer used the re-export).

# WO-01.A additions (PORT_AS_IS from V3.5; May 17, 2026) — soft-retired
# WO-HOUSEKEEPING-01-SOFT-RETIRE (May 21, 2026). Files preserved at
# contracts/_retired/ for reversibility; no production readers ever wired.

# WO-BLUEPRINT-04 additions (INVENT #4 — Segment/Slot factoring, May 19, 2026)
# Blueprint Section 2.4.3 / 2.4.4 / 2.4.5 specifications.
# Note on CausalVerdict name collision: V4 has an existing dataclass-form
# `CausalVerdict` in falsification/prediction_comparator.py (V3.5 5-outcome
# match-quality type). This Blueprint enum-form CausalVerdict is the
# 8-value causal-context taxonomy. Sub-Phase 5 rename target: rename the
# V3.5 dataclass to CausalMatchQuality. Until then, qualified imports.
from .shape_class import ShapeClass, ShapeSignature
from .segment import Segment
from .causal_verdict import CausalVerdict, PreconditionStatus
from .delta_summary import DeltaSummary
from .probe_event import ProbeEvent

# WO-BLUEPRINT-05 additions (INVENT #3 anchor — Completion predicate enum,
# May 19, 2026). Sibling enums: PrerequisitePredicate (Section 3.4.1) +
# AttributeType (Section 3.5.1).
from .prerequisite_predicate import PrerequisitePredicate
from .completion_predicate import CompletionPredicate
from .attribute_type import AttributeType

__all__ = [
    "ActionRealityReport",
    "NavLeverCandidate",
    # V4 new contracts
    "RoutingDirective",
    # WO-BLUEPRINT-04 additions (INVENT #4 + #2 family)
    "ShapeClass",
    "ShapeSignature",
    "Segment",
    "CausalVerdict",        # Blueprint Section 2.4.5 enum form
    "PreconditionStatus",
    "DeltaSummary",
    "ProbeEvent",
    # WO-BLUEPRINT-05 additions (INVENT #3 anchor)
    "PrerequisitePredicate",
    "CompletionPredicate",
    "AttributeType",
]
