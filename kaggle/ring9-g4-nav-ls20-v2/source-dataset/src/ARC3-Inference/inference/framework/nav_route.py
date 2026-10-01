"""Deterministic embodied routing over demonstrated stands.

Routes use only anchors the ego has occupied.  One step beyond that graph is
an explicit probe.  Contact is the action whose predicted landing footprint
intersects the bound target; adjacency alone never counts.

Ported and adapted from virelai-golden/captain/nav_lattice.py.
Author: Sol (Alpha build seat), 2026-10-01.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Mapping

Cell = tuple[int, int]


@dataclass(frozen=True)
class NavLattice:
    anchor: Cell
    shape: frozenset[Cell]
    bearings: Mapping[str, Cell]
    stands: frozenset[Cell]
    refused: frozenset[tuple[Cell, str]]
    bounds: tuple[int, int]


@dataclass(frozen=True)
class NavStep:
    action: str
    intent: str
    stand: Cell
    landing: Cell
    target_entity_id: str
    reason: str


def footprint(lat: NavLattice, anchor: Cell) -> frozenset[Cell]:
    return frozenset((anchor[0]+r, anchor[1]+c) for r, c in lat.shape)


def routes(lat: NavLattice):
    dist = {lat.anchor: 0}
    parent: dict[Cell, tuple[Cell, str]] = {}
    queue = deque([lat.anchor])
    while queue:
        here = queue.popleft()
        for action, delta in sorted(lat.bearings.items()):
            if (here, action) in lat.refused:
                continue
            there = (here[0]+delta[0], here[1]+delta[1])
            if there in dist or there not in lat.stands:
                continue
            dist[there] = dist[here] + 1
            parent[there] = (here, action)
            queue.append(there)
    return dist, parent


def first_step(parent, start: Cell, goal: Cell):
    if start == goal:
        return None
    prior, action = parent[goal]
    while prior != start:
        prior, action = parent[prior]
    return action


def _in_bounds(lat: NavLattice, anchor: Cell) -> bool:
    rows, cols = lat.bounds
    return all(0 <= r < rows and 0 <= c < cols for r, c in footprint(lat, anchor))


def plan_contact(lat: NavLattice, target_entity_id: str, target_cells) -> NavStep | None:
    target = frozenset(tuple(map(int, cell)) for cell in target_cells)
    if not target or not lat.bearings:
        return None
    dist, parent = routes(lat)
    contacts = []
    for stand, distance in dist.items():
        for action, delta in sorted(lat.bearings.items()):
            if (stand, action) in lat.refused:
                continue
            landing = (stand[0]+delta[0], stand[1]+delta[1])
            if _in_bounds(lat, landing) and footprint(lat, landing) & target:
                contacts.append((distance, stand, action, landing))
    if contacts:
        _, stand, contact_action, landing = min(contacts)
        action = contact_action if stand == lat.anchor else first_step(parent, lat.anchor, stand)
        assert action is not None
        delta = lat.bearings[action]
        actual_landing = (lat.anchor[0]+delta[0], lat.anchor[1]+delta[1])
        intent = "CONTACT_ATTEMPT" if stand == lat.anchor else "APPROACH"
        return NavStep(action, intent, lat.anchor, actual_landing, target_entity_id,
                       "predicted footprint intersects target" if intent == "CONTACT_ATTEMPT"
                       else "shortest demonstrated route to a contact stand")
    # No contact surface is known. Move through the demonstrated graph to the
    # stand closest to the target, then make exactly one frontier experiment.
    def distance(anchor):
        return min(abs(r-tr)+abs(c-tc) for r, c in footprint(lat, anchor) for tr, tc in target)
    best = min(dist, key=lambda cell: (distance(cell), dist[cell], cell))
    if best != lat.anchor:
        action = first_step(parent, lat.anchor, best)
        delta = lat.bearings[action]
        return NavStep(action, "APPROACH", lat.anchor,
                       (lat.anchor[0]+delta[0], lat.anchor[1]+delta[1]), target_entity_id,
                       "shortest demonstrated route toward unresolved target")
    probes = []
    for action, delta in sorted(lat.bearings.items()):
        if (lat.anchor, action) in lat.refused:
            continue
        landing = (lat.anchor[0]+delta[0], lat.anchor[1]+delta[1])
        if _in_bounds(lat, landing):
            probes.append((distance(landing), action, landing))
    if not probes:
        return None
    _, action, landing = min(probes)
    return NavStep(action, "CONTACT_ATTEMPT" if footprint(lat, landing) & target else "APPROACH",
                   lat.anchor, landing, target_entity_id, "one-step frontier experiment")


def classify_contact(before_cells, after_cells, target_cells, board_changed: bool) -> str:
    before, after, target = map(frozenset, (before_cells, after_cells, target_cells))
    if after & target:
        return "ENTERED"
    if before != after:
        return "DISPLACED"
    return "TRANSFORMED" if board_changed else "REFUSED"


__all__ = ["NavLattice", "NavStep", "classify_contact", "first_step", "footprint", "plan_contact", "routes"]
