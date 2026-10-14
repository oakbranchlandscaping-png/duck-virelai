"""Pure, evidence-bounded typing of an observed effect channel: the neutral home of ``classify_effect_channel``.

Moved verbatim on 2026-10-13 (WO-DESC-B, interface v3 §10; Sol's ruling 5) from
``inference/framework/virelai_semantic/typing.py``, which now re-exports it. Importing it loads none of the legacy
semantic compiler. Port sources: V3.5 cycle_probe and V4 lever-subtree mechanism_classify. This version keeps
mechanism and condition separate and refuses recurrence claims across intervening actions. Duck's surface calls the
result an *observed effect type*; nothing here certifies a mechanic.
"""
from __future__ import annotations

from typing import Any, Sequence


def _state(row: dict[str, Any], side: str) -> tuple[Any, ...]:
    value, cells, anchor = row[side]
    return value, cells, None if anchor is None else tuple(anchor)


def _transform(row: dict[str, Any]) -> tuple[Any, ...]:
    before, after = _state(row, "before"), _state(row, "after")
    motion = None
    if before[2] is not None and after[2] is not None:
        motion = (after[2][0] - before[2][0], after[2][1] - before[2][1])
    count_delta = None if before[1] is None or after[1] is None else after[1] - before[1]
    return before[0], after[0], count_delta, motion


def classify_effect_channel(transitions: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Classify only what this ordered transition record logically establishes."""
    rows = sorted(transitions, key=lambda row: (row["left_node"], row["right_node"]))
    if len(rows) < 2:
        return {
            "mechanism": "UNKNOWN",
            "status": "INSUFFICIENT_OBSERVATIONS",
            "witness_count": len(rows),
            "condition": "UNMEASURED",
        }

    # Recurrence is licensed only inside uninterrupted activation runs. Separated discovery
    # observations remain evidence, but do not break a later controlled depth sequence.
    runs: list[list[dict[str, Any]]] = []
    for row in rows:
        if not runs or runs[-1][-1]["right_node"] != row["left_node"]:
            runs.append([row])
        else:
            runs[-1].append(row)
    for run in sorted(runs, key=len, reverse=True):
        states = [_state(run[0], "before")] + [_state(row, "after") for row in run]
        for period in range(2, len(states)):
            matches = all(states[index] == states[index - period] for index in range(period, len(states)))
            # Two complete periods are the confirmation floor; one return is only a candidate.
            if matches and len(states) >= 2 * period:
                return {
                    "mechanism": "TOGGLE" if period == 2 else "CYCLE",
                    "status": "EXACT_RECURRENCE_CONFIRMED",
                    "period": period,
                    "witness_count": len(run),
                    "total_observations": len(rows),
                    "condition": "OPEN_OR_UNMEASURED",
                }

    transforms = [_transform(row) for row in rows]
    if len(set(transforms)) == 1 and _state(rows[0], "before") != _state(rows[0], "after"):
        return {
            "mechanism": "UNIFORM_TRANSFORM",
            "status": "OBSERVED_REPEATEDLY",
            "transform": {
                "class_before": transforms[0][0],
                "class_after": transforms[0][1],
                "cell_count_delta": transforms[0][2],
                "anchor_delta": transforms[0][3],
            },
            "witness_count": len(rows),
            "condition": "UNMEASURED",
        }

    # A deterministic transition table is useful even when the observations were
    # separated by other actions and therefore cannot license a period claim.
    # Repeated inputs must agree exactly; this describes only the states seen.
    successors: dict[tuple[Any, ...], set[tuple[Any, ...]]] = {}
    for row in rows:
        successors.setdefault(_state(row, "before"), set()).add(_state(row, "after"))
    if successors and all(len(values) == 1 for values in successors.values()):
        observed_edges = sorted(
            ((before, next(iter(after))) for before, after in successors.items()),
            key=repr,
        )
        if any(before != after for before, after in observed_edges):
            return {
                "mechanism": "DETERMINISTIC_STATE_TRANSITION",
                "status": "OBSERVED_INPUTS_HAVE_UNIQUE_SUCCESSORS",
                "state_transitions": [
                    {
                        "before": list(before),
                        "after": list(after),
                    }
                    for before, after in observed_edges
                ],
                "witness_count": len(rows),
                "condition": "ONLY_FOR_OBSERVED_INPUT_STATES",
            }

    deltas = [item[2] for item in transforms if item[2] not in (None, 0)]
    if deltas and len(deltas) == len(transforms) and (
        all(value > 0 for value in deltas) or all(value < 0 for value in deltas)
    ):
        return {
            "mechanism": "DIRECTIONAL_CHANGE",
            "status": "CONSISTENT_SIGN_OBSERVED",
            "cell_count_direction": "INCREASE" if deltas[0] > 0 else "DECREASE",
            "witness_count": len(rows),
            "condition": "UNMEASURED",
        }
    return {
        "mechanism": "UNKNOWN",
        "status": "OBSERVATIONS_DO_NOT_SEAL_A_TYPE",
        "witness_count": len(rows),
        "condition": "UNMEASURED",
    }


__all__ = ["classify_effect_channel"]
