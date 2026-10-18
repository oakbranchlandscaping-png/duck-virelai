"""WO-G4-DOSSIER-A fail-first tests (T0): schema v6's lever dossiers — the schema, the projections and the attacks.

Author: Claude (Alpha build seat), 2026-10-16; revision 2, 2026-10-17. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2``
§9 (cases 1-30, Sol's review) and Sol's revision-2 directive (blockers 1-4, the provenance scope, the T0 rhythm).

Three kinds of test, kept apart in the fail-first records:

* **revision-1 behaviour** (``test_v6_<n>_*``): fails on ``e8984c2``;
* **revision-2 behaviour** (``test_v6_r2_*``): fails on revision 1 — executor provenance, submitter and certifier,
  exact transformation-event links, affected-subject joins, the provenance scope and the size budget;
* **compatibility guards** (``test_guard_*``): pass on ``e8984c2`` and must still pass.

T0 holds the pure schema, projection and attack cases: synthetic provenance fixtures (``dossier_provenance_
fixtures``), hand-built transitions, and two record states replayed once per module (attacks edit copies). The
full-record semantic cases are in ``test_world_model_v6_dossier_records`` (T1).
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

import dossier_fixtures as fx
import dossier_provenance_fixtures as pf

FIXTURES = Path(__file__).parent / "fixtures"
WRITER = "virelai-world-model-v7"  # the writer since WO-G4-DOSSIER-B (B1)
RELATIONS = "G4-B-LEVER-RELATIONS"
_SHARED: dict = {}


def _shared(key, build):
    if key not in _SHARED:
        _SHARED[key] = build()
    return _SHARED[key]


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _rehash(model: dict) -> dict:
    """Recompute every chapter digest and the model hash, so only the semantic rule under test can refuse."""
    from inference.framework import lever_dossiers

    for level in model["levels"]:
        for entity_id, dossier in level["lever_dossiers"].items():
            for name, item in dossier["chapters"].items():
                item["digest"] = lever_dossiers.chapter_digest(entity_id, name, item)
    model["content_sha256"] = _wm().content_sha256(model)
    return model


def _refused(model: dict, match: str) -> None:
    with pytest.raises(_wm().WorldModelV2Error, match=match):
        _wm().validate(_rehash(model))


@pytest.fixture(scope="module")
def t80_machine():
    return fx.ft09_through(80).machine  # read only: compilation never changes the machine


@pytest.fixture(scope="module")
def t80_model(t80_machine):
    return fx.compiled(t80_machine, persist_reason="LEVEL_ADVANCE")


@pytest.fixture(scope="module")
def anatomy_model():
    return fx.compiled(fx.ft09_anatomy(8).machine, persist_reason="LEVEL_ADVANCE")


# ---- 9-13 · validation refuses forgeries, even rehashed -------------------------------------------------------

def test_v6_09_every_reference_resolves_and_a_dangling_one_is_refused(t80_model):
    model = copy.deepcopy(t80_model)
    level = fx.open_level(model)
    for dossier in level["lever_dossiers"].values():
        for item in dossier["chapters"].values():
            assert all(ref in level["receipts"]["evidence"] for ref in item["evidence_refs"])
    orbit = fx.chapter(level, "E0054", "orbit")
    orbit["facts"]["run"]["steps"][0]["evidence_ref"] = "E-0000000000000000"
    orbit["evidence_refs"] = sorted({*orbit["evidence_refs"], "E-0000000000000000"})
    _refused(model, "resolve|evidence")


def test_v6_10_a_forged_fact_is_refused_even_after_rehashing(t80_model):
    model = copy.deepcopy(t80_model)
    orbit = fx.chapter(model, "E0053", "orbit")
    orbit["facts"]["period"] = (orbit["facts"]["period"] or 0) + 1
    _refused(model, "product")


def test_v6_11_a_forged_status_is_refused_both_ways(t80_model):
    upgraded = copy.deepcopy(t80_model)
    fx.chapter(upgraded, "E0054", "orbit").update(status="COMPLETE", basis="PRODUCT_CERTIFIED")
    _refused(upgraded, "COMPLETE")
    downgraded = copy.deepcopy(t80_model)
    fx.chapter(downgraded, "E0053", "orbit").update(status="IN_PROGRESS", basis="RUN_OPEN")
    _refused(downgraded, "COMPLETE")


def test_v6_12_a_product_and_dossier_disagreement_is_refused(anatomy_model):
    from inference.framework import product_content

    model = copy.deepcopy(anatomy_model)
    level = fx.open_level(model)
    (pid,) = [p for p, e in level["product_content"].items() if e["gate_id"] == "G4-REACTIONS"]
    entry = level["product_content"][pid]
    entry["payload"]["anatomies"][0]["channels"][0]["bbox"][0] += 1  # the stored product now says something else
    entry["digest"] = product_content.digest_record({k: entry[k] for k in ("gate_id", "product_type", "revision",
                                                                         "dependencies", "payload")})
    level["receipts"]["products"][pid]["payload_sha256"] = product_content.legacy_payload_sha256(entry["payload"])
    _refused(model, "product")


def test_v6_13_an_unresolved_join_or_another_levers_witness_cannot_contaminate_a_dossier(t80_model):
    model = copy.deepcopy(t80_model)
    level = fx.open_level(model)
    other = fx.chapter(level, "E0054", "identity")["facts"]["witnesses"][0]
    identity = fx.chapter(level, "E0053", "identity")
    identity["facts"]["witnesses"].append(other)
    identity["evidence_refs"] = sorted({*identity["evidence_refs"], other["evidence_ref"]})
    _refused(model, "witness")
    joined = copy.deepcopy(t80_model)
    dossier = fx.open_level(joined)["lever_dossiers"]["E0053"]
    dossier["track_join"] = {"status": "EXACT_ONE_TO_ONE", "track_id": "O-L1-P1-E-forged", "basis": {"key": "k"}}
    _refused(joined, "track_join")


# ---- 16 · compatibility --------------------------------------------------------------------------------------

def test_v6_16_frozen_v5_reads_by_its_frozen_rules_and_v6_is_the_writer():
    wm = _wm()
    v5 = json.loads((FIXTURES / "world_model_v5_frozen.json").read_text())  # sealed by e8984c2's v5 code
    assert wm.SCHEMA == WRITER and wm.V5_SCHEMA == "virelai-world-model-v5"
    assert wm.read_world_model(v5)["schema"] == "virelai-world-model-v5"
    wm.validate_v5(v5)


# ---- 19, 20, 30 · strict canonical JSON ----------------------------------------------------------------------

@pytest.mark.parametrize("value", [{1: "a"}, {"o": {2.5: "a"}}, {"o": [{True: 1}]}, {"o": {None: 1}},
                                   {"n": math.nan}, {"n": [math.inf]}, {"n": {"d": -math.inf}}],
                         ids=["int", "float_nested", "bool_in_list", "null_nested", "nan", "inf", "neg_inf"])
def test_v6_19_one_strict_canonicalizer_refuses_with_a_path(value):
    from inference.framework import answer_shapes, product_content, strict_json

    with pytest.raises(strict_json.StrictJsonError, match=r"at \$"):
        strict_json.canonical_json(value)
    with pytest.raises(answer_shapes.AnswerProjectionError, match="NON_JSON_VALUE"):
        answer_shapes.canonical_json(value)
    with pytest.raises(product_content.ProductContentError):
        product_content.canonical_json(value)
    assert answer_shapes.canonical_json({"1": "x"}) == strict_json.canonical_json({"1": "x"})


def test_v6_30_strict_sealing_refuses_a_nested_non_string_key_even_rehashed(t80_model):
    model = copy.deepcopy(t80_model)
    fx.open_level(model)["description"]["schema_note"] = {7: "a key json.dumps would silently stringify"}
    with pytest.raises(_wm().WorldModelV2Error, match="non-string mapping key"):
        _wm().validate(_rehash(model))
    with pytest.raises(_wm().WorldModelV2Error, match="non-string mapping key"):
        _wm().seal(model)


def test_guard_20_valid_canonical_payloads_keep_their_hashes():
    from inference.framework import answer_shapes, product_content

    payload = {"b": [1, (2, 3)], "a": "x", "c": {"d": None, "e": 1.5, "f": True}}
    assert answer_shapes.sha16(payload) == "add00600185a893b"  # pinned at e8984c2
    assert product_content.digest_record(payload)["value"][:16] == "add00600185a893b"
    v5 = json.loads((FIXTURES / "world_model_v5_frozen.json").read_text())
    for level in v5["levels"]:
        for entry in level["product_content"].values():
            identity = {k: entry[k] for k in ("gate_id", "product_type", "revision", "dependencies", "payload")}
            assert product_content.digest_record(identity) == entry["digest"]


# ---- revision 2 · blocker 1: chooser and executor ----------------------------------------------------------------

def _actor(model: dict) -> dict:
    return pf.dossier(model)["chapters"]["identity"]["facts"]["actor"]


def _actor_tuple(model: dict) -> tuple:
    actor = _actor(model)
    return actor["chooser"], actor["chooser_basis"], actor["executor"], actor["status"], actor["basis"]


def test_v6_r2_01_a_duck_chosen_and_duck_executed_activation(tmp_path):
    model = pf.sealed(pf.model("RUN_END", chooser="DUCK"), pf.journal(tmp_path, [("DUCK", pf.EVIDENCE, 1)]))
    assert _actor_tuple(model) == ("DUCK", "G3_SELECTION_EVENT", "DUCK", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")
    assert _actor(model)["execution_event_id"] == pf.executions_of(model)[pf.EVIDENCE][0]


def test_v6_r2_02_a_duck_chosen_but_controller_executed_activation(tmp_path):
    model = pf.sealed(pf.model("RUN_END", chooser="DUCK"), pf.journal(tmp_path, [("CONTROLLER", pf.EVIDENCE, 1)]))
    assert _actor_tuple(model) == ("DUCK", "G3_SELECTION_EVENT", "CONTROLLER", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")


def test_v6_r2_03_controller_coverage_with_no_duck_choice(tmp_path):
    model = pf.sealed(pf.model("RUN_END"), pf.journal(tmp_path, [("CONTROLLER", pf.EVIDENCE, 1)]))
    assert _actor_tuple(model) == ("CONTROLLER", "G3_COVERAGE_ORDER", "CONTROLLER", "VERIFIED",
                                   "EVIDENCE_LINKED_EXECUTION")
    forged = copy.deepcopy(model)
    _actor(forged)["executor"] = "DUCK"  # the journal says the controller executed it
    _refused(forged, "actor|executor")


@pytest.mark.parametrize("reason", ["LIVE_VIEW", "LEVEL_ADVANCE"])
def test_v6_r2_04_live_and_h1_provenance_is_pending_and_never_defaults_to_the_controller(reason):
    model = _wm().seal(pf.model(reason, chooser="DUCK"))
    assert _actor_tuple(model) == ("DUCK", "G3_SELECTION_EVENT", None, "PENDING", "PROVENANCE_NOT_FINAL")
    assert _actor(model)["execution_event_id"] is None
    identity = pf.dossier(model)["chapters"]["identity"]
    assert identity["status"] == "COMPLETE" and not [i for i in identity["open"] if i["kind"] == "PROVENANCE_INCOMPLETE"]
    forged = copy.deepcopy(model)
    _actor(forged).update(executor="CONTROLLER", status="VERIFIED", basis="EVIDENCE_LINKED_EXECUTION")
    _refused(forged, "actor|executor")


def test_v6_r2_05_an_h2_journal_missing_the_execution_fails_the_executor_closed_and_keeps_the_witness(tmp_path):
    model = pf.sealed(pf.model("RUN_END", chooser="DUCK"), pf.journal(tmp_path, executions=()))
    assert _actor_tuple(model) == ("DUCK", "G3_SELECTION_EVENT", None, "FAILED_CLOSED", "EXECUTION_MISSING")
    identity = pf.dossier(model)["chapters"]["identity"]
    assert (identity["status"], identity["basis"]) == ("COMPLETE", "WITNESS_CERTIFIED")  # the witness is not erased
    assert [w["evidence_ref"] for w in identity["facts"]["witnesses"]] == [pf.EVIDENCE]
    item = {"kind": "PROVENANCE_INCOMPLETE", "field": "ACTIVATION_EXECUTOR", "basis": "EXECUTION_MISSING",
            "evidence_ref": pf.EVIDENCE}
    assert item in identity["open"]
    assert {"chapter": "identity", **item} in pf.dossier(model)["chapters"]["open_items"]["facts"]["provenance_incomplete"]
    unavailable = pf.sealed(pf.model("RUN_END"), None)  # no journal could be read at H2
    assert _actor_tuple(unavailable)[2:] == (None, "FAILED_CLOSED", "JOURNAL_UNAVAILABLE")


def test_v6_r2_06_an_execution_that_disagrees_with_its_evidence_fails_the_identity_claim_closed(tmp_path):
    model = pf.sealed(pf.model("RUN_END", chooser="DUCK"), pf.journal(tmp_path, [("DUCK", pf.EVIDENCE, 2)]))
    identity = pf.dossier(model)["chapters"]["identity"]
    assert (identity["status"], identity["basis"], identity["prior_status"], identity["facts"]) == (
        "CLOSED_UNRESOLVED", "PROVENANCE_INCOMPLETE", "COMPLETE", None)
    assert identity["integrity"] == {"status": "FAILED_CLOSED", "reasons": ["PROVENANCE_INCOMPLETE"],
                                     "refs": [pf.EVIDENCE]}
    assert {"kind": "PROVENANCE_INCOMPLETE", "field": "EVIDENCE_EXECUTION", "basis": "EXECUTION_EVIDENCE_DISAGREES",
            "refs": [pf.EVIDENCE]} in identity["open"]
    forged = copy.deepcopy(model)  # a failure provenance does not support is refused too
    pf.dossier(forged)["chapters"]["identity"]["integrity"]["refs"] = ["E-2"]
    _refused(forged, "PROVENANCE_INCOMPLETE")


# ---- revision 2 · the provenance scope ---------------------------------------------------------------------------

def test_v6_r2_07_unverifiable_authorship_leaves_anatomy_orbit_and_prediction_facts_standing(t80_machine):
    model = fx.compiled(t80_machine, persist_reason="BUDGET_STOP")  # H2 with no journal: nothing can be verified
    level = fx.open_level(model)
    for dossier in level["lever_dossiers"].values():
        identity = dossier["chapters"]["identity"]
        assert identity["status"] == "COMPLETE"
        assert (identity["facts"]["actor"]["executor"], identity["facts"]["actor"]["status"]) == (None, "FAILED_CLOSED")
    orbit, anatomy = fx.chapter(level, "E0053", "orbit"), fx.chapter(level, "E0053", "anatomy")
    assert (orbit["status"], anatomy["status"]) == ("COMPLETE", "COMPLETE") and orbit["facts"]["run"]["steps"]
    assert all(c["integrity"]["status"] == "OK" for c in level["lever_dossiers"]["E0053"]["chapters"].values())


def test_v6_r2_08_provenance_contradicting_a_receipt_fails_only_the_chapters_resting_on_it(t80_machine, tmp_path):
    model = fx.compiled(t80_machine, persist_reason="RUN_END")
    level = fx.open_level(model)
    step = fx.chapter(level, "E0053", "orbit")["facts"]["run"]["steps"][0]
    sealed = pf.sealed(model, pf.journal(tmp_path, [("CONTROLLER", step["evidence_ref"], step["transition_id"] + 1)]))
    level = fx.open_level(sealed)
    for name, prior in (("orbit", "COMPLETE"), ("limits", "IN_PROGRESS")):
        chapter = fx.chapter(level, "E0053", name)
        assert (chapter["status"], chapter["basis"], chapter["prior_status"]) == (
            "CLOSED_UNRESOLVED", "PROVENANCE_INCOMPLETE", prior)
        assert chapter["integrity"]["refs"] == [step["evidence_ref"]]
    for name in ("identity", "anatomy"):
        assert fx.chapter(level, "E0053", name)["integrity"]["status"] == "OK"
    assert fx.chapter(level, "E0054", "orbit")["integrity"]["status"] == "OK"


# ---- revision 2 · blocker 2: the submitter and the certifier ----------------------------------------------------

def test_v6_r2_09_duck_submits_a_relation_set_and_the_gate_certifies_it():
    from inference.framework import lever_dossier_facts as F

    answer = {"answer_id": "G4B-A1", "description": "d", "relations": [{"levers": ["E1"], "claim": "c"}]}
    payload = {"status": "COMPLETE", "certified_by": "DUCK", "from_record": None, "lever_entities": ["E1"],
               "pressed_levers": ["E1"], "predictions": [], "missing_conditions": [], "answer": answer}
    frozen = copy.deepcopy(payload)
    facts = F.relations_facts(payload, "E1")
    assert "certified_by" not in facts and payload == frozen  # the frozen G4 payload is not changed
    assert facts["submission"] == {"submission_source": None, "certifier": RELATIONS,
                                   "certification_origin": "ANSWER_CERTIFIED", "status": "PENDING",
                                   "basis": "PROVENANCE_NOT_FINAL", "answer_event_id": None}
    record = {**payload, "certified_by": "RECORD", "from_record": {"answer_id": "G4B-A1"}}
    assert F.relations_facts(record, "E1")["submission"] == {
        "submission_source": "RECORD", "certifier": RELATIONS, "certification_origin": "RELATIONS_CERTIFIED_FROM_RECORD",
        "status": "VERIFIED", "basis": "GATE_RECORD_DERIVATION", "answer_event_id": None}


# ---- revision 2 · blockers 3 and 4: event links and affected subjects (pure) --------------------------------------

def _event(event_id: str, verb: str, runs: list, track: str = "O-L1-P1-E-a", side: dict | None = None) -> dict:
    groups = {"retained_rewritten": [{"cell_runs": runs, "outcome": "CHANGED", "cell_count": 0}],
              "prior_footprint_only": [], "later_footprint_only": []}
    return {"event_id": event_id, "transition_id": 5, "verb": verb, "subject": {"track_id": track, "roles": []},
            "before": side, "after": side, "delta": {"footprint": {"membership_groups": groups}}}


def _channel(runs: list, bbox: list, locality: str = "LOCAL") -> dict:
    return {"channel_id": "CH-x", "locality": locality, "cell_runs": runs, "bbox": bbox}


def _link(channel: dict, events: list, tracks=("O-L1-P1-E-a", "O-L1-P1-E-b", "O-L1-P1-E-c")) -> dict:
    from inference.framework import lever_dossier_links as L

    return L.link_channel(channel, {"transition_id": 5, "evidence_ref": "E-5", "events": events}, set(tracks))


def test_v6_r2_10_one_local_event_links_and_joins_its_track_by_an_exact_footprint():
    side = {"bbox": [2, 2, 2, 3], "cell_count": 2}
    linked = _link(_channel([[2, 2, 3]], [2, 2, 2, 3]), [_event("EV-a", "RECOLOR", [[2, 2, 3]], side=side),
                                                       _event("EV-z", "SHRINK", [[9, 9, 9]], "O-L1-P1-E-c")])
    assert linked["events"] == [{"event_id": "EV-a", "transition_id": 5, "verb": "RECOLOR"}]
    assert linked["event_status"] == "LINKED"
    assert linked["subject"] == {"status": "EXACT_TRACK", "track_id": "O-L1-P1-E-a",
                                 "basis": {"key": "EXACT_EVENT_FOOTPRINT", "event_id": "EV-a", "transition_id": 5}}


def test_v6_r2_11_one_remote_event_links_but_a_partial_footprint_joins_no_track():
    side = {"bbox": [7, 0, 7, 4], "cell_count": 5}
    linked = _link(_channel([[7, 3, 4]], [7, 3, 7, 4], "REMOTE"), [_event("EV-r", "GROW", [[7, 3, 4]], side=side)])
    assert linked["events"] == [{"event_id": "EV-r", "transition_id": 5, "verb": "GROW"}]
    assert linked["subject"] == {"status": "UNRESOLVED_REGION", "reason": "NO_EXACT_MATCH"}


def test_v6_r2_12_several_events_from_one_activation_and_an_ambiguous_footprint():
    one, two = {"bbox": [1, 1, 1, 1], "cell_count": 1}, {"bbox": [1, 2, 1, 2], "cell_count": 1}
    linked = _link(_channel([[1, 1, 2]], [1, 1, 1, 2]), [_event("EV-1", "BIRTH", [[1, 1, 1]], side=one),
                                                       _event("EV-2", "BIRTH", [[1, 2, 2]], "O-L1-P1-E-b", side=two)])
    assert [ref["event_id"] for ref in linked["events"]] == ["EV-1", "EV-2"]
    assert linked["subject"] == {"status": "UNRESOLVED_REGION", "reason": "NO_EXACT_MATCH"}
    side = {"bbox": [1, 1, 1, 2], "cell_count": 2}
    twins = _link(_channel([[1, 1, 2]], [1, 1, 1, 2]), [_event("EV-1", "RECOLOR", [[1, 1, 2]], side=side),
                                                      _event("EV-2", "RECOLOR", [[1, 1, 2]], "O-L1-P1-E-b", side=side)])
    assert twins["subject"] == {"status": "UNRESOLVED_REGION", "reason": "AMBIGUOUS_MATCH"}  # never a guess


def test_v6_r2_13_no_matching_event_an_undescribed_transition_and_a_track_of_another_level():
    from inference.framework import lever_dossier_links as L

    partial = _link(_channel([[3, 3, 3]], [3, 3, 3, 3]), [_event("EV-p", "MOVE", [[3, 3, 4]])])
    assert (partial["events"], partial["event_status"]) == ([], "NO_MATCHING_EVENT")
    assert partial["subject"] == {"status": "UNRESOLVED_REGION", "reason": "NO_EXACT_MATCH"}
    absent = L.link_channel(_channel([[3, 3, 3]], [3, 3, 3, 3]), None, set())
    assert (absent["events"], absent["event_status"]) == ([], "TRANSITION_NOT_DESCRIBED")
    side = {"bbox": [3, 3, 3, 3], "cell_count": 1}
    foreign = _link(_channel([[3, 3, 3]], [3, 3, 3, 3]), [_event("EV-f", "RECOLOR", [[3, 3, 3]], "O-L2-P1-E-a", side)])
    assert foreign["events"] and foreign["subject"]["status"] == "UNRESOLVED_REGION"


# ---- revision 2 · blockers 3 and 4: the validator refuses forged links and joins --------------------------------

def _linked_channel(model: dict) -> dict:
    (channel,) = fx.chapter(model, "E0053", "anatomy")["facts"]["channels"]
    assert channel["events"] and channel["subject"]["status"] == "EXACT_TRACK"
    return channel


def _witness_events(model: dict, channel: dict) -> list[dict]:
    transition = channel["events"][0]["transition_id"]
    return next(t for t in fx.open_level(model)["description"]["transitions"] if t["transition_id"] == transition)["events"]


def test_v6_r2_14_a_forged_event_id_is_refused(anatomy_model):
    model = copy.deepcopy(anatomy_model)
    _linked_channel(model)["events"][0]["event_id"] = "EV-0000000000000000"
    _refused(model, "event")


def test_v6_r2_15_an_event_from_another_transition_is_refused(anatomy_model):
    model = copy.deepcopy(anatomy_model)
    channel = _linked_channel(model)
    witness = channel["events"][0]["transition_id"]
    other = next(event for t in fx.open_level(model)["description"]["transitions"] if t["transition_id"] != witness
                 for event in t["events"] if event["verb"] != "STILL")
    channel["events"].append({"event_id": other["event_id"], "transition_id": other["transition_id"],
                              "verb": other["verb"]})
    _refused(model, "event")


def test_v6_r2_16_an_event_whose_footprint_misses_the_certified_residue_is_refused(anatomy_model):
    model = copy.deepcopy(anatomy_model)
    channel = _linked_channel(model)
    linked = {ref["event_id"] for ref in channel["events"]}
    stranger = next(e for e in _witness_events(model, channel) if e["verb"] != "STILL" and e["event_id"] not in linked)
    channel["events"].append({"event_id": stranger["event_id"], "transition_id": stranger["transition_id"],
                              "verb": stranger["verb"]})
    _refused(model, "intersect|residue")


def test_v6_r2_17_an_injected_or_foreign_track_join_is_refused(anatomy_model):
    model = copy.deepcopy(anatomy_model)
    channel = _linked_channel(model)
    tracks = [t["track_id"] for t in fx.open_level(model)["observation"]["tracks"]]
    channel["subject"]["track_id"] = next(t for t in tracks if t != channel["subject"]["track_id"])
    _refused(model, "subject|track")
    foreign = copy.deepcopy(anatomy_model)
    _linked_channel(foreign)["subject"]["track_id"] = "O-L2-P1-E-9ba0bdad2bf9"
    _refused(foreign, "subject|track")


def test_v6_r2_18_a_join_the_description_makes_ambiguous_is_refused(anatomy_model):
    from inference.framework import lever_dossier_schema as S

    model = copy.deepcopy(anatomy_model)
    channel = _linked_channel(model)
    events = _witness_events(model, channel)
    matched = next(e for e in events if e["event_id"] == channel["subject"]["basis"]["event_id"])
    twin = copy.deepcopy(matched)
    twin.update(event_id="EV-ffffffffffffffff", subject={**matched["subject"], "track_id": "O-L1-P1-E-twin"})
    events.append(twin)  # a second object with exactly the same footprint: the join can no longer be unique
    fx.open_level(model)["observation"]["tracks"].append({"track_id": "O-L1-P1-E-twin"})
    with pytest.raises(S.DossierError, match="subject|track|event"):
        S.validate_level(fx.open_level(model), model["manifest"], model["provenance"])


# ---- revision 2 · the size budget ----------------------------------------------------------------------------

def test_guard_r2_dossiers_stay_inside_the_review_budget(t80_model, anatomy_model):
    from inference.framework import strict_json

    for model in (t80_model, anatomy_model):
        total = len(_wm().canonical_bytes(model))
        for level in model["levels"]:
            size = len(strict_json.canonical_json(level["lever_dossiers"]))
            assert size <= 128 * 1024 and size <= 0.10 * total


# ---- revision 3 · execution joins are scoped by level (Sol's conditional acceptance) ---------------------------

def _two_level(tmp_path, rows) -> dict:
    """E-1 at transition 1 on a frozen level 1 and an open level 2; ``rows`` are (executor, evidence, transition, level)."""
    return pf.sealed(pf.two_level_model("RUN_END", chooser="DUCK"), pf.journal(tmp_path, rows))


def _identity_on(model: dict, index: int) -> dict:
    return model["levels"][index]["lever_dossiers"][pf.ENTITY]["chapters"]["identity"]


def _executor_on(model: dict, index: int) -> tuple:
    actor = _identity_on(model, index)["facts"]["actor"]
    return actor["executor"], actor["status"], actor["basis"], actor["execution_event_id"]


def test_v6_r3_01_one_evidence_id_on_two_levels_has_two_independently_verified_executors(tmp_path):
    model = _two_level(tmp_path, [("DUCK", pf.EVIDENCE, 1, 1), ("CONTROLLER", pf.EVIDENCE, 1, 2)])
    (first,) = pf.executions_of(model, 1)[pf.EVIDENCE]
    (second,) = pf.executions_of(model, 2)[pf.EVIDENCE]
    assert _executor_on(model, 0) == ("DUCK", "VERIFIED", "EVIDENCE_LINKED_EXECUTION", first)
    assert _executor_on(model, 1) == ("CONTROLLER", "VERIFIED", "EVIDENCE_LINKED_EXECUTION", second)
    forged = copy.deepcopy(model)  # level 2's execution can never verify level 1's executor
    _identity_on(forged, 0)["facts"]["actor"].update(executor="CONTROLLER", execution_event_id=second)
    _refused(forged, "actor|executor")


def test_v6_r3_02_an_execution_on_another_level_never_makes_this_level_duplicated(tmp_path):
    model = _two_level(tmp_path, [("DUCK", pf.EVIDENCE, 1, 1), ("DUCK", pf.EVIDENCE, 1, 2)])
    for index in (0, 1):
        assert _executor_on(model, index)[1:3] == ("VERIFIED", "EVIDENCE_LINKED_EXECUTION")
        assert not [i for i in _identity_on(model, index)["open"] if i["kind"] == "PROVENANCE_INCOMPLETE"]


def test_v6_r3_03_an_execution_on_another_level_never_contradicts_this_levels_receipt(tmp_path):
    model = _two_level(tmp_path, [("DUCK", pf.EVIDENCE, 1, 1), ("CONTROLLER", pf.EVIDENCE, 7, 2)])
    first = _identity_on(model, 0)
    assert (first["status"], first["integrity"]["status"]) == ("COMPLETE", "OK")
    assert _executor_on(model, 0)[:3] == ("DUCK", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")
    second = _identity_on(model, 1)  # level 2's own receipt says transition 1: its own claim fails, level 1's stands
    assert (second["status"], second["basis"], second["integrity"]["refs"]) == (
        "CLOSED_UNRESOLVED", "PROVENANCE_INCOMPLETE", [pf.EVIDENCE])


def test_v6_r3_04_a_same_level_duplicate_still_fails_the_executor_closed(tmp_path):
    model = _two_level(tmp_path, [("DUCK", pf.EVIDENCE, 1, 1), ("CONTROLLER", pf.EVIDENCE, 1, 1),
                                  ("CONTROLLER", pf.EVIDENCE, 1, 2)])
    assert _executor_on(model, 0) == (None, "FAILED_CLOSED", "EXECUTION_DUPLICATED", None)
    assert _executor_on(model, 1)[:3] == ("CONTROLLER", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")


def test_v6_r3_05_a_same_level_wrong_transition_still_fails_the_dependent_chapter_closed(tmp_path):
    model = _two_level(tmp_path, [("DUCK", pf.EVIDENCE, 2, 1), ("CONTROLLER", pf.EVIDENCE, 1, 2)])
    first = _identity_on(model, 0)
    assert (first["status"], first["basis"], first["prior_status"], first["facts"]) == (
        "CLOSED_UNRESOLVED", "PROVENANCE_INCOMPLETE", "COMPLETE", None)
    assert {"kind": "PROVENANCE_INCOMPLETE", "field": "EVIDENCE_EXECUTION", "basis": "EXECUTION_EVIDENCE_DISAGREES",
            "refs": [pf.EVIDENCE]} in first["open"]
    assert _executor_on(model, 1)[:3] == ("CONTROLLER", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")


def test_v6_r3_06_an_execution_found_only_on_another_level_leaves_this_level_missing(tmp_path):
    model = _two_level(tmp_path, [("CONTROLLER", pf.EVIDENCE, 1, 2)])
    assert _executor_on(model, 0) == (None, "FAILED_CLOSED", "EXECUTION_MISSING", None)
    assert _identity_on(model, 0)["status"] == "COMPLETE"  # no cross-level fallback, and the witness stands
    assert _executor_on(model, 1)[:3] == ("CONTROLLER", "VERIFIED", "EVIDENCE_LINKED_EXECUTION")


def test_v6_r3_07_the_corrected_two_level_model_seals_and_validates_deterministically(tmp_path):
    rows = [("DUCK", pf.EVIDENCE, 1, 1), ("CONTROLLER", pf.EVIDENCE, 1, 2)]
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first, second = _two_level(tmp_path / "a", rows), _two_level(tmp_path / "b", rows)
    assert [_executor_on(first, index)[:2] for index in (0, 1)] == [("DUCK", "VERIFIED"), ("CONTROLLER", "VERIFIED")]
    assert _wm().canonical_bytes(first) == _wm().canonical_bytes(second)
    resealed = _wm().seal(copy.deepcopy(first))  # sealing a sealed model again changes nothing
    assert resealed == first
    _wm().validate(first)
    _wm().validate(resealed)


# ---- WO-G4-DOSSIER-B · B1: derived current state, persistence and reversal (Sol's rulings 2 and 3) ------------

def _state():
    from inference.framework import lever_dossier_state

    return lever_dossier_state


def _scope(rows, initial=None, regions=("A", "B")):
    return {"level": 1, "life": 1, "initial": initial or {"A": "a0", "B": "b0"},
            "regions": {entity: 4 for entity in regions}, "rows": rows}


def _row(transition_id, actor, contents, *, cited=True, boundary=None):
    return {"transition_id": transition_id, "boundary": boundary, "actor": actor, "contents": contents,
            "evidence_ref": f"E-{transition_id}" if cited else None}


def test_b1_01_persistence_counts_cited_interventions_and_zero_trials_stays_untested():
    rows = [_row(1, "B", {"A": "a0", "B": "b1"}), _row(2, "B", {"A": "a0", "B": "b0"}),
            _row(3, None, {"A": "a1", "B": "b0"})]
    first = _state().derive(_scope(rows), "A")["persistence"]
    assert (first["status"], first["tested"], first["unchanged"], first["changed"]) == ("TESTED", 3, 2, 1)
    assert first["unchanged_transitions"] == [1, 2]
    assert first["changed_cases"] == [{"transition_id": 3, "evidence_ref": "E-3", "acting_lever": None}]
    alone = _state().derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"})]), "A")
    assert (alone["persistence"]["status"], alone["persistence"]["tested"]) == ("UNTESTED", 0)
    assert alone["reversal"]["cross_reversal"]["status"] == "UNTESTED"
    empty = _state().derive(_scope([]), "A")
    assert empty["current_region_state"]["label"] == "S0" and empty["scope"]["as_of_transition"] is None
    assert all(item["status"] == "UNTESTED" for item in empty["reversal"].values())


def test_b1_02_a_two_state_toggle_is_reversal_and_a_longer_cycle_is_only_recurrence():
    toggle = _state().derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"}), _row(2, "A", {"A": "a0", "B": "b0"})]), "A")
    assert toggle["reversal"]["toggle_reversal"]["status"] == "OBSERVED"
    (case,) = toggle["reversal"]["toggle_reversal"]["cases"]
    assert (case["from_state"], case["to_state"], case["cycle_length"], case["acting_lever"]) == ("S1", "S0", 2, "A")
    cycle = _state().derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"}), _row(2, "A", {"A": "a2", "B": "b0"}),
                                    _row(3, "A", {"A": "a0", "B": "b0"})]), "A")
    assert cycle["reversal"]["toggle_reversal"]["status"] == "NOT_OBSERVED"
    (case,) = cycle["reversal"]["self_recurrence"]["cases"]
    assert (case["to_state"], case["cycle_length"]) == ("S0", 3)


def test_b1_03_cross_reversal_names_the_other_lever_and_other_actions_stay_apart():
    model = _state().derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"}), _row(2, "B", {"A": "a0", "B": "b1"}),
                                    _row(3, None, {"A": "a1", "B": "b1"}), _row(4, None, {"A": "a0", "B": "b1"})]), "A")
    (cross,) = model["reversal"]["cross_reversal"]["cases"]
    assert (cross["acting_lever"], cross["transition_id"], cross["cycle_length"]) == ("B", 2, 2)
    assert [(case["acting_lever"], case["transition_id"]) for case in model["reversal"]["other_return"]["cases"]] == [
        (None, 3), (None, 4)]
    assert model["reversal"]["toggle_reversal"]["status"] == "NOT_OBSERVED"  # its own press never returned it


def test_b1_04_a_boundary_ends_the_scope_a_reset_inside_a_life_fails_closed_and_an_uncited_row_is_never_a_trial():
    """Revision 2 (Sol): a reset is never skipped inside a life. Only a reset that opens the life is its entry
    (``observe`` takes the board after it); any other reset leaves the observations failed closed."""
    rows = [_row(1, "B", {"A": "a0", "B": "b1"}), _row(2, "B", {"A": "a0", "B": "b0"}, cited=False),
            _row(3, "B", {"A": "a9", "B": "b9"}, boundary="END"), _row(4, "B", {"A": "a0", "B": "b1"})]
    model = _state().derive(_scope(rows), "A")
    assert model["persistence"]["tested"] == 1 and model["scope"]["excluded"] == {"uncited": 1, "boundary": 1}
    assert model["scope"]["as_of_transition"] == 2 and _state().cited_transitions(model) == {1}
    reset = _state().derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"}), _row(2, None, {"A": "a0", "B": "b0"},
                                                                            boundary="RESET")]), "A")
    assert (reset["status"], reset["basis"], reset["failure"]) == (
        "FAILED_CLOSED", "RESET_INSIDE_LIFE", {"basis": "RESET_INSIDE_LIFE", "refs": ["2"]})
    assert reset["persistence"] is None and reset["reversal"] is None and reset["current_region_state"] is None


def test_b1_05_an_orbit_phase_needs_an_exact_mapping_inside_the_scope():
    state = _state()
    assert state.phase_mapping(["S0", "S1", "S0", "S1"], 2, "S1") == {
        "position": 1, "period": 2, "run_states": ["S0", "S1", "S0", "S1"]}
    assert state.phase_mapping(["S0", "S1", "S2"], 2, "S1") is None  # the run does not repeat with its period
    assert state.phase_mapping(["S0", "S1", "S0"], 2, "S2") is None  # the present state is outside the orbit
    rows = [_row(5, "A", {"A": "a1", "B": "b0"}), _row(6, "A", {"A": "a0", "B": "b0"})]
    assert state.run_states(_scope(rows), "A", {"steps": [{"transition_id": 5}, {"transition_id": 6}]}) == [
        "S0", "S1", "S0"]
    assert state.run_states(_scope(rows), "A", {"steps": [{"transition_id": 4}]}) is None  # another life's run


def test_b1_06_schema_v7_writes_observations_and_frozen_v6_reads_by_its_rules():
    wm = _wm()
    v6 = json.loads((FIXTURES / "world_model_v6_frozen.json").read_text())  # sealed by 87639d7's v6 code
    assert wm.SCHEMA == WRITER and wm.V6_SCHEMA == "virelai-world-model-v6"
    assert wm.read_world_model(v6)["schema"] == "virelai-world-model-v6"
    wm.validate_v6(v6)
    dossier = next(iter(wm.seal(pf.model("BUDGET_STOP"))["levels"][0]["lever_dossiers"].values()))
    assert dossier["observations"]["status"] == "NOT_BUILT"  # no anatomy region: nothing derived, nothing claimed


def _observations(model, entity):
    return fx.open_level(model)["lever_dossiers"][entity]["observations"]


def test_b1_07_derived_facts_cite_only_this_levels_life_and_resolve(t80_model):
    level = fx.open_level(t80_model)
    lives = {t["transition_id"]: t["life"] for t in level["description"]["transitions"]}
    for entity, dossier in level["lever_dossiers"].items():
        observations = dossier["observations"]
        assert observations["status"] == "OBSERVED" and observations["scope"]["level"] == level["level"]
        cited = _state().cited_transitions(observations)
        assert cited and all(lives[transition] == observations["scope"]["life"] for transition in cited)
        by_transition = {receipt["transition_id"] for receipt in level["receipts"]["evidence"].values()}
        assert cited <= by_transition  # every cited transition has its evidence receipt on this level
        persistence = observations["persistence"]
        assert persistence["tested"] == persistence["unchanged"] + persistence["changed"]


def test_b1_08_forged_observations_are_refused_even_rehashed(t80_model):
    from inference.framework import lever_dossier_state

    def refused(edit, match):
        model = copy.deepcopy(t80_model)
        observations = _observations(model, "E0053")
        edit(observations, model)
        lever_dossier_state.seal("E0053", observations)
        _refused(model, match)

    refused(lambda o, m: o["persistence"].update(unchanged=o["persistence"]["unchanged"] + 1), "persistence")
    refused(lambda o, m: o["scope"].update(life=2), "life")  # every cited transition lies in life 1
    refused(lambda o, m: o["reversal"]["toggle_reversal"]["cases"][0].update(cycle_length=3), "toggle|reversal")
    from inference.framework import lever_dossiers

    unmapped = copy.deepcopy(t80_model)  # E0054's orbit is still open: no phase may be named
    dossier = fx.open_level(unmapped)["lever_dossiers"]["E0054"]
    observations = dossier["observations"]
    observations["current_region_state"].update(orbit_phase={"run_id": "R", "position": 0, "period": 2,
                                                             "run_states": ["S0", "S1", "S0"]},
                                                phase_basis="EXACT_ORBIT_MAPPING")
    lever_dossier_state.seal("E0054", observations)
    chapters = dossier["chapters"]  # a thorough forger recomputes the derived chapter too
    chapters["open_items"]["facts"] = lever_dossiers.open_items(chapters, observations, True)["facts"]
    _refused(unmapped, "phase|orbit")


def test_b1_09_a_written_model_reads_back_whatever_its_key_order(t80_model):
    """Found by T1 (test_wo_l2a_hooks): a written model is canonical JSON with sorted keys; reading it back must
    validate (the reversal readings are a set of four, not an ordered tuple)."""
    reread = json.loads(_wm().canonical_bytes(t80_model))
    assert list(_observations(reread, "E0053")["reversal"]) == sorted(_state().CATEGORIES)
    _wm().validate(reread)
    assert _wm().read_world_model(reread)["schema"] == WRITER


# ---- WO-G4-DOSSIER-B · B1 revision 2 (Sol's review): reset entry, the limits basis --------------------------------

def _stub_machine(rows, life):
    """A minimal gate machine for ``observe``: a 1x2 board, lever A at (0,0) and lever B at (0,1), each pressed on
    its own cell; the current board is the initial board with every recorded change applied."""
    from types import SimpleNamespace

    return SimpleNamespace(transition_index=rows, lives=SimpleNamespace(level=1, life=life), _adapters={},
                           counter=SimpleNamespace(initial_grid=[[0, 0]]))


_STUB_ANATOMIES = {entity: {"entity_id": entity, "intervention": {"action": "ACTION6", "row": 0, "col": col},
                            "channels": [{"locality": "LOCAL", "cells": [[0, col]]}]}
                   for entity, col in (("A", 0), ("B", 1))}


def _stub_row(transition_id, life, changed, *, col=None, kind="PROBE", boundary="NOT_FINISHED"):
    action = {"action": "RESET"} if kind == "RESET" else {"action": "ACTION6", "row": 0, "col": col}
    return {"transition_id": transition_id, "level": 1, "life": life, "kind": kind, "boundary_state": boundary,
            "action": action, "changed": changed, "evidence_id": None if kind == "RESET" else f"E-{transition_id}"}


def _reset_record(extra=()):
    """Life 1 leaves lever A in state 5 (the press at t1) and dies at t2; the reset t3 opens life 2 with A in state
    7; the press at t4 turns A back to 5 — a state only life 1 ever held."""
    return [_stub_row(1, 1, [(0, 0, 0, 5)], col=0), _stub_row(2, 1, [(0, 1, 0, 9)], col=1, boundary="GAME_OVER"),
            _stub_row(3, 2, [(0, 0, 5, 7), (0, 1, 9, 0)], kind="RESET", boundary="RESET"),
            _stub_row(4, 2, [(0, 0, 7, 5)], col=0), *extra]


def test_b1_15_a_reset_opens_its_life_at_the_post_reset_board_and_carries_no_history():
    """Sol's fail-first case: life 1 holds state A; the reset opens life 2 at B; one press then produces A. Life 2
    reports A as a new state and no reversal: nothing before the reset is this life's."""
    state = _state()
    rows = _reset_record()
    scope = state.observe(_stub_machine(rows, 2), 1, _STUB_ANATOMIES, {f"E-{t}": {} for t in (1, 2, 4)})
    lever = state.derive(scope, "A")
    assert all(not item["cases"] for item in lever["reversal"].values())  # life 1's state is not this life's
    current = lever["current_region_state"]
    assert (current["label"], current["states_seen"]) == ("S1", 2)  # a new state of life 2, not life 1's S0
    assert lever["reversal"]["toggle_reversal"]["status"] == "NOT_OBSERVED"  # tested once: no return in this life
    assert scope["life"] == 2 and scope["entry_reset"] == 3
    assert [row["transition_id"] for row in scope["rows"]] == [4]  # the reset row is the entry, not an intervention
    assert lever["status"] == "OBSERVED" and lever["scope"]["entry_reset"] == 3
    assert lever["scope"]["excluded"] == {"uncited": 0, "boundary": 0}
    other = state.derive(scope, "B")
    assert other["persistence"]["unchanged_transitions"] == [4] and other["current_region_state"]["label"] == "S0"


def test_b1_16_a_reset_anywhere_else_in_the_life_fails_closed():
    state = _state()
    rows = _reset_record([_stub_row(5, 2, [(0, 0, 5, 7)], kind="RESET", boundary="RESET"),
                          _stub_row(6, 2, [(0, 0, 7, 5)], col=0)])
    scope = state.observe(_stub_machine(rows, 2), 1, _STUB_ANATOMIES, {f"E-{t}": {} for t in (1, 2, 4, 6)})
    for entity in ("A", "B"):
        lever = state.derive(scope, entity)
        assert (lever["status"], lever["basis"], lever["failure"]["refs"]) == ("FAILED_CLOSED", "RESET_INSIDE_LIFE", ["5"])
        assert lever["scope"]["life"] == 2 and lever["current_region_state"] is None


def test_b1_17_the_limits_basis_says_whether_a_probe_is_still_owed(t80_model):
    """Sol: ``ENDPOINT_OBSERVED_PROBES_OWED`` while either field is owed; ``RECORD_OBSERVED_NOT_GATE_CERTIFIED``
    once the record shows both and no limits probe remains. Limits stays IN_PROGRESS: no product certifies it."""
    from inference.framework import lever_dossier_facts

    state = _state()
    both = state.derive(_scope([_row(1, "A", {"A": "a1", "B": "b0"}), _row(2, "A", {"A": "a0", "B": "b0"}),
                                _row(3, "B", {"A": "a0", "B": "b1"})]), "A")
    persistence_only = state.derive(_scope([_row(1, "B", {"A": "a0", "B": "b1"})]), "A")
    untested = state.derive(_scope([]), "A")
    assert lever_dossier_facts.limits_basis(both) == "RECORD_OBSERVED_NOT_GATE_CERTIFIED"
    for owed in (persistence_only, untested, None, state.failed("RESET_INSIDE_LIFE", ["2"], None)):
        assert lever_dossier_facts.limits_basis(owed) == "ENDPOINT_OBSERVED_PROBES_OWED"
    limits = fx.chapter(fx.open_level(t80_model), "E0053", "limits")
    assert (limits["status"], limits["basis"]) == ("IN_PROGRESS", "RECORD_OBSERVED_NOT_GATE_CERTIFIED")
    assert not [item for item in limits["open"] if item["kind"] == "PROBE_OWED"]
    assert "RECORD_OBSERVED_NOT_GATE_CERTIFIED" in __import__(
        "inference.framework.lever_dossier_schema", fromlist=["BASES"]).BASES["IN_PROGRESS"]


def test_b1_18_the_limits_basis_is_pinned_and_reverts_when_the_observations_fail(t80_model):
    from inference.framework import lever_dossiers

    def forged(basis):
        model = copy.deepcopy(t80_model)
        dossier = fx.open_level(model)["lever_dossiers"]["E0053"]
        dossier["chapters"]["limits"]["basis"] = basis
        chapters = dossier["chapters"]
        chapters["open_items"]["facts"] = lever_dossiers.open_items(chapters, dossier["observations"], True)["facts"]
        return model

    _refused(forged("ENDPOINT_OBSERVED_PROBES_OWED"), "limits.*basis")
    failed = copy.deepcopy(t80_model)
    level = fx.open_level(failed)
    dossier = level["lever_dossiers"]["E0053"]
    _state().fail(dossier["observations"], "RECORD_MISMATCH", ["E0053"])
    lever_dossiers.reseal("E0053", dossier, level)  # the observations no longer show anything: both fields owed
    limits = dossier["chapters"]["limits"]
    assert (limits["status"], limits["basis"]) == ("IN_PROGRESS", "ENDPOINT_OBSERVED_PROBES_OWED")
    assert [item["field"] for item in limits["open"] if item["kind"] == "PROBE_OWED"] == [
        "LIMITS_PERSISTENCE", "LIMITS_REVERSAL"]


def test_b1_19_a_reset_entry_or_a_reset_failure_must_name_the_records_reset(t80_model):
    """The validator resolves the reset an observation scope names against the level's recorded resets."""
    from inference.framework import lever_dossiers

    entry = copy.deepcopy(t80_model)
    observations = _observations(entry, "E0053")
    observations["scope"]["entry_reset"] = 40  # transition 40 is a press, not a reset
    _state().seal("E0053", observations)
    _refused(entry, "reset")
    closed = copy.deepcopy(t80_model)
    level = fx.open_level(closed)
    dossier = level["lever_dossiers"]["E0053"]
    dossier["observations"] = _state().failed("RESET_INSIDE_LIFE", ["40"], dossier["observations"]["scope"])
    lever_dossiers.reseal("E0053", dossier, level)
    _refused(closed, "reset")
