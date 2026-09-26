from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

import pytest

from inference.framework.virelai_continuity import (
    ContinuityCompiler,
    arithmetic_signature,
    cut_visible_frame,
    pixel_arithmetic,
)
from inference.framework.virelai_runtime import CompactFrameRecord, VirelaiRuntime
from tools.grade_continuity_key import _validate_archive_provenance


@dataclass
class FakeFrame:
    frame: list[list[list[int]]]
    game_id: str = "continuity-fixture"
    guid: str = "continuity-guid"
    state: str = "NOT_FINISHED"
    levels_completed: int = 0
    win_levels: int = 3
    full_reset: bool = False
    available_actions: tuple[int, ...] = (1, 2, 3, 4, 6)


def _record(layer: list[list[int]], node: int, *, completed: int = 0):
    return CompactFrameRecord.from_frame(
        FakeFrame(frame=[layer], levels_completed=completed),
        node_index=node,
        frames_len=node + 1,
        action_id=None if node == 0 else 1,
        acted_cell=None,
    )


def _class_tracks(compiler: ContinuityCompiler, class_id: int):
    return [
        track
        for track in compiler.canonical_tracks()
        if track["observations"][0]["class_id"] == class_id
    ]


def test_pixel_arithmetic_is_total_and_never_invents_an_empty_cell():
    left = cut_visible_frame(_record([[1, 1], [0, 0]], 0), level=1)
    right = cut_visible_frame(_record([[1, 2], [0, 0]], 1), level=1)
    record = pixel_arithmetic(left, right)

    assert record["coverage_status"] == "TOTAL"
    assert record["site_count"] == 4
    assert record["held_cells"] == 3
    assert record["changed_cells"] == 1
    assert record["signed_class_delta"] == [[1, -1], [2, 1]]
    assert record["conservation_closes"] is True
    assert {
        (group["before_class"], group["after_class"], group["cell_count"])
        for group in record["transition_groups"]
    } == {(0, 0, 2), (1, 1, 1), (1, 2, 1)}


def test_footprint_signature_uses_neutral_membership_names_and_exact_rewrites():
    left = cut_visible_frame(_record([[1, 1, 0]], 0), level=1)
    right = cut_visible_frame(_record([[0, 1, 1]], 1), level=1)
    before = next(region for region in left.regions if region.class_id == 1)
    after = next(region for region in right.regions if region.class_id == 1)
    signature = arithmetic_signature(before, after, left, right)

    assert signature["lexicon_form"] == "MOVE"
    assert signature["translation"] == (0, 1)
    assert set(signature["membership_groups"]) == {
        "retained_same_value",
        "retained_rewritten",
        "prior_footprint_only",
        "later_footprint_only",
    }
    rendered = json.dumps(signature)
    assert "vacated" not in rendered and "claimed" not in rendered
    assert signature["membership_groups"]["prior_footprint_only"] == [{
        "before_class": 1,
        "after_class": 0,
        "outcome": "CHANGED",
        "cell_count": 1,
        "cell_runs": [(0, 0, 0)],
    }]
    assert signature["membership_groups"]["later_footprint_only"] == [{
        "before_class": 0,
        "after_class": 1,
        "outcome": "CHANGED",
        "cell_count": 1,
        "cell_runs": [(0, 2, 2)],
    }]


def test_unique_move_recolor_growth_and_shrink_keep_monotonic_handle():
    compiler = ContinuityCompiler(game_id="verbs", artifact_dir=None)
    frames = [
        [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 0, 2, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 2, 2, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 2, 0, 0], [0, 0, 0, 0]],
    ]
    for node, layer in enumerate(frames):
        compiler.submit(_record(layer, node), level=1)
    compiler.wait_until_idle()

    colored = [
        track
        for track in compiler.canonical_tracks()
        if track["observations"][0]["class_id"] == 1
    ]
    assert len(colored) == 1
    assert [stitch["verb"] for stitch in colored[0]["stitches"]] == [
        "MOVE",
        "RECOLOR",
        "GROW",
        "SHRINK",
    ]
    assert [item["node_index"] for item in colored[0]["observations"]] == [0, 1, 2, 3, 4]
    compiler.close()


def test_identical_candidates_abstain_instead_of_forcing_identity(tmp_path):
    compiler = ContinuityCompiler(game_id="ambiguous", artifact_dir=tmp_path)
    compiler.submit(
        _record([[0, 0, 0], [0, 1, 0], [0, 0, 0]], 0),
        level=1,
    )
    compiler.submit(
        _record([[0, 0, 0], [1, 0, 1], [0, 0, 0]], 1),
        level=1,
    )
    summary = compiler.close()

    original = _class_tracks(compiler, 1)[0]
    assert original["end_reason"] == "AMBIGUOUS"
    assert original["stitches"] == []
    assert len(_class_tracks(compiler, 1)) == 3
    assert summary["ambiguous_terminations"] >= 1
    edges = [json.loads(line) for line in (tmp_path / "weave_edges.jsonl").read_text().splitlines()]
    assert any(item["verb"] == "AMBIGUOUS" for item in edges)


def test_unlicensed_deformation_and_geometry_change_terminate_identity():
    compiler = ContinuityCompiler(game_id="termination", artifact_dir=None)
    compiler.submit(_record([[0, 0, 0], [1, 1, 0], [0, 0, 0]], 0), level=1)
    compiler.submit(_record([[0, 0, 0], [1, 0, 0], [1, 0, 0]], 1), level=1)
    compiler.submit(_record([[0, 0], [0, 1]], 2), level=1)
    compiler.close()

    colored = _class_tracks(compiler, 1)
    assert colored[0]["end_reason"] == "DEFORM"
    assert colored[1]["end_reason"] == "GEOMETRY_CHANGE"
    assert colored[0]["track_id"] < colored[1]["track_id"] < colored[2]["track_id"]


def test_exact_partition_fence_remains_experimental_and_does_not_define_identity(tmp_path):
    compiler = ContinuityCompiler(game_id="split", artifact_dir=tmp_path)
    compiler.submit(
        _record([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0]], 0),
        level=1,
    )
    compiler.submit(
        _record([[0, 0, 0, 0], [0, 2, 1, 0], [0, 2, 1, 0]], 1),
        level=1,
    )
    compiler.close()

    original = _class_tracks(compiler, 1)[0]
    assert original["end_reason"] == "RUN_CLOSED"
    assert [item["verb"] for item in original["stitches"]] == ["SHRINK"]
    assert len(_class_tracks(compiler, 1)) == 1
    assert len([track for track in compiler.canonical_tracks()
                if track["observations"][0]["class_id"] in {1, 2}]) == 2
    golden = [json.loads(line) for line in (tmp_path / "golden_weave_edges.jsonl").read_text().splitlines()]
    accepted = [json.loads(line) for line in (tmp_path / "weave_edges.jsonl").read_text().splitlines()]
    experimental = [json.loads(line) for line in
                    (tmp_path / "experimental_partition_edges.jsonl").read_text().splitlines()]
    assert any(edge["verb"] == "SHRINK" for edge in golden)
    assert any(edge["verb"] == "SHRINK" for edge in accepted)
    assert any(edge["verb"] == "SPLIT" for edge in experimental)


def test_anchored_remainder_can_continue_as_shrink_through_color_exchange():
    compiler = ContinuityCompiler(game_id="anchored-shrink", artifact_dir=None)
    compiler.submit(_record([[1, 1, 1, 1]], 0), level=1)
    compiler.submit(_record([[1, 1, 1, 2]], 1), level=1)
    compiler.close()

    original = _class_tracks(compiler, 1)[0]
    assert original["end_reason"] == "RUN_CLOSED"
    assert [stitch["verb"] for stitch in original["stitches"]] == ["SHRINK"]
    assert original["stitches"][0]["witnesses"] == ["golden_cascade"]


def test_level_boundary_closes_all_tracks_and_never_reuses_ids():
    compiler = ContinuityCompiler(game_id="levels", artifact_dir=None)
    layer = [[0, 0], [0, 1]]
    compiler.submit(_record(layer, 0), level=1)
    compiler.submit(_record(layer, 1, completed=1), level=2)
    compiler.close()

    tracks = compiler.canonical_tracks()
    assert {track["level"] for track in tracks} == {1, 2}
    assert all(track["end_reason"] == "LEVEL_BOUNDARY" for track in tracks if track["level"] == 1)
    assert max(track["track_id"] for track in tracks if track["level"] == 1) < min(
        track["track_id"] for track in tracks if track["level"] == 2
    )


def test_runtime_persists_lossless_raw_and_canonical_shadow_artifacts(tmp_path):
    runtime = VirelaiRuntime(game_id="integrated", artifact_root=tmp_path)
    runtime.observe_initial(FakeFrame(frame=[[[0, 0, 0], [0, 1, 0]]]))
    runtime.observe_transition(
        frame=FakeFrame(frame=[[[0, 0, 0], [0, 0, 1]]]),
        action_id=4,
        action_name="RIGHT",
        acted_cell=None,
        actor="DUCK",
        result={"level": 1},
    )
    runtime.flush()

    root = tmp_path / "integrated"
    summary = json.loads((root / "summary.json").read_text())
    continuity = json.loads((root / "continuity_summary.json").read_text())
    fidelity = json.loads((root / "continuity_fidelity.json").read_text())
    tracks = json.loads((root / "continuity_tracks.json").read_text())
    assert summary["frames"] == 2
    assert summary["transitions"] == 1
    assert continuity["compiled_through_node"] == 1
    assert continuity["faults"] == 0
    assert continuity["duck_visible"] is False
    assert fidelity["passed"] is True
    assert fidelity["correctness_status"] == "REQUIRES_EXTERNAL_KEY"
    assert (root / "flipbook_cuts.json").is_file()
    assert (root / "pixel_arithmetic.jsonl").is_file()
    assert (root / "weave_edges.jsonl").is_file()
    arithmetic = [json.loads(line) for line in
                  (root / "pixel_arithmetic.jsonl").read_text().splitlines()]
    assert arithmetic[0]["site_count"] == 6
    assert arithmetic[0]["held_cells"] == 4
    assert arithmetic[0]["changed_cells"] == 2
    edges = [json.loads(line) for line in (root / "weave_edges.jsonl").read_text().splitlines()]
    move = next(edge for edge in edges if edge["verb"] == "MOVE")
    assert move["arithmetic_form"] == "MOVE"
    assert move["form_agrees"] is True
    assert "prior_footprint_only" in move["arithmetic_signature"]["membership_groups"]
    assert any(
        stitch["verb"] == "MOVE"
        for track in tracks
        for stitch in track["stitches"]
    )


def test_targeted_action_resolves_against_pre_action_sighting(tmp_path):
    runtime = VirelaiRuntime(game_id="pre-action", artifact_root=tmp_path)
    runtime.observe_initial(FakeFrame(frame=[[[0, 0, 0], [0, 1, 0]]]))
    runtime.observe_transition(
        frame=FakeFrame(frame=[[[0, 0, 0], [0, 0, 1]]]),
        action_id=6,
        action_name="CLICK",
        acted_cell=(1, 1),
        actor="DUCK",
        result={"level": 1},
    )
    runtime.flush()
    rows = [json.loads(line) for line in
            (tmp_path / "pre-action" / "acted_on.jsonl").read_text().splitlines()]
    assert rows == [{
        "action_id": 6,
        "issued_from_node": 0,
        "level": 1,
        "resolution_frame": "PRE_ACTION",
        "result_node": 1,
        "status": "RESOLVED",
        "target_cell": [1, 1],
        "window_id": 1,
        "worldline_id": 1,
    }]


def test_frozen_key_refuses_a_different_recording(tmp_path):
    frames_path = tmp_path / "game-a" / "frames.bin"
    frames_path.parent.mkdir()
    frames_path.write_bytes(b"labelled recording")
    digest = hashlib.sha256(frames_path.read_bytes()).hexdigest()
    key = {"archives": {"game-a": {"frames_bin_sha256": digest}}}

    assert _validate_archive_provenance(key, tmp_path)[0]["status"] == "MATCH"
    frames_path.write_bytes(b"different recording")
    with pytest.raises(ValueError, match="recording provenance mismatch"):
        _validate_archive_provenance(key, tmp_path)


def test_capture_does_not_wait_for_continuity_compilation(tmp_path, monkeypatch):
    import inference.framework.virelai_continuity as module

    original = module.segment_visible_components

    def delayed(*args, **kwargs):
        import time

        time.sleep(0.05)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "segment_visible_components", delayed)
    runtime = VirelaiRuntime(game_id="nonblocking", artifact_root=tmp_path)
    runtime.observe_initial(FakeFrame(frame=[[[0, 1]]]))
    capture = runtime.query("overview")["data"]["capture_performance"]
    assert capture["max_ms"] < 50.0
    runtime.flush()


def test_prefix_replay_is_deterministic_and_extension_never_renumbers_handles():
    frames = [
        [[0, 0, 0], [0, 1, 0]],
        [[0, 0, 0], [0, 0, 1]],
        [[0, 0, 0], [0, 1, 0]],
    ]
    short = ContinuityCompiler(game_id="prefix-short", artifact_dir=None)
    long = ContinuityCompiler(game_id="prefix-long", artifact_dir=None)
    for node, layer in enumerate(frames[:2]):
        short.submit(_record(layer, node), level=1)
        long.submit(_record(layer, node), level=1)
    short.wait_until_idle()
    long.wait_until_idle()

    def prefix_signature(compiler):
        return [
            {
                "track_id": track["track_id"],
                "observations": [item for item in track["observations"] if item["node_index"] <= 1],
                "stitches": [item for item in track["stitches"] if item["to_node"] <= 1],
            }
            for track in compiler.canonical_tracks()
            if track["born_node"] <= 1
        ]

    frozen_prefix = prefix_signature(short)
    assert prefix_signature(long) == frozen_prefix
    long.submit(_record(frames[2], 2), level=1)
    long.wait_until_idle()
    assert prefix_signature(long) == frozen_prefix
    short.close()
    long.close()
