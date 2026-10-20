"""WO-WIN-01: the observed-win episode in the semantic library (world model v10, frozen v9).

Author: Claude (Alpha build seat), 2026-10-19 (INTERFACE_WO_WIN_01_v1). Written before any WIN-01 edit and run
fail-first on ``40940a8``. The positive case is real: the committed carry-v7 record, replayed through the
production gate path, clears level 1 at t26 (``ACTION6`` at row 32, col 60; evidence ``E-389ff8759efd3ffc``). The
death, reset and controlled-stop cases are real runs (the ft09 G4-B record continued on its offline world; carry-v7
cut short). Boundary attacks are labelled doubles: each changes only the stored episode (or one level field) and
recomputes the model's content hash, the only seal a forger must reach.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import pickle
from pathlib import Path

import pytest

import dossier_fixtures as fx

FIXTURES = Path(__file__).parent / "fixtures"
V9_MODEL = FIXTURES / "world_model_v9_frozen.json.gz"
WIN = 26
EVIDENCE = "E-389ff8759efd3ffc"
PRE_BOARD = "f14cacc2ea85995e"
POST_BOARD = "63ff750b20b7f013"
_CACHE: dict[str, bytes] = {}


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _W():
    from inference.framework import win_episode

    return win_episode


def _carry():
    """(machine, the H2 model, journal reconciled) of the full carry-v7 record."""
    if "carry" not in _CACHE:
        machine = fx.carry_v7().machine
        _CACHE["carry"] = pickle.dumps((machine, fx.compiled(machine, persist_reason="RUN_END", reconcile=True)))
    return pickle.loads(_CACHE["carry"])


def _episode(model, level=1):
    return next(item for item in model["levels"] if item["level"] == level)["win_episode"]


def _forged(model, mutate):
    """A labelled double: ``mutate(episode, model)`` changes the stored episode; the content hash is recomputed."""
    out = copy.deepcopy(model)
    mutate(out["levels"][0]["win_episode"], out)
    out["content_sha256"] = _wm().content_sha256(out)
    return out


def _refused(model, match):
    with pytest.raises(_wm().WorldModelV2Error, match=match):
        _wm().read_world_model(model)


# ---- 1-5 · the real level clear -------------------------------------------------------------------------------------

def test_w01_a_real_carry_v7_level_clear_produces_one_observed_episode():
    _machine, model = _carry()
    W = _W()
    states = [(level["level"], level["state"], level["win_episode"]["state"]) for level in model["levels"]]
    assert states == [(1, "FROZEN", "OBSERVED_PARTLY_EXPLAINED"), (2, "OPEN", "NOT_OBSERVED")]
    episode = _episode(model)
    assert episode["schema"] == W.EPISODE_SCHEMA
    assert episode["boundary"]["kind"] == "LEVEL_CLEAR" and episode["boundary"]["state"] == "NOT_FINISHED"
    assert (episode["boundary"]["level_before"], episode["boundary"]["level_after"]) == (1, 2)
    assert episode["limits"]["claim"] == "RETROSPECTIVE_ONLY" and episode["limits"]["observations"] == 1
    _wm().read_world_model(model)


def test_w02_the_episode_uses_the_winning_life_only():
    machine, model = _carry()
    episode = _episode(model)
    assert episode["identity"]["life"] == episode["boundary"]["life"] == 1
    assert episode["window"]["opened_by"] == {"kind": "INITIAL_FRAME", "after_transition": 0}
    assert episode["window"]["prior_lives"] == []
    level = model["levels"][0]
    lives = {r["transition_id"]: r["life"] for r in level["description"]["transitions"]}
    assert [item["transition_id"] for item in episode["transitions"]] == list(range(1, WIN))  # r2: the clear is apart
    assert {lives[item["transition_id"]] for item in episode["transitions"]} == {1}
    assert episode["window"]["actions"] == WIN and episode["window"]["first_transition"] == 1
    assert (episode["window"]["semantic_transitions"], episode["window"]["clear_transition"]) == (WIN - 1, WIN)
    assert [life["life"] for life in machine.lives.summary() if WIN in (life.get("level_changes") or ())] == [1]


def test_w03_the_terminal_action_and_receipt_resolve_exactly():
    _machine, model = _carry()
    episode, level = _episode(model), model["levels"][0]
    identity = episode["identity"]
    assert identity["winning_transition"] == episode["boundary"]["transition_id"] == WIN
    assert identity["terminal_action"] == {"action": "ACTION6", "col": 60, "row": 32}
    assert identity["evidence_ref"] == EVIDENCE and identity["actor"] == "G4.2-LEVER-ORBITS"
    assert episode["clear"]["transition_id"] == WIN
    assert level["receipts"]["evidence"][EVIDENCE]["transition_id"] == WIN
    assert identity["receipt"] == {"gate_id": "G4.2-LEVER-ORBITS", "probe_id": "G4.2-LEVER-ORBITS:GUIDED:11"}


def test_w04_the_final_transition_is_included_once():
    """Revision 2 (Sol): the clear is included once, as the boundary, never as a listed transformation."""
    _machine, model = _carry()
    episode = _episode(model)
    ids = [item["transition_id"] for item in episode["transitions"]]
    assert WIN not in ids and ids[-1] == WIN - 1
    assert (episode["identity"]["winning_transition"], episode["clear"]["transition_id"],
            episode["window"]["clear_transition"], episode["boundary"]["transition_id"]) == (WIN, WIN, WIN, WIN)


def test_w05_the_next_levels_entry_is_excluded():
    _machine, model = _carry()
    episode, level, nxt = _episode(model), model["levels"][0], model["levels"][1]
    assert nxt["entry"] == {**nxt["entry"], "source": "LEVEL_ENTRY", "after_transition": WIN}
    assert episode["boundary"]["successor_entry_sha256"] == nxt["entry"]["board_sha256"]
    assert episode["boundary"]["successor_entry_sha256"].startswith(POST_BOARD)
    assert episode["boundary"]["pre_board_sha256"].startswith(PRE_BOARD)
    assert episode["clear"]["visual_status"] == "SUCCESSOR_SPAWN_NOT_WINNING_RENDER"
    assert not any(p["track_id"].startswith(f"O-L1-P1-T{WIN}-") for p in episode["participants"])  # r2: spawn apart
    tracks = {t["track_id"] for t in level["observation"]["tracks"]}
    later = {t["track_id"] for t in nxt["observation"]["tracks"]}
    named = {p["track_id"] for p in episode["participants"]}
    assert named <= tracks and not named & later
    assert all(item["transition_id"] <= WIN for item in episode["transitions"])


# ---- 6-8 · no clear, no episode ------------------------------------------------------------------------------------

def _states(model):
    return [(level["level"], level["state"], level["win_episode"]["state"]) for level in model["levels"]]


def test_w06_a_death_produces_no_win_episode():
    import test_lever_experiments as T
    from test_g4_selection_persisted import _unsealed

    machine, _world, death, _reset = T._died()
    assert [row["boundary_state"] for row in machine.transition_index if row["transition_id"] == death] == ["GAME_OVER"]
    assert machine.level_censuses == []
    model = _wm().seal(_unsealed(machine))
    assert _states(model) == [(1, "OPEN", "NOT_OBSERVED")]
    _wm().validate(model)


def test_w07_a_harness_reset_produces_no_win_episode():
    import test_lever_experiments as T
    from test_g4_selection_persisted import _unsealed

    machine, _world = T._opening()
    resets = [row for row in machine.transition_index if row.get("kind") == "RESET"]
    assert resets and machine.level_censuses == []
    model = _wm().seal(_unsealed(machine))
    assert _states(model) == [(1, "OPEN", "NOT_OBSERVED")]
    assert [b["kind"] for r in model["levels"][0]["description"]["transitions"] if (b := r["boundary"])] == \
        ["RESET"] * len(resets)


def test_w08_a_controlled_stop_produces_no_win_episode():
    from inference.framework.record_replay import load_record, replay

    machine = replay(load_record(fx.CARRY_V7), max_steps=WIN - 1, measure=False).machine
    model = fx.compiled(machine, persist_reason="BUDGET_STOP", reconcile=True)
    assert _states(model) == [(1, "OPEN", "NOT_OBSERVED")]
    assert model["manifest"]["persist_reason"] == "BUDGET_STOP"
    _wm().read_world_model(model)


# ---- 9-14 · identity, roles, events and explanations ------------------------------------------------------------

def test_w09_a_clear_with_unresolved_identity_keeps_the_track_handle_and_the_gap():
    W = _W()
    _machine, model = _carry()
    episode = _episode(model)
    by_track = {p["track_id"]: p for p in episode["participants"]}
    # real: the lever tracks are AMBIGUOUS only at the clear, whose events are a boundary delta (r2): no gap is drawn
    # from the successor spawn; both keep their handle and bindings
    for track in ("O-L1-P1-E-eaa42db11f57", "O-L1-P1-E-422caa01b5cd"):
        assert by_track[track]["identity_gaps"] == [] and by_track[track]["kind"] == "BOUND_ROLE"
    # labelled double: an unbound track whose pre-clear sighting is ambiguous becomes an unresolved region, handle kept
    level = copy.deepcopy(model["levels"][0])
    subject = "O-L1-P1-E-c5ddda4439c0"
    for event in level["description"]["transitions"][WIN - 2]["events"]:
        if event["subject"]["track_id"] == subject:
            event["correspondence"]["ambiguity"] = "MULTIPLE_LICENSED_SUCCESSORS"
    derived = {p["track_id"]: p for p in W.derive(level, episode["boundary"])["participants"]}
    assert derived[subject]["kind"] == "UNRESOLVED_REGION" and derived[subject]["roles"] == []
    assert derived[subject]["identity_gaps"] == [{"reason": "AMBIGUOUS_CORRESPONDENCE", "transitions": [WIN - 1]}]
    assert subject in W.derive(level, episode["boundary"])["limits"]["identity_gaps"]


def test_w10_certified_roles_are_rendered_only_through_bindings():
    W = _W()
    _machine, model = _carry()
    episode, level = _episode(model), model["levels"][0]
    bound = {(b["track_id"], b["role"], b["role_ref"]) for b in level["description"]["role_bindings"]}
    stated = {(p["track_id"], r["role"], r["role_ref"]) for p in episode["participants"] for r in p["roles"]}
    assert stated == bound == {("O-L1-P1-E-eaa42db11f57", "LEVER", "E0004"), ("O-L1-P1-E-422caa01b5cd", "LEVER", "E0005")}
    assert {p["kind"] for p in episode["participants"] if not p["roles"]} <= {"TRACK", "UNRESOLVED_REGION"}
    assert episode["limits"]["unbound_roles"] == [{"role": "COUNTER", "gate_id": "G2-COUNTER"},
                                                  {"role": "EGO", "gate_id": "G1-EGO"}]
    # labelled double: without bindings no participant holds a role, whatever the certified list or a G3 join says
    unbound = copy.deepcopy(level)
    unbound["description"]["role_bindings"] = []
    derived = W.derive(unbound, episode["boundary"])
    assert all(p["roles"] == [] and p["kind"] != "BOUND_ROLE" for p in derived["participants"])
    assert {p["g3_join"] for p in derived["participants"]} >= {"E0004", "E0005"}


def test_w11_every_transformation_resolves_to_a_descriptive_event():
    _machine, model = _carry()
    episode, level = _episode(model), model["levels"][0]
    ledger = {e["event_id"]: (r["transition_id"], e["subject"]["track_id"], e["verb"])
              for r in level["description"]["transitions"] if r["transition_id"] < WIN for e in r["events"]}
    listed = [(item["transition_id"], e["event_id"], e["track_id"], e["verb"])
              for item in episode["transitions"] for e in item["events"]]
    assert len(listed) == len(ledger) == len({e for _t, e, _k, _v in listed})
    assert all(ledger[event] == (t, track, verb) for t, event, track, verb in listed)
    assert {verb for *_x, verb in listed} <= {"STILL", "RECOLOR", "MOVE", "GROW", "SHRINK", "BIRTH", "DEATH", "DEFORM",
                                              "AMBIGUOUS"}  # the nine verbs; never SPLIT or MERGE
    terminal = [e["event_id"] for r in level["description"]["transitions"] if r["transition_id"] == WIN for e in r["events"]]
    assert episode["clear"]["boundary_delta"]["event_ids"] == terminal  # r2: the clear's events, kept for audit only


def test_w12_explanation_statuses_agree_with_the_stored_description():
    _machine, model = _carry()
    episode, level = _episode(model), model["levels"][0]
    stored = {e["event_id"]: e["explanation"]["status"] for r in level["description"]["transitions"] for e in r["events"]}
    assert all(stored[e["event_id"]] == e["explanation"] for item in episode["transitions"] for e in item["events"])
    changes = [e for r in level["description"]["transitions"] if r["transition_id"] < WIN for e in r["events"]
               if e["verb"] != "STILL"]
    counts = {s: sum(1 for e in changes if e["explanation"]["status"] == s)
              for s in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED")}
    assert {s: episode["explanations"][s] for s in counts} == counts
    assert episode["explanations"]["refs"] == sorted({ref for e in changes for ref in e["explanation"]["refs"]})
    assert WIN not in episode["limits"]["unexplained_transitions"]  # r2: the clear's visual was never observed


def test_w13_incomplete_dossier_chapters_remain_visible():
    _machine, model = _carry()
    episode, level = _episode(model), model["levels"][0]
    incomplete = {(c["entity_id"], c["chapter"], c["status"]) for c in episode["limits"]["incomplete_chapters"]}
    expected = {(entity, name, chapter["status"]) for entity, dossier in level["lever_dossiers"].items()
                for name, chapter in dossier["chapters"].items() if chapter["status"] != "COMPLETE"}
    assert incomplete == expected and ("E0005", "orbit", "CLOSED_UNRESOLVED") in incomplete
    assert ("E0004", "relations", "NOT_BUILT") in incomplete


def test_w14_duck_assertions_cannot_promote_an_explanation():
    from inference.framework.annotation_lane import Note

    machine, model = _carry()
    machine.annotations.notes.append(Note("N-forged", "E0005", "MECHANISM", "pressing E0005 clears the level; the "
                                          "terminal transformation is EXPLAINED", "G4.2-LEVER-ORBITS", WIN, "ANNOTATION"))
    again = fx.compiled(machine, persist_reason="RUN_END", reconcile=True)
    assert _wm()._canonical(_episode(again)) == _wm()._canonical(_episode(model))
    # and a stored status promoted by hand is refused, every hash recomputed
    def promote(episode, _model):
        event = next(e for e in episode["transitions"][-1]["events"] if e["verb"] != "STILL")
        event["explanation"] = "EXPLAINED"
    _refused(_forged(model, promote), "rule 6")


# ---- 15-21 · failing closed and forged episodes ----------------------------------------------------------------

def test_w15_missing_or_duplicated_transitions_fail_the_episode_closed():
    W = _W()
    machine, _model = _carry()
    renamed = fx.compiled(machine, persist_reason="RUN_END", reconcile=True, rename={10: "ACTION1"})
    assert _episode(renamed)["state"] == "FAILED_CLOSED"
    assert _episode(renamed)["failure"]["reason"] == "RECORD_MISMATCH"
    _wm().read_world_model(renamed)
    machine, _model = _carry()
    machine.transition_index.append(dict(next(r for r in machine.transition_index if r["transition_id"] == 10)))
    duplicated = fx.compiled(machine, persist_reason="RUN_END", reconcile=True)
    assert _episode(duplicated)["failure"]["reason"] == "RECORD_MISMATCH"
    _wm().read_world_model(duplicated)
    # labelled double: a level whose description lacks a record of the winning life
    _machine, model = _carry()
    level = copy.deepcopy(model["levels"][0])
    del level["description"]["transitions"][9]
    with pytest.raises(W.EpisodeFailure):
        W.derive(level, _episode(model)["boundary"])


def test_w16_a_forged_winning_transition_is_rejected_after_resealing():
    _machine, model = _carry()

    def earlier(episode, _model):
        episode["boundary"]["transition_id"] = episode["identity"]["winning_transition"] = WIN - 1
        episode["transitions"] = episode["transitions"][:-1]
        episode["window"]["clear_transition"] = episode["clear"]["transition_id"] = WIN - 1
    _refused(_forged(model, earlier), r"rule (2|10)")

    def not_a_clear(episode, _model):
        episode["boundary"]["kind"] = "GAME_OVER"
    _refused(_forged(model, not_a_clear), "rule 2")

    def hidden(episode, out):  # the recorded clear may not be hidden as NOT_OBSERVED
        out["levels"][0]["win_episode"] = {"schema": episode["schema"], "state": "NOT_OBSERVED"}
    _refused(_forged(model, hidden), "the record shows this level's clear")


def test_w17_a_forged_terminal_receipt_is_rejected():
    _machine, model = _carry()
    other = model["levels"][0]["description"]["transitions"][WIN - 2]["evidence_ref"]

    def receipt(episode, _model):
        episode["identity"]["evidence_ref"] = other
    _refused(_forged(model, receipt), "rule 3")

    def action(episode, _model):
        episode["identity"]["terminal_action"] = {"action": "ACTION6", "col": 0, "row": 0}
    _refused(_forged(model, action), "rule 3")


def test_w18_a_forged_participant_role_is_rejected():
    _machine, model = _carry()

    def role(episode, _model):
        item = next(p for p in episode["participants"] if p["kind"] == "TRACK")
        item["kind"], item["roles"] = "BOUND_ROLE", [{"role": "EGO", "gate_id": "G1-EGO", "role_ref": "EGO",
                                                      "ends_at_transition": None}]
    _refused(_forged(model, role), "rule 7")

    def unbound(episode, _model):
        item = next(p for p in episode["participants"] if p["kind"] == "BOUND_ROLE")
        item["kind"], item["roles"] = "TRACK", []
    _refused(_forged(model, unbound), "rule 7")


def test_w19_a_forged_explanation_reference_is_rejected():
    _machine, model = _carry()

    def reference(episode, _model):
        episode["explanations"]["refs"] = sorted(episode["explanations"]["refs"] + ["COUNTER-forged"])
    _refused(_forged(model, reference), "rule 8")

    def count(episode, _model):
        episode["explanations"]["EXPLAINED"] += 1
        episode["state"] = "OBSERVED"
    _refused(_forged(model, count), "rule 12")


def test_w20_cross_life_evidence_is_rejected():
    _machine, model = _carry()

    def life(episode, _model):
        episode["boundary"]["life"] = episode["identity"]["life"] = 2
    _refused(_forged(model, life), "rule 5")


def test_w21_cross_level_evidence_is_rejected():
    _machine, model = _carry()
    later = model["levels"][1]["observation"]["tracks"][0]["track_id"]

    def participant(episode, _model):
        episode["participants"].append({"track_id": later, "kind": "TRACK", "roles": [], "g3_join": None,
                                        "identity_gaps": [], "events": 1})
    _refused(_forged(model, participant), "rule 11")

    def transition(episode, _model):
        episode["transitions"].append({**episode["transitions"][-1], "transition_id": WIN + 1})
    _refused(_forged(model, transition), "rule 10")

    def board(episode, _model):
        episode["boundary"]["successor_entry_sha256"] = episode["boundary"]["pre_board_sha256"]
    _refused(_forged(model, board), "rule 9")


# ---- 22-24 · schema v10, frozen v9, determinism ---------------------------------------------------------------

def test_w22_the_frozen_v9_fixture_from_40940a8_reads_unchanged():
    wm = _wm()
    raw = gzip.decompress(V9_MODEL.read_bytes())
    v9 = json.loads(raw)
    assert (wm.SCHEMA, wm.V9_SCHEMA) == ("virelai-world-model-v10", "virelai-world-model-v9")
    assert v9["schema"] == wm.V9_SCHEMA and [level["state"] for level in v9["levels"]] == ["FROZEN", "OPEN"]
    assert not any("win_episode" in level for level in v9["levels"])  # v9 holds a clear but no episode
    wm.validate_v9(v9)
    assert wm.read_world_model(v9)["schema"] == wm.V9_SCHEMA
    assert wm._canonical(v9) == raw  # read back unchanged: the bytes 40940a8 wrote
    with pytest.raises(wm.WorldModelV2Error, match="schema must be virelai-world-model-v10"):
        wm.validate(v9)  # the v10 contract is never applied to a v9 artifact


def test_w23_v9_refuses_v10_at_the_schema_boundary():
    wm = _wm()
    _machine, model = _carry()
    assert model["schema"] == wm.SCHEMA
    with pytest.raises(wm.WorldModelV2Error, match="schema must be virelai-world-model-v9"):
        wm.validate_v9(model)
    with pytest.raises(wm.WorldModelV2Error, match="unknown world model schema"):
        wm.read_world_model({**model, "schema": "virelai-world-model-v11"})


def test_w24_deterministic_recompilation_is_byte_identical():
    machine, model = _carry()
    again = fx.compiled(machine, persist_reason="RUN_END", reconcile=True)
    assert _wm().canonical_bytes(again) == _wm().canonical_bytes(model)
    _wm().read_world_model(json.loads(_wm().canonical_bytes(model)))  # as written to disk: no order-dependent field
    # the H1 episode and the episode H2 re-derived from the settled level are the same bytes
    assert _wm()._canonical(machine.level_censuses[0]["win_episode"]) == _wm()._canonical(_episode(model))
    level = model["levels"][0]
    assert _wm()._canonical(_W().derive(level, _episode(model)["boundary"])) == _wm()._canonical(_episode(model))


# ---- 25-28 · Duck's surface and the action path ------------------------------------------------------------------

def test_w25_world_report_references_resolve():
    from inference.framework import world_report
    from test_world_description import _assert_report_refs

    _machine, model = _carry()
    text = world_report.render_world_report(model)
    assert "### Win episode" in text
    lines = text.split("### Win episode", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
    assert "one retrospective observation, not a winning rule" in lines and f"t1-t{WIN - 1}" in lines
    assert EVIDENCE in lines and "levels[0].win_episode" in lines
    assert _assert_report_refs(model, text) > 20


def test_w26_the_digest_retains_the_selected_question():
    from inference.framework.library_agenda import selected_target
    from inference.framework.library_view import DIGEST_BUDGET, library_digest, library_page, live_model, render_library_digest

    machine, _model = _carry()
    model = live_model(machine)
    target = selected_target(machine)
    text = render_library_digest(model, target=target)
    digest = library_digest(model, target=target)
    assert len(text) <= DIGEST_BUDGET and digest["goal"]["question"] in text
    assert digest["win"] == [f"L1 cleared at t{WIN} by ACTION6(32,60) in life 1 after {WIN} actions; the preceding "
                             "life is partly explained; the game immediately supplied level 2's entry board, so no "
                             "winning render was observed; one retrospective observation: "
                             "virelai('library', kind='win_episode', level=1)"]
    assert not any(word in text.lower() for word in ("strategy", "how to win", "repeat", "will win", "winning rule"))
    # the win line is the first thing to go when the section is tight; the selected question never is
    tight = len(text) - 1
    smaller = library_digest(model, tight, target=target)
    assert "win" not in smaller and smaller["goal"]["question"] == digest["goal"]["question"]
    page = library_page(model, "win_episode", level=1)
    assert page["episode"]["state"] == "OBSERVED_PARTLY_EXPLAINED" and page["total"] == WIN - 1
    assert page["items"][0]["transition_id"] == 1 and len(json.dumps(page)) <= 3_000


def test_w26b_the_guarded_carry_v7_digest_differs_only_by_the_win_line():
    """The DUCK_VIEWS_AFE93C8 guard's old digest hash is recovered byte for byte once the one added key is removed."""
    from inference.framework import library_view as V

    machine, _model = _carry()
    model = V.live_model(machine)
    rev = model["content_sha256"][:12]
    digest = V.library_digest(model)
    assert "win" in digest
    old = V._render({key: value for key, value in digest.items() if key != "win"})
    assert hashlib.sha256(old.replace(rev, "<REVISION>").encode()).hexdigest() == \
        "bb268bff3fbd383130b8690ff36111549ed8815a3546915640f05158be15295b"


def test_w27_no_episode_compilation_occurs_on_a_controller_step(monkeypatch):
    W = _W()
    calls = {"attach": 0, "derive": 0, "reconcile": 0}
    for name in calls:
        original = getattr(W, name)
        monkeypatch.setattr(W, name, lambda *a, _o=original, _n=name, **k: calls.__setitem__(_n, calls[_n] + 1) or _o(*a, **k))
    result = fx.carry_v7()
    assert result.steps_replayed == WIN
    assert calls == {"attach": 1, "derive": 1, "reconcile": 0}  # once, at the level change: never per step


def test_w28_the_g3_and_g4_no_choice_goldens_remain_byte_identical():
    from g3_no_choice_trace import GOLDEN as G3, RECORDS, no_choice_trace
    from g4_no_choice_trace import GOLDEN as G4, traces

    assert no_choice_trace(RECORDS["carry_v7"]) == json.loads(G3.read_text())["carry_v7"]
    assert traces() == json.loads(G4.read_text())
