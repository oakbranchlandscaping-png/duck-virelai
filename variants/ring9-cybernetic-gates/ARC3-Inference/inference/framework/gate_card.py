"""The binding gate card: the one rendering of the gate that Duck sees each turn.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 stage M-0).

Moved out of ``ToolAgent`` so the production prompt path, the offline replay harness and the tests
measure the same bytes. Until the slot-built card lands (stage M-1), this is the gate payload as
production renders it today; its size is what the 24,000-character guard checks.
"""
from __future__ import annotations

import json
from typing import Any

BINDING_HEADER = "VIRELAI GATE (binding):\n"
CURRENT_PROBE_INSTRUCTION = (
    "Execute current_probe directly. Its token is current for this turn; "
    "do not reuse a token from prior history."
)


def binding_gate_payload(machine: Any) -> dict[str, Any]:
    """The gate view plus, when a probe is due, the current probe capability."""
    compact_gate = machine.gate_view()
    context: dict[str, Any] = dict(compact_gate)
    if compact_gate.get("next_operation") == "QUERY_NEXT_PROBE":
        capability = machine.next_probe_capability()
        if capability is not None:
            context["current_probe"] = capability
            context["instruction"] = CURRENT_PROBE_INSTRUCTION
    return context


def render_binding_gate_context(machine: Any) -> str:
    """The exact text appended to Duck's user prompt."""
    return BINDING_HEADER + json.dumps(binding_gate_payload(machine), sort_keys=True)
