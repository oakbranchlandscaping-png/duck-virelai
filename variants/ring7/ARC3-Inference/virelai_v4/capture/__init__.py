"""WO-CC-S1 · Campaign A · Stage 1 — the CAPTURE package.

An append-only, interpretation-free record of the given: what the platform
hands the solver at each choose_action entry. Records; derives nothing.
"""

from virelai_v4.capture.frame_record import (
    CaptureRecord,
    CaptureStore,
    FrameRecordLog,
)

__all__ = ["CaptureRecord", "FrameRecordLog", "CaptureStore"]
