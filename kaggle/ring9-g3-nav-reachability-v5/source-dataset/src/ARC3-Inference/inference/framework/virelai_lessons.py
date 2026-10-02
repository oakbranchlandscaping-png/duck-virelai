"""Deterministic, evidence-linked lessons compiled from observed level wins."""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass
from math import gcd
from typing import Any

LESSON_SCHEMA = "virelai-level-lesson-v1"


@dataclass(frozen=True)
class LevelLesson:
    schema: str
    completed_level: int
    compiled_at_transition: int
    actor: str
    boundary: dict[str, Any]
    established: tuple[dict[str, Any], ...]
    contrasts: tuple[dict[str, Any], ...]
    hypotheses: tuple[dict[str, Any], ...]
    transfer_clauses: tuple[dict[str, Any], ...]
    evidence_refs: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return asdict(self)

    def model_view(self, current_binding: dict[str, Any]) -> dict[str, Any]:
        """Compact player-facing view; full evidence remains available by reference."""
        standing = self.established[1]["changes"]
        trigger = self.established[2]["rewrites"]
        increases = [item for item in standing if item["delta"] > 0]
        decreases = [item for item in standing if item["delta"] < 0]
        exchanges = []
        for gain in increases:
            for loss in decreases:
                if gain["delta"] == -loss["delta"]:
                    exchanges.append({
                        "cells": gain["delta"],
                        "from_class": loss["class_id"],
                        "to_class": gain["class_id"],
                    })
        contrast = self.contrasts[0]
        return {
            "schema": "virelai-level-lesson-player-v1",
            "completed_level": self.completed_level,
            "observed_win": {
                "action_kind": str(self.boundary["winning_action"]).split("(", 1)[0],
                "same_exact_action_failed_earlier": contrast["attempts"],
                "same_action_visible_changes_without_win": contrast["attempts_with_visible_change"],
            },
            "what_accumulated_before_win": {
                "balanced_class_exchanges": exchanges[:6],
                "other_class_count_changes": standing[:12],
                "truncated": len(standing) > 12,
            },
            "what_final_action_changed": {
                "literal_rewrites": trigger[:12],
                "truncated": len(trigger) > 12,
            },
            "interpretation": [
                {"claim": item["claim"], "status": item["status"], "basis": item["basis"]}
                for item in self.hypotheses
            ],
            "new_level": current_binding,
            "how_to_use": (
                "Look for a new-level mechanism producing an analogous relationship. "
                "Do not repeat old coordinates or assume recurring colors have the same role."
            ),
            "evidence_transition_ids": [item["transition_id"] for item in self.evidence_refs],
        }


def _payload_for_ref(journal: Any, reference: Any) -> tuple[bytes, int, int] | None:
    if reference is None:
        return None
    record = journal.record_at(int(reference.node_index))
    descriptor = record.layers[int(reference.layer_index)]
    return record.layer_bytes(int(reference.layer_index)), descriptor.rows, descriptor.cols


def _class_counts(view: tuple[bytes, int, int] | None) -> dict[int, int]:
    return dict(sorted(Counter(view[0]).items())) if view is not None else {}


def _count_delta(left: dict[int, int], right: dict[int, int]) -> list[dict[str, int]]:
    return [
        {"class_id": key, "before": left.get(key, 0), "after": right.get(key, 0),
         "delta": right.get(key, 0) - left.get(key, 0)}
        for key in sorted(set(left) | set(right))
        if left.get(key, 0) != right.get(key, 0)
    ]


def _rewrite_counts(
    left: tuple[bytes, int, int] | None,
    right: tuple[bytes, int, int] | None,
) -> tuple[list[dict[str, int]], str | None]:
    if left is None or right is None:
        return [], "MISSING_RENDER"
    if left[1:] != right[1:]:
        return [], "GEOMETRY_CHANGED"
    counts = Counter(zip(left[0], right[0]))
    return ([
        {"before_class": before, "after_class": after, "cell_count": count}
        for (before, after), count in sorted(counts.items()) if before != after
    ], None)


def compile_level_lesson(
    *, capsule: Any, journal: Any, transitions: list[Any]
) -> LevelLesson:
    """Compile bounded observations and conservative transfer hypotheses."""
    level = int(capsule.completed_level)
    root = _payload_for_ref(journal, capsule.level_root_ref)
    pre_win = _payload_for_ref(journal, capsule.pre_win_ref)
    win = _payload_for_ref(journal, capsule.winning_render_ref)
    successor = _payload_for_ref(journal, capsule.successor_spawn_ref)
    standing = _count_delta(_class_counts(root), _class_counts(pre_win))
    trigger, trigger_friction = _rewrite_counts(pre_win, win)
    successor_overlap = sorted(set(_class_counts(pre_win)) & set(_class_counts(successor)))

    earlier_same_action = [
        item for item in transitions
        if item.level_before == level
        and item.transition_id < capsule.transition_id
        and item.action_name == capsule.action_name
        and not item.level_completed
        and not item.run_complete
    ]
    changed_earlier = sum(item.geometry_changed or item.cell_delta_count > 0
                          for item in earlier_same_action)
    established = (
        {
            "fact": "OBSERVED_WINNING_ACTION",
            "action": capsule.action_name,
            "acted_cell": capsule.acted_cell,
            "transition_id": capsule.transition_id,
        },
        {
            "fact": "ROOT_TO_PRE_WIN_CLASS_BALANCE",
            "changes": standing,
            "meaning": "integer-class counts that accumulated before the winning action",
        },
        {
            "fact": "WINNING_ACTION_LITERAL_REWRITES",
            "rewrites": trigger,
            "meaning": "exact cell-value rewrites between pre-win and outgoing winning render",
        },
    )
    contrasts = ({
        "comparison": "EARLIER_SAME_ACTION_WITHOUT_WIN",
        "attempts": len(earlier_same_action),
        "attempts_with_visible_change": changed_earlier,
        "transition_ids": [item.transition_id for item in earlier_same_action[-12:]],
        "truncated": len(earlier_same_action) > 12,
    },)
    hypotheses: list[dict[str, Any]] = []
    if earlier_same_action:
        hypotheses.append({
            "claim": "WIN_REQUIRED_CONTEXT_BEYOND_ACTION_NAME",
            "status": "SUPPORTED",
            "basis": f"The same action failed to win on {len(earlier_same_action)} earlier recorded uses.",
        })
    else:
        hypotheses.append({
            "claim": "ACTION_NAME_ALONE_CAUSED_WIN",
            "status": "UNKNOWN",
            "basis": "No earlier non-winning use of the same action was recorded.",
        })
    if trigger:
        hypotheses.append({
            "claim": "WIN_RELATED_TO_RECORDED_TRIGGER_REWRITES",
            "status": "UNTESTED",
            "basis": "These rewrites occurred on the observed win edge; causation is not established.",
        })
    transfer = (
        {
            "clause": "SEEK_ANALOGOUS_MECHANISM_NOT_OLD_COORDINATES",
            "status": "UNTESTED",
            "prior_action": capsule.action_name,
            "prior_trigger_rewrites": trigger,
            "classes_visible_in_both_PREWIN_and_NEW_LEVEL": successor_overlap,
            "warning": "Shared integer classes are supporting evidence only, not object identity.",
        },
    )
    limitations = list(capsule.evidence_friction)
    if trigger_friction:
        limitations.append(trigger_friction)
    limitations.extend((
        "A win edge proves that the level ended, not which observed condition caused it.",
        "Old coordinates and object instances do not transfer as facts to the new level.",
        "Worldline semantics may be enriched asynchronously; this immediate lesson uses exact boundary evidence.",
    ))
    return LevelLesson(
        schema=LESSON_SCHEMA,
        completed_level=level,
        compiled_at_transition=int(capsule.transition_id),
        actor=str(capsule.actor),
        boundary={
            "winning_action": capsule.action_name,
            "acted_cell": capsule.acted_cell,
            "pre_win_ref": asdict(capsule.pre_win_ref) if capsule.pre_win_ref else None,
            "winning_render_ref": asdict(capsule.winning_render_ref) if capsule.winning_render_ref else None,
            "successor_spawn_ref": asdict(capsule.successor_spawn_ref) if capsule.successor_spawn_ref else None,
        },
        established=established,
        contrasts=contrasts,
        hypotheses=tuple(hypotheses),
        transfer_clauses=transfer,
        evidence_refs=tuple({"transition_id": item.transition_id}
                            for item in earlier_same_action[-12:]) + ({"transition_id": capsule.transition_id},),
        limitations=tuple(limitations),
    )


def bind_lesson_to_current(lesson: LevelLesson, current_record: Any) -> dict[str, Any]:
    """Provide cautious fresh-level correspondence hints without copying identity."""
    if not current_record.layers:
        return {"status": "UNKNOWN", "candidates": [], "reason": "NO_VISIBLE_LAYER"}
    visible = Counter(current_record.layer_bytes(-1))
    prior_classes = set(
        lesson.transfer_clauses[0].get("classes_visible_in_both_PREWIN_and_NEW_LEVEL", [])
    )
    candidates = [
        {"class_id": value, "current_cell_count": visible[value], "status": "UNTESTED"}
        for value in sorted(prior_classes & set(visible))
    ]
    return {
        "status": "UNTESTED" if candidates else "UNKNOWN",
        "current_level": max(1, int(current_record.levels_completed) + 1),
        "candidates": candidates,
        "reason": (
            "Integer classes recur across levels; behavior must reconfirm function. "
            "No prior coordinates or instance identifiers were reused."
        ),
    }


def _shape(cells: list[tuple[int, int]]) -> tuple[int, int, tuple[int, ...]]:
    if not cells:
        return (0, 0, ())
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    present = set(cells)
    mask = tuple(int((r0 + r, c0 + c) in present)
                 for r in range(height) for c in range(width))
    scale = gcd(height, width)
    while scale > 1:
        if all(len({mask[(br * scale + dr) * width + bc * scale + dc]
                        for dr in range(scale) for dc in range(scale)}) == 1
               for br in range(height // scale) for bc in range(width // scale)):
            mask = tuple(mask[(br * scale) * width + bc * scale]
                         for br in range(height // scale) for bc in range(width // scale))
            height, width = height // scale, width // scale
            scale = gcd(height, width)
        else:
            scale -= 1
    return height, width, mask


def _grid(journal: Any, ref: dict[str, Any] | None) -> list[list[int]] | None:
    if not ref:
        return None
    record = journal.record_at(int(ref["node_index"]))
    index = int(ref.get("layer_index", 0))
    descriptor = record.layers[index]
    raw = record.layer_bytes(index)
    return [list(raw[row * descriptor.cols:(row + 1) * descriptor.cols])
            for row in range(descriptor.rows)]


def _components(grid: list[list[int]], allowed: set[int]) -> list[dict[str, Any]]:
    rows, cols, seen, output = len(grid), len(grid[0]), set(), []
    for row in range(rows):
        for col in range(cols):
            value = grid[row][col]
            if value not in allowed or (row, col) in seen:
                continue
            queue, cells = deque([(row, col)]), []
            seen.add((row, col))
            while queue:
                rr, cc = queue.popleft(); cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen and grid[nr][nc] == value:
                        seen.add((nr, nc)); queue.append((nr, nc))
            output.append({"integer_class": value, "cell_count": len(cells),
                           "bbox": [min(r for r, _ in cells), min(c for _, c in cells),
                                    max(r for r, _ in cells), max(c for _, c in cells)],
                           "shape": _shape(cells)})
    return output


def _region_state(grid: list[list[int]], bbox: list[int]) -> dict[str, int]:
    top, left, bottom, right = bbox
    counts = Counter(grid[row][col] for row in range(top, bottom + 1)
                     for col in range(left, right + 1))
    return {str(key): counts[key] for key in sorted(counts)}


def _object_win_explanation(
    lesson: LevelLesson, journal: Any, transitions: tuple[Any, ...], library: dict[str, Any]
) -> dict[str, Any]:
    from tools.compile_post_win_grammars import _known_regions, _minimal_separator

    regions = _known_regions(library, lesson.completed_level)
    pre = _grid(journal, lesson.boundary.get("pre_win_ref"))
    if pre is None or not regions:
        return {"status": "INSUFFICIENT_OBJECT_MODEL", "distinguishing_conditions": []}
    win = [_region_state(pre, region["bbox"]) for region in regions]
    earlier = [item for item in transitions
               if item.level_before == lesson.completed_level
               and item.transition_id < lesson.compiled_at_transition
               and item.action_name == lesson.boundary["winning_action"]
               and not item.level_completed and not item.run_complete]
    failed = []
    for transition in earlier:
        record = journal.record_at(transition.from_node)
        descriptor = record.layers[-1]; raw = record.layer_bytes(-1)
        grid = [list(raw[row * descriptor.cols:(row + 1) * descriptor.cols])
                for row in range(descriptor.rows)]
        failed.append([_region_state(grid, region["bbox"]) for region in regions])
    chosen = _minimal_separator(win, failed)
    conditions = [] if chosen is None else [
        {**regions[index], "winning_pre_state": win[index],
         "failed_pre_states": [dict(value) for value in sorted({
             tuple(sorted(row[index].items())) for row in failed})]}
        for index in chosen
    ]
    return {
        "status": ("MINIMAL_OBSERVED_SEPARATOR" if conditions else
                   "NO_EARLIER_EXACT_ACTION_CONTRAST" if not earlier else
                   "NO_SEPARATOR_WITHIN_THREE_REGION_BUDGET"),
        "earlier_same_action_failures": len(earlier),
        "distinguishing_conditions": conditions,
        "causal_limit": (
            "This separator distinguishes the recorded win from recorded exact-action "
            "failures. It is not yet a proven cause."
        ),
    }


def enrich_lesson(
    lesson: LevelLesson, journal: Any, transitions: tuple[Any, ...] = ()
) -> dict[str, Any]:
    """Compile the validated player grammar and conservative spawn matches on demand."""
    from inference.framework.virelai_semantic.compiler import compile_semantic_library
    from tools.render_physics_grammar import compile_grammar

    library = compile_semantic_library(journal)
    grammar = compile_grammar(library)
    level_row = next((row for row in grammar["levels"]
                      if int(row["level"]) == lesson.completed_level), None)
    pre = _grid(journal, lesson.boundary.get("pre_win_ref"))
    spawn = _grid(journal, lesson.boundary.get("successor_spawn_ref"))
    matches = []
    if level_row is not None and pre is not None and spawn is not None:
        priors = []
        controls = level_row.get("remote_levers", []) + level_row.get("self_reactive_controls", [])
        for control in controls:
            bbox = control.get("location")
            if bbox is None:
                continue
            top, left, bottom, right = bbox
            classes: dict[int, list[tuple[int, int]]] = {}
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    classes.setdefault(pre[row][col], []).append((row, col))
            choices = [(value, cells) for value, cells in classes.items() if value != 0] or list(classes.items())
            value, cells = max(choices, key=lambda item: (len(item[1]), -item[0]))
            priors.append((control["name"], bbox, value, _shape(cells)))
        candidates = _components(spawn, {item[2] for item in priors})
        for name, bbox, value, signature in priors:
            found = [item for item in candidates
                     if item["integer_class"] == value and item["shape"] == signature]
            if found:
                matches.append({"prior_control": name, "prior_location": bbox,
                                "candidate_count": len(found),
                                "candidate_locations": [item["bbox"] for item in found[:12]],
                                "truncated": len(found) > 12,
                                "status": ("UNTESTED_TYPE_CORRESPONDENCE" if len(found) == 1
                                           else "AMBIGUOUS_UNTESTED_TYPE_CORRESPONDENCE")})
    return {
        "physics_grammar": level_row,
        "observed_win_explanation": _object_win_explanation(
            lesson, journal, transitions, library),
        "new_level_type_correspondences": matches,
        "carry_rule": (
            "Prior-level mechanics and the observed win are evidence about the completed "
            "level and hypotheses for this level, not guarantees. Reconfirm behavior."
        ),
        "semantic_basis": "Observed action-indexed transitions through the winning edge.",
    }


__all__ = ["LESSON_SCHEMA", "LevelLesson", "bind_lesson_to_current", "compile_level_lesson",
           "enrich_lesson"]
