"""The level census: every object seen on a level, what the gates certify about it, and what is open.

Author: Claude (Alpha build seat), 2026-10-10. WO-L2a (INTERFACE_WO_L2A_WORLD_MODEL_V2 v2; Sol's reviews of
WO-L2-00 and of the interface, 2026-10-10).

A pure, read-only projection. It never calls a gate method that builds or freezes state (no G3
``_ensure_*``, ``snapshot``, ``inventory_view`` or ``next_probe*``); it reads attributes and active
products only, so a census taken at G1 leaves G3 uninitialized.

**Observation tier.** The level-entry board and the level's recorded transitions
(``machine.transition_index``) are cut into components and threaded by the runtime weave's own
algorithm (``virelai_continuity.weave_window`` then ``re_join``), one window per life. Tracks are scoped
to level and life: identical spawn pixels in two lives are a *possible correspondence*, never a join.
The entry board is ``INITIAL_FRAME`` or ``LEVEL_ENTRY``, never a transition.

**Certified tier.** EGO from the G1 product, COUNTER from the G2 product (a spatial mask; an object joins
it only on an exact footprint at a mask witness), LEVER from a G3 witness (inventory status separate).
A track joins a G3 entity only on an exact one-to-one ``(time, integer, cells)`` key. Everything else is
a typed gap; INERT, force, driven reactions, scoped negatives and Band 1 are ``NOT_BUILT``.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.virelai_continuity import (
    ComponentObservation,
    NodeCut,
    _shape_hash,
    re_join,
    weave_window,
)

Grid = tuple[tuple[int, ...], ...]
Cell = tuple[int, int]
GATE_ORDER = (
    "G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS",
    "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW",
)
CLASS_VERBS = frozenset({"RECOLOR", "GROW", "SHRINK", "DEFORM"})
LEVEL_GAPS = (
    ("INERT", "Is any object coverage-certified INERT?", "NOT_BUILT", "no coverage certificate exists (G6, WO-L3b)"),
    ("ENVIRONMENTAL_FORCE", "Does any environmental force act on this level?", "NOT_BUILT", "no G5 gate (WO-L3a)"),
    ("REACTIVE_DRIVEN", "Which objects are driven by another object?", "NOT_BUILT", "no driven-reaction gate (WO-DRIVEN)"),
    ("SCOPED_NEGATIVES", "What was shown not to happen, and under what scope?", "NOT_BUILT", "no G6 chapter (WO-L3b)"),
    ("BAND1", "Which objects are STATIC or REACTIVE under the animation law?", "NOT_BUILT", "settled-frame Band 1 is a later slice"),
)


@dataclass(frozen=True)
class ExecutionRecord:
    """What the harness actually executed, given explicitly (never read from hidden state)."""

    entry_board: Grid
    entry_level: int
    valid_actions: tuple[str, ...]
    executed: tuple[str, ...] = ()  # action names in execution order; transition_id = index + 1


@dataclass
class _Window:
    life: int
    cuts: list[NodeCut] = field(default_factory=list)
    sources: dict[int, dict[str, Any]] = field(default_factory=dict)


def _grid(value: Iterable[Iterable[int]]) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in value]


def board_cut(grid: Sequence[Sequence[int]], *, node: int, level: int) -> NodeCut:
    """The runtime weave's cut (``cut_visible_frame``) computed from a grid instead of a frame record."""
    rows, cols = len(grid), len(grid[0]) if grid else 0
    seen: set[Cell] = set()
    components: list[tuple[int, tuple[Cell, ...]]] = []
    for start_row in range(rows):
        for start_col in range(cols):
            if (start_row, start_col) in seen:
                continue
            class_id = int(grid[start_row][start_col])
            stack, cells = [(start_row, start_col)], []
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                    if 0 <= other[0] < rows and 0 <= other[1] < cols and other not in seen \
                            and int(grid[other[0]][other[1]]) == class_id:
                        seen.add(other)
                        stack.append(other)
            components.append((class_id, tuple(sorted(cells))))
    components.sort(key=lambda item: item[1][0])
    regions = tuple(
        ComponentObservation(
            node_index=node, level=level, component_id=index, class_id=class_id, cells=cells,
            anchor=(min(r for r, _ in cells), min(c for _, c in cells)),
            bbox=(min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)),
            cell_count=len(cells), shape_hash=_shape_hash(class_id, cells),
        )
        for index, (class_id, cells) in enumerate(components)
    )
    digest = hashlib.sha256(repr([list(row) for row in grid]).encode()).hexdigest()
    return NodeCut(node, level, (rows, cols), digest, False, None, None, regions)


def level_rows(transition_index: Sequence[Mapping[str, Any]], level: int) -> list[dict[str, Any]]:
    return sorted((dict(row) for row in transition_index if row.get("level") == level),
                  key=lambda row: int(row["transition_id"]))


def _windows(level: int, entry_board: Grid, entry: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
             entry_life: int) -> tuple[list[_Window], list[list[int]], list[dict[str, Any]]]:
    """Replay the level's rows from its entry board, one weave window per life."""
    board = _grid(entry_board)
    entry_node = (int(rows[0]["transition_id"]) - 1) if rows else 0
    windows = [_Window(entry_life)]
    windows[0].cuts.append(board_cut(board, node=entry_node, level=level))
    windows[0].sources[entry_node] = dict(entry)
    discontinuities: list[dict[str, Any]] = []
    for row in rows:
        transition_id = int(row["transition_id"])
        for r, c, before, after in row.get("changed") or ():
            if before is not None and board[r][c] != before:
                discontinuities.append({"transition_id": transition_id, "cell": [r, c]})
            board[r][c] = int(after)
        if row.get("kind") == "RESET":
            windows.append(_Window(int(row.get("life") or windows[-1].life + 1)))
        windows[-1].cuts.append(board_cut(board, node=transition_id, level=level))
        windows[-1].sources[transition_id] = {"source": "TRANSITION", "transition_id": transition_id}
    return windows, board, discontinuities


def _segments(steps: Sequence[ComponentObservation], sources: Mapping[int, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Consecutive identical sightings as one segment: a still object is one appearance seen many times."""
    segments: list[dict[str, Any]] = []
    for step in steps:
        last = segments[-1] if segments else None
        if last is not None and last["_key"] == (step.class_id, step.cells):
            last["last"], last["count"] = dict(sources[step.node_index]), last["count"] + 1
            continue
        segments.append({"_key": (step.class_id, step.cells), "first": dict(sources[step.node_index]),
                         "last": dict(sources[step.node_index]), "count": 1, "class_id": step.class_id,
                         "shape_hash": step.shape_hash, "anchor": list(step.anchor), "bbox": list(step.bbox),
                         "cell_count": step.cell_count})
    for segment in segments:
        del segment["_key"]
    return segments


def project_tracks(level: int, entry_board: Grid, entry: Mapping[str, Any],
                   rows: Sequence[Mapping[str, Any]], *, entry_life: int = 1) -> dict[str, Any]:
    """Observation tracks for one level: present and departed, scoped to level and life."""
    windows, final_board, discontinuities = _windows(level, entry_board, entry, rows, entry_life)
    last_node = windows[-1].cuts[-1].node_index
    tracks: list[dict[str, Any]] = []
    steps_by_track: dict[str, tuple[ComponentObservation, ...]] = {}
    first_cuts: list[dict[tuple[int, tuple[Cell, ...]], str]] = []
    for position, window in enumerate(windows):
        lines = re_join(weave_window(window.cuts), window.cuts)
        window_end = window.cuts[-1].node_index
        spawn: dict[tuple[int, tuple[Cell, ...]], str] = {}
        for line in sorted(lines, key=lambda item: (item.steps[0].node_index, item.steps[0].anchor, item.local_id)):
            first = line.steps[0]
            born_at_start = first.node_index == window.cuts[0].node_index
            token = ("E" if position == 0 else f"R{first.node_index}") if born_at_start else f"T{first.node_index}"
            track_id = (f"O-L{level}-P{window.life}-{token}-"
                        + hashlib.sha256(repr((first.class_id, first.cells)).encode()).hexdigest()[:12])
            last = line.steps[-1]
            track = {
                "track_id": track_id,
                "life": window.life,
                "segments": _segments(line.steps, window.sources),
                "present_now": last.node_index == last_node,
                "end": None if last.node_index == last_node else {
                    "last_seen": dict(window.sources[last.node_index]),
                    "reason": "LIFE_ENDED" if last.node_index == window_end else "DEPARTED",
                },
                "class_events": [
                    {"transition_id": edge.now.node_index, "verb": edge.verb, "witness": edge.witness}
                    for edge in line.edges
                    if edge.verb in CLASS_VERBS and edge.now is not None
                ],
                "band1": {"status": "UNSETTLED", "reason": "NOT_BUILT"},
                "g3_join": {"status": "NOT_APPLICABLE", "entity_id": None, "basis": None},
            }
            if born_at_start:
                spawn[(first.class_id, first.cells)] = track_id
                if position > 0:
                    track["possible_correspondence"] = sorted(
                        prior[(first.class_id, first.cells)] for prior in first_cuts
                        if (first.class_id, first.cells) in prior
                    )
            tracks.append(track)
            steps_by_track[track_id] = line.steps
        first_cuts.append(spawn)
    return {
        "tracks": tracks,
        "steps": steps_by_track,
        "final_board": final_board,
        "discontinuities": discontinuities,
        "reset_born": [t["track_id"] for t in tracks if "possible_correspondence" in t],
    }


def _payload_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _receipts(machine: Any, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The minimum index a certified role's references must resolve against, read from gate state only.

    - ``evidence``: every recorded transition of the level that carries a gate evidence id;
    - ``products``: each active gate product (gate, type, revision, payload hash);
    - ``witnesses``: each G3 witness, with the entity its member binds to and its evidence id.
    """
    evidence = {
        str(row["evidence_id"]): {"transition_id": int(row["transition_id"]), "gate_id": row.get("gate_id"),
                                  "probe_id": row.get("probe_id")}
        for row in rows if row.get("evidence_id")
    }
    products = {}
    for contract in machine.target_registry.ordered():
        product = machine.target_journal.active_product(contract.target_id)
        if product is not None:
            products[product.product_id] = {"gate_id": contract.target_id, "product_type": product.product_type,
                                            "revision": product.revision, "payload_sha256": _payload_sha256(product.payload)}
    adapter = (getattr(machine, "_adapters", None) or {}).get("G3-LEVERS")
    ledger = getattr(adapter, "entity_ledger", None)
    witnesses = {}
    accumulator = getattr(adapter, "evidence", None)
    for member_id, rows_ in sorted((getattr(accumulator, "_witnesses", None) or {}).items()):
        for witness in rows_:
            witnesses[witness.witness_id] = {
                "entity_id": None if ledger is None else ledger.member_to_entity.get(member_id),
                "member_id": member_id, "evidence_ref": witness.evidence_ref,
                "transition_id": int(witness.transition_id), "channel": witness.channel,
            }
    return {"evidence": evidence, "products": products, "witnesses": witnesses}


def _resolvable(refs: Iterable[Any], receipts: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """Split cited refs into those the receipt index resolves and those it cannot (kept, labelled)."""
    known = set(receipts["evidence"]) | set(receipts["products"]) | set(receipts["witnesses"])
    refs = [str(ref) for ref in refs if ref]
    return [ref for ref in refs if ref in known], [ref for ref in refs if ref not in known]


def _evidence_transitions(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {str(row["evidence_id"]): int(row["transition_id"]) for row in rows if row.get("evidence_id")}


def _g3_joins(machine: Any, steps: Mapping[str, tuple[ComponentObservation, ...]]) -> dict[str, dict[str, Any]]:
    """E-id → track, only on an exact one-to-one ``(time, integer, cells)`` key; ambiguity abstains."""
    adapter = (getattr(machine, "_adapters", None) or {}).get("G3-LEVERS")
    ledger = getattr(adapter, "entity_ledger", None)  # attribute read only; None before G3 (W2)
    if ledger is None:
        return {}
    seed_time = int(getattr(machine.counter, "observed_through_step", 0))
    entity_keys: dict[tuple[int, int, tuple[Cell, ...]], list[str]] = {}
    for entity_id, hypothesis in ledger.entities.items():
        first = hypothesis.sightings[0] if hypothesis.sightings else None
        if first is None or first.relation not in {"SEED", "BIRTH", "RESET_BIRTH"} or hypothesis.ambiguity_refs:
            continue
        time = seed_time if first.relation == "SEED" else int(first.transition_id)
        entity_keys.setdefault((time, int(first.integer), tuple(sorted(first.cells))), []).append(entity_id)
    track_keys: dict[tuple[int, int, tuple[Cell, ...]], list[str]] = {}
    for track_id, line in steps.items():
        for step in line:
            track_keys.setdefault((step.node_index, step.class_id, step.cells), []).append(track_id)
    joins: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for key, entities in entity_keys.items():
        tracks = track_keys.get(key) or []
        if len(entities) == 1 and len(tracks) == 1:
            basis = {"key": "TIME_INTEGER_CELLS", "transition_or_seed": key[0], "seed": key[0] == seed_time}
            joins.setdefault(tracks[0], []).append((entities[0], basis))
    result: dict[str, dict[str, Any]] = {}
    claimed: dict[str, int] = {}
    for track_id, rows in joins.items():
        for entity_id, _basis in rows:
            claimed[entity_id] = claimed.get(entity_id, 0) + 1
    for track_id, rows in joins.items():
        if len(rows) == 1 and claimed[rows[0][0]] == 1:
            result[rows[0][0]] = {"track_id": track_id, "basis": rows[0][1]}
    return result


def _gate_dispositions(machine: Any | None) -> list[dict[str, Any]]:
    if machine is None:
        return [{"gate_id": gate_id, "disposition": "NOT_STARTED"} for gate_id in GATE_ORDER]
    rows = []
    for contract in machine.target_registry.ordered():
        product = machine.target_journal.active_product(contract.target_id)
        if product is not None:
            rows.append({"gate_id": contract.target_id, "disposition": "CERTIFIED", "product_id": product.product_id,
                         "product_type": product.product_type, "revision": product.revision})
        elif contract.target_id == machine.gate_id:
            rows.append({"gate_id": contract.target_id, "disposition": "IN_PROGRESS"})
        else:
            rows.append({"gate_id": contract.target_id, "disposition": "NOT_REACHED"})
    return rows


def _identity(track_id: str | None, basis: Mapping[str, Any] | None) -> dict[str, Any]:
    if track_id is None:
        return {"status": "UNRESOLVED", "track_id": None, "basis": None}
    return {"status": "EXACT_ONE_TO_ONE", "track_id": track_id, "basis": dict(basis or {})}


def _unique_track(steps: Mapping[str, tuple[ComponentObservation, ...]], cells: Iterable[Cell],
                  at_nodes: Iterable[int] | None = None) -> str | None:
    wanted = tuple(sorted((int(r), int(c)) for r, c in cells))
    nodes = None if at_nodes is None else set(at_nodes)
    hits = {
        track_id for track_id, line in steps.items() for step in line
        if step.cells == wanted and (nodes is None or step.node_index in nodes)
    }
    return next(iter(hits)) if len(hits) == 1 else None


def _certified(machine: Any, steps: Mapping[str, tuple[ComponentObservation, ...]], rows: Sequence[Mapping[str, Any]],
               joins: Mapping[str, Mapping[str, Any]], receipts: Mapping[str, Any],
               ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Roles certified by gate products or G3 witnesses; terrain observations; identity gaps."""
    roles: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    journal = machine.target_journal
    ego_product = journal.active_product("G1-EGO")
    if ego_product is not None:
        law = ego_product.payload
        refs, unverified = _resolvable(list(law.get("evidence_refs") or ()) + [law.get("demonstration_ref")], receipts)
        role = {"role": "EGO", "gate_id": "G1-EGO", "product_id": ego_product.product_id, "mode": law.get("mode"),
                "evidence_refs": refs, "unverified_refs": unverified}
        if law.get("mode") == "POINTER_GOD_MODE":
            role.update(identity={"status": "NOT_APPLICABLE", "track_id": None, "basis": None},
                        subject="POINTER_NULL_LOCUS", binding_source="POINTER_EGO_HAS_NO_GRID_FOOTPRINT")
        else:
            # A shallow copy: the binding's nav-control memo (nav_control.py:266) lands on the copy,
            # so the census leaves the gate machine byte-identical.
            cells, source = copy.copy(machine.ego).embodied_ego_binding()
            track = None if source == "DUCK_DECLARED_SCOPE_FALLBACK" or not cells else _unique_track(steps, cells)
            role.update(identity=_identity(track, {"key": "EGO_BINDING_CELLS", "source": source} if track else None),
                        binding_source=source, subject="EMBODIED_FOOTPRINT")
            if track is None:
                gaps.append({"subject": "EGO", "archetype_question": "Which observed object is the embodied ego?",
                             "reason": "IDENTITY_UNRESOLVED", "source": source})
        roles.append(role)
    counter_product = journal.active_product("G2-COUNTER")
    mask = (counter_product.payload.get("mask_law") if counter_product is not None else None) or None
    if counter_product is not None and mask:
        evidence = _evidence_transitions(rows)
        witness_nodes = [evidence[ref] for ref in mask.get("witness_evidence_refs") or () if ref in evidence]
        track = _unique_track(steps, mask.get("cells") or (), at_nodes=witness_nodes)
        roles.append({
            "role": "COUNTER", "gate_id": "G2-COUNTER", "product_id": counter_product.product_id,
            "subject": "MASK", "mask_law_version_id": mask.get("law_version_id"),
            "mask_cell_count": len(mask.get("cells") or ()),
            **dict(zip(("evidence_refs", "unverified_refs"), _resolvable(
                list(mask.get("witness_evidence_refs") or ()) + [mask.get("demonstration_ref")], receipts))),
            "identity": _identity(track, {"key": "EXACT_MASK_FOOTPRINT_AT_WITNESS"} if track else None),
        })
        if track is None:
            gaps.append({"subject": "COUNTER", "archetype_question": "Which observed object, if any, is the counter?",
                         "reason": "IDENTITY_UNRESOLVED", "source": "mask footprint matches no single track at a witness"})
    adapter = (getattr(machine, "_adapters", None) or {}).get("G3-LEVERS")
    lifecycle = getattr(adapter, "lifecycle_journal", None)
    nulls: list[dict[str, Any]] = []
    terrain: list[dict[str, Any]] = []
    if lifecycle is not None:
        g3_product = journal.active_product("G3-LEVERS")
        accepted = set((g3_product.payload.get("lever_entities") or ()) if g3_product is not None else ())
        discoveries = {str(item.get("entity_id")): item for item in (adapter._lever_discoveries or {}).values()}
        for entity_id, item in sorted(lifecycle.entities.items()):
            join = joins.get(entity_id)
            if item.witness_refs:
                discovery = discoveries.get(entity_id) or {}
                evidence_refs, unverified = _resolvable(
                    [discovery.get("evidence_ref"), discovery.get("record_ref")], receipts)
                roles.append({
                    "role": "LEVER", "gate_id": "G3-LEVERS", "entity_id": entity_id,
                    "witness_refs": list(item.witness_refs),
                    "evidence_refs": evidence_refs, "unverified_refs": unverified,
                    "inventory_status": "ACCEPTED" if entity_id in accepted else "PENDING",
                    "identity": _identity(join and join["track_id"], join and join["basis"]),
                })
                if join is None:
                    gaps.append({"subject": entity_id, "archetype_question": "Which observed object is this lever?",
                                 "reason": "IDENTITY_UNRESOLVED", "source": "no exact one-to-one track join"})
            elif item.state == "NO_RESPONSE_YET":
                gaps.append({"subject": entity_id, "archetype_question": "Is this object a lever?",
                             "reason": "NOT_REACHED",
                             "source": "G3 NO_RESPONSE_YET: a scoped null is recorded; the row is not closed"})
            elif item.state == "G3-CLOSED":
                nulls.append({"entity_id": entity_id, "evidence_ref": item.events[-1].evidence_ref if item.events else None,
                              "scope": "OBSERVED_INTERACTION_IN_RECORDED_STATE", "inertness_claim_permitted": False,
                              "track_id": join["track_id"] if join else None})
        for entity_id, record in sorted((adapter._terrain_roles or {}).items()):
            join = joins.get(entity_id)
            terrain.append({"entity_id": entity_id, "label": record.get("role"), "interaction": record.get("interaction"),
                            "evidence_refs": list(record.get("evidence_refs") or ()), "scope": record.get("scope"),
                            "track_id": join["track_id"] if join else None})
        for entity_id, record in sorted((adapter._bounded_ambiguities or {}).items()):
            state = lifecycle.entities[entity_id].state if entity_id in lifecycle.entities else None
            if state not in {"AMBIGUOUS", "BUDGET_STOPPED", "PRESUMED_UNREACHABLE"}:
                continue
            gaps.append({"subject": entity_id, "archetype_question": "Is this object a lever?",
                         "reason": {"BUDGET_STOPPED": "BUDGET", "AMBIGUOUS": "INCONCLUSIVE"}.get(state, "NOT_REACHED"),
                         "source": f"G3 {state}: {record.get('disposition')}"})
    return {"roles": roles, "scoped_nulls": nulls}, terrain, gaps


def _action_gaps(machine: Any) -> list[dict[str, Any]]:
    product = machine.target_journal.active_product("G1-EGO")
    gaps = []
    for item in (product.payload.get("limitations") or ()) if product is not None else ():
        if "open obligation" in str(item):
            action = str(item).split(":", 1)[0].strip()
            gaps.append({"subject": action, "archetype_question": f"What does {action} do?",
                         "reason": "NOT_BUILT", "source": "G1 interface axiom explains ACTION6 only (WO-L1a)"})
    return gaps


def record_check(transition_index: Sequence[Mapping[str, Any]], executed: Sequence[str]) -> dict[str, Any]:
    """The gate record against what the harness executed: missing, extra, duplicated and renamed ids."""
    ids = [int(row["transition_id"]) for row in transition_index]
    duplicated = sorted({t for t in ids if ids.count(t) > 1})
    recorded = {int(row["transition_id"]): str((row.get("action") or {}).get("action") or "") for row in transition_index}
    expected = {index + 1: str(name) for index, name in enumerate(executed)}
    missing = sorted(set(expected) - set(recorded))
    extra = sorted(set(recorded) - set(expected))
    renamed = sorted(t for t in set(expected) & set(recorded) if recorded[t] and expected[t] and recorded[t] != expected[t])
    return {"ok": not (missing or extra or renamed or duplicated), "missing": missing, "extra": extra,
            "duplicated": duplicated, "renamed": renamed, "recorded": len(ids), "executed": len(expected)}


def _entry(machine: Any | None, level: int) -> dict[str, Any]:
    """The entry board's provenance: the first board the machine saw, or the board a level change left."""
    if machine is None:
        return {"source": "INITIAL_FRAME"}
    previous = [int(row["transition_id"]) for row in machine.transition_index if row.get("level") == level - 1]
    return {"source": "LEVEL_ENTRY", "after_transition": max(previous)} if previous else {"source": "INITIAL_FRAME"}


def compile_level(machine: Any | None, execution: ExecutionRecord | None = None, *, state: str = "OPEN",
                  level: int | None = None) -> dict[str, Any]:
    """The census of one level (or, with no machine, of the observed entry board), journal check PENDING.

    A FROZEN census is taken at a level boundary, inside ``_advance_level`` before ``freeze_level``. By then
    ``LifeRecord.tag`` has already moved ``machine.lives.level`` to the next level (``life_record.py``), while
    the board, rows and gate products still belong to the level that ended. So a frozen census must be
    given the boundary's ``level_before``; it never reads the level from the machine.

    No census here is checked against the harness's execution history: the gate machine never receives
    it. ``reconcile`` does that at finalization (Sol, 2026-10-11), and only it can mark a level ACCOUNTED.
    """
    if state == "FROZEN" and level is None:
        raise ValueError("a frozen census needs the boundary's level_before, explicitly")
    if machine is None:
        if execution is None:
            raise ValueError("a census without a gate machine needs the observed entry board")
        level, board, rows, life = execution.entry_level, execution.entry_board, [], 1
        valid_actions = list(execution.valid_actions)
    else:
        level = int(level if level is not None else machine.lives.level)
        board = tuple(tuple(row) for row in machine.ego._initial_grid)
        rows = level_rows(machine.transition_index, level)
        life = int(rows[0]["life"]) if rows else int(machine.lives.life)
        valid_actions = [item.action for item in machine.ego.affordances]
    entry = _entry(machine, level)
    projection = project_tracks(level, board, entry, rows, entry_life=life)
    gaps: list[dict[str, Any]] = [
        {"subject": f"LEVEL-{level}", "archetype_question": question, "reason": reason, "source": source,
         "chapter": chapter}
        for chapter, question, reason, source in LEVEL_GAPS
    ]
    certified: dict[str, Any] = {"roles": [], "scoped_nulls": []}
    terrain: list[dict[str, Any]] = []
    receipts: dict[str, Any] = {"evidence": {}, "products": {}, "witnesses": {}}
    if machine is not None:
        joins = _g3_joins(machine, projection["steps"])
        for entity_id, join in joins.items():
            track = next(t for t in projection["tracks"] if t["track_id"] == join["track_id"])
            track["g3_join"] = {"status": "EXACT_ONE_TO_ONE", "entity_id": entity_id, "basis": join["basis"]}
        receipts = _receipts(machine, rows)
        certified, terrain, identity_gaps = _certified(machine, projection["steps"], rows, joins, receipts)
        gaps.extend(identity_gaps)
        gaps.extend(_action_gaps(machine))
    dispositions = _gate_dispositions(machine)
    certified_ids = {d["gate_id"] for d in dispositions if d["disposition"] == "CERTIFIED"}
    foundation_open = not {"G1-EGO", "G2-COUNTER"} <= certified_ids
    role_tracks = {role["identity"]["track_id"] for role in certified["roles"] if role["identity"].get("track_id")}
    for track in projection["tracks"]:
        if track["track_id"] not in role_tracks:
            gaps.append({"subject": track["track_id"], "archetype_question": "Which roles does this object hold?",
                         "reason": "FOUNDATION_UNRESOLVED" if foundation_open else "NOT_REACHED",
                         "source": "no certified role names this track"})
    for track_id in projection["reset_born"]:
        gaps.append({"subject": track_id, "archetype_question": "Is this the same object as one seen in an earlier life?",
                     "reason": "IDENTITY_UNRESOLVED", "source": "lives are not joined without continuity evidence"})
    missing = ["JOURNAL_CHECK_PENDING"]
    if projection["discontinuities"]:
        missing.append("BOARD_DISCONTINUITY")
        gaps.append({"subject": f"LEVEL-{level}", "archetype_question": "Do the recorded changes rebuild every board?",
                     "reason": "RECORD_MISMATCH", "source": "a recorded before-value disagrees with the replayed board",
                     "transitions": sorted({d["transition_id"] for d in projection["discontinuities"]})})
    return {
        "level": level,
        "state": state,
        "entry": {**entry, "board_sha256": hashlib.sha256(repr([list(r) for r in board]).encode()).hexdigest(),
                  "valid_actions": valid_actions},
        "record": {"transition_ids": [int(row["transition_id"]) for row in rows], "journal_check": {"status": "PENDING"}},
        "observation": {"tracks": projection["tracks"], "terrain": terrain},
        "certified": {"gates": dispositions, **certified},
        "receipts": receipts,
        "gaps": gaps,
        "accounting": {"status": "NOT_ACCOUNTED", "missing": missing},
    }


def freeze_level_census(machine: Any, *, level_before: int) -> dict[str, Any]:
    """H1: the ended level's census from gate state alone, its journal check PENDING (never ACCOUNTED)."""
    return compile_level(machine, None, state="FROZEN", level=level_before)


def freeze_census_or_failure(machine: Any, outcome: Mapping[str, Any]) -> dict[str, Any]:
    """What H1 appends: the frozen census, or a recorded failure. A census error never stops a level advance.

    ``LifeRecord.tag`` has already moved ``machine.lives.level`` on, so the level is the boundary's
    ``level_before``, read from the outcome that ended it.
    """
    boundary = outcome.get("boundary_event")
    level_before = boundary.get("level_before") if isinstance(boundary, Mapping) else None
    try:
        return freeze_level_census(machine, level_before=int(level_before))
    except Exception as exc:  # noqa: BLE001 - recorded, never raised into the gate machine
        return {"level": level_before, "census_failed": f"{type(exc).__name__}: {exc}"}


_CHECK_KEYS = ("missing", "extra", "duplicated", "renamed")


def assign_mismatches(check: Mapping[str, Any], transition_index: Sequence[Mapping[str, Any]],
                      levels: Sequence[int]) -> dict[int, dict[str, list[int]]]:
    """Each mismatched id to the level that owns it (interface v4 §0a step 2).

    A recorded id belongs to its row's level. A missing id (executed, never recorded) belongs to the level
    whose recorded span contains it, else to the next level's span, else to the last level. A level the
    census does not hold (a failed H1) gives its ids to the last level.
    """
    present = sorted(int(level) for level in levels)
    row_level = {int(row["transition_id"]): int(row.get("level") or present[-1]) for row in transition_index}
    spans: dict[int, tuple[int, int]] = {}
    for tid, level in row_level.items():
        low, high = spans.get(level, (tid, tid))
        spans[level] = (min(low, tid), max(high, tid))

    def owner(tid: int, recorded: bool) -> int:
        if recorded and tid in row_level:
            level = row_level[tid]
        else:
            inside = [level for level, (low, high) in spans.items() if low <= tid <= high]
            later = sorted(level for level, (low, _high) in spans.items() if low > tid)
            level = inside[0] if inside else later[0] if later else present[-1]
        return level if level in present else present[-1]

    result = {level: {key: [] for key in _CHECK_KEYS} for level in present}
    for key in _CHECK_KEYS:
        for tid in check.get(key) or ():
            result[owner(int(tid), key != "missing")][key].append(int(tid))
    return result


def _apply_check(level: Mapping[str, Any], ids: Mapping[str, list[int]], totals: Mapping[str, Any]) -> dict[str, Any]:
    level = copy.deepcopy(dict(level))
    if level["record"]["journal_check"].get("status") != "PENDING":
        raise ValueError(f"level {level['level']} was already reconciled")
    ok = not any(ids[key] for key in _CHECK_KEYS)
    level["record"]["journal_check"] = {"status": "CHECKED", "ok": ok, **{k: list(ids[k]) for k in _CHECK_KEYS},
                                        "recorded": totals["recorded"], "executed": totals["executed"]}
    missing = [item for item in level["accounting"]["missing"] if item != "JOURNAL_CHECK_PENDING"]
    if not ok:
        level["gaps"].append({"subject": f"LEVEL-{level['level']}",
                              "archetype_question": "Does the gate record match what was executed?",
                              "reason": "RECORD_MISMATCH", "source": "record_check",
                              **{k: list(ids[k]) for k in _CHECK_KEYS}})
        missing.append("RECORD_MISMATCH")
        unmatched = set(ids["extra"]) | set(ids["renamed"]) | set(ids["duplicated"])
        receipts, kept = level["receipts"], []
        for role in level["certified"]["roles"]:
            cited = {receipts["evidence"][ref]["transition_id"] for ref in role.get("evidence_refs") or ()
                     if ref in receipts["evidence"]}
            cited |= {receipts["witnesses"][ref]["transition_id"] for ref in role.get("witness_refs") or ()
                      if ref in receipts["witnesses"]}
            if cited & unmatched:
                level["gaps"].append({"subject": role.get("entity_id") or role["role"],
                                      "archetype_question": f"Is the {role['role']} claim grounded?",
                                      "reason": "RECORD_MISMATCH", "source": "its evidence lies on an unmatched transition",
                                      "transitions": sorted(cited & unmatched)})
            else:
                kept.append(role)
        level["certified"]["roles"] = kept
    level["accounting"] = {"status": "NOT_ACCOUNTED" if missing else "ACCOUNTED", "missing": missing}
    return level


def reconcile(levels: Sequence[Mapping[str, Any]], machine: Any | None, execution: ExecutionRecord) -> list[dict[str, Any]]:
    """H2: check the whole gate record against the whole execution history, once, and settle every level."""
    rows = list(machine.transition_index) if machine is not None else []
    check = record_check(rows, execution.executed)
    owned = assign_mismatches(check, rows, [int(level["level"]) for level in levels])
    totals = {"recorded": check["recorded"], "executed": check["executed"]}
    return [_apply_check(level, owned[int(level["level"])], totals) for level in levels]


def compile_world_model(machine: Any | None, execution: ExecutionRecord, *, game_id: str, run_stem: str,
                        persist_reason: str, frozen_levels: Sequence[Mapping[str, Any]] = (),
                        reconcile_journal: bool = True) -> dict[str, Any]:
    """The unsealed v2 payload: frozen levels plus the current open level, in one artifact.

    With ``reconcile_journal`` (H2, final) every level is checked against ``execution``; without it (the
    interim write after H1) every level keeps its PENDING check and nothing is ACCOUNTED.
    """
    failures = [dict(level) for level in frozen_levels if "census_failed" in level]
    frozen = [dict(level) for level in frozen_levels if "census_failed" not in level]
    advance_incomplete = machine is not None and len(getattr(machine, "level_censuses", ())) > len(machine.levels)
    levels = list(frozen)
    if not advance_incomplete:  # an advance that froze its census but never rebuilt leaves no open level
        current = compile_level(machine, execution)
        levels = [level for level in frozen if level.get("level") != current["level"]] + [current]
    levels = sorted(levels, key=lambda item: int(item["level"]))
    if reconcile_journal:
        levels = reconcile(levels, machine, execution)
    return {
        "game_id": game_id,
        "run_stem": run_stem,
        "manifest": {
            "status": "ACTIVE" if execution.executed else "OBSERVED_NEVER_ACTED",
            "persist_reason": persist_reason,
            "actions_executed": len(execution.executed),
            "gate_machine": machine is not None,
            "journal_check": "RECONCILED" if reconcile_journal else "PENDING",
            "census_failures": failures,
        },
        "levels": levels,
    }


__all__ = ["ExecutionRecord", "assign_mismatches", "board_cut", "compile_level", "compile_world_model",
           "freeze_census_or_failure", "freeze_level_census", "level_rows", "project_tracks", "reconcile",
           "record_check"]
