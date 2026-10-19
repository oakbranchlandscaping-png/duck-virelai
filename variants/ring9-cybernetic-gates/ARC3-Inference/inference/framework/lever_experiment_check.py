"""The saved model's B3 chain: admitted limits experiment → its step receipts → its typed close and observations.

Author: Claude (Alpha build seat), 2026-10-18 (WO-G4-DOSSIER-B3; interface §5; revision 2 after Sol's review). A
v9 validation step (the frozen v8 contract never runs it), called by ``lever_dossier_selection.problems`` with the
G4-B admissions the selection log paired with their closes; pure, it reads only the model and the persisted contract
(``lever_experiment_contract``), never the experiment engine. What v9 holds of an experiment: the audit rows
(admission and close; the close's reason names its type, ``TYPE: detail``), the level receipt index (each step's
probe id names its experiment and step), the transitions' recorded pixel rewrites, and B1's observations. The
outcome is recomputed from those and must equal the type the close records.

Refused, with every hash a forger can reach recomputed:

* a step receipt whose experiment was never admitted, or that names another lever, level or life than its admission;
* steps that are not ``1..m`` exactly once, of more than one kind, or beyond the kind's cap;
* a close whose type its event and kind cannot carry: a ``FINISHED`` close names one of its kind's finished types
  (never an interruption, never the other kind's), a ``STALE`` close a typed interruption (never an outcome);
* a ``FINISHED`` experiment with no step;
* a ``FINISHED`` self-reversal whose subject's observations (same level and life, stated) cite a return at any step
  but the last, or cite none although fewer steps than the cap were taken; and one whose recorded type is not what
  they show: a two-state return ``REVERSAL_OBSERVED``, a longer cycle ``RECURRENCE_OBSERVED``, no return ``CAPPED``;
* a ``FINISHED`` persistence trial that is not one step its observations count as a trial, or whose recorded type is
  not what the record shows: ``PERSISTENCE_INCONCLUSIVE`` when the acting lever's own region did not change in that
  transition's recorded rewrite, else ``PERSISTENCE_CHANGED`` or ``PERSISTENCE_UNCHANGED`` as the observations count it.

Observations failed closed (missing or duplicated execution evidence, a mismatched record) or of a later life state
nothing, so no outcome is recomputed from them: the close's type must still fit its event and kind, and the receipts
are still checked.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def _steps(levels: Mapping[Any, Mapping[str, Any]]) -> tuple[dict[tuple, list[tuple]], list[str]]:
    """Every experiment step receipt in the model, keyed by (level, life, lever, admission): (k, code, ref, receipt)."""
    from inference.framework.lever_experiment_contract import parse

    found: dict[tuple, list[tuple]] = {}
    problems = []
    for number, level in levels.items():
        lives = {item["transition_id"]: item.get("life") for item in (level.get("description") or {}).get("transitions") or ()}
        for ref, receipt in sorted(level["receipts"]["evidence"].items()):
            step = parse(receipt.get("probe_id"))
            if step is None:
                continue
            life = lives.get(receipt.get("transition_id"), step["life"])
            if step["level"] != number or life != step["life"]:
                problems.append(f"receipt {ref} ({receipt['probe_id']}) lies outside the level and life it names")
            key = (step["level"], step["life"], step["entity_id"], step["admission"])
            found.setdefault(key, []).append((step["k"], step["code"], ref, receipt))
    return found, problems


def problems(levels: Mapping[Any, Mapping[str, Any]], pairs: Sequence[tuple[Mapping[str, Any], Any, int]],
             journal: bool) -> list[str]:
    """Every way the saved model breaks the B3 chain (``pairs``: G4-B admissions, their close or None, ordinal).

    ``journal``: the model embeds a readable H2 journal (sealed or open), the record of every admission. Without one
    (the live view, H1, an unavailable or corrupt journal) each experiment's receipts are still checked as a group."""
    steps, found = _steps(levels)
    admitted = {}
    for row, closed, ordinal in pairs:
        admitted[(row.get("level"), row.get("life"), row["refs"]["subject"], ordinal)] = (row, closed)
    for key, items in sorted(steps.items(), key=lambda kv: str(kv[0])):
        if key not in admitted and journal:
            found += [f"receipt {ref} ({receipt['probe_id']}) belongs to no admitted experiment" for _k, _c, ref, receipt in items]
        elif key not in admitted:
            found += _experiment(levels.get(key[0]), key, None, sorted(items))
    for key, (row, closed) in sorted(admitted.items(), key=lambda kv: str(kv[0])):
        found += _experiment(levels.get(key[0]), key, closed, sorted(steps.get(key, ())))
    return found


def _experiment(level: Mapping[str, Any] | None, key: tuple, closed: Mapping[str, Any] | None,
                items: Sequence[tuple]) -> list[str]:
    """One experiment: its receipts as a group, then (when closed) its typed close against what its evidence shows."""
    from inference.framework.lever_experiment_contract import CODES, admits, experiment_id, terminal_type

    codes = {code for _k, code, _ref, _receipt in items}
    code = next(iter(codes)) if len(codes) == 1 else None
    name = experiment_id(code or "?", key[2], key[0], key[1], key[3])
    if len(codes) > 1:
        return [f"experiment {name}: its steps are of more than one kind"]
    cap = CODES[code][2] if code else None
    if [k for k, *_ in items] != list(range(1, len(items) + 1)) or (cap is not None and len(items) > cap):
        return [f"experiment {name}: its steps are not 1..{len(items)} once each within its cap"]
    if closed is None:
        return []  # a valid admission may stay open at any stop
    event = str(((closed.get("refs") or {}).get("source_event") or {}).get("event"))
    terminal = terminal_type((closed.get("reason") or {}).get("text"))
    if not admits(event, code, terminal):
        return [f"experiment {name}: its {event} close names {terminal or 'no terminal type'}, which a "
                f"{code or 'step-less'} experiment's {event} close may not carry"]
    if event != "FINISHED":
        return []
    if not items:
        return [f"experiment {name}: FINISHED with no step receipt"]
    found, shown = _outcome(level, key, name, code, items)
    if shown is not None and shown != terminal:
        found.append(f"experiment {name}: its close records {terminal}, but its evidence shows {shown}")
    return found


def _outcome(level: Mapping[str, Any] | None, key: tuple, name: str, code: str,
             items: Sequence[tuple]) -> tuple[list[str], str | None]:
    """(problems, the finished type the evidence shows): recomputed from the subject's observations where they speak
    for the experiment's life, else (nothing failed closed or of a later life is a finding) only its kind is checked."""
    observations = ((level or {}).get("lever_dossiers") or {}).get(key[2], {}).get("observations") or {}
    scope = observations.get("scope") or {}
    if observations.get("status") != "OBSERVED" or (scope.get("level"), scope.get("life")) != key[:2]:
        return [], None
    transitions = {receipt["transition_id"]: k for k, _code, _ref, receipt in items}
    if code == "PERSISTENCE":
        return _persistence(level, key, name, observations, list(transitions))
    return _reversal(name, code, observations, transitions, len(items))


def _reversal(name: str, code: str, observations: Mapping[str, Any], transitions: Mapping[int, int],
              steps: int) -> tuple[list[str], str | None]:
    from inference.framework.lever_experiment_contract import CODES

    returns = [(transitions[case["transition_id"]], case["cycle_length"]) for reading in ("toggle_reversal", "self_recurrence")
               for case in observations["reversal"][reading]["cases"] if case["transition_id"] in transitions]
    if returns and [k for k, _cycle in returns] != [steps]:
        return [f"experiment {name}: a return is cited at step {sorted(returns)[0][0]}, not its last step {steps}"], None
    if not returns and steps != CODES[code][2]:
        return [f"experiment {name}: no return is cited, yet it finished after {steps} of {CODES[code][2]} steps"], None
    if not returns:
        return [], "CAPPED"
    return [], "REVERSAL_OBSERVED" if returns[0][1] == 2 else "RECURRENCE_OBSERVED"


def _persistence(level: Mapping[str, Any], key: tuple, name: str, observations: Mapping[str, Any],
                 transitions: Sequence[int]) -> tuple[list[str], str | None]:
    persistence = observations["persistence"]
    changed = {case["transition_id"] for case in persistence["changed_cases"]}
    if len(transitions) != 1 or not set(transitions) <= set(persistence["unchanged_transitions"]) | changed:
        return [f"experiment {name}: its persistence trial is not one step its observations count"], None
    responded = _acting_responded(level, key[2], transitions[0])
    if responded is None:
        return [], None  # the acting lever's own response is not on the record: only the kind is checked
    if not responded:
        return [], "PERSISTENCE_INCONCLUSIVE"
    return [], "PERSISTENCE_CHANGED" if transitions[0] in changed else "PERSISTENCE_UNCHANGED"


def _cells(runs: Any) -> set[tuple[int, int]]:
    return {(int(row), col) for row, start, end in runs or () for col in range(int(start), int(end) + 1)}


def _acting_responded(level: Mapping[str, Any], subject: str, transition: int) -> bool | None:
    """Whether the trial's press changed its own lever's region (that lever's LOCAL anatomy cells, else all its
    channels: the region G4.1 recorded), read from the transition's recorded pixel rewrite; None when either is
    missing."""
    record = next((item for item in (level.get("description") or {}).get("transitions") or ()
                   if item.get("transition_id") == transition), None)
    if record is None or not isinstance(record.get("pixel_rewrite"), Mapping):
        return None
    for entity, dossier in sorted((level.get("lever_dossiers") or {}).items()):
        facts = dossier["chapters"]["anatomy"].get("facts") or {}
        if entity == subject or facts.get("intervention") != record.get("action"):
            continue
        channels = [item for item in facts.get("channels") or () if isinstance(item, Mapping)]
        local = [item for item in channels if item.get("locality") == "LOCAL"] or channels
        region = set().union(*(_cells(item.get("cell_runs")) for item in local)) if local else set()
        moved = set().union(*(_cells(group.get("cell_runs")) for group in record["pixel_rewrite"].get("changed") or ()
                              if group.get("outcome") == "CHANGED")) if record["pixel_rewrite"].get("changed") else set()
        return bool(region & moved) if region else None
    return None


__all__ = ["problems"]
