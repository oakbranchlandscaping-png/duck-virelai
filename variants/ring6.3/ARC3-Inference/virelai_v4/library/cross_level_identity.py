"""
virelai_v4/library/cross_level_identity.py — cross-level TYPE identity.

WO-XLEVEL-01 (§12 ruling / Apex Directive 3; BR-CP1-READ-00 mining). Levels
re-instantiate objects as fresh instances of the same TYPE: vc33's levers stay
class-9 toggle squares while count doubles, rendered scale halves (4x4 -> 2x2),
and positions/region_ids change. There is NO 1:1 instance mapping — so the
cross-level match key is TYPE: (pixel_class, scale-normalized shape).
region_id is falsified across levels and plays no part; raw size/count are
scale-variant and excluded. Every type-match earns trust only through one
behavioral re-confirmation probe (the V3.5 `delta >= min_delta` discipline,
execution/click_discovery.py:231 — concept-port).

Blueprint amendment carried: §2.8.5 Step 3's `class_signature + region_id`
match is OVERRULED by the §12 ruling — type signature, region_id dropped.

INVENT: the scale-normalized shape signature (V3.5 carried class+count+
quadrant, never shape; the contracts ShapeSignature scaffold is
position-canonical only). PORT: the type-match + re-confirm semantics.

Pure module: no side effects, no library writes, deterministic and
process-stable (no str hashing; canonical tuples only). The §2.8.5 hook
(XLEVEL-02) and boundary re-falsification (XLEVEL-03) WIRE these primitives.
"""

from __future__ import annotations

from math import gcd
from typing import FrozenSet, Iterable, NamedTuple, Tuple


class TypeSignature(NamedTuple):
    """The cross-level match key: pixel class + scale-normalized shape.
    NO region_id, NO position, NO raw size/count."""
    pixel_class: int
    shape: Tuple[int, int, Tuple[int, ...]]  # (norm_h, norm_w, flat 0/1 mask)


def _bbox_mask(cells: FrozenSet[Tuple[int, int]]) -> Tuple[int, int, Tuple[int, ...]]:
    """Cells -> bounding-box binary mask (position-invariant)."""
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, c0 = min(rows), min(cols)
    h = max(rows) - r0 + 1
    w = max(cols) - c0 + 1
    mask = [0] * (h * w)
    for (r, c) in cells:
        mask[(r - r0) * w + (c - c0)] = 1
    return h, w, tuple(mask)


def _block_uniform(mask: Tuple[int, ...], h: int, w: int, k: int) -> bool:
    """True iff the h x w mask is an exact k x k block upscale of a smaller mask."""
    for br in range(h // k):
        for bc in range(w // k):
            v = mask[(br * k) * w + (bc * k)]
            for dr in range(k):
                for dc in range(k):
                    if mask[(br * k + dr) * w + (bc * k + dc)] != v:
                        return False
    return True


def _downscale(mask: Tuple[int, ...], h: int, w: int, k: int) -> Tuple[int, int, Tuple[int, ...]]:
    nh, nw = h // k, w // k
    out = [mask[(br * k) * w + (bc * k)] for br in range(nh) for bc in range(nw)]
    return nh, nw, tuple(out)


def scale_normalized_shape(
    cells: Iterable[Tuple[int, int]],
) -> Tuple[int, int, Tuple[int, ...]]:
    """The INVENT: a position- AND scale-invariant canonical shape.

    Bounding-box mask, then downscaled by the LARGEST k dividing both
    dimensions for which the mask is an exact k x k block upscale — so a 4x4
    solid square and a 2x2 solid square both canonicalize to the 1x1 solid
    (the vc33 L3 halving case). Aspect ratio and fill pattern survive; raw
    scale does not. Pure; deterministic; process-stable (no str hashing)."""
    cs = frozenset((int(r), int(c)) for r, c in cells)
    if not cs:
        return (0, 0, ())
    h, w, mask = _bbox_mask(cs)
    k = gcd(h, w)
    while k > 1:
        if h % k == 0 and w % k == 0 and _block_uniform(mask, h, w, k):
            h, w, mask = _downscale(mask, h, w, k)
            k = gcd(h, w)
        else:
            k -= 1
    return (h, w, mask)


def type_signature(pixel_class: int, cells: Iterable[Tuple[int, int]]) -> TypeSignature:
    """The cross-level match key for one object instance."""
    return TypeSignature(int(pixel_class), scale_normalized_shape(cells))


def type_signature_of(obj) -> TypeSignature:
    """Duck-typed convenience: works for LibraryObject (class_id/cells) and the
    Segment scaffold (class_signature/cells)."""
    pixel_class = getattr(obj, "class_id", None)
    if pixel_class is None:
        pixel_class = getattr(obj, "class_signature")
    return type_signature(pixel_class, obj.cells)


def signatures_match(a: TypeSignature, b: TypeSignature) -> bool:
    """Type-level equality. region_id, position, raw size/count never enter."""
    return a == b


# V3.5 default (execution/click_discovery.py:231: delta_range[0] else 20).
DEFAULT_MIN_DELTA = 20


def is_reconfirmed(probe_delta: int, min_delta: int = DEFAULT_MIN_DELTA) -> bool:
    """Behavioral re-confirmation (PORTed discipline): a type-matched carry is
    trusted only after one probe whose observed delta meets the floor. The
    carried belief stays a re-falsifiable prior until this fires."""
    return probe_delta >= min_delta


__all__ = [
    "TypeSignature", "scale_normalized_shape", "type_signature",
    "type_signature_of", "signatures_match", "is_reconfirmed",
    "DEFAULT_MIN_DELTA",
]
