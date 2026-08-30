"""WO_LEDGER_ENTRY_POINT v2 · the capture -> ledger ASSEMBLY module.

The committed production entry-point that turns an on-disk / in-memory capture
into a graded Sighting Ledger. It is the perception-DEPENDENT step (it runs
``scan_grid``), so by CE ruling it lives OUTSIDE the perception-free compile
layer (``clay.py`` / ``ledger.py``, fenced by
``tests/capture/test_ledger.py::test_ledger_and_clay_are_interpretation_free``)
and here instead — mirroring how ``diagnostics/render_stages`` already holds the
loop, but now as committed surface R2 can build on.

Layering (locked by ``tests/capture/test_ledger_build.py``):
  - PERCEPTION-ALLOWED: this module MAY import ``perception.grid_scan`` / scipy.
  - INTERPRETATION-FORBIDDEN: it must NOT import ``library``, ``captain``,
    ``targeting``, ``nested_read``, ``render_read``, ``classification``, or
    ``virelai.virelai``. It assembles the given into cuts; it decides nothing,
    matches nothing, classifies nothing (that is R2).

It introduces NO new algorithm. ``ledger_from_capture`` is the verbatim loop
proven at ``render_stages.py:301-311`` (and in the WO v1 scratch harness); its
output is byte-identical to that chain for the same log.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, List, Tuple

import numpy as np

from virelai_v4.capture.frame_record import FrameRecordLog
from virelai_v4.capture.clay import RegionClay, NodeCut, _hash_visible
from virelai_v4.perception.animation import _UNSET, classify_press
from virelai_v4.perception.grid_scan import scan_grid


def delivery_of(layers, previous=_UNSET) -> "Tuple[int, str, int]":
    """`(layer count, delivery class, interior magnitude)` for one turn's delivery.

    **THE ONE PRODUCER, AND IT WRAPS THE COMMITTED CLASSIFIER RATHER THAN REIMPLEMENTING
    IT.** `perception.animation.classify_press` is PRODUCTION_LIVE, universal, and has been
    reading interior layers since WO-EYE-01 — what it has never had is a consumer on the
    path the golden run is graded from. **Two spellings of one classification is how the
    weave-side line and the diagnostic's line come to disagree**, and that disagreement is
    graded explicitly, so there is exactly one spelling and every site calls it.

    **THIS MODULE IS THE RIGHT HOME AND `clay.py` IS NOT.** `clay.py` is stdlib-only and its
    own locking test forbids `grid_scan`; `perception.animation` imports `grid_scan`. This
    module's header declares it perception-ALLOWED and interpretation-FORBIDDEN, and a
    structural classification of a delivery decides nothing about the world — §P2.

    **WHAT IT IS NOT.** `classify_press` returns `SILENT` whenever `len(layers) <= 1`,
    before comparing anything to a prior board, and `_endpoints_differ` compares the first
    and last layer of ONE delivery and never sees the previous node. **It classifies the
    DELIVERY, not the outcome** — a single-layer turn that moved the ego reads `SILENT`.
    Every name this returns into is `delivery_*` for that reason.

    **ABSENCE IS ABSENCE, AND THERE ARE NOW TWO OF THEM.** `layers is None` — the caller has
    no layers rather than zero layers — yields the not-observed triple, which is what an
    un-looked-at cut carries by default. And `previous` carries the second: **unsupplied**
    means the caller did not look for a predecessor and restores the intra-delivery answer;
    **`None` supplied** means the caller looked and there is none, which is the first node of
    a record and yields `UNCOMPARED`. `WO-DELIVERY-CLASS-02` — the two are different facts
    and the signature keeps them apart."""
    if layers is None:
        return -1, "", -1
    press_class, magnitude = classify_press(layers, previous)
    return len(layers), press_class, int(magnitude)


def deliveries_of(log) -> "List[Tuple[int, int, str, int]]":
    """`(node_index, layer count, class, magnitude)` per node — the render's whole input.

    **THE GATHERING LIVES BESIDE THE PRODUCER; THE RENDERER ONLY FORMATS.** The delivery
    roster is drawn by `diagnostics.integration_roster`, whose own locking test holds it to
    stdlib plus `capture.clay` — *"what lets this diagnostic run where the SDK and scipy are
    absent."* This module imports scipy through `grid_scan`, so handing it the log directly
    would break the renderer in exactly the environment it was built for. **The caller
    computes and passes values in** — the same ruling `visible_hash` and `grid_shape`
    already follow into `NodeCut.from_record`.

    Absence is absence: no log, or an empty one, yields no rows."""
    if log is None or not len(log):
        return []
    rows = []
    _previous_settled = None          # the first node has no predecessor, and says so
    for rec in log.records:
        _delivered = log.reconstruct(rec.node_index)
        rows.append((int(rec.node_index),) + delivery_of(_delivered, _previous_settled))
        _previous_settled = _delivered[-1]
    return rows


def regions_of(grid) -> "Tuple[RegionClay, ...]":
    """The visual objects on ONE grid — the scan, with ONE producer.

    **EXTRACTED BY WO-BUDGET-OUT-01, NOT ADDED.** This line stood inline inside
    `ledger_from_capture`'s per-record loop, which walks the WHOLE log. The stillness
    read needs the same scan on ONE fresh frame, and duplicating the expression would
    have made a second producer of *the regions of a grid* — the drift shape
    `WO-EGO-SET-01` spent a rung closing. Both callers now run this."""
    return tuple(RegionClay.from_region(r) for r in scan_grid(grid).regions)


def regions_at(log, node_index) -> "Tuple[RegionClay, ...]":
    """The visual objects on the VISIBLE layer of ONE node, freshly reconstructed.

    **O(1) IN THE LOG, WHICH IS THE WHOLE POINT.** `ledger_from_capture` walks every
    record and costs O(n) — measured at 6098 ms for one refresh over 132 records, which
    is why `coverage_sweep`'s cadence gate exists. This reconstructs and scans ONE frame.
    It answers a question about PRESENCE, never about identity: identity is a path
    through a window (`worldline.weave_window`) and cannot be had at this price."""
    return regions_of(np.array(log.reconstruct(node_index)[-1], dtype=np.int32))


def ledger_from_capture(log: FrameRecordLog) -> List[NodeCut]:
    """Compile a capture log into the per-node cut list — the Sighting Ledger's
    object substrate. Verbatim the proven loop (``render_stages.py:301-311``):
    per record, reconstruct the visible grid, ``scan_grid`` it, wrap each region
    as a geometry-only ``RegionClay``, and assemble a ``NodeCut`` addressed on the
    VISIBLE-grid hash. No matching, no classification, no belief write.

    ``log`` is a ``FrameRecordLog`` (duck-typed ``.records`` + ``.reconstruct``).
    Returns the cuts in record order; feed straight to
    ``ledger.grade_pristine(cuts, log)`` for the fidelity gate.
    """
    cuts: List[NodeCut] = []
    # WO-DELIVERY-CLASS-02 · the previous node's SETTLED grid, carried one iteration.
    # `log.records` is documented "in order" and the walk is sequential, so node t-1's
    # settled grid is in hand when node t is classified — no second pass, no lookahead.
    # **`None` on the first node is supplied deliberately**: it says a predecessor does not
    # exist, which is not the same as a caller that did not look.
    _previous_settled = None
    for rec in log.records:
        # WO-ANIMATION-01 · **THE LIST IS BOUND ONCE AND `[-1]` IS UNMOVED.** The settled
        # path is byte-identical: the same reconstruct, the same last element, one name
        # earlier. The delivery is classified from the SAME list — no second read of the
        # record, and no change to what the visible layer is.
        _delivered = log.reconstruct(rec.node_index)
        visible = _delivered[-1]                               # the visible layer
        grid = np.array(visible, dtype=np.int32)
        regions = regions_of(grid)
        _n, _cls, _mag = delivery_of(_delivered, _previous_settled)
        _previous_settled = visible
        cut = NodeCut.from_record(
            rec, regions,
            visible_hash=_hash_visible(visible),
            grid_shape=(int(grid.shape[0]), int(grid.shape[1])),
            delivery_layers=_n, delivery_class=_cls, delivery_magnitude=_mag,
        )
        cuts.append(cut)
    return cuts


def load_capture(recording_path: str) -> FrameRecordLog:
    """Build a ``FrameRecordLog`` from an official ``*.recording.jsonl`` OFFLINE.

    Each line is ``{"timestamp", "data"}``; ``data`` already carries the given the
    committed recorder reads (``frame``/``state``/``available_actions``/
    ``full_reset``/``game_id``/``guid``/``levels_completed``/``win_levels``/
    ``action_input``). Each framed line is wrapped in a frame-like namespace and
    handed to the COMMITTED ``FrameRecordLog.append`` -> ``CaptureRecord.from_frame``
    path (frame layers passed through verbatim); the log owns ``node_index``.
    Non-framed lines are skipped. Deterministic; never runs the game live.

    WO-A2-03 Part 2 — THE ACTION IS ROUTED THROUGH ``_parse_action``.
    Previously this passed the raw ``action_input`` dict straight to ``append``.
    That dict is the harness placeholder — ``{'id': 0, 'data': {}, 'reasoning':
    None}`` on every framed line of every recording. It is not ``None``, so
    ``from_frame`` ran ``_norm_key(action)``; a dict is not a tuple, so
    ``_norm_key`` returned ``(action_id, target)`` with THE WHOLE DICT in the
    ``action_id`` slot:

        edge == ({'id': 0, 'data': {}, 'reasoning': None}, None)

    on every node, silently, and ``load_node_actions_from_log`` over an offline
    capture yielded a dict where the contract says int. ``_parse_action`` lived
    in this file, unused, written for exactly this, and was bypassed.

    Routed, the edge is an HONEST ``(0, None)``: action-id-0, no target. It can
    never be INFORMATIVE — ``virelai.py`` already names the ``.recording.jsonl``
    "action-blind"; the placeholder is the harness's design and no recording will
    ever carry the real action. It can be honest. A consumer that needs the
    action must read the live log; an offline capture must be able to SAY it
    cannot see, rather than return a dict-shaped lie.
    """
    log = FrameRecordLog()
    with open(recording_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line).get("data", {})
            if not isinstance(data, dict) or "frame" not in data or not data["frame"]:
                continue
            aid, target = _parse_action(data.get("action_input"))
            action = (aid, target) if aid is not None else None
            log.append(SimpleNamespace(**data), action=action)
    return log


def _parse_action(action_input) -> "Tuple[Any, Any]":
    """Extract ``(action_id, target_cell)`` from a recorded ``action_input``.

    ``action_id`` = the integer action id. ``target_cell`` = ``(row, col)`` for an
    ACTION6 CLICK carrying coordinates (per ``contracts/probe_event.py:64``:
    "(row, col) for ACTION6 clicks; None for directional"), else ``None``.

    CONVENTION (documented): the recorded ``action_input`` is the action that
    PRODUCED this frame — the INBOUND action (matches ``CaptureRecord.edge``, "the
    inbound edge"). So ``action_id[node t]`` is the action that produced the
    transition INTO node t.

    CAVEAT — the recording's click-coordinate schema is UNVERIFIABLE on the click
    canary (its whole corpus is action id=0, no clicks). The ACTION6 ``data``
    mapping below ({x: col, y: row} -> (row, col)) follows the (row, col) contract
    but has not been exercised on a real click recording; the Director must
    confirm it against a click-bearing capture. Non-click actions are unaffected
    (target None).

    WO-A2-07 — THE BARE-INT SHAPE. ``action_input`` has two legal forms and this
    parser only knew one. ``_norm_key`` (state_tracker.py) documents both: "a bare
    int -> (int, None); an already-composite (action_id, target) tuple passes
    through unchanged." Pre-A2-03, ``load_capture`` handed ``action_input`` to
    ``_norm_key`` raw, so a bare int became a real edge for free. Routing through
    this parser — correct, and the fix the induced map's author asked for — moved
    the input through a ``not isinstance(dict)`` guard that answered ``(None,
    None)``, i.e. "no action," i.e. a ROOT. Every offline edge died.

    ACTION-BLINDNESS IS A FACT ABOUT THE HARNESS'S OUTPUT, NEVER A POLICY THIS
    LOADER IMPOSES. The placeholder dict yields the honest ``(0, None)`` because
    that is what the harness wrote; a genuine action id yields a genuine edge
    because that is what the harness wrote. Both are the same rule: parse what is
    there. This parser now covers both shapes ``_norm_key`` always did.
    """
    if isinstance(action_input, int) and not isinstance(action_input, bool):
        return (action_input, None)          # the bare-int form (_norm_key's "bare int")
    if isinstance(action_input, tuple) and len(action_input) == 2:
        return (action_input[0], action_input[1])   # already-composite, passed through
    if not isinstance(action_input, dict):
        return (None, None)
    aid = action_input.get("id")
    data = action_input.get("data") or {}
    target = None
    if isinstance(data, dict) and ("x" in data and "y" in data):
        try:
            target = (int(data["y"]), int(data["x"]))     # (row, col)
        except (TypeError, ValueError):
            target = None
    elif isinstance(data, dict) and ("row" in data and "col" in data):
        try:
            target = (int(data["row"]), int(data["col"]))
        except (TypeError, ValueError):
            target = None
    return (aid, target)


def load_node_actions_from_log(log: "Any") -> "List[Tuple[Any, Any]]":
    """WO-R1-02c — per-node ``(action_id, target_cell)`` read from the LOG ITSELF.

    The weave's action intake. Returns the same shape as the sidecar loader, so it
    is a pure source swap behind the ``node_actions`` contract that
    ``acted_on``/``build_coupling``/``infer_roles`` consume.

    Why the log and not the sidecar (WO-R1-02b): the ``.actions.jsonl`` sidecar is
    CLICK-ONLY (the choke point early-returns on every non-ACTION6) and keys on a
    PER-LIFE counter, while ``cuts`` are dense and accumulate — a sparse source and
    a dense one that no index key reconciles. That hazard was documented as an
    assumption ("true on the pinned canary, which has zero skipped lines") — and
    WO-A2-01..04 measured it: the canary was the WORST case, not the safe one
    (1222 of 1366 rows destroyed). The sidecar readers are retired; this is the
    only action reader. See the retired-terms register for the full derivation.

    The log has no such gap. Each record IS its node, and carries BOTH halves of
    the inbound action: ``edge`` = (action_id, region) for identity, and
    ``acted_cell`` = the (row, col) the solver acted on. Entry *t* is node *t* by
    construction — the index rule (``action_roster.action_node_indices``: a record
    for node ``t`` carries the action that produced ``t``) is satisfied natively,
    with no re-derivation and nothing to misalign. The root node has no producing
    action → ``(None, None)``.

    Dense over EVERY action type: a directional's ``(action_id, None)`` reaches the
    weave here, which the click-only sidecar could never express — and which
    ``has_directional`` (EGO's evidence) requires.
    """
    out: List[Tuple[Any, Any]] = []
    for rec in getattr(log, "records", ()) or ():
        edge = getattr(rec, "edge", None)
        aid = edge[0] if edge else None
        out.append((aid, getattr(rec, "acted_cell", None)))
    return out


# ---------------------------------------------------------------------------
# WO-A2-04 — THE SIDECAR READERS ARE RETIRED. Deleted here, in the same commit
# that lands their successors:
#     load_node_actions · load_node_actions_from_sidecar · load_node_action_records
#     _sidecar_path · _framed_node_count · _coord_cell
#     _RECORDING_SUFFIX · _ACTION_LOG_SUFFIX
#
# Not dead code — a ruled retirement. The sidecar's rows keyed on `frame_index`
# (== ctx.actions_this_life, PERSIST_LEVELS_RESET_LIFE) while the node array is
# ctx.frame_record_log (PERSIST_LIVES_RESET_LEVEL). No field in the record sat at
# the node array's lifetime tier: one key reset too often, the other never reset.
# There was never an index rule to find. Measured on the live canary at ecee9d0:
# 1222 of 1366 rows destroyed by last-write-wins; 1265 of 1322 nodes wrong under
# BOTH candidate keys; `global_action_idx` perfectly injective and worse than the
# key it would have replaced.
#
# The derivation that installed them (WO_ACTION_INGEST_R1 — a correct diagnosis
# of the placeholder, a grader-RED-first swap, a green floor, and a single-life
# fixture that could not have exposed a life-keyed collision) is preserved in the
# retired-terms register, so no future chamber re-swaps to the sidecar on finding
# `(0, None)` "uninformative" again.
#
# `load_node_actions_from_log` above is the ruled reader: entry t IS node t,
# dense over every action type, no key, nothing to misalign.
# `_parse_action` survives — it was never wrong, only never called; `load_capture`
# now routes through it.
# ---------------------------------------------------------------------------
