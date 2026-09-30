"""Intent is not evidence. Evaluate only declared, directly observable predictions."""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Intent:
    id: str
    question_id: str
    submitted_at: int
    level: int
    model_version: int
    action_id: int
    acted_cell: tuple[int, int] | None
    prediction: str
    scope_cell: tuple[int, int] | None


ACTION_IDS = {"RESET": 0, "UP": 1, "DOWN": 2, "LEFT": 3, "RIGHT": 4, "SPACE": 5, "MOUSE": 6}


def _cell(value):
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(type(x) is not int or x < 0 for x in value):
        raise ValueError("cell must be two nonnegative integers")
    return tuple(value)


def make_intent(params, agenda, ordinal):
    qid = params.get("question_id")
    question = next((q for q in agenda["questions"] if q["id"] == qid), None)
    if question is None or question["disposition"] != "OPEN":
        raise ValueError("intent requires an existing OPEN question")
    specification = params.get("action")
    if not isinstance(specification, dict):
        raise ValueError("intent requires action={'action':'UP'} or action={'action':'MOUSE','row':r,'col':c}")
    action_name = str(specification.get("action") or "").strip().upper()
    if action_name not in ACTION_IDS:
        raise ValueError("action.action must be one of RESET, UP, DOWN, LEFT, RIGHT, SPACE or MOUSE")
    available = {str(item).strip().upper() for item in params.get("valid_actions", ())}
    if available and action_name not in available:
        raise ValueError(f"{action_name} is not currently offered; available actions: {', '.join(sorted(available))}")
    action = ACTION_IDS[action_name]
    prediction = params.get("prediction", "UNKNOWN")
    if prediction not in {"CHANGED", "UNCHANGED", "UNKNOWN"}:
        raise ValueError("prediction must be CHANGED, UNCHANGED or UNKNOWN")
    target = _cell([specification.get("row"), specification.get("col")]) if action_name == "MOUSE" else None
    if action == 6 and target is None:
        raise ValueError("MOUSE intent requires integer row and col in the action dictionary")
    if action_name != "MOUSE" and any(key in specification for key in ("row", "col")):
        raise ValueError("row and col only apply to MOUSE")
    return Intent(f"E{ordinal}", qid, agenda["observed_through_step"], agenda["current_level"], agenda["model_version"],
                  action, target, prediction, _cell(params.get("scope_cell")))


def evaluate(intent, transition):
    result = {"intent_id": intent.id, "question_id": intent.question_id,
              "transition_id": transition.transition_id, "prediction": intent.prediction,
              "scope_cell": intent.scope_cell, "question_closed": False}
    if transition.actor != "DUCK" or transition.level_before != intent.level:
        return {**result, "outcome": "NOT_EVALUATED", "reason": "actor or level differs"}
    if transition.action_id != intent.action_id or transition.acted_cell != intent.acted_cell:
        return {**result, "outcome": "NOT_ATTEMPTED", "reason": "next action did not match declared interaction"}
    if transition.action_id == 0 or transition.level_completed or transition.game_over or transition.run_complete or transition.geometry_changed:
        return {**result, "outcome": "NOT_EVALUATED", "reason": "reset, terminal boundary or geometry change requires separate interpretation"}
    total_changes = transition.cell_delta_count
    if intent.scope_cell is not None:
        shape = transition.before_shape
        if shape is None or intent.scope_cell[0] >= shape[0] or intent.scope_cell[1] >= shape[1]:
            return {**result, "outcome": "NOT_EVALUATED", "reason": "scope outside observed grid"}
        scoped_changes = sum((d.row, d.col) == intent.scope_cell for d in transition.cell_deltas)
        changed = scoped_changes > 0
        remote_changes = max(0, total_changes - scoped_changes)
        tested_scope = f"cell {intent.scope_cell}"
    else:
        changed = transition.cell_delta_count > 0
        remote_changes = 0
        tested_scope = "whole visible grid"
    observed = "CHANGED" if changed else "UNCHANGED"
    verdict = "UNRESOLVED" if intent.prediction == "UNKNOWN" else "SUPPORTED" if observed == intent.prediction else "CONTRADICTED"
    if intent.scope_cell is not None:
        observed_summary = f"Tested {tested_scope}: {observed.lower()}. Other cells changed: {remote_changes}."
    else:
        observed_summary = (f"Tested {tested_scope}: {observed.lower()} ({total_changes} cell rewrites). "
                            "This does not separate the intended effect from autonomous change.")
    return {**result, "outcome": verdict, "observed": observed,
            "tested_scope": tested_scope, "total_cell_delta_count": total_changes,
            "other_cell_delta_count": remote_changes, "observed_summary": observed_summary,
            "limitation": "The verdict applies only to the declared variable and scope. Remote changes may be lever effects or autonomous processes; no role, causality, reachability or universal law is established."}
