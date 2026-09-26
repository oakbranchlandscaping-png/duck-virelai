from __future__ import annotations

import pytest

from inference.framework.virelai_semantic.depth_adapter import PointerDepthAdapter


def _library(kind="VISUAL_OBJECT"):
    return {
        "segments": [{
            "lever_mechanics": {
                "levers": [{
                    "lever": "L-A",
                    "kind": kind,
                    "visible": {"bbox": [0, 2, 1, 3]},
                    "effect_channels": [{
                        "channel": "E-1",
                        "affected_bbox": [1, 0, 1, 1],
                    }],
                }]
            }
        }]
    }


def test_pointer_adapter_chooses_an_inside_cell_and_preserves_request():
    adapter = PointerDepthAdapter(_library())
    result = adapter.next_pointer_action()
    assert result["status"] == "ACTION_READY"
    assert result["action"] == {"action_name": "ACTION6", "row": 0, "col": 2}
    assert result["request"]["lever"] == "L-A"


def test_adapter_measures_only_exact_effect_bbox_across_all_layers():
    adapter = PointerDepthAdapter(_library(), engineering_cap=1)
    frame = [
        [[9, 9, 8, 8], [1, 2, 3, 4]],
        [[7, 7, 6, 6], [5, 6, 7, 8]],
    ]
    adapter.observe_result(lever="L-A", step=1, frame=frame)
    channel = adapter.report()["levers"][0]["channels"]["E-1"]
    assert channel["observations"] == 1
    assert channel["novel_states"] == 1


def test_body_surface_is_explicitly_unsupported_by_pointer_adapter():
    adapter = PointerDepthAdapter(_library(kind="CONTACT_SURFACE"))
    result = adapter.next_pointer_action()
    assert result["status"] == "UNSUPPORTED_ACTIVATION_MODE"
    assert result["action"] is None


def test_effect_bbox_outside_frame_fails_instead_of_clipping():
    adapter = PointerDepthAdapter(_library())
    with pytest.raises(ValueError, match="outside frame"):
        adapter.observe_result(lever="L-A", step=1, frame=[[[0]]])


def test_self_reactive_control_enters_same_pointer_depth_queue():
    library = {
        "segments": [{
            "lever_mechanics": {
                "levers": [],
                "reactive_controls": [{
                    "control": "R-A",
                    "kind": "SELF_REACTIVE_CONTROL",
                    "visible": {"bbox": [2, 2, 3, 3]},
                    "self_effect_channels": [{
                        "channel": "SELF-1",
                        "affected_bbox": [2, 2, 3, 3],
                    }],
                }],
            }
        }]
    }
    adapter = PointerDepthAdapter(library)
    result = adapter.next_pointer_action()
    assert result["status"] == "ACTION_READY"
    assert result["request"]["lever"] == "R-A"
    assert result["request"]["channels_to_measure"] == ["SELF-1"]
    assert result["action"] == {"action_name": "ACTION6", "row": 2, "col": 2}
