"""virelai_v4/scipy_check.py — Centralized scipy import gate.

scipy is a hard dependency per pyproject.toml (scipy>=1.17.1). This module
is the single point of scipy access for virelai_v4. Importing from this
module raises a clear error at module load time if scipy is missing, rather
than producing silently-degraded results at call time.

Placement: package root (not inside library/). WO-MINE-CLEAN-08 originally
placed this in library/, which introduced a perception→library→perception
import cycle via library/__init__.py force-loading library_sync. The cycle
was resolved in WO-MINE-CLEAN-08.1 by relocating to the package root, where
the scipy import chain does not touch any sub-package __init__.py.

FRICTION-RM-01: prior versions of this codebase used silent try/except
fallbacks around scipy imports that returned qualitatively wrong answers
when scipy was unavailable. That pattern cost nine work orders to diagnose
and is eliminated here. If scipy is not installed, this module fails
loudly at import time.
"""

try:
    from scipy.ndimage import label as ndimage_label
except ImportError as e:
    raise ImportError(
        "scipy is required for Virelai V4. Install via "
        "`uv sync` in the solver root. "
        "See FRICTION-RM-01 for the history of soft-import failures."
    ) from e

__all__ = ["ndimage_label"]
