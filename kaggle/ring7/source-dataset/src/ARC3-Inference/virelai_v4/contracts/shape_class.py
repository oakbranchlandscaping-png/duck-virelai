"""
virelai_v4/contracts/shape_class.py — Shape classification for Segment dataclass.

Per Blueprint Section 2.4.3 specification, the Segment dataclass carries a
`shape_class: ShapeClass` field. The enum determines anchor derivation rules
(per Section 2.4.3) and supports future deformation-detection revocation
triggers.

Per the Blueprint Section 1.6 glossary:
    ShapeClass — A typed enumeration of broad shape categories: RECT, LINE,
    L_SHAPE, IRREGULAR, and others. Determines anchor derivation rules per
    Section 2.4.3.

This file ships the enum + the ShapeSignature type alias used by Segment.

Filed under WO-BLUEPRINT-04 (Sub-Phase 2 of Blueprint Absorption), May 19, 2026.
INVENT anchor: #4 — Class-change revocation + Segment/Slot factoring.
"""

from __future__ import annotations

from enum import Enum, auto


# ShapeSignature: a position-invariant canonical-form hash of a Segment's
# cells. Two Segments with the same shape but different positions have the
# same shape_signature. Used for displacement detection (Section 1.6) and
# future deformation-revocation triggers.
#
# Per Blueprint Section 1.6 glossary. Implemented as `int` (Python's
# native hash of a canonicalized cell-set) for Phase B.1 scaffold work.
# Section 4+ may refine to a structured hash type.
ShapeSignature = int


class ShapeClass(Enum):
    """Broad shape category enum per Blueprint Section 2.4.3.

    Determines anchor derivation rules per Section 2.4.3:
      - RECT: anchor = bbox center
      - LINE: anchor = midpoint of the line
      - L_SHAPE: anchor = corner pixel
      - IRREGULAR: anchor = centroid (V3.5 default)

    The shape_class field is present in the Segment dataclass but used
    minimally in Phase B.1 scaffold work per Section 2.4.3. Anchor
    derivation and the future deformation-detection revocation trigger
    depend on it.

    Additional values can be added as Section 4 variant catalogs surface
    them. The Blueprint Section 2.4.3 glossary notes "RECT | LINE |
    L_SHAPE | IRREGULAR | ..." — the ellipsis indicates extensibility.
    """
    RECT = auto()
    LINE = auto()
    L_SHAPE = auto()
    IRREGULAR = auto()
    # Future additions per Section 4 variant catalog work.
