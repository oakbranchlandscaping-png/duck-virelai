"""
virelai_v4/targeting/dispatch_registry.py — Registry-in-Router dispatch table.

WO-FM11-FIX (Stage 2). This module is the relocated world-discrimination locus
(Structural Law 5 / FM-11): the captain and the selector must not branch on
`world_type`; the Router/Registry is the sole world-discrimination authority.

Shape: a table keyed `(world_type, AttributeType)`; each cell is either a real
dispatch primitive (`PrimitiveId`) or an explicit `TypedGap` sentinel naming
WO-PRIMITIVES. The table is **exhaustive** over the live enum product
(`DISPATCH_WORLD_TYPES × DISPATCHABLE_ATTRIBUTE_TYPES`), validated at import
(`_validate_exhaustive`) — not only in tests.

SR boundary (WO-FM11-FIX F-1f, verdict NO): the `tier → AttributeType`
translation lives here (the Router already owns `tier → mode` in `router.py`),
so the legacy tier-keyed selector can dispatch via this Registry **without
touching the captain walk**. This is a coarse tier→representative-attribute_type
mapping sufficient for primitive selection; per-slot key production remains the
captain Form B walk's (FOUNDATION-MIGRATION).

Behavior preservation: the legacy selector dispatched exactly two world-keyed
cells — `(CLICK, tier 4) → tier4_click` (`action_selector.py:423`) and
`(NAV, tier 3) → tier3_nav` (`:448`). This Registry maps those two cells to
`PrimitiveId.TIER4_CLICK` / `PrimitiveId.TIER3_NAV`; the selector consumes only
those two verdicts and falls through for everything else — so captain-owned
cells (e.g. `(CLICK, FIRST_TOUCH_PROBE)`) and unbuilt cells (typed gaps) do not
change the selector's behavior.

Pure module: stdlib + contracts only. No arcengine, no library mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Tuple, Union, TYPE_CHECKING

from virelai_v4.contracts.attribute_type import AttributeType

if TYPE_CHECKING:
    from virelai_v4.contracts.routing_directive import RoutingDirective
    from virelai_v4.library.semantic_library import SemanticLibrary


# ---------------------------------------------------------------------------
# The dispatch world-type space and the dispatchable attribute set.
# ---------------------------------------------------------------------------

# Live world types the dispatch covers. GLOBAL/HYBRID appear in docstrings but
# are not produced by the live world_type classifier path (WO-FM11-FIX F-1d).
DISPATCH_WORLD_TYPES: Tuple[str, ...] = ("CLICK", "NAV")

# Every AttributeType except the OUT_OF_TAPE sentinel is a dispatch cell.
DISPATCHABLE_ATTRIBUTE_TYPES: Tuple[AttributeType, ...] = tuple(
    a for a in AttributeType if a is not AttributeType.OUT_OF_TAPE
)


# ---------------------------------------------------------------------------
# Primitive identities + the typed-gap sentinel.
# ---------------------------------------------------------------------------

class PrimitiveId(Enum):
    """Identity of an existing dispatch primitive. The selector executes the
    primitive named by the Registry verdict — world-agnostically (the Registry
    already did the world-discrimination)."""
    TIER4_CLICK = auto()        # legacy (CLICK, tier 4) — _select_tier4_click_action
    TIER3_NAV = auto()          # legacy (NAV, tier 3) — _select_tier3_nav_action (+stride/NavPlan)
    FIRST_TOUCH_CLICK = auto()  # captain-owned (CLICK, FIRST_TOUCH_PROBE) — Form B walk
    CYCLE_PROBE_CLICK = auto()  # captain-owned (CLICK, CYCLE_PERIOD_DETECTION_PROBE)
    TIER1_CHANNEL = auto()      # world-agnostic channel exhaustion (foundation world-type probe)


@dataclass(frozen=True)
class TypedGap:
    """An explicit 'no primitive built for this cell' sentinel — never
    random_probe, never a crash. Carries the cell coordinates and a reason
    naming the owning WO."""
    world_type: str
    attribute_type: AttributeType
    reason: str


RegistryEntry = Union[PrimitiveId, TypedGap]


# ---------------------------------------------------------------------------
# tier -> representative AttributeType (Router-side translation; F-1f).
# ---------------------------------------------------------------------------

# Mirrors router.py::_MODE_MAP (tier -> mode), extended to attribute_type.
# Distinct from the captain-claimed CLICK cells (FIRST_TOUCH / CYCLE) so the
# legacy cells do not collide with Path-1 ownership (WO-FM11-FIX behavior
# preservation).
_TIER_TO_ATTRIBUTE_TYPE: Dict[int, AttributeType] = {
    1: AttributeType.WORLD_TYPE_PROBE,            # PROBE_WORLD_TYPE
    2: AttributeType.COUNTER_IDENTIFICATION_PROBE,  # PROBE_LIFE_COUNTER
    3: AttributeType.FIRST_TOUCH_PROBE,           # PROBE_REACTIVE — the NAV (3) cell
    4: AttributeType.LEVER_CONFIRMATION_PROBE,    # PROBE_LEVERS — the CLICK (4) cell
    5: AttributeType.CYCLE_PERIOD_DETECTION_PROBE,  # PROBE_LEVER_TYPE
    6: AttributeType.LEVER_MECHANISM_DISCRIMINATION_PROBE,  # PROBE_CAUSAL (placeholder)
}


def tier_to_attribute_type(tier: int) -> AttributeType:
    """Translate a Router tier (1..6) into its representative AttributeType.
    Out-of-range tiers map to WORLD_TYPE_PROBE (foundation) defensively."""
    return _TIER_TO_ATTRIBUTE_TYPE.get(tier, AttributeType.WORLD_TYPE_PROBE)


# ---------------------------------------------------------------------------
# The Registry table — built exhaustively, then overlaid with real primitives.
# ---------------------------------------------------------------------------

def _gap(world_type: str, attribute_type: AttributeType) -> TypedGap:
    return TypedGap(
        world_type=world_type,
        attribute_type=attribute_type,
        reason=(
            f"No dispatch primitive built for ({world_type}, "
            f"{attribute_type.name}); owned by WO-PRIMITIVES."
        ),
    )


def _build_registry() -> Dict[Tuple[str, AttributeType], RegistryEntry]:
    # Start with every cell an explicit typed gap (exhaustive by construction).
    table: Dict[Tuple[str, AttributeType], RegistryEntry] = {
        (wt, at): _gap(wt, at)
        for wt in DISPATCH_WORLD_TYPES
        for at in DISPATCHABLE_ATTRIBUTE_TYPES
    }
    # Overlay the cells that have real primitives today.
    # Legacy world-keyed selector cells (the two relocated branches):
    table[("CLICK", AttributeType.LEVER_CONFIRMATION_PROBE)] = PrimitiveId.TIER4_CLICK
    table[("NAV", AttributeType.FIRST_TOUCH_PROBE)] = PrimitiveId.TIER3_NAV
    # Captain Form B walk cells (Path 1 — dispatched by the captain, not the
    # selector; recorded here so the Registry is the complete world-discrimination map):
    table[("CLICK", AttributeType.FIRST_TOUCH_PROBE)] = PrimitiveId.FIRST_TOUCH_CLICK
    table[("CLICK", AttributeType.CYCLE_PERIOD_DETECTION_PROBE)] = PrimitiveId.CYCLE_PROBE_CLICK
    # World-agnostic foundation channel exhaustion (tier-1 world-type probe):
    table[("CLICK", AttributeType.WORLD_TYPE_PROBE)] = PrimitiveId.TIER1_CHANNEL
    table[("NAV", AttributeType.WORLD_TYPE_PROBE)] = PrimitiveId.TIER1_CHANNEL
    return table


def _validate_exhaustive(table: Dict[Tuple[str, AttributeType], RegistryEntry]) -> None:
    """Construction-time guard: the table covers exactly the product, and every
    entry is a PrimitiveId or a TypedGap. Raises on drift — the invariant is
    enforced at import, not only in tests."""
    expected = {
        (wt, at)
        for wt in DISPATCH_WORLD_TYPES
        for at in DISPATCHABLE_ATTRIBUTE_TYPES
    }
    keys = set(table.keys())
    if keys != expected:
        raise ValueError(
            "dispatch_registry not exhaustive over world_type x attribute_type: "
            f"missing={expected - keys}, extra={keys - expected}"
        )
    for key, entry in table.items():
        if not isinstance(entry, (PrimitiveId, TypedGap)):
            raise TypeError(f"registry cell {key} is not a primitive or typed gap: {entry!r}")


REGISTRY: Dict[Tuple[str, AttributeType], RegistryEntry] = _build_registry()
_validate_exhaustive(REGISTRY)


# ---------------------------------------------------------------------------
# The facade — the selector's sole dispatch question.
# ---------------------------------------------------------------------------

def resolve_dispatch_primitive(
    directive: Optional["RoutingDirective"],
    library: Optional["SemanticLibrary"],
) -> Optional[RegistryEntry]:
    """Given the Router directive (tier) and the library (world_type), return
    the Registry verdict for this frame — a PrimitiveId or a TypedGap.

    Returns None only when there is no directive or no library (the selector
    then keeps its existing non-dispatch fallback). This function is the **only**
    place world_type is read for dispatch — the selector no longer branches on it.
    """
    if directive is None or library is None:
        return None
    world_type = library.header.world_type
    attribute_type = tier_to_attribute_type(directive.tier)
    return REGISTRY.get((world_type, attribute_type))


__all__ = [
    "DISPATCH_WORLD_TYPES",
    "DISPATCHABLE_ATTRIBUTE_TYPES",
    "PrimitiveId",
    "TypedGap",
    "REGISTRY",
    "tier_to_attribute_type",
    "resolve_dispatch_primitive",
]
