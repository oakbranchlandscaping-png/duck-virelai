"""Adaptive, observation-only coverage planning for the G1 ego gate.

The planner ports the Captain opening's consecutive simple-action pairs and
replaces exhaustive coordinate enumeration with deterministic target classes.
It schedules observations; it never assigns semantic roles to components or
action numbers.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import Any, Mapping, Sequence


Cell = tuple[int, int]


@dataclass(frozen=True)
class CoordinateCandidate:
    member_id: str
    class_id: str
    anchor: Cell
    integer: int
    cell_count: int
    bbox: tuple[int, int, int, int]
    shape_family: str
    size_band: str
    fingerprint_frequency: str
    position: str
    scale: str
    zone: str
    adjacent_component_count: int
    contained_by_count: int
    cells: tuple[Cell, ...]


@dataclass(frozen=True)
class CoordinateTargetClass:
    class_id: str
    descriptor: tuple[str, ...]
    member_ids: tuple[str, ...]
    representative_member_id: str


@dataclass(frozen=True)
class CoordinateObservation:
    member_id: str
    signature: str
    effect_observed: bool


def visual_object_rank(candidate: CoordinateCandidate) -> tuple[int, int, int, int, int, str]:
    """Return the Captain's deterministic visual-object experiment order.

    Ranking is scheduling, not semantic evidence: smallest footprint, lowest
    observed integer, nearest member anchor to (0, 0), then exact coordinate
    and stable-id tie-breaks.
    """
    row, col = candidate.anchor
    return (
        candidate.cell_count,
        candidate.integer,
        row + col,
        row,
        col,
        candidate.member_id,
    )


def _normal_shape(cells: Sequence[Cell]) -> tuple[Cell, ...]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_family(cells: Sequence[Cell], bbox: tuple[int, int, int, int]) -> str:
    if len(cells) == 1:
        return "POINT"
    min_row, min_col, max_row, max_col = bbox
    height, width = max_row - min_row + 1, max_col - min_col + 1
    if height == 1 or width == 1:
        return "LINE"
    if len(cells) == height * width:
        return "SOLID_RECTANGLE"
    return "OTHER"


def _size_band(size: int) -> str:
    if size == 1:
        return "1"
    if size <= 4:
        return "2_4"
    if size <= 16:
        return "5_16"
    if size <= 64:
        return "17_64"
    return "65_PLUS"


def _zone(anchor: Cell, height: int, width: int) -> str:
    row, col = anchor
    row_band = min(2, (3 * row) // max(1, height))
    col_band = min(2, (3 * col) // max(1, width))
    return ("N", "C", "S")[row_band] + ("W", "C", "E")[col_band]


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    owner: dict[Cell, int] = {}
    for start_row, row_values in enumerate(grid):
        for start_col, raw_value in enumerate(row_values):
            if (start_row, start_col) in seen:
                continue
            value = int(raw_value)
            cells: list[Cell] = []
            frontier = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while frontier:
                row, col = frontier.pop()
                cells.append((row, col))
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < len(grid[nr])
                        and neighbor not in seen
                        and int(grid[nr][nc]) == value
                    ):
                        seen.add(neighbor)
                        frontier.append(neighbor)
            ordered = tuple(sorted(cells))
            rows = [cell[0] for cell in ordered]
            cols = [cell[1] for cell in ordered]
            component_id = len(components)
            for cell in ordered:
                owner[cell] = component_id
            components.append({
                "component_id": component_id,
                "integer": value,
                "cells": ordered,
                "anchor": min(ordered),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    for component in components:
        adjacent: set[int] = set()
        for row, col in component["cells"]:
            for neighbor in (
                (row - 1, col - 1), (row - 1, col), (row - 1, col + 1),
                (row, col - 1), (row, col + 1),
                (row + 1, col - 1), (row + 1, col), (row + 1, col + 1),
            ):
                other = owner.get(neighbor)
                if other is not None and other != component["component_id"]:
                    adjacent.add(other)
        component["adjacent_component_count"] = len(adjacent)
    for component in components:
        r0, c0, r1, c1 = component["bbox"]
        component["contained_by_count"] = sum(
            1
            for other in components
            if other is not component
            and other["bbox"][0] < r0
            and other["bbox"][1] < c0
            and other["bbox"][2] > r1
            and other["bbox"][3] > c1
        )
    return components


def _signature(outcome: Mapping[str, Any]) -> tuple[str, bool]:
    boundary = outcome.get("boundary_event")
    boundary_flags = ()
    if isinstance(boundary, Mapping):
        boundary_flags = tuple(
            key
            for key in ("done", "level_completed", "game_over", "run_complete")
            if bool(boundary.get(key))
        )
    changed_count = outcome.get("changed_cell_count")
    effect = bool(outcome.get("board_changed")) or (
        isinstance(changed_count, int) and changed_count > 0
    )
    payload = {
        "effect": effect,
        "local": outcome.get("target_local_changed_cell_count"),
        "remote": outcome.get("remote_changed_cell_count"),
        "boundary": boundary_flags,
        "actions_after": sorted(str(item) for item in outcome.get("available_actions_after", ())),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")), effect


class AdaptiveCoordinateCoverage:
    """Representative-first coordinate coverage with evidence-driven expansion."""

    def __init__(self, grid: Sequence[Sequence[int]]) -> None:
        height = len(grid)
        width = max((len(row) for row in grid), default=0)
        raw = _components(grid)
        fingerprint_counts = Counter(
            (item["integer"], _normal_shape(item["cells"])) for item in raw
        )
        provisional: list[CoordinateCandidate] = []
        class_members: dict[tuple[str, ...], list[str]] = defaultdict(list)
        for index, item in enumerate(raw, start=1):
            bbox = item["bbox"]
            cells = item["cells"]
            border = (
                bbox[0] == 0 or bbox[1] == 0 or bbox[2] == height - 1 or bbox[3] == width - 1
            )
            fingerprint_frequency = (
                "REPEATED"
                if fingerprint_counts[(item["integer"], _normal_shape(cells))] > 1
                else "UNIQUE"
            )
            descriptor = (
                _shape_family(cells, bbox),
                _size_band(len(cells)),
                fingerprint_frequency,
                "BORDER" if border else "INTERIOR",
                "FIELD" if len(cells) >= max(1, height * width // 4) else "FEATURE",
            )
            member_id = f"M{index:04d}"
            candidate = CoordinateCandidate(
                member_id=member_id,
                class_id="",
                anchor=item["anchor"],
                integer=item["integer"],
                cell_count=len(cells),
                bbox=bbox,
                shape_family=descriptor[0],
                size_band=descriptor[1],
                fingerprint_frequency=descriptor[2],
                position=descriptor[3],
                scale=descriptor[4],
                zone=_zone(item["anchor"], height, width),
                adjacent_component_count=item["adjacent_component_count"],
                contained_by_count=item["contained_by_count"],
                cells=tuple(item["cells"]),
            )
            provisional.append(candidate)
            class_members[descriptor].append(member_id)

        by_id = {item.member_id: item for item in provisional}
        descriptors = sorted(
            class_members,
            key=lambda key: (
                key[4] == "FIELD",
                min(by_id[mid].cell_count for mid in class_members[key]),
                key,
            ),
        )
        classes: list[CoordinateTargetClass] = []
        candidates: dict[str, CoordinateCandidate] = {}
        for ordinal, descriptor in enumerate(descriptors, start=1):
            class_id = f"TC{ordinal:03d}"
            members = tuple(
                sorted(
                    class_members[descriptor],
                    key=lambda mid: (by_id[mid].cell_count, by_id[mid].anchor, mid),
                )
            )
            for member_id in members:
                candidates[member_id] = replace(by_id[member_id], class_id=class_id)
            classes.append(CoordinateTargetClass(class_id, descriptor, members, members[0]))
        self.candidates = candidates
        self.classes = tuple(classes)
        self._observations: dict[str, CoordinateObservation] = {}

    def initial_representatives(self) -> tuple[CoordinateCandidate, ...]:
        representatives = (
            self.candidates[item.representative_member_id] for item in self.classes
        )
        return tuple(sorted(representatives, key=visual_object_rank))

    def ranked_candidates(self) -> tuple[CoordinateCandidate, ...]:
        """Return every frame-zero component in strict sweep order."""
        return tuple(sorted(self.candidates.values(), key=visual_object_rank))

    def record(self, member_id: str, outcome: Mapping[str, Any]) -> None:
        if member_id not in self.candidates:
            raise ValueError(f"unknown coordinate coverage member: {member_id}")
        signature, effect = _signature(outcome)
        self._observations[member_id] = CoordinateObservation(member_id, signature, effect)

    def _observed(self, target_class: CoordinateTargetClass) -> list[CoordinateObservation]:
        return [
            self._observations[member_id]
            for member_id in target_class.member_ids
            if member_id in self._observations
        ]

    def next_adaptive(self) -> tuple[CoordinateCandidate, str] | None:
        if any(
            target_class.representative_member_id not in self._observations
            for target_class in self.classes
        ):
            return None
        # Once two members disagree, enumerate the remainder of that class.
        for target_class in self.classes:
            observed = self._observed(target_class)
            if len({item.signature for item in observed}) > 1:
                untested = [
                    member_id
                    for member_id in target_class.member_ids
                    if member_id not in self._observations
                ]
                if untested:
                    return self.candidates[untested[0]], "INCONSISTENT_CLASS_EXPANSION"
        # A positive representative receives one within-class contrast where possible.
        for target_class in self.classes:
            observed = self._observed(target_class)
            if (
                len(observed) == 1
                and observed[0].effect_observed
                and len(target_class.member_ids) > 1
            ):
                member_id = next(
                    item for item in target_class.member_ids if item not in self._observations
                )
                return self.candidates[member_id], "POSITIVE_CLASS_CONTRAST"
        return None

    @property
    def effect_observed(self) -> bool:
        return any(item.effect_observed for item in self._observations.values())

    @property
    def representatives_complete(self) -> bool:
        return all(
            item.representative_member_id in self._observations for item in self.classes
        )

    @property
    def state(self) -> str:
        if not self.representatives_complete or self.next_adaptive() is not None:
            return "ACTIVE"
        return "READY" if self.effect_observed else "REPRESENTATION_GAP"

    def certificate(self, *, include_unknown_members: bool) -> dict[str, Any]:
        rows = []
        for target_class in self.classes:
            observed = self._observed(target_class)
            unknown = [
                self.candidates[mid]
                for mid in target_class.member_ids
                if mid not in self._observations
            ]
            signatures = sorted({item.signature for item in observed})
            if len(signatures) > 1:
                status = "INCONSISTENT_EXPANDED" if not unknown else "INCONSISTENT_EXPANDING"
            elif observed and any(item.effect_observed for item in observed):
                status = "POSITIVE_CONTRASTED" if len(observed) > 1 or not unknown else "POSITIVE_REPRESENTATIVE"
            elif observed:
                status = "NEGATIVE_REPRESENTATIVE"
            else:
                status = "UNTESTED"
            row: dict[str, Any] = {
                "class_id": target_class.class_id,
                "descriptor": list(target_class.descriptor),
                "members_total": len(target_class.member_ids),
                "members_tested": len(observed),
                "members_unknown": len(unknown),
                "representative_member_id": target_class.representative_member_id,
                "status": status,
                "outcome_signatures": signatures,
            }
            if include_unknown_members:
                row["unknown_members"] = [asdict(item) for item in unknown]
            rows.append(row)
        result = {
            "schema": "virelai-g1-coordinate-coverage-v1",
            "state": self.state,
            "candidate_count": len(self.candidates),
            "class_count": len(self.classes),
            "tested_count": len(self._observations),
            "unknown_count": len(self.candidates) - len(self._observations),
            "effect_observed": self.effect_observed,
        }
        if include_unknown_members:
            result["classes"] = rows
        else:
            result["class_status_counts"] = dict(sorted(Counter(row["status"] for row in rows).items()))
        return result

    def unknown_candidates(self) -> tuple[CoordinateCandidate, ...]:
        return tuple(
            self.candidates[member_id]
            for target_class in self.classes
            for member_id in target_class.member_ids
            if member_id not in self._observations
        )


def candidate_digest(candidate: CoordinateCandidate) -> str:
    payload = json.dumps(asdict(candidate), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:10]


__all__ = [
    "AdaptiveCoordinateCoverage",
    "CoordinateCandidate",
    "CoordinateObservation",
    "CoordinateTargetClass",
    "candidate_digest",
    "visual_object_rank",
]
