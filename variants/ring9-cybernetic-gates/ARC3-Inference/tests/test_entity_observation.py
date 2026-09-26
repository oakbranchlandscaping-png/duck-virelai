from inference.framework.entity_observation import EntityLedger


def transition(before, after, *, transition_id=1, action=None):
    changed = []
    sites = []
    rows = len(before)
    cols = len(before[0])
    for row in range(rows):
        for col in range(cols):
            left, right = before[row][col], after[row][col]
            sites.append({"row": row, "col": col, "before": left, "after": right})
            if left != right:
                changed.append({"row": row, "col": col, "before": left, "after": right})
    return {
        "schema": "virelai-probe-outcome-v1",
        "transition_id": transition_id,
        "action": action or {"action": "ACTION6", "row": 0, "col": 0},
        "changed_cells": changed,
        "site_transitions": sites,
        "shape_before": [rows, cols],
        "shape_after": [rows, cols],
        "acted_site": {"row": 0, "col": 0},
        "boundary_event": {"state": "PLAYING"},
    }


def test_member_binding_survives_unique_translation_and_recolor():
    before = ((1, 0, 2, 0), (0, 0, 0, 0))
    ledger = EntityLedger(before)
    entity = ledger.entity_at((0, 0))
    ledger.bind_members([{"member_id": "M1", "integer": 1, "cells": [[0, 0]]}])
    assert ledger.entity_for_member("M1") == entity

    moved = ((0, 1, 2, 0), (0, 0, 0, 0))
    result = ledger.observe(transition(before, moved))
    assert (entity, "MOVE", "PRESENT") in result.relations
    assert ledger.cells_for(entity) == ((0, 1),)

    recolored = ((0, 3, 2, 0), (0, 0, 0, 0))
    result = ledger.observe(transition(moved, recolored, transition_id=2))
    assert (entity, "RECOLOR", "PRESENT") in result.relations
    assert ledger.cells_for(entity) == ((0, 1),)


def test_ambiguous_translation_creates_new_hypothesis_and_records_limit():
    before = ((1, 0, 1, 0), (0, 0, 0, 0))
    ledger = EntityLedger(before)
    after = ((0, 1, 0, 1), (0, 0, 0, 0))
    result = ledger.observe(transition(before, after))
    assert any(relation == "AMBIGUOUS" for _, relation, _ in result.relations)
    assert any(item.ambiguity_refs for item in ledger.entities.values())


def test_scope_uses_pre_action_owner_and_retains_counter_and_contact_cells():
    before = ((1, 0, 2, 0), (0, 0, 0, 0))
    after = ((0, 1, 2, 0), (0, 0, 0, 0))
    ledger = EntityLedger(before)
    target = ledger.entity_at((0, 2))
    ego = ledger.entity_at((0, 0))
    scope = ledger.scope(
        transition(before, after),
        target_entity_id=target,
        ego_entity_ids=[ego],
        counter_mask_cells=[(1, 1)],
        expected_ego_motion=True,
    )
    assert scope.status == "READY"
    assert scope.pre_action_owner_entity_id == ego
    assert scope.target_cells == ((0, 2),)
    assert scope.ego_expected_cells == ((0, 0), (0, 1))
    assert scope.counter_mask_cells == ()
    assert scope.ego_motion_basis == "AUTHORIZED_EGO_MOTION_SCOPE"


def test_role_binding_is_explicit_and_click_does_not_authorize_ego_subtraction():
    before = ((1, 0, 2, 0), (0, 0, 0, 0))
    after = ((0, 1, 2, 0), (0, 0, 0, 0))
    ledger = EntityLedger(before)
    ego = ledger.bind_role_cells("EGO", [(0, 0)])[0]
    scope = ledger.scope(
        transition(before, after),
        target_entity_id=ledger.entity_at((0, 2)),
        ego_entity_ids=[ego],
        expected_ego_motion=False,
    )
    assert scope.ego_expected_cells == ()
    assert scope.ego_confounded_cells == ((0, 1),)
    assert scope.ego_motion_basis == "NO_AUTHORIZED_EGO_MOTION_FOR_ACTION"


def test_scope_abstains_when_site_ledger_is_missing():
    ledger = EntityLedger(((1,),))
    scope = ledger.scope(
        {"transition_id": 1, "changed_cells": []},
        target_member_id="M1",
    )
    assert scope.status == "UNRESOLVED"
    assert any("site_transitions" in item for item in scope.limitations)


def test_duplicate_transition_is_idempotent_and_preserves_frame_chain():
    before = ((1, 0, 2),)
    after = ((0, 1, 2),)
    ledger = EntityLedger(before)
    entity = ledger.entity_at((0, 0))
    outcome = transition(before, after, transition_id=7)

    first = ledger.observe(outcome)
    version = ledger.entities[entity].version
    second = ledger.observe(outcome)

    assert second is first
    assert len(ledger.transitions) == 1
    assert ledger.entities[entity].version == version
    assert "before frame did not match" not in ledger.limitations


def test_site_only_reset_return_preserves_spawn_entity_and_member_binding():
    spawn = ((1, 0, 2),)
    changed = ((0, 1, 2),)
    ledger = EntityLedger(spawn)
    entity = ledger.entity_at((0, 0))
    ledger.bind_members([{"member_id": "M1", "integer": 1, "cells": [[0, 0]]}])
    ledger.observe(transition(spawn, changed, transition_id=1))

    reset = transition(changed, spawn, transition_id=2, action={"action": "RESET"})
    result = ledger.observe_reset(reset)

    assert (entity, "RESET_RETURN", "PRESENT") in result.relations
    assert ledger.entity_for_member("M1") == entity
    assert ledger.entity_at((0, 0)) == entity
    assert ledger.entities[entity].current.relation == "RESET_RETURN"


def test_masked_counter_ticks_do_not_create_or_churn_entity_hypotheses():
    before = ((1, 1), (0, 2))
    after = ((3, 0), (0, 2))
    ledger = EntityLedger(
        before,
        ignored_cells=[(0, 0), (0, 1)],
        mask_law_version_id="MASK-counter",
    )
    initial_entities = set(ledger.entities)

    first = ledger.observe(transition(before, after, transition_id=1))
    second = ledger.observe(transition(after, before, transition_id=2))

    assert set(ledger.entities) == initial_entities
    assert all(relation == "STILL" for _, relation, _ in first.relations)
    assert all(relation == "STILL" for _, relation, _ in second.relations)
    assert ledger.entity_at((0, 0)) is None
    snapshot = ledger.snapshot()
    assert snapshot["mask_law_version_id"] == "MASK-counter"
    assert snapshot["ignored_cell_count"] == 2


def test_partial_mask_overlap_retains_disconnected_projection_as_one_target():
    grid = ((5, 5, 5),)
    ledger = EntityLedger(grid, ignored_cells=[(0, 1)])
    ledger.bind_members([{
        "member_id": "M-partial",
        "integer": 5,
        "cells": [[0, 0], [0, 2]],
    }])

    entity_id = ledger.entity_for_member("M-partial")
    assert entity_id is not None
    assert ledger.cells_for(entity_id) == ((0, 0), (0, 2))
    assert ledger.entity_at((0, 0)) == entity_id
    assert ledger.entity_at((0, 1)) is None
    assert any("composite outside-mask projection" in item for item in ledger.limitations)
