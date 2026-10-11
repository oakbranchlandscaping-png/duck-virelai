"""The controller executor: who owns the next step (memory law M8, DESIGN_VIRELAI_MEMORY_v2 §5.5).

Author: Claude (Alpha build seat), 2026-09-29. R9-R08 (memory stage M-2), rulings D2 and D5;
extended through G4 in R9-R10 (stage M-4), rulings D3 and D4.

Before every analyzer turn the executor asks one question of the gate machine: can the controller
compute this step, or does it need judgment? A computable step is taken by the controller, with no
model call: either one gate answer rendered from certified state, or exactly one bound action. Then
the new frame is read and the question is asked again. Duck is woken for everything else.

This module is pure: it reads the machine and returns a decision. The agent executes it through the
same recording path Duck's actions use (``controller_turn.py``).

What the controller owns:
- G0 action metadata and G1 pointer ego: the templates are derived from metadata.
- Every exact G1 probe and prospective demonstration in NAV and HYBRID worlds. Duck explains the
  embodied ego after the controller has collected the Delphi record; it does not spend a turn on
  an action the gate already selected.
- G2 search: the first untried ranked object (Duck followed this order exactly, live, twice).
- G2 label and frozen prediction, when the record's trigger class is EVERY_TRANSITION or
  EFFECTIVE_TRANSITIONS_ONLY: a COUNTER_REWRITE on the template's certified action.
- Every bound G2 and G3 probe action (demonstration, route and sweep).
- G3 dossiers and the inventory, when nothing is ambiguous.
- G4.1 anatomy answers (M-4): the channels are certified; the prose is rendered from them.
- G4-A lever runs (D3): each lever is pressed, one press per step, until its run is confirmed,
  diverged or ended; a same-level death returns it to the study (D4, in the gate).
- An extra run Duck asks for (D3): up to 8 CLICK activations or routed NAV contacts with one lever.

- G4-B's relations, from the level's record (R9-R24 D19, RULING_G4_CONTROLLER_FIRST_v2 G-1).

Duck owns: the orientation turn (M-3; due once G4.1 is certified), every G4-A orbit explanation,
an OPEN or IRREGULAR trigger record (the discriminating prediction is a choice, not a
computation), ambiguity, unbound or multi-action probes, G4-C's test and any G4-B prediction the
record cannot answer (both within Duck's per-level budget, R9-R24 D20), normal play after the gates
(D22), and semantic stop-and-wake conditions (``wake_reason``). Bound tests and certified answers
remain controller-owned even after a wake; the wake is delivered when the next step independently
requires judgment.

The prose in a controller answer is rendered deterministically from the certified fields; the
certified content is the structured part (M7). It is marked as controller-rendered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from inference.framework.annotation_lane import orientation_due
from inference.framework.card_builder import world_budgets
from inference.framework.lever_repeat import certified
from inference.framework.memory_store import cell_bbox as _bbox
from inference.framework.virelai_gates import control_archetype_prior

CONTROLLER, DUCK, END = "CONTROLLER", "DUCK", "END"
ANSWER, ACTION = "ANSWER", "ACTION"
ORBITS, RELATIONS, LAW = "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
PREDICTION_GATES = (RELATIONS, LAW)  # Duck freezes each prediction; the controller takes it
CONTROLLER_GATES = ("G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS", "G4-REACTIONS", ORBITS, *PREDICTION_GATES)
LEVEL_CLOSED = "G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9"
OWNED_TRIGGERS = ("EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY")
STUDY_ORDER = ("RUNNING", "CONFIRMING", "RUN_ENDED_RESTART_NEEDED", "NOT_STARTED")
MAX_RERUN_PRESSES = 8
# Budget wakes fire once, when a budget crosses its threshold (so once per life for the counter).
# Provisional until the D7 throughput run measures real per-game budgets.
WAKE_TICKS_REMAINING = 2
WAKE_ACTIONS_REMAINING = 10
WAKE_SECONDS_REMAINING = 120.0
RENDERED = "Controller-rendered from certified state; the certified content is the structured fields."
AMBIGUOUS_DISPOSITIONS = ("AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION")
BOUNDARY_KEYS = ("done", "level_completed", "game_over", "run_complete")


@dataclass(frozen=True)
class OwnedStep:
    owner: str  # CONTROLLER | DUCK | END
    gate_id: str
    reason: str
    kind: str | None = None  # ANSWER | ACTION, for the controller
    answer: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    probe_token: str | None = None
    refusal_key: tuple[str, int, int | None] | None = field(default=None)
    decision: dict[str, Any] | None = None


def _duck(machine: Any, reason: str) -> OwnedStep:
    return OwnedStep(owner=DUCK, gate_id=machine.gate_id, reason=reason)


def _answer_due(view: Mapping[str, Any]) -> bool:
    return view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"


def ladder_end(machine: Any) -> str | None:
    """Where the built ladder ends, the run ends cleanly (Director, 2026-09-29; R9-I02).

    Nothing is left for Duck there: before this, the step went to Duck with no move to make.
    """
    if machine.target_router.current() is None:
        return "every built gate is satisfied, through G4-C; the next slice is not built"
    relations = machine.target_journal.active_product(RELATIONS)
    level_closed = relations is not None and relations.payload.get("status") == "CLOSED_BY_LEVEL_BOUNDARY"
    if level_closed or (machine.gate_id == ORBITS and machine.gate_view().get("next_operation") == LEVEL_CLOSED):
        return "the level changed during G4; cross-level work (G9) is not built"
    return None


def return_to_mu_if_stuck(machine: Any) -> str | None:
    """M-4 (RULING_MU_BUCKET_v1): before a planned stop or a dead state, retry mu on a changed board."""
    from inference.framework.mu_return import return_to_mu

    from inference.framework.virelai_gates import PLAY_GATE_ID

    resting = machine.gate_id == PLAY_GATE_ID and machine._adapters[PLAY_GATE_ID].rest_check_due()  # R9-R24
    stuck = resting or machine.target_router.current() is None or not machine.legal_move_status().get("legal", True)
    retry = return_to_mu(machine) if stuck else []
    return f"mu return on a changed board: retrying {', '.join(retry)}" if retry else None


def next_owned_step(
    machine: Any, *, refused: frozenset | set = frozenset(), rerun: Mapping[str, Any] | None = None,
    g3_choice_handoff: bool = False,
) -> OwnedStep:
    """Who owns the next step, and, for the controller, exactly what it is.

    ``rerun`` is an extra run Duck asked for (D3): ``{"entity_id", "click", "left"}``.
    ``g3_choice_handoff`` (WO-G3-DIRECTED, the live session only) offers Duck one bounded G3 choice per phase.
    """
    # G0 is metadata-derived in every world.  Test it before the world branch: the earlier NAV
    # dispatcher returned Duck here and accidentally bypassed the generic controller answer.
    if machine.gate_id == "G0-ACTION-METADATA":
        return _ordinary_step(machine, refused=refused)
    if orientation_due(machine):
        return _duck(machine, "the orientation turn is due")
    world = control_archetype_prior(machine.ego.affordances)["world_type"]
    if world in {"NAVIGATION", "HYBRID"}:
        return _nav_step(machine, refused=refused, rerun=rerun)
    if world != "CLICK_GOD_MODE":
        return _duck(machine, f"unsupported controller world type {world}")
    if machine.gate_id not in CONTROLLER_GATES:
        return _duck(machine, f"{machine.gate_id} needs judgment")
    return _ordinary_step(machine, refused=refused, rerun=rerun, g3_choice_handoff=g3_choice_handoff)


def _ordinary_step(
    machine: Any, *, refused: frozenset | set = frozenset(),
    rerun: Mapping[str, Any] | None = None, g3_choice_handoff: bool = False,
) -> OwnedStep:
    """Controller ownership shared by CLICK and world-independent exact capabilities."""
    capability = machine.next_probe_capability()  # first: it can advance the gate's own state
    if g3_choice_handoff and capability is not None and _g3_choice_due(machine):
        return _duck(machine, "G3 choice: several rows are eligible; choose one with "
                              "virelai('next_probe', question_id=...), or the controller takes the coverage head")
    if machine.gate_id in PREDICTION_GATES:
        return _relations_step(machine, capability, refused)
    view = machine.gate_view()
    if machine.gate_id == ORBITS:
        return _orbit_step(machine, capability, view, rerun)
    if _answer_due(view):
        return _certified_answer_step(machine, view, refused=refused)
    if capability is None:
        return _duck(machine, f"{machine.gate_id} offers no probe and no answer")
    action, reason = _bound_action(capability)
    if action is None:
        return _duck(machine, reason)
    return OwnedStep(
        CONTROLLER, machine.gate_id, reason, ACTION, action=action,
        probe_token=str(capability["probe_token"]),
    )


def _g3_choice_due(machine: Any) -> bool:
    """Sol, 2026-10-11: at most one bounded handoff per G3 phase per level, only for a genuine choice."""
    from inference.framework import g3_selection

    if machine.gate_id != "G3-LEVERS":
        return False
    adapter = machine._adapters["G3-LEVERS"]
    if not g3_selection.choice_handoff_due(adapter):
        g3_selection.note_coverage_resumed(adapter)
        return False
    g3_selection.note_choice_handoff(adapter)
    return True


def _nav_step(
    machine: Any, *, refused: frozenset | set = frozenset(),
    rerun: Mapping[str, Any] | None = None,
) -> OwnedStep:
    """Controller-owned deterministic movement; Duck still owns explanations."""
    if machine.gate_id == "G1-EGO":
        view = machine.gate_view()
        if _answer_due(view):
            return _duck(machine, "the embodied ego explanation and prospective prediction need judgment")
        capability = machine.next_probe_capability()
        if capability is None:
            return _duck(machine, "G1 offers no exact probe and no answer")
        action, reason = _bound_action(capability)
        if action is None:
            return _duck(machine, reason)
        return OwnedStep(
            CONTROLLER, machine.gate_id, reason, ACTION, action=action,
            probe_token=str(capability["probe_token"]),
        )
    if machine.gate_id == "G2-COUNTER":
        view = machine.gate_view()
        if _answer_due(view):
            return _certified_answer_step(machine, view, refused=refused)
        capability = machine.next_probe_capability()
        if capability is None:
            return _duck(machine, "G2 offers no active target or exact counter probe")
        if capability.get("purpose") != "PILOT_TO_CONTACT":
            action, reason = _bound_action(capability)
            if action is None:
                return _duck(machine, reason)
            return OwnedStep(
                CONTROLLER, machine.gate_id, reason, ACTION, action=action,
                probe_token=str(capability["probe_token"]),
            )
        target = capability.get("target") or {}
        planned = machine.counter.planned_nav_step(target)
        if planned is None:
            return _duck(machine, "G1 evidence does not support another deterministic G2 route step")
        return OwnedStep(
            CONTROLLER, machine.gate_id,
            f"G2 NAV {planned.intent.lower()}: {planned.reason}", ACTION,
            action={"action": planned.action}, probe_token=str(capability["probe_token"]),
            decision={"pilot_intent": planned.intent},
        )
    if machine.gate_id == ORBITS:
        capability = machine.next_probe_capability()
        if capability is not None and rerun and int(rerun.get("left") or 0) > 0:
            entity = str(rerun.get("entity_id") or "")
            planned = machine._adapters[ORBITS].planned_nav_step(entity)
            if planned is None:
                return _duck(machine, f"no evidence-bounded route for the extra run of {entity}")
            return OwnedStep(
                CONTROLLER, ORBITS, f"G4-A NAV extra run {planned.intent.lower()} for {entity}",
                ACTION, action={"action": planned.action}, probe_token=str(capability["probe_token"]),
                decision={"intent": f"NAV:{planned.intent}:{entity}"},
            )
        view = machine.gate_view()
        awaiting = [item for item in view.get("answer_templates") or () if isinstance(item, Mapping)]
        if awaiting:
            return _duck(machine, f"the NAV run of {awaiting[0].get('entity_id')} is confirmed: explaining it is Duck's")
        if capability is None:
            return _duck(machine, "G4-A NAV has no active lever procedure")
        levers = [item for item in (capability.get("target") or {}).get("levers") or () if isinstance(item, Mapping)]
        for status in STUDY_ORDER:
            lever = next((item for item in levers if item.get("status") == status), None)
            if lever is None:
                continue
            planned = machine._adapters[ORBITS].planned_nav_step(str(lever.get("entity_id")))
            if planned is None:
                return _duck(machine, f"no evidence-bounded route to {lever.get('entity_id')}")
            return OwnedStep(
                CONTROLLER, ORBITS, f"G4-A NAV {planned.intent.lower()} for {lever.get('entity_id')}",
                ACTION, action={"action": planned.action}, probe_token=str(capability["probe_token"]),
                decision={"intent": f"NAV:{planned.intent}:{lever.get('entity_id')}"},
            )
        return _duck(machine, "G4-A NAV has no lever the controller can route to")
    if machine.gate_id == "G4-REACTIONS":
        # G4.1 consumes certified G3 channels.  Its answer is world-independent; NAV must reuse
        # the same renderer as CLICK instead of waking Duck merely because contact is embodied.
        return _ordinary_step(machine, refused=refused)
    if machine.gate_id in PREDICTION_GATES:
        capability = machine.next_probe_capability()
        if capability is None:
            # R9-R24 D19 is world-independent: if the level record already
            # certifies G4-B, NAV must consume that answer without waking Duck.
            return _relations_step(machine, capability, refused)
        entity = str((capability.get("target") or {}).get("entity_id") or "")
        planned = machine._adapters[ORBITS].planned_nav_step(entity)
        if planned is None:
            return _duck(machine, f"no evidence-bounded route to prediction target {entity}")
        return OwnedStep(
            CONTROLLER, machine.gate_id, f"{machine.gate_id} NAV {planned.intent.lower()} for {entity}",
            ACTION, action={"action": planned.action}, probe_token=str(capability["probe_token"]),
            decision={"intent": f"NAV:{planned.intent}:{entity}"},
        )
    if machine.gate_id != "G3-LEVERS":
        return _duck(machine, f"the NAV branch for {machine.gate_id} has no computable step yet")
    view = machine.gate_view()
    if _answer_due(view):
        return _certified_answer_step(machine, view, refused=refused)
    capability = machine.next_probe_capability()
    if capability is None:
        return _duck(machine, "G3 NAV needs an answer or has no active target")
    if capability.get("purpose") not in {"PILOT_TO_LEVER_CONTACT", "CONFIRM_LEVER_WITNESS"}:
        return _duck(machine, f"G3 NAV cannot compute {capability.get('purpose')}")
    target = capability.get("target") or {}
    adapter = machine._adapters["G3-LEVERS"]
    planned = adapter.planned_nav_step(target)
    if planned is None:
        return _duck(machine, "G1 evidence does not yet support a deterministic route step")
    return OwnedStep(
        CONTROLLER, machine.gate_id,
        f"G3 NAV {planned.intent.lower()}: {planned.reason}", ACTION,
        action={"action": planned.action}, probe_token=str(capability["probe_token"]),
        decision={"pilot_intent": planned.intent},
    )


def _certified_answer_step(
    machine: Any, view: Mapping[str, Any], *, refused: frozenset | set = frozenset(),
) -> OwnedStep:
    """Render a world-independent certified answer, or identify the judgment still missing."""
    key = (machine.gate_id, int(view.get("revision") or 0), machine.lives.level)
    if key in refused:
        return _duck(machine, f"{machine.gate_id} refused the controller's answer at this revision")
    answer, reason = controller_answer(machine, view)
    if answer is None:
        return _duck(machine, reason)
    return OwnedStep(CONTROLLER, machine.gate_id, reason, ANSWER, answer=answer, refusal_key=key)


def _relations_step(machine: Any, capability: Mapping[str, Any] | None, refused: frozenset | set = frozenset()) -> OwnedStep:
    """G4-B from the record (R9-R24 D19); Duck's frozen predictions are taken by the controller."""
    gate = machine.gate_id
    if gate == RELATIONS and capability is None:
        adapter = machine._adapters[RELATIONS]
        key = (gate, adapter.revision, machine.lives.level)
        answer = None if key in refused else adapter.record_answer()
        if answer is not None:
            return OwnedStep(CONTROLLER, gate, "G4-B: the level's record certifies the relations (ruling G-1)",
                             ANSWER, answer=answer, refusal_key=key)
    if capability is not None:
        target = capability.get("target") or {}
        return OwnedStep(
            CONTROLLER, gate, f"{gate}: take {target.get('prediction_id')}, the prediction Duck froze",
            ACTION, action=dict(capability["actions"][0]), probe_token=str(capability["probe_token"]),
        )
    view = machine.gate_view()
    recent = (view.get("progress") or {}).get("recent") or [(view.get("subject") or {}).get("last_test")]
    graded = f"{recent[-1]['prediction_id']} was graded {recent[-1]['status']}; " if recent[-1] else ""
    if gate == LAW:
        return _duck(machine, graded + "testing the description with one new prediction is Duck's")
    return _duck(machine, graded + "the next prediction, or the description of the lever set, is Duck's")


def _orbit_step(
    machine: Any, capability: Mapping[str, Any] | None, view: Mapping[str, Any],
    rerun: Mapping[str, Any] | None,
) -> OwnedStep:
    """G4-A (D3): the controller presses; Duck explains each confirmed orbit."""
    if capability is not None and rerun and int(rerun.get("left") or 0) > 0:
        return OwnedStep(
            CONTROLLER, ORBITS, f"extra run of {rerun['entity_id']} Duck asked for", ACTION,
            action=dict(rerun["click"]), probe_token=str(capability["probe_token"]),
        )
    awaiting = [item for item in view.get("answer_templates") or () if isinstance(item, Mapping)]
    if awaiting:
        return _duck(machine, f"the run of {awaiting[0].get('entity_id')} is confirmed: explaining it is Duck's")
    if capability is None:
        return _duck(machine, "G4-A has no lever left to run")
    levers = [item for item in (capability.get("target") or {}).get("levers") or () if isinstance(item, Mapping)]
    for status in STUDY_ORDER:
        lever = next((item for item in levers if item.get("status") == status), None)
        if lever is not None:
            return OwnedStep(
                CONTROLLER, ORBITS, f"G4-A: run {lever.get('entity_id')} ({status})", ACTION,
                action=dict(lever["click"]), probe_token=str(capability["probe_token"]),
            )
    return _duck(machine, "G4-A has no lever the controller can run")


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
    if template.get("answer_kind") == "LEVER_EFFECT_ANATOMY":
        return _anatomy_answer(template), "G4.1 anatomy from the certified channels"
    if template.get("answer_kind") == "LEVER_DOSSIER":
        return _dossier_answer(template), "G3 dossier from the effect summary"
    # Sol, 2026-10-03: reuse accepted causal meaning; the current target facts
    # still come from this controller-certified template.
    if (
        template.get("answer_kind") == "TARGET_REACHABILITY"
        and template.get("semantic_reuse") is True
    ):
        return dict(template), "G3 reachability meaning reused for this certified target"
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


REPEAT_TEXT = {  # R9-R22 D7: the repeat press, said as observed (a typing input for G4, never a retraction)
    "NULL_AT_OBSERVED_STATE": "; a repeat press then changed nothing (it moved, then held).",
    "OBSERVED_STATE_RECURRENCE": "; a repeat press then undid it exactly.",
    "NOVEL_STATE_REVEALED": "; a repeat press then changed the board again, to a third state.",
}


def _dossier_answer(template: Mapping[str, Any]) -> dict[str, Any]:
    summary = template["effect_summary"]
    repeat = (template.get("repeat") or {}).get("repeat_disposition")
    action = template["intervention"]
    site = f"({action.get('row')}, {action.get('col')})" if "row" in action else str(action.get("action"))
    remote = int(summary.get("remote_changed_cell_count") or 0)
    text = (
        f"Activating {template['target_member_id']} via {site} rewrote {summary.get('local_changed_cell_count')} "
        f"of its own cells (bbox {summary.get('local_changed_bbox')}) and {remote} cells elsewhere"
        + (f" (bbox {summary.get('remote_changed_bbox')})" if remote else "")
        + REPEAT_TEXT.get(repeat, "; this is the preserved first attributed witness.")
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
        "falsifier": "The same activation from the same masked state leaves the object unchanged.",
        "limitations": [RENDERED],
    }


def _anatomy_answer(template: Mapping[str, Any]) -> dict[str, Any]:
    entity = template["entity_id"]
    phrases = [
        f"{channel.get('channel_id')} rewrites "
        + ", ".join(f"{before}->{after}" for before, after, *_rest in channel.get("integer_transitions") or ())
        + f" over {channel.get('changed_cell_count')} {str(channel.get('locality') or '').lower()} cells"
        for channel in template.get("effect_channels") or ()
    ]
    return {
        **template,
        "mechanism_explanation": f"Lever {entity}: " + "; ".join(phrases) + ", counter changes masked.",
        "competing_models": ["A hidden process changed the region at the same moment as the click."],
        "falsifier": "The same click from the same masked state produces a different exact residue.",
        "limitations": [*template.get("limitations", ()), RENDERED],
    }


def _inventory_answer(template: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    levers, nulls = list(template["lever_entities"]), list(template.get("clean_null_entities") or ())
    mu = list(template.get("ambiguous_entities") or ())
    if mu and not levers:
        return None, "G3 has bounded ambiguity and no certified lever: the coverage report is Duck's"
    return {
        **template,
        "explanation": (  # R9-R23 D17: levers here may act locally or remotely
            f"The complete probe roster found {len(levers)} levers whose activations produce attributed "
            f"changes ({', '.join(levers)}) and {len(nulls)} objects closed with scoped null evidence"
            + (f"; {len(mu)} mystery objects ({', '.join(mu)}) are set aside in the mu bucket, to retry "
               "when the board has changed (G3 closes PARTIAL)" if mu else "")
            + "; counter changes were excluded by the mask as bookkeeping."
        ),
        "competing_models": ["An object closed as null may respond from a different world state."],
        "falsifier": "A clean-null object responds to the same click from the same masked state.",
        "limitations": [RENDERED],
    }, "G3 inventory"


# ---- stop-and-wake ----------------------------------------------------------------------------

def wake_signals(machine: Any, result: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """What ``wake_reason`` compares before and after a controller action.

    The counter's ticks come from the certified budget; actions and seconds remaining come from
    the environment's step payload (``solver.timing_payload``).
    """
    result = result or {}
    return {
        "rejected_candidates": len(getattr(machine.counter, "_rejected_candidates", ()) or ()),
        "ticks": (world_budgets(machine) or {}).get("counter_ticks_remaining"),
        "actions": result.get("actions_remaining"),
        "seconds": result.get("time_remaining_seconds"),
    }


def _crossed(before: Any, after: Any, threshold: float) -> bool:
    return after is not None and after <= threshold and (before is None or before > threshold)


def _ladder_restarted(machine: Any, boundary: list[str]) -> bool:
    """A level change that froze the level and restarted the ladder at G0: level entry is the controller's (R9-R21 D6)."""
    return boundary == ["level_completed"] and bool(getattr(machine, "levels", None)) and machine.gate_id == "G0-ACTION-METADATA"


def wake_reason(
    machine: Any, event: Mapping[str, Any] | None, result: Mapping[str, Any],
    before: Mapping[str, int] | None = None,
) -> str | None:
    """Why Duck must take the next step after a controller action, or None to continue."""
    boundary = [key for key in BOUNDARY_KEYS if result.get(key)]
    if boundary and not _ladder_restarted(machine, boundary):
        return "boundary event: " + ", ".join(boundary)
    event = event or {}
    comparison = event.get("counter_comparison") or {}
    if comparison.get("outcome") == "CONTRADICTED" and comparison.get("evidence_ref") == event.get("evidence_id"):
        return "the frozen G2 prediction was contradicted"
    after = wake_signals(machine, result)
    before = before or {}
    if after["rejected_candidates"] > int(before.get("rejected_candidates", after["rejected_candidates"])):
        return "G2 rejected its counter candidate"
    if event.get("gate_status_after") in {"UNRESOLVED", "REOPENED"}:
        return f"{event.get('gate_id')} is {event['gate_status_after']}"
    confirmation = (event.get("confirmation") or {}).get("status")
    readings = getattr((getattr(machine, "_adapters", None) or {}).get("G3-LEVERS"), "_repeat_readings", {})
    if confirmation in {"CONTRADICTED", "BOUNDARY_DEFERRED"} and not certified(event["confirmation"], readings):
        return f"a G3 confirmation was {confirmation}"
    attribution = event.get("attribution") or {}
    if (
        event.get("bounded_ambiguity")
        or (
            event.get("pilot_intent") != "APPROACH"
            and attribution.get("disposition") in AMBIGUOUS_DISPOSITIONS
        )
    ):
        return f"attribution is {attribution.get('disposition') or 'ambiguous'}"
    if attribution.get("boundary_state"):
        return "a boundary interrupted the attribution"
    for name, threshold, unit in (
        ("ticks", WAKE_TICKS_REMAINING, "counter ticks"), ("actions", WAKE_ACTIONS_REMAINING, "actions"),
        ("seconds", WAKE_SECONDS_REMAINING, "seconds"),
    ):
        if _crossed(before.get(name), after[name], threshold):
            return f"the budget is nearly spent: {after[name]:g} {unit} left"
    return None


__all__ = [
    "ACTION", "ANSWER", "CONTROLLER", "DUCK", "OwnedStep", "controller_answer",
    "next_owned_step", "wake_reason", "wake_signals",
]
