"""Render a shadow semantic library for human grading."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(path: Path) -> str:
    library = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        f"# Semantic Library Review — {library['game_id']}",
        "",
        f"Observed: {library['observed_nodes']} frames; levels {library['levels_observed']}; "
        f"record pristine: {library['record_pristine']}.",
        "",
        "> Shadow evidence only. Role labels are unvalidated detector verdicts, not player facts.",
    ]
    for segment in library["segments"]:
        control = segment["control"]
        lines.extend([
            "",
            f"## {segment['segment']} — nodes {segment['first_node']}–{segment['last_node']}",
            "",
            f"Control: {control['kind']} ({control['status']}); {control['witness_count']} witness transitions.",
            "",
            "### Role verdicts",
            "",
        ])
        typed = []
        for entity in segment["semantic_entities"]:
            for role in entity["roles"]:
                state = entity["current"]
                typed.append(
                    f"- {role['role']}: `{entity['handle']}` — integer classes "
                    f"{state['integer_classes']}, {state['cells']} cells, bbox {state['bbox']}; "
                    f"{role['witness_count']} witnesses; {role['status']}."
                )
        lines.extend(typed or ["- No role predicate sealed in this segment."])
        changed = [row for row in segment["joint_deltas"] if row["visible_cells_rewritten"]]
        lines.extend([
            "",
            "### Action-indexed evidence",
            "",
            f"{len(segment['joint_deltas'])} actions recorded; {len(changed)} changed the visible grid. "
            "The canonical JSON contains every object's exact entered and departed sites.",
        ])
        mechanics = segment.get("lever_mechanics", {})
        lines.extend(["", "### Lever mechanics", ""])
        if not mechanics.get("levers"):
            lines.append("- No lever was sealed from the observed evidence.")
        lever_names = {
            lever["lever"]: f"Lever {chr(65 + index)}"
            for index, lever in enumerate(mechanics.get("levers", []))
        }
        for lever in mechanics.get("levers", []):
            repeated = [target for target in lever["targets"] if target["observations"] >= 2]
            visible = lever.get("visible") or {}
            subject = "Contact surface" if lever.get("kind") == "CONTACT_SURFACE" else lever_names[lever["lever"]]
            components = (
                f"{visible.get('components')} visual components; "
                if lever.get("kind") == "CONTACT_SURFACE" else ""
            )
            lines.append(
                f"- **{subject}**: integer classes {visible.get('integer_classes')}, "
                f"{visible.get('cells')} cells, bbox {visible.get('bbox')}; "
                f"{components}"
                f"{lever['attributed_presses']} attributed presses; "
                f"{lever['null_presses']} visibly null; {len(repeated)} repeatedly affected targets."
            )
            for channel in lever.get("effect_channels", []):
                if channel["integer_class_before"] is None:
                    continue
                lines.append(
                    f"  - Effect region class {channel['integer_class_before']}, "
                    f"bbox {channel['affected_bbox']}: {channel['direction']}; "
                    f"{channel['observations']} observations; deltas {channel['cell_count_deltas']}."
                )
                typing = channel.get("typing", {})
                lines.append(
                    f"    - Type: {typing.get('mechanism')} ({typing.get('status')}); "
                    f"condition: {typing.get('condition')}."
                )
        for relation in mechanics.get("shared_controls", []):
            lines.append(
                f"- **Shared control:** {lever_names.get(relation['lever_a'], relation['lever_a'])} and "
                f"{lever_names.get(relation['lever_b'], relation['lever_b'])} "
                f"repeatedly reverse {len(relation['affected_targets'])} common visible effects."
            )
            lines.append(f"  - Limit: {relation['interpretation_limit']}")
    lines.extend(["", "## Not yet compiled", "", "State variables, win cause, and cross-level transfer.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("library", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = render(args.library)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
