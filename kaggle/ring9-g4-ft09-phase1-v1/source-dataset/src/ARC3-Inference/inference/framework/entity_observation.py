"""Production-shaped G3 entity continuity and observation scopes.

Visual components are sightings.  Entity hypotheses persist only when the
adjacent observations admit a unique exact, recolor, translation, growth, or
shrink correspondence.  Ambiguous or deforming correspondence is surfaced and
does not silently preserve identity.

This module consumes the lossless ``site_transitions`` already produced by the
runtime evidence compiler.  It does not assign semantic meaning to integers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.masked_world_state import grids_from_probe_outcome


Cell = tuple[int, int]
Grid = tuple[tuple[int, ...], ...]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _components(
    grid: Grid, ignored_cells: Iterable[Cell] = ()
) -> tuple[dict[str, Any], ...]:
    height = len(grid)
    ignored = frozenset((int(row), int(col)) for row, col in ignored_cells)
    seen: set[Cell] = set()
    rows: list[dict[str, Any]] = []
    for row, values in enumerate(grid):
        for col, raw in enumerate(values):
            seed = (row, col)
            if seed in seen or seed in ignored:
                continue
            integer = int(raw)
            cells: set[Cell] = {seed}
            seen.add(seed)
            frontier = [seed]
            while frontier:
                r, c = frontier.pop()
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < len(grid[nr])
                        and (nr, nc) not in seen
                        and (nr, nc) not in ignored
                        and int(grid[nr][nc]) == integer
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        frontier.append((nr, nc))
            ordered = tuple(sorted(cells))
            rows.append({
                "integer": integer,
                "cells": ordered,
                "anchor": min(ordered),
                "bbox": (
                    min(r for r, _ in ordered),
                    min(c for _, c in ordered),
                    max(r for r, _ in ordered),
                    max(c for _, c in ordered),
                ),
            })
    return tuple(sorted(rows, key=lambda item: (len(item["cells"]), item["integer"], item["anchor"])))


def _normal(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _translation(left: tuple[Cell, ...], right: tuple[Cell, ...]) -> tuple[int, int] | None:
    if len(left) != len(right) or _normal(left) != _normal(right):
        return None
    l_anchor, r_anchor = min(left), min(right)
    delta = (r_anchor[0] - l_anchor[0], r_anchor[1] - l_anchor[1])
    return delta if delta != (0, 0) else None


@dataclass(frozen=True)
class EntitySighting:
    entity_id: str
    transition_id: int
    frame: str
    integer: int
    cells: tuple[Cell, ...]
    relation: str
    evidence_ref: str | None = None

    @property
    def anchor(self) -> Cell:
        return min(self.cells)


@dataclass
class EntityHypothesis:
    entity_id: str
    status: str = "PRESENT"
    version: int = 1
    member_ids: set[str] = field(default_factory=set)
    sightings: list[EntitySighting] = field(default_factory=list)
    ambiguity_refs: list[str] = field(default_factory=list)

    @property
    def current(self) -> EntitySighting | None:
        for sighting in reversed(self.sightings):
            if sighting.frame == "AFTER":
                return sighting
        return self.sightings[-1] if self.sightings else None


@dataclass(frozen=True)
class EntityTransition:
    transition_id: int
    evidence_ref: str | None
    relations: tuple[tuple[str, str, str], ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ObservationScope:
    schema: str
    transition_id: int
    target_entity_id: str | None
    target_member_id: str | None
    target_cells: tuple[Cell, ...]
    pre_action_owner_entity_id: str | None
    ego_expected_cells: tuple[Cell, ...]
    ego_confounded_cells: tuple[Cell, ...]
    ego_motion_basis: str
    body_contact_cells: tuple[Cell, ...]
    ground_exchange_cells: tuple[Cell, ...]
    counter_mask_cells: tuple[Cell, ...]
    status: str
    limitations: tuple[str, ...]


class EntityLedger:
    """Append-only worldline hypotheses reconstructed from runtime evidence."""

    def __init__(
        self,
        initial_grid: Sequence[Sequence[int]],
        *,
        ignored_cells: Iterable[Cell] = (),
        mask_law_version_id: str | None = None,
    ) -> None:
        self._grid: Grid = tuple(tuple(int(value) for value in row) for row in initial_grid)
        self._ignored_cells = frozenset(
            (int(row), int(col)) for row, col in ignored_cells
        )
        self.mask_law_version_id = (
            str(mask_law_version_id) if mask_law_version_id else None
        )
        self._active: dict[tuple[int, tuple[Cell, ...]], str] = {}
        self.entities: dict[str, EntityHypothesis] = {}
        self.member_to_entity: dict[str, str] = {}
        self._member_spawn_keys: dict[str, tuple[int, tuple[Cell, ...]]] = {}
        self._masked_projection_entities: dict[str, tuple[Cell, ...]] = {}
        self.role_bindings: dict[str, set[str]] = {}
        self.transitions: list[EntityTransition] = []
        self._transitions_by_id: dict[int, EntityTransition] = {}
        self.limitations: list[str] = []
        self._serial = 0
        self._seed(self._grid)

    def _new_entity(self, component: Mapping[str, Any], *, relation: str, transition_id: int) -> str:
        self._serial += 1
        entity_id = f"E{self._serial:04d}"
        sighting = EntitySighting(
            entity_id=entity_id,
            transition_id=transition_id,
            frame="BEFORE" if transition_id == 0 else "AFTER",
            integer=int(component["integer"]),
            cells=tuple(component["cells"]),
            relation=relation,
        )
        self.entities[entity_id] = EntityHypothesis(entity_id, sightings=[sighting])
        return entity_id

    def _seed(self, grid: Grid) -> None:
        self._active = {}
        for component in _components(grid, self._ignored_cells):
            entity_id = self._new_entity(component, relation="SEED", transition_id=0)
            key = (int(component["integer"]), tuple(component["cells"]))
            self._active[key] = entity_id

    def bind_members(self, members: Iterable[Mapping[str, Any]]) -> None:
        """Bind G2 member labels to seed hypotheses by exact pre-action footprint."""
        for member in members:
            member_id = str(member.get("member_id") or "")
            raw_cells = tuple(
                sorted(tuple(int(value) for value in cell) for cell in member.get("cells", ()))
            )
            cells = tuple(cell for cell in raw_cells if cell not in self._ignored_cells)
            integer = member.get("integer")
            entity_id = self._active.get((int(integer), cells)) if integer is not None else None
            if member_id and integer is not None and cells:
                self._member_spawn_keys[member_id] = (int(integer), cells)
            if member_id and entity_id is not None:
                self.member_to_entity[member_id] = entity_id
                self.entities[entity_id].member_ids.add(member_id)
            elif member_id and integer is not None and cells:
                # A total counter mask can split one frozen G2 component into
                # several disconnected outside-mask components. Keep the
                # projected subject as one auditable target identity instead
                # of silently dropping it because no single component owns
                # the complete projected footprint.
                entity_id = self._new_entity(
                    {"integer": int(integer), "cells": cells},
                    relation="MASKED_PROJECTION",
                    transition_id=0,
                )
                self.member_to_entity[member_id] = entity_id
                self.entities[entity_id].member_ids.add(member_id)
                self._masked_projection_entities[entity_id] = cells
                self.limitations.append(
                    f"member {member_id} uses a composite outside-mask projection"
                )

    def observe_reset(self, outcome: Mapping[str, Any]) -> EntityTransition:
        """Thread an observed life reset as a site-only back-edge.

        Virelai's earlier weave treats death as Groundhog Day: the same
        level-scoped entity returns at its exact spawn footprint, while the
        reset displacement is excluded from action-law evidence. Stable G2
        member labels are spawn slots, so they re-anchor existing entity ids
        by exact ``(integer, cells)`` equality and are never force-matched.
        """
        transition_id = int(outcome.get("transition_id") or 0)
        if transition_id in self._transitions_by_id:
            return self._transitions_by_id[transition_id]
        evidence_ref = str(outcome.get("evidence_id") or "") or None
        grids = grids_from_probe_outcome(outcome)
        if grids is None:
            limitation = "reset continuity requires total fixed-geometry site_transitions"
            self.limitations.append(limitation)
            transition = EntityTransition(transition_id, evidence_ref, (), (limitation,))
            self.transitions.append(transition)
            self._transitions_by_id[transition_id] = transition
            return transition
        _before, after = grids
        components = tuple(_components(after, self._ignored_cells))
        by_key = {
            (int(component["integer"]), tuple(component["cells"])): component
            for component in components
        }
        next_active: dict[tuple[int, tuple[Cell, ...]], str] = {}
        relations: list[tuple[str, str, str]] = []
        reused: set[str] = set()
        for member_id, key in self._member_spawn_keys.items():
            component = by_key.get(key)
            entity_id = self.member_to_entity.get(member_id)
            if component is None or entity_id is None or entity_id in reused:
                continue
            entity = self.entities[entity_id]
            entity.version += 1
            entity.status = "PRESENT"
            entity.sightings.append(EntitySighting(
                entity_id=entity_id,
                transition_id=transition_id,
                frame="AFTER",
                integer=int(component["integer"]),
                cells=tuple(component["cells"]),
                relation="RESET_RETURN",
                evidence_ref=evidence_ref,
            ))
            next_active[key] = entity_id
            reused.add(entity_id)
            relations.append((entity_id, "RESET_RETURN", "PRESENT"))
        for key, component in by_key.items():
            if key in next_active:
                continue
            entity_id = self._new_entity(
                component, relation="RESET_BIRTH", transition_id=transition_id
            )
            next_active[key] = entity_id
            relations.append((entity_id, "RESET_BIRTH", "PRESENT"))
        for entity_id in set(self._active.values()) - reused:
            self.entities[entity_id].status = "ABSENT"
            relations.append((entity_id, "RESET_ABSENCE", "ABSENT"))
        self._active = next_active
        self._grid = after
        transition = EntityTransition(
            transition_id, evidence_ref, tuple(sorted(relations)), ()
        )
        self.transitions.append(transition)
        self._transitions_by_id[transition_id] = transition
        return transition

    def entity_for_member(self, member_id: str | None) -> str | None:
        return self.member_to_entity.get(str(member_id)) if member_id else None

    def bind_role_cells(self, role: str, cells: Iterable[Cell]) -> tuple[str, ...]:
        """Bind a role explicitly to seed entities whose footprints overlap its cells."""
        role_name = str(role or "").strip().upper()
        requested = {(int(row), int(col)) for row, col in cells}
        matched = {
            entity_id
            for (_integer, footprint), entity_id in self._active.items()
            if requested and set(footprint) & requested
        }
        if role_name and matched:
            self.role_bindings.setdefault(role_name, set()).update(matched)
        elif role_name and requested:
            self.limitations.append(f"role {role_name} has no matching seed entity")
        return tuple(sorted(matched))

    def role_entities(self, role: str) -> tuple[str, ...]:
        return tuple(sorted(self.role_bindings.get(str(role or "").strip().upper(), set())))

    def entity_at(self, cell: Cell, *, before: bool = True) -> str | None:
        del before  # the ledger's active map is always the pre-action view for scope building
        if cell in self._ignored_cells:
            return None
        for entity_id, cells in self._masked_projection_entities.items():
            if cell in cells:
                return entity_id
        for (integer, cells), entity_id in self._active.items():
            del integer
            if cell in cells:
                return entity_id
        return None

    def cells_for(self, entity_id: str | None) -> tuple[Cell, ...]:
        if entity_id is None or entity_id not in self.entities:
            return ()
        if self.entities[entity_id].status != "PRESENT":
            return ()
        sighting = self.entities[entity_id].current
        return () if sighting is None else sighting.cells

    def observe(self, outcome: Mapping[str, Any]) -> EntityTransition:
        transition_id = int(outcome.get("transition_id") or 0)
        if transition_id in self._transitions_by_id:
            return self._transitions_by_id[transition_id]
        evidence_ref = str(outcome.get("evidence_id") or "") or None
        grids = grids_from_probe_outcome(outcome)
        if grids is None:
            limitation = "entity continuity requires total fixed-geometry site_transitions"
            self.limitations.append(limitation)
            transition = EntityTransition(transition_id, evidence_ref, (), (limitation,))
            self.transitions.append(transition)
            self._transitions_by_id[transition_id] = transition
            return transition
        before, after = grids
        if before != self._grid:
            limitation = "before frame did not match the ledger's current frame"
            self.limitations.append(limitation)
            transition = EntityTransition(transition_id, evidence_ref, (), (limitation,))
            self.transitions.append(transition)
            self._transitions_by_id[transition_id] = transition
            return transition
        current = tuple(
            {"integer": item["integer"], "cells": item["cells"]}
            for item in _components(after, self._ignored_cells)
        )
        relations: list[tuple[str, str, str]] = []
        next_active: dict[tuple[int, tuple[Cell, ...]], str] = {}
        consumed_previous: set[str] = set()
        for now in current:
            exact = self._active.get((int(now["integer"]), tuple(now["cells"])))
            if exact is not None and exact not in consumed_previous:
                entity_id, relation = exact, "STILL"
            else:
                candidates = []
                for (integer, cells), candidate_id in self._active.items():
                    if candidate_id in consumed_previous or integer != int(now["integer"]):
                        continue
                    translation = _translation(tuple(cells), tuple(now["cells"]))
                    if translation is not None:
                        candidates.append(candidate_id)
                if len(candidates) == 1:
                    entity_id, relation = candidates[0], "MOVE"
                elif len(candidates) > 1:
                    entity_id, relation = self._new_entity(now, relation="AMBIGUOUS_BIRTH", transition_id=transition_id), "AMBIGUOUS"
                    self.entities[entity_id].ambiguity_refs.append(evidence_ref or f"T-{transition_id}")
                else:
                    same_footprint = [
                        candidate_id
                        for (integer, cells), candidate_id in self._active.items()
                        if candidate_id not in consumed_previous and tuple(cells) == tuple(now["cells"])
                    ]
                    if len(same_footprint) == 1:
                        entity_id, relation = same_footprint[0], "RECOLOR"
                    else:
                        entity_id, relation = self._new_entity(now, relation="BIRTH", transition_id=transition_id), "BIRTH"
            consumed_previous.add(entity_id)
            old = self.entities[entity_id]
            old.version += 1
            old.status = "PRESENT"
            old.sightings.append(EntitySighting(
                entity_id=entity_id,
                transition_id=transition_id,
                frame="AFTER",
                integer=int(now["integer"]),
                cells=tuple(now["cells"]),
                relation=relation,
                evidence_ref=evidence_ref,
            ))
            next_active[(int(now["integer"]), tuple(now["cells"]))] = entity_id
            relations.append((entity_id, relation, "PRESENT"))
        for entity_id in set(self._active.values()) - consumed_previous:
            self.entities[entity_id].status = "ABSENT"
            relations.append((entity_id, "DEATH_OR_DEFORM", "ABSENT"))
        self._active = next_active
        self._grid = after
        transition = EntityTransition(transition_id, evidence_ref, tuple(sorted(relations)), ())
        self.transitions.append(transition)
        self._transitions_by_id[transition_id] = transition
        return transition

    def scope(
        self,
        outcome: Mapping[str, Any],
        *,
        target_member_id: str | None = None,
        target_entity_id: str | None = None,
        ego_entity_ids: Iterable[str] = (),
        ground_entity_ids: Iterable[str] = (),
        counter_mask_cells: Iterable[Cell] = (),
        expected_ego_motion: bool = False,
    ) -> ObservationScope:
        transition_id = int(outcome.get("transition_id") or 0)
        target_entity_id = target_entity_id or self.entity_for_member(target_member_id)
        target_cells = self.cells_for(target_entity_id)
        acted = outcome.get("acted_site")
        acted_cell = (
            (int(acted["row"]), int(acted["col"]))
            if isinstance(acted, Mapping) and "row" in acted and "col" in acted else None
        )
        owner = self.entity_at(acted_cell) if acted_cell is not None else None
        ego_before = set().union(*(self.cells_for(entity_id) for entity_id in ego_entity_ids))
        # Observe once, then the AFTER sighting is available through the same ids.
        transition = self.observe(outcome)
        if any("before frame did not match" in item for item in transition.limitations):
            owner = None
        ego_after = set().union(*(self.cells_for(entity_id) for entity_id in ego_entity_ids))
        contact = set(target_cells) & ego_after
        ground = set().union(*(self.cells_for(entity_id) for entity_id in ground_entity_ids))
        ego_motion = (ego_before | ego_after) if expected_ego_motion else set()
        changed = {
            (int(item["row"]), int(item["col"]))
            for item in outcome.get("changed_cells") or ()
            if isinstance(item, Mapping)
        }
        confounded = (changed & ego_after) - set(target_cells)
        limitations = list(transition.limitations)
        if target_entity_id is None:
            limitations.append("target member has no resolved persistent entity hypothesis")
        if target_entity_id is not None and not target_cells:
            limitations.append("target entity is not present in the pre-action ledger")
        status = "READY" if target_entity_id is not None and bool(target_cells) and not limitations else "UNRESOLVED"
        return ObservationScope(
            schema="virelai-g3-observation-scope-v1",
            transition_id=transition_id,
            target_entity_id=target_entity_id,
            target_member_id=target_member_id,
            target_cells=tuple(sorted(target_cells)),
            pre_action_owner_entity_id=owner,
            ego_expected_cells=tuple(sorted(ego_motion & changed)),
            ego_confounded_cells=tuple(sorted(confounded)),
            ego_motion_basis=(
                "AUTHORIZED_EGO_MOTION_SCOPE"
                if expected_ego_motion else "NO_AUTHORIZED_EGO_MOTION_FOR_ACTION"
            ),
            body_contact_cells=tuple(sorted(contact & changed)),
            ground_exchange_cells=tuple(sorted(ground & changed)),
            counter_mask_cells=tuple(sorted(set(counter_mask_cells) & changed)),
            status=status,
            limitations=tuple(dict.fromkeys(limitations)),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "virelai-g3-entity-ledger-v1",
            "mask_law_version_id": self.mask_law_version_id,
            "ignored_cell_count": len(self._ignored_cells),
            "entity_count": len(self.entities),
            "present_entity_ids": sorted(
                entity_id for entity_id, item in self.entities.items() if item.status == "PRESENT"
            ),
            "member_bindings": dict(sorted(self.member_to_entity.items())),
            "role_bindings": {
                role: sorted(entity_ids)
                for role, entity_ids in sorted(self.role_bindings.items())
            },
            "entities": {
                entity_id: {
                    "status": item.status,
                    "version": item.version,
                    "member_ids": sorted(item.member_ids),
                    "ambiguity_refs": list(item.ambiguity_refs),
                    "sightings": [asdict(sighting) for sighting in item.sightings[-4:]],
                }
                for entity_id, item in sorted(self.entities.items())
            },
            "transition_count": len(self.transitions),
            "limitations": list(dict.fromkeys(self.limitations)),
        }


def evidence_digest(outcome: Mapping[str, Any]) -> str:
    return "OBS-" + hashlib.sha256(_canonical(outcome).encode()).hexdigest()[:16]


__all__ = ["EntityHypothesis", "EntityLedger", "EntitySighting", "EntityTransition", "ObservationScope", "evidence_digest"]
