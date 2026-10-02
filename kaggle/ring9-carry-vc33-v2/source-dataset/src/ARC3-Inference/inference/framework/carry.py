"""G9-A: a finished level's levers, carried to the next level as predictions the new level grades.

Author: Claude (Alpha build seat), 2026-10-01. R9-R18 (MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4, L2
and L3). Director rulings 2026-10-01: carry hypotheses only; G0-G2 run again on each level.

Identity across levels is by TYPE, never by instance or position: a lever on level L and an object
on level L+1 match when their type signatures match: integer and scale-normalized shape. The shape
canonicalization is ported from virelai_v4 ``library/cross_level_identity.py`` (an exact k x k block
upscale is reduced, so a larger rendering of the same shape matches).

At level entry, every object on the new board whose type matches a carried lever becomes a carry
candidate with a prediction frozen before anything is clicked: clicking it changes the
counter-masked board, with the same locality (the object itself, elsewhere, or both) as the lever's
level-L reaction. The level's own probes grade it, at no extra action: the first click on the
candidate after G2 has certified this level's counter mask. A changed board with the carried
locality RECONFIRMS the carry; no change, or a different locality, FALSIFIES it. A click on a
transition that ends a life or a level is not evidence (R9-R16, D3). Nothing here certifies a lever:
G3 still witnesses every lever on its own evidence.
"""
from __future__ import annotations

from math import gcd
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.entity_observation import _components
from inference.framework.g4_guided import is_terminal

Cell = tuple[int, int]
UNCONFIRMED, RECONFIRMED, FALSIFIED = "UNCONFIRMED", "RECONFIRMED", "FALSIFIED"


def _block_uniform(mask: tuple[int, ...], h: int, w: int, k: int) -> bool:
    return all(
        mask[(br * k + dr) * w + (bc * k + dc)] == mask[(br * k) * w + (bc * k)]
        for br in range(h // k) for bc in range(w // k) for dr in range(k) for dc in range(k)
    )


def scale_normalized_shape(cells: Iterable[Cell]) -> tuple[int, int, tuple[int, ...]]:
    """Bounding-box mask, reduced by the largest exact k x k block upscale (ported, see module doc)."""
    points = {(int(r), int(c)) for r, c in cells}
    if not points:
        return (0, 0, ())
    r0, c0 = min(r for r, _ in points), min(c for _, c in points)
    h, w = max(r for r, _ in points) - r0 + 1, max(c for _, c in points) - c0 + 1
    mask = tuple(1 if (r0 + i // w, c0 + i % w) in points else 0 for i in range(h * w))
    k = gcd(h, w)
    while k > 1:
        if h % k == 0 and w % k == 0 and _block_uniform(mask, h, w, k):
            mask = tuple(mask[(br * k) * w + bc * k] for br in range(h // k) for bc in range(w // k))
            h, w = h // k, w // k
            k = gcd(h, w)
        else:
            k -= 1
    return (h, w, mask)


def type_signature(integer: int, cells: Iterable[Cell]) -> tuple[int, tuple[int, int, tuple[int, ...]]]:
    return (int(integer), scale_normalized_shape(cells))


def lever_signatures(machine: Any, entity_id: str) -> list[list[Any]]:
    """Every type signature a lever showed on its level (a lever that recolours shows several)."""
    ledger = getattr(machine._adapters.get("G3-LEVERS"), "entity_ledger", None)
    entity = None if ledger is None else ledger.entities.get(entity_id)
    found = {type_signature(s.integer, s.cells) for s in (entity.sightings if entity is not None else ())}
    return [[integer, list(shape[:2]), list(shape[2])] for integer, shape in sorted(found)]


def _key(signature: Sequence[Any]) -> tuple[Any, ...]:
    integer, size, mask = signature
    return (int(integer), (int(size[0]), int(size[1]), tuple(int(v) for v in mask)))


def _locality(changed: Iterable[Cell], cells: Sequence[Cell]) -> list[str]:
    rows, cols = [r for r, _ in cells], [c for _, c in cells]
    box = (min(rows), min(cols), max(rows), max(cols))
    inside = {box[0] <= r <= box[2] and box[1] <= c <= box[3] for r, c in changed}
    return sorted(({"LOCAL"} if True in inside else set()) | ({"REMOTE"} if False in inside else set()))


class CarryLedger:
    """The carried levers' predictions on this level, and their grades (LEVEL tier)."""

    def __init__(self, prior: Mapping[str, Any] | None, grid: Sequence[Sequence[int]], entry: int) -> None:
        self.prior_level = None if prior is None else prior.get("level")
        self.entry = int(entry)
        carried: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        self.not_carried: list[str] = []
        for lever in (prior or {}).get("levers") or ():
            if not lever.get("locality") or not lever.get("signatures"):
                self.not_carried.append(lever["entity_id"])  # no recorded reaction or shape to predict from
                continue
            for signature in lever["signatures"]:
                carried.setdefault(_key(signature), []).append(lever)
        self.candidates: list[dict[str, Any]] = []
        for component in _components(grid):
            levers = carried.get(type_signature(component["integer"], component["cells"]))
            if not levers:
                continue
            self.candidates.append({
                "candidate_id": f"C{len(self.candidates) + 1:02d}", "integer": component["integer"],
                "cells": [list(cell) for cell in component["cells"]], "anchor": list(component["anchor"]),
                "carried_from": sorted({item["entity_id"] for item in levers}),
                "predicted_locality": sorted({place for item in levers for place in item["locality"]}),
                "declared_at_transition": self.entry, "status": UNCONFIRMED, "evidence": None,
            })
        matched = {entity for item in self.candidates for entity in item["carried_from"]}
        self.not_found = sorted(
            item["entity_id"] for item in (prior or {}).get("levers") or ()
            if item["entity_id"] not in matched and item["entity_id"] not in self.not_carried
        )

    def observe(self, outcome: Mapping[str, Any], mask_cells: Iterable[Cell] | None) -> dict[str, Any] | None:
        """Grade the candidate a click lands on, once a counter mask exists on this level."""
        action = outcome.get("action") if isinstance(outcome.get("action"), Mapping) else {}
        if mask_cells is None or "row" not in action or is_terminal(outcome.get("boundary_event")):
            return None
        site = [int(action["row"]), int(action["col"])]
        candidate = next((item for item in self.candidates if site in item["cells"]), None)
        if candidate is None or candidate["status"] != UNCONFIRMED:
            return None
        masked = set(map(tuple, mask_cells))
        changed = [(int(c["row"]), int(c["col"])) for c in outcome.get("changed_cells") or () if (c["row"], c["col"]) not in masked]
        observed = _locality(changed, [tuple(cell) for cell in candidate["cells"]]) if changed else []
        candidate["status"] = RECONFIRMED if observed == candidate["predicted_locality"] else FALSIFIED
        candidate["evidence"] = {"transition_id": int(outcome.get("transition_id") or 0), "observed_locality": observed,
                                 "masked_changed_cells": len(changed)}
        return candidate

    def view(self) -> dict[str, Any]:
        counts = {status: sum(1 for item in self.candidates if item["status"] == status)
                  for status in (UNCONFIRMED, RECONFIRMED, FALSIFIED)}
        return {
            "schema": "virelai-carry-v1", "prior_level": self.prior_level, "declared_at_transition": self.entry,
            "counts": counts, "not_found": self.not_found, "not_carried": self.not_carried,
            "candidates": [{key: value for key, value in item.items() if key != "cells"} for item in self.candidates],
        }

    def line(self) -> str | None:
        if self.prior_level is None:
            return None
        view = self.view()
        counts = ", ".join(f"{n} {status}" for status, n in view["counts"].items() if n)
        sources = sorted({entity for item in self.candidates for entity in item["carried_from"]})
        return (f"level {self.prior_level} levers {', '.join(sources) or 'none'} -> {len(self.candidates)} "
                f"same-type objects here ({counts or 'none'}); not found: {', '.join(self.not_found) or 'none'}")


__all__ = ["FALSIFIED", "RECONFIRMED", "UNCONFIRMED", "CarryLedger", "lever_signatures", "scale_normalized_shape",
           "type_signature"]
