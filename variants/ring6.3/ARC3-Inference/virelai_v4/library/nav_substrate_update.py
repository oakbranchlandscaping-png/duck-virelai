"""
virelai_v4/library/nav_substrate_update.py — NavAtlas substrate update primitive.

Per WO-CAMPAIGN3-PHASE1-04 (May 2, 2026).

Free function ``maybe_record_move`` encapsulates the gating logic +
``nav_atlas.record_move`` call. The Virelai class's ``_record_nav_move``
helper method (in ``virelai.py``) is a thin wrapper around this
function, allowing the substrate-update logic to be unit-tested
without constructing a Virelai instance (which requires arcengine).

Per the V4 precedent at ``tests/test_choose_action_contracts.py``:

> "Constructing a Virelai for runtime testing would require either the
>  full framework stack or sys.modules stubbing of arcengine, both of
>  which were judged heavier than the diagnostic value warrants..."

This module's free function is the testable unit. The Virelai
method is glue.

V3.5 caller analog: ``execution/nav_executor.py:582-586`` — the only
production call site for ``record_move`` in V3.5. V4's call lives in
``virelai.py:choose_action`` after ``_update_ego_position`` and before
the target/route block.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from virelai_v4.library.nav_atlas import NavAtlas


# Cardinal action IDs (ACTION1=up, ACTION2=down, ACTION3=left, ACTION4=right).
# NavAtlas only models cardinal-action substrate (action_dirs is keyed on
# 1-4); record_move is invoked only for these IDs. RESET (0), ACTION5 (5),
# ACTION6 (6), and ACTION7 (7) are non-cardinal and should not call into
# the NavAtlas substrate.
_CARDINAL_IDS = frozenset({1, 2, 3, 4})


def maybe_record_move(
    nav_atlas: Optional[NavAtlas],
    last_action_id: Optional[int],
    prev_ego_pos: Optional[Tuple[int, int]],
    ego_current_pos: Optional[Tuple[int, int]],
    current_grid: np.ndarray,
    prev_grid: Optional[np.ndarray],
) -> bool:
    """Conditionally invoke ``nav_atlas.record_move`` per the WO-04 gate.

    Returns
    -------
    bool
        ``True`` if ``record_move`` was invoked (substrate updated).
        ``False`` if the call was suppressed by one of the gate
        conditions below (substrate unchanged).

    Gate conditions — record_move is suppressed when ANY hold:
      - ``nav_atlas is None`` — stride probe still in progress per
        WO-03; the probe will instantiate NavAtlas at commit time.
        Information loss for probe-frame moves is acceptable per
        WO-04 Step 0 §5.3.
      - ``last_action_id not in {1, 2, 3, 4}`` — non-cardinal action
        (RESET, ACTION5, ACTION6, ACTION7); NavAtlas doesn't model
        these.
      - ``prev_ego_pos is None`` — first frame or non-NAV world; no
        prior position to compare.
      - ``ego_current_pos is None`` — same as above; no current
        position to record.

    moved derivation (per Step 0 §3.3 — Path A):
        ``moved = (prev_ego_pos != ego_current_pos)``

        V4's ``_update_ego_position`` updates ``ego_current_pos`` only
        on successful displacement. On wall collision, the field is
        left unchanged. Therefore position-comparison is semantically
        equivalent to V3.5's HUD-masked pixel-delta derivation for
        the use case (informing record_move which path the body took).

    V3.5 source: ``execution/nav_executor.py:582-586``.
    """
    if (
        nav_atlas is None
        or last_action_id not in _CARDINAL_IDS
        or prev_ego_pos is None
        or ego_current_pos is None
    ):
        return False
    moved = prev_ego_pos != ego_current_pos
    nav_atlas.record_move(
        prev_pos=prev_ego_pos,
        new_pos=ego_current_pos,
        action_id=last_action_id,
        moved=moved,
        grid=current_grid,
        prev_grid=prev_grid,
    )
    return True


__all__ = ["maybe_record_move"]
