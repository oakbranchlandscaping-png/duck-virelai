"""Compile Ring 8's lossless journal into one evidence-grounded semantic library.

This is the missing integration seam.  It joins the compact record, flip-book cuts,
worldlines, foundation roles, and exact per-action object arithmetic in one immutable
artifact.  It deliberately does not infer mechanisms, objectives, or win causes yet.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Iterable, Sequence

from inference.framework.virelai_runtime import CompactFrameJournal, CompactFrameRecord
from virelai_golden.roles.infer import RoleRead, infer_roles
from virelai_golden.substrate.ledger import Cut, cuts, grade_pristine
from virelai_golden.substrate.record import Given, Record, build, freeze_layers
from virelai_golden.weave.rejoin import re_join
from virelai_golden.weave.verbs import Verb
from virelai_golden.weave.worldline import Worldline, region_at, weave_window
from inference.framework.virelai_semantic.mechanics import compile_lever_mechanics

SEMANTIC_LIBRARY_SCHEMA = "virelai-semantic-library-shadow-v1"


@dataclass(frozen=True)
class EvidenceRef:
    left_node: int
    right_node: int
    action_id: int | None


@dataclass(frozen=True)
class RoleClaim:
    role: str
    status: str
    witness_count: int
    witnesses: tuple[EvidenceRef, ...]
    basis: str
    limitations: str


@dataclass(frozen=True)
class ObjectState:
    node: int
    integer_class: int
    cells: int
    anchor: tuple[int, int]
    bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class EntityDossier:
    handle: str
    worldline_id: int
    segment: str
    born_node: int
    last_seen_node: int
    observations: int
    current: ObjectState
    verbs_observed: tuple[str, ...]
    roles: tuple[RoleClaim, ...]


@dataclass(frozen=True)
class SemanticObjectState:
    node: int
    present: bool
    integer_classes: tuple[int, ...]
    components: int
    cells: int
    bbox: tuple[int, int, int, int] | None


@dataclass(frozen=True)
class SemanticEntity:
    handle: str
    kind: str
    segment: str
    member_handles: tuple[str, ...]
    born_node: int
    last_seen_node: int
    observations: int
    current: SemanticObjectState
    verbs_observed: tuple[str, ...]
    roles: tuple[RoleClaim, ...]


@dataclass(frozen=True)
class ObjectDelta:
    handle: str
    worldline_id: int
    verb: str
    integer_class_before: int
    integer_class_after: int
    cells_before: int
    cells_after: int
    anchor_before: tuple[int, int]
    anchor_after: tuple[int, int]
    motion: tuple[int, int]
    entered_sites: tuple[tuple[int, int, int, int], ...]
    departed_sites: tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class JointDelta:
    left_node: int
    right_node: int
    action_id: int | None
    acted_cell: tuple[int, int] | None
    visible_cells_rewritten: int
    objects: tuple[ObjectDelta, ...]


@dataclass(frozen=True)
class ControlModel:
    kind: str
    status: str
    witness_count: int
    witnesses: tuple[EvidenceRef, ...]
    basis: str
    limitations: str


@dataclass(frozen=True)
class SegmentModel:
    segment: str
    level: int
    life: int
    shape: tuple[int, int]
    first_node: int
    last_node: int
    pristine: bool
    control: ControlModel
    semantic_entities: tuple[SemanticEntity, ...]
    lever_mechanics: dict[str, Any]
    entities: tuple[EntityDossier, ...]
    joint_deltas: tuple[JointDelta, ...]
    role_typed_order: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _canonical(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_canonical(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(_canonical(value), indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_canonical(row), sort_keys=True) + "\n")
    temporary.replace(path)


def journal_to_record(journal: CompactFrameJournal) -> Record:
    """Losslessly adapt the passive journal; no visual or semantic field is invented."""
    records: Sequence[CompactFrameRecord] = tuple(journal.iter_records())
    givens = [
        Given(
            layers=freeze_layers(record.reconstruct_frame()),
            state=record.state,
            levels_completed=record.levels_completed,
            win_levels=record.win_levels,
            available_actions=record.available_actions,
            full_reset=record.full_reset,
            guid=str(record.guid or ""),
            game_id=record.game_id,
            action=(record.action_id, record.acted_cell) if record.action_id is not None else None,
        )
        for record in records
    ]
    return build(
        givens,
        origin="RING8_INITIAL_FRAME",
        action_channel="LIVE(RING8_JOURNAL)",
        source="CompactFrameJournal",
    )


def _segment_cuts(record: Record, node_cuts: Sequence[Cut]) -> list[tuple[int, int, int, tuple[Cut, ...]]]:
    """Split only on observed level, life, or geometry boundaries."""
    groups: list[tuple[int, int, int, tuple[Cut, ...]]] = []
    current: list[Cut] = []
    current_key: tuple[int, int, tuple[int, int]] | None = None
    ordinal = 0
    for node, cut in zip(record.nodes, node_cuts):
        key = (max(1, node.levels_completed + 1), node.life, cut.shape)
        if current and key != current_key:
            ordinal += 1
            assert current_key is not None
            groups.append((ordinal, current_key[0], current_key[1], tuple(current)))
            current = []
        current_key = key
        current.append(cut)
    if current:
        ordinal += 1
        assert current_key is not None
        groups.append((ordinal, current_key[0], current_key[1], tuple(current)))
    return groups


def _handle(segment: str, worldline: Worldline) -> str:
    region = worldline.first_region
    return (
        f"{segment}-N{worldline.first_node:04d}-"
        f"C{region.value}-R{region.anchor[0]}-C{region.anchor[1]}-A{region.area}"
    )


def _bbox(cells: frozenset[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _edge_refs(worldline: Worldline, predicate: Any = None) -> tuple[EvidenceRef, ...]:
    refs: list[EvidenceRef] = []
    for index, edge in enumerate(worldline.edges):
        if predicate is not None and not predicate(edge):
            continue
        left, right = worldline.steps[index][0], worldline.steps[index + 1][0]
        refs.append(EvidenceRef(left, right, None))
    return tuple(refs)


def _refs_with_actions(record: Record, refs: Iterable[EvidenceRef]) -> tuple[EvidenceRef, ...]:
    return tuple(
        EvidenceRef(
            ref.left_node,
            ref.right_node,
            None if record.nodes[ref.right_node].action is None else record.nodes[ref.right_node].action[0],
        )
        for ref in refs
    )


def _role_claims(record: Record, read: RoleRead, worldline: Worldline) -> tuple[RoleClaim, ...]:
    verdict = read.verdicts[worldline.id]
    role = verdict.band2
    if role is None:
        return ()
    claims: list[RoleClaim] = []
    for name in str(role).split("+"):
        refs: tuple[EvidenceRef, ...] = ()
        if name == "EGO":
            refs = _edge_refs(worldline, lambda edge: edge.verb is Verb.MOVE)
        elif name == "GROUND" and read.ground is not None:
            steps = [step for item in read.ground.verdicts if worldline.id in item.members for step in item.steps]
            refs = tuple(EvidenceRef(step.left, step.right, step.action) for step in steps)
        elif name == "WALL" and read.walls is not None and worldline.id in read.walls.verdicts:
            refs = tuple(
                EvidenceRef(item.left, item.right, item.action)
                for item in read.walls.verdicts[worldline.id].refusals
            )
        elif name == "COUNTER" and read.counters and worldline.id in read.counters:
            refs = _edge_refs(worldline, lambda edge: edge.verb is not Verb.STILL)
        elif name == "LEVER" and read.levers is not None and worldline.id in read.levers.verdicts:
            refs = tuple(
                EvidenceRef(press.left, press.right, press.action)
                for press in read.levers.presses
                if worldline.id in press.attributed and any(partner != worldline.id for partner in press.partners)
            )
        refs = _refs_with_actions(record, refs)
        claims.append(
            RoleClaim(
                role=name,
                status="DETECTOR_VERDICT_UNVALIDATED",
                witness_count=len(refs),
                witnesses=refs,
                basis=verdict.basis,
                limitations=verdict.parallax,
            )
        )
    return tuple(claims)


def _control_model(record: Record, read: RoleRead, worldlines: Sequence[Worldline]) -> ControlModel:
    if read.pointer is not None:
        witness = read.pointer.witness
        return ControlModel(
            kind="POINTER",
            status="DETECTOR_VERDICT_UNVALIDATED",
            witness_count=len(read.pointer.delta_presses),
            witnesses=tuple(
                EvidenceRef(press.node - 1, press.node, press.action)
                for press in read.pointer.delta_presses
            ),
            basis=read.pointer.basis,
            limitations=read.pointer.parallax,
        )
    bodies = [body for body in read.bodies if body.members]
    if bodies:
        ego_members = {member for body in bodies for member in body.members}
        refs = [
            ref
            for worldline in worldlines
            if worldline.id in ego_members
            for ref in _refs_with_actions(
                record,
                _edge_refs(worldline, lambda edge: edge.verb is Verb.MOVE),
            )
        ]
        return ControlModel(
            kind="BODY",
            status="DETECTOR_VERDICT_UNVALIDATED",
            witness_count=len(refs),
            witnesses=tuple(refs),
            basis=" ‖ ".join(body.basis for body in bodies),
            limitations=" ; ".join(body.parallax for body in bodies),
        )
    return ControlModel(
        kind="UNKNOWN",
        status="UNRESOLVED",
        witness_count=0,
        witnesses=(),
        basis="No ego modality satisfied its exact observational predicate in this segment.",
        limitations="Absence of a verdict is not evidence that the world has no ego.",
    )


def _object_delta(
    record: Record,
    segment: str,
    worldline: Worldline,
    left_node: int,
    right_node: int,
) -> ObjectDelta | None:
    before, after = region_at(worldline, left_node), region_at(worldline, right_node)
    if before is None or after is None or before.fingerprint == after.fingerprint:
        return None
    before_grid = record.nodes[left_node].settled
    after_grid = record.nodes[right_node].settled
    departed = tuple(
        (row, col, before.value, int(after_grid[row, col]))
        for row, col in sorted(before.cells - after.cells)
    )
    entered = tuple(
        (row, col, int(before_grid[row, col]), after.value)
        for row, col in sorted(after.cells - before.cells)
    )
    verb = next(
        (
            edge.verb.value
            for index, edge in enumerate(worldline.edges)
            if worldline.steps[index][0] == left_node and worldline.steps[index + 1][0] == right_node
        ),
        "CHANGED",
    )
    return ObjectDelta(
        handle=_handle(segment, worldline),
        worldline_id=worldline.id,
        verb=verb,
        integer_class_before=before.value,
        integer_class_after=after.value,
        cells_before=before.area,
        cells_after=after.area,
        anchor_before=before.anchor,
        anchor_after=after.anchor,
        motion=(after.anchor[0] - before.anchor[0], after.anchor[1] - before.anchor[1]),
        entered_sites=entered,
        departed_sites=departed,
    )


def _joint_deltas(
    record: Record,
    segment: str,
    window: Sequence[Cut],
    worldlines: Sequence[Worldline],
) -> tuple[JointDelta, ...]:
    out: list[JointDelta] = []
    for left, right in zip(window, window[1:]):
        node = record.nodes[right.node]
        action_id = None if node.action is None else node.action[0]
        acted_cell = None if node.action is None else node.action[1]
        before_grid, after_grid = record.nodes[left.node].settled, node.settled
        changed = -1 if before_grid.shape != after_grid.shape else int((before_grid != after_grid).sum())
        object_rows = tuple(
            row
            for worldline in worldlines
            if (row := _object_delta(record, segment, worldline, left.node, right.node)) is not None
        )
        out.append(JointDelta(left.node, right.node, action_id, acted_cell, changed, object_rows))
    return tuple(out)


def _merge_claims(dossiers: Sequence[EntityDossier]) -> tuple[RoleClaim, ...]:
    by_role: dict[str, list[RoleClaim]] = {}
    for dossier in dossiers:
        for claim in dossier.roles:
            by_role.setdefault(claim.role, []).append(claim)
    merged = []
    for role, claims in sorted(by_role.items()):
        witnesses = {
            (ref.left_node, ref.right_node, ref.action_id): ref
            for claim in claims
            for ref in claim.witnesses
        }
        merged.append(
            RoleClaim(
                role=role,
                status="DETECTOR_VERDICT_UNVALIDATED",
                witness_count=len(witnesses),
                witnesses=tuple(witnesses[key] for key in sorted(witnesses, key=lambda item: (item[1], item[0]))),
                basis=" ‖ ".join(dict.fromkeys(claim.basis for claim in claims if claim.basis)),
                limitations=" ; ".join(
                    dict.fromkeys(claim.limitations for claim in claims if claim.limitations)
                ),
            )
        )
    return tuple(merged)


def _semantic_entities(
    segment: str,
    window: Sequence[Cut],
    worldlines: Sequence[Worldline],
    read: RoleRead,
    dossiers: Sequence[EntityDossier],
) -> tuple[SemanticEntity, ...]:
    """Fold implementation worldlines into the role-level things a player would consult."""
    by_id = {worldline.id: worldline for worldline in worldlines}
    dossier_by_id = {dossier.worldline_id: dossier for dossier in dossiers}
    groups: list[tuple[str, tuple[int, ...]]] = []
    assigned: set[int] = set()
    for body in read.bodies:
        members = tuple(member for member in body.members if member not in assigned)
        if members:
            groups.append(("EGO_BODY", members))
            assigned.update(members)
    if read.ground is not None:
        for ground in read.ground.verdicts:
            members = tuple(member for member in ground.members if member not in assigned)
            if members:
                groups.append(("GROUND", members))
                assigned.update(members)
    counter_ids = set(read.counters or {}) - assigned
    counter_support = {
        wid: frozenset(cell for _, region in by_id[wid].steps for cell in region.cells)
        for wid in counter_ids
    }
    while counter_ids:
        component = {min(counter_ids)}
        changed = True
        while changed:
            changed = False
            footprint = frozenset(cell for wid in component for cell in counter_support[wid])
            neighbours = {
                wid for wid in counter_ids - component if footprint & counter_support[wid]
            }
            if neighbours:
                component.update(neighbours)
                changed = True
        members = tuple(sorted(component))
        groups.append(("COUNTER_PROCESS", members))
        assigned.update(members)
        counter_ids.difference_update(component)
    for worldline in worldlines:
        if worldline.id not in assigned:
            groups.append(("OBJECT", (worldline.id,)))

    current_node = window[-1].node
    rows = []
    kind_count: dict[str, int] = {}
    for base_kind, members in groups:
        member_dossiers = [dossier_by_id[member] for member in members]
        claims = _merge_claims(member_dossiers)
        role_names = {claim.role for claim in claims}
        kind = base_kind
        if base_kind == "OBJECT" and role_names:
            kind = "+".join(sorted(role_names))
        kind_count[kind] = kind_count.get(kind, 0) + 1
        if len(members) == 1 and kind == "OBJECT":
            handle = member_dossiers[0].handle.replace("-N", "-OBJECT-N", 1)
        else:
            handle = f"{segment}-{kind}-{kind_count[kind]:02d}"

        current_regions = [region_at(by_id[member], current_node) for member in members]
        current_regions = [region for region in current_regions if region is not None]
        current_cells = frozenset(cell for region in current_regions for cell in region.cells)
        state = SemanticObjectState(
            node=current_node,
            present=bool(current_regions),
            integer_classes=tuple(sorted({region.value for region in current_regions})),
            components=len(current_regions),
            cells=len(current_cells),
            bbox=_bbox(current_cells) if current_cells else None,
        )
        rows.append(
            SemanticEntity(
                handle=handle,
                kind=kind,
                segment=segment,
                member_handles=tuple(dossier.handle for dossier in member_dossiers),
                born_node=min(dossier.born_node for dossier in member_dossiers),
                last_seen_node=max(dossier.last_seen_node for dossier in member_dossiers),
                observations=sum(dossier.observations for dossier in member_dossiers),
                current=state,
                verbs_observed=tuple(
                    sorted({verb for dossier in member_dossiers for verb in dossier.verbs_observed})
                ),
                roles=claims,
            )
        )
    return tuple(rows)


def _compile_segment(
    record: Record,
    ordinal: int,
    level: int,
    life: int,
    window: tuple[Cut, ...],
    record_pristine: bool,
) -> SegmentModel:
    segment = f"L{level}-F{life}-S{ordinal}"
    worldlines = re_join(weave_window(window), window)
    read = infer_roles(record, window, worldlines)
    entities = []
    for worldline in worldlines:
        current = worldline.last_region
        entities.append(
            EntityDossier(
                handle=_handle(segment, worldline),
                worldline_id=worldline.id,
                segment=segment,
                born_node=worldline.first_node,
                last_seen_node=worldline.last_node,
                observations=len(worldline.steps),
                current=ObjectState(
                    node=worldline.last_node,
                    integer_class=current.value,
                    cells=current.area,
                    anchor=current.anchor,
                    bbox=_bbox(current.cells),
                ),
                verbs_observed=tuple(sorted({edge.verb.value for edge in worldline.edges})),
                roles=_role_claims(record, read, worldline),
            )
        )
    semantic_entities = _semantic_entities(segment, window, worldlines, read, entities)
    lever_mechanics = compile_lever_mechanics(
        segment=segment,
        record=record,
        read=read,
        worldlines=worldlines,
        semantic_entities=semantic_entities,
        raw_handle=_handle,
    )
    return SegmentModel(
        segment=segment,
        level=level,
        life=life,
        shape=window[0].shape,
        first_node=window[0].node,
        last_node=window[-1].node,
        pristine=record_pristine,
        control=_control_model(record, read, worldlines),
        semantic_entities=semantic_entities,
        lever_mechanics=lever_mechanics,
        entities=tuple(entities),
        joint_deltas=_joint_deltas(record, segment, window, worldlines),
        role_typed_order=read.typed,
    )


def compile_semantic_library(journal: CompactFrameJournal) -> dict[str, Any]:
    started = time.perf_counter()
    record = journal_to_record(journal)
    node_cuts = cuts(record)
    pristine = grade_pristine(record, node_cuts)
    segments = tuple(
        _compile_segment(record, ordinal, level, life, window, pristine.passed)
        for ordinal, level, life, window in _segment_cuts(record, node_cuts)
    )
    detector_claims = sum(
        len(entity.roles)
        for segment in segments
        for entity in segment.entities
    )
    payload = {
        "schema": SEMANTIC_LIBRARY_SCHEMA,
        "game_id": record.game_id,
        "source": record.source,
        "action_channel": record.action_channel,
        "observed_nodes": len(record.nodes),
        "observed_transitions": max(0, len(record.nodes) - 1),
        "levels_observed": sorted({segment.level for segment in segments}),
        "lives_observed": record.lives,
        "record_pristine": pristine.passed,
        "record_pristine_nodes": pristine.n_pass,
        "segments": [_canonical(segment) for segment in segments],
        "summary": {
            "segments": len(segments),
            "entities": sum(len(segment.entities) for segment in segments),
            "semantic_entities": sum(len(segment.semantic_entities) for segment in segments),
            "detector_role_claims": detector_claims,
            "role_claim_validation": "NOT_RUN",
            "joint_delta_rows": sum(len(segment.joint_deltas) for segment in segments),
            "compile_ms": round((time.perf_counter() - started) * 1000.0, 3),
            "model_exposed": False,
            "mechanics_compiled": True,
            "mechanics_validation": "NOT_RUN",
            "objectives_compiled": False,
        },
        "epistemic_limits": [
            "The 4-connected component partition is an explicit interim ontology.",
            "Worldline correspondence remains the anchor-first INTERIM_O9 matcher.",
            "Roles are exact verdicts under the current predicates, not hidden purposes.",
            "Role detector verdicts remain unvalidated until a fixture grades each claim type.",
            "No mechanism, objective, or win cause is inferred in this shadow milestone.",
        ],
    }
    return payload


class SemanticLibraryCompiler:
    """Persistence boundary for the shadow library; compilation is never on the action path."""

    def __init__(self, *, artifact_dir: Path | None) -> None:
        self.artifact_dir = artifact_dir
        self.last_summary: dict[str, Any] | None = None

    def close(self, journal: CompactFrameJournal) -> dict[str, Any]:
        library = compile_semantic_library(journal)
        if self.artifact_dir is not None:
            _write_json(self.artifact_dir / "semantic_library.json", library)
            _write_jsonl(
                self.artifact_dir / "semantic_entities.jsonl",
                (
                    entity
                    for segment in library["segments"]
                    for entity in segment["semantic_entities"]
                ),
            )
            _write_jsonl(
                self.artifact_dir / "worldline_dossiers.jsonl",
                (
                    entity
                    for segment in library["segments"]
                    for entity in segment["entities"]
                ),
            )
            _write_jsonl(
                self.artifact_dir / "semantic_joint_deltas.jsonl",
                (
                    row
                    for segment in library["segments"]
                    for row in segment["joint_deltas"]
                ),
            )
        self.last_summary = dict(library["summary"])
        return self.last_summary
