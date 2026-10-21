"""One supported-access hint for a sandbox error against ``TransitionView`` (WO-RUNTIME-01 §9).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Public-25: Duck called ``.get``, subscripted, unpacked
and read guessed attributes (``boundary_state``, ``changed_cell_count``) on the documented sandbox object. The object
is not widened into a mapping and no guessed method is emulated: the error keeps its text and gains one line naming
the object's public fields. Only an error that names ``TransitionView`` is touched, so the ordinary turn and its
digest never change.
"""
from __future__ import annotations

import re

_NAMES = re.compile(r"TransitionView|ActionTransitionView")
HINT = ("HINT: a TransitionView is an object with exactly the fields action, before_frame, after_frame, frame and "
        "result (a dict, set on the last transition only). Read them as attributes, e.g. "
        "last_transition.before_frame.grid or transitions[-1].result.get('state'); it is not a mapping, tuple or "
        "summary.")


def transition_view_hint(error: str) -> str:
    """The error, plus the hint once when it concerns a TransitionView (unchanged otherwise)."""
    if not error or HINT in error or not _NAMES.search(error):
        return error
    return f"{error}\n{HINT}"


__all__ = ["HINT", "transition_view_hint"]
