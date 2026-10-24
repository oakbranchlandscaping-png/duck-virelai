"""The gate-contract repair obligation, bounded by what the turn did and by the question it belongs to (WO-RUNTIME-01A).

Author: Claude (Alpha build seat), 2026-10-22. Base ``8b47c73``. Interface: ``INTERFACE_WO_RUNTIME_01A_v1_2026-10-22``
§3.1 (the diagnosis) and §4.1 (the rule).

A rejected gate answer opens an obligation (``ToolAgent._record_contract_repair``): Duck's next call should be the
corrected answer, and a call that inspects instead ends the turn ``contract_repair_loop``, a typed
``RECOVERABLE_NO_ACTION`` / ``CONTRACT_REPAIR_EXHAUSTED`` failure bounded by the HARD budget (``turn_recovery``).

The canary (dc22, ka59, sc25) showed the two places the obligation outlived its meaning. Each ended the game:

* **an executed action is progress.** When Duck acted under the obligation and the gate admitted and executed the
  action, the guard still raised the controlled stop. The turn was typed ``ACTION_EXECUTED`` (an executed step is not
  a failure), so ``solver._turn_ends_game`` read the stop and ended the game. Now the guard does not fire on an
  executed dispatch; the ordinary progress path ends the turn and resets the guard, the obligation with it.
* **a closed question owes no answer.** The obligation was kept until the board, level or gate changed, so it
  survived the controller's ``CLOSED_UNRESOLVED`` close of the very question it belonged to (dc22: the next turn, on
  the next lever, still carried it). Now a close discharges it, so an interface failure on a closed question is never
  charged to the next one.

The repair path itself is unchanged: a rejected answer still asks for its correction, a call that inspects instead
still ends the turn as a typed recoverable failure, and two such turns still close the question.
"""
from __future__ import annotations

from typing import Any

REPAIRING = frozenset({"CONTRACT_REPAIR", "GATE_TRANSITION"})  # dispatches that answer the obligation


def stops_turn(agent: Any, dispatch: Any) -> bool:
    """True when the open obligation stops the turn: the dispatch neither repaired, transitioned nor executed."""
    return bool(getattr(agent, "_contract_repair_required", False)) \
        and dispatch.interaction_kind not in REPAIRING and not dispatch.step_executed


def discharge(agent: Any) -> None:
    """The question the obligation belonged to was closed: nothing is owed on it any more."""
    if agent is not None:
        agent._contract_repair_required = False
        agent._contract_repair_signatures = set()


__all__ = ["REPAIRING", "discharge", "stops_turn"]
