"""WO-PE-03C: the key contract, its validator, the mapping sheet and the key-authoring frame view (interface §3).

Author: Claude (Alpha build seat), 2026-10-25. Base ``0f2e703``. Every key item here is synthetic, written by the build
seat for code tests only (``method: SYNTHETIC_TEST``), and is refused for formal grading. On the base every test fails:
``inference.paper_evidence`` does not exist.
"""
from __future__ import annotations

import gzip
import json
import subprocess

import pytest

from pe03_support import (AGENT, COUNTER_BAR, GOLDEN_VC33, LEVER_A, NOWHERE, VC33, item, model, obj, packet,
                          synthetic_key)
from inference.paper_evidence import keys, mapping


def test_01_a_well_formed_synthetic_key_validates_and_gets_content_ids():
    key = keys.validate(synthetic_key(), formal=False)
    ids = [i["key_id"] for i in key["items"]]
    assert len(ids) == len(set(ids)) and all(len(v) == 64 for v in ids)
    assert ids == [keys.item_id({k: v for k, v in i.items() if k != "key_id"}) for i in key["items"]]


def test_02_a_synthetic_key_is_refused_for_formal_grading():
    with pytest.raises(keys.KeyError_) as refused:
        keys.validate(synthetic_key())
    assert any("SYNTHETIC_TEST" in reason for reason in refused.value.reasons)
    assert any("construction.commit" in reason for reason in refused.value.reasons)


@pytest.mark.parametrize("mutate, expected", [
    (lambda k: k.update(schema="other"), "schema must be"),
    (lambda k: k["items"].append(dict(k["items"][0])), "duplicate key item"),
    (lambda k: k["items"][0].update(predicate="ROLE_MAYBE"), "has no predicate"),
    (lambda k: k["items"][0].update(object="INERT"), "must be one of"),
    (lambda k: k["items"][0]["subject"]["geometry"].update(bbox=[27, 60, 24, 63]), "ordered"),
    (lambda k: k["items"][0]["subject"].update(geometry=None), "geometry or a description"),
    (lambda k: k["items"][0].update(level=9), "not in the key's levels"),
    (lambda k: k["construction"].update(entry_frames={}), "entry_frames[1]"),
    (lambda k: k["construction"].pop("blind_to_reports"), "blind_to_reports"),
    (lambda k: k["construction"].update(frozen_on="tomorrow"), "frozen_on"),
    (lambda k: k["items"][0].update(key_id="0" * 64), "does not match its content"),
])
def test_03_each_malformed_key_is_refused_with_its_reason(mutate, expected):
    key = synthetic_key()
    mutate(key)
    found = keys.problems(key, formal=False)
    assert any(expected in reason for reason in found), found


def test_03b_conflicting_single_valued_key_items_are_refused():
    first = item(LEVER_A, "ROLE", "ROLE_IS", "LEVER")
    second = item(LEVER_A, "ROLE", "ROLE_IS", "COUNTER")
    found = keys.problems(synthetic_key([first, second]), formal=False)
    assert any("conflicting single-valued ROLE_IS" in reason for reason in found), found


def test_04_an_item_may_describe_an_object_first_seen_after_entry():
    later = {"type": "OBJECT", "handle": "the shape that appears", "description": "appears after the first click",
             "geometry": {"frame": "LATER"}}
    assert keys.problems(synthetic_key([item(later, "ROLE", "ROLE_IS", "LEVER")]), formal=False) == []


def test_05_levels_whose_entry_frame_differs_or_was_never_reached_are_excluded():
    key = synthetic_key(levels=(1, 2, 9))
    key["construction"]["entry_frames"]["2"] = "f" * 64
    excluded = keys.excluded_levels(key, packet(VC33)["stamp"])
    assert excluded == {"2": "ENTRY_FRAME_MISMATCH", "9": "LEVEL_NOT_REACHED"}


def test_06_the_mapper_proposes_exact_composite_and_unmatched():
    level3 = {str(l["level"]): l["entry"]["board_sha256"] for l in model(VC33)["levels"]}["3"]
    pair = obj("both small bars", (56, 24), (56, 24, 57, 29), 8, 9)
    key = synthetic_key([item(LEVER_A, "ROLE", "ROLE_IS", "LEVER"), item(NOWHERE, "ROLE", "ROLE_IS", "LEVER"),
                         item(COUNTER_BAR, "ROLE", "ROLE_IS", "COUNTER"), item(AGENT, "LAW", "CONTROL_MODE", "POINTER"),
                         item(pair, "ROLE", "ROLE_IS", "LEVER", level=3)], levels=(1, 3))
    assert key["construction"]["entry_frames"]["3"] == level3
    rows = {r["key_subject"]["handle"]: r for r in mapping.propose(packet(VC33), keys.validate(key, formal=False))["rows"]}
    assert rows["c9@24,60"]["outcome"] == "EXACT" and rows["c9@24,60"]["confirmed"]
    assert rows["c2@10,10"]["outcome"] == "UNMATCHED" and rows["c2@10,10"]["confirmed"] is None
    assert {s["type"] for s in rows["c7@0,0"]["proposed"]} == {"OBJECT", "COUNTER"}  # one object, held twice
    assert rows["agent"]["outcome"] == "EXACT"
    assert rows["both small bars"]["outcome"] == "EXACT"  # the solver's own composite lever has this exact union
    assert "+" in rows["both small bars"]["proposed"][0]["handle"]


def test_07_a_key_object_made_of_two_solver_objects_is_composite():
    """Synthetic packet: two separate solver objects whose union the key names as one."""
    def subject(handle, anchor, bbox, cells):
        return {"type": "OBJECT", "handle": handle, "geometry": {"frame": "ENTRY", "board_sha256": "a" * 64, "class": 9,
                                                                  "anchor": anchor, "bbox": bbox, "cell_count": cells}}
    claims = [{"level": 1, "kind": "PROPOSITION", "subject": subject(h, a, b, n)}
              for h, a, b, n in (("left", [0, 0], [0, 0, 1, 1], 4), ("right", [0, 4], [0, 4, 1, 5], 4))]
    fake = {"stamp": {"content_sha256": "b" * 64}, "claims": claims}
    key = synthetic_key([item(obj("wide", (0, 0), (0, 0, 1, 5), 8, 9), "ROLE", "ROLE_IS", "LEVER")])
    (row,) = mapping.propose(fake, keys.validate(key, formal=False))["rows"]
    assert row["outcome"] == "COMPOSITE" and sorted(s["handle"] for s in row["proposed"]) == ["left", "right"]
    assert row["confirmed"] is None  # a person confirms every non-exact mapping
    key = synthetic_key([item(obj("too wide", (0, 0), (0, 0, 1, 5), 9, 9), "ROLE", "ROLE_IS", "LEVER")])
    (row,) = mapping.propose(fake, keys.validate(key, formal=False))["rows"]
    assert row["outcome"] == "UNMATCHED"  # an inexact sum is never forced


def test_08_the_ancestry_check_is_git_s(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], capture_output=True, text=True, check=True).stdout.strip()
    git("init", "-q")
    for name in ("key", "evidence"):
        (tmp_path / name).write_text(name)
        git("add", name)
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", name)
    key_commit, evidence_commit = git("rev-parse", "HEAD~1"), git("rev-parse", "HEAD")
    assert keys.commit_is_ancestor(tmp_path, key_commit, evidence_commit)
    assert not keys.commit_is_ancestor(tmp_path, evidence_commit, key_commit)


def test_09_the_frame_view_lists_the_entry_objects_in_the_solver_s_own_segmentation(tmp_path):
    """The September golden recording's level-1 entry frame is the canary's: same board hash, same 11 objects."""
    import tools.paper_key_frames as frames

    recording = tmp_path / "vc33.golden.jsonl"
    recording.write_bytes(gzip.decompress(GOLDEN_VC33.read_bytes()))
    found = frames.listing(recording)
    level = model(VC33)["levels"][0]
    assert found["levels"]["1"]["board_sha256"] == level["entry"]["board_sha256"]
    entry_tracks = {(tuple(s["anchor"]), tuple(s["bbox"]), s["cell_count"], s["class_id"])
                    for s in (t["segments"][0] for t in level["observation"]["tracks"])
                    if s["first"]["source"] == "INITIAL_FRAME"}
    listed = {(tuple(o["anchor"]), tuple(o["bbox"]), o["cell_count"], o["class"]) for o in found["levels"]["1"]["objects"]}
    assert listed == entry_tracks
    assert frames.main([str(recording), "--out", str(tmp_path)]) == 0
    skeleton = json.loads((tmp_path / f"{VC33}_key_skeleton.json").read_text())
    assert skeleton["construction"]["entry_frames"] == {"1": level["entry"]["board_sha256"]} and skeleton["items"] == []
