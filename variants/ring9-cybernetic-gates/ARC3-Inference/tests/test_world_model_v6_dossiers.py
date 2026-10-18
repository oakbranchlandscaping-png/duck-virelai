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
V6 = "virelai-world-model-v6"
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
    assert wm.SCHEMA == V6 and wm.V5_SCHEMA == "virelai-world-model-v5"
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
