"""Integer-seeded, footprint-aware NAV terrain and reachability hypotheses.

The palette is learned from observed ego/ground exchange and refused landings.
It seeds a configuration-space map; it never turns a visual integer into an
unconditional world law.  Reachability analysis proposes a hypothesis and a
shortest falsifying action.  Only the gate owns promotion to a provisional
verdict after that action is observed.

Ported from Universal Solver v3.5's integer bridge and Golden's action-space
navigation corrections.  Author: Sol (Alpha build seat), 2026-10-03.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.masked_world_state import grids_from_probe_outcome

Cell = tuple[int, int]
Edge = tuple[Cell, str]
Grid = tuple[tuple[int, ...], ...]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class TerrainPalette:
    schema: str
    palette_id: str
    floor_integers: tuple[int, ...]
    wall_integers: tuple[int, ...]
    floor_cells: tuple[Cell, ...]
    wall_cells: tuple[Cell, ...]
    floor_evidence: tuple[tuple[int, tuple[str, ...]], ...]
    wall_evidence: tuple[tuple[int, tuple[str, ...]], ...]
    action_coverage: tuple[str, ...]
    limitations: tuple[str, ...]

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)

    def floor_refs(self, integer: int | None = None) -> tuple[str, ...]:
        rows = dict(self.floor_evidence)
        if integer is not None:
            return rows.get(int(integer), ())
        return tuple(dict.fromkeys(ref for refs in rows.values() for ref in refs))

    def wall_refs(self, integer: int | None = None) -> tuple[str, ...]:
        rows = dict(self.wall_evidence)
        if integer is not None:
            return rows.get(int(integer), ())
        return tuple(dict.fromkeys(ref for refs in rows.values() for ref in refs))


@dataclass(frozen=True)
class TerrainHypothesis:
    schema: str
    hypothesis_id: str
    target_entity_id: str
    status: str
    current_anchor: Cell
    valid_stands: tuple[Cell, ...]
    reachable_stands: tuple[Cell, ...]
    contact_edges: tuple[tuple[Cell, str, Cell], ...]
    bridge_edges: tuple[tuple[Cell, str, Cell], ...]
    closest_stand: Cell
    remaining_gap: int
    palette_id: str
    reason: str

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TerrainPlan:
    action: str
    intent: str
    stand: Cell
    landing: Cell
    target_entity_id: str
    reason: str
    hypothesis_id: str
    hypothesis_status: str
    experiment_kind: str


@dataclass(frozen=True)
class ReachabilitySignature:
    """Target-specific inputs and experiments behind a provisional route limit.

    ``reachable_stands`` and ``world_state_address`` are retained for audit.
    Reopening is controlled by the target geometry, ego law, topology epoch,
    contact edges and nearest unspent target-directed bridge edges.

    Author: Sol (Alpha build seat), 2026-10-03.
    """

    schema: str
    signature_id: str
    target_entity_id: str
    target_geometry_id: str
    target_cells: tuple[Cell, ...]
    ego_law_id: str
    ego_shape: tuple[Cell, ...]
    bearings: tuple[tuple[str, Cell], ...]
    action_surface: tuple[str, ...]
    topology_epoch: int
    world_state_address: str | None
    reachable_stands: tuple[Cell, ...]
    contact_edges: tuple[tuple[Cell, str, Cell], ...]
    bridge_edges: tuple[tuple[Cell, str, Cell], ...]

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBridgeSupport:
    """A previously refused boundary press that dominates open target bridges.

    The refusal may support several targets, but this result is recomputed for
    each target and retains that target's own gap and edge set.

    Author: Sol (Alpha build seat), 2026-10-03.
    """

    schema: str
    target_entity_id: str
    status: str
    refused_edges: tuple[tuple[Cell, str, Cell], ...]
    closest_refused_gap: int | None
    closest_open_gap: int | None
    reason: str

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


REACHABILITY_REOPEN_FIELDS = (
    "target_geometry_id",
    "ego_law_id",
    "topology_epoch",
    "contact_edges",
    "bridge_edges",
)


def reachability_signature(
    hypothesis: TerrainHypothesis,
    *,
    target_cells: Iterable[Cell],
    shape: Iterable[Cell],
    bearings: Mapping[str, Cell],
    action_surface: Iterable[str],
    topology_epoch: int,
    world_state_address: str | None,
) -> ReachabilitySignature:
    """Freeze the target-specific route question represented by a hypothesis."""
    target = tuple(sorted((int(r), int(c)) for r, c in target_cells))
    ego_shape = tuple(sorted((int(r), int(c)) for r, c in shape))
    bearing_rows = tuple(sorted(
        (str(action), (int(delta[0]), int(delta[1])))
        for action, delta in bearings.items()
    ))
    actions = tuple(sorted(str(action) for action in action_surface))
    target_geometry_id = "TG-" + hashlib.sha256(
        _canonical(target).encode()
    ).hexdigest()[:16]
    ego_law_id = "EL-" + hashlib.sha256(_canonical({
        "shape": ego_shape,
        "bearings": bearing_rows,
        "actions": actions,
    }).encode()).hexdigest()[:16]

    # The controller will execute only the nearest target-directed bridge.
    # Keeping every equally nearest bridge preserves real alternatives while
    # excluding unrelated frontier growth elsewhere in the room.
    bridge_edges: tuple[tuple[Cell, str, Cell], ...] = ()
    if hypothesis.bridge_edges:
        first = hypothesis.bridge_edges[0]
        nearest_gap = _distance(frozenset(ego_shape), first[2], frozenset(target))
        bridge_edges = tuple(
            edge for edge in hypothesis.bridge_edges
            if _distance(frozenset(ego_shape), edge[2], frozenset(target)) == nearest_gap
        )
    reopen_payload = {
        "target_geometry_id": target_geometry_id,
        "ego_law_id": ego_law_id,
        "topology_epoch": int(topology_epoch),
        "contact_edges": hypothesis.contact_edges,
        "bridge_edges": bridge_edges,
    }
    signature_id = "RS-" + hashlib.sha256(
        _canonical(reopen_payload).encode()
    ).hexdigest()[:16]
    return ReachabilitySignature(
        schema="virelai-nav-reachability-signature-v1",
        signature_id=signature_id,
        target_entity_id=str(hypothesis.target_entity_id),
        target_geometry_id=target_geometry_id,
        target_cells=target,
        ego_law_id=ego_law_id,
        ego_shape=ego_shape,
        bearings=bearing_rows,
        action_surface=actions,
        topology_epoch=int(topology_epoch),
        world_state_address=(
            None if world_state_address is None else str(world_state_address)
        ),
        reachable_stands=tuple(hypothesis.reachable_stands),
        contact_edges=tuple(hypothesis.contact_edges),
        bridge_edges=bridge_edges,
    )


def reachability_signature_changes(
    before: Mapping[str, Any], after: Mapping[str, Any],
) -> tuple[str, ...]:
    """Return only changes that create a different reachability question."""
    return tuple(
        field for field in REACHABILITY_REOPEN_FIELDS
        if _canonical(before.get(field)) != _canonical(after.get(field))
    )


def shared_bridge_support(
    hypothesis: TerrainHypothesis,
    *,
    shape: Iterable[Cell],
    bearings: Mapping[str, Cell],
    refused: Iterable[Edge],
    target_cells: Iterable[Cell],
    bounds: tuple[int, int],
) -> SharedBridgeSupport:
    """Find already-spent boundary presses that settle this target's next probe.

    A shared refusal is sufficient only when it is strictly closer to the
    target than every still-open bridge. Equal-distance open alternatives must
    be tried rather than hidden by reuse.
    """
    body = frozenset((int(r), int(c)) for r, c in shape)
    target = frozenset((int(r), int(c)) for r, c in target_cells)
    reachable = frozenset(hypothesis.reachable_stands)
    valid = frozenset(hypothesis.valid_stands)
    refused_candidates: list[tuple[int, Cell, str, Cell]] = []
    for stand, action in sorted(set(refused)):
        if stand not in reachable or action not in bearings:
            continue
        dr, dc = bearings[action]
        landing = (stand[0] + dr, stand[1] + dc)
        if not _in_bounds(body, landing, bounds):
            continue
        if footprint(body, landing) & target or landing in valid:
            continue
        refused_candidates.append((
            _distance(body, landing, target), stand, action, landing,
        ))
    closest_refused = (
        min((row[0] for row in refused_candidates), default=None)
    )
    closest_open = (
        _distance(body, hypothesis.bridge_edges[0][2], target)
        if hypothesis.bridge_edges else None
    )
    supported = bool(
        closest_refused is not None
        and (closest_open is None or closest_refused < closest_open)
    )
    edges = tuple(
        (stand, action, landing)
        for gap, stand, action, landing in refused_candidates
        if supported and gap == closest_refused
    )
    return SharedBridgeSupport(
        schema="virelai-nav-shared-bridge-support-v1",
        target_entity_id=hypothesis.target_entity_id,
        status="SUPPORTED" if supported else "UNSUPPORTED",
        refused_edges=edges,
        closest_refused_gap=closest_refused,
        closest_open_gap=closest_open,
        reason=(
            "The closest target-directed boundary experiment was already refused in this "
            "topology and every open bridge is farther away."
            if supported else
            "No prior refusal strictly dominates the target's remaining open bridge experiments."
        ),
    )


def footprint(shape: Iterable[Cell], anchor: Cell) -> frozenset[Cell]:
    return frozenset((anchor[0] + r, anchor[1] + c) for r, c in shape)


def _in_bounds(shape: Iterable[Cell], anchor: Cell, bounds: tuple[int, int]) -> bool:
    rows, cols = bounds
    return all(0 <= r < rows and 0 <= c < cols for r, c in footprint(shape, anchor))


def _pattern(grid: Grid, cells: Iterable[Cell]) -> tuple[tuple[int, int, int], ...]:
    cells = tuple(sorted(cells))
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r-r0, c-c0, int(grid[r][c])) for r, c in cells))


def _occurrences(grid: Grid, pattern: Sequence[tuple[int, int, int]]) -> tuple[Cell, ...]:
    if not grid or not pattern:
        return ()
    max_r = max(r for r, _, _ in pattern)
    max_c = max(c for _, c, _ in pattern)
    found = []
    for ar in range(len(grid) - max_r):
        for ac in range(len(grid[0]) - max_c):
            if all(int(grid[ar+r][ac+c]) == value for r, c, value in pattern):
                found.append((ar, ac))
    return tuple(found)


def _evidence_ref(ego: Any, outcome: Mapping[str, Any], index: int) -> str:
    probe_id = str(outcome.get("probe_id") or "")
    row = next(
        (item for item in getattr(ego, "evidence", ()) if item.get("probe_id") == probe_id),
        None,
    )
    return str((row or {}).get("evidence_id") or outcome.get("evidence_id") or f"G1-OUTCOME-{index+1}")


def infer_terrain_palette(
    ego: Any,
    *,
    current_grid: Sequence[Sequence[int]],
    current_ego_cells: Iterable[Cell],
    bearings: Mapping[str, Cell],
    refused: Iterable[Edge] = (),
    refused_evidence: Mapping[Edge, str] | None = None,
) -> TerrainPalette:
    """Infer current-state integer hypotheses from direct movement evidence.

    Floor values come only from cells the demonstrated body entered or left on
    an observed translation.  Wall values come only from uniform destination
    footprints of refused edges and never override a directly observed floor.
    """
    grid: Grid = tuple(tuple(int(value) for value in row) for row in current_grid)
    ego_cells = tuple(sorted((int(r), int(c)) for r, c in current_ego_cells))
    shape = ()
    if ego_cells:
        anchor = min(ego_cells)
        shape = tuple((r-anchor[0], c-anchor[1]) for r, c in ego_cells)
    pattern = _pattern(grid, ego_cells)
    floor_refs: dict[int, list[str]] = defaultdict(list)
    floor_cells: set[Cell] = set()
    action_coverage: set[str] = set()
    limitations: list[str] = []
    for index, outcome in enumerate(getattr(ego, "_lossless_outcomes", ())):
        grids = grids_from_probe_outcome(outcome)
        if grids is None or not pattern or not shape:
            continue
        before, after = grids
        raw_action = outcome.get("action") or {}
        action = str(
            raw_action.get("action") if isinstance(raw_action, Mapping) else raw_action
        ).upper()
        delta = bearings.get(action)
        if delta is None:
            continue
        left = _occurrences(before, pattern)
        right = _occurrences(after, pattern)
        pairs = [
            (p, q) for p in left for q in right
            if (q[0]-p[0], q[1]-p[1]) == tuple(delta)
        ]
        if len(pairs) != 1:
            continue
        p, q = pairs[0]
        before_body = footprint(shape, p)
        after_body = footprint(shape, q)
        exchanged: list[tuple[Cell, int]] = []
        exchanged.extend((cell, int(before[cell[0]][cell[1]])) for cell in after_body-before_body)
        exchanged.extend((cell, int(after[cell[0]][cell[1]])) for cell in before_body-after_body)
        if not exchanged:
            continue
        ref = _evidence_ref(ego, outcome, index)
        action_coverage.add(action)
        for cell, integer in exchanged:
            floor_cells.add(cell)
            if ref not in floor_refs[integer]:
                floor_refs[integer].append(ref)
    if not floor_refs:
        limitations.append("no ego/ground exchange could be uniquely reconstructed")

    refused_evidence = refused_evidence or {}
    wall_refs: dict[int, list[str]] = defaultdict(list)
    wall_cells: set[Cell] = set()
    floor_values = set(floor_refs)
    for stand, action in sorted(set(refused)):
        delta = bearings.get(action)
        if delta is None or not shape:
            continue
        landing = (stand[0]+delta[0], stand[1]+delta[1])
        if not _in_bounds(shape, landing, (len(grid), len(grid[0]))):
            continue
        cells = footprint(shape, landing)
        values = {int(grid[r][c]) for r, c in cells}
        if len(values) != 1:
            continue
        integer = next(iter(values))
        if integer in floor_values:
            # The exact edge refusal remains authoritative, but it does not
            # turn a directly traversed terrain integer into a global wall.
            continue
        ref = str(refused_evidence.get((stand, action)) or "")
        wall_cells.update(cells)
        if ref and ref not in wall_refs[integer]:
            wall_refs[integer].append(ref)
    if refused and not wall_refs:
        limitations.append("refused edges did not support a uniform non-floor wall integer")

    payload = {
        "floor": sorted(floor_refs), "wall": sorted(wall_refs),
        "floor_cells": sorted(floor_cells), "wall_cells": sorted(wall_cells),
        "floor_refs": {str(k): v for k, v in sorted(floor_refs.items())},
        "wall_refs": {str(k): v for k, v in sorted(wall_refs.items())},
        "actions": sorted(action_coverage),
    }
    palette_id = "TP-" + hashlib.sha256(_canonical(payload).encode()).hexdigest()[:16]
    return TerrainPalette(
        schema="virelai-nav-terrain-palette-v1",
        palette_id=palette_id,
        floor_integers=tuple(sorted(floor_refs)),
        wall_integers=tuple(sorted(wall_refs)),
        floor_cells=tuple(sorted(floor_cells)),
        wall_cells=tuple(sorted(wall_cells)),
        floor_evidence=tuple((k, tuple(v)) for k, v in sorted(floor_refs.items())),
        wall_evidence=tuple((k, tuple(v)) for k, v in sorted(wall_refs.items())),
        action_coverage=tuple(sorted(action_coverage)),
        limitations=tuple(limitations),
    )


def _valid_stands(
    grid: Grid,
    shape: frozenset[Cell],
    floor_integers: frozenset[int],
    current_anchor: Cell,
    demonstrated_stands: Iterable[Cell],
) -> frozenset[Cell]:
    if not shape or not floor_integers:
        return frozenset({current_anchor, *demonstrated_stands})
    rows, cols = len(grid), len(grid[0])
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    stands = {
        (r, c)
        for r in range(rows-max_r)
        for c in range(cols-max_c)
        if all(int(grid[r+dr][c+dc]) in floor_integers for dr, dc in shape)
    }
    stands.add(current_anchor)
    stands.update(
        stand for stand in demonstrated_stands
        if _in_bounds(shape, stand, (rows, cols))
    )
    return frozenset(stands)


def _routes(
    start: Cell,
    stands: frozenset[Cell],
    bearings: Mapping[str, Cell],
    refused: frozenset[Edge],
) -> tuple[dict[Cell, int], dict[Cell, tuple[Cell, str]]]:
    dist = {start: 0}
    parent: dict[Cell, tuple[Cell, str]] = {}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        for action, (dr, dc) in sorted(bearings.items()):
            there = (here[0]+dr, here[1]+dc)
            if (here, action) in refused or there in dist or there not in stands:
                continue
            dist[there] = dist[here] + 1
            parent[there] = (here, action)
            queue.append(there)
    return dist, parent


def _first_step(parent: Mapping[Cell, tuple[Cell, str]], start: Cell, goal: Cell) -> str | None:
    if start == goal:
        return None
    prior, action = parent[goal]
    while prior != start:
        prior, action = parent[prior]
    return action


def _distance(shape: frozenset[Cell], anchor: Cell, target: frozenset[Cell]) -> int:
    return min(
        abs(r-tr) + abs(c-tc)
        for r, c in footprint(shape, anchor)
        for tr, tc in target
    )


def analyze_terrain_reachability(
    *,
    grid: Sequence[Sequence[int]],
    anchor: Cell,
    shape: frozenset[Cell],
    bearings: Mapping[str, Cell],
    palette: TerrainPalette,
    demonstrated_stands: Iterable[Cell],
    refused: Iterable[Edge],
    target_entity_id: str,
    target_cells: Iterable[Cell],
) -> TerrainHypothesis:
    current: Grid = tuple(tuple(int(value) for value in row) for row in grid)
    bounds = (len(current), len(current[0]))
    target = frozenset((int(r), int(c)) for r, c in target_cells)
    stands = _valid_stands(
        current, shape, frozenset(palette.floor_integers), anchor, demonstrated_stands,
    )
    refused_set = frozenset(refused)
    dist, _parent = _routes(anchor, stands, bearings, refused_set)
    contacts: list[tuple[Cell, str, Cell]] = []
    bridges: list[tuple[int, int, Cell, str, Cell]] = []
    for stand, route_distance in dist.items():
        for action, (dr, dc) in sorted(bearings.items()):
            if (stand, action) in refused_set:
                continue
            landing = (stand[0]+dr, stand[1]+dc)
            if not _in_bounds(shape, landing, bounds):
                continue
            if footprint(shape, landing) & target:
                contacts.append((stand, action, landing))
            elif landing not in stands:
                bridges.append((
                    _distance(shape, landing, target), route_distance,
                    stand, action, landing,
                ))
    ordered_contacts = tuple(sorted(
        contacts, key=lambda row: (dist[row[0]], row[0], row[1], row[2])
    ))
    ordered_bridges = tuple(
        (stand, action, landing)
        for _gap, _route, stand, action, landing in sorted(bridges)
    )
    closest = min(dist, key=lambda stand: (_distance(shape, stand, target), dist[stand], stand))
    gap = _distance(shape, closest, target)
    status = "PREDICTED_REACHABLE" if ordered_contacts else "PREDICTED_UNREACHABLE"
    reason = (
        "the integer-seeded ego-pose component contains a terminal contact action"
        if ordered_contacts else
        "the integer-seeded ego-pose component contains no terminal contact action"
    )
    payload = {
        "target": target_entity_id, "status": status, "palette": palette.palette_id,
        "anchor": anchor, "reachable": sorted(dist), "contacts": ordered_contacts,
        "bridges": ordered_bridges, "target_cells": sorted(target),
    }
    hypothesis_id = "RH-" + hashlib.sha256(_canonical(payload).encode()).hexdigest()[:16]
    return TerrainHypothesis(
        schema="virelai-nav-terrain-reachability-hypothesis-v1",
        hypothesis_id=hypothesis_id,
        target_entity_id=str(target_entity_id),
        status=status,
        current_anchor=anchor,
        valid_stands=tuple(sorted(stands)),
        reachable_stands=tuple(sorted(dist)),
        contact_edges=ordered_contacts,
        bridge_edges=ordered_bridges,
        closest_stand=closest,
        remaining_gap=gap,
        palette_id=palette.palette_id,
        reason=reason,
    )


def plan_hypothesis_test(
    hypothesis: TerrainHypothesis,
    *,
    bearings: Mapping[str, Cell],
    refused: Iterable[Edge],
) -> TerrainPlan | None:
    """Route to contact or make the closest target-conditioned bridge attempt."""
    stands = frozenset(hypothesis.reachable_stands)
    dist, parent = _routes(
        hypothesis.current_anchor, stands, bearings, frozenset(refused),
    )
    candidates = (
        hypothesis.contact_edges
        if hypothesis.status == "PREDICTED_REACHABLE"
        else hypothesis.bridge_edges[:1]
    )
    if not candidates:
        return None
    stand, terminal_action, terminal_landing = candidates[0]
    if stand != hypothesis.current_anchor:
        action = _first_step(parent, hypothesis.current_anchor, stand)
        if action is None:
            return None
        dr, dc = bearings[action]
        return TerrainPlan(
            action=action,
            intent="APPROACH",
            stand=hypothesis.current_anchor,
            landing=(hypothesis.current_anchor[0]+dr, hypothesis.current_anchor[1]+dc),
            target_entity_id=hypothesis.target_entity_id,
            reason=(
                "shortest integer-seeded floor route to contact"
                if hypothesis.status == "PREDICTED_REACHABLE" else
                "shortest integer-seeded floor route to the target's falsifying bridge"
            ),
            hypothesis_id=hypothesis.hypothesis_id,
            hypothesis_status=hypothesis.status,
            experiment_kind="ROUTE",
        )
    return TerrainPlan(
        action=terminal_action,
        intent=(
            "CONTACT_ATTEMPT"
            if hypothesis.status == "PREDICTED_REACHABLE" else "APPROACH"
        ),
        stand=stand,
        landing=terminal_landing,
        target_entity_id=hypothesis.target_entity_id,
        reason=(
            "predicted footprint intersects target"
            if hypothesis.status == "PREDICTED_REACHABLE" else
            "target-conditioned falsification of the predicted routing limit"
        ),
        hypothesis_id=hypothesis.hypothesis_id,
        hypothesis_status=hypothesis.status,
        experiment_kind=(
            "CONTACT" if hypothesis.status == "PREDICTED_REACHABLE" else "FALSIFIER"
        ),
    )


__all__ = [
    "ReachabilitySignature", "SharedBridgeSupport", "TerrainHypothesis", "TerrainPalette", "TerrainPlan",
    "analyze_terrain_reachability", "infer_terrain_palette", "plan_hypothesis_test",
    "reachability_signature", "reachability_signature_changes",
    "shared_bridge_support",
]
