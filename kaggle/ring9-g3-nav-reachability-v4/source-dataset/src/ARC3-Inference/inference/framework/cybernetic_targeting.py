"""Dependency-aware target selection and durable products for cybernetic gates.

This module knows how to sequence bounded goals.  It deliberately knows
nothing about ARC action semantics or how any particular gate is answered.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping


class TargetContractError(ValueError):
    """A target definition or product violates the targeting contract."""


@dataclass(frozen=True)
class GoalContract:
    goal_id: str
    target_id: str
    question: str
    desired_knowledge: tuple[str, ...]
    prerequisites: tuple[str, ...]
    admissible_probe_kinds: tuple[str, ...]
    completion_predicate: str
    memory_product_type: str

    def goal_card(self, *, status: str) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "gate_id": self.target_id,
            "status": status,
            "question": self.question,
            "desired_knowledge": list(self.desired_knowledge),
            "prerequisites": list(self.prerequisites),
            "admissible_probe_kinds": list(self.admissible_probe_kinds),
            "completion_predicate": self.completion_predicate,
            "memory_product_type": self.memory_product_type,
        }


@dataclass(frozen=True)
class MemoryProduct:
    product_id: str
    product_type: str
    target_id: str
    revision: int
    payload: Mapping[str, Any]
    dependencies: tuple[str, ...] = ()
    status: str = "ACTIVE"


@dataclass(frozen=True)
class GateAssessment:
    """Read-only grade of one target; it never selects or executes a probe."""

    target_id: str
    revision: int
    disposition: str
    evidence_refs: tuple[str, ...] = ()
    unmet_requirements: tuple[str, ...] = ()
    explanation: str = ""

    @property
    def satisfied(self) -> bool:
        return self.disposition == "SATISFIED"


class TargetRegistry:
    """Ordered target definitions and their dependency graph."""

    def __init__(self) -> None:
        self._contracts: dict[str, GoalContract] = {}
        self._order: list[str] = []

    def register(self, contract: GoalContract) -> None:
        if not contract.target_id or not contract.goal_id:
            raise TargetContractError("Target and goal identifiers must be non-empty.")
        if contract.target_id in self._contracts:
            raise TargetContractError(f"Target {contract.target_id!r} is already registered.")
        missing = [item for item in contract.prerequisites if item not in self._contracts]
        if missing:
            raise TargetContractError(
                f"Target {contract.target_id!r} has unregistered prerequisites: {missing!r}."
            )
        self._contracts[contract.target_id] = contract
        self._order.append(contract.target_id)

    def get(self, target_id: str) -> GoalContract:
        try:
            return self._contracts[target_id]
        except KeyError as exc:
            raise TargetContractError(f"Unknown target {target_id!r}.") from exc

    def ordered(self) -> tuple[GoalContract, ...]:
        return tuple(self._contracts[target_id] for target_id in self._order)

    def descendants(self, target_id: str) -> tuple[str, ...]:
        self.get(target_id)
        found: list[str] = []
        frontier = [target_id]
        while frontier:
            parent = frontier.pop(0)
            for contract in self.ordered():
                if contract.target_id not in found and parent in contract.prerequisites:
                    found.append(contract.target_id)
                    frontier.append(contract.target_id)
        return tuple(found)


class TargetJournal:
    """Versioned products; invalidated products remain auditable as stale history."""

    def __init__(self, registry: TargetRegistry) -> None:
        self.registry = registry
        self._active: dict[str, MemoryProduct] = {}
        self.history: list[MemoryProduct] = []

    def active_product(self, target_id: str) -> MemoryProduct | None:
        product = self._active.get(target_id)
        return product if product is not None and product.status == "ACTIVE" else None

    def put(self, product: MemoryProduct) -> MemoryProduct:
        contract = self.registry.get(product.target_id)
        if product.product_type != contract.memory_product_type:
            raise TargetContractError(
                f"Target {product.target_id!r} requires product type "
                f"{contract.memory_product_type!r}, received {product.product_type!r}."
            )
        if tuple(product.dependencies) != tuple(contract.prerequisites):
            raise TargetContractError(
                f"Product dependencies for {product.target_id!r} must be "
                f"{contract.prerequisites!r}."
            )
        missing = [item for item in product.dependencies if self.active_product(item) is None]
        if missing:
            raise TargetContractError(
                f"Product {product.product_id!r} has inactive prerequisites: {missing!r}."
            )
        previous = self.active_product(product.target_id)
        if previous is not None:
            self.invalidate(product.target_id, include_self=True)
        active = replace(product, status="ACTIVE")
        self._active[product.target_id] = active
        self.history.append(active)
        return active

    def invalidate(self, target_id: str, *, include_self: bool) -> tuple[str, ...]:
        prefix = (target_id,) if include_self else ()
        affected = (*prefix, *self.registry.descendants(target_id))
        invalidated: list[str] = []
        for item in affected:
            product = self._active.pop(item, None)
            if product is None:
                continue
            stale = replace(product, status="STALE")
            self.history.append(stale)
            invalidated.append(item)
        return tuple(invalidated)

    def snapshot(self) -> dict[str, Any]:
        return {
            "active_products": {
                target_id: asdict(product) for target_id, product in self._active.items()
            },
            "history": [asdict(product) for product in self.history],
        }


class TargetRouter:
    """Select the first unresolved target whose prerequisites are active."""

    def __init__(self, registry: TargetRegistry, journal: TargetJournal) -> None:
        self.registry = registry
        self.journal = journal

    def current(self) -> GoalContract | None:
        for contract in self.registry.ordered():
            if self.journal.active_product(contract.target_id) is not None:
                continue
            if all(self.journal.active_product(item) is not None for item in contract.prerequisites):
                return contract
        return None

    def current_or_last(self) -> GoalContract:
        current = self.current()
        if current is not None:
            return current
        ordered = self.registry.ordered()
        if not ordered:
            raise TargetContractError("No targets are registered.")
        return ordered[-1]
