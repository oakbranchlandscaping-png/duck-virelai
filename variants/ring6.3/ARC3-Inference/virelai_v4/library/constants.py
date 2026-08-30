"""
virelai_v4/library/constants.py — Cross-module library constants.

Centralized constants consumed by multiple library modules. Currently
holds the BBA Layer One confirmation threshold added in WO-BLUEPRINT-07
for use by WO-BLUEPRINT-08's predicate migrations.

Import sovereignty: stdlib only. No other virelai_v4 module imports.
Reading this module must not trigger downstream import chains.

Filed under WO-BLUEPRINT-07 (May 22, 2026).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# BBA Layer One sigmoid confidence threshold
# ---------------------------------------------------------------------------

# Sigmoid confidence threshold above which a log-score axis is considered
# "confirmed" — the level at which BBA Layer One predicates accept the
# slot as carrying the role.
#
# Per Blueprint Section 2 v1.1 prior discussion (cited in
# `docs/architecture/BBA_LAYER_ONE_COEXISTENCE_AUDIT.md` §3.3).
#
# Retained for predicates outside the lever category — currently P4
# (COUNTER_IDENTIFIED) per Section 2 v1.3 amendment Section 6 item 4:
# "the counter category does not have the two-state distinction the lever
# category requires."
CONFIRMATION_THRESHOLD: float = 0.8


# ---------------------------------------------------------------------------
# WO-BLUEPRINT-08-TWO-THRESHOLD — Apex ratified May 22, 2026.
# ---------------------------------------------------------------------------
#
# Per Section 2 v1.3 amendment (filed alongside this constant): the lever
# category's belief axis (`lever_log_score`) is read by two predicates at
# two distinct thresholds.
#
# LEVER_LOCKED_THRESHOLD — the LOW threshold. P13 (SLOT_IS_LEVER_LOCKED)
# reads against it. Crosses when a slot is confirmed enough to start
# probing its mechanism. A single LEVER_LOCAL_* probe outcome at the
# damped accumulator confidence (0.7) drives lever_log_score above this.
LEVER_LOCKED_THRESHOLD: float = 0.6

# LEVER_TYPED_THRESHOLD — the HIGH threshold. C2 (LEVER_TYPED) reads
# against it. Crosses when a slot's mechanism is characterized enough to
# stop probing. Only cycle_probe terminal commits (at the un-damped
# accumulator confidence 1.0) drive lever_log_score above this. The
# Section 2 v1.2 saturation semantic is preserved because cycle_probe.py
# fires the accumulator on every terminal commit including SATURATED.
LEVER_TYPED_THRESHOLD: float = 0.95


__all__ = [
    "CONFIRMATION_THRESHOLD",
    "LEVER_LOCKED_THRESHOLD",
    "LEVER_TYPED_THRESHOLD",
]
