from __future__ import annotations

import pytest

from inference.framework.virelai_world_model import (
    Claim,
    EvidenceRef,
    WORLD_MODEL_SCHEMA,
    WorldModel,
    canonical_bytes,
    empty_world_model,
    from_semantic_library_metadata,
    from_semantic_library,
    model_sha256,
    query_world_model,
    transition_briefing,
    with_level_lessons,
    with_clock_patterns,
)


def test_empty_model_serialization_is_byte_deterministic():
    first = empty_world_model(
        game_id="vc33-fixture",
        observed_through_step=26,
        levels_observed=[2, 1, 1],
        current_level=2,
        source_schema="fixture-v1",
    )
    second = empty_world_model(
        game_id="vc33-fixture",
        observed_through_step=26,
        levels_observed=[1, 2],
        current_level=2,
        source_schema="fixture-v1",
    )
    assert canonical_bytes(first) == canonical_bytes(second)
    assert model_sha256(first) == model_sha256(second)


def test_observed_claim_requires_real_evidence():
    model = WorldModel(
        schema=WORLD_MODEL_SCHEMA,
        game_id="fixture",
        model_version=1,
        observed_through_step=1,
        levels_observed=(1,),
        current_level=1,
        world_mode="UNKNOWN",
        claims=(
            Claim(
                claim_id="C1",
                predicate="Lever A changes Resource R",
                status="OBSERVED",
                scope="L1",
                witness_count=0,
            ),
        ),
    )
    with pytest.raises(ValueError, match="lacks a witness"):
        canonical_bytes(model)


def test_observed_claim_with_evidence_is_valid():
    evidence = EvidenceRef(
        transition_id=4,
        level=1,
        step=4,
        observation="ACTION6 rewrote the cells of region R",
    )
    model = WorldModel(
        schema=WORLD_MODEL_SCHEMA,
        game_id="fixture",
        model_version=1,
        observed_through_step=4,
        levels_observed=(1,),
        current_level=1,
        world_mode="POINTER",
        claims=(
            Claim(
                claim_id="C1",
                predicate="ACTION6 visibly changed region R",
                status="OBSERVED",
                scope="L1",
                witness_count=1,
                evidence=(evidence,),
            ),
        ),
    )
    assert b'"status":"OBSERVED"' in canonical_bytes(model)


def test_clock_pattern_becomes_scoped_visible_process_not_hidden_timer():
    model = empty_world_model(
        game_id="fixture",
        observed_through_step=9,
        levels_observed=[1],
        current_level=1,
        source_schema="fixture-v1",
    )
    enriched = with_clock_patterns(model, [{
        "level": 1,
        "tracked_classes": [{
            "class_id": 7, "current_standing": 3, "direction": "decreasing",
        }],
        "witness_steps": list(range(2, 10)),
        "rate": {"min": -1, "median": -1, "max": -1, "recent": [-1] * 8},
        "process_kind": "monotone_visible_consumption",
        "terminal_extent_observed": False,
        "caveat": "Not a proven timer or objective.",
    }])

    assert len(enriched.mechanics) == 1
    rule = enriched.mechanics[0]
    assert rule.trigger_action == "ANY_OBSERVED_DUCK_ACTION"
    assert rule.transformation == "monotone_visible_consumption"
    assert rule.witness_transition_ids == tuple(range(2, 10))
    assert rule.endpoint_behavior == "TERMINAL_EXTENT_UNOBSERVED"
    assert "timer" not in enriched.claims[0].predicate.lower()
    canonical_bytes(enriched)


def test_metadata_adapter_admits_no_unvalidated_semantics():
    model = from_semantic_library_metadata(
        {
            "schema": "semantic-fixture-v1",
            "game_id": "vc33-fixture",
            "observed_transitions": 26,
            "levels_observed": [1, 2],
            "segments": [{"role_typed_order": "COUNTER"}],
        }
    )
    assert model.levels_observed == (1, 2)
    assert model.current_level == 2
    assert model.claims == ()
    assert model.mechanics == ()
    assert model.world_mode == "UNKNOWN"


def test_worldline_adapter_creates_stable_objects_without_roles():
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 2,
        "levels_observed": [1],
        "segments": [
            {
                "segment": "L1-F1-S1",
                "level": 1,
                "entities": [
                    {
                        "handle": "L1-O1",
                        "worldline_id": 7,
                        "born_node": 0,
                        "last_seen_node": 2,
                        "current": {
                            "integer_class": 4,
                            "cells": 4,
                            "bbox": [3, 5, 4, 6],
                        },
                        "roles": [],
                    }
                ],
            }
        ],
    }
    model = from_semantic_library(payload)
    assert len(model.objects) == 1
    assert len(model.object_types) == 1
    assert model.objects[0].worldline_ids == ("7",)
    assert model.object_types[0].roles == ()
    assert model.claims == ()


def test_unvalidated_source_role_is_admitted_only_as_candidate():
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 1,
        "levels_observed": [1],
        "segments": [
            {
                "segment": "L1-F1-S1",
                "level": 1,
                "entities": [
                    {
                        "handle": "L1-O1",
                        "worldline_id": 1,
                        "born_node": 0,
                        "last_seen_node": 1,
                        "current": {
                            "integer_class": 4,
                            "cells": 4,
                            "bbox": [1, 1, 2, 2],
                        },
                        "roles": [
                            {
                                "role": "LEVER",
                                "status": "DETECTOR_VERDICT",
                                "witness_count": 1,
                                "witnesses": [
                                    {"left_node": 0, "right_node": 1, "action_id": 6}
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    model = from_semantic_library(payload)
    assert model.claims[0].status == "CANDIDATE"
    assert model.claims[0].witness_count == 1
    assert model.objects[0].claim_ids == (model.claims[0].claim_id,)


def test_witnessed_effect_channel_is_observed_without_claiming_causation():
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 2,
        "levels_observed": [1],
        "segments": [
            {
                "segment": "L1-F1-S1",
                "level": 1,
                "lever_mechanics": {
                    "levers": [
                        {
                            "lever": "SOURCE-01",
                            "evidence": [
                                {
                                    "left_node": 1,
                                    "right_node": 2,
                                    "action_id": 6,
                                }
                            ],
                            "effect_channels": [
                                {
                                    "channel": "EFFECT-01",
                                    "observations": 1,
                                    "direction": "DECREASES_CELL_COUNT",
                                    "affected_bbox": [0, 0, 0, 3],
                                    "integer_class_before": 4,
                                    "cell_count_deltas": [-1],
                                    "target_worldlines": ["WL-9"],
                                    "transitions": [
                                        {
                                            "left_node": 1,
                                            "right_node": 2,
                                            "before": [4, 4, [0, 0]],
                                            "after": [4, 3, [0, 0]],
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                },
            }
        ],
    }
    model = from_semantic_library(payload)
    assert len(model.mechanics) == 1
    assert len(model.state_variables) == 1
    assert model.mechanics[0].trigger_action == "ACTION6"
    assert model.mechanics[0].magnitude == "-1"
    assert model.mechanics[0].subject_ids == ("SOURCE-01",)
    assert model.mechanics[0].affected_region == (0, 0, 0, 3)
    assert model.mechanics[0].witness_transition_ids == (2,)
    assert model.mechanics[0].scope == "L1"
    assert model.mechanics[0].status == "OBSERVED"
    claim = next(item for item in model.claims if item.status == "OBSERVED")
    assert claim.witness_count == 1
    assert "causation remain unproven" in claim.limitations[0]


def test_reactive_control_and_shared_control_are_not_dropped():
    transition = {
        "left_node": 1,
        "right_node": 2,
        "before": [3, 4, [0, 0]],
        "after": [4, 4, [0, 0]],
    }
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 3,
        "levels_observed": [1],
        "segments": [{
            "segment": "L1-F1-S1",
            "level": 1,
            "lever_mechanics": {
                "reactive_controls": [{
                    "control": "CONTROL-A",
                    "kind": "SELF_REACTIVE_CONTROL",
                    "evidence": [{"left_node": 1, "right_node": 2, "action_id": 6}],
                    "self_effect_channels": [{
                        "channel": "SELF-01",
                        "observations": 2,
                        "direction": "CLASS_REWRITE_WITHOUT_SIZE_CHANGE",
                        "affected_bbox": [0, 0, 0, 3],
                        "target_worldlines": ["CONTROL-A"],
                        "typing": {
                            "mechanism": "UNIFORM_TRANSFORM",
                            "status": "OBSERVED_REPEATEDLY",
                            "condition": "UNMEASURED",
                        },
                        "transitions": [transition, {**transition, "left_node": 2, "right_node": 3}],
                    }],
                }],
                "shared_controls": [{
                    "lever_a": "CONTROL-A",
                    "lever_b": "CONTROL-B",
                    "affected_targets": [{
                        "target": "RESOURCE-X",
                        "lever_a_deltas": [1, 1],
                        "lever_b_deltas": [-1, -1],
                    }],
                    "interpretation_limit": "Shared hidden state is not proven.",
                }],
            },
        }],
    }

    model = from_semantic_library(payload)
    transformations = {rule.transformation for rule in model.mechanics}
    assert "UNIFORM_TRANSFORM" in transformations
    assert "OPPOSED_DIRECTION_CONTROL_BUNDLE" in transformations
    shared = next(
        rule for rule in model.mechanics
        if rule.transformation == "OPPOSED_DIRECTION_CONTROL_BUNDLE"
    )
    assert shared.subject_ids == ("CONTROL-A", "CONTROL-B")
    assert shared.affected_ids == ("RESOURCE-X",)
    assert shared.status == "CANDIDATE"


def test_unwitnessed_effect_channel_is_not_admitted():
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 1,
        "levels_observed": [1],
        "segments": [
            {
                "segment": "L1-F1-S1",
                "level": 1,
                "lever_mechanics": {
                    "levers": [
                        {
                            "lever": "SOURCE-01",
                            "effect_channels": [
                                {"channel": "EFFECT-01", "observations": 2, "transitions": []}
                            ],
                        }
                    ]
                },
            }
        ],
    }
    model = from_semantic_library(payload)
    assert model.mechanics == ()
    assert model.state_variables == ()


def test_win_diff_queries_and_briefing_share_the_canonical_model():
    payload = {
        "schema": "semantic-fixture-v1",
        "game_id": "fixture",
        "observed_transitions": 4,
        "levels_observed": [1, 2],
        "segments": [
            {"segment": "L1", "level": 1, "entities": [{
                "handle": "L1-O1", "worldline_id": 1, "born_node": 0,
                "last_seen_node": 2,
                "current": {"integer_class": 4, "cells": 4, "bbox": [1, 1, 2, 2]},
            }]},
            {"segment": "L2", "level": 2, "entities": [{
                "handle": "L2-O1", "worldline_id": 2, "born_node": 3,
                "last_seen_node": 4,
                "current": {"integer_class": 4, "cells": 4, "bbox": [5, 5, 6, 6]},
            }]},
        ],
    }
    model = with_level_lessons(from_semantic_library(payload), [{
        "completed_level": 1,
        "compiled_at_transition": 3,
        "boundary": {"winning_action": "ACTION6"},
        "established": [{"fact": "OBSERVED_WINNING_ACTION"}],
        "contrasts": [{"attempts": 2}],
        "hypotheses": [{"claim": "WIN_REQUIRED_CONTEXT", "status": "SUPPORTED"}],
    }])
    assert model.wins[0].causal_status == "UNKNOWN"
    assert model.level_diffs[0].still_present
    assert query_world_model(model, "diff")["ok"]
    assert query_world_model(model, "object", "L2-O1")["ok"]
    briefing = transition_briefing(model, 2)
    assert "earlier identical-action failures: 2" in briefing
    assert "Cause remains UNKNOWN" in briefing
