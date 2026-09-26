import pytest

from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.g4_reactions import (
    G4ReactionError,
    anatomy_payload,
    compile_effect_anatomy,
    validate_reaction_answer,
)
from inference.framework.lever_attribution import attribute_lever_outcome
from inference.framework.virelai_gates import CyberneticGateMachine


GRID = (
    (0, 0, 0, 0),
    (0, 2, 0, 3),
    (0, 0, 0, 0),
)


def attribution():
    return attribute_lever_outcome(
        {
            "transition_id": 7,
            "acted_site": {"row": 1, "col": 1},
            "changed_cells": [
                {"row": 1, "col": 1, "before": 2, "after": 4},
                {"row": 0, "col": 3, "before": 0, "after": 5},
                {"row": 2, "col": 3, "before": 5, "after": 0},
                {"row": 0, "col": 0, "before": 8, "after": 7},
            ],
            "boundary_event": {"state": "PLAYING"},
        },
        evidence_ref="E-witness",
        channel="POINTER",
        target_member_id="M0001",
        target_cells=((1, 1),),
        counter_mask_cells=((0, 0),),
        ego_motion_cells=(),
        pre_action_owner_member_id="M0001",
    )


def compiled():
    return compile_effect_anatomy(
        attribution(),
        entity_id="E0001",
        intervention={"action": "ACTION6", "row": 1, "col": 1},
        confirmation_evidence_ref="E-confirm",
        dossier_answer_ref="G3-DOSSIER",
        mask_law_version_id="MASK-v1",
    )


def valid_answer(anatomy):
    phrases = []
    for channel in anatomy.channels:
        rewrites = ", ".join(
            f"{before}->{after}" for before, after, _count in channel.integer_transitions
        )
        phrases.append(f"{channel.channel_id} affects its {channel.locality.lower()} region by {rewrites}")
    return {
        "answer_kind": "LEVER_EFFECT_ANATOMY",
        "entity_id": anatomy.entity_id,
        "intervention": dict(anatomy.intervention),
        "effect_channels": anatomy_payload(anatomy, include_cells=False)["channels"],
        "mechanism_explanation": f"Lever {anatomy.entity_id}: " + "; ".join(phrases) + ".",
        "evidence_refs": [anatomy.witness_evidence_ref, anatomy.confirmation_evidence_ref],
        "record_refs": [anatomy.dossier_answer_ref, anatomy.anatomy_id],
        "competing_models": ["The regions share an unseen upstream cause."],
        "falsifier": "The exact intervention produces a different scoped residue.",
        "limitations": list(anatomy.limitations),
    }


def test_anatomy_exactly_partitions_non_counter_residue():
    anatomy = compiled()
    cells = {cell for channel in anatomy.channels for cell in channel.cells}
    assert anatomy.coverage_complete is True
    assert anatomy.residue_cell_count == 3
    assert cells == {(1, 1), (0, 3), (2, 3)}
    assert (0, 0) not in cells
    assert {channel.locality for channel in anatomy.channels} == {"LOCAL", "REMOTE"}
    assert sum(channel.changed_cell_count for channel in anatomy.channels) == 3
    assert "REPETITION_LAW" in anatomy.open_questions


def test_answer_requires_human_use_of_every_exact_channel():
    anatomy = compiled()
    answer = validate_reaction_answer(valid_answer(anatomy), anatomy)
    assert answer.entity_id == "E0001"

    missing = valid_answer(anatomy)
    missing["mechanism_explanation"] = "E0001 changed several affected regions in a visible way."
    with pytest.raises(G4ReactionError, match="must discuss channel"):
        validate_reaction_answer(missing, anatomy)

    corrupted = valid_answer(anatomy)
    corrupted["effect_channels"] = corrupted["effect_channels"][:-1]
    with pytest.raises(G4ReactionError, match="exactly preserve"):
        validate_reaction_answer(corrupted, anatomy)


def machine_at_g3():
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=GRID)
    machine.submit_answer({
        "answer_id": "G0-test",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-test", product_type="EgoLaw", target_id="G1-EGO", revision=1,
        payload={"mode": "POINTER_GOD_MODE"}, dependencies=("G0-ACTION-METADATA",),
    ))
    machine.target_journal.put(MemoryProduct(
        product_id="COUNTER-test", product_type="CounterGateProduct", target_id="G2-COUNTER",
        revision=1, payload={"counter_model": {"model_id": "CM-test"}, "mask_law": {
            "law_version_id": "MASK-test"}, "ranked_object_frontier": {}},
        dependencies=("G1-EGO",),
    ))
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-test", law_version_id="MASK-test", revision=1, status="LOCKED",
        cells=(), rewrite="remove counter", witness_evidence_refs=("E-counter",),
        demonstration_ref="E-counter-confirm",
    )
    machine.counter._ranked_visual_targets = machine.counter._ranked_visual_targets[:1]
    return machine


def test_g4_routes_from_clean_g3_inventory_and_emits_anatomy_product():
    machine = machine_at_g3()
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    machine.record_outcome(probe, {
        "transition_id": 1,
        "action": first["actions"][0],
        "changed_cells": [{"row": 1, "col": 1, "before": 2, "after": 4}],
        "site_transitions": [], "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe({"probe_token": confirm["probe_token"]}, confirm["actions"])
    machine.record_outcome(confirm_probe, {
        "transition_id": 2,
        "action": confirm["actions"][0],
        "changed_cells": [{"row": 1, "col": 1, "before": 2, "after": 4}],
        "site_transitions": [], "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    dossier_template = machine.gate_view()["answer_template"]
    machine.submit_answer({
        **dossier_template,
        "explanation": "The clicked target causes the exact non-counter local residue.",
        "competing_models": ["A hidden process caused the same response."],
        "falsifier": "A repeat fails to reproduce the scoped response.",
    })
    assert machine.next_probe_capability() is None
    entity_id = first["target"]["entity_id"]
    witness_ref = machine._adapters["G3-LEVERS"].lifecycle_journal.entities[entity_id].witness_refs[0]
    machine.submit_answer({
        "answer_kind": "LEVER_INVENTORY",
        "lever_entities": [entity_id], "clean_null_entities": [], "ambiguous_entities": [],
        "explanation": "The complete click roster found one confirmed lever.",
        "evidence_refs": [witness_ref],
        "competing_models": ["The response was spontaneous."],
        "falsifier": "The supported click stops producing the response.",
    })

    assert machine.gate_id == "G4-REACTIONS"
    view = machine.gate_view()
    assert view["subject_accounting"]["g3_ready_lever_count"] == 1
    assert view["subject_accounting"]["excluded_scoped_null_count"] == 0
    assert view["current_lever"]["coverage_complete"] is True
    detail = machine.reaction_view(entity_id)
    assert detail["anatomy"]["channels"][0]["cells"]

    template = view["answer_template"]
    channel = template["effect_channels"][0]
    rewrites = ", ".join(
        f"{before}->{after}" for before, after, _count in channel["integer_transitions"]
    )
    machine.submit_answer({
        **template,
        "mechanism_explanation": (
            f"Lever {entity_id}: {channel['channel_id']} affects the local target region "
            f"through the exact observed rewrite {rewrites}."
        ),
        "competing_models": ["A hidden event coincided with the click."],
        "falsifier": "The same intervention produces a different exact residue.",
    })
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    assert machine.status == "PROBE_REQUIRED"
    assert machine.gate_view()["next_operation"] == "QUERY_NEXT_PROBE"
    product = machine.target_journal.active_product("G4-REACTIONS")
    assert product is not None
    assert product.product_type == "LeverEffectAnatomySet"
    g2_product_id = machine.target_journal.active_product("G2-COUNTER").product_id
    g3_product_id = machine.target_journal.active_product("G3-LEVERS").product_id
    g4_product_id = product.product_id
    # A leftover historical boundary obligation must be inert after G2. It is
    # included here to reproduce the live v2 regression that reopened G3.
    machine.counter.boundary_obligation = {"status": "OPEN", "source_after": 1}

    orbit_capability = machine.next_probe_capability()
    assert orbit_capability["purpose"] == "REPEAT_CONFIRMED_LEVER"
    orbit_probe = machine.validate_probe(
        {"probe_token": orbit_capability["probe_token"]},
        orbit_capability["actions"],
    )
    first_sites = [
        {
            "row": row,
            "col": col,
            "before": value,
            "after": 5 if (row, col) == (0, 1) else value,
        }
        for row, values in enumerate(GRID)
        for col, value in enumerate(values)
    ]
    orbit_event = machine.record_outcome(orbit_probe, {
        "transition_id": 3,
        "action": orbit_capability["actions"][0],
        "changed_cells": [{"row": 0, "col": 1, "before": 0, "after": 5}],
        "site_transitions": first_sites,
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    assert orbit_event["orbit_step"]["disposition"] == "NOVEL_STATE_REVEALED"
    assert orbit_event["counter_baseline"]["policy"] == "MASK_AND_IGNORE_AFTER_G2"
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    assert machine.target_journal.active_product("G2-COUNTER").product_id == g2_product_id
    assert machine.target_journal.active_product("G3-LEVERS").product_id == g3_product_id
    assert machine.target_journal.active_product("G4-REACTIONS").product_id == g4_product_id

    second_capability = machine.next_probe_capability()
    assert machine.next_probe().probe_id.endswith(":2")
    second_probe = machine.validate_probe(
        {"probe_token": second_capability["probe_token"]},
        second_capability["actions"],
    )
    second_sites = [
        {
            "row": row,
            "col": col,
            "before": 5 if (row, col) == (0, 1) else value,
            "after": 5 if (row, col) == (0, 1) else value,
        }
        for row, values in enumerate(GRID)
        for col, value in enumerate(values)
    ]
    second_event = machine.record_outcome(second_probe, {
        "transition_id": 4,
        "action": second_capability["actions"][0],
        "changed_cells": [],
        "site_transitions": second_sites,
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    })
    assert second_event["orbit_step"]["disposition"] == "NULL_AT_OBSERVED_STATE"
    orbit_answer = machine.gate_view()["answer_template"]
    machine.submit_answer({
        **orbit_answer,
        "mechanism_explanation": (
            "Repeated activation left the complete counter-masked world unchanged at this state."
        ),
        "competing_models": ["The lever may respond from another world state."],
        "falsifier": "The same repeat changes this exact masked state later.",
    })
    assert machine.gate_id == "G4.3-LEVER-LIMITS"
    assert machine.status == "PROBE_REQUIRED"
    assert machine.gate_view()["progress"]["current_phase"] == "CONFIRM_ENDPOINT"
    orbit_product = machine.target_journal.active_product("G4.2-LEVER-ORBITS")
    assert orbit_product is not None
    assert orbit_product.payload["orbits"][0]["status"] == "NULL_AT_OBSERVED_STATE"
