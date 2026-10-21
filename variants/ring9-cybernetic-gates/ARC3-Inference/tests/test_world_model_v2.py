"""WO-L2a: the v2 world-model contract (schema, canonical bytes, the version-aware reader, the one writer).

Author: Claude (Alpha build seat), 2026-10-10. Sol's reviews of WO-L2-00 and of the WO-L2a interface.
"""
from __future__ import annotations

import copy
import json
from dataclasses import asdict

import pytest

from inference.framework.descriptive_events import event_id, witness_sha256
from inference.framework.virelai_world_model import canonical_bytes as v1_bytes
from inference.framework.virelai_world_model import empty_world_model
from inference.framework.world_model_v2 import (
    SCHEMA, WorldModelV2Error, canonical_bytes, read_world_model, seal, validate, write_canonical,
)


TRACK = "O-L1-P1-E-x"


def _witness() -> dict:
    receipt = {"entity_id": "E0001", "member_id": "M0001", "evidence_ref": "E-1", "transition_id": 1, "channel": "CLICK",
               "residue": {"local_runs": [[0, 0, 0]], "remote_runs": [], "cell_count": 1}}
    return {**receipt, "witness_sha256": witness_sha256("W-1", receipt)}  # schema v3 receipts carry residue and hash


def _description(lever: bool = True) -> dict:
    """Schema v3 (WO-DESC-A): this level's description. The one track is still at transition 1; a track bound to a
    certified role has its STILL emitted, any other is only counted."""
    roles = [{"role": "LEVER", "gate_id": "G3-LEVERS", "role_ref": "E0001"}] if lever else []
    shape = {"class": 3, "anchor": [0, 0], "bbox": [0, 0, 0, 0], "cell_count": 1, "shape_hash": "h"}
    still = {"event_id": event_id(1, 1, TRACK, "STILL"), "transition_id": 1, "level": 1, "life": 1,
             "subject": {"track_id": TRACK, "roles": roles}, "verb": "STILL", "before": shape, "after": shape,
             "delta": {"footprint": {"membership_groups": {"retained_rewritten": [], "prior_footprint_only": [],
                                                           "later_footprint_only": []}, "retained_same_value_cells": 1}},
             "correspondence": {"source": "SITE", "witness": "golden_cascade", "ambiguity": None},
             "flags": {"recolor": False, "returns_to_prior_state": False, "reopens_role_typing": False,
                       "role_binding_ends": False},
             "status": "OBSERVED", "explanation": {"status": "UNEXPLAINED", "refs": [], "basis": "NO_CHANGE"}}
    return {
        "schema": "virelai-description-v1",
        "basis": {"continuity": "virelai-golden-weave-v1:weave_window+re_join", "entry_node": 0,
                  "windows": [{"life": 1, "from_node": 0, "to_node": 1}]},
        "integrity": "VERIFIED", "first_mismatch": None,
        "transitions": [{"transition_id": 1, "level": 1, "life": 1, "kind": "PROBE", "action": {"action": "ACTION6"},
                         "actor": "G3-LEVERS", "evidence_ref": "E-1",
                         "pixel_rewrite": {"coverage_status": "TOTAL", "changed": [], "held_cells": 1,
                                           "signed_class_delta": []},
                         "still_total": 1, "still_emitted": int(lever), "still_omitted": int(not lever),
                         "events": [still] if lever else [], "boundary": None, "record_status": "VERIFIED"}],
        "presence": {TRACK: [[0, 1]]},
        "role_bindings": [{**role, "track_id": TRACK, "ends_at_transition": None} for role in roles],
        "scene": {"as_of_transition": 1, "as_of_node": 1, "life": 1, "record_mismatch": None,
                  "present": [{"track_id": TRACK, "class": 3, "anchor": [0, 0], "bbox": [0, 0, 0, 0], "cell_count": 1,
                               "roles": roles or "UNRESOLVED_OBJECT"}],
                  "departed": [], "unverified_tracks": [], "verb_counts": {"STILL": 1} if lever else {},
                  "unexplained": [], "open_identity": []},
    }


def _product_content(product_id: str) -> tuple[dict, str]:
    """Schema v5: a product's stored body and the legacy receipt hash it must agree with (WO-PE-03A)."""
    from types import SimpleNamespace

    from inference.framework import product_content

    product = SimpleNamespace(product_id=product_id, product_type="EgoLaw", revision=1, dependencies=(),
                              payload={"law_id": product_id})
    return product_content.entry("G1-EGO", product), product_content.legacy_payload_sha256(product.payload)


def _model() -> dict:
    """The smallest valid model: one level, one track at the entry board, one witnessed lever."""
    return _with_dossiers({
        "game_id": "g", "run_stem": "g_p0",
        "manifest": {"status": "ACTIVE", "persist_reason": "BUDGET_STOP"},
        "levels": [{
            "level": 1, "state": "OPEN",
            "entry": {"source": "INITIAL_FRAME"},
            "record": {"transition_ids": [1], "journal_check": {
                "status": "CHECKED", "ok": True, "missing": [], "extra": [], "duplicated": [], "renamed": []}},
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
                "products": {"L-1": {"gate_id": "G1-EGO", "product_type": "EgoLaw", "revision": 1,
                                     "payload_sha256": _product_content("L-1")[1]}},
                "witnesses": {"W-1": _witness()},
            },
            "product_content": {"L-1": _product_content("L-1")[0]},  # schema v5 (WO-PE-03A): the product's body
            "gaps": [{"subject": "LEVEL-1", "archetype_question": "Is anything INERT?", "reason": "NOT_BUILT"},
                     {"subject": "E0003", "archetype_question": "Is this object a lever?", "reason": "INCONCLUSIVE"}],
            "accounting": {"status": "ACCOUNTED", "missing": []},
            "description": _description(),
            "win_episode": {"schema": "virelai-win-episode-v1", "state": "NOT_OBSERVED"},  # schema v10 (WO-WIN-01)
        }],
    })


def _with_dossiers(model: dict) -> dict:
    """Schema v6 (WO-G4-DOSSIER-A): the lever's dossier, compiled from a gate view with nothing retained."""
    from inference.framework import lever_dossiers

    for level in model["levels"]:
        level["lever_dossiers"] = lever_dossiers.build(level, lever_dossiers.EMPTY_VIEW)
    model["levels"] = lever_dossiers.finalize(model["levels"], model["manifest"]["persist_reason"])
    return model


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
            _level(model)["description"] = _description(lever=False)  # a pointer ego binds no track
            _level(model)["lever_dossiers"] = {}  # schema v6: no LEVER role remains, so no dossier
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
        read_world_model({"schema": "virelai-world-model-v12"})  # WO-RUNTIME-01: v11 is the writer now


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


def test_only_a_checked_journal_may_be_accounted():
    def pending(model):
        _level(model)["record"]["journal_check"] = {"status": "PENDING"}
    _refused(pending, "pending is NOT_ACCOUNTED")

    def pending_honest(model):
        pending(model)
        _level(model)["accounting"] = {"status": "NOT_ACCOUNTED", "missing": ["JOURNAL_CHECK_PENDING"]}
    seal(_apply(_model(), pending_honest))
    _refused(lambda m: _level(m)["record"].pop("journal_check"), "PENDING or CHECKED")
    _refused(lambda m: _level(m)["record"]["journal_check"].update(missing=[3]), "ok agrees with its ids")

    def mismatch(model, gap_ids):
        _level(model)["record"]["journal_check"].update(ok=False, renamed=[1])
        _level(model)["accounting"] = {"status": "NOT_ACCOUNTED", "missing": ["RECORD_MISMATCH"]}
        _level(model)["gaps"].append({"subject": "LEVEL-1", "archetype_question": "q", "reason": "RECORD_MISMATCH",
                                      "source": "record_check", "missing": [], "extra": [], "duplicated": [],
                                      "renamed": gap_ids})
        return model
    seal(mismatch(_model(), [1]))
    with pytest.raises(WorldModelV2Error, match="naming the same ids"):
        seal(mismatch(_model(), [2]))
