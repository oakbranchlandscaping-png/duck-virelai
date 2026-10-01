"""Controlled POINTER adapter between a semantic-library snapshot and lever-depth planner.

Unlike the planner, this adapter is allowed to nominate a concrete pointer coordinate.  It is
still not wired into Duck or the production solver.  The caller remains responsible for
executing the action and returning the resulting frame.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from inference.framework.virelai_semantic.depth_probe import (
    ActivationObservation,
    LeverDepthPlanner,
)


def _plain_layers(frame: Any) -> list[list[list[int]]]:
    value = getattr(frame, "frame", frame)
    layers = value.tolist() if hasattr(value, "tolist") else value
    result = []
    for layer in layers:
        layer = layer.tolist() if hasattr(layer, "tolist") else layer
        result.append([
            [int(cell) for cell in (row.tolist() if hasattr(row, "tolist") else row)]
            for row in layer
        ])
    return result


class PointerDepthAdapter:
    """Translate POINTER probe requests into clicks and exact bounded observations."""

    def __init__(self, library: Mapping[str, Any], *, engineering_cap: int = 64) -> None:
        self.planner = LeverDepthPlanner(engineering_cap=engineering_cap)
        self._effect_boxes: dict[str, dict[str, tuple[int, int, int, int]]] = {}
        self.refresh(library)

    def refresh(self, library: Mapping[str, Any]) -> None:
        segments = library.get("segments", [])
        self.planner.refresh(segments)
        for segment in segments:
            mechanics = segment.get("lever_mechanics") or {}
            candidates = [
                (lever, "lever", "effect_channels") for lever in mechanics.get("levers", [])
            ] + [
                (control, "control", "self_effect_channels")
                for control in mechanics.get("reactive_controls", [])
            ]
            for lever, handle_key, channels_key in candidates:
                handle = str(lever[handle_key])
                boxes = self._effect_boxes.setdefault(handle, {})
                for channel in lever.get(channels_key, []):
                    bbox = channel.get("affected_bbox")
                    if bbox is not None:
                        boxes[str(channel["channel"])] = tuple(int(value) for value in bbox)

    def next_pointer_action(self) -> dict[str, Any]:
        request = self.planner.request()
        if request["status"] != "PROBE_REQUIRED":
            return request
        item = request["request"]
        if item["activation_mode"] != "POINTER_TARGET_REQUIRED":
            return {
                "status": "UNSUPPORTED_ACTIVATION_MODE",
                "request": item,
                "action": None,
            }
        bbox = item.get("bbox")
        if bbox is None:
            return {"status": "TARGET_GEOMETRY_MISSING", "request": item, "action": None}
        top, left, bottom, right = bbox
        return {
            "status": "ACTION_READY",
            "request": item,
            "action": {
                "action_name": "ACTION6",
                "row": (int(top) + int(bottom)) // 2,
                "col": (int(left) + int(right)) // 2,
            },
        }

    def observe_result(self, *, lever: str, step: int, frame: Any) -> None:
        layers = _plain_layers(frame)
        if not layers:
            raise ValueError("frame contains no layers")
        boxes = self._effect_boxes.get(lever, {})
        expected = self.planner.request().get("request") or {}
        channels = expected.get("channels_to_measure", [])
        states = {}
        for channel in channels:
            if channel not in boxes:
                raise ValueError(f"effect geometry missing for {lever}/{channel}")
            top, left, bottom, right = boxes[channel]
            crops = []
            for layer in layers:
                rows, cols = len(layer), len(layer[0]) if layer else 0
                if top < 0 or left < 0 or bottom >= rows or right >= cols:
                    raise ValueError(f"effect geometry outside frame for {lever}/{channel}")
                crops.append([
                    row[left : right + 1]
                    for row in layer[top : bottom + 1]
                ])
            states[channel] = {
                "shape": [len(layers[0]), len(layers[0][0]) if layers[0] else 0],
                "bbox": [top, left, bottom, right],
                "layers": crops,
            }
        self.planner.record(
            ActivationObservation(lever=lever, step=int(step), channel_states=states)
        )

    def report(self) -> dict[str, Any]:
        payload = self.planner.export()
        payload["adapter"] = "CONTROLLED_POINTER_V1"
        return payload


__all__ = ["PointerDepthAdapter"]
