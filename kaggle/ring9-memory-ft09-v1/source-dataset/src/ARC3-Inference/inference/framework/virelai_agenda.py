"""Evidence-derived exploration agenda. No actions and no independent belief store."""
from dataclasses import asdict, dataclass
from typing import Any
from inference.framework.virelai_world_model import WorldModel

@dataclass(frozen=True)
class Question:
    id: str
    stage: str
    subject: str
    question: str
    disposition: str
    evidence: tuple[str, ...] = ()
    limitation: str = ""
    answer: str | None = None


def compile_agenda(model: WorldModel) -> dict[str, Any]:
    level = model.current_level
    prefix = f"L{level}"
    claims = {c.claim_id: c for c in model.claims}
    questions = []
    # A witnessed action-bound mechanic establishes a control channel without
    # pretending that its moving object has already been identified as EGO.
    action_mechanics = []
    for mechanic in model.mechanics:
        claim = claims.get(mechanic.claim_id)
        if (level in mechanic.levels_observed and mechanic.trigger_action != "RESET"
                and claim is not None and claim.evidence
                and claim.status in {"OBSERVED", "INFERRED"}
                and claim.contradiction_count == 0):
            action_mechanics.append(mechanic)
    # Role names are an existing serialized claim convention, not new inference.
    for stage, role, wording in (
        ("CONTROL", "EGO", "Establish embodied control, pointer control, or both using offered actions and probes."),
        ("COUNTER", "COUNTER", "Distinguish recurring autonomous changes from effects of particular actions or targets."),
        ("LEVERS", "LEVER", "Find reachable interactions and distinguish self-effects from changes in other entities."),
    ):
        relevant = tuple(c for c in model.claims if c.scope == prefix and
                         c.predicate.rsplit("semantic role ", 1)[-1] == role)
        supported = tuple(c for c in relevant if c.status in {"OBSERVED", "INFERRED"} and c.evidence and c.contradiction_count == 0)
        witnesses = tuple(c.claim_id for c in relevant if c.evidence and c.status != "CONTRADICTED")
        control_by_channel = stage == "CONTROL" and bool(action_mechanics)
        disposition = "CLOSED_BY_DATA" if supported or control_by_channel else "OPEN"
        if control_by_channel:
            witnesses = tuple(sorted({m.claim_id for m in action_mechanics if m.claim_id}))
        questions.append(Question(f"{prefix}:{stage}", stage, prefix, wording, disposition,
                                  witnesses,
                                  "A witnessed control channel does not identify the embodied or pointer EGO."
                                  if control_by_channel and not supported else
                                  "Candidate detector output does not establish a role." if witnesses and not supported else "",
                                  "Witnessed offered-action channel changes visible state."
                                  if control_by_channel else None))
    role_questions = {
        "EGO": "Probe this candidate's action mapping, displacement, collision, reachability and interaction range; separate autonomous changes.",
        "COUNTER": "Vary action and target: does this candidate change anyway? Measure increment, reset, saturation and whether it constrains available play.",
        "LEVER": "Compare activation with a nearby control trial. Identify contact conditions, every affected object, response magnitude, limits and reversal.",
        "WALL": "Test approach from another direction. Distinguish collision from a missing action condition; keep untested cells unknown.",
        "GROUND": "Check whether apparent ground changes with traversal, exchanges cells, or responds to an interaction.",
    }
    for obj in model.objects:
        if obj.level != level or obj.last_seen_step != model.observed_through_step:
            continue
        for cid in obj.claim_ids:
            claim = claims.get(cid)
            if claim is None or claim.status == "CONTRADICTED":
                continue
            role = claim.predicate.rsplit("semantic role ", 1)[-1]
            if role in role_questions and claim.evidence:
                questions.append(Question(f"{prefix}:{obj.object_id}:{role}", "DEPTH", obj.object_id,
                    f"{role} candidate, class {obj.integer_classes}, last bbox {obj.bbox}: " + role_questions[role],
                    "OPEN", (cid,), "Detector candidate, not established function. Inspect object and model_evidence before targeting."))
    for mechanic in model.mechanics:
        if level not in mechanic.levels_observed:
            continue
        claim = claims.get(mechanic.claim_id)
        valid = claim is not None and claim.status in {"OBSERVED", "INFERRED"} and bool(claim.evidence) and claim.contradiction_count == 0
        properties = (
            ("magnitude", "How large is this effect in the observed trials?", mechanic.magnitude),
            ("conditions", "Under which conditions does this interaction work or fail?", None),
            ("recurrence", "Does repeated activation cycle, drift, or depend on prior history?", str(mechanic.period) if mechanic.period is not None else None),
            ("limits", "Does the response stop at a boundary, or is an activation condition missing?", mechanic.endpoint_behavior),
            ("reverse", "Can another interaction restore all affected state, not just one visible quantity?", mechanic.inverse_rule_id),
        )
        for kind, wording, answer in properties:
            closed = valid and answer is not None
            questions.append(Question(f"{prefix}:{mechanic.rule_id}:{kind}", "DEPTH", mechanic.rule_id,
                wording, "CLOSED_BY_DATA" if closed else "OPEN", (mechanic.claim_id,) if claim else (),
                "Answer applies only to the recorded scope; new evidence may reopen it.", answer if closed else None))
    observed_win = bool(model.wins)
    if observed_win:
        questions.insert(0, Question(f"{prefix}:WIN", "EXPLAIN_AND_CARRY", prefix,
            "Explain the observed win using standing conditions and the final transition; reconfirm bindings and mechanics here. Preserve alternative explanations.",
            "OPEN", tuple(cid for w in model.wins for cid in w.claim_ids),
            "A recorded win does not prove its cause. New-level roles remain unconfirmed."))
    unbounded_question_count = len(questions)
    # The agenda is an attention surface, not a lossless library dump. Preserve
    # prerequisites and win work, then keep a small deterministic depth frontier.
    fixed = [q for q in questions if q.stage != "DEPTH"]
    depth = [q for q in questions if q.stage == "DEPTH"]
    depth.sort(key=lambda q: (q.disposition != "OPEN", not bool(q.evidence), q.subject, q.id))
    questions = fixed + depth[:24]
    active = [q for q in questions if q.disposition == "OPEN"]
    # Candidate evidence permits deeper investigation, never factual closure.
    focus = next((q.stage for q in active if q.stage != "EXPLAIN_AND_CARRY" and (not q.evidence or q.stage == "DEPTH")), active[0].stage if active else "COVERAGE")
    if observed_win and model.observed_through_step <= max(w.transition_id for w in model.wins) + 1:
        focus = "EXPLAIN_AND_CARRY"
    return {"schema": "virelai-agenda-v1", "game_id": model.game_id, "current_level": level,
            "model_version": model.model_version, "observed_through_step": model.observed_through_step,
            "focus": focus,
            "first_win_observed": observed_win, "questions": [asdict(q) for q in questions],
            "questions_total_unbounded": unbounded_question_count,
            "questions_frontier_truncated": unbounded_question_count > len(questions),
            "working_memory": working_memory(model),
            "limitations": ["Initial agenda: not a saturation or completeness certificate.",
                "An unresolved prerequisite is not an action barrier; investigate other informative questions when blocked."]}


def working_memory(model: WorldModel) -> list[str]:
    """Small factual context; historical model coordinates are never action commands."""
    claims = {c.claim_id: c for c in model.claims}
    lines = []
    relevant = [m for m in model.mechanics if model.current_level in m.levels_observed]
    if not relevant:
        relevant = list(model.mechanics)
    for rule in relevant[:2]:
        c = claims.get(rule.claim_id)
        if c is None:
            continue
        refs = ", ".join(str(e.transition_id) for e in c.evidence[:3])
        description = rule.transformation[:180]
        lines.append(f"Effect ({c.status}, {c.scope}): {rule.trigger_action} accompanied {description}. "
                     f"Magnitude: {rule.magnitude or 'unresolved'}. Witness transitions: {refs or 'none'}. "
                     f"Inspect virelai('mechanic', id={rule.rule_id!r}).")
    if model.wins:
        w = max(model.wins, key=lambda x: x.transition_id)
        lines.append(f"Observed win in level {w.completed_level}: {w.winning_action} at transition {w.transition_id}; "
                     f"{w.earlier_same_action_failures} recorded earlier same-action failures. "
                     f"Cause: {w.causal_status}. The action alone is not an established win rule. "
                     f"Inspect virelai('lesson', level={w.completed_level}).")
        if w.separator_predicates:
            lines.append("Candidate distinctions, not proven causes: " + "; ".join(w.separator_predicates[:2])[:220])
        lines.append("Rebind to this level's current objects; prior coordinates and roles are not confirmed here.")
    return lines


def render_agenda(agenda: dict[str, Any]) -> str:
    lines = ["VIRELAI EXPLORATION AGENDA", f"Level {agenda['current_level']}; evidence through step {agenda['observed_through_step']}; focus {agenda['focus']}."]
    lines.extend(agenda.get("working_memory", []))
    active = [q for q in agenda['questions'] if q['disposition'] == 'OPEN']
    active.sort(key=lambda q: q["stage"] != agenda["focus"])
    for q in active[:2]:
        lines.append(f"Question: {q['question']} Inspect virelai('question', id={q['id']!r}).")
    closed = [q for q in agenda['questions'] if q['disposition'] == 'CLOSED_BY_DATA']
    frontier_note = (f" Displaying a bounded frontier from {agenda['questions_total_unbounded']} generated questions."
                     if agenda.get("questions_frontier_truncated") else "")
    lines.append(f"Frontier: {len(active)} open; {len(closed)} answered from recorded data.{frontier_note} Candidate evidence permits deeper investigation, not role confirmation. If blocked, pursue another informative question. A recorded win does not prove its cause.")
    return "\n".join(lines)


def agenda_changes(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[str]:
    """Report evidential changes, never infer closure from missing/truncated questions."""
    if not previous or previous.get("game_id") != current.get("game_id"):
        return []
    before = {q["id"]: q for q in previous.get("questions", [])}
    lines = []
    for q in current.get("questions", []):
        old = before.get(q["id"])
        if not old or old["disposition"] == q["disposition"]:
            continue
        if q["disposition"] == "OPEN":
            lines.append("Reopened: " + q["question"])
        elif q["disposition"] == "CLOSED_BY_DATA":
            lines.append("Answered by evidence: " + q["question"] + " " + str(q.get("answer") or ""))
    return lines[:3]
