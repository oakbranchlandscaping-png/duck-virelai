"""WO-DESC-A fail-first tests: the schema-v3 descriptive event ledger and scene state.

Author: Claude (Alpha build seat), 2026-10-13. Interface: ``INTERFACE_WO_DESC_A_v2_2026-10-13`` (Sol's review of
v1, "proceed with amendments"). Every transition of a level gets one record; every change gets an OBSERVED event
whose verb is the accepted continuity's verdict on a census track. An event says what happened, never why: its
explanation is recomputed from the certified tier and its receipts, and the validator refuses causal status, a
forged explanation and anything derived after the verified prefix.

Synthetic boards exercise the pure ``describe_level`` with the accepted weave only. The saved development
records exercise the production census. Imports of the new module stay inside the tests, so each test fails on
its own on ``5fdac9a``.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pickle
from pathlib import Path

import pytest

from inference.framework.library_census import board_cut, project_tracks

NINE = {"STILL", "RECOLOR", "MOVE", "GROW", "SHRINK", "BIRTH", "DEATH", "DEFORM", "AMBIGUOUS"}
ENTRY = {"source": "INITIAL_FRAME"}
FROZEN_V2 = Path(__file__).parent / "fixtures" / "world_model_v2_carry_v7_frozen.json"


def _module():
    from inference.framework import descriptive_events

    return descriptive_events


def _error():
    from inference.framework.world_model_v2 import WorldModelV2Error

    return WorldModelV2Error


# ---- synthetic worlds -----------------------------------------------------------------------------------------

def _board(size: int = 12, fill: int = 0) -> list[list[int]]:
    return [[fill] * size for _ in range(size)]


def _paint(board, cells, value):
    out = [row[:] for row in board]
    for r, c in cells:
        out[r][c] = value
    return out


def _block(top, left, height=2, width=2):
    return [(top + r, left + c) for r in range(height) for c in range(width)]


def _rows(boards, *, kinds=None, lives=None, start=1, acted=None, level=1):
    """Transition rows (the census's ``transition_index`` shape) between consecutive boards."""
    rows = []
    for index, (before, after) in enumerate(zip(boards, boards[1:])):
        transition = start + index
        changed = [[r, c, before[r][c], after[r][c]] for r in range(len(before)) for c in range(len(before[0]))
                   if before[r][c] != after[r][c]]
        kind = (kinds or {}).get(transition, "PROBE")
        site = (acted or {}).get(transition)
        action = {"action": "RESET"} if kind == "RESET" else (
            {"action": "ACTION6", "row": site[0], "col": site[1]} if site else {"action": "ACTION1"})
        rows.append({"transition_id": transition, "kind": kind, "level": level,
                     "life": (lives or {}).get(transition, 1), "action": action,
                     "acted_site": {"row": site[0], "col": site[1]} if site else None, "changed": changed,
                     "gate_id": "G1-EGO", "evidence_id": None if kind == "RESET" else f"E-synthetic-{transition:04d}",
                     "probe_id": None})
    return rows


def _describe(boards, **kwargs):
    rows = kwargs.pop("rows", None)
    if rows is None:
        rows = _rows(boards, **{k: kwargs.pop(k) for k in ("kinds", "lives", "acted") if k in kwargs})
    return _module().describe_level(1, tuple(map(tuple, boards[0])), ENTRY, rows, **kwargs), rows


def _events(description, transition=None):
    return [event for record in description["transitions"] for event in record["events"]
            if transition is None or record["transition_id"] == transition]


def _projection(boards, rows):
    return project_tracks(1, tuple(map(tuple, boards[0])), ENTRY, rows)


def _track_at(boards, rows, cells):
    """The census track whose first sighting has exactly these cells (accepted continuity, no new matcher)."""
    wanted = tuple(sorted(cells))
    hits = [track_id for track_id, steps in _projection(boards, rows)["steps"].items() if steps[0].cells == wanted]
    assert len(hits) == 1, hits
    return hits[0]


def _on(description, track_id, transition=None):
    return [e for e in _events(description, transition) if e["subject"]["track_id"] == track_id]


def _verbs_on(description, track_id):
    return [event["verb"] for event in _on(description, track_id)]


def _cells(runs):
    return [(row, col) for row, first, last in runs for col in range(first, last + 1)]


def _role_names(event):
    return [role["role"] for role in event["subject"]["roles"]]


def _exact(track_id):
    return {"status": "EXACT_ONE_TO_ONE", "track_id": track_id, "basis": {"key": "TEST"}}


UNRESOLVED = {"status": "UNRESOLVED", "track_id": None, "basis": None}


def _evidence(rows):
    return {row["evidence_id"]: {"transition_id": row["transition_id"], "gate_id": row["gate_id"], "probe_id": None}
            for row in rows if row["evidence_id"]}


def _context(boards, rows, *, roles=(), receipts=None, gaps=None):
    tracks = {track["track_id"] for track in _projection(boards, rows)["tracks"]}
    receipts = receipts or {"evidence": _evidence(rows), "products": {}, "witnesses": {}}
    return {"recorded": [row["transition_id"] for row in rows], "tracks": tracks, "receipts": receipts,
            "roles": list(roles), "gaps": gaps}


def _validate(description, context):
    _module().validate_description(description, recorded=context["recorded"], tracks=context["tracks"],
                                   receipts=context["receipts"], roles=context["roles"], gaps=context.get("gaps"))


def _refused(description, context, match=None):
    with pytest.raises(_error(), match=match):
        _validate(description, context)


# ---- 1 · the nine observation verbs, each on its own subject --------------------------------------------------

def test_move_recolor_grow_shrink_are_typed_on_their_subjects():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base,
              _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 3),           # MOVE 4 right
              _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 4),           # RECOLOR 3 -> 4
              _paint(_paint(base, _block(2, 2), 0), _block(2, 6, 2, 3), 4),     # GROW 2x2 -> 2x3
              _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 4)]           # SHRINK back to 2x2
    description, rows = _describe(boards)
    track = _track_at(boards, rows, _block(2, 2))
    assert _verbs_on(description, track) == ["MOVE", "RECOLOR", "GROW", "SHRINK"]
    (move,) = _on(description, track, 1)
    assert move["delta"]["translation"] == [0, 4] and move["before"]["anchor"] == [2, 2] and move["after"]["anchor"] == [2, 6]
    (recolor,) = _on(description, track, 2)
    assert recolor["delta"]["class"] == [3, 4]
    (grow,) = _on(description, track, 3)
    assert grow["delta"]["count"] == 2 and grow["delta"]["entered_sites"]["count"] == 2


def test_birth_and_death_are_events_not_omissions():
    base = _board()
    boards = [base, _paint(base, [(5, 5)], 7), base]
    description, rows = _describe(boards)
    born = [e for e in _events(description, 1) if e["verb"] == "BIRTH"]
    assert len(born) == 1 and born[0]["after"]["class"] == 7 and born[0]["before"] is None
    died = [e for e in _events(description, 2) if e["verb"] == "DEATH"]
    assert len(died) == 1 and died[0]["subject"]["track_id"] == born[0]["subject"]["track_id"]


def test_deform_and_ambiguous_are_honest_outcomes():
    base = _board()
    ell = [(3, 3), (4, 3), (5, 3), (5, 4)]
    line = [(3, 3), (3, 4), (3, 5), (3, 6)]
    description, _rows_ = _describe([_paint(base, ell, 2), _paint(base, line, 2)])
    assert "DEFORM" in {e["verb"] for e in _events(description, 1)}
    twin = [_paint(base, _block(5, 5), 3), _paint(_paint(base, _block(1, 1), 3), _block(9, 9), 3)]
    description, rows = _describe(twin)
    track = _track_at(twin, rows, _block(5, 5))
    ambiguous = _on(description, track, 1)
    assert [e["verb"] for e in ambiguous] == ["AMBIGUOUS"]
    assert ambiguous[0]["correspondence"]["ambiguity"] == "MULTIPLE_LICENSED_SUCCESSORS"


def _ego_world():
    """A still ego block, an unrelated block, one changed pixel elsewhere."""
    base = _paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6)
    boards = [base, _paint(base, [(0, 11)], 9)]
    rows = _rows(boards)
    ego = _track_at(boards, rows, _block(8, 8))
    roles = [{"role": "EGO", "gate_id": "G1-EGO", "product_id": "P-ego", "identity": _exact(ego)}]
    receipts = {"evidence": _evidence(rows), "products": {"P-ego": {"gate_id": "G1-EGO", "payload_sha256": "0" * 64}},
                "witnesses": {}}
    return boards, rows, ego, roles, receipts


def test_still_is_emitted_for_a_bound_track_and_every_still_is_counted():
    boards, rows, ego, roles, receipts = _ego_world()
    description, _ = _describe(boards, rows=rows, certified={"roles": roles, "scoped_nulls": []}, receipts=receipts)
    record = description["transitions"][0]
    still = [e for e in record["events"] if e["verb"] == "STILL"]
    assert [e["subject"]["track_id"] for e in still] == [ego] and _role_names(still[0]) == ["EGO"]
    assert record["still_emitted"] == 1 and record["still_omitted"] >= 1
    assert record["still_total"] == record["still_emitted"] + record["still_omitted"]
    assert {e["verb"] for e in _events(description)} <= NINE
    _validate(description, _context(boards, rows, roles=roles, receipts=receipts))


def test_still_totals_are_exact_against_the_accepted_weave():
    from inference.framework.virelai_continuity import re_join, weave_window

    base = _paint(_paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6), _block(8, 2), 5)
    boards = [base, _paint(base, [(0, 11)], 9), _paint(_paint(base, _block(8, 8), 0), _block(8, 9), 6)]
    description, rows = _describe(boards)
    cuts = [board_cut(board, node=index, level=1) for index, board in enumerate(boards)]
    for record in description["transitions"]:
        woven = sum(1 for line in re_join(weave_window(cuts), cuts) for edge in line.edges
                    if edge.verb == "STILL" and edge.now.node_index == record["transition_id"])
        assert record["still_total"] == woven > 0
        assert record["still_total"] == record["still_emitted"] + record["still_omitted"]
        assert record["still_emitted"] == sum(1 for e in record["events"] if e["verb"] == "STILL") == 0


def test_still_is_emitted_for_the_acted_site_track():
    base = _paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6)
    boards = [base, _paint(base, [(0, 11)], 9)]
    description, rows = _describe(boards, acted={1: (8, 9)})
    clicked = _track_at(boards, rows, _block(8, 8))
    still = [e for e in _events(description, 1) if e["verb"] == "STILL"]
    assert [e["subject"]["track_id"] for e in still] == [clicked] and still[0]["subject"]["roles"] == []
    assert still[0]["explanation"] == {"status": "UNEXPLAINED", "refs": [], "basis": still[0]["explanation"]["basis"]}


# ---- 2 · several changes, resets, transients, class changes, a broken record -----------------------------------

def test_one_transition_with_two_changes_gives_two_observed_events_and_no_cause():
    base = _paint(_paint(_board(), _block(2, 2), 3), _block(8, 2), 5)
    boards = [base, _paint(_paint(base, _block(2, 2), 4), _block(8, 2), 6)]
    description, _ = _describe(boards)
    recolors = [e for e in _events(description, 1) if e["verb"] == "RECOLOR"]
    assert len(recolors) == 2
    assert {e["status"] for e in _events(description)} == {"OBSERVED"}
    assert {e["explanation"]["status"] for e in recolors} == {"UNEXPLAINED"}


def test_a_reset_is_a_boundary_not_a_flood_of_births_and_lives_are_not_joined():
    base = _paint(_board(), _block(2, 2), 3)
    moved = _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 3)
    boards = [base, moved, base]
    description, rows = _describe(boards, kinds={2: "RESET"}, lives={2: 2})
    reset = description["transitions"][1]
    assert reset["kind"] == "RESET" and reset["events"] == []
    assert reset["boundary"]["kind"] == "RESET" and (reset["boundary"]["life_before"], reset["boundary"]["life_after"]) == (1, 2)
    assert reset["boundary"]["tracks_started"] >= 1 and reset["boundary"]["possible_correspondences"] >= 1


def test_a_transient_that_returns_is_flagged_and_band1_is_untouched():
    base = _paint(_board(), _block(4, 4), 3)
    boards = [base, _paint(base, _block(4, 4), 8), base]
    description, rows = _describe(boards)
    track = _track_at(boards, rows, _block(4, 4))
    (back,) = _on(description, track, 2)
    assert back["verb"] == "RECOLOR" and back["flags"]["returns_to_prior_state"] is True
    (first,) = _on(description, track, 1)
    assert first["flags"]["returns_to_prior_state"] is False
    assert "band1" not in json.dumps(description)  # the description makes no Band-1 change


def test_a_class_change_reopens_role_typing():
    base = _paint(_board(), _block(4, 4), 3)
    boards = [base, _paint(base, _block(4, 4), 5)]
    description, _ = _describe(boards)
    (event,) = [e for e in _events(description, 1) if e["verb"] == "RECOLOR"]
    assert event["flags"]["recolor"] is True and event["flags"]["reopens_role_typing"] is True


def _class_change_world():
    """A certified ego block recolors at 1 (its binding ends there), then moves at 2."""
    base = _paint(_board(), _block(4, 4), 3)
    recolored = _paint(base, _block(4, 4), 5)
    boards = [base, recolored, _paint(_paint(recolored, _block(4, 4), 0), _block(4, 7), 5)]
    rows = _rows(boards)
    ego = _track_at(boards, rows, _block(4, 4))
    role = {"role": "EGO", "gate_id": "G1-EGO", "product_id": "P-ego", "identity": _exact(ego)}
    receipts = {"evidence": _evidence(rows), "products": {"P-ego": {"gate_id": "G1-EGO", "payload_sha256": "0" * 64}},
                "witnesses": {}}
    description, _ = _describe(boards, rows=rows, certified={"roles": [role], "scoped_nulls": []}, receipts=receipts)
    return boards, rows, ego, role, receipts, description


def test_a_class_change_ends_the_role_binding_and_keeps_its_history():
    boards, rows, ego, role, receipts, description = _class_change_world()
    (recolor,) = _on(description, ego, 1)
    assert recolor["verb"] == "RECOLOR" and _role_names(recolor) == ["EGO"] and recolor["flags"]["role_binding_ends"]
    assert recolor["explanation"]["status"] == "UNEXPLAINED"  # G1's law covers displacement, not a class change
    (move,) = _on(description, ego, 2)
    assert move["verb"] == "MOVE" and move["subject"]["roles"] == []  # the old role is not carried on
    assert move["explanation"]["status"] == "UNEXPLAINED"
    (binding,) = description["role_bindings"]
    assert (binding["role"], binding["track_id"], binding["ends_at_transition"]) == ("EGO", ego, 1)
    (present,) = [item for item in description["scene"]["present"] if item["track_id"] == ego]
    assert present["roles"] == "UNRESOLVED_OBJECT" and present["class"] == 5
    ended = {**role, "binding_ends_at": 1}  # the census keeps the role (history) and records where it ended
    gap = {"subject": "EGO", "reason": "CLASS_CHANGED", "archetype_question": "q", "track_id": ego, "transitions": [1]}
    context = _context(boards, rows, roles=[ended], receipts=receipts, gaps=[gap])
    _validate(description, context)
    _refused(description, {**context, "roles": [role]}, "binding")          # the end was not recorded on the role
    _refused(description, {**context, "gaps": []}, "CLASS_CHANGED")          # the end has no typed gap


def test_a_broken_record_stops_the_description_at_the_verified_prefix():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, _paint(base, _block(2, 2), 4), _paint(_paint(base, _block(2, 2), 0), _block(6, 6), 5),
              _paint(_board(), [(11, 11)], 9)]
    rows = _rows(boards)
    rows[1]["changed"][0][2] = 9  # transition 2 claims a before-value the board does not hold
    description, _ = _describe(boards, rows=rows)
    assert description["integrity"] == "RECORD_MISMATCH"
    assert description["first_mismatch"] == {"transition_id": 2, "reason": "CONTRADICTED_BEFORE_VALUE"}
    assert description["transitions"][0]["record_status"] == "VERIFIED" and description["transitions"][0]["events"]
    for record in description["transitions"][1:]:
        assert record["record_status"] == "UNVERIFIED_AFTER_MISMATCH" and record["events"] == []
        assert record["still_total"] == record["still_emitted"] == record["still_omitted"] == 0
    scene = description["scene"]
    assert scene["as_of_transition"] == 1 and scene["record_mismatch"] == description["first_mismatch"]
    track = _track_at(boards, rows, _block(2, 2))
    (present,) = [item for item in scene["present"] if item["track_id"] == track]
    assert present["class"] == 4 and present["anchor"] == [2, 2]  # the board at 1, not a board rebuilt later
    assert all(span[1] <= 1 for spans in description["presence"].values() for span in spans)
    later = {t for t in _projection(boards, rows)["steps"] if t not in description["presence"]}
    assert later and later == set(scene["unverified_tracks"])


@pytest.mark.parametrize("fault", ["duplicate", "missing"])
def test_a_duplicate_or_missing_transition_ends_the_verified_prefix(fault):
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, _paint(base, _block(2, 2), 4), _paint(base, _block(2, 2), 5), _paint(base, _block(2, 2), 6)]
    rows = _rows(boards)
    rows = rows[:2] + [dict(rows[1])] + rows[2:] if fault == "duplicate" else [rows[0], rows[2]]
    description, _ = _describe(boards, rows=rows)
    expected = {"duplicate": (2, "DUPLICATE_TRANSITION"), "missing": (2, "MISSING_TRANSITION")}[fault]
    assert (description["first_mismatch"]["transition_id"], description["first_mismatch"]["reason"]) == expected
    assert [r["transition_id"] for r in description["transitions"]] == sorted({row["transition_id"] for row in rows})
    assert description["scene"]["as_of_transition"] == 1
    assert all(not r["events"] for r in description["transitions"] if r["transition_id"] >= 2)


def _entry_world():
    """Transition 1 changes one block and transitions 2 and 3 another, so dropping row 1 contradicts no
    before-value: only the entry board can show that the record does not begin where the level does."""
    base = _paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6)
    first = _paint(base, _block(2, 2), 4)
    return [base, first, _paint(first, _block(8, 8), 5), _paint(first, _block(8, 8), 7)]


def test_a_missing_first_transition_leaves_the_scene_at_the_entry_board():
    """Revision 1 (Sol): the expected first transition comes from the entry board, not from the first row. With
    transition 1 missing, nothing is verified: every row is unverified and the scene is the entry board."""
    boards = _entry_world()
    rows = _rows(boards)[1:]  # the first row, not an interior one, is missing
    description = _module().describe_level(1, tuple(map(tuple, boards[0])), ENTRY, rows)
    assert description["first_mismatch"] == {"transition_id": 1, "reason": "MISSING_TRANSITION"}
    assert description["basis"]["entry_node"] == 0
    assert [r["transition_id"] for r in description["transitions"]] == [2, 3]
    assert all(r["record_status"] == "UNVERIFIED_AFTER_MISMATCH" and not r["events"] for r in description["transitions"])
    scene = description["scene"]
    assert scene["as_of_transition"] is None and scene["as_of_node"] == 0
    assert sorted(item["class"] for item in scene["present"]) == [0, 3, 6]  # the entry board's objects
    assert all(spans == [[0, 0]] for spans in description["presence"].values())
    context = {"recorded": [2, 3], "tracks": set(_projection(boards, rows)["steps"]),
               "receipts": {"evidence": _evidence(rows), "products": {}, "witnesses": {}}, "roles": []}
    _validate(description, context)
    honest = _module().describe_level(1, tuple(map(tuple, boards[0])), ENTRY, _rows(boards))
    hidden = copy.deepcopy(honest)
    hidden["basis"]["entry_node"] = -1  # a ledger that would start one transition early
    _refused(hidden, {**context, "recorded": [1, 2, 3], "tracks": set(_projection(boards, _rows(boards))["steps"])},
             "contiguously")


@pytest.mark.parametrize(("start", "expected"), [(11, None), (12, (11, "MISSING_TRANSITION")),
                                                 (10, (10, "BEFORE_ENTRY"))])
def test_a_level_entry_board_sets_the_expected_first_transition(start, expected):
    boards = _entry_world()
    rows = _rows(boards, start=start)
    entry = {"source": "LEVEL_ENTRY", "after_transition": 10}
    description = _module().describe_level(1, tuple(map(tuple, boards[0])), entry, rows)
    assert description["basis"]["entry_node"] == 10
    mismatch = description["first_mismatch"]
    assert (None if mismatch is None else (mismatch["transition_id"], mismatch["reason"])) == expected
    verified = [r["transition_id"] for r in description["transitions"] if r["record_status"] == "VERIFIED"]
    assert verified == ([11, 12, 13] if expected is None else [])


@pytest.mark.parametrize("offending", [10, 9], ids=["at_the_entry", "below_the_entry"])
def test_a_transition_numbered_at_or_before_the_entry_leaves_the_entry_board_trusted(offending):
    """Revision 2 (Sol): a row numbered at or before the level-entry board cannot be placed after it. It and every
    later row stay unverified, yet the entry board itself stays trusted: the scene is exactly that board, its tracks
    are present, and nothing the offending row did enters the scene."""
    boards = _entry_world()  # the offending row recolors the 2x2 block 3 -> 4
    rows = _rows(boards, start=11)
    rows[0]["transition_id"] = offending
    entry = {"source": "LEVEL_ENTRY", "after_transition": 10}
    description = _module().describe_level(1, tuple(map(tuple, boards[0])), entry, rows)
    assert description["first_mismatch"] == {"transition_id": offending, "reason": "BEFORE_ENTRY"}
    assert [r["transition_id"] for r in description["transitions"]] == [offending, 12, 13]
    assert all(r["record_status"] == "UNVERIFIED_AFTER_MISMATCH" and not r["events"] and r["pixel_rewrite"] is None
               for r in description["transitions"])
    scene = description["scene"]
    assert scene["as_of_transition"] is None and scene["as_of_node"] == 10
    pristine = sorted((r.class_id, list(r.anchor), r.cell_count) for r in board_cut(boards[0], node=10, level=1).regions)
    assert sorted((p["class"], p["anchor"], p["cell_count"]) for p in scene["present"]) == pristine
    tracks = _module_tracks(boards, entry, rows)
    entry_tracks = {t["track_id"] for t in tracks if t["segments"][0]["first"] == entry}
    assert {p["track_id"] for p in scene["present"]} == entry_tracks  # each entry sighting is the entry's own
    assert not entry_tracks & set(scene["unverified_tracks"]) and scene["departed"] == []
    assert all(spans == [[10, 10]] for t, spans in description["presence"].items() if t in entry_tracks)
    assert set(description["presence"]) == entry_tracks
    _validate(description, {"recorded": [r["transition_id"] for r in rows], "tracks": {t["track_id"] for t in tracks},
                            "receipts": {"evidence": _evidence(rows), "products": {}, "witnesses": {}}, "roles": []})


def _module_tracks(boards, entry, rows):
    return project_tracks(1, tuple(map(tuple, boards[0])), entry, rows)["tracks"]


def test_a_level_entered_but_never_acted_in_is_described_by_its_entry_board():
    base = _paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6)
    description, _ = _describe([base], rows=[])
    assert description["transitions"] == [] and description["integrity"] == "VERIFIED"
    scene = description["scene"]
    assert scene["as_of_transition"] is None and scene["departed"] == [] and scene["unverified_tracks"] == []
    assert sorted(item["class"] for item in scene["present"]) == [0, 3, 6]
    _validate(description, {"recorded": [], "tracks": {i["track_id"] for i in scene["present"]},
                            "receipts": {"evidence": {}, "products": {}, "witnesses": {}}, "roles": []})


def test_every_recorded_transition_has_exactly_one_record_in_order():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, base, _paint(base, _block(2, 2), 4), _paint(base, _block(2, 2), 4)]
    description, rows = _describe(boards)
    assert [r["transition_id"] for r in description["transitions"]] == [row["transition_id"] for row in rows]
    assert description["transitions"][0]["events"] == [] and description["transitions"][2]["events"] == []


def test_the_same_inputs_describe_byte_identically():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, _paint(_paint(base, _block(2, 2), 0), _block(2, 6), 3), _paint(base, [(9, 9)], 7)]
    first, _ = _describe(boards)
    second, _ = _describe(copy.deepcopy(boards))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_the_scene_partitions_the_tracks_and_its_references_resolve():
    base = _paint(_paint(_board(), _block(2, 2), 3), [(9, 9)], 7)
    boards = [base, _paint(base, [(9, 9)], 0), _paint(_paint(base, [(9, 9)], 0), [(5, 5)], 8)]
    description, rows = _describe(boards)
    scene = description["scene"]
    present = {item["track_id"] for item in scene["present"]}
    departed = {item["track_id"] for item in scene["departed"]}
    unverified = set(scene["unverified_tracks"])
    tracks = set(_projection(boards, rows)["steps"])
    assert present | departed | unverified == tracks
    assert not (present & departed or present & unverified or departed & unverified)
    assert present == {t for t, spans in description["presence"].items() if any(a <= 2 <= b for a, b in spans)}
    events = {e["event_id"]: e for e in _events(description)}
    assert scene["unexplained"] and all(events[ref]["explanation"]["status"] == "UNEXPLAINED" for ref in scene["unexplained"])
    context = _context(boards, rows)
    _validate(description, context)
    forged = copy.deepcopy(description)
    forged["scene"]["unexplained"].append("EV-" + "0" * 16)
    _refused(forged, context, "unexplained")
    forged = copy.deepcopy(description)
    forged["scene"]["departed"].append(dict(forged["scene"]["present"][0], last_seen_node=1, end_reason="DEPARTED"))
    _refused(forged, context, "partition")


def test_event_ids_are_unique_and_each_event_sits_under_its_own_transition():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, _paint(base, _block(2, 2), 4), _paint(base, _block(2, 2), 5)]
    description, rows = _describe(boards)
    ids = [e["event_id"] for e in _events(description)]
    assert len(ids) == len(set(ids)) and all(e["transition_id"] == r["transition_id"]
                                             for r in description["transitions"] for e in r["events"])
    context = _context(boards, rows)
    forged = copy.deepcopy(description)
    forged["transitions"][1]["events"].append(copy.deepcopy(forged["transitions"][0]["events"][0]))
    _refused(forged, context)
    forged = copy.deepcopy(description)
    forged["transitions"][0]["events"].append(copy.deepcopy(forged["transitions"][0]["events"][0]))
    _refused(forged, context, "unique")


def _sighting(cut, snapshot):
    """The cut's region a snapshot states (class, anchor and shape hash name exactly one sighting)."""
    (region,) = [r for r in cut.regions if (r.class_id, list(r.anchor), r.shape_hash)
                 == (snapshot["class"], snapshot["anchor"], snapshot["shape_hash"])]
    return region


def test_identity_and_verbs_are_the_accepted_continuitys():
    """Every subject is a census track, and every verb is the accepted weave's verdict on that sighting: the
    line's own edge for a continuation or bridge, the replayed ``weave_edge`` cascade for a terminal verdict.
    Every footprint equals the accepted ``arithmetic_signature``'s membership groups."""
    from inference.framework.virelai_continuity import arithmetic_signature, re_join, weave_edge, weave_window

    base = _paint(_paint(_board(), _block(2, 2), 3), [(10, 1)], 7)
    ell = [(6, 6), (7, 6), (8, 6), (8, 7)]
    twin_cells = _block(0, 9)
    boards = [base,
              _paint(_paint(_paint(base, _block(2, 2), 0), _block(2, 5), 3), ell, 2),             # MOVE, BIRTH
              _paint(_paint(_paint(_paint(base, _block(2, 2), 0), _block(2, 5), 4), [(6, 6), (6, 7), (6, 8), (6, 9)], 2),
                     [(10, 1)], 0),                                                               # RECOLOR, DEFORM, DEATH
              _paint(_paint(_paint(_paint(base, _block(2, 2), 0), _block(2, 5), 0), twin_cells, 4), _block(9, 9), 4)]
    description, rows = _describe(boards)
    projection = _projection(boards, rows)
    owner = {(step.node_index, step.cells): track for track, steps in projection["steps"].items() for step in steps}
    cuts = [board_cut(board, node=index, level=1) for index, board in enumerate(boards)]
    lines = re_join(weave_window(cuts), cuts)
    woven = {(edge.now.node_index, edge.now.cells): edge for line in lines for edge in line.edges if edge.now is not None}
    seen = set()
    for event in _events(description):
        t, verb = event["transition_id"], event["verb"]
        seen.add(verb)
        cascade = weave_edge(cuts[t - 1].regions, cuts[t].regions)
        after = _sighting(cuts[t], event["after"]) if event["after"] else None
        prior = event["correspondence"].get("gap_from", t - 1)  # a resumed track was last seen before the gap
        before = _sighting(cuts[prior], event["before"]) if event["before"] else None
        subject = owner[(t, after.cells)] if after else owner[(prior, before.cells)]
        assert event["subject"]["track_id"] == subject  # the census track that owns the sighting
        if verb == "BIRTH":
            assert before is None and any(e.verb == "BIRTH" and e.now == after for e in cascade)
            continue
        if after is None:  # a terminal verdict: the replayed cascade's, on that very sighting
            (edge,) = [e for e in cascade if e.prev == before]
            assert edge.verb == verb and edge.now is None
        else:
            edge = woven[(t, after.cells)]
            assert edge.verb == verb and edge.prev == before
            signature = arithmetic_signature(before, after, cuts[t - 1], cuts[t])["membership_groups"]
            held = sum(group["cell_count"] for group in signature.pop("retained_same_value"))
            assert event["delta"]["footprint"] == json.loads(json.dumps(
                {"membership_groups": signature, "retained_same_value_cells": held}))
    assert {"MOVE", "BIRTH", "RECOLOR", "DEATH", "AMBIGUOUS", "DEFORM"} <= seen
    resumed = [e for e in _events(description) if "gap_from" in e["correspondence"]]
    assert resumed and {e["correspondence"]["witness"] for e in resumed} <= {"occlusion", "exact_return"}


# ---- 3 · explanations are recomputed from the certified tier, and forgeries are refused -------------------------

MASK = [(0, c) for c in range(6)]


def _counter_world(edit=None):
    """A counter bar (5) whose mask law rewrites 5 -> 0, and a certified ego block (3).

    1: tick (0,5) 5->0 · 2: the ego moves · 3: a refill (0,5) 0->5 · 4: tick (0,5) again and the ego moves back."""
    base = _paint(_paint(_board(), MASK, 5), _block(6, 6), 3)
    b1 = _paint(base, [(0, 5)], 0)
    b2 = _paint(_paint(b1, _block(6, 6), 0), _block(6, 8), 3)
    b3 = _paint(b2, [(0, 5)], 5)
    b4 = _paint(_paint(_paint(b3, [(0, 5)], 0), _block(6, 8), 0), _block(6, 6), 3)
    boards = [base, b1, b2, b3, b4]
    rows = _rows(boards)
    ego = _track_at(boards, rows, _block(6, 6))
    roles = [{"role": "EGO", "gate_id": "G1-EGO", "product_id": "P-ego", "identity": _exact(ego)},
             {"role": "COUNTER", "gate_id": "G2-COUNTER", "product_id": "P-ctr", "identity": UNRESOLVED}]
    receipts = {"evidence": _evidence(rows), "witnesses": {}, "products": {
        "P-ego": {"gate_id": "G1-EGO", "payload_sha256": "0" * 64},
        "P-ctr": {"gate_id": "G2-COUNTER", "payload_sha256": "1" * 64,
                  "mask": {"cell_runs": [[0, 0, 5]], "cell_count": 6, "rewrite": {"from": 5, "to": 0},
                           "law_version_id": "MASK-v1"}}}}
    gaps = [{"subject": "COUNTER", "reason": "IDENTITY_UNRESOLVED", "archetype_question": "q"}]
    if edit is not None:
        edit(rows, receipts)
    description, _ = _describe(boards, rows=rows, certified={"roles": roles, "scoped_nulls": []}, receipts=receipts)
    return boards, rows, ego, description, _context(boards, rows, roles=roles, receipts=receipts, gaps=gaps)


def _changed(event):
    groups = event["delta"]["footprint"]["membership_groups"]
    return {cell for name in ("retained_rewritten", "prior_footprint_only", "later_footprint_only")
            for group in groups.get(name) or () if group["before_class"] != group["after_class"]
            for cell in _cells(group["cell_runs"])}


def test_the_mask_law_explains_only_its_own_rewrite_inside_its_mask():
    boards, rows, ego, description, context = _counter_world()
    _validate(description, context)
    ticks = [e for e in _events(description, 1) if e["verb"] != "STILL"]  # the bound ego's STILL is no tick
    assert len(ticks) == 2 and {e["explanation"]["status"] for e in ticks} == {"EXPLAINED"}
    assert all(e["explanation"]["refs"] == ["E-synthetic-0001", "P-ctr"] for e in ticks)
    refill = [e for e in _events(description, 3) if _changed(e)]
    assert refill and all(_changed(e) <= set(MASK) for e in refill)
    assert "EXPLAINED" not in {e["explanation"]["status"] for e in refill}  # an inverse rewrite is not the law
    mixed = [e for e in _events(description, 4) if _changed(e) - set(MASK)]
    assert mixed and "EXPLAINED" not in {e["explanation"]["status"] for e in mixed}
    (tick4,) = [e for e in _events(description, 4) if e["verb"] == "SHRINK" and _changed(e) <= set(MASK)]
    assert tick4["explanation"]["status"] == "EXPLAINED"
    (move,) = _on(description, ego, 2)
    assert move["explanation"] == {"status": "PARTLY_EXPLAINED", "refs": ["P-ego"], "basis": move["explanation"]["basis"]}
    assert description["scene"]["open_identity"] == [{"role": "COUNTER", "gate_id": "G2-COUNTER", "subject": "COUNTER"}]
    _refused(description, {**context, "gaps": []}, "open_identity")  # an open identity names its gap


def _forge(description, transition, pick, explanation):
    forged = copy.deepcopy(description)
    record = next(r for r in forged["transitions"] if r["transition_id"] == transition)
    event = next(e for e in record["events"] if pick(e))
    event["explanation"] = explanation
    return forged


def test_a_forged_mask_explanation_is_refused():
    boards, rows, ego, description, context = _counter_world()
    claim = {"status": "EXPLAINED", "refs": ["E-synthetic-0002", "P-ctr"], "basis": "forged"}
    outside = _forge(description, 2, lambda e: e["subject"]["track_id"] == ego, claim)
    _refused(outside, context, "explanation")                                    # an event outside the mask
    inverse = _forge(description, 3, lambda e: bool(_changed(e)),
                     {**claim, "refs": ["E-synthetic-0003", "P-ctr"]})
    _refused(inverse, context, "explanation")                                    # the wrong rewrite inside the mask
    wrong_product = _forge(description, 1, lambda e: True,
                           {"status": "EXPLAINED", "refs": ["E-synthetic-0001", "P-ego"], "basis": "forged"})
    _refused(wrong_product, context, "explanation")                              # a true claim, the wrong product
    wrong_transition = _forge(description, 1, lambda e: True,
                              {"status": "EXPLAINED", "refs": ["E-synthetic-0002", "P-ctr"], "basis": "forged"})
    _refused(wrong_transition, context, "explanation")                           # a true claim, the wrong transition
    wrong_object = _forge(description, 3, lambda e: bool(_changed(e)),
                          {"status": "PARTLY_EXPLAINED", "refs": ["P-ego"], "basis": "forged"})
    _refused(wrong_object, context, "explanation")                               # the ego's claim on another object
    pixels = copy.deepcopy(description)
    event = next(e for e in pixels["transitions"][1]["events"] if e["subject"]["track_id"] == ego)
    event["delta"]["footprint"]["membership_groups"]["later_footprint_only"][0]["cell_runs"] = [[0, 0, 0]]
    _refused(pixels, context, "pixel")                                           # changed sites the record never saw


def _drop_receipt(rows, receipts):
    del receipts["evidence"]["E-synthetic-0001"]


def _no_evidence_id(rows, receipts):
    rows[0]["evidence_id"] = None
    del receipts["evidence"]["E-synthetic-0001"]


def _receipt_of_another_transition(rows, receipts):
    receipts["evidence"]["E-synthetic-0001"]["transition_id"] = 2


@pytest.mark.parametrize("edit", [_drop_receipt, _no_evidence_id, _receipt_of_another_transition])
def test_the_mask_law_explains_nothing_on_a_transition_without_its_own_evidence(edit):
    """Revision 1 (Sol): a G2 explanation needs the transition's own evidence receipt, and cites it beside the
    product. Without it the tick stays UNEXPLAINED, and an EXPLAINED claim citing the product alone is refused."""
    boards, rows, ego, description, context = _counter_world(edit)
    ticks = [e for e in _events(description, 1) if e["verb"] != "STILL"]
    assert len(ticks) == 2 and {e["explanation"]["status"] for e in ticks} == {"UNEXPLAINED"}
    (later,) = [e for e in _events(description, 4) if e["verb"] == "SHRINK"]
    assert later["explanation"] == {"status": "EXPLAINED", "refs": ["E-synthetic-0004", "P-ctr"], "basis": "G2_MASK_LAW"}
    if edit is not _receipt_of_another_transition:  # a receipt index naming another transition is itself refused
        _validate(description, context)
        product_only = _forge(description, 1, lambda e: e["verb"] != "STILL",
                              {"status": "EXPLAINED", "refs": ["P-ctr"], "basis": "G2_MASK_LAW"})
        _refused(product_only, context, "explanation")


def _lever_world():
    """A clicked lever (4) and a remote door (6) that recolors at its witness; an unrelated pixel changes too."""
    base = _paint(_paint(_paint(_board(), _block(2, 8), 4), [(8, 1), (8, 2), (8, 3)], 6), [(10, 10)], 9)
    b1 = _paint(_paint(base, [(8, 1), (8, 2), (8, 3)], 7), [(10, 10)], 8)
    b2 = _paint(b1, [(11, 0)], 2)
    boards = [base, b1, b2]
    rows = _rows(boards, acted={1: (2, 8), 2: (2, 8)})
    lever = _track_at(boards, rows, _block(2, 8))
    door = _track_at(boards, rows, [(8, 1), (8, 2), (8, 3)])
    module = _module()
    witnesses = {}
    for wid, transition, remote in (("W-1", 1, [[8, 1, 3]]), ("W-2", 2, [[11, 0, 0]])):
        receipt = {"entity_id": "E1", "member_id": "M1", "evidence_ref": f"E-synthetic-{transition:04d}",
                   "transition_id": transition, "channel": "CLICK",
                   "residue": {"local_runs": [], "remote_runs": remote, "cell_count": len(_cells(remote))}}
        witnesses[wid] = {**receipt, "witness_sha256": module.witness_sha256(wid, receipt)}
    roles = [{"role": "LEVER", "gate_id": "G3-LEVERS", "entity_id": "E1", "witness_refs": ["W-1", "W-2"],
              "identity": _exact(lever)}]
    receipts = {"evidence": _evidence(rows), "products": {}, "witnesses": witnesses}
    description, _ = _describe(boards, rows=rows, certified={"roles": roles, "scoped_nulls": []}, receipts=receipts)
    return boards, rows, lever, door, description, _context(boards, rows, roles=roles, receipts=receipts)


def test_a_lever_witness_partly_explains_only_its_own_residue():
    boards, rows, lever, door, description, context = _lever_world()
    _validate(description, context)
    (recolor,) = _on(description, door, 1)
    assert recolor["verb"] == "RECOLOR" and recolor["explanation"]["status"] == "PARTLY_EXPLAINED"
    assert recolor["explanation"]["refs"] == ["W-1"]
    other = [e for e in _events(description, 1) if e["subject"]["track_id"] not in {door, lever}]
    assert other and {e["explanation"]["status"] for e in other} == {"UNEXPLAINED"}
    (still,) = _on(description, lever, 1)
    assert still["verb"] == "STILL" and _role_names(still) == ["LEVER"]
    assert still["subject"]["roles"][0]["role_ref"] == "E1"
    claim = {"status": "PARTLY_EXPLAINED", "refs": ["W-1"], "basis": "forged"}
    outside = other[0]["event_id"]
    _refused(_forge(description, 1, lambda e: e["event_id"] == outside, claim), context, "explanation")
    _refused(_forge(description, 1, lambda e: e["subject"]["track_id"] == door, {**claim, "refs": ["W-2"]}),
             context, "explanation")                                                  # the wrong witness
    tampered = copy.deepcopy(context)
    tampered["receipts"]["witnesses"]["W-1"]["residue"]["remote_runs"] = [[10, 10, 10]]
    _refused(description, tampered, "witness")                                        # a residue its hash denies


# ---- 4 · the validator's basic refusals --------------------------------------------------------------------------

def _valid():
    base = _paint(_board(), _block(2, 2), 3)
    boards = [base, _paint(base, _block(2, 2), 4)]
    rows = _rows(boards)
    description, _ = _describe(boards, rows=rows)
    return description, _context(boards, rows)


def test_the_validator_accepts_an_honest_description():
    description, context = _valid()
    _validate(description, context)


@pytest.mark.parametrize("with_receipt", [False, True])
def test_caused_is_refused_in_the_event_ledger(with_receipt):
    description, context = _valid()
    event = description["transitions"][0]["events"][0]
    event["status"] = "CAUSED"
    if with_receipt:
        event["explanation"] = {"status": "EXPLAINED", "refs": ["P-g4"], "basis": "forged"}
        context["receipts"]["products"]["P-g4"] = {"gate_id": "G4-REACTIONS", "payload_sha256": "0" * 64}
    _refused(description, context, "causal")


def test_an_explanation_must_resolve_its_receipts():
    description, context = _valid()
    event = description["transitions"][0]["events"][0]
    event["explanation"] = {"status": "EXPLAINED", "refs": ["P-nowhere"], "basis": "forged"}
    _refused(description, context)


def test_a_role_on_an_event_must_be_bound_to_that_track():
    description, context = _valid()
    event = description["transitions"][0]["events"][0]
    event["subject"]["roles"] = [{"role": "LEVER", "gate_id": "G3-LEVERS", "role_ref": "W-forged"}]
    _refused(description, context, "role")


def test_a_forged_event_id_or_a_gap_in_coverage_is_refused():
    description, context = _valid()
    forged = copy.deepcopy(description)
    forged["transitions"][0]["events"][0]["event_id"] = "EV-" + "0" * 16
    _refused(forged, context)
    _refused(description, {**context, "recorded": [1, 2]})  # transition 2 has no record


# ---- 5 · the schema: v3 written, a genuine v2 artifact still read ------------------------------------------------

def test_a_frozen_genuine_v2_artifact_still_reads_after_the_v3_switch():
    """The fixture was written by the accepted v2 implementation (``5538816``) from a carry-v7 replay, before any
    DESC-A edit: not a v3 object with its description removed."""
    from inference.framework.world_model_v2 import SCHEMA, read_world_model, validate, validate_v2

    payload = json.loads(FROZEN_V2.read_text())
    assert payload["schema"] == "virelai-world-model-v2" and SCHEMA == "virelai-world-model-v5"
    assert not any("description" in level or '"mask"' in json.dumps(level["receipts"]) for level in payload["levels"])
    assert read_world_model(payload)["schema"] == "virelai-world-model-v2"
    validate_v2(payload)
    with pytest.raises(_error()):
        validate(payload)  # a v2 artifact is not a v3 model
    tampered = copy.deepcopy(payload)
    tampered["levels"][0]["gaps"][0]["reason"] = "BUDGET"
    with pytest.raises(_error(), match="content_sha256"):
        read_world_model(tampered)


# ---- 6 · the production census on saved records ----------------------------------------------------------------

def _execution(path, cut):
    from inference.framework.library_census import ExecutionRecord
    from inference.framework.record_replay import decode_grid, load_record

    record = load_record(path)
    return ExecutionRecord(entry_board=tuple(tuple(r) for r in decode_grid(record["initial_grid"])), entry_level=1,
                           valid_actions=tuple(record["valid_actions"]),
                           executed=tuple(step["action"]["action"] for step in record["steps"][:cut]))


def _model(path, transition_id, *, executed=None):
    from inference.framework.library_census import ExecutionRecord, compile_world_model
    from inference.framework.record_replay import load_record
    from inference.framework.world_model_v2 import seal
    from replay_checkpoints import checkpoint

    record = load_record(path)
    cut = next(i for i, step in enumerate(record["steps"]) if step["transition_id"] == transition_id)
    machine = checkpoint(path, max_steps=cut, measure=False).machine
    execution = _execution(path, cut)
    if executed is not None:
        execution = ExecutionRecord(execution.entry_board, 1, execution.valid_actions, executed(execution.executed))
    before = hashlib.sha256(pickle.dumps(machine)).hexdigest()
    model = seal(compile_world_model(machine, execution, game_id="g", run_stem="g_p0", persist_reason="BUDGET_STOP"))
    assert hashlib.sha256(pickle.dumps(machine)).hexdigest() == before  # the census mutates nothing
    return model, machine


@pytest.fixture(scope="module")
def k008():
    from test_g3_hybrid_lifecycle_replay import K008

    return _model(K008, 45)  # G1 and G2 certified; G3 in its NAV pass


def test_k008_compiles_to_v3_with_one_record_per_recorded_transition(k008):
    model, _machine = k008
    assert model["schema"] == "virelai-world-model-v5"
    for level in model["levels"]:
        records = level["description"]["transitions"]
        assert [r["transition_id"] for r in records] == level["record"]["transition_ids"]
        assert level["description"]["integrity"] == "VERIFIED"


def test_k008_counter_ticks_are_explained_by_the_mask_law_and_ego_moves_stay_visible(k008):
    """The certified COUNTER is a spatial mask, so its law explains exactly its own rewrite inside the mask,
    whatever track it touches. k008's EGO identity is unresolved at this cut (no current-life join is guessed),
    so the role attaches to no event, its moves stay visible and UNEXPLAINED, and the scene names the gap."""
    model, machine = k008
    (level,) = model["levels"]
    roles = {role["role"]: role for role in level["certified"]["roles"]}
    law = machine.target_journal.active_product("G2-COUNTER").payload["mask_law"]
    mask = {tuple(cell) for cell in law["cells"]}
    source, target = (int(v) for v in law["rewrite"].split("->"))
    receipt = level["receipts"]["products"][roles["COUNTER"]["product_id"]]["mask"]
    assert receipt["rewrite"] == {"from": source, "to": target} and set(_cells(receipt["cell_runs"])) == mask
    events = [e for record in level["description"]["transitions"] for e in record["events"]]

    def rewrites(event):
        groups = event["delta"]["footprint"]["membership_groups"]
        return {(g["before_class"], g["after_class"]) for name in ("retained_rewritten", "prior_footprint_only",
                "later_footprint_only") for g in groups.get(name) or () if g["before_class"] != g["after_class"]}

    ticks = [e for e in events if _changed(e) and _changed(e) <= mask and rewrites(e) == {(source, target)}]
    assert ticks and {e["explanation"]["status"] for e in ticks} == {"EXPLAINED"}
    assert all(roles["COUNTER"]["product_id"] in e["explanation"]["refs"] for e in ticks)
    other = [e for e in events if e not in ticks]
    assert other and "EXPLAINED" not in {e["explanation"]["status"] for e in other}
    assert roles["EGO"]["identity"]["status"] == "UNRESOLVED"
    assert not any("EGO" in _role_names(e) for e in events)
    moves = [e for e in events if e["verb"] == "MOVE"]
    assert moves and {e["explanation"]["status"] for e in moves} == {"UNEXPLAINED"}
    assert {e["status"] for e in events} == {"OBSERVED"}
    assert {"role": "EGO", "gate_id": "G1-EGO", "subject": "EGO"} in level["description"]["scene"]["open_identity"]


def test_carry_v7_lever_witness_partly_explains_its_residue_and_causes_nothing():
    """A G3 witness is an attributed activation: the residue it recorded at its transition is PARTLY_EXPLAINED
    by that witness (the noun is admitted; the mechanism is G4's). Nothing is EXPLAINED by it, nothing is CAUSED."""
    from test_wo_l2a_hooks import CARRY

    model, machine = _model(CARRY, 20)
    level = model["levels"][0]
    witnesses = level["receipts"]["witnesses"]
    cited = {ref for role in level["certified"]["roles"] if role["role"] == "LEVER" for ref in role["witness_refs"]}
    residue = {}
    for rows_ in machine._adapters["G3-LEVERS"].evidence._witnesses.values():
        for witness in rows_:
            residue[witness.witness_id] = {tuple(c) for c in witness.local_residue_cells} | {
                tuple(c) for c in witness.remote_residue_cells}
    by_transition = {w["transition_id"]: ref for ref, w in witnesses.items() if ref in cited}
    events = [e for record in level["description"]["transitions"] for e in record["events"]]
    at_witness = [e for e in events if e["transition_id"] in by_transition and e["verb"] != "STILL"
                  and _changed(e) and _changed(e) <= residue[by_transition[e["transition_id"]]]]
    assert at_witness and {e["explanation"]["status"] for e in at_witness} == {"PARTLY_EXPLAINED"}
    assert all(by_transition[e["transition_id"]] in e["explanation"]["refs"] for e in at_witness)
    lever_tracks = {role["identity"]["track_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER"}
    on_levers = [e for e in events if e["subject"]["track_id"] in lever_tracks]
    assert on_levers and all(_role_names(e) == ["LEVER"] for e in on_levers)
    assert not any(e["explanation"]["status"] == "EXPLAINED" and set(e["explanation"]["refs"]) & set(witnesses)
                   for e in events)
    assert "CAUSED" not in json.dumps(level["description"])


def test_a_journal_mismatch_at_h2_truncates_the_description_to_its_verified_prefix():
    from test_g3_hybrid_lifecycle_replay import K008

    model, _machine = _model(K008, 45, executed=lambda names: names[:29] + ("ACTION9",) + names[30:])
    (level,) = model["levels"]
    description = level["description"]
    assert description["first_mismatch"] == {"transition_id": 30, "reason": "JOURNAL_CHECK"}
    assert all(not r["events"] for r in description["transitions"] if r["transition_id"] >= 30)
    assert any(r["events"] for r in description["transitions"] if r["transition_id"] < 30)
    assert description["scene"]["as_of_transition"] == 29
    assert all(span[1] <= 29 for spans in description["presence"].values() for span in spans)
    assert level["accounting"]["status"] == "NOT_ACCOUNTED"


def test_a_level_observed_but_never_acted_in_carries_its_description():
    from inference.framework.library_census import ExecutionRecord, compile_world_model
    from inference.framework.world_model_v2 import seal

    board = tuple(map(tuple, _paint(_paint(_board(), _block(2, 2), 3), _block(8, 8), 6)))
    model = seal(compile_world_model(None, ExecutionRecord(board, 1, ("ACTION1",), ()), game_id="g", run_stem="s",
                                     persist_reason="CANCELLED"))
    (level,) = model["levels"]
    assert model["schema"] == "virelai-world-model-v5" and level["description"]["transitions"] == []
    assert {item["track_id"] for item in level["description"]["scene"]["present"]} == {
        track["track_id"] for track in level["observation"]["tracks"]}


def test_two_compilations_of_one_state_are_byte_identical(k008):
    from inference.framework.library_census import ExecutionRecord, compile_world_model
    from inference.framework.world_model_v2 import canonical_bytes, seal

    model, machine = k008
    level = model["levels"][0]
    execution = ExecutionRecord(entry_board=tuple(tuple(r) for r in machine.ego._initial_grid), entry_level=1,
                                valid_actions=tuple(level["entry"]["valid_actions"]),
                                executed=tuple(str(r["action"]["action"]) for r in machine.transition_index))
    first = canonical_bytes(seal(compile_world_model(machine, execution, game_id="g", run_stem="s", persist_reason="BUDGET_STOP")))
    second = canonical_bytes(seal(compile_world_model(machine, execution, game_id="g", run_stem="s", persist_reason="BUDGET_STOP")))
    assert first == second and b'"description"' in first
