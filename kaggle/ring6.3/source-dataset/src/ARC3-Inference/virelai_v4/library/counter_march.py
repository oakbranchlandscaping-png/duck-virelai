"""virelai_v4/library/counter_march.py — life-counter march recognizer + death confirmer.

WO-E09-v2 (Campaign E). Two universal-machinery reads over belief the substrate
already maintains (after Deliverable 1 widens the live-count writer):

  - is_counter_march(history, window): the RECOGNIZER. A region whose live
    cell-count has marched in a direction-stable, regular (every-sync, non-zero)
    way for `window` consecutive per-sync deltas is a counter candidate. Variable
    step is accepted (the depletion may be 1 or 2 cells per action) — only
    direction-stability and presence are required; no step magnitude is hardcoded.

  - confirm_counter_on_death(library, is_death_frame): the CONFIRMER. On a death
    frame, a COUNTER-candidate that has depleted to its floor records a confirming
    observation on its counter belief; one that has NOT depleted records a
    disconfirming observation. Falsification cuts both ways (Popper-test landing).

Kind-legal: reads live cell-count, delta-sign, is_death_frame, and per-object
spawn/min counts only — no color, position, world, or game-tuned magnitude. The
confirm/disconfirm confidences are evidence strengths (logit anchors), not world
contents. Single-writer spine preserved: belief mutation goes through the
existing accumulate_role_evidence accumulator.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Sequence

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.library.constants import CONFIRMATION_THRESHOLD

# WO-E14 D1: the COUNTER sub-label opens when the accumulated counter belief
# crosses the role model's existing gate — NOT a new tuned constant.
_COUNTER_SUBLABEL_THRESHOLD: float = CONFIRMATION_THRESHOLD  # 0.80

# Evidence strengths for the death-frame corroboration (logit anchors for the
# BBA accumulator: >0.5 increments counter belief, <0.5 decrements it). Not
# game-tuned magnitudes — the strength of a single corroboration/refutation.
_COUNTER_CONFIRM_CONFIDENCE: float = 0.90
_COUNTER_DISCONFIRM_CONFIDENCE: float = 0.10


def is_counter_march(cell_count_history: Sequence[int], window: int) -> bool:
    """True iff the last `window` consecutive per-sync cell-count deltas are all
    non-zero and share one sign (direction-stable, regular march).

    Needs `window + 1` counts to form `window` deltas; returns False with fewer.
    Variable step accepted: only the sign and presence of each delta matter.
    """
    if window < 1:
        return False
    h = list(cell_count_history)
    if len(h) < window + 1:
        return False
    recent = h[-(window + 1):]
    deltas = [recent[i + 1] - recent[i] for i in range(window)]
    if any(d == 0 for d in deltas):
        return False  # regularity: a flat sync breaks the march
    first_sign = 1 if deltas[0] > 0 else -1
    return all((1 if d > 0 else -1) == first_sign for d in deltas)


def emit_counter_candidate_diag(
    obj, rid, changed_this_sync: bool, board_changed: bool,
    actions_taken: int, window: int,
) -> None:
    """WO-E12 D1: per-sync diagnostic line for one in-domain counter candidate.

    PURE READ — emits to stderr only when VIRELAI_DIAG_DUMP=1; mutates nothing.
    Shows whether the recorded history populates and marches, the per-sync
    board-change outcome, and which window is_counter_march fires on (the
    5-run watch). `window` is passed in (not imported) to avoid a role_classifier
    import cycle. Single responsibility: emit only.
    """
    if os.environ.get("VIRELAI_DIAG_DUMP", "0") != "1":
        return
    history = getattr(obj, "cell_count_history", ())
    fired = is_counter_march(history, window)
    sub_role = getattr(obj, "sub_role", "")
    # WO-E14 scope-tighten: emit only candidates that actually changed, marched,
    # or carry a sub-label — drops the ~9k all-candidate flood to the counter's
    # own ~100 lines (gradeable without per-rid filtering).
    if not (changed_this_sync or fired or sub_role):
        return
    outcome = (
        "CHANGED" if changed_this_sync
        else ("BOARD_ELSEWHERE" if board_changed else "INERT")
    )
    rec = {
        "tag": "E12-COUNTER-DIAG",
        "sync": actions_taken,
        "rid": rid,
        "class_id": getattr(obj, "class_id", None),
        "role": str(getattr(obj, "role", None)),
        "sub_role": sub_role,
        "current_cell_count": getattr(obj, "current_cell_count", None),
        "cell_count_history": list(history),
        "board_change": outcome,
        "history_pushed_this_sync": changed_this_sync,
        "march_fired": fired,
    }
    print(json.dumps(rec), file=sys.stderr, flush=True)


def maybe_open_counter_sublabel(obj) -> None:
    """WO-E14 D1: open the COUNTER sub-label under the (reactive) role when the
    accumulated counter belief crosses the role model's CONFIRMATION_THRESHOLD.

    The march evidence already accumulates in `counter_log_score` (E13/T3); this
    gives it an expression channel without flipping the categorical role.
    - Does NOT touch `obj.role` or `obj.confidence` — orthogonal to the role write
      and its confidence ratchet.
    - Latch-on: once `sub_role == "counter"`, a single below-threshold read does
      not clear it (the counter axis accumulates; a transient dip must not flicker
      the label). Default per WO-E14 D1.
    Kind-legal: opens on a universal belief axis crossing a universal gate; no
    row/class/outcome constant.
    """
    if getattr(obj, "sub_role", "") == "counter":
        return  # latched
    if obj.sigmoid_confidence("counter") >= _COUNTER_SUBLABEL_THRESHOLD:
        obj.sub_role = "counter"


def confirm_counter_on_death(library, is_death_frame: bool) -> None:
    """Record a confirming/disconfirming counter observation on the death frame.

    For each COUNTER-role object with a maintained cell-count history:
      - depleted-to-floor (current count is at its observed minimum AND below its
        spawn baseline) -> confirming observation (predicted "I deplete and the
        life ends" — corroborated).
      - otherwise (life ended without the candidate bottoming out) -> disconfirming
        observation (the prediction failed; candidacy must not be rubber-stamped).

    Pure read over ctx-supplied is_death_frame + library belief; mutates belief
    only through accumulate_role_evidence (single-writer spine). No-op off a
    death frame. The lower-bound predicate is the one confirmer-side tunable
    (Director may refine, as with N).
    """
    if not is_death_frame:
        return
    for obj in library.objects.values():
        # WO-E14 D3 coherence: corroborate the deepened counter — categorical
        # COUNTER role OR a region carrying the COUNTER sub-label (REACTIVE · counter).
        if obj.role != LibraryRole.COUNTER and getattr(obj, "sub_role", "") != "counter":
            continue
        history = getattr(obj, "cell_count_history", ())
        if not history:
            continue
        floor = min(history)
        depleted = (
            obj.current_cell_count <= floor
            and obj.current_cell_count < obj.initial_cell_count
        )
        confidence = (
            _COUNTER_CONFIRM_CONFIDENCE if depleted else _COUNTER_DISCONFIRM_CONFIDENCE
        )
        accumulate_role_evidence(obj, LibraryRole.COUNTER, confidence)
