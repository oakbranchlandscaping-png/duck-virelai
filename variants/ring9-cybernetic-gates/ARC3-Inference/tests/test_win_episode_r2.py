"""WO-WIN-01 revision 2: the clear is a boundary, not level-one physics; v10 cannot be downgraded to v9.

Author: Claude (Alpha build seat), 2026-10-19. Sol's review of revision 1:

1. The winning transition's after-board is level two's spawn, yet its 26 ledger events (14 spawn births, 12 old
   tracks rewritten by the board replacement) were counted as level-one transformations: in the participants, the
   explanation totals, the state and a terminal status of ``UNEXPLAINED``. Revision 2 keeps the clear's identity
   (transition, action, actor, receipt, board hashes, boundary) and holds those events only as an uninterpreted
   ``boundary_delta`` whose ids resolve for audit; the semantic window is the life before the clear.
2. A v10 model relabelled v9 and rehashed was read with its episode silently ignored. Revision 2 makes the shapes
   schema-exclusive: a model below v10 holds no ``win_episode``.

Written before the revision-2 edits and run fail-first on revision 1. The positive case is the real carry-v7 record
(level 1 cleared at t26); doubles are labelled.
"""
from __future__ import annotations

import copy
import gzip
import json
import pickle
from pathlib import Path

import pytest

import dossier_fixtures as fx

WIN = 26
FIXTURES = Path(__file__).parent / "fixtures"
_CACHE: dict[str, bytes] = {}


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _W():
    from inference.framework import win_episode

    return win_episode


def _carry():
    if "carry" not in _CACHE:
        machine = fx.carry_v7().machine
        _CACHE["carry"] = pickle.dumps((machine, fx.compiled(machine, persist_reason="RUN_END", reconcile=True)))
    return pickle.loads(_CACHE["carry"])


def _terminal(level):
    return next(r for r in level["description"]["transitions"] if r["transition_id"] == WIN)


def _relabel(model, schema):
    out = dict(model, schema=schema)
    out["content_sha256"] = _wm().content_sha256(out)
    return out


# ---- 1 · the successor spawn is not level-one physics ---------------------------------------------------------------

def test_r2_01_no_boundary_delta_event_is_counted_as_a_level_one_transformation():
    _machine, model = _carry()
    level = model["levels"][0]
    episode = level["win_episode"]
    terminal = {e["event_id"] for e in _terminal(level)["events"]}
    listed = [e["event_id"] for item in episode["transitions"] for e in item["events"]]
    assert len(terminal) == 26 and not terminal & set(listed)
    assert [item["transition_id"] for item in episode["transitions"]] == list(range(1, WIN))
    changes = [e for r in level["description"]["transitions"] if r["transition_id"] < WIN for e in r["events"]
               if e["verb"] != "STILL"]
    counted = sum(episode["explanations"][s] for s in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED"))
    assert counted == len(changes) == 110


def test_r2_02_terminal_born_tracks_are_not_participants():
    _machine, model = _carry()
    level = model["levels"][0]
    episode = level["win_episode"]
    born = {e["subject"]["track_id"] for e in _terminal(level)["events"] if e["verb"] == "BIRTH"}
    named = {p["track_id"] for p in episode["participants"]}
    assert len(born) == 14 and not born & named
    assert not born & set(episode["limits"]["identity_gaps"])
    assert all(not any(WIN in gap["transitions"] for gap in p["identity_gaps"]) for p in episode["participants"])
    assert "spawn_side_tracks" not in episode["limits"]


def test_r2_03_the_terminal_visual_is_typed_as_not_observed_never_unexplained():
    _machine, model = _carry()
    episode = model["levels"][0]["win_episode"]
    assert episode["clear"]["visual_status"] == "SUCCESSOR_SPAWN_NOT_WINNING_RENDER"
    assert episode["limits"]["terminal_visual"] == "SUCCESSOR_SPAWN_NOT_WINNING_RENDER"
    assert "terminal" not in episode["explanations"] and "terminal_explained" not in episode["limits"]
    assert WIN not in episode["limits"]["unexplained_transitions"]


def test_r2_04_the_state_derives_only_from_the_pre_terminal_window():
    W = _W()
    _machine, model = _carry()
    level = copy.deepcopy(model["levels"][0])
    boundary = level["win_episode"]["boundary"]
    assert W.derive(level, boundary)["state"] == "OBSERVED_PARTLY_EXPLAINED"
    # labelled double: every pre-terminal change explained; the 26 terminal events stay UNEXPLAINED in the ledger
    for record in level["description"]["transitions"]:
        for event in record["events"]:
            if record["transition_id"] < WIN and event["verb"] != "STILL":
                event["explanation"] = {"status": "EXPLAINED", "refs": [], "basis": "G2_MASK_LAW"}
    assert {e["explanation"]["status"] for e in _terminal(level)["events"]} == {"UNEXPLAINED"}
    explained = W.derive(level, boundary)
    assert explained["state"] == "OBSERVED" and explained["explanations"]["UNEXPLAINED"] == 0
    # and the reverse: terminal events marked EXPLAINED move nothing
    reverse = copy.deepcopy(model["levels"][0])
    for event in _terminal(reverse)["events"]:
        event["explanation"] = {"status": "EXPLAINED", "refs": [], "basis": "G2_MASK_LAW"}
    assert W.derive(reverse, boundary)["explanations"] == model["levels"][0]["win_episode"]["explanations"]


def test_r2_05_the_raw_terminal_events_stay_resolvable_for_audit_and_cannot_be_edited():
    _machine, model = _carry()
    level = model["levels"][0]
    episode = level["win_episode"]
    delta = episode["clear"]["boundary_delta"]
    assert delta["event_ids"] == [e["event_id"] for e in _terminal(level)["events"]] and delta["events"] == 26
    clear = episode["clear"]
    assert (clear["transition_id"], episode["identity"]["actor"]) == (WIN, "G4.2-LEVER-ORBITS")
    assert episode["boundary"]["successor_entry_sha256"] == model["levels"][1]["entry"]["board_sha256"]

    def forged(mutate):
        out = copy.deepcopy(model)
        mutate(out["levels"][0]["win_episode"]["clear"]["boundary_delta"])
        out["content_sha256"] = _wm().content_sha256(out)
        return out
    for mutate in (lambda d: d["event_ids"].pop(), lambda d: d["event_ids"].append(
            level["description"]["transitions"][0]["events"][0]["event_id"])):
        with pytest.raises(_wm().WorldModelV2Error, match="rule 6: the boundary delta"):
            _wm().read_world_model(forged(mutate))


# ---- 2 · the schema downgrade is closed ------------------------------------------------------------------------

def test_r2_06_a_v10_artifact_relabelled_v9_and_rehashed_is_refused_by_every_entry():
    """WO-RUNTIME-01 (reviewed cause): the writer is v11, so the v10 artifact attacked here is the frozen one the
    base wrote (``world_model_v10_frozen.json.gz``); the writer's own v11 is refused at every older entry too."""
    wm = _wm()
    model = json.loads(gzip.decompress((FIXTURES / "world_model_v10_frozen.json.gz").read_bytes()))
    assert model["schema"] == wm.V10_SCHEMA and all("win_episode" in level for level in model["levels"])
    _machine, current = _carry()
    for schema in (wm.V10_SCHEMA, wm.V9_SCHEMA, wm.V8_SCHEMA):
        with pytest.raises(wm.WorldModelV2Error, match="provenance"):
            wm.read_world_model(_relabel(current, schema))  # v11 carries chapter v3, which no older reader accepts
    for schema in (wm.V9_SCHEMA, wm.V8_SCHEMA):
        relabeled = _relabel(model, schema)
        message = f"a {schema} model holds no win_episode"
        with pytest.raises(wm.WorldModelV2Error, match=message):
            wm.read_world_model(relabeled)
    with pytest.raises(wm.WorldModelV2Error, match=f"a {wm.V9_SCHEMA} model holds no win_episode"):
        wm.validate_v9(_relabel(model, wm.V9_SCHEMA))


def test_r2_07_the_frozen_v9_fixture_from_40940a8_still_reads_unchanged():
    wm = _wm()
    raw = gzip.decompress((FIXTURES / "world_model_v9_frozen.json.gz").read_bytes())
    v9 = json.loads(raw)
    wm.validate_v9(v9)
    assert wm.read_world_model(v9)["schema"] == wm.V9_SCHEMA and wm._canonical(v9) == raw


# ---- 3 · Duck's surface says what was and was not observed ------------------------------------------------------

NO_RENDER = "the game immediately supplied level 2's entry board, so no winning render or terminal visual " \
            "transformation was observed"


def test_r2_08_the_report_page_and_digest_say_no_winning_render_was_observed():
    from inference.framework import library_view as V
    from inference.framework import world_report
    from inference.framework.library_agenda import selected_target

    machine, model = _carry()
    text = world_report.render_world_report(model)
    section = text.split("### Win episode", 1)[1].split("\n### ", 1)[0]
    assert "level 1 cleared at t26 by ACTION6(32,60)" in section and "the preceding life is partly explained" in section
    assert NO_RENDER in section and "UNEXPLAINED" not in section.split("the preceding life", 1)[0]
    live = V.live_model(machine)
    target = selected_target(machine)
    digest = V.library_digest(live, target=target)
    (line,) = digest["win"]
    assert "L1 cleared at t26 by ACTION6(32,60)" in line and "partly explained" in line and "no winning render" in line
    assert len(V.render_library_digest(live, target=target)) <= V.DIGEST_BUDGET
    page = V.library_page(live, "win_episode", level=1)
    assert page["episode"]["clear"]["visual_status"] == "SUCCESSOR_SPAWN_NOT_WINNING_RENDER"
    assert page["total"] == WIN - 1 and all(item["transition_id"] < WIN for item in page["items"])
