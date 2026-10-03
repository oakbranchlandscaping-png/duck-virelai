"""Render observed semantic mechanics as a concise player-facing physics grammar."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compile_grammar(library: dict[str, Any]) -> dict[str, Any]:
    levels = []
    for segment in library.get("segments", []):
        mechanics = segment.get("lever_mechanics") or {}
        controls = []
        for index, item in enumerate(mechanics.get("reactive_controls", []), start=1):
            visible = item.get("visible") or {}
            channels = item.get("self_effect_channels") or []
            typing = channels[0].get("typing", {}) if channels else {}
            rewrites = sorted({
                (row["before"][0], row["after"][0])
                for channel in channels for row in channel.get("transitions", [])
            })
            controls.append({
                "name": f"Control {chr(64 + index)}",
                "kind": "SELF_REACTIVE",
                "location": visible.get("bbox"),
                "size_cells": visible.get("cells"),
                "current_integer_classes": visible.get("integer_classes", []),
                "observed_rule": {
                    "mechanism": typing.get("mechanism", "UNKNOWN"),
                    "period": typing.get("period"),
                    "status": typing.get("status", "UNMEASURED"),
                    "class_rewrites": [list(pair) for pair in rewrites],
                    "observations": sum(channel.get("observations", 0) for channel in channels),
                },
                "known_effect": "Clicking changes this same visual object.",
            })
        source_levers = mechanics.get("levers", [])
        lever_names = {
            item["lever"]: f"Remote lever {chr(64 + index)}"
            for index, item in enumerate(source_levers, start=1)
        }
        target_visible = {
            target["target"]: target.get("visible")
            for item in source_levers for target in item.get("targets", [])
            if target.get("visible") is not None
        }
        shared = []
        shared_handles = set()
        for relation in mechanics.get("shared_controls", []):
            shared_handles.update((relation["lever_a"], relation["lever_b"]))
            shared.append({
                "kind": relation["kind"],
                "lever_a": lever_names.get(relation["lever_a"], "Unresolved control"),
                "lever_b": lever_names.get(relation["lever_b"], "Unresolved control"),
                "effects": [
                    {
                        "region": (target_visible.get(effect["target"]) or {}).get("bbox"),
                        "lever_a_deltas": effect["lever_a_deltas"],
                        "lever_b_deltas": effect["lever_b_deltas"],
                    }
                    for effect in relation.get("affected_targets", [])
                ],
            })
        remote = []
        for index, item in enumerate(source_levers, start=1):
            visible = item.get("visible") or {}
            effects = [] if item["lever"] in shared_handles else [
                {
                    "region": channel.get("affected_bbox"),
                    "direction": channel.get("direction"),
                    "type": (channel.get("typing") or {}).get("mechanism", "UNKNOWN"),
                    "period": (channel.get("typing") or {}).get("period"),
                    "observations": channel.get("observations", 0),
                }
                for channel in item.get("effect_channels", [])
            ]
            if not effects and item["lever"] not in shared_handles:
                continue
            remote.append({
                "name": f"Remote lever {chr(64 + index)}",
                "location": visible.get("bbox"),
                "size_cells": visible.get("cells"),
                "current_integer_classes": visible.get("integer_classes", []),
                "effects": effects,
            })
        levels.append({
            "level": segment.get("level"),
            "world_mode": segment.get("control", {}).get("kind", "UNKNOWN_UNKNOWN"),
            "self_reactive_controls": controls,
            "remote_levers": remote,
            "shared_control_relations": shared,
            "independent_process_observed": bool(
                mechanics.get("masked_action_independent_worldlines", [])
            ),
            "still_unknown": [
                "Winning condition has not been established.",
                "Unlisted visual objects have no sealed mechanic in this record.",
            ],
        })
    return {
        "schema": "virelai-player-physics-grammar-v1",
        "game": library.get("game_id"),
        "basis": "Observed action-indexed transitions only.",
        "levels": levels,
    }


def render_markdown(grammar: dict[str, Any]) -> str:
    lines = [
        f"# Physics grammar — {grammar['game']}", "",
        f"Basis: {grammar['basis']}", "",
    ]
    for level in grammar["levels"]:
        mode = "CLICK (pointer actions)" if level["world_mode"] == "POINTER" else level["world_mode"]
        lines.extend([f"## Level {level['level']}", "", f"World type: {mode}."])
        if level["independent_process_observed"]:
            lines.append(
                "A repeating display process changes independently after actions; it is not "
                "listed as an effect of the controls below."
            )
        lines.extend(["", "### Controls", ""])
        if not level["self_reactive_controls"] and not level["remote_levers"]:
            lines.append("No control mechanic was sealed from the observed actions.")
        for control in level["self_reactive_controls"]:
            rule = control["observed_rule"]
            type_text = rule["mechanism"]
            if rule.get("period") is not None:
                type_text += f" with period {rule['period']}"
            lines.append(
                f"- {control['name']}: {control['size_cells']} cells at bbox "
                f"{control['location']}; current integer class "
                f"{control['current_integer_classes']}. Clicking changes this same object. "
                f"Observed rewrites {rule['class_rewrites']}. Type: {type_text} "
                f"({rule['status']}, {rule['observations']} observations)."
            )
        for lever in level["remote_levers"]:
            lines.append(
                f"- {lever['name']}: {lever['size_cells']} cells at bbox {lever['location']}; "
                f"current integer class {lever['current_integer_classes']}."
            )
            for effect in lever["effects"]:
                lines.append(
                    f"  - Changes region {effect['region']}: {effect['direction']}; "
                    f"type {effect['type']} ({effect['observations']} observations)."
                )
        if level["shared_control_relations"]:
            lines.extend(["", "### Shared mechanics", ""])
            for relation in level["shared_control_relations"]:
                lines.append(
                    f"- {relation['kind']}: {relation['lever_a']} and {relation['lever_b']} "
                    f"reverse {len(relation['effects'])} common visible effects."
                )
                for effect in relation["effects"]:
                    lines.append(
                        f"  - Region {effect['region']}: {relation['lever_a']} produced "
                        f"{effect['lever_a_deltas']}; {relation['lever_b']} produced "
                        f"{effect['lever_b_deltas']}."
                    )
        lines.extend(["", "### Unknown", ""])
        lines.extend(f"- {item}" for item in level["still_unknown"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("library", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    grammar = compile_grammar(json.loads(args.library.read_text(encoding="utf-8")))
    if args.json_output:
        args.json_output.write_text(json.dumps(grammar, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(grammar), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(render_markdown(grammar))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
