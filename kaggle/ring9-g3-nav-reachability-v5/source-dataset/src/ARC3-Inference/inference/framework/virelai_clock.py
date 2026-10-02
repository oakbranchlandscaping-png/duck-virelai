"""Strict observational clock-pattern compilation for Ring 8.

The compiler consumes canonical visible transitions.  It does not infer time,
purpose, causality, or hidden state.  A candidate is only a visible class count
that changes in one direction on every transition in a sufficiently long,
action-diverse suffix of the current level.
"""
from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Any, Iterable

MIN_WITNESS_TRANSITIONS = 8
MAX_SUPPORT_CELLS = 64
MAX_RECENT_RATES = 16


def _transition_delta_by_class(transition: Any) -> Counter[int]:
    delta: Counter[int] = Counter()
    for cell in transition.cell_deltas:
        delta[int(cell.before_class)] -= 1
        delta[int(cell.after_class)] += 1
    return delta


def _current_class_counts(record: Any) -> Counter[int]:
    if record is None or not record.layers:
        return Counter()
    return Counter(record.layer_bytes(-1))


def _suffix_for_class(transitions: list[Any], class_id: int) -> list[tuple[Any, int]]:
    suffix: list[tuple[Any, int]] = []
    sign = 0
    for transition in reversed(transitions):
        amount = _transition_delta_by_class(transition).get(class_id, 0)
        if amount == 0:
            break
        amount_sign = 1 if amount > 0 else -1
        if sign and amount_sign != sign:
            break
        sign = amount_sign
        suffix.append((transition, amount))
    suffix.reverse()
    return suffix


def compile_clock_patterns(
    transitions: Iterable[Any],
    current_record: Any,
    *,
    level: int,
) -> list[dict[str, Any]]:
    """Return strictly qualified repeated visible-process candidates.

    Boundary/geometry-changing transitions are excluded.  The witness is a
    consecutive suffix, so a flat, reversal, reset, or level boundary reopens
    the claim rather than being averaged away.
    """
    eligible = [
        transition
        for transition in transitions
        if transition.actor == "DUCK"
        and transition.level_before == level
        and transition.level_after == level
        and not transition.geometry_changed
        and not transition.level_completed
        and not transition.game_over
        and not transition.run_complete
    ]
    if len(eligible) < MIN_WITNESS_TRANSITIONS:
        return []

    classes: set[int] = set()
    for transition in eligible[-MIN_WITNESS_TRANSITIONS:]:
        classes.update(_transition_delta_by_class(transition))

    standing = _current_class_counts(current_record)
    patterns: list[dict[str, Any]] = []
    for class_id in sorted(classes):
        suffix = _suffix_for_class(eligible, class_id)
        if len(suffix) < MIN_WITNESS_TRANSITIONS:
            continue
        # Track the consumed side of a rewrite. Every loss necessarily creates
        # a corresponding gain somewhere; compiling both duplicates one
        # process and lets unrelated gains inflate the apparent support.
        if suffix[-1][1] > 0:
            continue
        action_keys = sorted({transition.action_name for transition, _ in suffix})
        if len(action_keys) < 2:
            continue

        support: set[tuple[int, int]] = set()
        rewrites: Counter[tuple[int, int]] = Counter()
        targeted = False
        for transition, _ in suffix:
            for cell in transition.cell_deltas:
                if cell.before_class == class_id or cell.after_class == class_id:
                    coordinate = (int(cell.row), int(cell.col))
                    support.add(coordinate)
                    rewrites[(int(cell.before_class), int(cell.after_class))] += 1
                    if transition.acted_cell == coordinate:
                        targeted = True
        if targeted or not support:
            continue

        rates = [amount for _, amount in suffix]
        rows = [cell[0] for cell in support]
        cols = [cell[1] for cell in support]
        support_view: dict[str, Any]
        if len(support) <= MAX_SUPPORT_CELLS:
            support_view = {"cells": [list(cell) for cell in sorted(support)]}
        else:
            support_view = {
                "bounding_box": [min(rows), min(cols), max(rows), max(cols)],
                "cell_count": len(support),
            }
        patterns.append(
            {
                "kind": "pattern",
                "level": level,
                "class_id": class_id,
                "support": support_view,
                "rewrites": [
                    {"before_class": before, "after_class": after, "observations": count}
                    for (before, after), count in sorted(
                        rewrites.items(), key=lambda item: (-item[1], item[0])
                    )[:8]
                ],
                "witness_count": len(suffix),
                "witness_steps": [transition.transition_id for transition, _ in suffix],
                "distinct_action_keys": len(action_keys),
                "action_keys": action_keys[:8],
                "rate": {
                    "min": min(rates),
                    "median": median(rates),
                    "max": max(rates),
                    "recent": rates[-MAX_RECENT_RATES:],
                    "unit": "visible cells per Duck action",
                },
                "current_standing": int(standing.get(class_id, 0)),
                "direction": "increasing" if rates[-1] > 0 else "decreasing",
                "remaining_presses": None,
                "terminal_extent_observed": False,
                "caveat": (
                    "Repeated action-independent visual process; not a proven timer, "
                    "objective, cause, or hidden-state measurement."
                ),
            }
        )

    for pattern in patterns:
        pattern["tracked_classes"] = [
            {
                "class_id": pattern.pop("class_id"),
                "current_standing": pattern.pop("current_standing"),
                "direction": pattern.pop("direction"),
            }
        ]
        pattern["process_kind"] = "monotone_visible_consumption"
    return patterns
