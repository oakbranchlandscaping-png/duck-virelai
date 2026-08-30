"""virelai_v4/library/sweep_updater.py — Sweep state updates from probe outcomes.

Relocated from strategy/click_sweep.py (WO-MINE-CLEAN-04).
Updates the click sweep list based on a ProbeOutcome.

Import sovereignty: contracts/, library/, stdlib only.
No imports from targeting/, strategy/, perception/, memory/.

FINDING-DEC-14: this function was called from library_sync.py via a lazy
import workaround (library_sync.py:726) that acknowledged the cycle inline.
The workaround is eliminated by moving the function to library/.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from virelai_v4.contracts.probe_types import ProbeOutcome

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

logger = logging.getLogger(__name__)


def update_sweep_from_outcome(
    context: "VirelaiContext",
    probed_region_id: int,
    outcome: ProbeOutcome,
) -> None:
    """Update sweep consecutive_inerts and reactive_found based on probe outcome.

    LEVER_LOCAL_SELF, LEVER_LOCAL_REMOTE, LEVER_REMOTE_ONLY:
        - Reset sweep_consecutive_inerts to 0
        - Increment sweep_reactive_found

    NO_EFFECT:
        - Increment sweep_consecutive_inerts

    AMBIGUOUS:
        - No change to either counter

    Parameters
    ----------
    context : VirelaiContext
        Sweep state fields mutated in place.
    probed_region_id : int
        Region ID of the object that was probed (for logging).
    outcome : ProbeOutcome
        Classification result from classify_probe_outcome.
    """
    if outcome.outcome in ("LEVER_LOCAL_SELF", "LEVER_LOCAL_REMOTE", "LEVER_REMOTE_ONLY"):
        context.sweep_consecutive_inerts = 0
        context.sweep_reactive_found += 1
        logger.debug(
            "[SWEEP] Region %d: %s → reset consecutive_inerts, reactive_found=%d",
            probed_region_id, outcome.outcome, context.sweep_reactive_found,
        )

    elif outcome.outcome == "NO_EFFECT":
        context.sweep_consecutive_inerts += 1
        logger.debug(
            "[SWEEP] Region %d: NO_EFFECT → consecutive_inerts=%d",
            probed_region_id, context.sweep_consecutive_inerts,
        )

    # AMBIGUOUS: no change to either counter (per spec)


__all__ = ["update_sweep_from_outcome"]
