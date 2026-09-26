from __future__ import annotations

import pytest

from inference.framework.cybernetic_targeting import (
    GateAssessment,
    GoalContract,
    MemoryProduct,
    TargetContractError,
    TargetJournal,
    TargetRegistry,
    TargetRouter,
)


def test_gate_assessment_is_read_only_and_satisfaction_is_explicit():
    open_grade = GateAssessment(
        target_id="G1",
        revision=1,
        disposition="ANSWER_REQUIRED",
        unmet_requirements=("explanation",),
    )
    closed_grade = GateAssessment(target_id="G1", revision=2, disposition="SATISFIED")
    assert not open_grade.satisfied
    assert closed_grade.satisfied


def _contract(target_id: str, prerequisites: tuple[str, ...] = ()) -> GoalContract:
    return GoalContract(
        goal_id=f"{target_id}-goal",
        target_id=target_id,
        question=f"Resolve {target_id}",
        desired_knowledge=("bounded answer",),
        prerequisites=prerequisites,
        admissible_probe_kinds=("controlled probe",),
        completion_predicate="Evidence-bound answer",
        memory_product_type=f"{target_id}-product",
    )


def _product(target_id: str, revision: int, prerequisites: tuple[str, ...] = ()) -> MemoryProduct:
    return MemoryProduct(
        product_id=f"{target_id}-P{revision}",
        product_type=f"{target_id}-product",
        target_id=target_id,
        revision=revision,
        payload={"revision": revision},
        dependencies=prerequisites,
    )


def test_router_selects_lowest_unresolved_ready_target():
    registry = TargetRegistry()
    registry.register(_contract("G0"))
    registry.register(_contract("G1", ("G0",)))
    journal = TargetJournal(registry)
    router = TargetRouter(registry, journal)

    assert router.current().target_id == "G0"
    journal.put(_product("G0", 1))
    assert router.current().target_id == "G1"
    journal.put(_product("G1", 1, ("G0",)))
    assert router.current() is None


def test_invalidating_parent_marks_descendant_products_stale_and_relocks_parent():
    registry = TargetRegistry()
    registry.register(_contract("G0"))
    registry.register(_contract("G1", ("G0",)))
    journal = TargetJournal(registry)
    router = TargetRouter(registry, journal)
    journal.put(_product("G0", 1))
    journal.put(_product("G1", 1, ("G0",)))

    assert journal.invalidate("G0", include_self=True) == ("G0", "G1")
    assert router.current().target_id == "G0"
    assert journal.active_product("G1") is None
    assert [item.status for item in journal.history[-2:]] == ["STALE", "STALE"]


def test_new_child_target_requires_registration_only_and_router_discovers_it():
    registry = TargetRegistry()
    registry.register(_contract("G0"))
    registry.register(_contract("G1", ("G0",)))
    registry.register(_contract("G2", ("G1",)))
    journal = TargetJournal(registry)
    router = TargetRouter(registry, journal)
    journal.put(_product("G0", 1))
    journal.put(_product("G1", 1, ("G0",)))

    assert router.current().target_id == "G2"


def test_registry_rejects_missing_prerequisite_and_product_type_mismatch():
    registry = TargetRegistry()
    with pytest.raises(TargetContractError, match="unregistered prerequisites"):
        registry.register(_contract("G1", ("G0",)))
    registry.register(_contract("G0"))
    journal = TargetJournal(registry)
    with pytest.raises(TargetContractError, match="requires product type"):
        journal.put(MemoryProduct(
            product_id="wrong",
            product_type="wrong-type",
            target_id="G0",
            revision=1,
            payload={},
        ))
