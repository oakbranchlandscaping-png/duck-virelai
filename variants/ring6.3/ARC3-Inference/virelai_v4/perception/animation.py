"""virelai_v4/perception/animation.py — multi-frame animation perception (front end).

WO-EYE-01 (Campaign E / The Eyes front end). The interior frame layers that the
persistent path discards — it reads ``frame[-1]`` only (WO-EYE-00) — are read
HERE, on a disjoint, additive, diagnostic-only path that writes no belief.

Deliverables, in order:

  - ``animation_layers(frame)`` — INGEST (D1). The additive accessor that retains
    the full layer list the two collapse sites (``virelai.py:95`` ``_grid_from_frame``,
    ``virelai.py:737`` ``_sync_library``) drop when they take ``frame[-1]``. The
    persistent path's ``frame[-1]`` source is left exactly as is; this is a NEW,
    parallel read of the interior layers, never a rerouting of the settled-grid
    source. That untouched binding is the WO-EYE-00 separation fence.

  - ``classify_press(layers)`` — DETECT + CLASSIFY (D2). Bins a turn's press
    outcome into the FLASH / SILENT / EFFECTIVE trichotomy from structure alone.

  - ``scan_layers(layers)`` — iterates the interior layers through ``scan_grid``
    per-layer. Each layer is a 2-D ``rows x cols`` grid the existing geometry
    stack processes unchanged — ``scan_grid`` is NOT widened to accept the 3-D
    sequence (premise 2: iterate, don't widen). Pure read.

  - ``emit_animation_turn_diag(frame, turn_index)`` — EMIT (D3). One per-turn
    JSON line to the diagnostic surface, gated on ``VIRELAI_DIAG_DUMP``, off by
    default. Rhymes with the E12 ``emit_counter_candidate_diag`` surface. Pure
    read — the live path is byte-unchanged when not diagnosing.

Kind-legal: the trichotomy is structural — sequence length, endpoint equality,
interior-layer cell change. No color, class, position, world, or outcome
constant enters. A FLASH carries no state content: the classifier records THAT a
flash occurred, never decodes meaning from it. No belief is written anywhere in
this module — it ends at the diagnostic surface (Rungs 2-7 own the belief write).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

from virelai_v4.perception.grid_scan import GridScan, has_animation_frames, scan_grid

# Press-outcome trichotomy — machine grammar (FT09 WPS port), not world content.
FLASH = "FLASH"          # endpoint-neutral animation: the press flashed, committed nothing
SILENT = "SILENT"        # no animation and no persistent change
EFFECTIVE = "EFFECTIVE"  # settled endpoints differ: a persistent board change occurred
# WO-DELIVERY-CLASS-02 · the fourth name, and it is an ABSENCE rather than a class.
# The cross-node rule needs the previous node's settled grid; the first node of a record has
# none. **It cannot be EFFECTIVE or FLASH and it must not be defaulted into SILENT either**,
# because SILENT is a positive statement — *this delivery committed nothing* — and the first
# node has not been asked. The three names above are unrenamed and unchanged in value.
UNCOMPARED = "UNCOMPARED"  # multi-grid, but no predecessor exists to compare against

# The caller-did-not-look sentinel. **NOT `None`** — `None` is a supplied answer meaning
# *there is no predecessor*, and the two absences are different facts. Collapsing them would
# make an un-updated caller silently claim first-node status on every turn.
_UNSET = object()


def animation_layers(frame) -> Optional[list]:
    """INGEST (D1): the full interior layer sequence — additive read.

    Returns ``frame.frame`` (layers x rows x cols) when present, else ``None``.
    This is the parallel accessor that retains what ``_grid_from_frame`` /
    ``_sync_library`` drop when they take ``frame[-1]``. Read only by the
    animation path in this module — never by the persistent / Mode-B path, which
    keeps its independent ``frame[-1]`` extraction (``virelai.py:737``). That
    disjointness is the WO-EYE-00 separation guarantee.

    Returns ``None`` on an empty sequence, mirroring ``_grid_from_frame``'s
    ``if frame.frame:`` guard (``virelai.py:94``) so the len==0 turn class is
    handled identically upstream and downstream.
    """
    layers = getattr(frame, "frame", None)
    if not layers:
        return None
    return layers


def _interior_change_magnitude(layers) -> int:
    """Total cells changed across consecutive layer transitions (pure measure).

    Sums the per-transition changed-cell count over every adjacent pair in the
    sequence. Zero for a single layer or a sequence that never moves. A
    structural pixel count — no world content. A shape change between adjacent
    layers counts as a full-grid change (the larger layer's cell count).
    """
    if layers is None or len(layers) < 2:
        return 0
    arrs = [np.asarray(layer, dtype=np.int32) for layer in layers]
    total = 0
    for a, b in zip(arrs[:-1], arrs[1:]):
        if a.shape == b.shape:
            total += int(np.count_nonzero(a != b))
        else:
            total += int(max(a.size, b.size))
    return total


def _differs(a, b) -> bool:
    """True iff two settled grids differ (structural).

    **EXTRACTED, NOT ADDED.** `_endpoints_differ` below already asked this question of one
    delivery's two ends; the cross-node rule asks the same question of two nodes' settled
    grids, and one comparator answering both is what keeps the two from drifting. Shape
    mismatch counts as different, exactly as it did."""
    x = np.asarray(a, dtype=np.int32)
    y = np.asarray(b, dtype=np.int32)
    if x.shape != y.shape:
        return True
    return bool(np.any(x != y))


def _endpoints_differ(layers) -> bool:
    """True iff the settled endpoints frame[0] and frame[-1] differ (structural)."""
    return _differs(layers[0], layers[-1])


def classify_press(layers, previous=_UNSET) -> Tuple[str, int]:
    """DETECT + CLASSIFY (D2): bin a turn's delivery, structurally.

    Returns ``(press_class, interior_magnitude)``.

    ════════════════════════════════════════════════════════════════════════════════════
    WO-DELIVERY-CLASS-02 · **THE COMPARISON MOVED ACROSS THE NODE BOUNDARY, AND THE OLD ONE
    WAS COMPARING THE WRONG TWO GRIDS.**

    This decided ``EFFECTIVE`` from ``frame[0] != frame[-1]`` — **within one delivery.** But
    ``frame[0]`` is not the board before the press; **it is already the first animation
    frame.** Quoting `WO_DELIVERY_CLASS_02` §0, which measured it on the embodied canary —
    **not measured here; Cowork runs no live game**: one animated node whose first and last
    layers differ by 76 cells, whose last layer is byte-identical to the previous node's
    settled grid. Nothing persistent happened, and it was labelled ``EFFECTIVE``. **Seven of
    ten animated nodes are mislabelled this way.** The correction below is structural and
    stands on its own; the figures are CE's grading pre-registration, not its warrant.

    The rule is now:

      EFFECTIVE   — the settled grid differs from the PREVIOUS NODE's settled grid; the
                    board is somewhere else than the last turn left it.
      FLASH       — the settled grids agree and the interior layers moved; the press
                    flashed and committed nothing.
      SILENT      — ``len <= 1`` (a delivery with no interior to adjudicate), or a
                    multi-grid delivery whose interior never moved.
      UNCOMPARED  — multi-grid, and there is no predecessor to compare against.

    **A SINGLE-GRID DELIVERY IS `SILENT` WHATEVER THE PREVIOUS NODE HELD, AND THAT IS A
    RULING RATHER THAN AN OVERSIGHT.** It has no interior excursion to adjudicate, so the
    cross-node question does not arise. Making it ``EFFECTIVE`` on a board change would turn
    this field into an OUTCOME — and `WO_ANIMATION_01` §P5, the field names it feeds, and
    the roster's own header all exist to keep it a statement about the DELIVERY.

    ════════════════════════════════════════════════════════════════════════════════════
    TWO ABSENCES, KEPT APART BY THE SIGNATURE.

      ``previous`` UNSUPPLIED — *the caller did not look.* Restores the intra-delivery
                    answer **exactly**, so `emit_animation_turn_diag`, the library path and
                    every existing assertion are byte-identical. A caller that has not been
                    updated cannot silently acquire a new semantics.
      ``previous=None`` — *the caller looked and there is no predecessor.* Yields
                    ``UNCOMPARED``.

    **Collapsing those two would make every un-updated call claim first-node status on every
    turn**, which is the absence-collapse this campaign has now corrected five times.

    Pure read — labels the turn, writes no belief.
    """
    if layers is None or len(layers) == 0:
        return SILENT, 0
    magnitude = _interior_change_magnitude(layers)
    if len(layers) <= 1:
        return SILENT, magnitude
    if previous is None:
        return UNCOMPARED, magnitude
    # **THE ONLY THING THIS RUNG CHANGED IS WHICH TWO GRIDS ARE COMPARED.** The verdict
    # below is the pre-existing one, written once: settled-moved is EFFECTIVE, and a
    # settled-still delivery is a FLASH if its interior moved and SILENT if it did not.
    # `magnitude > 0` is inherited, not introduced, and it appears exactly once (§4).
    settled_moved = (_endpoints_differ(layers) if previous is _UNSET
                     else _differs(previous, layers[-1]))
    if settled_moved:
        return EFFECTIVE, magnitude
    return (FLASH if magnitude > 0 else SILENT), magnitude


def scan_layers(layers) -> List[GridScan]:
    """Iterate interior layers through ``scan_grid`` per-layer (premise 2 proof).

    Each layer is a 2-D ``rows x cols`` grid the existing geometry stack
    processes unchanged — ``scan_grid`` is called per-layer and is NOT widened to
    accept the 3-D sequence. Pure read; returns one ``GridScan`` per layer.
    Demonstrates the iterate-don't-widen shape on real frames, not just fixtures.
    """
    if layers is None:
        return []
    return [scan_grid(np.asarray(layer, dtype=np.int32)) for layer in layers]


def emit_animation_turn_diag(frame, turn_index: int, previous=_UNSET) -> None:
    """EMIT (D3): per-turn animation classification to the diagnostic surface.

    **WO-DELIVERY-CLASS-02 · `previous` IS THE SECOND PRODUCER'S HALF OF THE AGREEMENT.**
    The weave-side class and this line are graded turn-for-turn, and they can only agree if
    both ask the same question. The caller hands the previous node's settled grid; supplying
    nothing keeps the anchor's intra-delivery answer, so a caller that has not been updated
    is byte-identical rather than silently re-classified.

    PURE READ — emits one JSON line to stderr only when ``VIRELAI_DIAG_DUMP=1``;
    mutates nothing (no belief, no context, no library, no input frame). Off by
    default, so the live path is byte-unchanged when not diagnosing. Rhymes with
    the E12 ``emit_counter_candidate_diag`` surface. Single responsibility: emit.

    Fields: turn index, sequence length, press class (FLASH/SILENT/EFFECTIVE),
    the interior-event magnitude (cells changed across interior layers), and the
    per-layer scan count (proof that ``has_animation_frames`` fired and each
    interior layer fed ``scan_grid`` unchanged on this real turn).
    """
    if os.environ.get("VIRELAI_DIAG_DUMP", "0") != "1":
        return
    layers = animation_layers(frame)
    seq_len = 0 if layers is None else len(layers)
    press_class, magnitude = classify_press(layers, previous)

    # Wire the detector at the turn boundary, then prove premise 2 on the real
    # frame: an animation turn (len > 1) feeds each interior layer through
    # scan_grid per-layer. Pure read; the count is the evidence the per-layer
    # geometry pass ran without widening the 2-D contract.
    layers_scanned = 0
    if has_animation_frames(layers or []):
        layers_scanned = len(scan_layers(layers))

    rec = {
        "tag": "EYE01-ANIM-DIAG",
        "turn": turn_index,
        "seq_len": seq_len,
        "press_class": press_class,
        "interior_magnitude": magnitude,
        "layers_scanned": layers_scanned,
    }
    print(json.dumps(rec), file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# WO_AR · D1 — transient-cell perception (pure, universal; no belief write)
# ---------------------------------------------------------------------------
# The transient witness: cells that move in the interior animation planes but
# return by the settled frame (frame[0] == frame[-1] at that cell). A cell that
# changed persistently within the turn (frame[0] != frame[-1]) is NOT transient-
# only — it is the settled reactive witness and belongs to the settled path,
# never here (baseline-mask pattern, KNOWLEDGE_TRANSFER:26). Kind-level only: no
# color/class/world/position constant; the descriptor reports witnessed counts,
# never an invented magnitude. ft09 is the canary; this is a universal capability.


def _changed_cells(a: np.ndarray, b: np.ndarray) -> Set[Tuple[int, int]]:
    """The set of (row, col) where two same-turn layers differ. A shape change
    between layers is a whole-grid excursion — count the union extent."""
    if a.shape != b.shape:
        h = max(a.shape[0], b.shape[0])
        w = max(a.shape[1], b.shape[1])
        return {(r, c) for r in range(h) for c in range(w)}
    return {(int(r), int(c)) for r, c in np.argwhere(a != b)}


def transient_only_cells(layers) -> Tuple[FrozenSet[Tuple[int, int]], Dict[str, object]]:
    """D1: per-turn transient-only changed cells + a kind-level expression descriptor.

    A cell is transient-only iff it changed somewhere in the interior sequence
    AND the settled endpoints agree there (``frame[0] == frame[-1]`` at the cell)
    — it flashed and reverted. Cells that ended changed (the persistent, settled
    reactive witness) are subtracted out: they are not this witness's business.

    Returns ``(cells, descriptor)`` where descriptor is
    ``{"kind": "flash"|None, "layers": N, "steps": S, "cells": C}`` — S is the
    number of interior transitions that moved (the excursion's step tally), all
    derived from witnessed frames, nothing invented. A single-layer (or empty)
    frame yields ``(frozenset(), kind=None)``: no animation, no witness.
    """
    n = 0 if layers is None else len(layers)
    empty = {"kind": None, "layers": n, "steps": 0, "cells": 0}
    if layers is None or n <= 1:
        return frozenset(), empty

    arrs = [np.asarray(layer, dtype=np.int32) for layer in layers]
    settled = _changed_cells(arrs[0], arrs[-1])   # persistent this turn — excluded
    moved: Set[Tuple[int, int]] = set()
    steps = 0
    for prev, cur in zip(arrs[:-1], arrs[1:]):
        step_cells = _changed_cells(prev, cur)
        if step_cells:
            steps += 1
            moved |= step_cells

    transient = frozenset(moved - settled)
    desc = {
        "kind": "flash" if transient else None,
        "layers": n,
        "steps": steps,
        "cells": len(transient),
    }
    return transient, desc
