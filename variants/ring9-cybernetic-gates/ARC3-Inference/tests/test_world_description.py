"""WO-DESC-B fail-first tests: Duck's semantic world description, its pages and the world report.

Author: Claude (Alpha build seat), 2026-10-13. Interface: ``INTERFACE_WO_DESC_B_v3_2026-10-13`` (Sol's rulings on
v1; his review of v2 and the weave-compaction sweep). DESC-B is a pure projection of the validated v3 model. An
event folds into a primary statement only with evidence that it is the complementary reading of the same change:
a complete exchange of cell ownership between continuing tracks (``OWNER_EXCHANGE``, Ring 7 provenance), or a
certified G2 mask rewrite instantiated by both sides (``G2_MASK_REWRITE``). Coverage alone never folds. Pattern and
question ids are content-derived, so they survive a growing record. Patterns group presentation only: no identity is joined, no role is named
by resemblance, nothing causal is said. Every sentence resolves to DESC-A event, transition and receipt ids.

The new modules are imported inside each test, so each fails on its own on ``66b91cb``.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from inference.framework.library_census import project_tracks
from test_descriptive_events import (
    ENTRY, MASK, UNRESOLVED, _block, _board, _counter_world, _evidence, _exact, _model, _paint, _rows,
)

ROOT = Path(__file__).resolve().parents[1]
CAUSAL_WORDS = ("causes", "caused", "because", "makes", "controls", "drives", "triggers", "so that")


def _desc():
    from inference.framework import world_description

    return world_description


def _error():
    from inference.framework.world_model_v2 import WorldModelV2Error

    return WorldModelV2Error


# ---- synthetic levels built from the accepted DESC-A compiler ---------------------------------------------------

def _level(boards, rows, *, roles=(), receipts=None, gaps=()):
    from inference.framework.descriptive_events import describe_level

    board = tuple(map(tuple, boards[0]))
    receipts = receipts or {"evidence": _evidence(rows), "products": {}, "witnesses": {}}
    certified = {"roles": [copy.deepcopy(role) for role in roles], "scoped_nulls": []}
    projection = project_tracks(1, board, ENTRY, rows)
    description = describe_level(1, board, ENTRY, rows, certified=certified, receipts=receipts, projection=projection)
    return {"level": 1, "state": "OPEN", "entry": dict(ENTRY), "observation": {"tracks": projection["tracks"], "terrain": []},
            "certified": {"gates": [], **certified}, "receipts": receipts, "gaps": list(gaps), "description": description,
            "record": {"transition_ids": [row["transition_id"] for row in rows]}}


def _view(level):
    return _desc().describe_level_view(level)


def _events(level):
    return {e["event_id"]: e for r in level["description"]["transitions"] for e in r["events"]}


def _pattern_of(view, event_id):
    (pattern,) = [p for p in view["patterns"] if event_id in p["events"]]
    return pattern


def _fold_of(view, event_id):
    (fold,) = [f for f in view["folds"] if f["event_id"] == event_id]
    return fold


def _sites(event):
    from inference.framework.descriptive_events import changed_sites

    return changed_sites(event)[0]


def _mask_receipts(rows, rewrite=(5, 0)):
    return {"evidence": _evidence(rows), "witnesses": {}, "products": {
        "P-ctr": {"gate_id": "G2-COUNTER", "payload_sha256": "1" * 64,
                  "mask": {"cell_runs": [[0, 0, 5]], "cell_count": 6, "rewrite": {"from": rewrite[0], "to": rewrite[1]},
                           "law_version_id": "MASK-v1"}}}}


COUNTER_ROLE = {"role": "COUNTER", "gate_id": "G2-COUNTER", "product_id": "P-ctr", "identity": UNRESOLVED}


# ---- 1 · folding ------------------------------------------------------------------------------------------------

def _isolated_tick_world():
    """A counter bar (5) walled in by class 8: its tick leaves an isolated 0 cell, which the weave calls a BIRTH.
    BIRTH outranks SHRINK by verb kind; the certified mask's source side must outrank it anyway (Sol, ruling 1)."""
    base = _paint(_board(fill=8), MASK, 5)
    boards = [base, _paint(base, [(0, 5)], 0)]
    rows = _rows(boards)
    gaps = [{"subject": "COUNTER", "reason": "IDENTITY_UNRESOLVED", "archetype_question": "q"}]
    return _level(boards, rows, roles=[COUNTER_ROLE], receipts=_mask_receipts(rows), gaps=gaps)


def test_a_certified_mask_tick_headlines_its_source_side_not_the_target_birth():
    level = _isolated_tick_world()
    events = _events(level)
    shrink = next(e for e in events.values() if e["verb"] == "SHRINK")
    birth = next(e for e in events.values() if e["verb"] == "BIRTH")
    assert shrink["explanation"]["basis"] == birth["explanation"]["basis"] == "G2_MASK_LAW"  # the DESC-A premise
    view = _view(level)
    assert _pattern_of(view, shrink["event_id"])["verb"] == "SHRINK"
    fold = _fold_of(view, birth["event_id"])
    assert fold["mirror_of"] == [shrink["event_id"]] and fold["explanation"]["basis"] == "G2_MASK_LAW"
    _desc().validate_level_view(view, level)


def test_a_folded_mirror_keeps_its_own_distinct_explanation_counts():
    """A bound ego's MOVE is G1_EGO_MOVE; the background it moves through DEFORMs with nothing covering it. The
    background is folded, and its NOT_COVERED status stays visible on the pattern as a mirror count."""
    base = _paint(_board(), _block(6, 6), 3)
    boards = [base, _paint(_paint(base, _block(6, 6), 0), _block(6, 8), 3)]
    rows = _rows(boards)
    ego = next(t for t, steps in project_tracks(1, tuple(map(tuple, base)), ENTRY, rows)["steps"].items()
               if steps[0].cells == tuple(sorted(_block(6, 6))))
    roles = [{"role": "EGO", "gate_id": "G1-EGO", "product_id": "P-ego", "identity": _exact(ego)}]
    receipts = {"evidence": _evidence(rows), "witnesses": {},
                "products": {"P-ego": {"gate_id": "G1-EGO", "payload_sha256": "0" * 64}}}
    level = _level(boards, rows, roles=roles, receipts=receipts)
    view = _view(level)
    move = next(e for e in _events(level).values() if e["verb"] == "MOVE")
    pattern = _pattern_of(view, move["event_id"])
    assert pattern["object"]["role"] == {"role": "EGO", "gate_id": "G1-EGO", "role_ref": "P-ego"}
    assert pattern["explanations"] == {"G1_EGO_MOVE": 1} and pattern["mirror_explanations"] == {"NOT_COVERED": 1}


def test_a_split_piece_born_without_a_changed_site_stays_primary():
    """A tick inside the bar splits it: the old track is AMBIGUOUS and the unchanged left piece is BORN with no
    changed site. Nothing covers an empty footprint, so it is never folded."""
    base = _paint(_board(), MASK, 5)
    boards = [base, _paint(base, [(0, 3)], 0)]
    level = _level(boards, _rows(boards))
    view = _view(level)
    empty = [e for e in _events(level).values() if e["verb"] == "BIRTH" and not _sites(e)]
    assert empty and all(_pattern_of(view, e["event_id"]) for e in empty)


# ---- 1b · evidence-licensed folding (Sol's review of v2, amendment 1) -------------------------------------------

def _fold_cells(fold):
    return {(row, col) for row, first, last in fold["cells"] for col in range(first, last + 1)}


def test_a_continuing_owner_exchange_folds_with_exact_partner_and_cells():
    """The block moves through the background: both tracks continue, and every changed cell of the background is
    one the block gave or took. The background folds as OWNER_EXCHANGE, naming the block's event and the cells."""
    level = _move_world()
    view = _view(level)
    events = _events(level)
    move = next(e for e in events.values() if e["verb"] == "MOVE" and e["transition_id"] == 1)
    background = next(e for e in events.values() if e["transition_id"] == 1 and e["subject"]["track_id"]
                      != move["subject"]["track_id"])
    fold = _fold_of(view, background["event_id"])
    assert fold["basis"] == "OWNER_EXCHANGE" and fold["mirror_of"] == [move["event_id"]]
    assert _fold_cells(fold) == _sites(background) == _sites(move)


def test_an_overlapping_event_with_one_intrinsic_cell_stays_primary():
    """The block moves one step while a pixel is born elsewhere in the background. Every changed cell of the
    background is covered by the move or the birth, so coverage alone would fold it; but the cell it lost to the
    newborn pixel is a boundary transfer, not an exchange between continuing owners. It stays primary."""
    base = _paint(_board(), _block(4, 4), 3)
    boards = [base, _paint(_paint(_paint(base, _block(4, 4), 0), _block(4, 5), 3), [(10, 10)], 7)]
    level = _level(boards, _rows(boards))
    view = _view(level)
    events = _events(level)
    move = next(e for e in events.values() if e["verb"] == "MOVE")
    birth = next(e for e in events.values() if e["verb"] == "BIRTH")
    background = next(e for e in events.values() if e["event_id"] not in {move["event_id"], birth["event_id"]})
    assert _sites(background) <= _sites(move) | _sites(birth)  # the premise: coverage holds
    assert (10, 10) in _sites(background)
    assert background["event_id"] not in {f["event_id"] for f in view["folds"]}
    assert _pattern_of(view, background["event_id"])


def _bound_ego_world(kind):
    """A certified ego block (3) in walls (8). BIRTH: one ego cell becomes an isolated class-5 pixel. DEATH: a
    class-5 pixel beside the ego becomes ego-coloured. The ego's event outranks the pixel's (bound role), and the
    pixel's sites lie inside the ego's: overlap holds, but the pixel has no continuing owner on one side."""
    base = _paint(_board(fill=8), _block(4, 4), 3)
    if kind == "BIRTH":
        boards = [base, _paint(base, [(5, 5)], 5)]
    else:
        base = _paint(base, [(5, 6)], 5)
        boards = [base, _paint(base, [(5, 6)], 3)]
    rows = _rows(boards)
    ego = next(t for t, steps in project_tracks(1, tuple(map(tuple, boards[0])), ENTRY, rows)["steps"].items()
               if steps[0].cells == tuple(sorted(_block(4, 4))))
    roles = [{"role": "EGO", "gate_id": "G1-EGO", "product_id": "P-ego", "identity": _exact(ego)}]
    receipts = {"evidence": _evidence(rows), "witnesses": {},
                "products": {"P-ego": {"gate_id": "G1-EGO", "payload_sha256": "0" * 64}}}
    return _level(boards, rows, roles=roles, receipts=receipts)


@pytest.mark.parametrize("kind", ["BIRTH", "DEATH"])
def test_an_uncertified_boundary_birth_or_death_is_never_folded_by_overlap(kind):
    level = _bound_ego_world(kind)
    view = _view(level)
    events = _events(level)
    pixel = next(e for e in events.values() if e["verb"] == kind)
    ego = next(e for e in events.values() if e["subject"]["roles"])
    assert _sites(pixel) <= _sites(ego)  # the premise: the pixel is covered by the higher-ranked ego event
    assert pixel["event_id"] not in {f["event_id"] for f in view["folds"]}
    assert _pattern_of(view, pixel["event_id"])["verb"] == kind


def test_a_certified_mask_boundary_birth_folds_through_the_mask_rewrite():
    level = _isolated_tick_world()
    view = _view(level)
    events = _events(level)
    shrink = next(e for e in events.values() if e["verb"] == "SHRINK")
    birth = next(e for e in events.values() if e["verb"] == "BIRTH")
    fold = _fold_of(view, birth["event_id"])
    assert fold["basis"] == "G2_MASK_REWRITE" and fold["mirror_of"] == [shrink["event_id"]]
    assert _fold_cells(fold) == {(0, 5)}


def test_the_residual_census_counts_every_verified_event():
    level = _counter_level()
    view = _view(level)
    verified = [e for r in level["description"]["transitions"] if r["record_status"] == "VERIFIED" for e in r["events"]]
    assert sum(view["census"]["verbs"].values()) == len(verified)
    assert view["census"]["folded"] == len(view["folds"])


def _move_world(lives=False):
    base = _paint(_board(), _block(2, 2), 3)
    right = _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 3)
    down = _paint(_paint(base, _block(2, 2), 0), _block(6, 2), 3)
    if lives:
        boards = [base, right, base, right]
        return _level(boards, _rows(boards, kinds={2: "RESET"}, lives={2: 2, 3: 2}))
    boards = [base, right, base, down]
    rows = _rows(boards)
    rows[1]["action"] = {"action": "ACTION2"}
    rows[2]["action"] = {"action": "ACTION3"}
    return _level(boards, rows)


def test_every_change_is_primary_or_a_covered_mirror_and_none_is_hidden():
    for level in (_isolated_tick_world(), _move_world(), _move_world(lives=True), _counter_level()):
        view = _view(level)
        primary = [e for p in view["patterns"] for e in p["events"]]
        folded = [f["event_id"] for f in view["folds"]]
        events = _events(level)
        changed = [i for i, e in events.items() if e["verb"] != "STILL"]
        assert sorted(primary + folded) == sorted(changed) and len(set(primary)) == len(primary)
        for fold in view["folds"]:
            mirrors = set().union(*(_sites(events[m]) for m in fold["mirror_of"]))
            assert _sites(events[fold["event_id"]]) <= mirrors
            assert all(events[m]["transition_id"] == fold["transition_id"] for m in fold["mirror_of"])
        for record in level["description"]["transitions"]:  # folding never hides a changed site
            all_sites = set().union(set(), *(_sites(e) for e in record["events"]))
            kept = set().union(set(), *(_sites(e) for e in record["events"] if e["event_id"] in primary))
            assert kept == all_sites


def _counter_level():
    boards, rows, _ego, _description, context = _counter_world()
    return _level(boards, rows, roles=context["roles"], receipts=context["receipts"], gaps=context["gaps"])


# ---- 2 · patterns: presentation groups, action tables, observed effect types ---------------------------------

def test_a_pattern_tabulates_its_deltas_by_action_as_co_occurrence():
    view = _view(_move_world())
    (pattern,) = [p for p in view["patterns"] if p["verb"] == "MOVE"]
    assert pattern["count"] == len(pattern["events"]) == 3
    assert pattern["by_action"] == {"ACTION1": {"[0, 4]": 1}, "ACTION2": {"[0, -4]": 1}, "ACTION3": {"[4, 0]": 1}}
    assert "on ACTION1 transitions" in pattern["sentence"]


@pytest.mark.parametrize("name", ["k008", "k013", "carry"])
def test_a_verb_without_a_scalar_delta_tabulates_its_verb_never_null(name, request):
    """Revision 2 (Sol, F3): BIRTH, DEATH and a shapeless DEFORM have no scalar delta. Their action table names the
    verb ("on ACTION1 transitions: DEATH x1"); serialization vocabulary (``null``, ``None``) never reaches the
    sentences, the questions, Duck's digest or the report."""
    import re

    from inference.framework import library_view, world_report

    model = request.getfixturevalue(name)
    views = _desc().describe_world(model)["levels"]
    patterns = [p for v in views for p in v["patterns"]]
    for pattern in patterns:
        for deltas in pattern["by_action"].values():
            assert all(key == pattern["verb"] or json.loads(key) is not None for key in deltas), pattern["by_action"]
    shapeless = [p for p in patterns if any(pattern_key == p["verb"] for d in p["by_action"].values() for pattern_key in d)]
    assert shapeless and all(f"transitions: {p['verb']} x" in p["sentence"] for p in shapeless)
    if name == "k008":
        (death,) = [p for p in patterns if p["verb"] == "DEATH"]
        assert death["by_action"] == {"ACTION1": {"DEATH": 1}} and "on ACTION1 transitions: DEATH x1" in death["sentence"]
    prose = [p["sentence"] for p in patterns] + [q["text"] for v in views for q in v["questions"]] + [
        library_view.render_library_digest(model), world_report.render_world_report(model)]
    assert not any(re.search(r"\bnull\b|\bNone\b", text) for text in prose)


def test_an_appearance_group_spans_lives_without_joining_identity():
    level = _move_world(lives=True)
    view = _view(level)
    (pattern,) = [p for p in view["patterns"] if p["verb"] == "MOVE"]
    assert len(pattern["object"]["tracks"]) == 2 and pattern["object"]["lives"] == [1, 2]
    assert pattern["object"]["role"] is None and "2 tracks" in pattern["sentence"] and "lives 1,2" in pattern["sentence"]
    identity_gaps = [g for g in level["gaps"] if g["reason"] == "IDENTITY_UNRESOLVED"]
    assert all(g in level["gaps"] for g in identity_gaps)  # the view writes nothing; the census gap stands


def test_observed_effect_type_is_reported_verbatim_and_never_called_a_mechanism():
    from inference.framework.effect_typing import classify_effect_channel

    view = _view(_counter_level())
    typed = [t for p in view["patterns"] for t in p["observed_effect_type"]]
    for item in typed:
        assert set(item) >= {"track_id", "type", "status", "witness_count", "condition"}
    assert "mechanism" not in json.dumps(view)
    assert classify_effect_channel  # the neutral module exists


def test_the_view_is_deterministic():
    level = _counter_level()
    assert json.dumps(_view(level), sort_keys=True) == json.dumps(_view(copy.deepcopy(level)), sort_keys=True)


# ---- 3 · the validator ----------------------------------------------------------------------------------------

def _valid():
    level = _counter_level()
    return _view(level), level


@pytest.mark.parametrize("forgery", ["event_id", "count", "role", "causal", "explanations", "mirror", "gap",
                                     "fold_basis", "fold_cells"])
def test_the_view_validator_refuses_every_forgery(forgery):
    view, level = _valid()
    _desc().validate_level_view(view, level)
    forged = copy.deepcopy(view)
    pattern = forged["patterns"][0]
    if forgery == "event_id":
        pattern["events"][0] = "EV-" + "0" * 16
    elif forgery == "count":
        pattern["count"] += 1
    elif forgery == "role":
        unbound = next(p for p in forged["patterns"] if p["object"]["role"] is None)
        unbound["object"]["name"] = "COUNTER"
    elif forgery == "causal":
        pattern["sentence"] += " because ACTION1"
    elif forgery == "explanations":
        pattern["explanations"] = {"G2_MASK_LAW": pattern["count"] + 5}
    elif forgery == "mirror":
        fold = forged["folds"][0]
        fold["mirror_of"] = [e for e in pattern["events"] if e not in fold["mirror_of"]][:1] or ["EV-" + "1" * 16]
    elif forgery == "fold_basis":
        fold = next(f for f in forged["folds"] if f["basis"] == "OWNER_EXCHANGE")
        fold["basis"] = "G2_MASK_REWRITE"
    elif forgery == "fold_cells":
        forged["folds"][0]["cells"] = forged["folds"][0]["cells"][:-1] or [[11, 11, 11]]
    elif forgery == "gap":
        forged["questions"].append({"question_id": "Q99", "pattern_id": pattern["pattern_id"], "text": "?",
                                    "unexplained": 1, "gaps": ["NO-SUCH-GAP"]})
    with pytest.raises(_error()):
        _desc().validate_level_view(forged, level)


# ---- 4 · the saved records -----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def k008():
    from test_g3_hybrid_lifecycle_replay import K008

    return _model(K008, 45)[0]


@pytest.fixture(scope="module")
def k013():
    from test_g3_hybrid_lifecycle_replay import K013

    return _model(K013, 401)[0]


@pytest.fixture(scope="module")
def carry():
    from test_wo_l2a_hooks import CARRY

    return _model(CARRY, 20)[0]


def test_every_k008_mask_tick_has_one_primary_source_side_statement(k008):
    (level,) = k008["levels"]
    view = _view(level)
    primary = {e for p in view["patterns"] for e in p["events"]}
    folded = {f["event_id"]: f for f in view["folds"]}
    ticks = 0
    for record in level["description"]["transitions"]:
        masked = [e for e in record["events"] if e["explanation"]["basis"] == "G2_MASK_LAW"]
        if not masked:
            continue
        ticks += 1
        heads = [e for e in masked if e["event_id"] in primary]
        assert len(heads) == 1 and heads[0]["before"]["class"] == 14, record["transition_id"]  # the source side
        for mirror in (e for e in masked if e["event_id"] not in primary):
            assert heads[0]["event_id"] in folded[mirror["event_id"]]["mirror_of"]
    first = next(r for r in level["description"]["transitions"] if r["transition_id"] == 1)
    birth = next(e for e in first["events"] if e["verb"] == "BIRTH")
    assert birth["event_id"] in folded and ticks >= 40  # the first tick's vacated-region BIRTH is a mirror
    _desc().validate_level_view(view, level)


def test_k008_unbound_ego_like_pattern_cites_no_role_gap(k008):
    (level,) = k008["levels"]
    view = _view(level)
    (move,) = [p for p in view["patterns"] if p["verb"] == "MOVE"]
    assert move["object"]["role"] is None and move["object"]["handle"] == "c9@16,12"
    assert "EGO" not in move["sentence"] and "EGO" not in move["object"]["name"]
    question = next(q for q in view["questions"] if q["pattern_id"] == move["pattern_id"])
    cited = [level["gaps"][index] for index in question["gaps"]]
    assert all(gap["subject"] in set(move["object"]["tracks"]) for gap in cited)  # exact subject references only
    assert {item["role"] for item in view["open_identity"]} == {"EGO", "COUNTER"}  # listed separately


def test_k013_uncertified_shrink_is_not_called_the_counter(k013):
    (level,) = k013["levels"]
    view = _view(level)
    shrink = max((p for p in view["patterns"] if p["verb"] == "SHRINK"), key=lambda p: p["count"])
    assert shrink["object"]["handle"] == "c14@0,62" and shrink["object"]["role"] is None
    assert "COUNTER" not in shrink["sentence"] and "COUNTER" not in shrink["object"]["name"]
    # v3 (evidence-licensed folding): the 8 boundary ticks no longer fold into an uncertified BIRTH (v2 read 210+5)
    assert shrink["explanations"] == {"NOT_COVERED": 217, "G3_WITNESS_RESIDUE": 6}
    assert view["questions"][0]["pattern_id"] == shrink["pattern_id"]
    assert {p["object"]["handle"] for p in view["patterns"] if p["verb"] == "RECOLOR"} >= {"c9@19,39", "c10@19,41"}


def test_carry_folds_the_terrain_and_keeps_witness_counts(carry):
    level = carry["levels"][0]
    view = _view(level)
    terrain = [p for p in view["patterns"] if p["verb"] == "DEFORM" and p["object"]["handle"].startswith("c3@")]
    # revision 2 (Sol): the folds counted here are the terrain's own, by track; each one is an owner exchange
    terrain_tracks = {t["track_id"] for t in level["observation"]["tracks"] if _desc().appearance(t)[0].startswith("c3@")}
    terrain_folds = [f for f in view["folds"] if f["track_id"] in terrain_tracks]
    assert terrain_folds and all(f["basis"] == "OWNER_EXCHANGE" for f in terrain_folds)
    records = {r["transition_id"]: r for r in level["description"]["transitions"]}
    for pattern in terrain:  # v3: it stays primary only where it traded cells with a boundary (non-continuing) event
        for event_id, transition in zip(pattern["events"], pattern["transitions"]):
            assert any(e["verb"] != "STILL" and (e["before"] is None or e["after"] is None)
                       for e in records[transition]["events"] if e["event_id"] != event_id)
    witnessed = [p for p in view["patterns"] if p["explanations"].get("G3_WITNESS_RESIDUE")]
    assert {p["object"]["handle"] for p in witnessed} >= {"c4@44,46", "c11@44,50"}
    assert all(p["explanations"]["G3_WITNESS_RESIDUE"] + p["explanations"].get("NOT_COVERED", 0) == p["count"]
               for p in witnessed)  # the mixed statuses are counted as they are, never promoted


def test_pattern_and_question_ids_survive_an_extended_record(k008):
    """Sol's review of v2, amendment 2: ids are content-derived, never ranks. Compiled on the record's first 19
    transitions and again on 44, every surviving pattern and question keeps its id while its counts and last
    transition advance. A prefix statement that disappears may do so only because its events became licensed folds
    (G2 certified its mask at transition 37), never because an id moved."""
    from test_g3_hybrid_lifecycle_replay import K008

    prefix = _view(_model(K008, 20)[0]["levels"][0])
    full = _view(k008["levels"][0])
    owner = {e: p["pattern_id"] for p in full["patterns"] for e in p["events"]}
    folded = {f["event_id"] for f in full["folds"]}
    after = {p["pattern_id"]: p for p in full["patterns"]}
    survivors = 0
    for early in prefix["patterns"]:
        assert early["pattern_id"].startswith("P-")
        kept = [e for e in early["events"] if e in owner]
        if not kept:
            assert set(early["events"]) <= folded
            continue
        survivors += 1
        assert {owner[e] for e in kept} == {early["pattern_id"]} and set(kept) == set(early["events"])
        late = after[early["pattern_id"]]
        assert late["count"] >= early["count"] and late["transitions"][-1] >= early["transitions"][-1]
    assert survivors >= 2 and any(after[p["pattern_id"]]["count"] > p["count"] for p in prefix["patterns"]
                                  if p["pattern_id"] in after)
    late_q = {q["question_id"]: q["pattern_id"] for q in full["questions"]}
    surviving_q = [q for q in prefix["questions"] if q["pattern_id"] in after
                   and any(r["pattern_id"] == q["pattern_id"] for r in full["questions"])]
    assert surviving_q and all(late_q.get(q["question_id"]) == q["pattern_id"] for q in surviving_q)
    assert all(qid.startswith("Q-") for qid in late_q)


@pytest.mark.parametrize("name", ["k008", "k013", "carry"])
def test_the_view_validates_and_is_byte_identical_on_each_record(name, request):
    model = request.getfixturevalue(name)
    from inference.framework.world_model_v2 import canonical_bytes

    before = canonical_bytes(model)
    first, second = _desc().describe_world(model), _desc().describe_world(copy.deepcopy(model))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    _desc().validate_view(first, model)
    assert canonical_bytes(model) == before  # the view writes nothing into the model


# ---- 5 · Duck's surface ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["k008", "k013", "carry"])
def test_one_combined_library_section_holds_goal_findings_gaps_and_world_within_2500(name, request):
    from inference.framework.library_view import DIGEST_BUDGET, library_digest, render_library_digest

    model = request.getfixturevalue(name)
    rendered = render_library_digest(model)
    digest = library_digest(model)
    assert DIGEST_BUDGET == 2_500 and len(rendered) <= 2_500
    assert "world" in digest and digest["goal"]["question"] and rendered.index('"goal"') < rendered.index('"world"')
    assert len(json.dumps(digest["world"], sort_keys=True)) <= 1_500
    assert not any(word in rendered.lower() for word in CAUSAL_WORDS)


PATTERN_ID = r"P-[0-9a-f]{12}"
QUESTION_ID = r"Q-[0-9a-f]{12}"
ACCEPTED_HANDLES = (  # the six retrieval handles accepted at 66b91cb, in their order
    "virelai('library', kind='levels')",
    "virelai('library', kind='objects', offset=0, limit=10)",
    "virelai('library', kind='object', id=TRACK_ID)",
    "virelai('library', kind='gaps', reason=REASON, subject=SUBJECT, offset=0, limit=10)",
    "virelai('library', kind='role', id=ENTITY_ID_OR_ROLE)",
    "virelai('library', kind='evidence', id=REF)",
)


@pytest.mark.parametrize("name", ["k008", "k013", "carry"])
def test_the_digest_floor_shows_two_patterns_and_one_question_within_2500(name, request):
    """Revision 2 (Sol, F1): the ordinary turn carries transformation knowledge. Within the one 2,500-character
    section: two pattern statements and one world question, the question naming its pattern and that pattern shown,
    beside the selected gate question, the accounting status and the open-identity count. The general gap
    inventory shrinks first."""
    import re

    from inference.framework.library_view import library_digest, render_library_digest

    model = request.getfixturevalue(name)
    rendered = render_library_digest(model)
    digest = library_digest(model)
    world = digest["world"]
    assert len(rendered) <= 2_500 and len(json.dumps(world, sort_keys=True)) <= 1_500
    assert re.search(PATTERN_ID, rendered) and re.search(QUESTION_ID, rendered)
    assert len(world["patterns"]) >= 2 and len(world["questions"]) >= 1
    shown = [re.match(PATTERN_ID, line).group(0) for line in world["patterns"]]
    view = _desc().describe_level_view(model["levels"][-1])
    for line in world["questions"]:
        question_id, pattern_id = re.match(rf"({QUESTION_ID}) \(({PATTERN_ID})\)", line).groups()
        assert pattern_id in shown
        assert {q["question_id"]: q["pattern_id"] for q in view["questions"]}[question_id] == pattern_id
    assert digest["goal"]["question"] and digest["accounting"]["status"]
    assert world["open_identity"].startswith(f"{len(view['open_identity'])} unresolved")
    assert rendered.index('"goal"') < rendered.index('"world"')


def test_the_floor_keeps_the_record_mismatch_and_accounting_on_a_large_library():
    """The inflated live library of ``test_library_view`` (40 levels, 300 extra gap kinds and a RECORD_MISMATCH gap)
    still shows the floor: the mismatch and the accounting status survive, and so do two patterns and one question."""
    import re

    from inference.framework.library_view import library_digest, live_model, render_library_digest
    from replay_checkpoints import checkpoint
    from test_g3_hybrid_lifecycle_replay import K013
    from test_library_view import _large

    large = _large(live_model(checkpoint(K013, max_steps=400, measure=False).machine))
    rendered = render_library_digest(large)
    digest = library_digest(large)
    assert len(rendered) <= 2_500
    assert digest["open_gaps"]["kinds"][0].startswith("RECORD_MISMATCH x1") and digest["accounting"]["status"]
    assert len(re.findall(PATTERN_ID, json.dumps(digest["world"]["patterns"]))) >= 2
    assert re.search(QUESTION_ID, json.dumps(digest["world"]["questions"]))


def test_the_transformations_handle_is_appended_to_the_accepted_handles(k008):
    """Revision 2 (Sol, F2): a contract extension. The six accepted handles keep their text and order; the
    transformations handle is appended; the world block's retrieval line names the same handle."""
    from inference.framework.library_view import HANDLES, WORLD_HANDLE, library_digest

    assert HANDLES[:len(ACCEPTED_HANDLES)] == ACCEPTED_HANDLES
    assert HANDLES[len(ACCEPTED_HANDLES):] == (WORLD_HANDLE,) == ("virelai('library', kind='transformations')",)
    assert library_digest(k008)["world"]["retrieve"].endswith(HANDLES[-1])


def test_the_laws_page_shows_only_what_schema_v3_stores(k008):
    from inference.framework.library_view import library_page

    (level,) = k008["levels"]
    page = library_page(k008, "laws")
    rows = {row["gate_id"]: row for row in page["items"]}
    assert rows["G1-EGO"]["structured_law"] is None
    assert rows["G1-EGO"]["note"] == "G1 product recorded; structured movement law unavailable"
    counter = next(r for r in level["certified"]["roles"] if r["role"] == "COUNTER")
    assert rows["G2-COUNTER"]["structured_law"] == level["receipts"]["products"][counter["product_id"]]["mask"]
    text = json.dumps(page)
    assert "opaque_action_laws" not in text and "displacement" not in text.lower()


@pytest.mark.parametrize("kind", ["scene", "events", "transformations", "dossiers", "laws", "residuals"])
def test_every_new_page_is_bounded_on_k013(kind, k013):
    from inference.framework.library_view import PAGE_BUDGET, library_page

    page = library_page(k013, kind)
    assert len(json.dumps(page, sort_keys=True, default=str)) <= PAGE_BUDGET and page["kind"] == kind


def test_event_page_filters_are_applied_and_continuations_keep_them(k008):
    from inference.framework.library_view import library_page

    page = library_page(k008, "events", verb="SHRINK", from_transition=5, to_transition=20, include_folded=True,
                        limit=2)
    assert page["truncated"] and all(item["verb"] == "SHRINK" and 5 <= item["transition_id"] <= 20 for item in page["items"])
    for fragment in ("verb='SHRINK'", "from_transition=5", "to_transition=20", "include_folded=True"):
        assert fragment in page["next"]
    one = library_page(k008, "events", transition=1, object="c9@16,12")
    assert [item["transition_id"] for item in one["items"]] == [1] and one["items"][0]["object"] == "c9@16,12"


def test_the_dossier_page_is_a_stable_not_built_row_per_certified_lever(carry):
    from inference.framework.library_view import library_page

    level = carry["levels"][0]
    page = library_page(carry, "dossiers")
    levers = sorted(role["entity_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER")
    assert [row["id"] for row in page["items"]] == levers and {row["status"] for row in page["items"]} == {"NOT_BUILT"}


def test_duck_s_query_forwards_every_new_filter(monkeypatch):
    from inference.agent import memory_queries
    from inference.framework import library_view

    seen = {}
    monkeypatch.setattr(library_view, "live_model", lambda machine: {"stub": True})
    monkeypatch.setattr(library_view, "library_page", lambda model, kind, **options: seen.update(kind=kind, **options) or {})
    filters = {"transition": 3, "from_transition": 1, "to_transition": 9, "object": "c9@16,12", "verb": "MOVE",
               "include_folded": True}
    memory_queries._library_query(object(), {"kind": "events", **filters})
    assert {key: seen.get(key) for key in filters} == filters


# ---- 6 · the neutral effect-typing module ----------------------------------------------------------------------

def test_effect_typing_imports_without_the_legacy_compiler():
    code = ("import sys; import inference.framework.effect_typing as e; "
            "print(int('inference.framework.virelai_semantic.compiler' in sys.modules))")
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-400:]
    assert done.stdout.strip() == "0"
    from inference.framework.effect_typing import classify_effect_channel
    from inference.framework.virelai_semantic.typing import classify_effect_channel as legacy

    assert legacy is classify_effect_channel  # the legacy name re-exports the one function


# ---- 7 · the world report ----------------------------------------------------------------------------------------

def test_the_report_embeds_the_full_content_hash_and_renders_identically(k008, tmp_path):
    from inference.framework import world_report

    first, second = world_report.render_world_report(k008), world_report.render_world_report(copy.deepcopy(k008))
    assert first == second and k008["content_sha256"] in first
    result = world_report.write_world_report(k008, tmp_path)
    assert result.ok and (tmp_path / "world_report.md").read_text() == first
    assert not any(word in first.lower() for word in CAUSAL_WORDS)


ID_KEYS = ("event_id", "track_id", "product_id", "entity_id", "law_version_id", "mask_law_version_id", "payload_sha256",
           "evidence_refs", "witness_refs", "unverified_refs", "refs", "mirror_of")


def _model_ids(value, out):
    """The stored ids a report may cite: values under id and ref keys, and the keys of the receipt stores. Prose,
    statuses and verbs are never ids, so a token such as ``VERIFIED`` does not resolve."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("products", "evidence") and isinstance(item, dict):
                out.update(item)
            if key in ID_KEYS:
                out.update([item] if isinstance(item, str) else [x for x in item or () if isinstance(x, str)])
            _model_ids(item, out)
    elif isinstance(value, list):
        for item in value:
            _model_ids(item, out)
    return out


def _resolves(token, model, ids, level):
    """A report reference resolves: ``manifest`` or a top-level key; a canonical JSON path; a transition range; a
    stored id; or a pattern or question id of the view. Revision 3 (Sol): a path names only the level whose section
    it sits in, and a range lies inside that level: after its entry board and within its recorded transitions."""
    import re

    if token in ("manifest", "game_id", "run_stem", "schema", "levels"):
        return token in model
    if token.startswith("levels["):
        if not re.fullmatch(r"levels\[\d+\](\.[a-z_]+(\[\d+\])?)*", token):
            return False
        if level is None or int(re.match(r"levels\[(\d+)\]", token).group(1)) != level:
            return False
        node = model
        for name, index in re.findall(r"\.?([a-z_]+)?(?:\[(\d+)\])?", token):
            if not name and not index:
                continue
            if name:
                if not isinstance(node, dict) or name not in node:
                    return False
                node = node[name]
            if index:
                if not isinstance(node, list) or int(index) >= len(node):
                    return False
                node = node[int(index)]
        return True
    span = re.fullmatch(r"t(\d+)-t(\d+)", token)
    if span:
        if level is None:
            return False
        description = model["levels"][level]["description"]
        recorded = [r["transition_id"] for r in description["transitions"]]
        first = int(description["basis"]["entry_node"]) + 1
        return bool(recorded) and first <= int(span.group(1)) <= int(span.group(2)) <= max(recorded)
    return token != "none" and token in ids


def _assert_report_refs(model, text):
    """Every bullet and numbered claim ends in ``refs:`` and every reference resolves, scoped to the level section
    (``## Level N`` or ``### Appendix, level N``) it sits in. Serialization words never appear."""
    import re

    view = _desc().describe_world(model)
    ids = _model_ids(model, set()) | {p["pattern_id"] for v in view["levels"] for p in v["patterns"]} | {
        q["question_id"] for v in view["levels"] for q in v["questions"]}
    index_of = {level["level"]: index for index, level in enumerate(model["levels"])}
    assert not re.search(r"\bNone\b|\bnull\b|tNone|\bt0\b", text)
    current, claims = None, 0
    for line in text.splitlines():
        heading = re.match(r"^(?:## Level|### Appendix, level) (\d+)", line)
        if heading:
            current = index_of[int(heading.group(1))]
        if not line.strip() or line.startswith("#"):
            continue
        assert re.match(r"^\s*(- |\d+\. )", line), line  # only headings and claim lines are written
        assert "; refs: " in line, line
        tokens = line.rsplit("refs: ", 1)[1].split(", ")
        assert tokens and all(_resolves(token, model, ids, current) for token in tokens), line
        claims += 1
    return claims


@pytest.mark.parametrize("name", ["k008", "k013", "carry"])
def test_every_factual_report_line_ends_in_resolvable_refs(name, request):
    """Revision 2 (Sol): every bullet and numbered claim of the report ends in ``refs:``, and each reference resolves
    in the sealed model or its view. Nothing else is written outside the headings. Revision 3: references are
    scoped to their level section."""
    from inference.framework import world_report

    model = request.getfixturevalue(name)
    view = _desc().describe_world(model)
    ids = _model_ids(model, set()) | {p["pattern_id"] for v in view["levels"] for p in v["patterns"]}
    last = max(r["transition_id"] for r in model["levels"][0]["description"]["transitions"])
    # the resolver refuses what is not a reference: a status word, a missing path, a path or range outside its level
    assert not any(_resolves(token, model, ids, 0) for token in
                   ("VERIFIED", "SHRINK", "none", "levels[0].nope", "levels[9].gaps[0]", "levels[1].entry",
                    "t0-t1", f"t1-t{last + 1}"))
    assert not _resolves("levels[0].entry", model, ids, None) and not _resolves("t1-t2", model, ids, None)
    assert _assert_report_refs(model, world_report.render_world_report(model)) > 20


# ---- 7b · entry-state scenes (Sol's review of revision 2) -----------------------------------------------------

def _entry_level(number, boards, rows, entry):
    """A synthetic level entered at ``entry``; its rows are numbered after the entry board."""
    from inference.framework.descriptive_events import describe_level

    board = tuple(map(tuple, boards[0]))
    receipts = {"evidence": _evidence(rows), "products": {}, "witnesses": {}}
    certified = {"roles": [], "scoped_nulls": []}
    projection = project_tracks(number, board, entry, rows)
    description = describe_level(number, board, entry, rows, certified=certified, receipts=receipts,
                                 projection=projection)
    return {"level": number, "state": "OPEN", "entry": dict(entry),
            "observation": {"tracks": projection["tracks"], "terrain": []}, "certified": {"gates": [], **certified},
            "receipts": receipts, "gaps": [], "description": description,
            "record": {"transition_ids": [row["transition_id"] for row in rows]}}


def _scene_claims(text, number):
    """The two scene claim lines of level ``number``'s section."""
    section = text.split(f"## Level {number}\n", 1)[1].split("### Scene\n\n", 1)[1].split("\n\n", 1)[0]
    return section.splitlines()


@pytest.fixture(scope="module")
def carry_boundary():
    """The existing carry boundary fixture (``test_library_census``): level 1 frozen at its completion on
    transition 26, level 2 open at its entry board with no action yet."""
    from inference.framework.library_census import ExecutionRecord, compile_level, compile_world_model
    from inference.framework.record_replay import decode_grid, load_record, replay
    from inference.framework.virelai_gates import CyberneticGateMachine
    from inference.framework.world_model_v2 import seal
    from test_library_census import CARRY

    record = load_record(CARRY)
    boundary = next(step for step in record["steps"] if (step.get("boundary") or {}).get("level_completed"))
    executed = tuple(step["action"]["action"] for step in record["steps"]
                     if step["transition_id"] <= boundary["transition_id"])
    execution = ExecutionRecord(tuple(tuple(row) for row in decode_grid(record["initial_grid"])), 1,
                                tuple(record["valid_actions"]), executed)
    captured = {}
    original = CyberneticGateMachine._advance_level

    def hooked(self, outcome):
        captured["census"] = compile_level(self, execution, state="FROZEN",
                                           level=outcome["boundary_event"]["level_before"])
        original(self, outcome)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(CyberneticGateMachine, "_advance_level", hooked)
        machine = replay(record, measure=False).machine
    return seal(compile_world_model(machine, execution, game_id="g", run_stem="g_p0", persist_reason="RUN_END",
                                    frozen_levels=[captured["census"]]))


def test_an_observed_never_acted_world_reads_as_of_level_entry(tmp_path):
    """Revision 3 (Sol): the 77-world shape. One observed board and no action: the scene is the level entry, cites
    the entry and the scene, and carries no transition range; neither surface renders None, tNone or t0."""
    from inference.framework import world_report
    from inference.framework.library_view import library_digest, render_library_digest
    from test_wo_l2a_census_paths import _cancelled_before_first_turn

    folder, _game, _calls = _cancelled_before_first_turn(tmp_path)
    model = json.loads((folder / "world_model.json").read_text())
    assert model["levels"][0]["description"]["scene"]["as_of_transition"] is None  # the premise
    text = (folder / "world_report.md").read_text()
    assert text == world_report.render_world_report(model)
    first, counts = _scene_claims(text, model["levels"][0]["level"])
    assert first.startswith("- as of level entry, life ")
    for line in (first, counts):
        refs = line.rsplit("refs: ", 1)[1].split(", ")
        assert refs[:2] == ["levels[0].entry", "levels[0].description.scene"]
        assert not any(ref.startswith("t") for ref in refs)
    _assert_report_refs(model, text)
    assert library_digest(model)["world"]["scene"].startswith("as of level entry, life ")
    assert "None" not in render_library_digest(model) and "tNone" not in render_library_digest(model)


def test_the_open_second_level_at_its_entry_cites_its_own_entry(carry_boundary):
    """Revision 3 (Sol): the carry boundary. Level 2 opened after transition 26 and no action followed: its scene
    is that level's entry board, cited as ``levels[1].entry``, with no range reaching into level 1."""
    from inference.framework import world_report
    from inference.framework.library_view import library_digest

    model = carry_boundary
    opened = model["levels"][1]
    assert opened["entry"]["after_transition"] == 26 and opened["description"]["scene"]["as_of_transition"] is None
    text = world_report.render_world_report(model)
    first, counts = _scene_claims(text, 2)
    assert first.startswith("- as of level entry, life ")
    for line in (first, counts):
        refs = line.rsplit("refs: ", 1)[1].split(", ")
        assert refs[:2] == ["levels[1].entry", "levels[1].description.scene"]
        assert not any(ref.startswith("t") for ref in refs)
    level_one = _scene_claims(text, 1)[0].rsplit("refs: ", 1)[1].split(", ")
    assert level_one == ["levels[0].entry", "levels[0].description.scene", "levels[0].description.integrity", "t1-t26"]
    _assert_report_refs(model, text)
    assert library_digest(model)["world"]["scene"].startswith("as of level entry, life ")


def test_a_later_level_after_actions_cites_only_its_own_transitions():
    """Revision 3 (Sol): a level entered after transition 3, with transitions 4 to 6 verified. Its scene cites its
    entry board and ``t4-t6``: never ``t0`` and never a transition of the level before it."""
    from inference.framework import world_report
    from test_descriptive_events import _entry_world

    boards = _entry_world()
    first = _entry_level(1, boards, _rows(boards), ENTRY)
    second = _entry_level(2, boards, _rows(boards, start=4, level=2), {"source": "LEVEL_ENTRY", "after_transition": 3})
    assert second["description"]["basis"]["entry_node"] == 3
    assert [r["record_status"] for r in second["description"]["transitions"]] == ["VERIFIED"] * 3
    model = {"game_id": "g", "run_stem": "g_p0", "schema": "virelai-world-model-v4", "content_sha256": "0" * 64,
             "manifest": {"persist_reason": "RUN_END", "status": "ACTIVE"}, "levels": [first, second]}
    text = world_report.render_world_report(model)
    assert _scene_claims(text, 2)[0].startswith("- as of transition 6, life ")
    for line in _scene_claims(text, 2):
        assert line.rsplit("refs: ", 1)[1].split(", ")[-1] == "t4-t6"
        assert line.rsplit("refs: ", 1)[1].split(", ")[0] == "levels[1].entry"
    assert _scene_claims(text, 1)[0].rsplit("refs: ", 1)[1].split(", ")[-1] == "t1-t3"
    _assert_report_refs(model, text)


def test_a_live_view_never_writes_a_report(k008, tmp_path):
    from inference.framework import world_report
    from inference.framework.world_model_v2 import seal

    live = seal({**{k: v for k, v in k008.items() if k != "content_sha256"},
                 "manifest": {**k008["manifest"], "persist_reason": "LIVE_VIEW"}})
    assert not world_report.write_world_report(live, tmp_path).ok and not (tmp_path / "world_report.md").exists()


def test_a_failed_update_never_leaves_a_stale_report_for_another_model(k008, carry, tmp_path, monkeypatch):
    from inference.framework import world_report

    assert world_report.write_world_report(carry, tmp_path).ok
    monkeypatch.setattr(world_report, "render_world_report", lambda model: (_ for _ in ()).throw(RuntimeError("boom")))
    result = world_report.write_world_report(k008, tmp_path)
    assert not result.ok and "boom" in result.error
    report = tmp_path / "world_report.md"
    assert not report.exists() or k008["content_sha256"] in report.read_text()
    assert not report.exists() or carry["content_sha256"] not in report.read_text()


def test_the_cancelled_run_writes_the_report_beside_the_model(tmp_path):
    from test_wo_l2a_census_paths import _cancelled_before_first_turn

    folder, _game, _calls = _cancelled_before_first_turn(tmp_path)
    model = json.loads((folder / "world_model.json").read_text())
    assert model["content_sha256"] in (folder / "world_report.md").read_text()


def test_a_report_failure_keeps_the_model_and_records_a_warning(tmp_path, monkeypatch):
    from inference.framework import world_report
    from test_wo_l2a_census_paths import _cancelled_before_first_turn

    monkeypatch.setattr(world_report, "render_world_report", lambda model: (_ for _ in ()).throw(RuntimeError("boom")))
    folder, _game, _calls = _cancelled_before_first_turn(tmp_path)
    assert json.loads((folder / "world_model.json").read_text())["schema"] == "virelai-world-model-v4"
    assert not (folder / "world_report.md").exists()
    warnings = [json.loads(line) for line in (folder / "observer_warnings.jsonl").read_text().splitlines()]
    assert any(item.get("event") == "WORLD_REPORT_WRITE_FAILED" for item in warnings)
