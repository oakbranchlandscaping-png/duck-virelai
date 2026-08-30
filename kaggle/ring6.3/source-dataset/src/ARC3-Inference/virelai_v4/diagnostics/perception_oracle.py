"""
virelai_v4/diagnostics/perception_oracle.py — WO-3 perception-oracle
(Campaign A · rung 3).

Grades the PERCEPTION stage against the vc33 `.json` replay oracle and renders
the instrument's own oracle-expected / perception-observed / verdict triple
onto the rung-1 perception panel — read-only.

TWO-ORACLE BOUNDARY (load-bearing, charter §3): this oracle grades PERCEPTION
ONLY (intake, individuation, delta). It NEVER grades the model. The grade-time
triple is the instrument's own — generated here against the key — NOT a read
of any solver falsification log (the kernel is specified-not-built).

NON-CIRCULARITY (charter §6.3 / H2):
  - intake : graded against the raw ground-truth grid the replay delivered —
             independent of perception's algorithm.
  - delta  : expected = cell-difference of consecutive raw oracle grids,
             computed HERE from the grids — independent of perception's delta
             computation. A divergence is meaningful (e.g. perception's HUD
             masking or transform), rendered honestly (fidelity, not agreement).
  - individuation : the replay carries NO independent object segmentation, and
             no external individuation key exists in the corpus. Grading
             perception's segmentation against perception's own segmenter would
             be circular, so individuation is rendered NOT_GRADED with the
             reason stated. (H2 REFINED boundary — recorded, not faked.)

SCOPE: no downstream grading (rung 4), no model cross-grade, no fault
localization, no belief write, no solver-log read, no edit to
compose_frame_event / per_stage_render bodies (this module composes over
render_perception read-only).

NOTE on live vs sandbox: producing real perception-observed over the vc33
replay requires reconstructing the agent context (probe target + library) by
replaying the live agent, which needs the ARC SDK — the Director's live render
(§4b). In the sandbox the grader logic is exercised on constructed perception
events. The oracle grids themselves are sandbox-accessible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Optional

import numpy as np

from virelai_v4.diagnostics.per_stage_render import render_perception

# The three perception aspects this oracle may speak to — and ONLY these.
PERCEPTION_ASPECTS = ("intake", "individuation", "delta")

_INDIVIDUATION_NOT_GRADED_REASON = (
    "no independent individuation key in the oracle; grading perception's "
    "segmentation against its own segmenter would be circular (H2 boundary)"
)


# ---------------------------------------------------------------------------
# Oracle loading (sandbox-accessible: raw ground-truth grids from the replay)
# ---------------------------------------------------------------------------

def _extract_grid(frame: Any) -> Optional[np.ndarray]:
    """A frame may be [[...grid...]] (the recorder's outer-list wrapper) or a
    bare [[...grid...]] 2-D grid. Return the 2-D grid or None."""
    if not isinstance(frame, list) or not frame:
        return None
    # outer-list wrapper: frame[0] is the 2-D grid
    if isinstance(frame[0], list) and frame[0] and isinstance(frame[0][0], list):
        return np.asarray(frame[0])
    # bare 2-D grid
    if isinstance(frame[0], list) and frame[0] and isinstance(frame[0][0], int):
        return np.asarray(frame)
    return None


def load_oracle_frames(path: str) -> List[np.ndarray]:
    """Return the replay's ground-truth grids in order. Pure read.

    Adapts to the repo's official replay format (the Recorder / Playback
    schema, Mine-Then-Reuse):
      - `.recording.jsonl` — one JSON object per line, the frame at
        line["data"]["frame"] (outer-list wrapper). Empty/headerless lines
        skipped.
      - a `.json` official replay — a top-level JSON array of frame events,
        or {"frames": [...]} / {"recording": [...]}; each element is either a
        frame event ({"data": {"frame": ...}} or {"frame": ...}) or a bare
        grid. This branch lets the Director drop an official `.json` replay and
        have the oracle adapt with no code change.
    """
    grids: List[np.ndarray] = []

    def _consume(event: Any) -> None:
        if isinstance(event, dict):
            frame = event.get("frame")
            if frame is None and isinstance(event.get("data"), dict):
                frame = event["data"].get("frame")
        else:
            frame = event  # bare grid element
        g = _extract_grid(frame)
        if g is not None:
            grids.append(g)

    if path.endswith(".json"):
        with open(path) as fh:
            doc = json.load(fh)
        events = doc
        if isinstance(doc, dict):
            events = doc.get("frames") or doc.get("recording") or []
        for event in (events or []):
            _consume(event)
    else:  # .jsonl (the recorder's official line format)
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                _consume(json.loads(line))

    return grids


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

# Verdict vocabulary:
#   MATCH / MISMATCH  — graded against the external oracle (IN_TAPE frame).
#   NOT_MEASURED      — perception claimed no per-press delta this frame
#                       (OUT_OF_TAPE) or no prior oracle frame — P7. Distinct
#                       from MISMATCH (we do not grade what perception did not
#                       measure).
#   NOT_GRADED        — no external oracle present (P8), or individuation
#                       (no independent key).

@dataclass(frozen=True)
class PerceptionVerdict:
    """The instrument's own grade-time triple for one perception aspect."""
    aspect: str            # one of PERCEPTION_ASPECTS
    expected: Any          # oracle-expected (None when not graded)
    observed: Any          # perception-observed (None when not measured)
    verdict: str           # MATCH / MISMATCH / NOT_MEASURED / NOT_GRADED
    reason: str = ""       # populated for NOT_MEASURED / NOT_GRADED


def observed_delta_from_context(context: Any) -> Optional[int]:
    """Perception's OWN frame-time delta — ctx.frame_delta.total_changed,
    computed in _perceive() against the pre-advance prev_grid (virelai.py:~580)
    BEFORE prev_grid is advanced to the current frame (virelai.py:600).

    This is the correct perception-observed whole-frame delta. The out-of-band
    diagnostic must NOT recompute it via compose_frame_event, which reads
    ctx.prev_grid AFTER _perceive advanced it (== current frame) and so yields
    0 (frame-vs-itself). Same quantity, correct source. Pure read."""
    fd = getattr(context, "frame_delta", None)
    if fd is None:
        return None
    tc = getattr(fd, "total_changed", None)
    return int(tc) if tc is not None else None


def grade_intake(oracle_grid: np.ndarray,
                 observed_grid: Optional[np.ndarray]) -> PerceptionVerdict:
    """Did perception take in the grid the replay actually delivered?
    Summarised by shape + changed-cell count so the triple is legible."""
    if observed_grid is None:
        return PerceptionVerdict("intake", _grid_summary(oracle_grid), None,
                                 "NOT_MEASURED", "no observed grid")
    og = np.asarray(oracle_grid)
    ob = np.asarray(observed_grid)
    match = og.shape == ob.shape and bool(np.array_equal(og, ob))
    return PerceptionVerdict(
        "intake", _grid_summary(og), _grid_summary(ob),
        "MATCH" if match else "MISMATCH",
    )


def grade_delta(oracle_prev: Optional[np.ndarray], oracle_cur: np.ndarray,
                observed_delta_cells: Optional[int],
                in_tape: bool) -> PerceptionVerdict:
    """Cell-by-cell (P6): oracle-expected = count of cells differing between
    file[N-1] and file[N] — the transition perception measured. P7: grade only
    what perception claims — an OUT_OF_TAPE frame (no per-press delta) is
    NOT_MEASURED, never a MISMATCH."""
    if not in_tape:
        return PerceptionVerdict("delta", None, None, "NOT_MEASURED",
                                 "out-of-tape (no probed press this frame)")
    if oracle_prev is None:
        return PerceptionVerdict("delta", None, observed_delta_cells,
                                 "NOT_MEASURED", "no prior oracle frame")
    expected = int(np.count_nonzero(np.asarray(oracle_prev)
                                    != np.asarray(oracle_cur)))
    if observed_delta_cells is None:
        return PerceptionVerdict("delta", expected, None, "NOT_MEASURED",
                                 "perception reported no frame delta")
    observed = int(observed_delta_cells)
    return PerceptionVerdict(
        "delta", expected, observed,
        "MATCH" if expected == observed else "MISMATCH",
    )


def grade_individuation() -> PerceptionVerdict:
    """No independent key exists — rendered NOT_GRADED, honestly (not faked)."""
    return PerceptionVerdict("individuation", None, None, "NOT_GRADED",
                             _INDIVIDUATION_NOT_GRADED_REASON)


def grade_perception_frame(
    oracle_prev: Optional[np.ndarray],
    oracle_cur: np.ndarray,
    perception_event: Optional[dict],
    observed_grid: Optional[np.ndarray],
    observed_delta: Optional[int] = None,
) -> List[PerceptionVerdict]:
    """The full perception triple for one frame: intake, individuation, delta.

    perception_event is the rung-1 perception payload (its 'status' gates P7);
    observed_grid is the grid perception took in; observed_delta is perception's
    OWN frame-time delta (ctx.frame_delta.total_changed — see
    observed_delta_from_context). Pure, deterministic, read-only."""
    in_tape = (perception_event or {}).get("status") == "IN_TAPE"
    return [
        grade_intake(oracle_cur, observed_grid),
        grade_individuation(),
        grade_delta(oracle_prev, oracle_cur, observed_delta, in_tape),
    ]


# ---------------------------------------------------------------------------
# Graded render (extends the rung-1 perception panel; read-only)
# ---------------------------------------------------------------------------

def _grid_summary(grid: np.ndarray) -> str:
    g = np.asarray(grid)
    bg = int(np.bincount(g.ravel()).argmax()) if g.size else 0
    return f"{g.shape[0]}x{g.shape[1]}, {int(np.count_nonzero(g != bg))} non-bg cells"


def _verdict_line(v: PerceptionVerdict) -> str:
    if v.verdict in ("NOT_GRADED", "NOT_MEASURED"):
        return f"{v.aspect}: {v.verdict} — {v.reason}"
    return (f"{v.aspect}: {v.verdict} "
            f"(oracle-expected={v.expected!r} | observed={v.observed!r})")


_NO_ORACLE_REASON = "no external oracle (--oracle absent); P8 — verdicts " \
                    "require the official replay, never the solver's own grids"


def render_perception_graded(
    context: Any,
    grid: Optional[np.ndarray],
    oracle_prev: Optional[np.ndarray],
    oracle_cur: Optional[np.ndarray],
) -> str:
    """Render the rung-1 perception panel, then the graded triple.

    P8: when oracle_cur is None (no external oracle), the WHOLE graded panel is
    NOT_GRADED (no external oracle) — there is no grade against the solver's own
    grids. Otherwise grade intake/delta against the external oracle, with
    perception-observed delta sourced from ctx.frame_delta (frame-time, correct)
    — never recomputed against the advanced prev_grid.

    Read-only: render_perception is the rung-1 read; the grade reads the oracle
    grids + perception's recorded delta; nothing is written."""
    observed = render_perception(context, grid)
    lines = ["=== PERCEPTION (graded vs external oracle) ==="]
    lines.append(f"  observed: {observed}")
    lines.append("  --- oracle triple (perception only; two-oracle boundary) ---")

    if oracle_cur is None:                                   # P8
        for aspect in PERCEPTION_ASPECTS:
            reason = (_INDIVIDUATION_NOT_GRADED_REASON
                      if aspect == "individuation" else _NO_ORACLE_REASON)
            lines.append(f"  {aspect}: NOT_GRADED — {reason}")
        return "\n".join(lines)

    verdicts = grade_perception_frame(
        oracle_prev, oracle_cur, observed,
        np.asarray(grid) if grid is not None else None,
        observed_delta=observed_delta_from_context(context),
    )
    for v in verdicts:
        lines.append(f"  {_verdict_line(v)}")
    return "\n".join(lines)


__all__ = [
    "PERCEPTION_ASPECTS",
    "PerceptionVerdict",
    "load_oracle_frames",
    "grade_intake",
    "grade_delta",
    "grade_individuation",
    "grade_perception_frame",
    "render_perception_graded",
]
