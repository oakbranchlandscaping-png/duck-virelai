"""
contracts/object_class.py

Canonical ObjectClass definition. Single source of truth for the entire V3.5 codebase.

All modules must import from here:
    from .object_class import ObjectClass, ReactivityClass

No other file may define a class named ObjectClass.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReactivityClass(Enum):
    """
    Coarse reactivity classification for a pixel value.

    STATIC:      Never changes across any observed action (background).
    INERT:       No evidence of change yet — could be structural or interactive.
    RECEPTIVE:   Changes in response to some actions (directional or click).
    CONDITIONAL: Changes only under specific conditions (threshold, proximity).
    """
    STATIC = "STATIC"
    INERT = "INERT"
    RECEPTIVE = "RECEPTIVE"
    CONDITIONAL = "CONDITIONAL"


@dataclass(frozen=True)
class ObjectClass:
    """
    Measured properties of a single pixel value.

    No role. No semantic label. Pure measurement.
    Canonical schema: 8 measured fields + 1 derived flag.

    All production code must use this definition.
    Shadow definitions in contracts/phase1.py and
    world_characterization/object_census.py have been removed.
    """
    pixel_value: int
    total_cells: int
    num_components: int
    area_mean: float
    area_max: int
    compactness: float           # mean area / bounding_box_area [0, 1]
    reactivity_class: ReactivityClass
    background_fraction: float   # this value's fraction of total grid cells
    is_static: bool              # True when reactivity_class == STATIC


__all__ = ["ReactivityClass", "ObjectClass"]
