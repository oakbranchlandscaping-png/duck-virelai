"""WO-CC-S1-SEAL · CAPTURE round-trip verifier — the scipy/arcengine-free core
of the ``--capture-verify`` seal hook.

Given a live ``FrameRecordLog`` and the frames actually handed to the agent per
node, it asserts the Stage-1 seal criterion read-only and emits a verdict block:

  for every node i in 0..N-1:
    - log.reconstruct(i) == the frame.frame handed at node i (ALL layers, byte-equal)
    - node_index monotonic 0..N-1
    - layered_hash non-empty and stable (matches a re-hash of the stored layers)
  node-0 edge is None, and the first node of each life carries edge is None —
  counted and reported, never failed on (per the WO-CC-S1 return's honesty flag).

Game-free and dependency-light: stdlib + the capture module's own hash helper.
Never writes belief/dispatch; compares the log against the locally-captured
handed frames, not against itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple

from virelai_v4.capture.frame_record import _freeze_layers, _hash_layers


@dataclass(frozen=True)
class CaptureVerifyResult:
    """Outcome of the round-trip verification over one run's capture log."""

    n_nodes: int
    n_pass: int
    k_edge_none: int
    # (node_index, human-readable first-divergence detail) or None if all pass.
    first_fail: Optional[Tuple[int, str]]


def _first_layer_diff(expected: Any, got: Any) -> str:
    """Locate the first differing (layer, row, col) between two 3D grids, or a
    shape-mismatch description. ``expected`` = handed frame, ``got`` = reconstruct."""
    if len(expected) != len(got):
        return f"layer count: expected {len(expected)}, got {len(got)}"
    for li, (elayer, glayer) in enumerate(zip(expected, got)):
        if len(elayer) != len(glayer):
            return f"layer {li} row count: expected {len(elayer)}, got {len(glayer)}"
        for ri, (erow, grow) in enumerate(zip(elayer, glayer)):
            if len(erow) != len(grow):
                return f"layer {li} row {ri} width: expected {len(erow)}, got {len(grow)}"
            for ci, (ev, gv) in enumerate(zip(erow, grow)):
                if ev != gv:
                    return f"layer {li} row {ri} col {ci}: expected {ev}, got {gv}"
    return "no cell diff (equal)"


def verify_roundtrip(
    log: Any, handed_frames: Sequence[Any]
) -> CaptureVerifyResult:
    """Verify the capture log round-trips to the frames handed during the run.

    ``log`` is a ``FrameRecordLog`` (duck-typed: ``.records`` + ``.reconstruct``);
    ``handed_frames`` is the list of ``latest_frame.frame`` (3D layer stacks)
    captured by the observer, one per node, index-aligned with the log.
    """
    records = list(log.records)
    n_nodes = len(records)
    n_pass = 0
    k_edge_none = 0
    first_fail: Optional[Tuple[int, str]] = None

    if len(handed_frames) != n_nodes:
        first_fail = (
            min(len(handed_frames), n_nodes),
            f"length mismatch: log has {n_nodes} records, "
            f"observer handed {len(handed_frames)} frames",
        )

    for i, record in enumerate(records):
        if record.edge is None:
            k_edge_none += 1

        node_ok = True
        detail = ""

        # Monotonic node_index.
        if record.node_index != i:
            node_ok = False
            detail = f"node_index {record.node_index} != position {i}"

        # layered_hash non-empty and stable (re-hash the stored payload).
        elif not record.layered_hash or record.layered_hash != _hash_layers(record.layers):
            node_ok = False
            detail = "layered_hash empty or does not match stored layers"

        # Round-trip: reconstruct(i) == the handed frame (all layers, byte-equal).
        elif i < len(handed_frames):
            reconstructed = log.reconstruct(record.node_index)
            handed = _thaw(handed_frames[i])
            if reconstructed != handed:
                node_ok = False
                detail = _first_layer_diff(handed, reconstructed)
        else:
            node_ok = False
            detail = "no handed frame captured for this node"

        if node_ok:
            n_pass += 1
        elif first_fail is None:
            first_fail = (i, detail)

    return CaptureVerifyResult(
        n_nodes=n_nodes,
        n_pass=n_pass,
        k_edge_none=k_edge_none,
        first_fail=first_fail,
    )


def _thaw(frame_layers: Any) -> List[List[List[int]]]:
    """Normalize a handed 3D grid to nested int lists for byte-equal compare —
    the same normalization ``reconstruct`` applies to the stored payload."""
    return [[[int(c) for c in row] for row in layer] for layer in (frame_layers or [])]


def format_verdict(result: CaptureVerifyResult) -> str:
    """The verdict block printed at the post-loop seal site."""
    if result.first_fail is None and result.n_pass == result.n_nodes:
        return (
            f"CAPTURE-VERIFY: {result.n_nodes} nodes, "
            f"{result.n_pass} round-trip PASS, "
            f"{result.k_edge_none} life-boundary edge=None"
        )
    node, detail = result.first_fail if result.first_fail else (-1, "unknown")
    return (
        f"CAPTURE-VERIFY: FAIL at node {node} — {detail}. "
        f"({result.n_pass}/{result.n_nodes} nodes passed, "
        f"{result.k_edge_none} life-boundary edge=None)"
    )


_SEAL_HEADER = (
    "\n########## CAPTURE-VERIFY — Stage-1 round-trip seal "
    "(--capture-verify) ##########"
)


@dataclass(frozen=True)
class SealDecision:
    """What the seal block should do on one ``cleanup`` call.

    action:
      - ``noop``    — flag off or already verified; do nothing.
      - ``fire``    — data complete; print ``output`` and latch.
      - ``defer``   — data incomplete on a non-final call; wait for a later one.
      - ``skipped`` — data still incomplete on the FINAL call; print the explicit
                      SKIPPED line and latch. Never silent.
    """

    action: str
    output: Optional[str]
    latch: bool


def evaluate_seal(
    *,
    capture_verify: bool,
    already_verified: bool,
    handed_frames: Sequence[Any],
    log: Any,
    is_final_call: bool,
) -> SealDecision:
    """Pure seal decision for one ``cleanup`` call — no printing, no state write.

    Fires once, only on a COMPLETE record (``handed_frames`` non-empty and
    length-matched to the log). On an incomplete non-final call it defers; on an
    incomplete FINAL call it emits an explicit SKIPPED line rather than going
    silent (silence is the defect WO_CC_S1_SEAL_DIAG diagnosed). The caller
    prints ``output`` (if any) and sets its once-flag when ``latch`` is True.
    """
    if not capture_verify or already_verified:
        return SealDecision("noop", None, False)

    n_handed = len(handed_frames)
    n_log = len(log) if log is not None else 0
    complete = n_handed > 0 and log is not None and n_log == n_handed

    if complete:
        verdict = format_verdict(verify_roundtrip(log, handed_frames))
        return SealDecision("fire", f"{_SEAL_HEADER}\n{verdict}", True)

    if is_final_call:
        return SealDecision(
            "skipped",
            f"{_SEAL_HEADER}\nCAPTURE-VERIFY: SKIPPED — record incomplete "
            f"(handed={n_handed}, log={n_log})",
            True,
        )

    return SealDecision("defer", None, False)
