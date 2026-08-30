"""
virelai_v4/contracts/probe_types.py — ProbeOutcome frozen dataclass.

Consumed by WO-02 (probe executor) and WO-03 (causal attributor).
Produced by classify_probe_outcome() in library/probe_outcome_classifier.py.
(Relocated under WO-MINE-CLEAN-04 to break the library↔strategy import cycle.)

Frozen: no mutation after construction. All fields have defaults to allow
partial construction in tests.

WO-01 LEVER-CATALOG
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal


@dataclass(frozen=True)
class ProbeOutcome:
    """Result of classifying a single probe's world delta.

    Five outcomes:
        LEVER_LOCAL_SELF    — probed object's own cells changed; no other region affected.
                              Classic self-referential lever (FT09-style toggle).
        LEVER_LOCAL_REMOTE  — probed object's own cells changed AND other regions changed.
                              Lever with both local and remote effects.
        LEVER_REMOTE_ONLY   — probed object unchanged; other regions changed.
                              Classic remote lever (vc33-style).
        NO_EFFECT           — no world delta beyond ego displacement.
                              Probed object is inert (or not a lever).
        AMBIGUOUS           — world delta is non-empty but entirely attributable to ego
                              displacement. Caller should re-probe after ego moves.

    Fields
    ------
    outcome : Literal[...]
        One of the five outcome strings above.
    probed_region_id : int
        Region ID of the object that was probed.
    affected_region_ids : List[int]
        Region IDs of other objects whose cells changed (REMOTE evidence).
        Empty for LEVER_LOCAL_SELF, NO_EFFECT, and AMBIGUOUS.
    disregarded_region_ids : List[int]
        WO-EFFECT-LABEL — live/HUD region IDs whose cells ALSO changed on this
        press but were CONSCIOUSLY DISREGARDED as non-effects (the COUNTER ticks
        every press). This is active labeling + conscious disregard, NOT a silent
        mask: the change is observed and recorded here, attributed to its role,
        and deliberately excluded from affected_region_ids. Empty when nothing
        live was touched.
    self_cells_changed : bool
        True when the probed object's own cells appeared in the world delta.
    other_reactive_cells_changed : bool
        True when at least one other region's cells appeared in the world delta.
    notes : str
        Optional diagnostic message (e.g. re-probe advice, missing region note).
    """
    outcome: Literal[
        "LEVER_LOCAL_SELF",
        "LEVER_LOCAL_REMOTE",
        "LEVER_REMOTE_ONLY",
        "NO_EFFECT",
        "AMBIGUOUS",
    ]
    probed_region_id: int
    affected_region_ids: List[int] = field(default_factory=list)
    disregarded_region_ids: List[int] = field(default_factory=list)
    self_cells_changed: bool = False
    other_reactive_cells_changed: bool = False
    notes: str = ""
