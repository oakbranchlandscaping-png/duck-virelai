import pytest

from inference.framework.virelai_gates import CyberneticGateMachine, GateContractError


GRID = (
    (7, 7, 7, 7, 0, 0),
    (0, 0, 0, 0, 0, 0),
    (0, 2, 2, 0, 3, 0),
    (0, 0, 0, 0, 0, 0),
)


def g2_machine():
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=GRID)
    machine.submit_answer({
        "answer_id": "G0-click",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until controlled observation reveals them.",
    })
    machine.submit_answer({
        "answer_id": "G1-pointer",
        "answer_kind": "POINTER_GOD_MODE",
        "subjects": ["the ACTION6 site-selecting control locus"],
        "mechanism": "Duck moves its pointer ego by supplying a new grid coordinate",
        "action_laws": {"ACTION6": "places direct intervention at the supplied grid coordinate"},
        "conditions": ["the coordinate is legal"],
        "constraints": ["target effects remain unknown"],
        "evidence_refs": ["G0-ACTION-METADATA"],
        "competing_models": ["a persistent embodied grid object is controlled"],
        "falsifier": "ACTION6 requires no selected coordinate for direct intervention",
        "limitations": ["no target response has been classified"],
    })
    assert machine.gate_id == "G2-COUNTER"
    return machine


def test_click_counter_hunt_uses_exhaustive_strict_visual_object_order():
    machine = g2_machine()
    ranked = machine.counter._visual_roster.ranked_candidates()
    actions = machine.counter._probe_actions
    assert len(actions) == len(ranked)
    assert actions == tuple(
        {"action": "ACTION6", "row": item.anchor[0], "col": item.anchor[1]}
        for item in ranked
    )
    protocol = machine.counter.snapshot()["opening_protocol"]
    assert protocol["sweep_arm"] == "CLICK_EVERYTHING"
    assert protocol["enumeration_total"] == len(ranked)
    assert protocol["rank_is_semantics"] is False


def test_nav_counter_hunt_binds_ranked_target_while_duck_pilots_to_contact():
    from inference.framework.virelai_gates import CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        affordances=action_affordances(["ACTION1", "ACTION2", "ACTION3", "ACTION4"]),
        initial_grid=GRID,
        observed_through_step=8,
    )
    first = counter.next_probe()
    assert first is not None
    assert first.purpose == "PILOT_TO_CONTACT"
    assert first.actions == ()
    assert first.admissible_actions == ("ACTION1", "ACTION2", "ACTION3", "ACTION4")
    assert first.target["rank"] == 1
    target_id = first.target["member_id"]

    approach = counter.validate_probe(
        {"pilot_intent": "APPROACH"}, [{"action": "ACTION1"}]
    )
    event = counter.record_outcome(approach, {
        "transition_id": 9,
        "action": {"action": "ACTION1"},
        "board_changed": True,
        "changed_cell_count": 1,
        "changed_cells": [{"row": 3, "col": 5, "before": 0, "after": 1}],
        "boundary_event": {},
    })
    assert "navigation_target_result" not in event
    assert counter.next_probe().target["member_id"] == target_id

    contact = counter.validate_probe(
        {"pilot_intent": "CONTACT_ATTEMPT"}, [{"action": "ACTION2"}]
    )
    target_cell = counter._ranked_target().cells[0]
    event = counter.record_outcome(contact, {
        "transition_id": 10,
        "action": {"action": "ACTION2"},
        "board_changed": True,
        "changed_cell_count": 1,
        "changed_cells": [{
            "row": target_cell[0], "col": target_cell[1], "before": 3, "after": 0
        }],
        "boundary_event": {},
    })
    result = event["navigation_target_result"]
    assert result["member_id"] == target_id
    assert result["disposition"] == "TARGET_RESPONDED"
    assert result["attribution"] == "DIRECT_TARGET_FOOTPRINT_DELTA"
    assert counter.sweep_frontier()["observed_count"] == 1
    assert counter.next_probe().target["rank"] == 2


def test_nav_roster_excludes_duck_identified_ego_and_structural_fields():
    from inference.framework.virelai_gates import CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        affordances=action_affordances(["ACTION1", "ACTION2"]),
        initial_grid=GRID,
        observed_through_step=4,
        excluded_ego_cells=((2, 1), (2, 2)),
        ego_binding_source="DEMONSTRATED_AFTER_FOOTPRINT",
    )
    targets = counter._ranked_visual_targets
    assert targets
    assert all(item.scale != "FIELD" for item in targets)
    assert all(not (set(item.cells) & {(2, 1), (2, 2)}) for item in targets)
    frontier = counter.sweep_frontier()
    assert frontier["ego_binding_source"] == "DEMONSTRATED_AFTER_FOOTPRINT"
    assert frontier["excluded_ego_cells"] == [[2, 1], [2, 2]]


def test_nav_declared_refused_contact_records_lower_strength_result_and_advances():
    from inference.framework.virelai_gates import CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        affordances=action_affordances(["ACTION1", "ACTION2"]),
        initial_grid=GRID,
        observed_through_step=2,
    )
    probe = counter.validate_probe(
        {"pilot_intent": "CONTACT_ATTEMPT"}, [{"action": "ACTION1"}]
    )
    event = counter.record_outcome(probe, {
        "transition_id": 3,
        "action": {"action": "ACTION1"},
        "board_changed": False,
        "changed_cell_count": 0,
        "changed_cells": [],
        "boundary_event": {},
    })
    result = event["navigation_target_result"]
    assert result["disposition"] == "REFUSED_CONTACT_REPORTED"
    assert result["attribution"] == "DUCK_DECLARED_CONTACT_WITH_NO_VISIBLE_DELTA"
    assert counter.next_probe().target["rank"] == 2


def test_nav_capability_binds_target_but_admits_one_duck_selected_pilot_action():
    from inference.framework.cybernetic_targeting import MemoryProduct

    machine = CyberneticGateMachine(
        valid_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION4"],
        initial_grid=GRID,
    )
    machine.submit_answer({
        "answer_id": "G0-nav",
        "action_metadata": [
            {"action": f"ACTION{i}", "requires_coordinates": False}
            for i in range(1, 5)
        ],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EL-test",
        product_type="EgoLaw",
        target_id="G1-EGO",
        revision=1,
        payload={"mode": "EMBODIED_EGO"},
        dependencies=("G0-ACTION-METADATA",),
    ))
    capability = machine.next_probe_capability()
    assert capability["purpose"] == "PILOT_TO_CONTACT"
    assert capability["actions"] == []
    assert capability["admissible_actions"] == [
        "ACTION1", "ACTION2", "ACTION3", "ACTION4"
    ]
    assert capability["target"]["rank"] == 1

    with pytest.raises(GateContractError, match="pilot_intent"):
        machine.validate_probe(
            {"probe_token": capability["probe_token"]},
            [{"action": "ACTION2"}],
        )
    admitted = machine.validate_probe(
        {
            "probe_token": capability["probe_token"],
            "pilot_intent": "APPROACH",
        },
        [{"action": "ACTION2"}],
    )
    assert admitted.actions == ({"action": "ACTION2"},)
    assert admitted.pilot_intent == "APPROACH"


def test_nav_counter_answer_exposes_stored_quiet_action_and_locks_mask_baseline():
    from inference.framework.virelai_gates import CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        affordances=action_affordances(["ACTION1", "ACTION2", "ACTION3", "ACTION4"]),
        initial_grid=GRID,
        observed_through_step=8,
    )

    def outcome(transition, action, before_bar, after_bar, *, extra=(), game_over=False):
        changed = [
            {"row": 0, "col": col, "before": before, "after": after}
            for col, (before, after) in enumerate(zip(before_bar, after_bar, strict=True))
            if before != after
        ]
        changed.extend(extra)
        extras = {(item["row"], item["col"]): item for item in extra}
        sites = []
        for row in range(4):
            for col in range(6):
                before = before_bar[col] if row == 0 and col < 4 else GRID[row][col]
                after = after_bar[col] if row == 0 and col < 4 else GRID[row][col]
                if (row, col) in extras:
                    before = extras[(row, col)]["before"]
                    after = extras[(row, col)]["after"]
                sites.append({
                    "row": row,
                    "col": col,
                    "before": before,
                    "after": after,
                    "outcome": "CHANGED" if before != after else "HELD",
                })
        return {
            "transition_id": transition,
            "shape_before": [4, 6],
            "shape_after": [4, 6],
            "action": {"action": action},
            "acted_site": None,
            "board_changed": bool(changed),
            "changed_cell_count": len(changed),
            "changed_cells": changed,
            "site_transitions": sites,
            "boundary_event": {
                "state": "GAME_OVER" if game_over else "PLAYING",
                "game_over": game_over,
            },
        }

    first = counter.validate_probe(
        {"pilot_intent": "APPROACH"}, [{"action": "ACTION1"}]
    )
    counter.record_outcome(first, outcome(
        9,
        "ACTION1",
        (7, 7, 7, 7),
        (7, 7, 7, 4),
        extra=({"row": 2, "col": 1, "before": 2, "after": 0},),
    ))
    second = counter.validate_probe(
        {"pilot_intent": "APPROACH"}, [{"action": "ACTION3"}]
    )
    counter.record_outcome(second, outcome(
        10, "ACTION3", (7, 7, 7, 4), (7, 7, 4, 4)
    ))

    assert counter.status == "ANSWER_REQUIRED"
    template = counter.answer_template()
    assert template is not None
    assert template["novel_prediction"]["action"] == {"action": "ACTION3"}
    template.update({
        "tracked_variable": "remaining source cells in the top bar",
        "mechanism": "one bar cell rewrites from seven to four after every action",
        "bookkeeping_reason": "the same rewrite recurred under distinct controls away from the ego",
        "competing_models": ["the bar is a causal remote target"],
        "falsifier": "a future isolated action fails to produce the predicted rewrite",
    })
    template["novel_prediction"]["because"] = (
        "two varied witnesses showed the same one-cell bar rewrite"
    )
    template["novel_prediction"]["novelty"] = (
        "the claim is frozen before a later isolated transition"
    )
    counter.submit_answer(template)
    demonstration = counter.next_probe()
    assert demonstration is not None
    assert demonstration.purpose == "DEMONSTRATE"
    assert demonstration.actions == ({"action": "ACTION3"},)
    counter.record_outcome(demonstration, outcome(
        11, "ACTION3", (7, 7, 4, 4), (7, 4, 4, 4)
    ))
    assert counter.status == "CLOSED"
    assert counter.counter_model.status == "LOCKED_AS_MASK_BASELINE"

    event = counter.monitor_later_transition(outcome(
        12, "ACTION3", (7, 4, 4, 4), (4, 4, 4, 4), game_over=True
    ))
    assert event["policy"] == "MASK_AND_IGNORE_AFTER_G2"
    assert counter.status == "CLOSED"
    assert counter.counter_model.status == "LOCKED_AS_MASK_BASELINE"


def test_boundary_confirmation_batches_established_counter_only_action(monkeypatch):
    from inference.framework.virelai_gates import CounterGateMachine, action_affordances

    counter = CounterGateMachine(
        initial_grid=GRID,
        affordances=action_affordances(["ACTION3"]),
        observed_through_step=0,
    )
    counter.status = "BOUNDARY_CONFIRMATION_REQUIRED"
    counter._counter_only_action = {"action": "ACTION3"}
    counter.boundary_obligation = {"source_after": 19}
    monkeypatch.setattr(
        "inference.framework.virelai_gates.COUNTER_BOUNDARY_BATCH_MAX", 8
    )

    probe = counter.next_probe()

    assert probe is not None
    assert probe.purpose == "CONFIRM_BOUNDARY"
    assert probe.actions == tuple({"action": "ACTION3"} for _ in range(8))


def duck_choice(capability):
    """G2 CLICK is a stated target: Duck picks the action. Stand-in: next untried object."""
    if capability["actions"]:
        return capability["actions"]
    row, col = capability["target"]["untried_object_anchors"][0]
    return [{"action": "ACTION6", "row": row, "col": col}]


def execute_counter_probe(machine, step, changed_cell, *, game_over=False):
    capability = machine.next_probe_capability()
    actions = duck_choice(capability)
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, actions)
    action = actions[0]
    before_bar = {
        1: (7, 7, 7, 7),
        2: (7, 7, 4, 7),
        3: (7, 7, 4, 4),
        4: (7, 4, 4, 4),
    }[step]
    after_bar = tuple(
        4 if col == changed_cell[1] else value
        for col, value in enumerate(before_bar)
    )
    outcome = {
        "transition_id": step,
        "shape_before": [4, 6],
        "shape_after": [4, 6],
        "action": action,
        "acted_site": {"row": action["row"], "col": action["col"]},
        "board_changed": True,
        "changed_cell_count": 1,
        "changed_cells": [
            {"row": changed_cell[0], "col": changed_cell[1], "before": 7, "after": 4}
        ],
        "site_transitions": [
            {
                "row": row,
                "col": col,
                "before": (
                    before_bar[col] if row == 0 and col < 4 else GRID[row][col]
                ),
                "after": (
                    after_bar[col] if row == 0 and col < 4 else GRID[row][col]
                ),
                "outcome": (
                    "CHANGED" if row == 0 and col == changed_cell[1] else "HELD"
                ),
            }
            for row in range(4)
            for col in range(6)
        ],
        "boundary_event": {"state": "GAME_OVER" if game_over else "PLAYING", "game_over": game_over},
    }
    return machine.record_outcome(probe, outcome)


def later_counter_outcome(step, changed_cell, *, game_over=False):
    before_bar = {
        1: (7, 7, 7, 7),
        2: (7, 7, 4, 7),
        3: (7, 7, 4, 4),
        4: (7, 4, 4, 4),
    }[step]
    after_bar = tuple(
        4 if col == changed_cell[1] else value
        for col, value in enumerate(before_bar)
    )
    return {
        "transition_id": step,
        "shape_before": [4, 6],
        "shape_after": [4, 6],
        "action": {"action": "ACTION6", "row": 2, "col": 4},
        "acted_site": {"row": 2, "col": 4},
        "board_changed": True,
        "changed_cell_count": 1,
        "changed_cells": [
            {"row": changed_cell[0], "col": changed_cell[1], "before": 7, "after": 4}
        ],
        "site_transitions": [
            {
                "row": row,
                "col": col,
                "before": before_bar[col] if row == 0 and col < 4 else GRID[row][col],
                "after": after_bar[col] if row == 0 and col < 4 else GRID[row][col],
                "outcome": "CHANGED" if row == 0 and col == changed_cell[1] else "HELD",
            }
            for row in range(4)
            for col in range(6)
        ],
        "boundary_event": {
            "state": "GAME_OVER" if game_over else "PLAYING",
            "game_over": game_over,
        },
    }


def test_g2_routes_after_g1_and_stops_for_explanation_then_demonstration():
    machine = g2_machine()
    assert machine.gate_view()["next_operation"] == "QUERY_NEXT_PROBE"

    execute_counter_probe(machine, 1, (0, 2))
    execute_counter_probe(machine, 2, (0, 3))

    view = machine.gate_view()
    assert view["status"] == "ANSWER_REQUIRED"
    assert view["stop_reason"] == "RECURRENT_REMOTE_REWRITE_OBSERVED"
    assert view["candidate"]["status"] == "SCHEDULED_BOOKKEEPING_CANDIDATE"
    assert view["next_operation"] == "SUBMIT_GATE_ANSWER"
    candidate = machine.counter.candidate
    assert candidate is not None

    machine.submit_answer({
        "answer_id": "G2-top-strip",
        "candidate_id": candidate.candidate_id,
        "trigger": "EVERY_TRANSITION",  # axiom A1 v2: the bar ticks on every transition here
        "tracked_variable": "remaining visible units in the top strip",
        "mechanism": "one top-strip cell rewrites from integer seven to integer four per intervention",
        "bookkeeping_reason": "the rewrite recurs away from distinct selected sites under every tested intervention",
        "conditions": ["fixed geometry in the current level"],
        "evidence_refs": list(candidate.witness_evidence_refs),
        "competing_models": ["the strip is a remote lever target"],
        "falsifier": "the next intervention leaves the strip unchanged or reverses it",
        "limitations": ["the terminal meaning of zero remaining units is unknown"],
        "novel_prediction": view["answer_template"]["novel_prediction"],
    })
    assert machine.gate_view()["status"] == "DEMONSTRATION_REQUIRED"

    demonstration = execute_counter_probe(machine, 3, (0, 1))
    assert demonstration["counter_comparison"]["outcome"] == "SUPPORTED"
    assert machine.gate_id == "G3-LEVERS"
    assert machine.assessment().disposition == "ACTIVE"
    assert machine.counter.counter_model.tracked_variable.startswith("remaining visible")
    assert machine.counter.counter_model.status == "LOCKED_AS_MASK_BASELINE"
    assert machine.counter.boundary_obligation is None
    assert set(machine.counter.mask_law.cells) == {(0, 0), (0, 1), (0, 2), (0, 3)}
    frontier = machine.counter.sweep_frontier()
    assert frontier["observed_count"] == 2
    assert [row["status"] for row in frontier["candidates"]] == [
        "OBSERVED", "OBSERVED", "UNTRIED", "UNTRIED"
    ]
    provisional = machine.target_journal.active_product("G2-COUNTER")
    assert provisional is not None
    assert provisional.payload["boundary_obligation"] is None

    boundary = machine.monitor_counter_transition(
        later_counter_outcome(4, (0, 0), game_over=True)
    )
    assert boundary["policy"] == "MASK_AND_IGNORE_AFTER_G2"
    assert machine.counter.counter_model.status == "LOCKED_AS_MASK_BASELINE"
    assert machine.counter.boundary_obligation is None
    refreshed = machine.target_journal.active_product("G2-COUNTER")
    assert refreshed is not None
    assert refreshed.product_type == "CounterGateProduct"
    assert refreshed.payload["product_kind"] == "COUNTER_MODEL_AND_MASK"
    assert refreshed.payload["ranked_object_frontier"] == frontier
    assert refreshed.payload["state_identity"]["raw_state_count"] > 1
    assert refreshed.payload["state_identity"]["hud_only_transition_count"] >= 1
    assert refreshed.payload["counter_model"]["status"] == "LOCKED_AS_MASK_BASELINE"
    assert refreshed.payload["boundary_obligation"] is None
    assert refreshed.payload["derived_period_actions"] == 4
    assert machine.gate_id == "G3-LEVERS"
    g3 = machine.gate_view()
    assert g3["status"] == "ACTIVE"
    # Axiom A6 (2026-09-28): the card carries the source frontier's summary; its candidate rows
    # stay in the lossless snapshot.
    assert g3["source_frontier"] == {
        **{key: value for key, value in frontier.items() if key != "candidates"},
        "candidates_omitted": len(frontier["candidates"]),
    }
    assert machine._adapters["G3-LEVERS"].snapshot()["source_frontier"] == frontier
    assert g3["inherited_frontier"]["schema"] == "virelai-g3-mask-filtered-frontier-v1"
    assert g3["inherited_frontier"]["original_candidate_count"] == frontier["candidate_count"]
    assert g3["inherited_frontier"]["accounting_complete"] is True
    assert g3["inherited_frontier"]["excluded_candidate_count"] == 1
    assert g3["counter_period_actions"] == 4
    assert g3["attribution_contract"]["channels"] == ["BODY", "POINTER"]
    assert g3["attribution_contract"]["null_policy"] == (
        "SCOPED_NULL_RESPONSE_NEVER_PROVES_INERTNESS"
    )
    assert g3["next_operation"] == "QUERY_NEXT_G3_TARGET"


def test_g2_rejects_label_only_or_mismatched_evidence_explanation():
    machine = g2_machine()
    execute_counter_probe(machine, 1, (0, 2))
    execute_counter_probe(machine, 2, (0, 3))
    candidate = machine.counter.candidate
    assert candidate is not None
    try:
        machine.submit_answer({
            "answer_id": "bad",
            "candidate_id": candidate.candidate_id,
            "trigger": "EVERY_TRANSITION",  # axiom A1 v2: the bar ticks on every transition here
            "tracked_variable": "a counter",
            "mechanism": "it is just a counter",
            "bookkeeping_reason": "it looks like a timer",
            "evidence_refs": ["invented"],
            "competing_models": ["lever"],
            "falsifier": "it stops",
        })
    except GateContractError:
        pass
    else:
        raise AssertionError("label-only G2 answer was accepted")


def test_exhaustive_zero_delta_opening_closes_with_scoped_not_observed_product():
    machine = g2_machine()
    transition_id = 0
    while machine.counter.status == "ACTIVE":
        transition_id += 1
        capability = machine.next_probe_capability()
        actions = duck_choice(capability)
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, actions)
        machine.record_outcome(probe, {
            "transition_id": transition_id,
            "shape_before": [4, 6],
            "shape_after": [4, 6],
            "action": actions[0],
            "acted_site": {"row": actions[0]["row"], "col": actions[0]["col"]},
            "board_changed": False,
            "changed_cell_count": 0,
            "changed_cells": [],
            "boundary_event": {"state": "PLAYING"},
        })
    assert machine.counter.status == "CLOSED"
    assert machine.counter.stop_reason == "COUNTER_NOT_OBSERVED_WITHIN_OPENING"
    disposition = machine.counter.search_disposition
    assert disposition["scope"] == "BOUNDED_RANKED_OPENING_ONLY"
    assert disposition["reason"] == "NO_RECURRENT_PROCESS_AFTER_FULL_CLICK_COVERAGE"
    assert disposition["probe_count"] == len(machine.counter._ranked_visual_targets)
    assert "absence" in disposition["epistemic_limit"].lower()
    product = machine.target_journal.active_product("G2-COUNTER")
    assert product is not None
    assert product.product_type == "CounterGateProduct"
    assert product.payload["product_kind"] == "COUNTER_NOT_OBSERVED"
    assert product.payload["counter_model"] is None
    assert machine.gate_id == "G3-LEVERS"
    assert machine.gate_view()["next_operation"] == "QUERY_NEXT_G3_TARGET"


def test_g2_contradiction_reopens_probe_hunt_without_mask():
    machine = g2_machine()
    execute_counter_probe(machine, 1, (0, 2))
    execute_counter_probe(machine, 2, (0, 3))
    candidate = machine.counter.candidate
    template = machine.gate_view()["answer_template"]
    machine.submit_answer({
        "answer_id": "G2-proposed",
        "candidate_id": candidate.candidate_id,
        "trigger": "EVERY_TRANSITION",  # axiom A1 v2: the bar ticks on every transition here
        "tracked_variable": "remaining visible units in the top strip",
        "mechanism": "one top-strip cell rewrites from integer seven to integer four per intervention",
        "bookkeeping_reason": "the rewrite recurs away from distinct selected sites under every tested intervention",
        "conditions": [],
        "evidence_refs": list(candidate.witness_evidence_refs),
        "competing_models": ["the strip is a remote lever target"],
        "falsifier": "the next intervention does not repeat exactly one matching rewrite",
        "limitations": [],
        "novel_prediction": template["novel_prediction"],
    })
    capability = machine.next_probe_capability()
    actions = duck_choice(capability)
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, actions)
    action = actions[0]
    event = machine.record_outcome(probe, {
        "transition_id": 3,
        "shape_before": [4, 6],
        "shape_after": [4, 6],
        "action": action,
        "acted_site": {"row": action["row"], "col": action["col"]},
        "board_changed": False,
        "changed_cell_count": 0,
        "changed_cells": [],
    })
    assert event["counter_comparison"]["outcome"] == "CONTRADICTED"
    assert machine.counter.mask_law is None
    assert machine.counter.status == "ACTIVE"
