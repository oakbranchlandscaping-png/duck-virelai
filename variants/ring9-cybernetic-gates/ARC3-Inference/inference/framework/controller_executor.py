"""The controller executor: who owns the next step (memory law M8, DESIGN_VIRELAI_MEMORY_v2 §5.5).

Author: Claude (Alpha build seat), 2026-09-29. R9-R08 (memory stage M-2). Rulings D2 and D5.

Before every analyzer turn the executor asks one question of the gate machine: can the controller
compute this step, or does it need judgment? A computable step is taken by the controller, with no
model call: either one gate answer rendered from certified state, or exactly one bound action. Then
the new frame is read and the question is asked again. Duck is woken for everything else.

This module is pure: it reads the machine and returns a decision. The agent executes it through the
same recording path Duck's actions use (``controller_turn.py``).

What the controller owns (D2, CLICK worlds only; NAV is shelved):
- G0 action metadata and G1 pointer ego: the templates are derived from metadata.
- G2 search: the first untried ranked object (Duck followed this order exactly, live, twice).
- G2 label and frozen prediction, when the record's trigger class is EVERY_TRANSITION or
  EFFECTIVE_TRANSITIONS_ONLY: a COUNTER_REWRITE on the template's certified action.
- Every bound G2 and G3 probe action (demonstration, sweep, confirmation).
- G3 dossiers and the inventory, when nothing is ambiguous.

Duck owns: G4 onward (its first turn there is the orientation turn, M-3), an OPEN or IRREGULAR
trigger record (the discriminating prediction is a choice, not a computation), ambiguity,
unbound or multi-action probes, and every stop-and-wake condition (``wake_reason``).

The prose in a controller answer is rendered deterministically from the certified fields; the
certified content is the structured part (M7). It is marked as controller-rendered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from inference.framework.card_builder import world_budgets
from inference.framework.memory_store import cell_bbox as _bbox
from inference.framework.virelai_gates import control_archetype_prior

CONTROLLER, DUCK = "CONTROLLER", "DUCK"
ANSWER, ACTION = "ANSWER", "ACTION"
CONTROLLER_GATES = ("G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS")
OWNED_TRIGGERS = ("EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY")
WAKE_TICKS_REMAINING = 2
RENDERED = "Controller-rendered from certified state; the certified content is the structured fields."
AMBIGUOUS_DISPOSITIONS = ("AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION")
BOUNDARY_KEYS = ("done", "level_completed", "game_over", "run_complete")


@dataclass(frozen=True)
class OwnedStep:
    owner: str  # CONTROLLER | DUCK
    gate_id: str
    reason: str
    kind: str | None = None  # ANSWER | ACTION, for the controller
    answer: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    probe_token: str | None = None
    refusal_key: tuple[str, int] | None = field(default=None)


def _duck(machine: Any, reason: str) -> OwnedStep:
    return OwnedStep(owner=DUCK, gate_id=machine.gate_id, reason=reason)


def _answer_due(view: Mapping[str, Any]) -> bool:
    return view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"


def next_owned_step(machine: Any, *, refused: frozenset | set = frozenset()) -> OwnedStep:
    """Who owns the next step, and, for the controller, exactly what it is."""
    world = control_archetype_prior(machine.ego.affordances)["world_type"]
    if world != "CLICK_GOD_MODE":
        return _duck(machine, f"the controller executes CLICK worlds only; this is {world}")
    if machine.gate_id not in CONTROLLER_GATES:
        return _duck(machine, f"{machine.gate_id} needs judgment")
    capability = machine.next_probe_capability()  # first: it can advance the gate's own state
    view = machine.gate_view()
    key = (machine.gate_id, int(view.get("revision") or 0))
    if key in refused:
        return _duck(machine, f"{machine.gate_id} refused the controller's answer at this revision")
    if _answer_due(view):
        answer, reason = controller_answer(machine, view)
        if answer is None:
            return _duck(machine, reason)
        return OwnedStep(CONTROLLER, machine.gate_id, reason, ANSWER, answer=answer, refusal_key=key)
    if capability is None:
        return _duck(machine, f"{machine.gate_id} offers no probe and no answer")
    action, reason = _bound_action(capability)
    if action is None:
        return _duck(machine, reason)
    return OwnedStep(
        CONTROLLER, machine.gate_id, reason, ACTION, action=action,
        probe_token=str(capability["probe_token"]),
    )


def _bound_action(capability: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    actions = list(capability.get("actions") or ())
    if capability.get("purpose") == "GUIDED_ACTION" and capability.get("gate_id") == "G2-COUNTER":
        anchors = (capability.get("target") or {}).get("untried_object_anchors") or []
        if not anchors:
            return None, "G2 search has no untried ranked object"
        row, col = anchors[0]
        return {"action": "ACTION6", "row": int(row), "col": int(col)}, "G2 search: first untried ranked object"
    if len(actions) == 1:
        return dict(actions[0]), f"bound {capability.get('purpose')} action"
    return None, f"{capability.get('purpose')} probe binds {len(actions)} actions; Duck chooses"


# ---- answers rendered from certified state ------------------------------------------------------

def controller_answer(machine: Any, view: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    template = view.get("answer_template")
    if not isinstance(template, Mapping):
        return None, f"{machine.gate_id} demands an answer without a template"
    gate = machine.gate_id
    if gate == "G0-ACTION-METADATA":
        return {
            **template, "answer_id": "G0-CONTROLLER",
            "epistemic_limit": "Action effects remain unknown until controlled observation reveals them.",
        }, "G0 metadata"
    if gate == "G1-EGO":
        if template.get("answer_kind") != "POINTER_GOD_MODE":
            return None, "G1 is not the pointer ego"
        return dict(template), "G1 pointer ego from metadata"
    if gate == "G2-COUNTER":
        return _counter_answer(machine, template)
    if template.get("answer_kind") == "LEVER_DOSSIER":
        return _dossier_answer(template), "G3 dossier from the effect summary"
    if template.get("answer_kind") == "LEVER_INVENTORY" and "lever_entities" in template:
        return _inventory_answer(template)
    return None, f"{gate} answer shape {template.get('answer_kind')!r} is not controller-owned"


def _counter_answer(machine: Any, template: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    record = (template.get("trigger_options") or {}).get("record") or {}
    trigger = str(record.get("class") or "")
    if trigger not in OWNED_TRIGGERS:
        return None, f"the G2 trigger record is {trigger or 'unknown'}: the discriminating prediction is Duck's"
    prediction = dict(template["novel_prediction"])
    cells = list((prediction.get("scope") or {}).get("cells") or ())
    rewrite = prediction["expected_parameters"]["rewrite"]
    amount = int(prediction["expected_parameters"]["amount"])
    effective = int(record.get("effective_transitions_with_tick") or 0)
    null = int(record.get("null_transitions_without_tick") or 0) + int(record.get("null_transitions_with_tick") or 0)
    when = "effective transition" if trigger == "EFFECTIVE_TRANSITIONS_ONLY" else "transition"
    reason = (
        f"The footprint rewrote {amount} cells {rewrite} on all {effective} effective transitions, "
        f"at different acted sites, and on none of the {null} transitions that changed nothing else."
        if trigger == "EFFECTIVE_TRANSITIONS_ONLY" else
        f"The footprint rewrote {amount} cells {rewrite} on every one of the "
        f"{effective + null} recorded transitions, whether or not anything else changed."
    )
    return {
        **template,
        "trigger": trigger,
        "tracked_variable": f"the cells of a {len(cells)}-cell footprint (bbox {_bbox(cells)}) not yet rewritten {rewrite}",
        "mechanism": f"Each {when} rewrites {amount} footprint cells {rewrite} ({trigger}).",
        "bookkeeping_reason": reason,
        "competing_models": [
            "The footprint is a remote effect of the particular objects acted on, not a count of transitions.",
        ],
        "falsifier": (
            "An effective transition without a footprint rewrite, or a rewrite on a transition that "
            "changes nothing else." if trigger == "EFFECTIVE_TRANSITIONS_ONLY" else
            "A transition that leaves the footprint unchanged."
        ),
        "limitations": [*template.get("limitations", ()), RENDERED],
        "novel_prediction": {
            **prediction,
            "predicate": "COUNTER_REWRITE",
            "because": f"The footprint rewrote {amount} cells {rewrite} on every {when} recorded so far.",
            "novelty": (
                f"It is frozen at transition {machine.observed_through_step}, before the action is "
                "taken from the world state that follows."
            ),
        },
    }, f"G2 label and prediction ({trigger})"


def _dossier_answer(template: Mapping[str, Any]) -> dict[str, Any]:
    summary = template["effect_summary"]
    action = template["intervention"]
    site = f"({action.get('row')}, {action.get('col')})" if "row" in action else str(action.get("action"))
    remote = int(summary.get("remote_changed_cell_count") or 0)
    text = (
        f"Clicking {template['target_member_id']} at {site} rewrote {summary.get('local_changed_cell_count')} "
        f"of its own cells (bbox {summary.get('local_changed_bbox')}) and {remote} cells elsewhere"
        + (f" (bbox {summary.get('remote_changed_bbox')})" if remote else "")
        + ", and the prospective repeat reproduced that residue."
    )
    if int(summary.get("counter_masked_cell_count") or 0):
        text += (
            f" The {summary['counter_masked_cell_count']} counter cells that changed on each press "
            "were excluded by the mask as bookkeeping."
        )
    return {
        **template,
        "explanation": text,
        "competing_models": ["A hidden process changed the object at the same moment as the click."],
        "falsifier": "The same click from the same masked state leaves the object unchanged.",
        "limitations": [RENDERED],
    }


def _inventory_answer(template: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    if template.get("ambiguous_entities"):
        return None, "G3 has bounded ambiguity: the coverage report is Duck's"
    levers, nulls = list(template["lever_entities"]), list(template.get("clean_null_entities") or ())
    return {
        **template,
        "explanation": (
            f"The complete click roster found {len(levers)} levers that rewrite their own cells when "
            f"clicked ({', '.join(levers)}), and {len(nulls)} objects closed with scoped null "
            "evidence; counter changes were excluded by the mask as bookkeeping."
        ),
        "competing_models": ["An object closed as null may respond from a different world state."],
        "falsifier": "A clean-null object responds to the same click from the same masked state.",
        "limitations": [RENDERED],
    }, "G3 inventory"


# ---- stop-and-wake ----------------------------------------------------------------------------

def wake_signals(machine: Any) -> dict[str, int]:
    """Counters read before a controller action, so ``wake_reason`` sees only what it changed."""
    return {"rejected_candidates": len(getattr(machine.counter, "_rejected_candidates", ()) or ())}


def wake_reason(
    machine: Any, event: Mapping[str, Any] | None, result: Mapping[str, Any],
    before: Mapping[str, int] | None = None,
) -> str | None:
    """Why Duck must take the next step after a controller action, or None to continue."""
    if any(result.get(key) for key in BOUNDARY_KEYS):
        return "boundary event: " + ", ".join(key for key in BOUNDARY_KEYS if result.get(key))
    event = event or {}
    comparison = event.get("counter_comparison") or {}
    if comparison.get("outcome") == "CONTRADICTED" and comparison.get("evidence_ref") == event.get("evidence_id"):
        return "the frozen G2 prediction was contradicted"
    if before is not None and wake_signals(machine)["rejected_candidates"] > before["rejected_candidates"]:
        return "G2 rejected its counter candidate"
    if event.get("gate_status_after") in {"UNRESOLVED", "REOPENED"}:
        return f"{event.get('gate_id')} is {event['gate_status_after']}"
    confirmation = (event.get("confirmation") or {}).get("status")
    if confirmation in {"CONTRADICTED", "BOUNDARY_DEFERRED"}:
        return f"a G3 confirmation was {confirmation}"
    attribution = event.get("attribution") or {}
    if event.get("bounded_ambiguity") or attribution.get("disposition") in AMBIGUOUS_DISPOSITIONS:
        return f"attribution is {attribution.get('disposition') or 'ambiguous'}"
    if attribution.get("boundary_state"):
        return "a boundary interrupted the attribution"
    budgets = world_budgets(machine) or {}
    ticks = budgets.get("counter_ticks_remaining")
    if ticks is not None and ticks <= WAKE_TICKS_REMAINING:
        return f"the counter has {ticks} ticks left"
    return None


__all__ = [
    "ACTION", "ANSWER", "CONTROLLER", "DUCK", "OwnedStep", "controller_answer",
    "next_owned_step", "wake_reason", "wake_signals",
]
