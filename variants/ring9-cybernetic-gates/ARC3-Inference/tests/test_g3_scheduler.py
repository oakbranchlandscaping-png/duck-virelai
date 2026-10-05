import json

import pytest

from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine
from inference.framework.virelai_gates import GateContractError


GRID = (
    (0, 0, 0, 0),
    (0, 2, 0, 3),
    (0, 0, 0, 0),
)


def machine_for(actions, mode, *, grid=GRID):
    machine = CyberneticGateMachine(valid_actions=actions, initial_grid=grid)
    machine.submit_answer({
        "answer_id": "G0-test",
        "action_metadata": [
            {"action": action, "requires_coordinates": action == "ACTION6"}
            for action in actions
        ],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-test",
        product_type="EgoLaw",
        target_id="G1-EGO",
        revision=1,
        payload={"mode": mode},
        dependencies=("G0-ACTION-METADATA",),
    ))
    machine.target_journal.put(MemoryProduct(
        product_id="COUNTER-test",
        product_type="CounterGateProduct",
        target_id="G2-COUNTER",
        revision=1,
        payload={
            "counter_model": {"model_id": "CM-test"},
            "mask_law": {"law_version_id": "MASK-test"},
            "ranked_object_frontier": {"schema": "virelai-ranked-object-frontier-v1"},
        },
        dependencies=("G1-EGO",),
    ))
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-test",
        law_version_id="MASK-test",
        revision=1,
        status="LOCKED",
        cells=(),
        rewrite="remove sealed counter cells from the derived G3 view",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )
    return machine


def submit_pending_dossier(machine, *, explanation=None):
    template = machine.gate_view()["answer_template"]
    return machine.submit_answer({
        **template,
        "explanation": explanation or (
            "The confirmed direct intervention changes the target-owned residue within the "
            "controller supplied non-counter causal scope."
        ),
        "competing_models": ["An unrelated hidden process produced the same visible response."],
        "falsifier": "A later identical intervention repeatedly fails to reproduce the scoped response.",
    })


def test_click_first_positive_witness_certifies_lever_and_advances_roster():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    first = machine.next_probe_capability()
    assert machine.gate_id == "G3-LEVERS"
    assert first["purpose"] == "RANKED_CLICK_TARGET"
    assert first["target"]["rank"] == 1
    again = machine.next_probe_capability()
    assert again["probe_token"] == first["probe_token"]
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [{"row": 1, "col": 1}],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    assert event["scheduler"]["target_index"] == 1
    assert event["scheduler"]["target_changed"] is True
    assert event["attribution"]["disposition"] == "LOCAL_LEVER_WITNESS"
    assert event["lever_discovery"]["status"] == "LEVER_FOUND"
    assert event["lever_discovery"]["channel"] == "POINTER"
    assert machine._adapters["G3-LEVERS"]._pending_confirmation is None
    entity_id = event["lever_discovery"]["entity_id"]
    assert machine._adapters["G3-LEVERS"].lifecycle_journal.entities[entity_id].state == "G4-READY"
    evidence = machine.evidence_view(event["evidence_id"])
    assert evidence["gate_id"] == "G3-LEVERS"
    assert evidence["evidence_id"] == event["evidence_id"]
    assert evidence["observation"]["target_member_id"] == first["target"]["member_id"]
    assert evidence["observation"]["changed_cells"]
    assert machine.next_probe_capability()["target"]["rank"] == 2


def test_g3_model_view_is_bounded_and_entity_geometry_is_queryable():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    view = machine.gate_view()

    assert len(json.dumps(view)) < 24_000
    assert view["entity_ledger"]["schema"] == "virelai-g3-entity-ledger-compact-v1"
    entity_id = machine.next_probe_capability()["target"]["entity_id"]
    compact = view["entity_ledger"]["entities"][entity_id]
    assert "cells" not in compact["current"]

    detail = machine.entity_view(entity_id, offset=0, limit=1)
    assert detail["current"]["page"]["limit"] == 1
    assert len(detail["current"]["cells_page"]) == 1
    assert detail["current"]["page"]["total"] == compact["current"]["cell_count"]


def test_g3_large_frontier_keeps_full_geometry_out_of_automatic_view():
    large_grid = tuple(
        tuple(
            2 if (row, col) == (20, 20) else 3 if (row, col) == (42, 42) else 0
            for col in range(64)
        )
        for row in range(64)
    )
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE", grid=large_grid)
    lever = machine._adapters["G3-LEVERS"]

    full_frontier = lever._frontier_snapshot()
    view = machine.gate_view()
    compact_frontier = view["inherited_frontier"]

    assert len(json.dumps(full_frontier)) > 24_000
    assert len(json.dumps(view)) < 24_000
    # Axiom A6 (2026-09-28): the card is a bounded window of the roster; the rest is one paged
    # query away and the lossless roster stays in the snapshot.
    assert compact_frontier["view"] == "WINDOWED_ROSTER"
    assert compact_frontier["accounting_complete"] is True
    assert (
        len(compact_frontier["candidates"]) + compact_frontier["candidates_omitted"]
        == len(full_frontier["candidates"])
    )
    assert "inventory" in compact_frontier["roster_query"]
    assert all("cells" not in row and "original_cells" not in row
               for row in compact_frontier["candidates"])
    assert all(row["entity_id"] in row["detail_query"]
               for row in compact_frontier["candidates"])
    listed = {row["member_id"] for row in compact_frontier["candidates"]}
    assert sum(row["cells_omitted"] for row in compact_frontier["candidates"]) == sum(
        len(row["cells"]) for row in full_frontier["candidates"] if row["member_id"] in listed
    )


def test_g3_confirmation_geometry_is_expandable_and_not_prompt_inline():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    lever = machine._adapters["G3-LEVERS"]
    cells = [[row, col] for row in range(5) for col in range(53)]
    lever._confirmation_records = [{
        "witness_evidence_ref": "E-witness",
        "confirmation_evidence_ref": "E-confirmation",
        "target_member_id": "M0004",
        "entity_id": "E0004",
        "declared_at_transition": 4,
        "graded_at_transition": 5,
        "frozen_target": {"cells": cells, "bbox": [0, 0, 4, 52]},
        "predicted_local_cells": cells[:20],
        "predicted_remote_cells": cells[20:],
        "status": "SUPPORTED",
    }]

    compact = machine.gate_view()
    full = machine.snapshot()
    record = compact["attribution_contract"]["confirmation_records"][0]

    assert len(json.dumps(compact)) < 24_000
    assert len(json.dumps(full)) > len(json.dumps(compact))
    assert record["geometry_delivery"] == "FOCUSED_EVIDENCE_QUERY"
    assert "predicted_remote_cells" not in record
    assert record["predicted_remote_summary"]["cell_count"] == len(cells) - 20
    assert record["frozen_target_summary"]["cell_count"] == len(cells)


def test_g3_model_view_omits_unbound_transient_worldlines():
    from inference.framework.entity_observation import EntityHypothesis

    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    lever = machine._adapters["G3-LEVERS"]
    ledger = lever._ensure_entity_ledger()
    for index in range(100):
        entity_id = f"TRANSIENT-{index:03d}"
        ledger.entities[entity_id] = EntityHypothesis(entity_id=entity_id, status="ABSENT")

    view = machine.gate_view()

    assert len(json.dumps(view)) < 24_000
    assert view["entity_ledger"]["entity_count"] >= 100
    assert view["entity_ledger"]["omitted_transient_entity_count"] >= 100
    assert not any(key.startswith("TRANSIENT-") for key in view["entity_ledger"]["entities"])


def test_nav_scheduler_binds_one_target_and_requires_intent():
    machine = machine_for(["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO")
    capability = machine.next_probe_capability()
    assert capability["purpose"] == "PILOT_TO_LEVER_CONTACT"
    assert capability["actions"] == []
    assert capability["target"]["rank"] == 1
    admitted = machine.validate_probe(
        {"probe_token": capability["probe_token"], "pilot_intent": "APPROACH"},
        [{"action": "ACTION1"}],
    )
    assert admitted.pilot_intent == "APPROACH"
    assert machine.next_probe_capability()["target"]["rank"] == 1


def test_boundary_interrupted_confirmation_defers_to_g4_and_retries_target():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine._legacy_confirmation_replay = True
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [{"row": 1, "col": 1}],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    confirmation = machine.next_probe_capability()
    confirmation_probe = machine.validate_probe(
        {"probe_token": confirmation["probe_token"]}, confirmation["actions"]
    )
    interrupted = machine.record_outcome(confirmation_probe, {
        "transition_id": 2,
        "action": confirmation["actions"][0],
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "GAME_OVER", "done": True, "game_over": True},
    })
    assert interrupted["confirmation"]["status"] == "BOUNDARY_DEFERRED"
    assert interrupted["scheduler"]["target_index"] == 0
    view = machine.gate_view()
    entity_id = first["target"]["entity_id"]
    assert view["lifecycle_journal"]["entities"][entity_id]["state"] == "AMBIGUOUS"
    assert view["deferred_observations"][-1]["target_gate"] == "G4-REACTIONS"
    retry = machine.next_probe_capability()
    assert retry["purpose"] == "RANKED_CLICK_TARGET"
    assert retry["target"]["rank"] == 1


def test_boundary_interrupted_ranked_click_retries_same_target():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    interrupted = machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "GAME_OVER", "done": True, "game_over": True},
    })
    assert interrupted["scheduler"]["target_index"] == 0
    assert machine.next_probe_capability()["target"]["rank"] == 1
    entity_id = first["target"]["entity_id"]
    assert machine.gate_view()["lifecycle_journal"]["entities"][entity_id]["state"] == "AMBIGUOUS"


def test_unresolved_click_is_bounded_when_no_distinct_probe_exists_and_sweep_advances():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    outcome = {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    }
    # Force the acted-site owner to be unknown without changing the ranked target.
    outcome["acted_site"] = {"row": 0, "col": 0}
    event = machine.record_outcome(probe, outcome)

    assert event["attribution"]["disposition"] == "UNRESOLVED_ATTRIBUTION"
    assert event["scheduler"]["target_index"] == 1
    assert event["bounded_ambiguity"]["terminal_state"] == "AMBIGUOUS"
    assert event["bounded_ambiguity"]["inertness_claim_permitted"] is False
    following = machine.next_probe_capability()
    assert following["target"]["rank"] == first["target"]["rank"] + 1
    entity_id = first["target"]["entity_id"]
    assert machine.gate_view()["lifecycle_journal"]["entities"][entity_id]["state"] == "AMBIGUOUS"


def test_system_reset_keeps_g3_target_identity_bound_to_spawn_slot():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    first = machine.next_probe_capability()
    entity_id = first["target"]["entity_id"]
    reset = {
        "transition_id": 1,
        "action": {"action": "RESET"},
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING", "reset": True},
    }

    machine.observe_system_reset(reset)
    after = machine.next_probe_capability()

    assert after["target"]["entity_id"] == entity_id
    detail = machine.entity_view(entity_id)
    assert detail["current"]["relation"] == "RESET_RETURN"


def test_boundary_reset_retry_can_attribute_the_same_rank_after_respawn():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine._legacy_confirmation_replay = True
    first = machine.next_probe_capability()
    entity_id = first["target"]["entity_id"]
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    boundary = {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "GAME_OVER", "game_over": True},
    }
    machine.record_outcome(probe, boundary)
    reset = dict(boundary)
    reset.update({
        "transition_id": 2,
        "action": {"action": "RESET"},
        "boundary_event": {"state": "PLAYING", "reset": True},
    })
    machine.observe_system_reset(reset)

    retry = machine.next_probe_capability()
    assert retry["target"]["rank"] == first["target"]["rank"]
    assert retry["target"]["entity_id"] == entity_id
    retry_probe = machine.validate_probe(
        {"probe_token": retry["probe_token"]}, retry["actions"]
    )
    target_cell = tuple(retry["target"]["cells"][0])
    outcome = {
        "transition_id": 3,
        "action": retry["actions"][0],
        "changed_cells": [{"row": target_cell[0], "col": target_cell[1]}],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    }
    event = machine.record_outcome(retry_probe, outcome)

    assert event["attribution"]["disposition"] == "LOCAL_LEVER_WITNESS"
    assert event["attribution"]["contact_attributed"] is True
    assert event["attribution"]["attribution_basis"] == "PRE_ACTION_POINTER_OWNER"
    assert event["scheduler"]["target_index"] == 0
    assert machine.next_probe_capability()["purpose"] == "CONFIRM_LEVER_WITNESS"


def test_completed_probe_roster_requires_and_accepts_evidence_bound_inventory():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine._legacy_confirmation_replay = True
    lever = machine._adapters["G3-LEVERS"]
    lever.machine.counter._ranked_visual_targets = lever.machine.counter._ranked_visual_targets[:1]
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [{"row": 1, "col": 1}],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe(
        {"probe_token": confirm["probe_token"]}, confirm["actions"]
    )
    machine.record_outcome(confirm_probe, {
        "transition_id": 2,
        "action": confirm["actions"][0],
        "changed_cells": [{"row": 1, "col": 1}],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    dossier = submit_pending_dossier(machine)
    assert machine.next_probe_capability() is None
    view = machine.gate_view()
    assert view["status"] == "ANSWER_REQUIRED"
    assert view["next_operation"] == "SUBMIT_GATE_ANSWER"
    entity_id = first["target"]["entity_id"]
    witness_ref = machine.snapshot()["lifecycle_journal"]["entities"][entity_id]["witness_refs"][0]
    inventory = machine.submit_answer({
        "answer_kind": "LEVER_INVENTORY",
        "lever_entities": [entity_id],
        "explanation": "The exhaustive click roster found this object to be a lever.",
        "evidence_refs": [witness_ref],
        "competing_models": ["The response was spontaneous."],
        "falsifier": "A reset and repeated click fails to reproduce the response.",
    })
    assert dossier.answer_kind == "LEVER_DOSSIER"
    assert inventory.answer_kind == "LEVER_INVENTORY"
    assert machine.gate_id == "G4-REACTIONS"
    completion = lever._completion_gate_view()
    revision = completion["revision"]
    assert completion["status"] == "SATISFIED"
    assert completion["completion"]["kind"] == "CLEAN_INVENTORY"
    assert completion["answer_template"] is None
    assert completion["next_operation"] == "WAIT_FOR_NEXT_TARGET"
    assert [row["query"] for row in completion["expand"]] == [
        "virelai('inventory', offset=0, limit=10)",
        "virelai('entity', id=entity_id, offset=0, limit=128)",
        "virelai('evidence', id=evidence_id)",
    ]
    assert machine.target_journal.active_product("G3-LEVERS") is not None
    with pytest.raises(GateContractError, match="already accepted"):
        lever.submit_answer({
            "answer_kind": "LEVER_INVENTORY",
            "lever_entities": [entity_id],
        })
    assert lever._completion_gate_view()["revision"] == revision


def test_g3_excludes_wholly_masked_counter_member_and_preserves_source_ranks():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    counter_member = machine.counter._ranked_visual_targets[1]
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-test",
        law_version_id="MASK-test",
        revision=2,
        status="LOCKED",
        cells=tuple(counter_member.cells),
        rewrite="remove the entire sealed counter footprint from the derived G3 view",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )

    view = machine.gate_view()
    frontier = view["inherited_frontier"]
    assert frontier["original_candidate_count"] == 3
    assert frontier["candidate_count"] == 2
    assert frontier["excluded_candidate_count"] == 1
    assert frontier["accounting_complete"] is True
    assert [item["source_rank"] for item in frontier["candidates"]] == [1, 3]
    assert [item["eligible_rank"] for item in frontier["candidates"]] == [1, 2]
    exclusion = frontier["excluded_candidates"][0]
    assert exclusion["member_id"] == counter_member.member_id
    assert exclusion["source_rank"] == 2
    assert exclusion["disposition"] == "COUNTER_ROLE_EXCLUDED"
    assert exclusion["mask_law_version_id"] == "MASK-test"
    assert exclusion["evidence_refs"] == [
        "E-counter-witness", "E-counter-demonstration"
    ]

    scheduled = []
    while True:
        capability = machine.next_probe_capability()
        if capability is None:
            break
        scheduled.append(capability["target"])
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        machine.record_outcome(probe, {
            "transition_id": len(scheduled),
            "action": capability["actions"][0],
            "changed_cells": [],
            "site_transitions": [
                {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
                for row in range(3) for col in range(4)
            ],
            "shape_before": [3, 4], "shape_after": [3, 4],
            "boundary_event": {"state": "PLAYING"},
        })

    assert [item["source_rank"] for item in scheduled] == [1, 3]
    assert [item["eligible_rank"] for item in scheduled] == [1, 2]
    assert counter_member.member_id not in {item["member_id"] for item in scheduled}
    final = machine.snapshot()
    assert counter_member.member_id not in final["entity_ledger"]["member_bindings"]


def test_typed_dossier_rejects_scalar_competitor_and_counter_causal_reintroduction():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine._legacy_confirmation_replay = True
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-test", law_version_id="MASK-test", revision=2, status="LOCKED",
        cells=((0, 0),), rewrite="0->1",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    base = {
        "action": first["actions"][0],
        "changed_cells": [
            {"row": 1, "col": 1, "before": 2, "after": 4},
            {"row": 0, "col": 0, "before": 0, "after": 1},
        ],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    }
    machine.record_outcome(probe, {**base, "transition_id": 1})
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe(
        {"probe_token": confirm["probe_token"]}, confirm["actions"]
    )
    machine.record_outcome(confirm_probe, {**base, "transition_id": 2})
    template = machine.gate_view()["answer_template"]

    with pytest.raises(GateContractError, match="competing_models must be a list"):
        machine.submit_answer({
            **template,
            "explanation": (
                "The target caused the local residue while the counter bookkeeping change was masked and excluded."
            ),
            "competing_models": "A hidden process caused the visible response.",
            "falsifier": "A repeated click fails to reproduce the scoped local response.",
        })

    with pytest.raises(GateContractError, match="counter change"):
        machine.submit_answer({
            **template,
            "explanation": (
                "The clicked lever caused the local residue and the counter changed as a third causal effect."
            ),
            "competing_models": ["A hidden process caused the visible response."],
            "falsifier": "A repeated click fails to reproduce the scoped local response.",
        })

    answer = machine.submit_answer({
        **template,
        "explanation": (
            "The clicked lever caused the local residue; the counter bookkeeping change was masked and excluded."
        ),
        "competing_models": ["A hidden process caused the visible response."],
        "falsifier": "A repeated click fails to reproduce the scoped local response.",
    })
    assert answer.effect_summary["counter_masked_cell_count"] == 1
    assert answer.effect_summary["counter_treatment"] == (
        "COUNTER_CHANGES_EXCLUDED_FROM_LEVER_CAUSALITY"
    )


def test_bounded_ambiguity_finishes_roster_with_nonclosing_coverage_report():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine.counter._ranked_visual_targets = machine.counter._ranked_visual_targets[:1]
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "acted_site": {"row": 0, "col": 0},
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    assert event["bounded_ambiguity"]["retry_condition"]
    assert machine.next_probe_capability() is None
    view = machine.gate_view()
    template = view["answer_template"]
    report = machine.submit_answer({
        **template,
        "explanation": (
            "The exhaustive authorized roster ended with one explicitly bounded attribution ambiguity."
        ),
        "competing_models": ["The target responds only under an unobserved hidden condition."],
        "falsifier": "A newly admissible discriminating probe resolves the target attribution.",
    })

    assert report.answer_kind == "G3_BOUNDED_COVERAGE_REPORT"
    completion = machine.gate_view()
    assert completion["schema"] == "virelai-g3-completion-card-v1"
    assert completion["status"] == "UNRESOLVED"
    assert completion["next_operation"] == "WAIT_FOR_DISCRIMINATING_EVIDENCE"
    assert completion["completion"]["kind"] == "BOUNDED_COVERAGE"
    assert completion["bounded_unknowns"]["total"] == 1
    assert "entity_ledger" not in completion
    assert "inherited_frontier" not in completion
    assert len(json.dumps(completion)) < 12_000
    inventory = machine.inventory_view(offset=0, limit=1)
    assert inventory["items"][0]["disposition"] == "BOUNDED_UNKNOWN"
    assert inventory["items"][0]["retry_condition"]
    assert machine.target_journal.active_product("G3-LEVERS") is None


def test_counter_only_final_target_closes_as_scoped_no_lever_response():
    machine = machine_for(["ACTION6"], "POINTER_GOD_MODE")
    machine.counter._ranked_visual_targets = machine.counter._ranked_visual_targets[:1]
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-counter-only",
        law_version_id="MASK-counter-only",
        revision=1,
        status="LOCKED",
        cells=((0, 0),),
        rewrite="remove sealed counter cells from the derived G3 view",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "acted_site": {"row": 0, "col": 0},
        "changed_cells": [{"row": 0, "col": 0, "before": 0, "after": 4}],
        "site_transitions": [
            {
                "row": row,
                "col": col,
                "before": GRID[row][col],
                "after": 4 if (row, col) == (0, 0) else GRID[row][col],
            }
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4],
        "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })

    assert event["attribution"]["disposition"] == "COUNTER_ONLY_RESPONSE"
    assert "bounded_ambiguity" not in event
    assert machine.next_probe_capability() is None
    template = machine.gate_view()["answer_template"]
    assert template["ambiguous_entities"] == []
    assert len(template["clean_null_entities"]) == 1
