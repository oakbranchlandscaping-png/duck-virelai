"""Pure, evidence-bounded typing of observed lever-effect channels (legacy import path).

The function moved verbatim to ``inference.framework.effect_typing`` on 2026-10-13 (WO-DESC-B), so the live
description can import it without loading this package's legacy compiler. This module re-exports the same object.
"""
from __future__ import annotations

from inference.framework.effect_typing import classify_effect_channel

__all__ = ["classify_effect_channel"]
