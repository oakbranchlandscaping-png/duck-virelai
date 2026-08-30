"""WO-R1-01a · WORLDLINE→SLOT BINDING · generalize the still join to movers.

The still bridge (``still_bridge.join_to_slot``) binds only *still* worldlines —
fingerprints seen unchanged across ≥2 nodes — because it joins by the worldline's
invariant fingerprint, and a mover mints a new fingerprint per position. This
module binds EVERY worldline (still OR mover) to its spawn-partition ``region_id``
by the SAME free equality join, applied to the worldline's ``first_region`` (its
spawn state) instead of an invariant fingerprint.

Why the spawn node is the right key (proven — WO-R1-01a Phase A reads):
  * The library's ``region_id`` and ``cells`` are fixed at the SPAWN partition
    (``library_sync`` Mode A populates objects once when ``len(objects)==0``; the
    Mode B delta path updates evidence fields — never relocates a slot's cells).
    So ``slot_fingerprints`` is keyed by spawn cells.
  * A mover's ``first_region`` is its spawn region — the same ``scan_grid``
    partition the spawn slot was minted from — so ``(class_id, cells)`` equality-
    matches the spawn slot. No nearest-match, no drift.
  * Rejoin/DEFORM never resets a mover's identity: a mover CONTINUES via
    MOVE/GROW/SHRINK and is never a BIRTH candidate (``rejoin.py``), so
    ``first_region`` is the true spawn region.

Discipline (mirrors ``still_bridge``): a PURE resolver. Reads the worldlines and
the slot-fingerprint dict, returns a binding map. Imports no ``library``, no
accumulator; writes no belief. Free equality join only. Worldlines with no
matching spawn slot — mid-run BIRTH / split products that did not exist at spawn
— are counted and honestly omitted, never force-matched. Landing role evidence
through the binding is a SEPARATE step (R1-01b); this module only binds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple

# (class_id, frozenset(cells)) — the same key still_bridge.slot_fingerprints uses.
Fingerprint = Tuple[int, "frozenset"]


@dataclass(frozen=True)
class BindReport:
    """The binding outcome — the raw material of the weave↔A divergence map."""

    total: int                 # worldlines seen
    bound: int                 # bound to a spawn slot
    unbound: int               # no equal spawn slot (honest miss; never force-matched)
    bindings: Dict[int, int]   # worldline_id -> region_id


def _first_region_fingerprint(worldline: Any) -> Fingerprint:
    """The ``(class_id, cells)`` of the worldline's spawn region — the same key
    ``still_bridge`` builds ``slot_fingerprints`` on."""
    fr = worldline.first_region
    return (fr.class_id, fr.cells)


def bind_worldlines_to_slots(
    worldlines: Iterable[Any],
    slot_fingerprints: Dict[Fingerprint, int],
) -> BindReport:
    """Bind each worldline — still OR mover — to its spawn-partition ``region_id``
    by ``first_region`` fingerprint equality (no still-invariance filter).

    Unbound worldlines (no equal spawn slot — mid-run BIRTH / split products) are
    counted and omitted, never force-matched. Returns a ``BindReport`` carrying
    the ``worldline_id -> region_id`` map for the bound.
    """
    bindings: Dict[int, int] = {}
    total = 0
    for w in worldlines:
        total += 1
        rid = slot_fingerprints.get(_first_region_fingerprint(w))
        if rid is not None:
            bindings[w.id] = rid
    bound = len(bindings)
    return BindReport(total=total, bound=bound, unbound=total - bound, bindings=bindings)
