# Shared-file note, 2026-10-09 (SUB-3)

**Filed by:** Claude, Alpha build seat (click line), before the commit. This follows ruling 9 and the harmony rules of `RULINGS_CONSOLIDATION_v2_2026-10-08.md`.
**Slice:** `BUILD_SLICE_SUB_3_FREE_PLAY_OUTCOME_2026-10-09.md`.
**Base:** `ring9-unified` @ `b805950`. Its runtime is SUB-2 `a2200c2`.

| File | Function | Change |
|---|---|---|
| `inference/framework/play_gate.py` | `PlayTarget.record_outcome` | The returned event gains `"outcome"`, the compacted outcome, built by a new module function `_event_outcome`. The adapter's own `_events` list and its snapshot are unchanged. |
| `inference/agent/python_tool_sandbox.py` | `run_sandboxed_python` (both `except` arms) | Each hidden error now passes through a new module function, `_hidden_error`. It logs the error's type, message and raising line, then returns the same text Duck saw before. |

Nothing else changes. Gates, the controller, the NAV branch, prompts and recording are untouched, and so is every other part of these two files. Sol's open work is not in these functions.
