"""WO_WORLD_GRAIN_IDENTITY · a declared, library-typed world-identity grain over the
sealed full-grid floor.

Node identity here MASKS the instrument (HUD) cells: two grids that differ ONLY in
HUD cells — a fuel/counter readout ticking — are the SAME world-node, so a room
re-converges across instrument states while the raw grain keeps every reading.

Rulings honored:
  - Two grains: the raw grain (``induced_map._default_key``, the sealed full-grid
    hash) is UNCHANGED. This is a SECOND grain reusing the same merge machinery with
    only the identity function swapped.
  - Recompute, never stored: the world map is re-derived over ``(records, hud_mask)``.
    When the mask firms up (the HUD typing converges), the map re-converges. The
    world key is a VIEW stamped with the mask it used, never a stored node key.
  - PORT, not invent: the ``hud_mask`` (a ``FrozenSet[(row, col)]`` of instrument
    cells) is INJECTED by the caller, which reads the classifier's accumulated
    ``ctx.hud_mask``. This module re-derives no HUD detection and imports nothing
    from ``library/`` — belief-free and library-free, exactly like the frontier
    labeler; belief enters only through the injected mask.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Tuple

from virelai_v4.weave.induced_map import InducedMap, _default_key, build_induced_map

Cell = Tuple[int, int]
# Masked cells collapse to a single sentinel value, so grids identical on the
# navigable world but differing in instrument readouts hash the same.
_MASK_SENTINEL = -1


def world_key(grid: Any, hud_mask: "FrozenSet[Cell]") -> str:
    """The world-grain identity: sha256 of the settled visible grid with every HUD
    cell replaced by ``_MASK_SENTINEL``. Grids that differ only in instrument cells
    hash identically. An empty mask reproduces the full-grid identity basis."""
    masked = tuple(
        tuple(_MASK_SENTINEL if (r, c) in hud_mask else int(v) for c, v in enumerate(row))
        for r, row in enumerate(grid or [])
    )
    return hashlib.sha256(repr(masked).encode("utf-8")).hexdigest()


def build_world_map(records, hud_mask: "FrozenSet[Cell]") -> InducedMap:
    """The world map: the SAME induced-map merge (loop closure, walked-only edges,
    reset-aware geometry) with the identity function swapped to ``world_key``.
    Injection-only — ``hud_mask`` is a parameter; nothing from ``library/`` is read.
    The sealed full-grid identity is untouched."""
    return build_induced_map(records, key_fn=lambda r: world_key(r.layers[-1], hud_mask))


def world_members(world_map: InducedMap, records) -> "Dict[str, FrozenSet[str]]":
    """The raw→world merge mapping as a NAMED CONTRACT: per world-node key, the set
    of RAW node keys (full-grid identities) that merged into it. Recovered from the
    world-node ``arrivals`` (raw record indices) + the records — the same mapping
    ``world_collapse`` computes transiently, now a stable API both audit reads bind
    to. Pure; reads nothing from ``library/``."""
    by_index = {int(r.node_index): r for r in records}
    out: Dict[str, FrozenSet[str]] = {}
    for wk, node in world_map.nodes.items():
        raws = {
            _default_key(by_index[int(i)])
            for i in node.arrivals
            if int(i) in by_index
        }
        out[wk] = frozenset(raws)
    return out


@dataclass(frozen=True)
class WorldCollapse:
    raw_nodes: int
    world_nodes: int
    hud_cells: int
    collapse_ratio: float                        # raw / world (>1 ⇒ re-convergence)
    top_absorbers: Tuple[Tuple[str, int], ...]   # (world_key[:8], distinct raw grids unified)


def world_collapse(records, hud_mask: "FrozenSet[Cell]") -> WorldCollapse:
    """The re-convergence measure: how far the HUD-inflated raw map collapses toward
    the true room count once instrument cells are masked, and which world-nodes
    absorbed the most raw grids (the fuel levels they unified)."""
    recs = list(records)
    raw = build_induced_map(recs)

    absorbed: Dict[str, set] = {}
    for r in recs:
        absorbed.setdefault(world_key(r.layers[-1], hud_mask), set()).add(_default_key(r))
    world_nodes = len(absorbed)
    top = sorted(((k, len(v)) for k, v in absorbed.items()), key=lambda kv: -kv[1])[:5]

    raw_nodes = len(raw.nodes)
    return WorldCollapse(
        raw_nodes=raw_nodes,
        world_nodes=world_nodes,
        hud_cells=len(hud_mask),
        collapse_ratio=(raw_nodes / world_nodes) if world_nodes else 1.0,
        top_absorbers=tuple((k[:8], n) for k, n in top),
    )


def render_world_grain(records, hud_mask: "FrozenSet[Cell]") -> str:
    """The re-convergence read: raw → world node counts, collapse ratio, mask size,
    and the world-nodes that unified the most instrument states."""
    c = world_collapse(records, hud_mask)
    lines = [
        f"WORLD GRAIN — raw {c.raw_nodes} nodes → world {c.world_nodes} nodes "
        f"(collapse {c.collapse_ratio:.2f}x) · {c.hud_cells} HUD cell(s) masked"
    ]
    if c.hud_cells == 0:
        lines.append("  (empty HUD mask — world grain equals raw grain; HUD typing "
                     "not yet converged, or no COUNTER in this world)")
    for k, n in c.top_absorbers:
        if n > 1:
            lines.append(f"  world[{k}] unified {n} raw grids (instrument states)")
    return "\n".join(lines)
