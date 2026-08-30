"""virelai_v4/diagnostics/frame_dump.py — Phase 1 per-frame physics dump.

WO-PHASE1-DIAGNOSTIC-DUMP-VC33-MOVERS-BOUNDARY (Physics Reframe NR-01,
Phase 1). Read-only instrumentation.

Emits one JSONL event per probed-lever press to a diagnostic file, gated
by VIRELAI_DIAG_DUMP=1 (path overridable via VIRELAI_DIAG_PATH). The
event carries the raw substrate state Phase 2 (NR-01 §4.3 authoring)
needs to author the boundary criterion FROM evidence:

  - delta_cells              raw count of changed cells (prev vs current)
  - displacement_vector      primary mover's (d_row, d_col), null if none
  - boundary_contact_state   FACTUAL occupancy summary (see below)
  - press_position_neighbors raw 4-neighborhood occupancy at the press

boundary_contact_state is a FACTUAL read of whether substance sits
adjacent to the press cells when nothing moved — NOT a behavioral verdict
(no "blocked" / "bounce" / "deform" classification; that is Phase 3, and
only after Phase 2 authors the criterion). The raw neighbor occupancy is
emitted alongside so Phase 2 can re-derive any criterion it chooses.

Scope discipline:
  - Write-only to a file. The captain never reads this output.
  - measure_operations() is recomputed read-only and ONLY when the dump
    is active (init opened the file). When disabled, maybe_emit_frame_event
    short-circuits before any work — the floor is byte-identical.
  - No substrate state is mutated. observation_status / rigid_observation
    _count / causes / caused_by are READ, never written.

Inheritance: dump-shape PORT-WITH-MODIFICATIONS from V3.5
scripts/dump_worldmodel.py (instrumentation, capture-only); path-gated
JSONL idiom mirrors virelai_v4/observability_choke_point.py; per-frame
vector/boundary fields are INVENT (V4-native A.2b measurer).
"""

from __future__ import annotations

import atexit
import json
import os
from typing import List, Optional, TextIO, TYPE_CHECKING

import numpy as np

from virelai_v4.perception.operation_measurer import measure_operations

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import cost
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import SemanticLibrary

# Von-Neumann 4-neighborhood, matching the WO event schema.
_NEIGHBOR_OFFSETS = ((0, 1), (0, -1), (1, 0), (-1, 0))

# Module-level file handle. None when the dump is disabled or closed.
_dump_file: Optional[TextIO] = None


# ---------------------------------------------------------------------------
# Env gating + lifecycle
# ---------------------------------------------------------------------------
def diag_enabled() -> bool:
    """True when VIRELAI_DIAG_DUMP=1. Independent of VIRELAI_QUIET — the
    dump is an intentional deliverable, not operational noise."""
    return os.environ.get("VIRELAI_DIAG_DUMP", "0") == "1"


def diag_path() -> str:
    """Dump file path; VIRELAI_DIAG_PATH overrides the default."""
    return os.environ.get("VIRELAI_DIAG_PATH", "/tmp/virelai_diag_dump.jsonl")


def init_dump_file() -> None:
    """Open (truncate) the dump file at session start when enabled.

    Idempotent: a second call while open is a no-op. Registers an atexit
    close so the handle is released even on early termination (per-event
    flush already makes the file crash-robust)."""
    global _dump_file
    if not diag_enabled() or _dump_file is not None:
        return
    _dump_file = open(diag_path(), "w")
    atexit.register(close_dump_file)


def emit_frame_event(event: dict) -> None:
    """Write one JSONL event. No-op when the dump is not open. Flushes
    per event for robustness against crashes mid-run."""
    if _dump_file is None:
        return
    _dump_file.write(json.dumps(event) + "\n")
    _dump_file.flush()


def close_dump_file() -> None:
    """Close the dump file at session end. Idempotent."""
    global _dump_file
    if _dump_file is not None:
        _dump_file.close()
        _dump_file = None


# ---------------------------------------------------------------------------
# Read-only event composition
# ---------------------------------------------------------------------------
def _background_value(grid: np.ndarray) -> int:
    """Modal grid value — the scanner's own background convention
    (grid_scan.py: most-frequent value is background). Pure read."""
    vals, counts = np.unique(grid, return_counts=True)
    return int(vals[int(counts.argmax())])


def _press_centroid(cells) -> List[int]:
    """Rounded centroid of the probed region's cells — the representative
    press position for the neighbor readout."""
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return [round(sum(rows) / len(rows)), round(sum(cols) / len(cols))]


def _neighbors(grid: np.ndarray, center: List[int], bg: int) -> List[dict]:
    """Raw 4-neighborhood occupancy at the press centroid. class_id is the
    raw cell value (null off-grid); occupied is value != background."""
    height, width = grid.shape
    crow, ccol = center
    out: List[dict] = []
    for d_row, d_col in _NEIGHBOR_OFFSETS:
        nrow, ncol = crow + d_row, ccol + d_col
        if 0 <= nrow < height and 0 <= ncol < width:
            value = int(grid[nrow, ncol])
            out.append({"offset": [d_row, d_col],
                        "occupied": value != bg,
                        "class_id": value})
        else:
            out.append({"offset": [d_row, d_col],
                        "occupied": False,
                        "class_id": None})
    return out


def _boundary_state(delta_cells: int, neighbors: List[dict]) -> str:
    """FACTUAL occupancy summary. NOT_APPLICABLE when something changed;
    otherwise ADJACENT_SUBSTANCE if any neighbor is occupied, else
    OPEN_FIELD. No behavioral verdict."""
    if delta_cells != 0:
        return "NOT_APPLICABLE"
    if any(n["occupied"] for n in neighbors):
        return "ADJACENT_SUBSTANCE"
    return "OPEN_FIELD"


def _primary_vector(operations) -> Optional[List[float]]:
    """Largest mover cluster's displacement vector (tie-break by
    magnitude); None when no rigid mover was measured."""
    if not operations:
        return None
    best = max(operations,
               key=lambda o: (o.region_count, o.vector[0] ** 2 + o.vector[1] ** 2))
    return [best.vector[0], best.vector[1]]


def compose_frame_event(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    prev_grid,
    grid,
) -> Optional[dict]:
    """Build one read-only event for the current probed press, or None
    when there is no press to record (no probe target / life-start /
    region absent — mirrors run_physics_measurement's own fences)."""
    rid = context.last_probe_target_region_id
    if rid is None or prev_grid is None:
        return None
    if rid not in library.objects:
        return None
    obj = library.objects[rid]

    grid_a = np.asarray(grid)
    grid_b = np.asarray(prev_grid)
    delta_cells = int(np.count_nonzero(grid_b != grid_a))
    operations = measure_operations(grid_b, grid_a)   # pure, read-only
    background = _background_value(grid_a)

    cells = context.last_probe_target_cells or frozenset()
    center = _press_centroid(cells) if cells else [-1, -1]
    neighbors = _neighbors(grid_a, center, background) if cells else []

    return {
        "frame": int(getattr(library.header, "actions_taken", -1)),
        "lever_rid": int(rid),
        "action": {"type": context.last_probe_action_kind, "coords": center},
        "delta_cells": delta_cells,
        "displacement_vector": _primary_vector(operations),
        "mover_count": len(operations),
        "boundary_contact_state": _boundary_state(delta_cells, neighbors),
        "mover_classification": str(obj.observation_status.value),
        "rigid_observation_count": int(obj.rigid_observation_count),
        "causes_list": list(obj.causes),
        "caused_by_list": list(obj.caused_by),
        "press_position_neighbors": neighbors,
    }


def maybe_emit_frame_event(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    prev_grid,
    grid,
) -> None:
    """Single facade hook. No-op (and zero recompute) unless the dump is
    open. All read-only; never mutates substrate or context."""
    if _dump_file is None:
        return
    event = compose_frame_event(context, library, prev_grid, grid)
    if event is not None:
        emit_frame_event(event)


__all__ = [
    "diag_enabled",
    "diag_path",
    "init_dump_file",
    "emit_frame_event",
    "close_dump_file",
    "compose_frame_event",
    "maybe_emit_frame_event",
]
