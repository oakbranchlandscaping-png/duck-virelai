"""Passive Ring 8 adapter for V4's flip-book ontology and golden weave.

The visible substrate is a sequence of complete grid cuts. A component at one
cut is a sighting, not an object identity. The golden site -> class -> residual
cascade threads sightings into retrospective worldlines, after which the V4
overlap, occlusion, and exact-return passes may conservatively rejoin threads.

This module infers no semantic roles and exposes nothing to Duck. It preserves
complete sightings and separates mechanically-checkable fidelity from
correspondence correctness, which requires an external answer key.
"""
from __future__ import annotations

import hashlib
import json
import queue
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CONTINUITY_SCHEMA = "virelai-golden-weave-v1"
CONTINUITY_SUMMARY_SCHEMA = "virelai-golden-weave-summary-v1"
CONTINUITY_FAULT_SCHEMA = "virelai-golden-weave-fault-v1"

Cell = tuple[int, int]
CONTINUE_VERBS = frozenset({"STILL", "RECOLOR", "MOVE", "GROW", "SHRINK"})
THETA_DOM = 0.80
THETA_MUT = 0.80


def _nearest_rank(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, (percentile * len(ordered) + 99) // 100 - 1))
    return ordered[index]


def _append_jsonl(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
        handle.write("\n")


def _normal_shape(cells: tuple[Cell, ...]) -> tuple[Cell, ...]:
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _shape_hash(class_id: int, cells: tuple[Cell, ...]) -> str:
    return hashlib.sha1(repr((class_id, _normal_shape(cells))).encode()).hexdigest()[:16]


def _cell_runs(cells: tuple[Cell, ...]) -> list[tuple[int, int, int]]:
    """Lossless row-run encoding: (row, first_col, last_col), inclusive."""
    runs: list[tuple[int, int, int]] = []
    by_row: dict[int, list[int]] = {}
    for row, col in cells:
        by_row.setdefault(row, []).append(col)
    for row in sorted(by_row):
        columns = sorted(by_row[row])
        start = previous = columns[0]
        for col in columns[1:]:
            if col != previous + 1:
                runs.append((row, start, previous))
                start = col
            previous = col
        runs.append((row, start, previous))
    return runs


@dataclass(frozen=True)
class ComponentObservation:
    """One exact per-page sighting. ``component_id`` is an address, not identity."""

    node_index: int
    level: int
    component_id: int
    class_id: int
    cells: tuple[Cell, ...]
    anchor: Cell
    bbox: tuple[int, int, int, int]
    cell_count: int
    shape_hash: str

    @property
    def fingerprint(self) -> tuple[int, tuple[Cell, ...]]:
        return self.class_id, self.cells

    def reference(self, *, include_cells: bool = True) -> dict[str, Any]:
        out = {
            "node_index": self.node_index,
            "level": self.level,
            "component_id": self.component_id,
            "class_id": self.class_id,
            "anchor": self.anchor,
            "bbox": self.bbox,
            "cell_count": self.cell_count,
            "shape_hash": self.shape_hash,
        }
        if include_cells:
            out["cells"] = self.cells
        return out


@dataclass(frozen=True)
class NodeCut:
    node_index: int
    level: int
    geometry: tuple[int, int]
    visible_hash: str
    full_reset: bool
    action_id: int | None
    acted_cell: Cell | None
    regions: tuple[ComponentObservation, ...]


def cut_visible_frame(record: Any, *, level: int) -> NodeCut:
    """Partition the final visible layer into 4-connected equal-class sightings."""
    if not record.layers:
        return NodeCut(int(record.node_index), int(level), (0, 0), "",
                       bool(getattr(record, "full_reset", False)),
                       getattr(record, "action_id", None), getattr(record, "acted_cell", None), ())
    descriptor = record.layers[-1]
    raw = record.layer_bytes(-1)
    rows, cols = int(descriptor.rows), int(descriptor.cols)
    seen: set[Cell] = set()
    components: list[tuple[int, tuple[Cell, ...]]] = []
    for start_row in range(rows):
        for start_col in range(cols):
            if (start_row, start_col) in seen:
                continue
            class_id = int(raw[start_row * cols + start_col])
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[Cell] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    other = row + drow, col + dcol
                    if not (0 <= other[0] < rows and 0 <= other[1] < cols):
                        continue
                    if other in seen or int(raw[other[0] * cols + other[1]]) != class_id:
                        continue
                    seen.add(other)
                    stack.append(other)
            components.append((class_id, tuple(sorted(cells))))
    # Address sightings in stable visual reading order. The weave independently
    # applies V4's size/class/anchor traversal; addressing must not inherit that
    # inference-oriented ordering or frozen external keys would renumber.
    components.sort(key=lambda item: item[1][0])
    regions: list[ComponentObservation] = []
    for component_id, (class_id, cells) in enumerate(components):
        row_values = [cell[0] for cell in cells]
        col_values = [cell[1] for cell in cells]
        regions.append(ComponentObservation(
            node_index=int(record.node_index), level=int(level), component_id=component_id,
            class_id=class_id, cells=cells,
            anchor=(min(row_values), min(col_values)),
            bbox=(min(row_values), min(col_values), max(row_values), max(col_values)),
            cell_count=len(cells), shape_hash=_shape_hash(class_id, cells),
        ))
    acted_cell = getattr(record, "acted_cell", None)
    return NodeCut(int(record.node_index), int(level), (rows, cols),
                   hashlib.sha256(raw).hexdigest(), bool(getattr(record, "full_reset", False)),
                   getattr(record, "action_id", None),
                   tuple(acted_cell) if acted_cell is not None else None, tuple(regions))


def segment_visible_components(record: Any, *, level: int) -> tuple[ComponentObservation, ...]:
    """Compatibility view over the canonical complete cut."""
    return cut_visible_frame(record, level=level).regions


def _translation(before: ComponentObservation, after: ComponentObservation) -> tuple[int, int] | None:
    if before.cell_count != after.cell_count or _normal_shape(before.cells) != _normal_shape(after.cells):
        return None
    delta = after.anchor[0] - before.anchor[0], after.anchor[1] - before.anchor[1]
    return delta if delta != (0, 0) else None


def _class_verb(before: ComponentObservation, after: ComponentObservation) -> str | None:
    before_cells, after_cells = set(before.cells), set(after.cells)
    if after_cells > before_cells:
        return "GROW"
    if after_cells < before_cells:
        return "SHRINK"
    return "MOVE" if _translation(before, after) is not None else None


def _cut_values(cut: NodeCut) -> dict[Cell, int]:
    """The exact integer at every site, reconstructed from a pristine cut."""
    return {cell: region.class_id for region in cut.regions for cell in region.cells}


def _rewrite_groups(
    cells: set[Cell],
    before_values: dict[Cell, int],
    after_values: dict[Cell, int],
) -> list[dict[str, Any]]:
    """Losslessly group sites by their literal integer rewrite."""
    grouped: dict[tuple[int, int], list[Cell]] = {}
    for cell in sorted(cells):
        grouped.setdefault((before_values[cell], after_values[cell]), []).append(cell)
    return [
        {
            "before_class": before_class,
            "after_class": after_class,
            "outcome": "HELD" if before_class == after_class else "CHANGED",
            "cell_count": len(members),
            "cell_runs": _cell_runs(tuple(members)),
        }
        for (before_class, after_class), members in sorted(grouped.items())
    ]


def pixel_arithmetic(left: NodeCut, right: NodeCut) -> dict[str, Any]:
    """Complete site -> (before, after, action) record for one observed edge."""
    base = {
        "schema": "virelai-pixel-arithmetic-v1",
        "from_node": left.node_index,
        "to_node": right.node_index,
        "level_before": left.level,
        "level_after": right.level,
        "action_id": right.action_id,
        "acted_cell": right.acted_cell,
        "before_shape": left.geometry,
        "after_shape": right.geometry,
        "geometry_changed": left.geometry != right.geometry,
    }
    if left.geometry != right.geometry:
        return {
            **base,
            "coverage_status": "UNDEFINED_ACROSS_GEOMETRY_CHANGE",
            "site_count": None,
            "held_cells": None,
            "changed_cells": None,
            "transition_groups": [],
            "signed_class_delta": [],
            "conservation_closes": None,
        }
    before_values, after_values = _cut_values(left), _cut_values(right)
    sites = set(before_values)
    groups = _rewrite_groups(sites, before_values, after_values)
    signed: dict[int, int] = {}
    for group in groups:
        count = int(group["cell_count"])
        before_class = int(group["before_class"])
        after_class = int(group["after_class"])
        if before_class != after_class:
            signed[before_class] = signed.get(before_class, 0) - count
            signed[after_class] = signed.get(after_class, 0) + count
    signed_delta = [[class_id, delta] for class_id, delta in sorted(signed.items()) if delta]
    held = sum(int(group["cell_count"]) for group in groups if group["outcome"] == "HELD")
    changed = len(sites) - held
    return {
        **base,
        "coverage_status": "TOTAL",
        "site_count": len(sites),
        "held_cells": held,
        "changed_cells": changed,
        "transition_groups": groups,
        "signed_class_delta": signed_delta,
        "conservation_closes": sum(delta for _, delta in signed_delta) == 0,
    }


def arithmetic_signature(
    before: ComponentObservation | None,
    after: ComponentObservation | None,
    left: NodeCut,
    right: NodeCut,
) -> dict[str, Any] | None:
    """Pair-relative footprint evidence, with no empty-cell fiction.

    The four groups describe membership in a proposed object's two endpoint
    footprints. Every member is joined to the literal integer at that site in
    both frames. ``prior_footprint_only`` never means the site became empty.
    """
    if before is None or after is None or left.geometry != right.geometry:
        return None
    before_values, after_values = _cut_values(left), _cut_values(right)
    before_cells, after_cells = set(before.cells), set(after.cells)
    shared = before_cells & after_cells
    retained_same = {cell for cell in shared if before_values[cell] == after_values[cell]}
    retained_rewritten = shared - retained_same
    translation = _translation(before, after)
    if before_cells == after_cells:
        form = "STILL" if before.class_id == after.class_id else "RECOLOR"
    elif translation is not None:
        form = "MOVE"
    elif before_cells < after_cells:
        form = "GROW"
    elif after_cells < before_cells:
        form = "SHRINK"
    else:
        form = "DEFORM"
    groups = {
        "retained_same_value": _rewrite_groups(
            retained_same, before_values, after_values
        ),
        "retained_rewritten": _rewrite_groups(
            retained_rewritten, before_values, after_values
        ),
        "prior_footprint_only": _rewrite_groups(
            before_cells - after_cells, before_values, after_values
        ),
        "later_footprint_only": _rewrite_groups(
            after_cells - before_cells, before_values, after_values
        ),
    }
    return {
        "schema": "virelai-footprint-arithmetic-v1",
        "from_node": before.node_index,
        "to_node": after.node_index,
        "adjacent_frames": after.node_index == before.node_index + 1,
        "lexicon_form": form,
        "recolor": before.class_id != after.class_id,
        "translation": translation,
        "before_cell_count": before.cell_count,
        "after_cell_count": after.cell_count,
        "membership_groups": groups,
        "membership_sites": len(before_cells | after_cells),
        "note": (
            "Footprint membership is object-relative; every listed site still "
            "contains the exact before_class and after_class integer."
        ),
    }


def _edge_artifact(edge: "_Edge", left: NodeCut, right: NodeCut, *, window_id: int) -> dict[str, Any]:
    signature = arithmetic_signature(edge.prev, edge.now, left, right)
    arithmetic_form = signature["lexicon_form"] if signature else None
    return {
        "window_id": window_id,
        "level": left.level,
        "from_node": left.node_index,
        "to_node": right.node_index,
        "verb": edge.verb,
        "anchor": edge.anchor,
        "delta": edge.delta,
        "witness": edge.witness,
        "before": edge.prev.reference(include_cells=False) if edge.prev else None,
        "after": edge.now.reference(include_cells=False) if edge.now else None,
        "related_branch_sightings": [
            item.reference(include_cells=False) for item in edge.related
        ],
        "arithmetic_form": arithmetic_form,
        "form_agrees": None if arithmetic_form is None else edge.verb == arithmetic_form,
        "arithmetic_signature": signature,
    }


@dataclass(frozen=True)
class ContinuityStitch:
    level: int
    track_id: int
    from_node: int
    from_component: int
    to_node: int
    to_component: int
    verb: str
    anchor: str
    delta: Any
    witnesses: tuple[str, ...]


@dataclass(frozen=True)
class _Edge:
    prev: ComponentObservation | None
    now: ComponentObservation | None
    verb: str
    anchor: str
    delta: Any = None
    witness: str = "golden_cascade"
    related: tuple[ComponentObservation, ...] = ()


def weave_edge(previous: tuple[ComponentObservation, ...], current: tuple[ComponentObservation, ...]) -> list[_Edge]:
    """V4's golden SITE -> CLASS -> residual correspondence cascade."""
    prevs = sorted(previous, key=lambda item: (item.cell_count, item.class_id, item.anchor))
    nows = sorted(current, key=lambda item: (item.cell_count, item.class_id, item.anchor))
    consumed: set[int] = set()
    edges: list[_Edge] = []
    by_cells: dict[tuple[Cell, ...], int] = {}
    for index, region in enumerate(nows):
        by_cells.setdefault(region.cells, index)
    unmatched: list[ComponentObservation] = []
    for before in prevs:
        index = by_cells.get(before.cells)
        if index is not None and index not in consumed:
            after = nows[index]
            verb = "STILL" if before.class_id == after.class_id else "RECOLOR"
            edges.append(_Edge(before, after, verb, "SITE", None if verb == "STILL" else
                               (before.class_id, after.class_id)))
            consumed.add(index)
        else:
            unmatched.append(before)
    by_class: dict[int, list[int]] = {}
    for index, region in enumerate(nows):
        by_class.setdefault(region.class_id, []).append(index)
    for before in unmatched:
        pool = [index for index in by_class.get(before.class_id, ()) if index not in consumed]
        licensed = [(index, _class_verb(before, nows[index])) for index in pool]
        licensed = [(index, verb) for index, verb in licensed if verb is not None]
        if len(licensed) == 1:
            index, verb = licensed[0]
            after = nows[index]
            consumed.add(index)
            delta = _translation(before, after) if verb == "MOVE" else after.cell_count - before.cell_count
            edges.append(_Edge(before, after, verb, "CLASS", delta))
        elif len(licensed) >= 2:
            edges.append(_Edge(before, None, "AMBIGUOUS", "NONE"))
        else:
            edges.append(_Edge(before, None, "DEFORM" if pool else "DEATH", "NONE"))
    for index, after in enumerate(nows):
        if index not in consumed:
            edges.append(_Edge(None, after, "BIRTH", "NONE"))
    return edges


def weave_edge_with_partition_fence(
    previous: tuple[ComponentObservation, ...],
    current: tuple[ComponentObservation, ...],
) -> list[_Edge]:
    """V4 cascade plus the previously built exact SPLIT/MERGE abstention fence.

    This is deliberately a separate function: ``weave_edge`` remains the
    unmodified golden verdict for comparison.  The extension uses set equality,
    not distance or a tuned score, and turns a false 1->1 identity into an
    explicit branch residual.
    """
    split_members: dict[ComponentObservation, list[ComponentObservation]] = {}
    for before in previous:
        before_cells = set(before.cells)
        pieces = [after for after in current if set(after.cells) < before_cells]
        if len(pieces) < 2 or set().union(*(set(piece.cells) for piece in pieces)) != before_cells:
            continue
        same_class = [piece for piece in pieces if piece.class_id == before.class_id]
        anchored_remainder = (len(same_class) == 1 and before.anchor in set(same_class[0].cells))
        if not anchored_remainder:
            split_members[before] = pieces
    merge_members: dict[ComponentObservation, list[ComponentObservation]] = {}
    for after in current:
        after_cells = set(after.cells)
        pieces = [before for before in previous if set(before.cells) < after_cells]
        if len(pieces) >= 2 and set().union(*(set(piece.cells) for piece in pieces)) == after_cells:
            merge_members[after] = pieces
    blocked_before = set(split_members)
    blocked_after = {piece for pieces in split_members.values() for piece in pieces}
    blocked_after.update(merge_members)
    for pieces in merge_members.values():
        blocked_before.update(pieces)
    ordinary = weave_edge(
        tuple(item for item in previous if item not in blocked_before),
        tuple(item for item in current if item not in blocked_after),
    )
    branch_edges = [
        _Edge(before, None, "SPLIT", "NONE", witness="exact_partition_fence",
              related=tuple(split_members[before]))
        for before in sorted(blocked_before, key=lambda item: (item.cell_count, item.class_id, item.anchor))
        if before in split_members
    ]
    branch_edges.extend(
        _Edge(before, None, "MERGE", "NONE", witness="exact_partition_fence",
              related=tuple(after for after, pieces in merge_members.items() if before in pieces))
        for before in sorted(blocked_before, key=lambda item: (item.cell_count, item.class_id, item.anchor))
        if before not in split_members
    )
    branch_edges.extend(
        _Edge(None, after, "BIRTH", "NONE", witness="exact_partition_fence",
              related=tuple(sorted(
                  [before for before, pieces in split_members.items() if after in pieces]
                  + list(merge_members.get(after, ())),
                  key=lambda item: (item.cell_count, item.class_id, item.anchor),
              )))
        for after in sorted(blocked_after, key=lambda item: (item.cell_count, item.class_id, item.anchor))
    )
    return ordinary + branch_edges


@dataclass(frozen=True)
class _Worldline:
    local_id: int
    steps: tuple[ComponentObservation, ...]
    edges: tuple[_Edge, ...]
    rejoin_witnesses: tuple[dict[str, Any], ...] = ()


def weave_window(cuts: list[NodeCut]) -> list[_Worldline]:
    """Build the INTERIM_O9 anchor-first worldlines.

    The exact-partition fence is deliberately excluded here.  It remains a
    separately persisted experimental hypothesis because a pixel partition is
    not sufficient evidence that one semantic object split or several merged.
    """
    if not cuts:
        return []
    builders: list[dict[str, Any]] = []
    active: dict[ComponentObservation, dict[str, Any]] = {}
    for region in sorted(cuts[0].regions, key=lambda item: (item.cell_count, item.class_id, item.anchor)):
        builder = {"steps": [region], "edges": []}
        builders.append(builder)
        active[region] = builder
    for before_cut, after_cut in zip(cuts, cuts[1:]):
        next_active: dict[ComponentObservation, dict[str, Any]] = {}
        for edge in weave_edge(before_cut.regions, after_cut.regions):
            if edge.verb in CONTINUE_VERBS:
                builder = active.get(edge.prev)
                if builder is None:
                    builder = {"steps": [edge.prev], "edges": []}
                    builders.append(builder)
                builder["steps"].append(edge.now)
                builder["edges"].append(edge)
                next_active[edge.now] = builder
            elif edge.verb == "BIRTH":
                builder = {"steps": [edge.now], "edges": []}
                builders.append(builder)
                next_active[edge.now] = builder
        active = next_active
    builders.sort(key=lambda item: (item["steps"][0].node_index, item["steps"][0].cell_count,
                                    item["steps"][0].class_id, item["steps"][0].anchor))
    return [_Worldline(index + 1, tuple(item["steps"]), tuple(item["edges"]))
            for index, item in enumerate(builders)]


def _overlap(left: tuple[Cell, ...], right: tuple[Cell, ...]) -> tuple[float, float]:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0, 0.0
    intersection = len(a & b)
    return intersection / min(len(a), len(b)), intersection / max(len(a), len(b))


def _merge(left: _Worldline, right: _Worldline, witness: dict[str, Any]) -> _Worldline:
    bridge = _Edge(left.steps[-1], right.steps[0], "DEFORM", "NONE", witness=witness["kind"])
    return _Worldline(left.local_id, left.steps + right.steps,
                      left.edges + (bridge,) + right.edges,
                      left.rejoin_witnesses + (witness,) + right.rejoin_witnesses)


def re_join(worldlines: list[_Worldline], cuts: list[NodeCut]) -> list[_Worldline]:
    """Faithful V4 ordering: overlap, witnessed occlusion, exact return."""
    result = list(worldlines)
    window_start = min((line.steps[0].node_index for line in result), default=0)
    changed = True
    while changed:
        changed = False
        for line in sorted(result, key=lambda item: (item.steps[-1].node_index, item.local_id)):
            last = line.steps[-1]
            candidates = []
            for birth in result:
                if birth is line or birth.steps[0].node_index != last.node_index + 1:
                    continue
                if birth.steps[0].node_index <= window_start or birth.steps[0].class_id != last.class_id:
                    continue
                dominant, mutual = _overlap(last.cells, birth.steps[0].cells)
                if dominant >= THETA_DOM and mutual >= THETA_MUT:
                    candidates.append((birth, dominant, mutual))
            if len(candidates) == 1:
                birth, dominant, mutual = candidates[0]
                merged = _merge(line, birth, {"kind": "dominant_mutual_overlap",
                    "from_node": last.node_index, "to_node": birth.steps[0].node_index,
                    "dominant": dominant, "mutual": mutual})
                result = [merged if item is line else item for item in result if item is not birth]
                changed = True
                break
    cut_by_node = {cut.node_index: cut for cut in cuts}
    order = [cut.node_index for cut in cuts]
    changed = True
    while changed:
        changed = False
        for line in sorted(result, key=lambda item: (item.steps[-1].node_index, item.local_id)):
            last = line.steps[-1]
            if last.node_index not in order:
                continue
            start = order.index(last.node_index)
            candidates = []
            for birth in sorted(result, key=lambda item: (item.steps[0].node_index, item.local_id)):
                first = birth.steps[0]
                if birth is line or first.node_index <= last.node_index or first.node_index not in order:
                    continue
                if first.fingerprint != last.fingerprint:
                    continue
                interior = order[start + 1:order.index(first.node_index)]
                if not interior:
                    continue
                covering = []
                for node in interior:
                    covers = [region for region in cut_by_node[node].regions if set(last.cells) < set(region.cells)]
                    if not covers:
                        break
                    cover = min(covers, key=lambda item: (item.cell_count, item.class_id, item.anchor))
                    covering.append({"node": node, "component_id": cover.component_id})
                else:
                    candidates.append((birth, covering))
            if candidates:
                birth, covering = candidates[0]
                merged = _merge(line, birth, {"kind": "occlusion", "from_node": last.node_index,
                    "to_node": birth.steps[0].node_index, "covering": covering})
                result = [merged if item is line else item for item in result if item is not birth]
                changed = True
                break
    changed = True
    while changed:
        changed = False
        for line in sorted(result, key=lambda item: (item.steps[-1].node_index, item.local_id)):
            last = line.steps[-1]
            candidates = [birth for birth in result if birth is not line
                          and birth.steps[0].node_index > last.node_index
                          and birth.steps[0].fingerprint == last.fingerprint]
            if not candidates:
                continue
            birth = min(candidates, key=lambda item: (item.steps[0].node_index, item.local_id))
            merged = _merge(line, birth, {"kind": "exact_return", "from_node": last.node_index,
                                         "to_node": birth.steps[0].node_index})
            result = [merged if item is line else item for item in result if item is not birth]
            changed = True
            break
    return result


@dataclass
class _Window:
    window_id: int
    level: int
    geometry: tuple[int, int]
    cuts: list[NodeCut] = field(default_factory=list)
    boundary_reason: str = "RUN_CLOSED"


class ContinuityCompiler:
    """Background cut builder plus retrospective golden-weave compiler."""
    _STOP = object()

    def __init__(self, *, game_id: str, artifact_dir: Path | None) -> None:
        self.game_id = str(game_id)
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else None
        self._faults_path = self.artifact_dir / "continuity_faults.jsonl" if self.artifact_dir else None
        self._queue: queue.Queue[Any] = queue.Queue()
        self._lock = threading.RLock()
        self._windows: list[_Window] = []
        self._compiled: list[dict[str, Any]] = []
        self._edge_records: list[dict[str, Any]] = []
        self._golden_edge_records: list[dict[str, Any]] = []
        self._experimental_edge_records: list[dict[str, Any]] = []
        self._pixel_records: list[dict[str, Any]] = []
        self._acted_on_records: list[dict[str, Any]] = []
        self._fidelity: dict[str, Any] = {}
        self._window_count = 0
        self._edge_count = 0
        self._ambiguous_count = 0
        self._acted_on_count = 0
        self._acted_on_defects = 0
        self._dirty = False
        self._submitted_through_node = -1
        self._cut_through_node = -1
        self._weave_compiled_through_node = -1
        self._cut_timings_ms: list[float] = []
        self._weave_timings_ms: list[float] = []
        self._faults: list[dict[str, Any]] = []
        self._closed = False
        self._new_window_after_life = False
        self._worker = threading.Thread(target=self._worker_loop,
                                        name=f"virelai-weave-{game_id}", daemon=True)
        self._worker.start()

    def submit(self, record: Any, *, level: int, life_ended: bool = False) -> None:
        with self._lock:
            if self._closed:
                return
            self._submitted_through_node = max(self._submitted_through_node, int(record.node_index))
        self._queue.put_nowait((record, int(level), bool(life_ended)))

    def _fault(self, exc: BaseException, node_index: int | None) -> None:
        payload = {"schema": CONTINUITY_FAULT_SCHEMA, "game_id": self.game_id,
                   "node_index": node_index, "error": f"{type(exc).__name__}: {exc}"}
        with self._lock:
            self._faults.append(payload)
        try:
            _append_jsonl(self._faults_path, payload)
        except OSError:
            pass

    def _compile_record(self, record: Any, level: int, life_ended: bool) -> None:
        started = time.perf_counter()
        cut = cut_visible_frame(record, level=level)
        with self._lock:
            current = self._windows[-1] if self._windows else None
            reason = None
            if current is not None:
                if self._new_window_after_life:
                    reason = "LIFE_RESET"
                elif level != current.level:
                    reason = "LEVEL_BOUNDARY"
                elif cut.geometry != current.geometry:
                    reason = "GEOMETRY_CHANGE"
                elif cut.full_reset and current.cuts:
                    reason = "LIFE_RESET"
            if current is None or reason is not None:
                if current is not None:
                    if current.boundary_reason != "LIFE_END":
                        current.boundary_reason = reason
                current = _Window(len(self._windows) + 1, level, cut.geometry)
                self._windows.append(current)
                self._new_window_after_life = False
            current.cuts.append(cut)
            if life_ended:
                current.boundary_reason = "LIFE_END"
                self._new_window_after_life = True
            self._cut_through_node = cut.node_index
            self._cut_timings_ms.append((time.perf_counter() - started) * 1000.0)
            self._dirty = True

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is self._STOP:
                    return
                record, level, life_ended = item
                try:
                    time.sleep(0.001)
                    self._compile_record(record, level, life_ended)
                except BaseException as exc:
                    self._fault(exc, getattr(record, "node_index", None))
            finally:
                self._queue.task_done()

    def wait_until_idle(self) -> None:
        self._queue.join()

    def _ensure_compiled(self) -> None:
        self.wait_until_idle()
        with self._lock:
            if not self._dirty:
                return
            started = time.perf_counter()
            compiled = []
            edge_records = []
            golden_edge_records = []
            experimental_edge_records = []
            all_cuts = sorted(
                (cut for window in self._windows for cut in window.cuts),
                key=lambda cut: cut.node_index,
            )
            pixel_records = [
                pixel_arithmetic(left, right)
                for left, right in zip(all_cuts, all_cuts[1:])
                if right.node_index == left.node_index + 1
            ]
            cut_by_node = {cut.node_index: cut for cut in all_cuts}
            acted_on_records = []
            expected: set[tuple[int, int]] = set()
            actual: list[tuple[int, int]] = []
            cut_failures = []
            track_offset = 0
            for window in self._windows:
                for cut in window.cuts:
                    cells: dict[Cell, int] = {}
                    conflict = False
                    for region in cut.regions:
                        expected.add((cut.node_index, region.component_id))
                        for cell in region.cells:
                            conflict = conflict or cell in cells
                            cells[cell] = region.class_id
                    rows, cols = cut.geometry
                    if conflict or len(cells) != rows * cols:
                        cut_failures.append({"node": cut.node_index, "covered_cells": len(cells),
                                             "expected_cells": rows * cols, "overlap": conflict})
                terminal: dict[tuple[int, int], str] = {}
                for left, right in zip(window.cuts, window.cuts[1:]):
                    golden_edges = weave_edge(left.regions, right.regions)
                    experimental_edges = weave_edge_with_partition_fence(
                        left.regions, right.regions
                    )
                    for edge in golden_edges:
                        record = _edge_artifact(
                            edge, left, right, window_id=window.window_id
                        )
                        edge_records.append(record)
                        golden_edge_records.append(record)
                        if edge.prev is not None and edge.now is None:
                            terminal[(edge.prev.node_index, edge.prev.component_id)] = edge.verb
                    for edge in experimental_edges:
                        experimental_edge_records.append(
                            _edge_artifact(edge, left, right, window_id=window.window_id)
                        )
                lines = re_join(weave_window(window.cuts), window.cuts)
                for line in sorted(lines, key=lambda item: item.local_id):
                    track_id = track_offset + line.local_id
                    actual.extend((step.node_index, step.component_id) for step in line.steps)
                    stitches = []
                    for edge in line.edges:
                        if edge.prev is None or edge.now is None:
                            continue
                        stitch = asdict(ContinuityStitch(
                            window.level, track_id, edge.prev.node_index, edge.prev.component_id,
                            edge.now.node_index, edge.now.component_id, edge.verb, edge.anchor,
                            edge.delta, (edge.witness,)))
                        left_cut = cut_by_node[edge.prev.node_index]
                        right_cut = cut_by_node[edge.now.node_index]
                        signature = arithmetic_signature(edge.prev, edge.now, left_cut, right_cut)
                        stitch["arithmetic_form"] = signature["lexicon_form"] if signature else None
                        stitch["form_agrees"] = (
                            None if signature is None else edge.verb == signature["lexicon_form"]
                        )
                        # The complete signature is canonical in weave_edges.jsonl.
                        # Do not duplicate its coordinate runs into every integral.
                        stitch["arithmetic_edge_ref"] = [
                            edge.prev.node_index, edge.now.node_index,
                            edge.prev.component_id, edge.now.component_id,
                        ]
                        stitches.append(stitch)
                    last = line.steps[-1]
                    end_reason = terminal.get(
                        (last.node_index, last.component_id), window.boundary_reason
                    )
                    compiled.append({
                        "window_id": window.window_id, "level": window.level,
                        "track_id": track_id, "local_worldline_id": line.local_id,
                        "display_id": f"W{window.window_id:03d}-###{line.local_id:03d}",
                        "born_node": line.steps[0].node_index,
                        "last_seen_node": line.steps[-1].node_index,
                        "status": "CLOSED", "end_reason": end_reason,
                        # Exact geometry lives once in flipbook_cuts.json.  These are
                        # lossless foreign keys plus useful scalar columns, not a
                        # second copy of every cell.
                        "observations": [step.reference(include_cells=False) for step in line.steps],
                        "stitches": stitches, "rejoin_witnesses": list(line.rejoin_witnesses),
                    })
                owner = {
                    (step.node_index, step.component_id): track_offset + line.local_id
                    for line in lines for step in line.steps
                }
                for before_cut, result_cut in zip(window.cuts, window.cuts[1:]):
                    target = result_cut.acted_cell
                    resolved_id = None
                    if target is None:
                        status = "NON_TARGETED"
                    elif not (0 <= target[0] < before_cut.geometry[0]
                              and 0 <= target[1] < before_cut.geometry[1]):
                        status = "EMPTY"
                    else:
                        sighting = next(
                            (region for region in before_cut.regions if target in region.cells), None
                        )
                        if sighting is None:
                            status = "DEFECT_IN_BOUNDS_UNOWNED"
                        else:
                            resolved_id = owner.get((before_cut.node_index, sighting.component_id))
                            status = "RESOLVED" if resolved_id is not None else "DEFECT_UNWOVEN"
                    acted_on_records.append({
                        "window_id": window.window_id,
                        "level": window.level,
                        "action_id": result_cut.action_id,
                        "target_cell": target,
                        "issued_from_node": before_cut.node_index,
                        "result_node": result_cut.node_index,
                        "worldline_id": resolved_id,
                        "status": status,
                        "resolution_frame": "PRE_ACTION",
                    })
                track_offset += max((line.local_id for line in lines), default=0)
            counts: dict[tuple[int, int], int] = {}
            for key in actual:
                counts[key] = counts.get(key, 0) + 1
            missing = sorted(expected - set(actual))
            duplicated = sorted(key for key, count in counts.items() if count != 1)
            self._compiled = compiled
            self._edge_records = edge_records
            self._golden_edge_records = golden_edge_records
            self._experimental_edge_records = experimental_edge_records
            self._pixel_records = pixel_records
            self._acted_on_records = acted_on_records
            self._window_count = len(self._windows)
            self._edge_count = len(edge_records)
            self._ambiguous_count = sum(edge["verb"] == "AMBIGUOUS" for edge in edge_records)
            self._acted_on_count = len(acted_on_records)
            self._acted_on_defects = sum(record["status"].startswith("DEFECT")
                                         for record in acted_on_records)
            self._fidelity = {
                "schema": "virelai-weave-fidelity-v1", "cuts": sum(len(w.cuts) for w in self._windows),
                "sightings_expected": len(expected), "sightings_in_worldlines": len(actual),
                "cut_partition_failures": cut_failures, "missing_sightings": missing,
                "duplicated_sightings": duplicated,
                "passed": not cut_failures and not missing and not duplicated and len(actual) == len(expected),
                "correctness_status": "REQUIRES_EXTERNAL_KEY",
            }
            self._weave_compiled_through_node = self._cut_through_node
            self._weave_timings_ms.append((time.perf_counter() - started) * 1000.0)
            self._dirty = False

    def canonical_tracks(self) -> list[dict[str, Any]]:
        self._ensure_compiled()
        with self._lock:
            return json.loads(json.dumps(self._compiled, default=str))

    def fidelity_verdict(self) -> dict[str, Any]:
        self._ensure_compiled()
        with self._lock:
            return json.loads(json.dumps(self._fidelity, default=str))

    @staticmethod
    def _performance(values: list[float]) -> dict[str, Any]:
        return {"samples": len(values), "p50_ms": round(_nearest_rank(values, 50), 3),
                "p95_ms": round(_nearest_rank(values, 95), 3),
                "max_ms": round(max(values, default=0.0), 3),
                "total_ms": round(sum(values), 3)}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "schema": CONTINUITY_SUMMARY_SCHEMA, "game_id": self.game_id,
                "submitted_through_node": self._submitted_through_node,
                "cut_through_node": self._cut_through_node,
                "compiled_through_node": self._weave_compiled_through_node,
                "queue_depth": self._queue.qsize(), "windows": self._window_count,
                "tracks": len(self._compiled),
                "stitches": sum(len(track["stitches"]) for track in self._compiled),
                "edges": self._edge_count,
                "pixel_arithmetic_edges": len(self._pixel_records),
                "pixel_arithmetic_total_edges": sum(
                    row["coverage_status"] == "TOTAL" for row in self._pixel_records
                ),
                "pixel_arithmetic_geometry_boundaries": sum(
                    row["geometry_changed"] for row in self._pixel_records
                ),
                "acted_on_records": self._acted_on_count,
                "acted_on_defects": self._acted_on_defects,
                "ambiguous_terminations": self._ambiguous_count, "faults": len(self._faults),
                "experimental_partition_branches": sum(
                    edge["verb"] in {"SPLIT", "MERGE"}
                    for edge in self._experimental_edge_records
                ),
                "cut_performance": self._performance(self._cut_timings_ms),
                "compile_performance": self._performance(self._weave_timings_ms),
                "fidelity": dict(self._fidelity),
                "identity_scope": "INTERIM_O9_anchor_first_per_level_life_window",
                "semantic_roles_inferred": False, "duck_visible": False,
            }

    def _write_artifacts(self) -> None:
        if self.artifact_dir is None:
            return
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        tracks = self.canonical_tracks()
        cuts = [{"window_id": window.window_id, "level": window.level,
                 "geometry": window.geometry, "boundary_reason": window.boundary_reason,
                 "sighting_encoding": "row_runs_inclusive",
                 "cuts": [{"node_index": cut.node_index, "visible_hash": cut.visible_hash,
                            "full_reset": cut.full_reset,
                            "regions": [{**r.reference(include_cells=False),
                                         "cell_runs": _cell_runs(r.cells)} for r in cut.regions]}
                           for cut in window.cuts]} for window in self._windows]
        events = []
        for track in tracks:
            events.append({"schema": CONTINUITY_SCHEMA, "event": "WORLDLINE", **track})
            events.extend({"schema": CONTINUITY_SCHEMA, "event": "STITCH", **stitch}
                          for stitch in track["stitches"])
            events.extend({"schema": CONTINUITY_SCHEMA, "event": "REJOIN_WITNESS",
                           "track_id": track["track_id"], **witness}
                          for witness in track["rejoin_witnesses"])
        (self.artifact_dir / "continuity.jsonl").write_text(
            "".join(json.dumps(event, sort_keys=True, default=str) + "\n" for event in events),
            encoding="utf-8")
        (self.artifact_dir / "weave_edges.jsonl").write_text(
            "".join(json.dumps(edge, sort_keys=True, default=str) + "\n"
                    for edge in self._edge_records), encoding="utf-8")
        (self.artifact_dir / "golden_weave_edges.jsonl").write_text(
            "".join(json.dumps(edge, sort_keys=True, default=str) + "\n"
                    for edge in self._golden_edge_records), encoding="utf-8")
        (self.artifact_dir / "experimental_partition_edges.jsonl").write_text(
            "".join(json.dumps(edge, sort_keys=True, default=str) + "\n"
                    for edge in self._experimental_edge_records), encoding="utf-8")
        (self.artifact_dir / "pixel_arithmetic.jsonl").write_text(
            "".join(json.dumps(record, sort_keys=True, default=str) + "\n"
                    for record in self._pixel_records), encoding="utf-8")
        (self.artifact_dir / "acted_on.jsonl").write_text(
            "".join(json.dumps(record, sort_keys=True, default=str) + "\n"
                    for record in self._acted_on_records), encoding="utf-8")
        for name, payload in (("continuity_tracks.json", tracks), ("flipbook_cuts.json", cuts),
                              ("continuity_fidelity.json", self.fidelity_verdict())):
            (self.artifact_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True,
                                                              default=str), encoding="utf-8")
        manifest = {
            "schema": "virelai-flipbook-manifest-v1",
            "canonical_sightings": "flipbook_cuts.json",
            "canonical_pixel_arithmetic": "pixel_arithmetic.jsonl",
            "canonical_correspondence_edges": "weave_edges.jsonl",
            "correspondence_policy": (
                "INTERIM_O9 anchor-first; observable correspondence hypothesis, "
                "not semantic identity"
            ),
            "unmodified_v4_edge_verdicts": "golden_weave_edges.jsonl",
            "experimental_partition_hypotheses": "experimental_partition_edges.jsonl",
            "worldline_integrals": "continuity_tracks.json",
            "pre_action_provenance": "acted_on.jsonl",
            "event_view": "continuity.jsonl",
            "fidelity_grade": "continuity_fidelity.json",
            "join_key": ["node_index", "component_id"],
            "cell_encoding": "row_runs_inclusive",
            "lossless": True,
            "semantic_roles_inferred": False,
            "duck_visible": False,
        }
        (self.artifact_dir / "flipbook_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    def close(self) -> dict[str, Any]:
        with self._lock:
            already_closed = self._closed
            self._closed = True
        if not already_closed:
            self._queue.put(self._STOP)
            self._worker.join()
        self._ensure_compiled()
        self._write_artifacts()
        summary = self.snapshot()
        if self.artifact_dir is not None:
            (self.artifact_dir / "continuity_summary.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        # The immutable compact frame journal is the retained source of truth.
        # Exact cuts and the complete edge table now live on disk; retaining a
        # second decompressed copy would multiply memory without adding evidence.
        with self._lock:
            self._windows.clear()
            self._edge_records.clear()
            self._golden_edge_records.clear()
            self._experimental_edge_records.clear()
            self._pixel_records.clear()
            self._acted_on_records.clear()
        return summary


__all__ = ["CONTINUITY_FAULT_SCHEMA", "CONTINUITY_SCHEMA", "CONTINUITY_SUMMARY_SCHEMA",
           "ComponentObservation", "ContinuityCompiler", "ContinuityStitch", "NodeCut",
           "arithmetic_signature", "cut_visible_frame", "pixel_arithmetic", "re_join",
           "segment_visible_components", "weave_edge", "weave_edge_with_partition_fence",
           "weave_window"]
