"""
contracts/execution_protocol.py

ExecutionProtocol — V3.5 Phase 3 output artifact.

Carried forward from V3 contracts/phase3.py (grade A).
V3.5 addition: confirmed_levers field resolves lever data flow gap
identified in the Lifecycle Trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ExecutionProtocol:
    """
    Compiled execution plan from a WinHypothesisBundle.

    Fields:
        protocol_id       — unique identifier for this protocol
        exit_condition     — what constitutes a successful exit
        abort_conditions   — conditions that trigger abort
        hypothesis_type    — which hypothesis type drove compilation
        target_value       — pixel value being targeted (if applicable)
        action_sequence    — ordered action IDs from DAG compilation
        friction_engine    — "v0" (counter) or "v1" (contact-win windowed)
        max_steps          — budget cap for this execution attempt
        confirmed_levers   — lever data from Phase 2 (V3.5 addition)
    """
    protocol_id: str
    exit_condition: str
    abort_conditions: Tuple[str, ...] = ()

    # M7 additions (carried from V3)
    hypothesis_type: str = "EXPLORATION_PRIOR"
    target_value: Optional[int] = None
    action_sequence: Tuple[int, ...] = ()
    friction_engine: str = "v0"
    max_steps: int = 50

    # V3.5 addition: lever data flows Phase 2 → Phase 3 → Phase 4
    confirmed_levers: Tuple = ()


@dataclass(frozen=True)
class ProtocolExecutionState:
    """Runtime state for tracking protocol execution progress."""
    protocol: ExecutionProtocol
    step_index: int = 0
    completed: bool = False
    aborted: bool = False
    abort_reason: Optional[str] = None


__all__ = [
    "ExecutionProtocol",
    "ProtocolExecutionState",
]
