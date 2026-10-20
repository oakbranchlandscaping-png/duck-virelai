"""WO-G4-DOSSIER-A on the committed records: the full-record semantic cases (T1; Sol's revision-2 test rhythm).

Author: Claude (Alpha build seat), 2026-10-16; split from ``test_world_model_v6_dossiers`` at revision 2
(2026-10-17). Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` §9 (cases 1-30) and Sol's revision-2 directive.

Every state is a real gate machine from a committed record or the offline ft09 world (``dossier_fixtures``). A
record is replayed once per module: compilation never changes the machine (``test_v6_guard_compilation_leaves_the_
gate_machine_byte_identical``), so read-only cases share one replay and one compiled model; a case that drives the
machine further takes its own copy. The pure schema, projection and attack cases are in ``test_world_model_v6_
dossiers`` (T0).

Revision 2 changed two revision-1 assertions on purpose, each by a ruling: case 2 (anatomy subjects are joined to a
census track where the footprint match is exact and unique; blocker 4) and case 24 (the record is the relation set's
submission source; the gate is its certifier; blocker 2).
"""
from __future__ import annotations

import copy
import json
import pickle
import re

import pytest

import dossier_fixtures as fx
import dossier_provenance_fixtures as pf

WRITER = "virelai-world-model-v10"  # the writer since WO-WIN-01
CHAPTERS = ("identity", "anatomy", "orbit", "limits", "relations", "law_tests", "open_items")
RELATIONS, LAW = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
_SHARED: dict = {}


def _shared(key, build):
    if key not in _SHARED:
        _SHARED[key] = build()
    return _SHARED[key]


def _through(transition_id: int):
    """A shared replay, for read-only use (compiling or reading); a case that drives the machine copies it."""
    return _shared(("ft09", transition_id), lambda: fx.ft09_through(transition_id)).machine


def _anatomy(answered: int):
    return _shared(("anatomy", answered), lambda: fx.ft09_anatomy(answered)).machine


def _compiled(machine_key: tuple, machine, reason: str, **options) -> dict:
    """A shared sealed model (callers that edit it copy it first)."""
    return _shared(("model", machine_key, reason, tuple(sorted(options.items()))),
                   lambda: fx.compiled(machine, persist_reason=reason, **options))


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _rehash(model: dict) -> dict:
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


def _statuses(level: dict, name: str) -> dict:
    return {entity: dossier["chapters"][name]["status"] for entity, dossier in level["lever_dossiers"].items()}


@pytest.fixture(scope="module")
def t80_model():
    return _compiled(("ft09", 80), _through(80), "LEVEL_ADVANCE")


@pytest.fixture(scope="module")
def anatomy_model():
    return _compiled(("anatomy", 8), _anatomy(8), "LEVEL_ADVANCE")


@pytest.fixture(scope="module")
def described():
    """G4-B closed by Duck's description (every lever pressed once), G4-C open: a Duck-submitted relation set."""
    from test_g4b_relations import start_g4b
    from test_g4c_law import _described

    machine, world = start_g4b()
    _described(machine, world)
    return machine


# ---- 1, 29 · a dossier from the first witness -----------------------------------------------------------------

def test_v6_01_29_first_witness_levers_have_dossiers_before_g4_and_before_the_inventory():
    machine = _through(70)
    assert machine.gate_id == "G3-LEVERS" and machine.target_journal.active_product("G3-LEVERS") is None
    model = _compiled(("ft09", 70), machine, "LEVEL_ADVANCE")
    assert model["schema"] == WRITER
    level = fx.open_level(model)
    levers = {role["entity_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER"}
    assert levers and set(level["lever_dossiers"]) == levers  # every witness-certified lever, inventory PENDING
    for entity_id, dossier in level["lever_dossiers"].items():
        identity = dossier["chapters"]["identity"]
        assert (identity["status"], identity["basis"], identity["source"]) == ("COMPLETE", "WITNESS_CERTIFIED", "GATE_WITNESS")
        assert identity["facts"]["inventory_status"] == "PENDING"
        assert [w["witness_id"] for w in identity["facts"]["witnesses"]] == sorted(
            next(r for r in level["certified"]["roles"] if r.get("entity_id") == entity_id)["witness_refs"])
        assert (dossier["chapters"]["anatomy"]["status"], dossier["chapters"]["anatomy"]["basis"]) == (
            "NOT_BUILT", "GATE_NOT_SEEDED")  # R3: no anatomy ahead of its gate
        assert dossier["subject"] == {"kind": "G3_ENTITY", "entity_id": entity_id, "level": level["level"]}


# ---- 2, 3, 27 · chapters with independent statuses ------------------------------------------------------------

def test_v6_02_anatomy_complete_with_later_chapters_unbuilt(anatomy_model):
    level = fx.open_level(anatomy_model)
    for entity_id in fx.FT09_LEVERS:
        anatomy = fx.chapter(level, entity_id, "anatomy")
        assert (anatomy["status"], anatomy["basis"], anatomy["source"]) == ("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT")
        assert anatomy["product_ref"]["product_type"] == "LeverEffectAnatomySet"
        assert anatomy["answer_ref"]["gate_id"] == "G4-REACTIONS" and anatomy["facts"]["channels"]
        # revision 2 (blocker 4): a channel names a census track only through an exact, unique footprint match
        for channel in anatomy["facts"]["channels"]:
            subject = channel["subject"]
            assert subject["status"] in ("EXACT_TRACK", "UNRESOLVED_REGION")
            if subject["status"] == "EXACT_TRACK":
                assert subject["basis"]["key"] == "EXACT_EVENT_FOOTPRINT" and subject["track_id"].startswith("O-L1-")
        for later in ("orbit", "relations", "law_tests"):
            assert fx.chapter(level, entity_id, later)["status"] == "NOT_BUILT"


def test_v6_03_27_two_levers_at_different_stages_and_limits_stay_open_while_probes_are_owed(t80_model):
    level = fx.open_level(t80_model)
    done, running = fx.chapter(level, "E0053", "orbit"), fx.chapter(level, "E0054", "orbit")
    assert (done["status"], done["basis"]) == ("COMPLETE", "PRODUCT_CERTIFIED")
    assert (running["status"], running["basis"], running["source"]) == ("IN_PROGRESS", "RUN_OPEN", "GATE_RETAINED")
    assert done["facts"]["run"]["run_status"] == "CONFIRMED" and done["facts"]["period"] is not None
    limits = fx.chapter(level, "E0053", "limits")
    # R5: limits stays IN_PROGRESS (no product certifies it). B1 revision 2 (Sol): with both fields observed and no
    # limits probe owed, the basis says so instead of claiming probes are owed
    assert (limits["status"], limits["basis"]) == ("IN_PROGRESS", "RECORD_OBSERVED_NOT_GATE_CERTIFIED")
    # B1 (Sol's ruling 2): persistence and reversal are read from the level's record, owed only where it is silent
    observations = level["lever_dossiers"]["E0053"]["observations"]
    assert (limits["facts"]["persistence"], limits["facts"]["reversal"]) == ("OBSERVED", "OBSERVED")
    assert observations["persistence"]["status"] == "TESTED"
    assert observations["reversal"]["toggle_reversal"]["status"] == "OBSERVED"
    owed = {item["field"] for item in limits["open"] if item["kind"] == "PROBE_OWED"}
    items = fx.chapter(level, "E0053", "open_items")
    assert not owed & {"LIMITS_PERSISTENCE", "LIMITS_REVERSAL"} and items["status"] == "IN_PROGRESS"  # R7


# ---- 4, 5, 6, 7, 8, 28 · stops keep partial work and never promote it ----------------------------------------

def test_v6_04_partial_work_survives_a_level_boundary():
    from inference.framework.library_census import freeze_level_census

    carried = _shared(("carry",), fx.carry_v7).machine
    frozen = carried.level_censuses[0]
    orbit = frozen["lever_dossiers"]["E0005"]["chapters"]["orbit"]
    assert (orbit["status"], orbit["basis"]) == ("CLOSED_UNRESOLVED", "INTERRUPTION_RELEASED")
    assert fx.chapter(frozen, "E0004", "orbit")["status"] == "COMPLETE"
    assert frozen["lever_dossiers"]["E0004"]["census_context"] == {"census": "H1_FROZEN", "persist_reason": "LEVEL_ADVANCE"}

    machine = copy.deepcopy(_through(79))  # E0053 confirmed, its explanation not yet accepted
    census = freeze_level_census(machine, level_before=1)
    pending = fx.chapter(census, "E0053", "orbit")
    assert (pending["status"], pending["basis"]) == ("PRODUCT_PENDING", "RUN_CONFIRMED_EXPLANATION_PENDING")
    assert pending["facts"]["run"]["run_status"] == "CONFIRMED" and pending["facts"]["run"]["steps"]
    items = fx.chapter(census, "E0053", "open_items")
    assert (items["status"], items["basis"], items["prior_status"]) == ("CLOSED_UNRESOLVED", "LEVEL_ENDED", "IN_PROGRESS")


@pytest.mark.parametrize("reason", ["BUDGET_STOP", "CONTROLLED_STOP"])
def test_v6_05_06_08_accepted_anatomy_survives_a_stop_although_no_aggregate_product_exists(reason):
    model = _compiled(("anatomy", 7), _anatomy(7), reason)
    level = fx.open_level(model)
    assert not any(e["gate_id"] == "G4-REACTIONS" for e in level["product_content"].values())  # v5 holds nothing
    statuses = _statuses(level, "anatomy")
    assert sorted(statuses.values()).count("PRODUCT_PENDING") == 7
    (open_one,) = [e for e, s in statuses.items() if s != "PRODUCT_PENDING"]
    stopped = fx.chapter(level, open_one, "anatomy")
    assert (stopped["status"], stopped["basis"], stopped["prior_status"], stopped["prior_basis"]) == (
        "INTERRUPTED", reason, "IN_PROGRESS", "ANSWER_REQUIRED")
    accepted = next(e for e, s in statuses.items() if s == "PRODUCT_PENDING")
    anatomy = fx.chapter(level, accepted, "anatomy")
    assert anatomy["basis"] == "ANSWER_ACCEPTED_AGGREGATE_OPEN" and anatomy["source"] == "GATE_RETAINED"
    assert anatomy["facts"]["channels"] and anatomy["answer_ref"]["answer_id"]
    assert level["lever_dossiers"][accepted]["census_context"] == {"census": "OPEN", "persist_reason": reason}


def test_v6_06_rest_in_play_then_h1_keeps_accepted_work_and_closes_open_work():
    from inference.framework.library_census import freeze_level_census
    from inference.framework.play_gate import rest_in_play

    machine = copy.deepcopy(_anatomy(7))
    rest_in_play(machine, "controlled stop (test)")
    census = freeze_level_census(machine, level_before=1)
    statuses = _statuses(census, "anatomy")
    assert sorted(statuses.values()) == ["CLOSED_UNRESOLVED"] + ["PRODUCT_PENDING"] * 7
    (closed,) = [e for e, s in statuses.items() if s == "CLOSED_UNRESOLVED"]
    assert fx.chapter(census, closed, "anatomy")["basis"] == "LEVEL_ENDED"


def test_v6_07_interrupted_work_is_never_promoted():
    level = fx.open_level(_compiled(("ft09", 77), _through(77), "CRASH"))  # E0053's run is confirming
    orbit = fx.chapter(level, "E0053", "orbit")
    assert (orbit["status"], orbit["basis"], orbit["prior_status"], orbit["prior_basis"]) == (
        "INTERRUPTED", "CRASH", "IN_PROGRESS", "RUN_OPEN")
    assert orbit["facts"]["run"]["run_status"] == "CONFIRMING"
    assert all(d["chapters"]["orbit"]["status"] != "COMPLETE" for d in level["lever_dossiers"].values())


@pytest.mark.parametrize("reason", ["LIVE_VIEW", "LEVEL_ADVANCE", "BUDGET_STOP", "CONTROLLED_STOP", "RUN_END",
                                    "CRASH", "CANCELLED"])
def test_v6_28_product_pending_keeps_its_semantic_basis_under_every_persist_reason(reason):
    level = fx.open_level(fx.compiled(_through(79), persist_reason=reason))
    orbit = fx.chapter(level, "E0053", "orbit")
    assert (orbit["status"], orbit["basis"], orbit["prior_status"]) == (
        "PRODUCT_PENDING", "RUN_CONFIRMED_EXPLANATION_PENDING", None)
    assert level["lever_dossiers"]["E0053"]["census_context"] == {"census": "OPEN", "persist_reason": reason}


# ---- 14 · levels ----------------------------------------------------------------------------------------------

def test_v6_14_dossiers_stay_on_their_own_level_and_never_transfer():
    """No committed record witnesses levers on two levels (carry v7's level 2 stops at G0), so separation is shown by
    construction and by refusal: level 2 holds no dossier although it carries level 1's levers as hypotheses; a level-1
    dossier moved onto level 2 is refused; a dossier citing evidence its own level does not hold is refused."""
    machine = _shared(("carry",), fx.carry_v7).machine
    model = _compiled(("carry",), machine, "RUN_END")
    first, second = model["levels"][0], model["levels"][1]
    assert set(first["lever_dossiers"]) == {"E0004", "E0005"} and second["lever_dossiers"] == {}
    assert all(d["subject"]["level"] == 1 for d in first["lever_dossiers"].values())
    moved = copy.deepcopy(model)
    moved["levels"][1]["lever_dossiers"]["E0004"] = moved["levels"][0]["lever_dossiers"]["E0004"]
    _refused(moved, "lever_dossiers|LEVER")
    foreign = copy.deepcopy(model)
    identity = foreign["levels"][0]["lever_dossiers"]["E0004"]["chapters"]["identity"]
    identity["facts"]["witnesses"][0]["evidence_ref"] = "E-from-another-level"
    identity["evidence_refs"] = sorted({*identity["evidence_refs"], "E-from-another-level"})
    _refused(foreign, "resolve|witness|evidence")


# ---- 15, 17, 18 · determinism, live view, page and report --------------------------------------------------------

def test_v6_15_compilation_is_byte_identical():
    from inference.framework.world_model_v2 import canonical_bytes

    machine = _through(80)
    first = canonical_bytes(fx.compiled(machine, persist_reason="BUDGET_STOP"))
    second = canonical_bytes(fx.compiled(machine, persist_reason="BUDGET_STOP"))
    assert first == second and json.loads(first)["schema"] == WRITER


def test_v6_17_live_view_is_noncanonical_and_refreshes_after_an_answer_with_no_transition(tmp_path):
    from inference.framework import world_model_v2
    from inference.framework.library_view import live_model

    machine = fx.ft09_anatomy(0).machine
    before = live_model(machine)
    assert before["manifest"]["persist_reason"] == "LIVE_VIEW" and not world_model_v2.write_canonical(before, tmp_path).ok
    assert set(_statuses(fx.open_level(before), "anatomy").values()) == {"IN_PROGRESS"}
    rows = len(machine.transition_index)
    fx.answer_next_anatomy(machine)  # accepted, no transition, no product
    assert len(machine.transition_index) == rows
    after = live_model(machine)
    assert sorted(_statuses(fx.open_level(after), "anatomy").values()).count("PRODUCT_PENDING") == 1


def test_v6_18_dossier_page_and_report_render_the_same_stored_content(t80_model):
    from inference.framework import world_report
    from inference.framework.library_view import library_page
    from test_world_description import _assert_report_refs

    rows, offset = {}, 0
    while offset is not None:  # every page fits the page budget; ``next`` continues it
        page = library_page(t80_model, "dossiers", id="E0053", offset=offset, limit=10)
        assert page["dossier"] == "E0053"
        rows.update({row["chapter"]: row for row in page["items"]})
        offset = page["offset"] + page["limit"] if page["next"] else None
    assert list(rows) == list(CHAPTERS)
    stored = fx.chapter(t80_model, "E0053", "orbit")
    assert rows["orbit"]["status"] == stored["status"] and rows["orbit"]["basis"] == stored["basis"]
    text = world_report.render_world_report(t80_model)
    assert f"dossier E0053 orbit: {stored['status']} ({stored['basis']})" in text
    assert "NOT_BUILT; witnesses" not in text  # the stub is gone where real content exists
    assert _assert_report_refs(t80_model, text) > 0


# ---- 21 · the k031 shape ----------------------------------------------------------------------------------------

def test_v6_21_an_unattributed_orbit_product_certifies_no_orbit():
    result = fx.ft09_through(77)
    fx.deliver(result, fx.GAME_OVER)  # a death before any lever is explained: G4-A emits with no answer
    level = fx.open_level(fx.compiled(result.machine, persist_reason="BUDGET_STOP"))
    (pid,) = [p for p, e in level["product_answers"].items() if e["gate_id"] == "G4.2-LEVER-ORBITS"]
    assert (level["product_answers"][pid]["origin"], level["product_answers"][pid]["basis"]) == (
        "UNATTRIBUTED", "NO_DECLARED_CLOSURE")
    for entity_id, dossier in level["lever_dossiers"].items():
        orbit = dossier["chapters"]["orbit"]
        assert orbit["status"] != "COMPLETE"
        assert {"kind": "PRODUCT_NOT_CERTIFYING", "product_id": pid, "origin": "UNATTRIBUTED",
                "basis": "NO_DECLARED_CLOSURE"} in orbit["open"]
    e0053 = fx.chapter(level, "E0053", "orbit")
    assert e0053["facts"]["run"]["steps"]  # the recorded steps stay, never a law


# ---- 22, 26 · an early stop keeps outcomes, contradictions and withdrawn models --------------------------------

def test_v6_22_an_early_stop_keeps_a_supported_and_a_contradicted_relation_test():
    from test_g4b_relations import _predict, _take, start_g4b

    machine, world = start_g4b()
    _predict(machine, "E0053")
    _take(machine, world)
    _predict(machine, "E0054", {"E0054": "UNCHANGED"})  # wrong: pressing E0054 steps its own tile
    _take(machine, world)
    level = fx.open_level(fx.compiled(machine, persist_reason="BUDGET_STOP"))
    assert not any(e["gate_id"] == RELATIONS for e in level["product_content"].values())
    tests = {t["prediction_id"]: t for t in fx.chapter(level, "E0054", "relations")["facts"]["tests"]}
    assert tests["P2"]["status"] == "CONTRADICTED" and tests["P2"]["evidence_ref"] in level["receipts"]["evidence"]
    assert fx.chapter(level, "E0053", "relations")["facts"]["tests"][0]["status"] == "SUPPORTED"
    relations = fx.chapter(level, "E0054", "relations")
    assert (relations["status"], relations["basis"]) == ("INTERRUPTED", "BUDGET_STOP")
    contradictions = fx.chapter(level, "E0054", "open_items")["facts"]["contradictions"]
    assert {"kind": "PREDICTION_CONTRADICTED", "chapter": "relations", "prediction_id": "P2",
            "evidence_ref": tests["P2"]["evidence_ref"]} in contradictions


@pytest.fixture(scope="module")
def withdrawn_model():
    from test_g4b_relations import _take, start_g4b
    from test_g4c_law import _described, _law

    machine, world = start_g4b()
    _described(machine, world)
    _law(machine, "E0055", {"E0055": "UNCHANGED"})
    _take(machine, world)  # contradicted: G4-B reopens and its product is invalidated
    return fx.compiled(machine, persist_reason="BUDGET_STOP")


def test_v6_26_a_withdrawn_description_leaves_active_relations_and_stays_a_rejected_model(withdrawn_model):
    level = fx.open_level(withdrawn_model)
    relations = fx.chapter(level, "E0053", "relations")
    assert relations["prior_basis"] == "REOPENED_BY_CONTRADICTION" and relations["facts"]["relations"] == []
    (withdrawn,) = relations["history"]
    assert (withdrawn["kind"], withdrawn["status"], withdrawn["reason"]) == (
        "WITHDRAWN_DESCRIPTION", "CONTRADICTED", "CONTRADICTED_BY_LAW_TEST")
    assert withdrawn["relations"][0]["levers"] == ["E0053", "E0054"] and withdrawn["relations"][0]["prediction_refs"] == ["P1"]
    assert withdrawn["contradiction"]["prediction_id"] == "L1"
    assert withdrawn["contradiction"]["evidence_ref"] in level["receipts"]["evidence"]
    assert withdrawn in fx.chapter(level, "E0053", "open_items")["facts"]["rejected_models"]
    law = {t["prediction_id"]: t for t in fx.chapter(level, "E0055", "law_tests")["facts"]["tests"]}
    assert law["L1"]["status"] == "CONTRADICTED"


# ---- 23-25 · integrity, the origin matrix and closures -------------------------------------------------------

def test_v6_23_a_complete_chapter_whose_evidence_breaks_fails_closed_with_its_prior_status():
    machine = _through(80)
    clean = fx.open_level(_compiled(("ft09", 80), machine, "RUN_END", reconcile=True))
    orbit = fx.chapter(clean, "E0053", "orbit")
    assert orbit["status"] == "COMPLETE"
    step = orbit["facts"]["run"]["steps"][0]["transition_id"]
    broken = fx.open_level(fx.compiled(machine, persist_reason="RUN_END", reconcile=True, rename={step: "ACTION1"}))
    failed = fx.chapter(broken, "E0053", "orbit")
    assert (failed["status"], failed["basis"], failed["prior_status"], failed["facts"]) == (
        "CLOSED_UNRESOLVED", "RECORD_MISMATCH", "COMPLETE", None)
    assert failed["integrity"]["status"] == "FAILED_CLOSED"
    limits = fx.chapter(broken, "E0053", "limits")  # the endpoint rests on the same presses
    assert (limits["status"], limits["basis"], limits["facts"]) == ("CLOSED_UNRESOLVED", "RECORD_MISMATCH", None)
    assert fx.chapter(broken, "E0053", "identity")["status"] == "COMPLETE"  # unaffected chapters stay


def test_v6_24_a_record_derived_relation_set_completes_the_relations_chapter():
    from test_g4b_relations import start_g4b

    machine, _world = start_g4b()  # every lever already has recorded presses (G4-A)
    effective = machine.prepare_answer({"answer_kind": "LEVER_RELATIONS_FROM_RECORD"})
    machine.submit_prepared(effective, executor="CONTROLLER")
    level = fx.open_level(fx.compiled(machine, persist_reason="LEVEL_ADVANCE"))
    (pid,) = [p for p, e in level["product_answers"].items() if e["gate_id"] == RELATIONS]
    assert level["product_answers"][pid]["basis"] == "RELATIONS_CERTIFIED_FROM_RECORD"
    relations = fx.chapter(level, "E0053", "relations")
    # revision 2 (blocker 2): the record is the submission source; the gate is the certifier
    submission = relations["facts"]["submission"]
    assert relations["status"] == "COMPLETE" and "certified_by" not in relations["facts"]
    assert (submission["submission_source"], submission["certifier"], submission["certification_origin"]) == (
        "RECORD", RELATIONS, "RELATIONS_CERTIFIED_FROM_RECORD")
    assert relations["facts"]["relations"][0]["kind"] == "RECORDED_EFFECTS"
    assert "claim" not in relations["facts"]["relations"][0] and relations["facts"]["relations"][0]["transitions"]


def test_v6_25_a_gate_derived_closure_never_completes_a_chapter():
    from test_g4b_relations import start_g4b

    machine, _world = start_g4b()
    machine._adapters[RELATIONS].close_unresolved("Duck's G4-B budget is spent (test)")
    model = fx.compiled(machine, persist_reason="LEVEL_ADVANCE")
    relations = fx.chapter(model, "E0053", "relations")
    assert (relations["status"], relations["basis"]) == ("CLOSED_UNRESOLVED", "PRODUCT_UNRESOLVED")
    forged = copy.deepcopy(model)
    fx.chapter(forged, "E0053", "relations").update(status="COMPLETE", basis="PRODUCT_CERTIFIED")
    _refused(forged, "COMPLETE")

    result = fx.ft09_through(77)
    fx.deliver(result, fx.LEVEL_UP)  # the level ends before any lever is explained: a GATE_DERIVED orbit closure
    frozen = result.machine.level_censuses[0]
    assert all(d["chapters"]["orbit"]["status"] != "COMPLETE" for d in frozen["lever_dossiers"].values())


# ---- guards ---------------------------------------------------------------------------------------------------

def test_v6_guard_compilation_leaves_the_gate_machine_byte_identical():
    from inference.framework.library_census import ExecutionRecord, compile_world_model

    machine = _through(80)
    before = pickle.dumps(machine)
    board = tuple(tuple(int(c) for c in row) for row in machine.ego._initial_grid)
    compile_world_model(machine, ExecutionRecord(board, 1, ("ACTION6",), ()), game_id="g", run_stem="g_p0",
                        persist_reason="BUDGET_STOP", reconcile_journal=False)
    assert pickle.dumps(machine) == before


def test_v6_guard_no_dossier_is_compiled_on_the_controller_path(monkeypatch):
    from inference.framework import lever_dossiers
    from inference.framework.card_builder import build_card
    from inference.framework.controller_executor import next_owned_step

    machine = copy.deepcopy(_through(80))
    monkeypatch.setattr(lever_dossiers, "attach", lambda *a, **k: pytest.fail("dossier compiled on the controller path"))
    next_owned_step(machine)
    build_card(machine)


def test_v6_digest_shows_chapter_counts_and_the_selected_lever_only_when_it_is_named(t80_model):
    from inference.framework.library_view import DIGEST_BUDGET, render_library_digest

    level_target = {"question_id": "Q:L1:G4.2-LEVER-ORBITS:LEVEL-1:LEVER_ORBITS", "gate_id": "G4.2-LEVER-ORBITS",
                    "subject": "LEVEL-1", "question": "Which states?", "level": 1}
    plain = render_library_digest(t80_model, target=level_target)
    assert "DOSSIERS x8" in plain and "SELECTED LEVER" not in plain and len(plain) <= DIGEST_BUDGET
    lever_target = {**level_target, "subject": "E0054", "question_id": "Q:L1:G3-LEVERS:E0054:IS_LEVER"}
    named = render_library_digest(t80_model, target=lever_target)
    assert "SELECTED LEVER E0054" in named and len(named) <= DIGEST_BUDGET
    assert "Which states?" in named  # the selected question stays


# ---- revision 2 on the records: event links, affected subjects, submitter and certifier --------------------------

WITNESS_EVENT = {"event_id": "EV-493a28ab61ba00ce", "transition_id": 58, "verb": "RECOLOR"}
WITNESS_TRACK = "O-L1-P1-E-9ba0bdad2bf9"


def test_v6_r2_20_an_anatomy_channel_links_its_exact_observed_events_and_its_affected_track(anatomy_model):
    level = fx.open_level(anatomy_model)
    (channel,) = fx.chapter(level, "E0053", "anatomy")["facts"]["channels"]
    assert channel["events"] == [WITNESS_EVENT] and channel["event_status"] == "LINKED"
    assert channel["subject"] == {"status": "EXACT_TRACK", "track_id": WITNESS_TRACK,
                                  "basis": {"key": "EXACT_EVENT_FOOTPRINT", "event_id": WITNESS_EVENT["event_id"],
                                            "transition_id": 58}}
    witness = next(t for t in level["description"]["transitions"] if t["transition_id"] == 58)
    masked = [e["event_id"] for e in witness["events"] if e["verb"] in ("SHRINK", "GROW")]  # the counter's change
    assert masked and not set(masked) & {e["event_id"] for e in channel["events"]}
    for dossier in level["lever_dossiers"].values():
        for item in dossier["chapters"]["anatomy"]["facts"]["channels"]:
            assert item["event_status"] in ("LINKED", "NO_MATCHING_EVENT", "TRANSITION_NOT_DESCRIBED")
            assert all(set(ref) == {"event_id", "transition_id", "verb"} for ref in item["events"])  # refs, no bodies


def test_v6_r2_21_page_and_report_render_event_links_and_the_affected_track(anatomy_model):
    from inference.framework import world_report
    from inference.framework.library_view import library_page
    from test_world_description import _assert_report_refs

    rows, offset = {}, 0
    while offset is not None:  # every page fits the page budget; ``next`` continues it
        page = library_page(anatomy_model, "dossiers", id="E0053", offset=offset, limit=10)
        rows.update({row["chapter"]: row for row in page["items"]})
        offset = page["offset"] + page["limit"] if page["next"] else None
    anatomy = rows["anatomy"]
    assert f"{WITNESS_EVENT['event_id']} RECOLOR t58" in anatomy["summary"] and WITNESS_TRACK in anatomy["summary"]
    text = world_report.render_world_report(anatomy_model)
    line = next(line for line in text.splitlines() if "dossier E0053 anatomy channel" in line)
    assert f"{WITNESS_EVENT['event_id']} RECOLOR t58" in line and WITNESS_TRACK in line
    assert WITNESS_EVENT["event_id"] in line.rsplit("refs: ", 1)[1]
    assert _assert_report_refs(anatomy_model, text) > 0


DUCK_CERTIFIED = re.compile(r"certified_by\W{0,4}DUCK|certified\s+by\s+duck\b", re.IGNORECASE)


def _surfaces(model: dict, entity_id: str) -> list[str]:
    from inference.framework import world_report
    from inference.framework.library_view import library_page, render_library_digest

    target = {"question_id": f"Q:L1:G3-LEVERS:{entity_id}:IS_LEVER", "gate_id": "G3-LEVERS", "subject": entity_id,
              "question": "Is it a lever?", "level": 1}
    pages, offset = [], 0
    while offset is not None:  # every page of the lever's dossier
        page = library_page(model, "dossiers", id=entity_id, offset=offset, limit=10)
        pages.append(json.dumps(page, sort_keys=True))
        offset = page["offset"] + page["limit"] if page["next"] else None
    assert any('"chapter": "relations"' in page for page in pages)
    return [*pages, render_library_digest(model, target=target), world_report.render_world_report(model)]


def test_v6_r2_22_no_surface_says_duck_certified_a_mechanic(described, withdrawn_model):
    model = fx.compiled(described, persist_reason="BUDGET_STOP")
    relations = fx.chapter(model, "E0053", "relations")
    assert relations["status"] == "COMPLETE" and "certified_by" not in relations["facts"]
    submission = relations["facts"]["submission"]
    assert (submission["certifier"], submission["certification_origin"]) == (RELATIONS, "ANSWER_CERTIFIED")
    (pid,) = [p for p, e in fx.open_level(model)["product_content"].items() if e["gate_id"] == RELATIONS]
    assert fx.open_level(model)["product_content"][pid]["payload"]["certified_by"] == "DUCK"  # frozen payload kept
    for surface in [*_surfaces(model, "E0053"), *_surfaces(withdrawn_model, "E0053")]:
        assert not DUCK_CERTIFIED.search(surface)
        assert '"certified_by"' not in surface
    (withdrawn,) = fx.chapter(withdrawn_model, "E0053", "relations")["history"]
    assert "certified_by" not in withdrawn and withdrawn["certifier"] == RELATIONS


@pytest.mark.parametrize("executor", ["DUCK", "CONTROLLER", None])
def test_v6_r2_23_the_answer_submitter_is_reconciled_with_the_journal_at_h2(described, executor, tmp_path):
    model = fx.compiled(described, persist_reason="RUN_END")
    relations = fx.chapter(model, "E0053", "relations")
    assert relations["facts"]["submission"]["status"] == "FAILED_CLOSED"  # H2 without a journal: never DUCK by default
    answer_id = relations["facts"]["description"]["answer_id"]
    extra = [] if executor is None else [pf.answer_row(executor, RELATIONS, answer_id)]
    sealed = pf.sealed(model, pf.journal(tmp_path, executions=(), extra=extra))
    relations = fx.chapter(sealed, "E0053", "relations")
    submission = relations["facts"]["submission"]
    assert relations["status"] == "COMPLETE" and relations["facts"]["tests"]  # the certified facts stay
    if executor is None:
        assert (submission["submission_source"], submission["status"], submission["basis"]) == (
            None, "FAILED_CLOSED", "ANSWER_ADMISSION_MISSING")
        assert {"kind": "PROVENANCE_INCOMPLETE", "field": "ANSWER_SUBMITTER", "basis": "ANSWER_ADMISSION_MISSING",
                "answer_id": answer_id} in relations["open"]
    else:
        (row,) = [r for r in sealed["provenance"]["rows"] if r["operation"] == "ANSWER"]
        assert (submission["submission_source"], submission["status"], submission["basis"],
                submission["answer_event_id"]) == (executor, "VERIFIED", "ANSWER_ADMISSION", row["event_id"])
        assert not [item for item in relations["open"] if item["kind"] == "PROVENANCE_INCOMPLETE"]
    assert submission["certifier"] == RELATIONS


def test_v6_r2_24_remote_channels_link_several_events_and_never_guess_a_subject():
    model = _compiled(("carry",), _shared(("carry",), fx.carry_v7).machine, "RUN_END")
    channels = fx.chapter(model["levels"][0], "E0004", "anatomy")["facts"]["channels"]
    assert {channel["locality"] for channel in channels} == {"REMOTE"}
    assert all(channel["event_status"] == "LINKED" for channel in channels)
    several = max(channels, key=lambda channel: len(channel["events"]))
    assert len(several["events"]) >= 2 and len({ref["transition_id"] for ref in several["events"]}) == 1
    for channel in channels:  # each residue spans more than one object's footprint: no exact, unique match
        assert channel["subject"] == {"status": "UNRESOLVED_REGION", "reason": "NO_EXACT_MATCH"}
    unavailable = fx.chapter(model["levels"][0], "E0004", "open_items")["facts"]["unavailable"]
    assert "AFFECTED_SUBJECT_IDENTITY" in unavailable and "CROSS_LEVEL_LIMITS" in unavailable


# ---- WO-G4-DOSSIER-B · B1 on the records: derived state, persistence and reversal ------------------------------

def test_b1_10_ft09_levers_hold_under_other_presses_and_only_this_lifes_evidence_counts(described):
    from inference.framework import lever_dossier_state

    """The record dies once (life 1 -> 2) before G4-B: everything is read from life 2 alone (Sol's ruling 3).

    Revision 2 (Sol's review): life 2 opens at the reset t89, so its entry board is the board after that reset and no
    state of life 1 is a state of life 2. Revision 1 read E0053's one life-2 press as a toggle back to the state the
    death left: a leak across lives. Recomputed, E0053, E0054 and E0055 each owe reversal (B3's real-record cases)."""
    model = fx.compiled(described, persist_reason="BUDGET_STOP")
    level = fx.open_level(model)
    owed_reversal, phased = set(), set()
    for entity, dossier in sorted(level["lever_dossiers"].items()):
        observations = dossier["observations"]
        persistence, reversal, state = observations["persistence"], observations["reversal"], observations["current_region_state"]
        assert observations["scope"]["life"] == 2 and observations["scope"]["level"] == 1
        assert observations["scope"]["entry_reset"] == 89 and 89 not in lever_dossier_state.cited_transitions(observations)
        assert (persistence["status"], persistence["changed"]) == ("TESTED", 0) and persistence["unchanged"] >= 20
        assert reversal["self_recurrence"]["status"] == "NOT_OBSERVED"  # a two-state lever never recurs longer
        assert reversal["cross_reversal"]["status"] == "NOT_OBSERVED" and reversal["cross_reversal"]["tested"] > 0
        limits, items = dossier["chapters"]["limits"], dossier["chapters"]["open_items"]["facts"]
        assert limits["facts"]["persistence"] == "OBSERVED" and "LIMITS_PERSISTENCE" not in items["probe_owed"]
        assert (limits["status"], limits["basis"], limits["prior_status"]) == ("INTERRUPTED", "BUDGET_STOP", "IN_PROGRESS")
        if reversal["toggle_reversal"]["status"] == "OBSERVED":
            assert limits["facts"]["reversal"] == "OBSERVED" and "LIMITS_REVERSAL" not in items["probe_owed"]
            assert limits["prior_basis"] == "RECORD_OBSERVED_NOT_GATE_CERTIFIED"  # nothing left to probe
        else:  # pressed once in this life: no return seen, so an experiment is still owed (B3's evidence)
            owed_reversal.add(entity)
            assert reversal["toggle_reversal"]["tested"] == 1 and not reversal["toggle_reversal"]["cases"]
            assert limits["facts"]["reversal"] == "PROBE_OWED" and "LIMITS_REVERSAL" in items["probe_owed"]
            assert limits["prior_basis"] == "ENDPOINT_OBSERVED_PROBES_OWED"
        if state["phase_basis"] == "EXACT_ORBIT_MAPPING":
            phased.add(entity)
            assert state["orbit_phase"]["period"] == 2 and "ORBIT_PHASE_NOW" not in items["unavailable"]
        else:  # its accepted run lies in life 1: never carried into life 2
            assert (state["phase_basis"], state["orbit_phase"]) == ("ORBIT_OUTSIDE_SCOPE", None)
            assert "ORBIT_PHASE_NOW" in items["unavailable"]
    assert owed_reversal == {"E0053", "E0054", "E0055"} and phased == {"E0056", "E0057", "E0060", "E0061", "E0062"}


def test_b1_11_a_death_starts_an_empty_life_that_carries_nothing():
    result = fx.ft09_through(77)
    fx.deliver(result, fx.GAME_OVER)
    level = fx.open_level(fx.compiled(result.machine, persist_reason="BUDGET_STOP"))
    for dossier in level["lever_dossiers"].values():
        observations = dossier["observations"]
        assert observations["scope"]["life"] == 2 and observations["scope"]["as_of_transition"] is None
        assert observations["persistence"]["status"] == "UNTESTED" and observations["persistence"]["tested"] == 0
        assert all(item["status"] == "UNTESTED" for item in observations["reversal"].values())
        assert observations["current_region_state"]["orbit_phase"] is None
        owed = dossier["chapters"]["open_items"]["facts"]["probe_owed"]
        assert "LIMITS_PERSISTENCE" in owed and "LIMITS_REVERSAL" in owed  # absent evidence stays owed


def test_b1_12_h1_freezes_the_observations_and_h2_keeps_them_byte_identical():
    from inference.framework import lever_dossier_state
    from inference.framework.library_census import freeze_level_census

    census = freeze_level_census(copy.deepcopy(_through(79)), level_before=1)
    frozen = census["lever_dossiers"]["E0053"]["observations"]
    assert frozen["status"] == "OBSERVED" and frozen["scope"] == {**frozen["scope"], "level": 1, "life": 1}
    carried = _compiled(("carry",), _shared(("carry",), fx.carry_v7).machine, "RUN_END")
    stored = carried["levels"][0]["lever_dossiers"]
    census_time = _shared(("carry",), fx.carry_v7).machine.level_censuses[0]["lever_dossiers"]
    for entity, dossier in stored.items():
        assert dossier["observations"]["scope"] == census_time[entity]["observations"]["scope"]
        assert dossier["observations"]["persistence"] == census_time[entity]["observations"]["persistence"]
    resealed = _wm().seal(copy.deepcopy(carried))
    assert _wm().canonical_bytes(resealed) == _wm().canonical_bytes(carried)
    assert lever_dossier_state.CATEGORIES == ("toggle_reversal", "self_recurrence", "cross_reversal", "other_return")


def test_b1_13_the_live_view_derives_observations_without_touching_the_machine():
    from inference.framework.library_view import _CACHE, live_model

    machine = copy.deepcopy(_through(80))
    before = pickle.dumps(machine)
    _CACHE.clear()
    model = live_model(machine)
    assert pickle.dumps(machine) == before
    assert model["manifest"]["persist_reason"] == "LIVE_VIEW"
    assert fx.open_level(model)["lever_dossiers"]["E0053"]["observations"]["status"] == "OBSERVED"


def test_b1_14_page_and_report_render_the_observations(t80_model):
    from inference.framework import world_report
    from test_world_description import _assert_report_refs

    text = world_report.render_world_report(t80_model)
    line = next(line for line in text.splitlines() if "dossier E0053 observations" in line)
    assert "persistence TESTED" in line and "toggle reversal" in line
    assert _assert_report_refs(t80_model, text) > 0


# ---- WO-G4-DOSSIER-B · B1 revision 2 (Sol's review): every observation line cites its canonical path -----------

def _observation_lines(text: str) -> dict[str, str]:
    return {match.group(1): line for line in text.splitlines()
            for match in [re.search(r"dossier (\S+) observations: ", line)] if match}


def test_b1_20_a_persistence_only_observation_line_cites_its_canonical_path(described):
    """A lever with persistence tested but no changed trial and no reversal case names no evidence id outright; its
    report line is supported by the observations it renders, cited by their canonical path."""
    from inference.framework import lever_dossier_state, world_report
    from test_world_description import _assert_report_refs

    model = fx.compiled(described, persist_reason="BUDGET_STOP")
    index = len(model["levels"]) - 1
    level = model["levels"][index]
    quiet = sorted(entity for entity, dossier in level["lever_dossiers"].items()
                   if dossier["observations"]["status"] == "OBSERVED"
                   and dossier["observations"]["persistence"]["tested"] > 0
                   and not lever_dossier_state.evidence_refs(dossier["observations"]))
    assert quiet  # the record holds a persistence-only lever (no reversal case, no changed trial)
    text = world_report.render_world_report(model)
    lines = _observation_lines(text)
    assert set(lines) == set(level["lever_dossiers"])
    for entity, line in lines.items():
        refs = line.rsplit("refs: ", 1)[1].split(", ")
        assert f"levels[{index}].lever_dossiers[{entity}].observations" in refs, line
    assert "persistence TESTED" in lines[quiet[0]]
    assert _assert_report_refs(model, text) > 0


def test_b1_21_the_reference_checker_refuses_another_levers_or_levels_observation_path(described):
    from inference.framework import world_report
    from test_world_description import _assert_report_refs

    model = fx.compiled(described, persist_reason="BUDGET_STOP")
    index = len(model["levels"]) - 1
    text = world_report.render_world_report(model)
    entities = sorted(_observation_lines(text))
    own, other = (f"levels[{index}].lever_dossiers[{entity}].observations" for entity in entities[:2])
    line = _observation_lines(text)[entities[0]]
    for forged in (other, f"levels[{index + 1}].lever_dossiers[{entities[0]}].observations",
                   f"levels[{index}].lever_dossiers[E9999].observations"):
        with pytest.raises(AssertionError):
            _assert_report_refs(model, text.replace(line, line.replace(own, forged)))
    with pytest.raises(AssertionError):  # the observation line must cite its own path
        _assert_report_refs(model, text.replace(line, line.replace(f", {own}", "")))
