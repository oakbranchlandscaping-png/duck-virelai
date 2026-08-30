"""
contracts/degradation.py

Degradation flag and severity types for V3.5 artifact chain.

Used by ExecutionOutcome and GlassBoxDossier to track degraded states
across the solver pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class Severity(Enum):
    WARN = "WARN"       # Log only, no behavioral change
    ERROR = "ERROR"     # Continue with degraded capability, flag visible in dossier
    FATAL = "FATAL"     # Transition to TERMINAL with reason


@dataclass(frozen=True)
class DegradationFlag:
    phase: str          # Which DFA state (INITIALIZE, DISCOVERY, CRUCIBLE, etc.)
    component: str      # Which module raised the flag
    error: str          # What went wrong (human-readable)
    severity: Severity  # How bad


__all__ = ["Severity", "DegradationFlag"]
