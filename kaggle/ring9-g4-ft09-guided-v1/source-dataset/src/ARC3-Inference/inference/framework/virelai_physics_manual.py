"""Deterministic player projection of the canonical Virelai physics grammar.

This is a view, never a second knowledge store.  It deliberately renders only
admitted state variables and mechanics; object rosters and raw pixel deltas stay
behind focused queries.
"""
from __future__ import annotations

from typing import Any
from collections import Counter, defaultdict
import json

from inference.framework.virelai_world_model import WorldModel


def physics_manual(model: WorldModel, *, level: int | None = None) -> dict[str, Any]:
    selected_level = max(1, int(level or model.current_level))
    rules = [rule for rule in model.mechanics if selected_level in rule.levels_observed]
    component_ids = {
        component_id
        for rule in rules
        for component_id in rule.component_rule_ids
    }
    # A BODY contact surface can also be emitted as several one-cell reactive
    # fragments by the lower-level matcher.  Keep those in the canonical model,
    # but omit them from this player view when a witnessed joint rule already
    # covers the fragment's region and transitions.
    joint_surfaces = [
        rule for rule in rules
        if rule.subject_kind == "CONTACT_SURFACE" and rule.component_rule_ids and rule.subject_bbox
    ]
    covered_fragments = set()
    for rule in rules:
        if rule.subject_kind == "CONTACT_SURFACE" or not rule.affected_region:
            continue
        r0, c0, r1, c1 = rule.affected_region
        for surface in joint_surfaces:
            s0, t0, s1, t1 = surface.subject_bbox
            if (
                s0 <= r0 <= r1 <= s1 and t0 <= c0 <= c1 <= t1
                and set(rule.witness_transition_ids) <= set(surface.witness_transition_ids)
            ):
                covered_fragments.add(rule.rule_id)
                break
    variables_by_owner = {}
    for variable in model.state_variables:
        variables_by_owner.setdefault(variable.owner_id, []).append(variable)
    entries = []
    for rule in sorted(rules, key=lambda item: item.rule_id):
        if rule.rule_id in component_ids or rule.rule_id in covered_fragments:
            continue
        entries.append({
            "handle": rule.rule_id,
            "status": rule.status,
            "subjects": list(rule.subject_ids),
            "action": rule.trigger_action,
            "condition": rule.condition,
            "transformation": rule.transformation,
            "affected": list(rule.affected_ids),
            "affected_region": list(rule.affected_region) if rule.affected_region else None,
            "direction": rule.direction,
            "magnitude": rule.magnitude,
            "period": rule.period,
            "phase": rule.phase,
            "endpoint": rule.endpoint_behavior,
            "witness_count": len(rule.witness_transition_ids),
            "counterexample_count": len(rule.counterexample_transition_ids),
            "component_rule_count": len(rule.component_rule_ids),
            "parameters": list(rule.parameters),
            "class_rewrites": [list(row) for row in rule.class_rewrites],
            "signed_class_delta": [list(row) for row in rule.signed_class_delta],
            "decomposition": [json.loads(row) for row in rule.decomposition],
            "subject_bbox": list(rule.subject_bbox) if rule.subject_bbox else None,
            "subject_integer_classes": list(rule.subject_integer_classes),
            "subject_cell_count": rule.subject_cell_count,
            "subject_kind": rule.subject_kind,
            "state": [
                {
                    "handle": variable.variable_id,
                    "current": variable.current_value,
                    "ordered": variable.ordered,
                    "cyclic": variable.cyclic,
                    "endpoints": list(variable.endpoints),
                }
                for affected in rule.affected_ids
                for variable in variables_by_owner.get(affected, ())
            ],
            "expand": f"virelai('mechanic', id='{rule.rule_id}')",
        })
    return {
        "schema": "virelai-physics-manual-v1",
        "game_id": model.game_id,
        "level": selected_level,
        "world_mode": model.world_mode,
        "observed_through_step": model.observed_through_step,
        "mechanics": entries,
        "mechanics_total": len(entries),
        "unknowns": list(model.unknowns),
        "scope_note": (
            "These are scoped observations from recorded transitions. They are "
            "not guaranteed to hold in unobserved states or later levels."
        ),
    }


def render_physics_manual(manual: dict[str, Any]) -> str:
    lines = [
        f"VIRELAI PHYSICS GRAMMAR — LEVEL {manual['level']}",
        f"WORLD: {manual['world_mode']}",
        f"OBSERVED THROUGH STEP: {manual['observed_through_step']}",
        "",
        "MECHANICS",
    ]
    if not manual["mechanics"]:
        lines.append("- No mechanic has met the evidence gate.")
    grouped: dict[tuple[tuple[str, ...], str, str], list[dict[str, Any]]] = defaultdict(list)
    for rule in manual["mechanics"]:
        grouped[(tuple(rule["subjects"]), rule["action"], rule["status"])].append(rule)
    physical = [item for item in sorted(grouped.items()) if item[1][0].get("subject_kind") != "CONTROL_RELATION"]
    relations = [item for item in sorted(grouped.items()) if item[1][0].get("subject_kind") == "CONTROL_RELATION"]
    names: dict[str, str] = {}
    for control_index, ((subject_tuple, action, status), rules) in enumerate(physical, start=1):
        visible = next((rule for rule in rules if rule.get("subject_bbox")), rules[0])
        control_name = f"Control {chr(64 + control_index)}"
        for subject in subject_tuple:
            names[subject] = control_name
        control_detail = ""
        if visible.get("subject_bbox"):
            control_detail = (
                f" ({visible.get('subject_cell_count')} cells, integer classes "
                f"{visible.get('subject_integer_classes')}, bbox {visible['subject_bbox']})"
            )
        transforms = Counter(rule["transformation"] for rule in rules)
        directions = Counter(rule["direction"] for rule in rules if rule.get("direction"))
        # Counts deliberately summarize coordinated channels; exact subjects,
        # boxes, state values, and evidence remain behind the listed handles.
        lines.append(
            f"- {control_name}{control_detail} under {action} [{status}]: "
            f"{len(rules)} joint rule(s); "
            f"types={dict(sorted(transforms.items()))}; "
            f"directions={dict(sorted(directions.items())) or 'unmeasured'}; "
            f"at least {max((rule['witness_count'] for rule in rules), default=0)} witnessed press(es)."
        )
        for rule in rules:
            if rule.get("component_rule_count"):
                parameters = ", ".join(rule.get("parameters") or ())
                lines.append(
                    f"  joint arithmetic: {rule['component_rule_count']} exact effect channel(s); "
                    f"{parameters}."
                )
                if rule.get("class_rewrites"):
                    rewrites = [
                        f"{before}->{after} x{cells}"
                        for before, after, cells in rule["class_rewrites"]
                    ]
                    lines.append("  repeated class rewrite: " + ", ".join(rewrites))
                if rule.get("signed_class_delta"):
                    lines.append(
                        "  net class-count change per press: "
                        + ", ".join(f"class {kind}: {delta:+d}" for kind, delta in rule["signed_class_delta"])
                    )
                for part in rule.get("decomposition") or ():
                    phrase = (
                        f"{part['kind']}: {part['components_observed']} component(s) across "
                        f"{part['presses_observed']} press(es), shape {part['component_shape']}, "
                        f"{part['component_cells']} cells each"
                    )
                    if part.get("bearing") is not None:
                        phrase += f", affected patch advances by {part['bearing']}"
                    rewrites = part.get("class_rewrites") or []
                    if rewrites:
                        phrase += "; rewrites " + ", ".join(
                            f"{row['before_class']}->{row['after_class']} x{row['observations']}"
                            for row in rewrites[:10]
                        )
                        if len(rewrites) > 10:
                            phrase += f" (+{len(rewrites) - 10} more)"
                    lines.append("  sub-process: " + phrase + ".")
            state_edges = []
            for parameter in rule.get("parameters") or ():
                if not parameter.startswith("observed_state_transition="):
                    continue
                row = json.loads(parameter.split("=", 1)[1])
                before, after = row.get("before") or [], row.get("after") or []
                if before and after:
                    state_edges.append(
                        f"class {before[0]} -> class {after[0]}"
                        + (f" ({before[1]} cells)" if len(before) > 1 and before[1] is not None else "")
                    )
            if state_edges:
                lines.append("  observed state transitions: " + "; ".join(state_edges) + ".")
        boxes = [rule["affected_region"] for rule in rules if rule.get("affected_region")]
        if boxes:
            shown = boxes[:6]
            suffix = f" (+{len(boxes) - len(shown)} more)" if len(boxes) > len(shown) else ""
            lines.append(f"  affected bboxes: {shown}{suffix}")
        typed = [rule for rule in rules if rule.get("period") or rule.get("endpoint")]
        for rule in typed[:4]:
            lines.append(
                f"  {rule['handle']}: {rule['transformation']}; period={rule['period']}; "
                f"endpoint={rule['endpoint']}."
            )
        handles = ", ".join(rule["handle"] for rule in rules[:6])
        suffix = f" (+{len(rules) - 6} more)" if len(rules) > 6 else ""
        lines.append(f"  expand mechanic handles: {handles}{suffix}")
    for (subject_tuple, action, status), rules in relations:
        labels = [names.get(subject, subject) for subject in subject_tuple]
        relation_name = " and ".join(labels)
        targets = sorted({target for rule in rules for target in rule.get("affected", ())})
        lines.append(
            f"- Relationship between {relation_name} [{status}]: the pair repeatedly changed "
            f"the same visible target(s) in opposite directions; "
            f"{max((rule['witness_count'] for rule in rules), default=0)} exact press transition(s)."
        )
        lines.append(f"  shared targets: {', '.join(targets)}")
        lines.append("  limit: this does not prove that the targets are one hidden variable.")
        lines.append("  expand mechanic handles: " + ", ".join(rule["handle"] for rule in rules))
    if manual["unknowns"]:
        lines.extend(["", "UNKNOWNS"])
        lines.extend(f"- {item}" for item in manual["unknowns"])
    lines.extend(["", manual["scope_note"]])
    return "\n".join(lines)


__all__ = ["physics_manual", "render_physics_manual"]
