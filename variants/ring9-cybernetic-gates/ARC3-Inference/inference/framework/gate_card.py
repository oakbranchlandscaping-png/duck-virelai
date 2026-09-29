"""The binding gate card: the one rendering of the gate that Duck sees each turn.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 stage M-0).

Moved out of ``ToolAgent`` so the production prompt path, the offline replay harness and the tests
measure the same bytes. From R9-R07 (stage M-1) the card is built from slots by
``inference.framework.card_builder``; the 24,000-character guard remains a tripwire.
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
    """The slot-built card (R9-R07, memory stage M-1): what Duck is shown and gets from 'gate'."""
    from inference.framework.card_builder import build_card

    return build_card(machine).payload


def render_binding_gate_context(machine: Any) -> str:
    """The exact text appended to Duck's user prompt."""
    return BINDING_HEADER + json.dumps(binding_gate_payload(machine), sort_keys=True, default=str)
