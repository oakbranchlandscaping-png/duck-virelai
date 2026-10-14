"""WO-L2a library view: the digest and retrieval Duck reads, built from the validated live library.

Author: Claude (Alpha build seat), 2026-10-11. Sol's directive: "Build its views from validated
world_model.json, with a clear current goal, compact certified findings, typed open gaps, and retrieval
handles. Keep the shared G3 admission edits for the separately reviewed design."

Fixtures are development records (ruling 10): k013 at G3 with nine witnessed levers, and the carry-v7
record across its level change. The production wiring is exercised through the real
gated ToolAgent: the per-turn gate context and the python tool's ``virelai('library', ...)``.
"""
from __future__ import annotations

import hashlib
import json
import pickle

import pytest

from inference.framework import library_view
from inference.framework.descriptive_events import scene_at
from inference.framework.library_view import (
    DIGEST_BUDGET, GOAL_QUESTIONS, HANDLES, HEADER, PAGE_BUDGET, library_digest, library_page, live_model,
    render_library_digest,
)
from inference.framework.world_model_v2 import seal
from inference.framework.record_replay import load_record, replay
from replay_checkpoints import checkpoint
from inference.framework.world_model_v2 import WorldModelV2Error, read_world_model, write_canonical
from test_g3_hybrid_lifecycle_replay import K013
from test_gated_python_bridge import _agent, _capability
from test_wo_l2a_hooks import CARRY


def _digest_of(machine) -> str:
    return hashlib.sha256(pickle.dumps(machine)).hexdigest()


@pytest.fixture(scope="module")
def k013():
    machine = checkpoint(K013, max_steps=400, measure=False).machine  # the shared checkpoint layer: a fresh copy
    before = _digest_of(machine)
    model = live_model(machine)
    assert _digest_of(machine) == before  # the live view leaves the gate machine byte-identical
    return machine, model


@pytest.fixture(scope="module")
def carry():
    machine = checkpoint(CARRY, measure=False).machine
    return machine, live_model(machine)


def test_the_live_library_is_a_validated_view_that_is_never_written(k013, tmp_path):
    _machine, model = k013
    read_world_model(model)  # passes the v2 validator
    assert model["manifest"]["persist_reason"] == "LIVE_VIEW"
    assert model["manifest"]["journal_check"] == "PENDING"
    assert all(level["accounting"]["status"] == "NOT_ACCOUNTED" for level in model["levels"])  # only H2 checks
    result = write_canonical(model, tmp_path)
    assert result.ok is False and "live view" in result.error
    assert not (tmp_path / "world_model.json").exists()


def test_the_digest_names_the_goal_the_findings_and_the_typed_gaps(k013):
    machine, model = k013
    digest = library_digest(model)
    assert digest["goal"] == {"gate_id": machine.gate_id, "question": GOAL_QUESTIONS["G3-LEVERS"], "level": 1}
    assert digest["revision"] == model["content_sha256"][:12]
    (levers,) = [line for line in digest["certified"] if line.startswith("LEVERS")]
    assert levers.startswith("LEVERS x9 (each witnessed once at G3")
    assert digest["certified"][0].startswith("EGO (")
    kinds = digest["open_gaps"]["kinds"]
    assert digest["open_gaps"]["total"] == len(model["levels"][0]["gaps"])
    assert kinds[0].startswith("INCONCLUSIVE x5: Is this object a lever?")  # the active goal's questions first
    assert kinds[1].startswith("NOT_REACHED x8: Is this object a lever?")
    # WO-DESC-B revision 2 (Sol): a contract extension. The six accepted handles keep their text and order, the
    # transformations handle is appended, and the world block's retrieval line names the same handle.
    accepted = ["virelai('library', kind='levels')", "virelai('library', kind='objects', offset=0, limit=10)",
                "virelai('library', kind='object', id=TRACK_ID)",
                "virelai('library', kind='gaps', reason=REASON, subject=SUBJECT, offset=0, limit=10)",
                "virelai('library', kind='role', id=ENTITY_ID_OR_ROLE)", "virelai('library', kind='evidence', id=REF)"]
    assert digest["retrieve"] == list(HANDLES) == accepted + ["virelai('library', kind='transformations')"]
    assert digest["world"]["retrieve"].endswith(HANDLES[-1])
    assert len(json.dumps(digest, sort_keys=True)) <= DIGEST_BUDGET


def test_the_digest_is_deterministic_and_cached_until_the_record_changes(k013):
    machine, model = k013
    assert live_model(machine) is model  # nothing it reads has changed
    assert render_library_digest(model) == render_library_digest(json.loads(json.dumps(model)))
    earlier = replay(load_record(K013), max_steps=300, measure=False).machine
    assert live_model(earlier)["content_sha256"] != model["content_sha256"]


def test_frozen_levels_and_the_open_level_after_a_level_change(carry):
    _machine, model = carry
    digest = library_digest(model)
    assert digest["goal"]["level"] == 2 and digest["goal"]["gate_id"] == "G0-ACTION-METADATA"
    assert digest["earlier_levels"] == ["L1 FROZEN NOT_ACCOUNTED"]
    levels = library_page(model, "levels")["items"]
    assert [(item["level"], item["state"], item["journal_check"]) for item in levels] == [
        (1, "FROZEN", "PENDING"), (2, "OPEN", "PENDING")]
    levers = library_page(model, "role", id="LEVER", level=1)["items"]
    assert sorted(role["entity_id"] for role in levers) == ["E0004", "E0005"]


def test_retrieval_pages_are_bounded_and_resolve_against_the_model(k013):
    _machine, model = k013
    first = library_page(model, "objects", offset=0, limit=10)
    assert first["total"] == 201 and len(first["items"]) == 10 and first["truncated"] is True
    capped = library_page(model, "objects", offset=195, limit=500)
    assert capped["limit"] == 25 and len(capped["items"]) == 6 and capped["truncated"] is False
    (lever,) = library_page(model, "role", id="E0007")["items"]
    track_id = lever["identity"]["track_id"]
    page = library_page(model, "object", id=track_id, limit=2)
    assert page["object"]["track_id"] == track_id and page["object"]["roles"] == ["LEVER E0007"]
    assert page["part"] == "segments" and len(page["items"]) <= 2
    inconclusive = library_page(model, "gaps", reason="inconclusive")
    assert inconclusive["total"] == 5 and {gap["reason"] for gap in inconclusive["items"]} == {"INCONCLUSIVE"}
    witness = lever["witness_refs"][0]
    receipt = library_page(model, "evidence", id=witness)
    assert receipt["table"] == "witnesses" and receipt["items"][0]["entity_id"] == "E0007"
    for kind, options in (("nonsense", {}), ("object", {"id": "O-none"}), ("evidence", {"id": "E-none"}),
                          ("role", {"id": "E9999"}), ("gaps", {"level": 7}),
                          ("object", {"id": track_id, "part": "board"})):
        with pytest.raises(ValueError):
            library_page(model, kind, **options)


def test_a_tampered_model_is_refused(k013):
    _machine, model = k013
    forged = json.loads(json.dumps(model))
    forged["levels"][0]["certified"]["roles"].append({**forged["levels"][0]["certified"]["roles"][-1],
                                                      "entity_id": "E9999"})
    with pytest.raises(WorldModelV2Error):
        library_digest(forged)


def test_duck_reads_the_digest_after_the_card_and_pages_the_library(tmp_path):
    """The production wiring: the per-turn gate context and the python tool's virelai('library', ...)."""
    agent, state_path = _agent(tmp_path)
    _capability(agent, state_path)
    context = agent._gate_context_update(state_path)
    card, library = context.split("\n" + HEADER)
    assert card.startswith("VIRELAI GATE (binding):")
    digest = json.loads(library)
    assert digest["goal"]["question"] == GOAL_QUESTIONS[digest["goal"]["gate_id"]]
    result = agent._run_python_tool(state_path, {"code": "result = virelai('library', kind='levels')"})
    visible = json.loads(json.loads(result.content)["stdout"])
    assert visible["error"] is None and visible["data"]["kind"] == "levels"
    assert visible["data"]["items"][0]["state"] == "OPEN"
    refused = agent._run_python_tool(state_path, {"code": "result = virelai('library', kind='object', id='O-none')"})
    shown = json.loads(json.loads(refused.content)["stdout"])
    assert shown["data"] is None and shown["error"].startswith("ValueError: no object")


# ---- a deliberately large library (Sol's review, 2026-10-11) ---------------------------------------------

LONG = "w" * 400


def _light(level: dict) -> dict:
    """Schema v3 describes every recorded transition, so a light level records none: no transition, no evidence
    on one, and a description of its entry board alone (it has no objects)."""
    level["record"]["transition_ids"] = []
    level["receipts"].update(evidence={}, witnesses={})
    description = level["description"]
    description.update(transitions=[], presence={}, role_bindings=[], first_mismatch=None, integrity="VERIFIED")
    description["scene"] = scene_at(description, [], [])
    return level


def _large(model) -> dict:
    """k013's validated level, inflated: 40 levels, 300 more gap kinds (one with a 600-id list), 120 terrain
    labels, and one object with 500 class events and 300 possible correspondences. Re-sealed, so still valid."""
    base = json.loads(json.dumps({key: value for key, value in model.items() if key != "content_sha256"}))
    level = base["levels"][0]
    level["gaps"] += [{"subject": f"S{n}-{LONG}", "archetype_question": f"Open question {n}? {LONG}",
                       "reason": "NOT_REACHED", "source": LONG} for n in range(300)]
    level["gaps"].append({"subject": "LEVEL-1", "archetype_question": "Does the gate record match what was executed?",
                          "reason": "RECORD_MISMATCH", "source": "record_check", "missing": list(range(1, 601)),
                          "extra": [], "duplicated": [], "renamed": []})
    level["observation"]["terrain"] += [{"entity_id": f"T{n}", "label": f"LABEL-{n}-{LONG}", "evidence_refs": []}
                                        for n in range(120)]
    track = level["observation"]["tracks"][0]
    track["class_events"] = [{"transition_id": n, "verb": "RECOLOR", "witness": LONG} for n in range(1, 501)]
    track["possible_correspondence"] = [f"O-L1-P1-E-{n:012d}" for n in range(300)]
    frozen = []
    for number in range(2, 41):  # light frozen levels: many of them, each still a valid level
        copy = json.loads(json.dumps({key: value for key, value in level.items() if key != "observation"}))
        copy.update(level=number, state="FROZEN", observation={"tracks": [], "terrain": []},
                    gaps=copy["gaps"][:3])
        copy["certified"]["roles"] = []
        frozen.append(_light(copy))
    level["level"] = 41
    base["levels"] = frozen + [level]
    return seal(base)


@pytest.fixture(scope="module")
def large(k013):
    return _large(k013[1])


def test_the_whole_digest_section_fits_its_budget_however_large_the_library(large):
    rendered = render_library_digest(large)
    assert len(rendered) <= DIGEST_BUDGET  # header included
    digest = library_digest(large)
    assert digest["open_gaps"]["kinds"][0].startswith("RECORD_MISMATCH x1")
    assert digest["earlier_levels"][0].startswith("+") and "kind='levels'" in digest["earlier_levels"][0]
    for budget in (1_200, 800, 500):
        assert len(render_library_digest(large, budget)) <= budget
    with pytest.raises(ValueError, match="cannot hold"):
        render_library_digest(large, 120)


def _follow(call: str) -> dict:
    """The keyword arguments of a printed ``virelai('library', ...)`` continuation, exactly as Duck would run it."""
    return eval(call, {"__builtins__": {}}, {"virelai": lambda operation, **kwargs: {"operation": operation, **kwargs}})


def _walk(model, kind, **options):
    """Follow each page's ``next`` call literally to the end; every response stays within the page budget."""
    seen, pages, request = [], 0, {"kind": kind, **options}
    while True:
        page = library_page(model, request.pop("kind"), **request)
        assert len(json.dumps(page, sort_keys=True, default=str)) <= PAGE_BUDGET
        seen += page["items"]
        pages += 1
        if not page["truncated"]:
            assert page["next"] is None
            return page, seen, pages
        request = _follow(page["next"])
        assert request.pop("operation") == "library" and request["offset"] == page["offset"] + page["limit"]


@pytest.mark.parametrize(("kind", "options", "total"), [
    ("levels", {}, 40),
    ("objects", {"limit": 25}, 201),
    ("gaps", {"limit": 25}, 673),
    ("gaps", {"reason": "RECORD_MISMATCH"}, 1),
    ("role", {"id": "LEVER", "limit": 25}, 9),
    ("object", {"part": "class_events", "limit": 25}, 500),
    ("object", {"part": "possible_correspondence", "limit": 25}, 300),
])
def test_every_page_is_bounded_and_its_continuation_reaches_every_row(large, kind, options, total):
    if kind == "object":
        options = {**options, "id": large["levels"][-1]["observation"]["tracks"][0]["track_id"]}
    last, seen, pages = _walk(large, kind, **options)
    assert last["total"] == total and len(seen) == total
    assert pages >= 1 and last["truncated"] is False


def test_a_long_list_inside_an_entry_is_clipped_to_a_count(large):
    (gap,) = library_page(large, "gaps", reason="RECORD_MISMATCH")["items"]
    assert len(gap["missing"]) <= library_view.LIST_KEEP and gap["missing_total"] == 600
    first = library_page(large, "gaps", subject="S0-" + LONG)
    assert first["total"] == 1 and first["items"][0]["subject"].endswith("chars)")  # a 400-char string, cut


def test_duck_pages_a_large_library_through_the_tool_without_truncation(tmp_path, monkeypatch, large):
    agent, state_path = _agent(tmp_path)
    _capability(agent, state_path)
    monkeypatch.setattr(library_view, "live_model", lambda machine, **_kw: large)
    code = "result = virelai('library', kind='gaps', offset=0, limit=25)"
    result = agent._run_python_tool(state_path, {"code": code})
    assert "[truncated" not in result.content  # the tool's output limit never cuts a page
    visible = json.loads(json.loads(result.content)["stdout"])
    assert visible["error"] is None and visible["data"]["total"] == 673
    following = visible["data"]["next"]
    assert following.startswith("virelai('library', kind='gaps'")
    again = agent._run_python_tool(state_path, {"code": f"result = {following}"})
    assert "[truncated" not in again.content
    assert json.loads(json.loads(again.content)["stdout"])["data"]["offset"] == visible["data"]["limit"]
    context = agent._gate_context_update(state_path)
    assert len(context.split("\n" + HEADER)[1]) + len(HEADER) <= DIGEST_BUDGET
