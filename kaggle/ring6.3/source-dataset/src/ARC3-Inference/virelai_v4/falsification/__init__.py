# virelai_v4/falsification/ — Adaptive probe loop for confidence-driven discovery.
#
# WO-01.A note: PORTed from V3.5 alongside cybernetic/. Only prediction_comparator.py
# was transferred in WO-01.A to satisfy the cybernetic.execution_monitor cross-package
# import (CJ-01 — the "scientific kernel" pure function, PORT_AS_IS per A.5).
#
# Per V3.5 Module Guide Step 1 finding: V3.5's falsification/__init__.py had no
# re-exports; callers used `from falsification.prediction_comparator import ...`
# directly. V4 adds a clean public API per V3.5 Final Code Report Section 2 REWRITE.

from virelai_v4.falsification.prediction_comparator import (  # noqa: F401
    CausalVerdict,
    compare_prediction,
)
