# virelai_v4/cybernetic/ — WO-CYBERNETIC-01 (PORTed from V3.5 per WO-01.A, May 17, 2026)
#
# Wiener feedback loop: execution monitoring + mismatch detection.
#
# WO-01.A note: V3.5's cybernetic/__init__.py re-exported from prediction_lookup
# and monitor_action. Both are PORT_WITH_MODIFICATIONS per WO-00 (deferred). This
# slimmed V4 __init__.py only re-exports from the 5 PORT_AS_IS files transferred
# in WO-01.A. The deferred files will be added in subsequent work orders.

from virelai_v4.cybernetic.execution_monitor import (  # noqa: F401
    ActionMatchResult,
    PredictedEffect,
    record_action,
    compute_nav_match,
)
from virelai_v4.cybernetic.mismatch_detector import (  # noqa: F401
    MismatchDetector,
    MismatchReport,
)
from virelai_v4.cybernetic.frame_delta import (  # noqa: F401
    FrameDelta,
    EMPTY_DELTA,
    compute_frame_delta,
    compute_consecutive_pure_lc,
)
from virelai_v4.cybernetic.cell_history import (  # noqa: F401
    CellHistory,
    update_cell_history,
    build_cell_history,
    record_probe_observation,
)
from virelai_v4.cybernetic.state_tracker import (  # noqa: F401
    StateTracker,
    compute_state_signature,
)
