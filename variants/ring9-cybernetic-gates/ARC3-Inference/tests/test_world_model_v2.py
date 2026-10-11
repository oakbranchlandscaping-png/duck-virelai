"""WO-L2a: the v2 world-model contract (schema, canonical bytes, the version-aware reader, the one writer).

Author: Claude (Alpha build seat), 2026-10-10. Sol's reviews of WO-L2-00 and of the WO-L2a interface.
"""
from __future__ import annotations

import copy
import json
from dataclasses import asdict

import pytest

from inference.framework.virelai_world_model import canonical_bytes as v1_bytes
from inference.framework.virelai_world_model import empty_world_model
from inference.framework.world_model_v2 import (
    SCHEMA, WorldModelV2Error, canonical_bytes, read_world_model, seal, validate, write_canonical,
)


def _model() -> dict:
    """The smallest valid model: one level, one track at the entry board, one witnessed lever."""
    return {
        "game_id": "g", "run_stem": "g_p0",
        "manifest": {"status": "ACTIVE", "persist_reason": "BUDGET_STOP"},
        "levels": [{
            "level": 1, "state": "OPEN",
            "entry": {"source": "INITIAL_FRAME"},
            "record": {"transition_ids": [1]},
            "observation": {"tracks": [{
                "track_id": "O-L1-P1-E-x",
                "segments": [{"first": {"source": "INITIAL_FRAME"}, "last": {"source": "TRANSITION", "transition_id": 1},
                              "count": 2, "class_id": 3, "shape_hash": "h", "anchor": [0, 0], "bbox": [0, 0, 0, 0],
                              "cell_count": 1}],
                "band1": {"status": "UNSETTLED"},
                "g3_join": {"status": "EXACT_ONE_TO_ONE", "entity_id": "E0001", "basis": {"key": "k"}},
            }]},
            "certified": {
                "roles": [{"role": "LEVER", "gate_id": "G3-LEVERS", "entity_id": "E0001", "witness_refs": ["W-1"],
                           "evidence_refs": ["E-1"], "inventory_status": "PENDING",
                           "identity": {"status": "EXACT_ONE_TO_ONE", "track_id": "O-L1-P1-E-x", "basis": {"key": "k"}}}],
                "scoped_nulls": [{"entity_id": "E0002", "evidence_ref": "E-2", "inertness_claim_permitted": False}],
            },
            "receipts": {
                "evidence": {"E-1": {"transition_id": 1, "gate_id": "G3-LEVERS", "probe_id": "G3-LEVERS:CLICK:1"}},
                "products": {"L-1": {"gate_id": "G1-EGO", "product_type": "EgoLaw", "revision": 1, "payload_sha256": "0" * 64}},
                "witnesses": {"W-1": {"entity_id": "E0001", "member_id": "M0001", "evidence_ref": "E-1",
                                      "transition_id": 1, "channel": "CLICK"}},
            },
            "gaps": [{"subject": "LEVEL-1", "archetype_question": "Is anything INERT?", "reason": "NOT_BUILT"},
                     {"subject": "E0003", "archetype_question": "Is this object a lever?", "reason": "INCONCLUSIVE"}],
            "accounting": {"status": "ACCOUNTED", "missing": []},
        }],
    }


def _level(model):
    return model["levels"][0]


def test_a_valid_model_seals_with_a_stable_hash():
    first, second = seal(_model()), seal(_model())
    assert first["schema"] == SCHEMA and first["content_sha256"] == second["content_sha256"]
    assert canonical_bytes(first) == canonical_bytes(second)
    tampered = copy.deepcopy(first)
    _level(tampered)["gaps"][0]["reason"] = "BUDGET"
    with pytest.raises(WorldModelV2Error, match="content_sha256"):
        validate(tampered)


def _refused(edit, message):
    model = _model()
    edit(model)
    with pytest.raises(WorldModelV2Error, match=message):
        seal(model)


def test_the_entry_board_is_never_a_transition():
    _refused(lambda m: _level(m)["entry"].update(transition_id=0), "not a transition")
    _refused(lambda m: _level(m)["record"]["transition_ids"].append(0), "transition 0 is not a receipt")
    _refused(lambda m: _level(m)["observation"]["tracks"][0]["segments"][0]["first"].update(transition_id=0),
             "entry sighting is not a transition")
    _refused(lambda m: _level(m)["entry"].update(source="LEVEL_ENTRY"), "cites the transition that ended")


def test_a_sighting_must_cite_a_recorded_transition():
    _refused(lambda m: _level(m)["observation"]["tracks"][0]["segments"][0]["last"].update(transition_id=9),
             "cites a recorded transition")


def test_only_gates_certify_and_never_inert():
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(role="INERT"), "cannot be certified")
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(gate_id="G4-REACTIONS"), "certified only by G3-LEVERS")
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(witness_refs=[]), "cites its G3 witness")
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(inventory_status="LATER"), "inventory status")
    _refused(lambda m: _level(m)["certified"]["scoped_nulls"][0].update(inertness_claim_permitted=True),
             "never claims inertness")
    _refused(lambda m: _level(m)["observation"]["tracks"][0].update(roles=["LEVER"]), "carries no role")


def test_a_role_reference_must_resolve_to_a_receipt():
    """Validation checks each certificate against the artifact's receipt index, not only its shape."""
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(witness_refs=["W-FABRICATED"]),
             "resolves to no witness receipt")
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(entity_id="E0009"), "belongs to E0001, not E0009")
    _refused(lambda m: _level(m)["certified"]["roles"][0].update(evidence_refs=["E-FABRICATED"]),
             "which no receipt resolves")

    def ego(product_id):
        def edit(model):
            _level(model)["certified"]["roles"][0].update(
                role="EGO", gate_id="G1-EGO", product_id=product_id, binding_source="POINTER_EGO_HAS_NO_GRID_FOOTPRINT",
                identity={"status": "NOT_APPLICABLE", "track_id": None, "basis": None})
        return edit
    seal(_apply(_model(), ego("L-1")))  # a resolvable product passes
    _refused(ego("L-FABRICATED"), "resolves to no product receipt")

    def counter(model):
        _level(model)["certified"]["roles"][0].update(
            role="COUNTER", gate_id="G2-COUNTER", product_id="L-1",
            identity={"status": "UNRESOLVED", "track_id": None, "basis": None})
    _refused(counter, "belongs to G1-EGO, not G2-COUNTER")


def test_every_receipt_sits_on_a_recorded_transition():
    _refused(lambda m: _level(m)["receipts"]["evidence"]["E-1"].update(transition_id=7), "not a recorded transition")
    _refused(lambda m: _level(m)["receipts"]["witnesses"]["W-1"].update(evidence_ref="E-9"), "cites no recorded evidence")
    _refused(lambda m: _level(m)["receipts"]["witnesses"]["W-1"].update(transition_id=2), "disagrees with its evidence")
    _refused(lambda m: _level(m).pop("receipts"), "receipt index")


def _apply(model, edit):
    edit(model)
    return model


def test_a_duck_declared_footprint_never_becomes_an_identity():
    def edit(model):
        _level(model)["certified"]["roles"][0].update(
            role="EGO", gate_id="G1-EGO", product_id="L-1", binding_source="DUCK_DECLARED_SCOPE_FALLBACK")
    _refused(edit, "a hint, never an identity")


def test_gaps_are_typed_and_a_mismatch_is_never_accounted():
    assert {gap["reason"] for gap in _level(seal(_model()))["gaps"]} == {"NOT_BUILT", "INCONCLUSIVE"}
    _refused(lambda m: _level(m)["gaps"][0].update(reason="UNKNOWN"), "unknown gap reason")
    _refused(lambda m: _level(m)["gaps"].append(
        {"subject": "LEVEL-1", "archetype_question": "q", "reason": "RECORD_MISMATCH"}), "never ACCOUNTED")
    _refused(lambda m: _level(m)["accounting"].update(missing=["X"]), "lists nothing missing")


def test_joins_and_band1_stay_honest():
    _refused(lambda m: _level(m)["observation"]["tracks"][0]["g3_join"].update(status="UNRESOLVED"),
             "only an exact one-to-one join names")
    _refused(lambda m: _level(m)["observation"]["tracks"][0].update(band1={"status": "STATIC"}), "UNSETTLED")
    _refused(lambda m: _level(m)["certified"]["roles"][0]["identity"].update(track_id="O-unknown"), "known track")


def test_the_reader_is_version_aware():
    v1 = json.loads(v1_bytes(empty_world_model(game_id="g", observed_through_step=0, levels_observed=(1,), current_level=1, source_schema="fixture")))
    assert asdict(read_world_model(v1))["schema"] == "virelai-world-model-v1"
    assert read_world_model(seal(_model()))["schema"] == SCHEMA
    with pytest.raises(WorldModelV2Error, match="unknown world model schema"):
        read_world_model({"schema": "virelai-world-model-v9"})


def test_the_writer_is_atomic_and_reports_failure(tmp_path):
    result = write_canonical(_model(), tmp_path / "run")
    assert result.ok and (tmp_path / "run" / "world_model.json").read_bytes() == canonical_bytes(seal(_model()))
    blocked = tmp_path / "file"
    blocked.write_text("not a directory")
    failed = write_canonical(_model(), blocked)
    assert not failed.ok and failed.sha256 is None and "Error" in failed.error
    invalid = _model()
    invalid["levels"][0]["entry"]["transition_id"] = 0
    refused = write_canonical(invalid, tmp_path / "run")
    assert not refused.ok and "not a transition" in refused.error
    assert (tmp_path / "run" / "world_model.json").read_bytes() == canonical_bytes(seal(_model()))  # untouched
    assert not list((tmp_path / "run").glob(".*.tmp"))


def test_each_write_uses_its_own_temporary_sibling(tmp_path, monkeypatch):
    import os

    stray = tmp_path / ".world_model.json.tmp"  # a fixed-name leftover must be neither used nor clobbered
    stray.write_text("someone else's")
    sources = []
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda src, dst: (sources.append(str(src)), real(src, dst))[1])
    assert write_canonical(_model(), tmp_path).ok and write_canonical(_model(), tmp_path).ok
    assert len(set(sources)) == 2 and all(os.path.dirname(src) == str(tmp_path) for src in sources)
    assert stray.read_text() == "someone else's"
    assert sorted(path.name for path in tmp_path.iterdir()) == [".world_model.json.tmp", "world_model.json"]
