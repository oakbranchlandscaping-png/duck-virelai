"""Deterministic embodied routing over demonstrated stands.

Routes use only anchors the ego has occupied.  One step beyond that graph is
an explicit probe.  Contact is the action whose predicted landing footprint
intersects the bound target; adjacency alone never counts.

Ported and adapted from virelai-golden/captain/nav_lattice.py.
Author: Sol (Alpha build seat), 2026-10-01.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class ReachabilityCertificate:
    """Evidence shape emitted only after the reachable lattice is exhausted.

    Geometry proves a routing limit, never inertness.  The gate binds evidence
    references and asks Duck to explain the conclusion before releasing the
    target.
    """

    schema: str
    target_entity_id: str
    status: str
    target_cell_count: int
    reachable_stands: tuple[Cell, ...]
    refused_edges: tuple[tuple[Cell, str], ...]
    closest_stand: Cell
    remaining_gap: int
    contact_surface_count: int
    open_frontier_edge_count: int
    reason: str
    inertness_claim_permitted: bool
    reopen_conditions: tuple[str, ...]

    def snapshot(self) -> dict:
        return asdict(self)


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


def _distance(lat: NavLattice, anchor: Cell, target: frozenset[Cell]) -> int:
    return min(
        abs(r-tr) + abs(c-tc)
        for r, c in footprint(lat, anchor)
        for tr, tc in target
    )


def _contact_surfaces(lat: NavLattice, dist, target: frozenset[Cell]):
    contacts = []
    for stand, distance in dist.items():
        for action, delta in sorted(lat.bearings.items()):
            if (stand, action) in lat.refused:
                continue
            landing = (stand[0]+delta[0], stand[1]+delta[1])
            if _in_bounds(lat, landing) and footprint(lat, landing) & target:
                contacts.append((distance, stand, action, landing))
    return sorted(contacts)


def _frontier_edges(lat: NavLattice, dist, target: frozenset[Cell]):
    """All one-step experiments reachable through demonstrated stands."""
    edges = []
    for stand, route_distance in dist.items():
        for action, delta in sorted(lat.bearings.items()):
            if (stand, action) in lat.refused:
                continue
            landing = (stand[0]+delta[0], stand[1]+delta[1])
            if not _in_bounds(lat, landing) or landing in lat.stands:
                continue
            edges.append((
                _distance(lat, landing, target), route_distance, stand, action, landing,
            ))
    return sorted(edges)


def plan_contact(lat: NavLattice, target_entity_id: str, target_cells) -> NavStep | None:
    target = frozenset(tuple(map(int, cell)) for cell in target_cells)
    if not target or not lat.bearings:
        return None
    dist, parent = routes(lat)
    contacts = _contact_surfaces(lat, dist, target)
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
    # No contact surface is known. Consider one-step experiments from every
    # reachable stand, then route through demonstrated stands to the best one.
    # This is Golden's wall-crawl order: a whole route stays on known floor;
    # exactly one terminal step may cross the current frontier.
    frontier = _frontier_edges(lat, dist, target)
    if frontier:
        _, _, stand, frontier_action, landing = frontier[0]
        if stand != lat.anchor:
            action = first_step(parent, lat.anchor, stand)
            assert action is not None
            delta = lat.bearings[action]
            return NavStep(action, "APPROACH", lat.anchor,
                           (lat.anchor[0]+delta[0], lat.anchor[1]+delta[1]), target_entity_id,
                           "shortest demonstrated route to an untried frontier edge")
        action = frontier_action
        delta = lat.bearings[action]
        return NavStep(action, "APPROACH", lat.anchor,
                       landing, target_entity_id, "one-step frontier experiment")
    return None


def certify_unreachable(
    lat: NavLattice, target_entity_id: str, target_cells,
) -> ReachabilityCertificate | None:
    """Certify exhaustion only when no contact or frontier press remains.

    The certificate is recomputed from the current lattice.  A newly stood
    anchor, yielded refusal, changed target, control map, or world state makes
    it disappear without a permanent filter.
    """
    target = frozenset(tuple(map(int, cell)) for cell in target_cells)
    if not target or not lat.bearings:
        return None
    dist, _parent = routes(lat)
    contacts = _contact_surfaces(lat, dist, target)
    frontier = _frontier_edges(lat, dist, target)
    if contacts or frontier:
        return None
    closest = min(dist, key=lambda cell: (_distance(lat, cell, target), dist[cell], cell))
    refused = tuple(sorted(
        (stand, action)
        for stand in dist
        for action in lat.bearings
        if (stand, action) in lat.refused
    ))
    return ReachabilityCertificate(
        schema="virelai-nav-reachability-certificate-v1",
        target_entity_id=str(target_entity_id),
        status="PRESUMED_UNREACHABLE",
        target_cell_count=len(target),
        reachable_stands=tuple(sorted(dist)),
        refused_edges=refused,
        closest_stand=closest,
        remaining_gap=_distance(lat, closest, target),
        contact_surface_count=0,
        open_frontier_edge_count=0,
        reason=(
            "No demonstrated stand has a contact press and every in-bounds edge from the "
            "reachable component has either been stood or refused."
        ),
        inertness_claim_permitted=False,
        reopen_conditions=(
            "new stood anchor",
            "previously refused edge yields",
            "target geometry or identity changes",
            "ego footprint, bearing map, or action surface changes",
            "terrain or level state changes",
        ),
    )


def classify_contact(before_cells, after_cells, target_cells, board_changed: bool) -> str:
    before, after, target = map(frozenset, (before_cells, after_cells, target_cells))
    if after & target:
        return "ENTERED"
    if before != after:
        return "DISPLACED"
    return "TRANSFORMED" if board_changed else "REFUSED"


__all__ = [
    "NavLattice", "NavStep", "ReachabilityCertificate", "certify_unreachable",
    "classify_contact", "first_step", "footprint", "plan_contact", "routes",
]
