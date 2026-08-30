"""
virelai_v4/contracts/segment.py — The Segment Layer-1 frozen dataclass.

Per Blueprint Section 2.4.3 specification — the Layer-1 frozen record of a
shape-in-position at a single frame. Per Section 1.6:

    Layer 1: The Segment. A frozen record of a shape-in-position at a
    single frame. A Segment carries the fields that describe what an
    object looks like *right now* — its cells, its bounding box, its
    anchor, its class signature. A Segment is anonymous: it does not
    carry identity across frames. It is evidence-free: it does not
    carry accumulated learning. It is replaced (never mutated) each
    frame. Any reference to a Segment is a reference to a specific
    frame's binding.

Produced by: GridScan + per-Slot Segment construction in substrate hygiene
              (Section 2.8.2). Each frame's GridScan output drives Segment
              instantiation; the prior Segment is dropped (never mutated).
Consumed by: Captain (reads cells, bbox, anchor for dispatch coordinate
              selection); class-change revocation hook (compares
              class_signature between current_segment and last_probed_segment
              per Section 1.7); BBA Layer One (consumes shape_signature for
              future deformation-revocation work, deferred).

Filed under WO-BLUEPRINT-04 (Sub-Phase 2 of Blueprint Absorption), May 19, 2026.
INVENT anchor: #4 — Class-change revocation + Segment/Slot factoring.

Persistence tier: No tier (rebuilt per frame). Per Section 2.10 the field
referencing this dataclass on LibraryObject (`current_segment`) is rebuilt
each frame; `last_probed_segment` is PER_LIFE_SCRATCHPAD.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple

from virelai_v4.contracts.shape_class import ShapeClass, ShapeSignature


@dataclass(frozen=True)
class Segment:
    """The Layer-1 frozen record of a shape-in-position at a single frame.

    Per Blueprint Section 2.4.3:

        @dataclass(frozen=True)
        class Segment:
            cells: frozenset[tuple[int, int]]
            bbox: tuple[int, int, int, int]
            anchor: tuple[float, float]
            class_signature: int
            shape_signature: ShapeSignature
            shape_class: ShapeClass

    `frozen=True` is load-bearing per Section 1.6 — any code holding a
    Segment reference holds a reference to one specific frame's binding,
    and the language prevents silent updates.

    Fields:
        cells: The cells this Segment occupies. frozenset of (row, col).
        bbox: (min_row, min_col, max_row, max_col) inclusive.
        anchor: Per-shape reference point as (float row, float col).
              Anchor derivation rule depends on shape_class.
        class_signature: The pixel class value (single-color regime).
              Section 2.4 specifies `int`; multi-color support is a Section 4+
              evolution.
        shape_signature: Canonical-form position-invariant hash. Two Segments
              with the same shape but different positions share this value.
        shape_class: Broad shape category — RECT, LINE, L_SHAPE, IRREGULAR.
    """
    cells: FrozenSet[Tuple[int, int]]
    bbox: Tuple[int, int, int, int]
    anchor: Tuple[float, float]
    class_signature: int
    shape_signature: ShapeSignature
    shape_class: ShapeClass
