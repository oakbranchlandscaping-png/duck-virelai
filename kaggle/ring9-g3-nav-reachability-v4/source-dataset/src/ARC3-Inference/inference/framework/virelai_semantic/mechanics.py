"""Observed lever mechanics compiled from the masked, action-indexed weave residue."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Sequence

from virelai_golden.roles.infer import RoleRead
from virelai_golden.weave.worldline import Worldline, region_at
from inference.framework.virelai_semantic.typing import classify_effect_channel
from inference.framework.virelai_semantic.joint_transform import compile_joint_transformation

MIN_ACTION_INDEPENDENT_PRESSES = 8


def _bbox(cells: set[tuple[int, int]]) -> list[int] | None:
    if not cells:
        return None
    return [
        min(row for row, _ in cells), min(col for _, col in cells),
        max(row for row, _ in cells), max(col for _, col in cells),
    ]


def _group_visible(
    group: Sequence[int],
    semantic_of: dict[int, str],
    entity_by_handle: dict[str, Any],
) -> dict[str, Any] | None:
    entities = [
        entity_by_handle[semantic_of[actor]]
        for actor in group
        if actor in semantic_of and semantic_of[actor] in entity_by_handle
    ]
    if not entities:
        return None
    boxes = [entity.current.bbox for entity in entities if entity.current.bbox is not None]
    return {
        "integer_classes": sorted({value for entity in entities for value in entity.current.integer_classes}),
        "cells": sum(entity.current.cells for entity in entities),
        "bbox": None if not boxes else [
            min(box[0] for box in boxes), min(box[1] for box in boxes),
            max(box[2] for box in boxes), max(box[3] for box in boxes),
        ],
        "components": len(entities),
    }


def _shared_control_bundles(
    actors: Sequence[int],
    signed: dict[tuple[int, str], list[tuple[int, int]]],
    semantic_of: dict[int, str],
) -> list[dict[str, Any]]:
    """Group exact opposed effects by lever pair without inventing a state variable."""
    bundles: list[dict[str, Any]] = []
    for index, left in enumerate(sorted(actors)):
        for right in sorted(actors)[index + 1:]:
            common = sorted(
                {target for actor, target in signed if actor == left}
                & {target for actor, target in signed if actor == right}
            )
            targets = []
            for target in common:
                a_rows, b_rows = signed[(left, target)], signed[(right, target)]
                a = [delta for _, delta in a_rows]
                b = [delta for _, delta in b_rows]
                if len(a) < 2 or len(b) < 2:
                    continue
                sign_a = {(value > 0) - (value < 0) for value in a}
                sign_b = {(value > 0) - (value < 0) for value in b}
                if len(sign_a) == len(sign_b) == 1 and sign_a != sign_b:
                    targets.append({
                        "target": target,
                        "lever_a_deltas": a,
                        "lever_b_deltas": b,
                        "lever_a_witness_steps": sorted({step for step, _ in a_rows}),
                        "lever_b_witness_steps": sorted({step for step, _ in b_rows}),
                    })
            if targets:
                bundles.append({
                    "kind": "OPPOSED_DIRECTION_CONTROL_BUNDLE",
                    "status": "OBSERVED_REPEATEDLY",
                    "lever_a": semantic_of.get(left, f"UNRESOLVED-W{left:03d}"),
                    "lever_b": semantic_of.get(right, f"UNRESOLVED-W{right:03d}"),
                    "affected_targets": targets,
                    "interpretation_limit": (
                        "The same lever pair repeatedly reversed these visible effects. "
                        "The observations do not prove that the targets form one hidden variable."
                    ),
                })
    return bundles


def _co_attributed_actor_groups(
    read: RoleRead, actors: Sequence[int] | None = None,
) -> list[tuple[int, ...]]:
    """Group BODY candidates only when their complete attributed-press histories are equal.

    This is an interaction-surface grouping, not an object-identity merge.  A multi-cell
    destination can give several visual worldlines to the ego on every contact.  Naming each
    fragment as an independent lever repeats one causal event several times.
    """
    actors = sorted(read.levers.verdicts) if actors is None and read.levers is not None else sorted(actors or ())
    signatures: dict[tuple[tuple[int, int, int | None], ...], list[int]] = defaultdict(list)
    for actor in actors:
        signature = tuple(
            (press.left, press.right, press.action)
            for press in read.levers.presses
            if actor in press.attributed
        )
        signatures[signature].append(actor)
    return [tuple(group) for _, group in sorted(signatures.items(), key=lambda item: item[1][0])]


def _action_independent_partner_ids(read: RoleRead) -> set[int]:
    """Find partners changing throughout an action-diverse consecutive press suffix.

    This is the semantic bridge to Ring 8's clock predicate.  POINTER actions share one numeric
    action id, so diversity here means distinct targeted worldlines.  A partner is masked only
    when it appears on every press in an eight-press suffix, at least two different targets were
    pressed, and the changing partner was never itself the target in that suffix.
    """
    if read.levers is None:
        return set()
    presses = list(read.levers.presses)
    candidates = {partner for press in presses for partner in press.partners}
    masked: set[int] = set()
    for partner in candidates:
        suffix = []
        for press in reversed(presses):
            if partner not in press.partners:
                break
            suffix.append(press)
        suffix.reverse()
        if len(suffix) < MIN_ACTION_INDEPENDENT_PRESSES:
            continue
        targets = {actor for press in suffix for actor in press.attributed}
        if len(targets) < 2 or partner in targets:
            continue
        masked.add(partner)
    return masked


def _effect_channels(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rejoin re-minted target worldlines by an exact visible effect footprint.

    Continuing target identity joins its own rows.  Re-minted targets join only when their
    pre-class and exact affected support agree.  Neither route asserts that the successive
    worldlines are one persistent visual object.
    """
    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    by_target: dict[str, int] = {}
    by_footprint: dict[tuple[Any, ...], int] = {}
    for index, row in enumerate(rows):
        target = row["target"]
        if target in by_target:
            union(index, by_target[target])
        else:
            by_target[target] = index
        bbox = tuple(row["affected_bbox"]) if row.get("affected_bbox") else None
        footprint = (row.get("integer_class_before"), bbox)
        if footprint in by_footprint:
            union(index, by_footprint[footprint])
        else:
            by_footprint[footprint] = index
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[find(index)].append(row)
    channels = []
    for ordinal, (_, members) in enumerate(
        sorted(grouped.items(), key=lambda item: min(row["right_node"] for row in item[1])), start=1
    ):
        per_edge: dict[tuple[int, int], dict[str, Any]] = {}
        for row in members:
            edge = (row["left_node"], row["right_node"])
            score = (
                row["integer_class_before"] is not None,
                row["cell_count_delta"] is not None,
                row["cells_before"] is not None and row["cells_after"] is not None,
            )
            held = per_edge.get(edge)
            held_score = (-1, -1, -1) if held is None else (
                held["integer_class_before"] is not None,
                held["cell_count_delta"] is not None,
                held["cells_before"] is not None and held["cells_after"] is not None,
            )
            if score > held_score:
                per_edge[edge] = row
        unique = list(per_edge.values())
        unique.sort(key=lambda row: (row["right_node"], row["target"]))
        if len(unique) < 2:
            continue
        deltas = [row["cell_count_delta"] for row in unique if row.get("cell_count_delta")]
        if deltas and all(value > 0 for value in deltas):
            direction = "INCREASES_CELL_COUNT"
        elif deltas and all(value < 0 for value in deltas):
            direction = "DECREASES_CELL_COUNT"
        elif deltas:
            direction = "MIXED_CELL_COUNT_DIRECTION"
        elif any(row["integer_class_before"] != row["integer_class_after"] for row in unique):
            direction = "CLASS_REWRITE_WITHOUT_SIZE_CHANGE"
        else:
            direction = "VISIBLE_CHANGE_WITHOUT_SIZE_DIRECTION"
        transitions = [
            {
                "left_node": row["left_node"],
                "right_node": row["right_node"],
                "before": [row["integer_class_before"], row["cells_before"], row["anchor_before"]],
                "after": [row["integer_class_after"], row["cells_after"], row["anchor_after"]],
            }
            for row in unique
        ]
        channels.append({
            "channel": f"EFFECT_CHANNEL-{ordinal:02d}",
            "status": "OBSERVED_REPEATEDLY",
            "observations": len(unique),
            "integer_class_before": unique[0]["integer_class_before"],
            "cells_before_observed": sorted({row["cells_before"] for row in unique if row["cells_before"] is not None}),
            "affected_bbox": unique[0]["affected_bbox"],
            "direction": direction,
            "cell_count_deltas": deltas,
            "target_worldlines": sorted({row["target"] for row in unique}),
            "typing": classify_effect_channel(transitions),
            "transitions": transitions,
            "interpretation_limit": (
                "Repeated exact effect footprint; persistent object identity and mechanism type remain unproven."
            ),
        })
    return channels


def compile_lever_mechanics(
    *,
    segment: str,
    record: Any,
    read: RoleRead,
    worldlines: Sequence[Worldline],
    semantic_entities: Sequence[Any],
    raw_handle: Callable[[str, Worldline], str],
) -> dict[str, Any]:
    """Return literal effect profiles plus exact opposed-control relations.

    Nothing here asserts purpose.  `direction` names the signed cell-count outcomes actually
    seen for one actor/target pair.  Opposed control requires each lever to repeat one sign at
    least twice and the signs to differ.
    """
    if read.levers is None:
        return {"status": "UNMEASURED", "levers": [], "shared_controls": []}
    by_id = {worldline.id: worldline for worldline in worldlines}
    semantic_of: dict[int, str] = {}
    entity_by_handle = {entity.handle: entity for entity in semantic_entities}
    for entity in semantic_entities:
        members = set(entity.member_handles)
        for worldline in worldlines:
            if raw_handle(segment, worldline) in members:
                semantic_of[worldline.id] = entity.handle

    observations: dict[int, list[dict[str, Any]]] = defaultdict(list)
    self_observations: dict[int, list[dict[str, Any]]] = defaultdict(list)
    action_independent = _action_independent_partner_ids(read)
    attributed_counts: dict[int, int] = defaultdict(int)
    null_counts: dict[int, int] = defaultdict(int)
    self_only_counts: dict[int, int] = defaultdict(int)
    for press in read.levers.presses:
        for actor in press.attributed:
            before_actor = region_at(by_id[actor], press.left) if actor in by_id else None
            if before_actor is not None:
                before_grid = record.nodes[press.left].settled
                after_grid = record.nodes[press.right].settled
                support = set(before_actor.cells)
                before_values = {int(before_grid[cell]) for cell in support}
                after_values = {int(after_grid[cell]) for cell in support}
                if len(before_values) == len(after_values) == 1 and before_values != after_values:
                    before_value, after_value = next(iter(before_values)), next(iter(after_values))
                    self_observations[actor].append({
                        "left_node": press.left,
                        "right_node": press.right,
                        "action_id": press.action,
                        "target": semantic_of.get(actor, f"UNRESOLVED-W{actor:03d}"),
                        "changed_cells": len(support),
                        "integer_class_before": before_value,
                        "integer_class_after": after_value,
                        "cells_before": len(support),
                        "cells_after": len(support),
                        "cell_count_delta": 0,
                        "anchor_before": list(before_actor.anchor),
                        "anchor_after": list(before_actor.anchor),
                        "affected_bbox": _bbox(support),
                    })
            if actor not in read.levers.verdicts and actor not in self_observations:
                continue
            attributed_counts[actor] += 1
            partners = {
                wid: cells for wid, cells in press.partners.items()
                if wid != actor and wid not in action_independent
            }
            if not press.residue:
                null_counts[actor] += 1
            elif not partners:
                self_only_counts[actor] += 1
            for partner, changed_cells in sorted(partners.items()):
                before = region_at(by_id[partner], press.left) if partner in by_id else None
                after = region_at(by_id[partner], press.right) if partner in by_id else None
                support = set()
                if before is not None:
                    support.update(before.cells)
                if after is not None:
                    support.update(after.cells)
                observations[actor].append({
                    "left_node": press.left,
                    "right_node": press.right,
                    "action_id": press.action,
                    "target": semantic_of.get(partner, f"UNRESOLVED-W{partner:03d}"),
                    "changed_cells": changed_cells,
                    "integer_class_before": None if before is None else before.value,
                    "integer_class_after": None if after is None else after.value,
                    "cells_before": None if before is None else before.area,
                    "cells_after": None if after is None else after.area,
                    "cell_count_delta": None if before is None or after is None else after.area - before.area,
                    "anchor_before": None if before is None else list(before.anchor),
                    "anchor_after": None if after is None else list(after.anchor),
                    "affected_bbox": _bbox(support),
                })

    profiles = []
    signed: dict[tuple[int, str], list[tuple[int, int]]] = defaultdict(list)
    remote_actors = sorted(read.levers.verdicts)
    actor_groups = _co_attributed_actor_groups(read, remote_actors) if read.bodies else [
        (actor,) for actor in sorted(read.levers.verdicts)
    ]
    actor_groups = [group for group in actor_groups if observations.get(group[0])]
    display_of = dict(semantic_of)
    for ordinal, group in enumerate(actor_groups, start=1):
        if len(group) > 1:
            display_of[group[0]] = f"{segment}-CONTACT_SURFACE-{ordinal:02d}"
    for group in actor_groups:
        actor = group[0]
        rows = observations.get(actor, [])
        by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_target[row["target"]].append(row)
            delta = row["cell_count_delta"]
            if delta:
                signed[(actor, row["target"])].append((int(row["right_node"]), delta))
        targets = []
        for target, target_rows in sorted(by_target.items()):
            deltas = [row["cell_count_delta"] for row in target_rows if row["cell_count_delta"]]
            if deltas and all(delta > 0 for delta in deltas):
                direction = "INCREASES_CELL_COUNT"
            elif deltas and all(delta < 0 for delta in deltas):
                direction = "DECREASES_CELL_COUNT"
            elif deltas:
                direction = "MIXED_CELL_COUNT_DIRECTION"
            elif any(row["integer_class_before"] != row["integer_class_after"] for row in target_rows):
                direction = "CLASS_REWRITE_WITHOUT_SIZE_CHANGE"
            else:
                direction = "VISIBLE_CHANGE_WITHOUT_SIZE_DIRECTION"
            targets.append({
                "target": target,
                "visible": (
                    {
                        "integer_classes": list(entity_by_handle[target].current.integer_classes),
                        "cells": entity_by_handle[target].current.cells,
                        "bbox": entity_by_handle[target].current.bbox,
                    }
                    if target in entity_by_handle else None
                ),
                "observations": len(target_rows),
                "direction": direction,
                "cell_count_deltas": deltas,
                "affected_regions": sorted({tuple(row["affected_bbox"]) for row in target_rows if row["affected_bbox"]}),
            })
        component_boxes = [
            row["affected_bbox"] for row in rows if row.get("affected_bbox") is not None
        ]
        profiles.append({
            "lever": display_of.get(actor, f"UNRESOLVED-W{actor:03d}"),
            "kind": "CONTACT_SURFACE" if len(group) > 1 else "VISUAL_OBJECT",
            "member_levers": [semantic_of.get(member, f"UNRESOLVED-W{member:03d}") for member in group],
            "visible": _group_visible(group, semantic_of, entity_by_handle),
            "worldline_ids": list(group),
            "attributed_presses": attributed_counts[actor],
            "effect_observations": len(rows),
            "null_presses": null_counts[actor],
            "self_only_presses": self_only_counts[actor],
            "targets": targets,
            "effect_channels": _effect_channels(rows),
            "joint_transformation": compile_joint_transformation(
                record, read.levers.presses, actor, component_boxes=component_boxes
            ),
            "evidence": rows,
            "period": {"status": "UNMEASURED"},
            "endpoint": {"status": "UNMEASURED"},
        })

    actors = [group[0] for group in actor_groups]
    reactive_controls = []
    for actor in sorted(self_observations):
        rows = self_observations.get(actor, [])
        channels = _effect_channels(rows)
        if not channels:
            continue
        reactive_controls.append({
            "control": semantic_of.get(actor, f"UNRESOLVED-W{actor:03d}"),
            "kind": "SELF_REACTIVE_CONTROL",
            "visible": _group_visible((actor,), semantic_of, entity_by_handle),
            "worldline_id": actor,
            "attributed_presses": sum(actor in press.attributed for press in read.levers.presses),
            "self_reaction_observations": len(rows),
            "self_effect_channels": channels,
            "evidence": rows,
            "interpretation_limit": (
                "The targeted visual object changed on the same presses. This establishes "
                "self-reaction, not an effect on a separate object or a winning purpose."
            ),
        })
    return {
        "status": "OBSERVATIONAL_PROFILES_UNVALIDATED",
        "levers": profiles,
        "reactive_controls": reactive_controls,
        "shared_controls": _shared_control_bundles(actors, signed, display_of),
        "masked_action_independent_worldlines": sorted(action_independent),
        "mask_basis": (
            "Changed on every press in an eight-press consecutive suffix spanning at least two "
            "different targeted worldlines; excluded as an effect of any one target."
        ),
    }
