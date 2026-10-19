"""WO-G4-DOSSIER-B (B1): each lever's record-derived observations — current region state, persistence, reversal.

Author: Claude (Alpha build seat), 2026-10-18. Interface: ``INTERFACE_WO_G4_DOSSIER_B_v1``; Sol's rulings 1-7 (B1).

Pure over the level's own record, never an experiment and never a gate call:

* ``observe`` reads the machine once per census (attribute reads only: the transition record, the current board,
  the counter mask, the G4.1 anatomies and the G3 ledger's current cells; never ``_ensure_*``): it rebuilds every
  board backward from now (the record is lossless, D18) and keeps one **scope** — this level and one life;
* ``derive`` turns that scope into one lever's observations. Nothing crosses a life or a level (ruling 3): the scope
  is the level's last life; a death or a level change ends it, and a death with no later row leaves a new, empty
  life (everything ``UNTESTED``). A transition is a trial only when its evidence id resolves on this level.

Resets (revision 2, Sol's review): a reset that opens the life is its **entry** — the board after it is the life's
first state, and the reset row is neither an intervention nor part of any return (``entry_reset`` names it). A reset
anywhere else inside the life leaves the observations failed closed (``RESET_INSIDE_LIFE``): nothing is skipped.

What is recorded (ruling 2):

* ``current_region_state`` — the lever region's present content, labelled S0, S1, ... in first-seen order within
  the scope. It is called an **orbit phase** only when an accepted orbit maps its states exactly onto that run's
  positions (``orbit_phase``);
* ``persistence`` — observed stability under cited interventions (other levers' presses and other actions):
  tested, unchanged and changed counts; every unchanged trial is cited by its transition (each recorded transition
  has exactly one evidence receipt on the level, which the validator resolves), every changed one by its transition
  and evidence id; zero trials is ``UNTESTED``;
* ``reversal`` — four separate readings of a return to an earlier state: ``toggle_reversal`` (the lever's own
  press, a two-state return), ``self_recurrence`` (its own press, through a longer cycle: recurrence, not
  reversal), ``cross_reversal`` (another lever's press) and ``other_return`` (an action that pressed no lever).

A region's state is the raw content of the lever's G4.1 anatomy cells (its LOCAL channels, else all of them), the
same reading as G4-B's ``state_now`` (``level_record.region_histories``).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from inference.framework import strict_json

TERMINAL_STATES = ("GAME_OVER", "WIN", "RESET")
ENDING_STATES = ("GAME_OVER", "WIN")  # a death or a win ends the life; a reset only ever opens one
RESET_INSIDE_LIFE = "RESET_INSIDE_LIFE"
CATEGORIES = ("toggle_reversal", "self_recurrence", "cross_reversal", "other_return")
OBSERVATION_KEYS = ("status", "basis", "scope", "region", "current_region_state", "persistence", "reversal",
                    "failure", "digest")
STATUSES = ("OBSERVED", "NOT_BUILT", "FAILED_CLOSED")
PHASE_BASES = ("EXACT_ORBIT_MAPPING", "NO_ACCEPTED_ORBIT", "ORBIT_OUTSIDE_SCOPE", "NOT_EXACT")


# ---- the machine read, once per census -------------------------------------------------------------------------

def _boards(machine: Any) -> dict[int, tuple[list[list[int]], list[list[int]]]] | None:
    """transition id -> (board before, board after), rebuilt backward from the current board over the whole record."""
    from inference.framework.card_builder import _current_grid

    grid = _current_grid(machine)
    if grid is None:
        return None
    out, after = {}, [list(row) for row in grid]
    for row in sorted(machine.transition_index, key=lambda item: int(item["transition_id"]), reverse=True):
        before = [list(line) for line in after]
        for r, c, old, _new in row.get("changed") or ():
            if old is not None:
                before[r][c] = old
        out[int(row["transition_id"])] = (before, after)
        after = before
    return out


def _scope_rows(machine: Any, level: int) -> tuple[int, list[Mapping[str, Any]], bool]:
    """(life, the life's rows, whether the level is still current): the level's last life, which a death ends."""
    rows = sorted((row for row in machine.transition_index if row.get("level") == level),
                  key=lambda item: int(item["transition_id"]))
    current = int(machine.lives.level) == level
    life = int(machine.lives.life) if current else max((int(row.get("life") or 1) for row in rows), default=1)
    scoped = [row for row in rows if int(row.get("life") or 1) == life]
    if current and scoped and scoped[-1].get("boundary_state") in ENDING_STATES:
        life, scoped = life + 1, []  # the life ended at a death: the next one has no row yet
    return life, scoped, current


def observe(machine: Any, level: int, anatomies: Mapping[str, Mapping[str, Any]], evidence: Mapping[str, Any]
            ) -> dict[str, Any] | None:
    """The scope every lever's observations are derived from (plain JSON), or None without a record."""
    from inference.framework.g4_relations import lever_regions
    from inference.framework.level_record import _acted_lever

    boards = _boards(machine) if anatomies else None
    if boards is None:
        return None
    regions = lever_regions([dict(payload) for _entity, payload in sorted(anatomies.items())], [])
    ledger = getattr((getattr(machine, "_adapters", None) or {}).get("G3-LEVERS"), "entity_ledger", None)
    objects = {region.entity_id: set(ledger.cells_for(region.entity_id)) if ledger is not None else set()
               for region in regions}
    life, scoped, current = _scope_rows(machine, level)
    entry = scoped[0] if scoped and _is_reset(scoped[0]) else None
    if entry is not None:  # the reset that opens the life: the board after it is the life's entry board
        scoped, start = scoped[1:], boards[int(entry["transition_id"])][1]
    elif scoped:
        start = boards[int(scoped[0]["transition_id"])][0]
    else:  # a new life with no row yet: the board now is its first state (an ended level holds none)
        from inference.framework.card_builder import _current_grid

        start = _current_grid(machine) if current else None

    def contents(board: Sequence[Sequence[int]]) -> dict[str, str]:
        return {region.entity_id: strict_json.sha16([int(board[r][c]) for r, c in region.cells]) for region in regions}

    rows = []
    for index, row in enumerate(scoped):
        before, after = boards[int(row["transition_id"])]
        ending = row.get("boundary_state") in ENDING_STATES or (not current and index == len(scoped) - 1)
        reset = _is_reset(row)
        ref = row.get("evidence_id")  # a frozen level's last row is the level change: it ends the scope
        rows.append({"transition_id": int(row["transition_id"]),
                     "boundary": "END" if ending else "RESET" if reset else None,
                     "evidence_ref": str(ref) if ref in evidence else None,
                     "actor": _acted_lever(regions, objects, row.get("action") or {}), "contents": contents(after)})
    return {"level": int(level), "life": int(life), "initial": None if start is None else contents(start),
            "entry_reset": None if entry is None else int(entry["transition_id"]),
            "regions": {region.entity_id: len(region.cells) for region in regions}, "rows": rows}


def _is_reset(row: Mapping[str, Any]) -> bool:
    return row.get("kind") == "RESET" or row.get("boundary_state") == "RESET"


# ---- the pure derivation ---------------------------------------------------------------------------------------

def _category(entity_id: str, actor: Any, cycle: int) -> str:
    if actor == entity_id:
        return "toggle_reversal" if cycle == 2 else "self_recurrence"
    return "other_return" if actor is None else "cross_reversal"


def _status(tested: int, cases: Sequence[Any]) -> str:
    return "UNTESTED" if not tested else "OBSERVED" if cases else "NOT_OBSERVED"


def derive(scope: Mapping[str, Any] | None, entity_id: str) -> dict[str, Any]:
    """One lever's observations from a scope (``observe``); ``NOT_BUILT`` without a record or a region."""
    if scope is None or scope.get("initial") is None or entity_id not in scope.get("regions", {}):
        reason = "NO_RECORD" if scope is None or scope.get("initial") is None else "NO_REGION"
        return not_built(reason, scope)
    if entity_id in (scope.get("experiment_failures") or {}):  # B3: its experiment's execution evidence broke
        return failed("RECORD_MISMATCH", scope["experiment_failures"][entity_id], _scope_of(scope, None, None))
    inside = [row["transition_id"] for row in _life_rows(scope) if row["boundary"] == "RESET"]
    if inside:  # a reset after the life's entry: the life's states cannot be read as one sequence
        return failed(RESET_INSIDE_LIFE, inside, _scope_of(scope, None, None))
    current = scope["initial"][entity_id]
    seen, path = [current], [current]
    trials = {"unchanged": [], "changed": [], "own": 0, "cross": 0, "other": 0}
    cases: dict[str, list] = {name: [] for name in CATEGORIES}
    as_of, excluded = None, {"uncited": 0, "boundary": 0}
    for row in scope["rows"]:
        if row["boundary"] == "END":
            excluded["boundary"] += 1
            break  # a death or a level change ends the scope; nothing after it is this life's
        after, actor, ref = row["contents"][entity_id], row["actor"], row["evidence_ref"]
        changed = after != current
        if ref is None:
            excluded["uncited"] += 1
        else:
            if actor != entity_id:
                trials["cross" if actor is not None else "other"] += 1
                if changed:
                    trials["changed"].append({"transition_id": row["transition_id"], "evidence_ref": ref,
                                              "acting_lever": actor})
                else:
                    trials["unchanged"].append(row["transition_id"])
            elif changed:
                trials["own"] += 1
            if changed and after in path:
                cycle = len(path) - (len(path) - 1 - path[::-1].index(after))
                cases[_category(entity_id, actor, cycle)].append(
                    {"transition_id": row["transition_id"], "evidence_ref": ref, "acting_lever": actor,
                     "from_state": f"S{seen.index(current)}", "to_state": f"S{seen.index(after)}",
                     "cycle_length": cycle})
        if changed:
            path.append(after)
            if after not in seen:
                seen.append(after)
        current, as_of = after, row["transition_id"]
    return _observed(scope, entity_id, current, seen, as_of, excluded, trials, cases)


def _life_rows(scope: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """The scope's rows up to the one that ends the life (a death, a win or the level change)."""
    out = []
    for row in scope["rows"]:
        if row["boundary"] == "END":
            break
        out.append(row)
    return out


def not_built(reason: str, scope: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"status": "NOT_BUILT", "basis": reason, "scope": None if scope is None else _scope_of(scope, None, None),
            "region": None, "current_region_state": None, "persistence": None, "reversal": None, "failure": None,
            "digest": None}


def _scope_of(scope: Mapping[str, Any], as_of: Any, excluded: Any) -> dict[str, Any]:
    return {"level": scope["level"], "life": scope["life"], "entry_reset": scope.get("entry_reset"),
            "as_of_transition": as_of, "excluded": excluded}


def _observed(scope, entity_id, current, seen, as_of, excluded, trials, cases) -> dict[str, Any]:
    tested = len(trials["unchanged"]) + len(trials["changed"])
    persistence = {"status": "TESTED" if tested else "UNTESTED", "tested": tested,
                   "unchanged": len(trials["unchanged"]), "changed": len(trials["changed"]),
                   "unchanged_transitions": trials["unchanged"], "changed_cases": trials["changed"]}
    tested_by = {"toggle_reversal": trials["own"], "self_recurrence": trials["own"],
                 "cross_reversal": trials["cross"], "other_return": trials["other"]}
    reversal = {name: {"status": _status(tested_by[name], cases[name]), "tested": tested_by[name],
                       "cases": cases[name]} for name in CATEGORIES}
    state = {"label": f"S{seen.index(current)}", "state_sha16": current, "states_seen": len(seen), "orbit_phase": None,
             "phase_basis": "NO_ACCEPTED_ORBIT"}
    out = {"status": "OBSERVED", "basis": "LEVEL_RECORD", "scope": _scope_of(scope, as_of, excluded),
           "region": {"cell_count": scope["regions"][entity_id], "source": "G4.1_ANATOMY_CELLS"},
           "current_region_state": state, "persistence": persistence, "reversal": reversal, "failure": None,
           "digest": None}
    return out


def _cases(observations: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    out = list((observations.get("persistence") or {}).get("changed_cases") or ())
    for item in (observations.get("reversal") or {}).values():
        out += item["cases"]
    return out


def evidence_refs(observations: Mapping[str, Any]) -> list[str]:
    """The evidence ids the observations name outright (changed trials and every reversal reading)."""
    return sorted({case["evidence_ref"] for case in _cases(observations)})


def cited_transitions(observations: Mapping[str, Any]) -> set[int]:
    """Every transition the observations rest on: each trial and each reading."""
    unchanged = (observations.get("persistence") or {}).get("unchanged_transitions") or ()
    return {int(item) for item in unchanged} | {int(case["transition_id"]) for case in _cases(observations)}


# ---- orbit phase: only through an accepted orbit's exact mapping ---------------------------------------------

def phase_mapping(run_states: Sequence[str], period: Any, label: str) -> dict[str, Any] | None:
    """The orbit position of ``label`` when the run's own state labels repeat exactly with its period; else None."""
    if not isinstance(period, int) or period < 2 or len(run_states) < period + 1:
        return None
    cycle = list(run_states[:period])
    if len(set(cycle)) != period or any(run_states[i] != cycle[i % period] for i in range(len(run_states))):
        return None
    return {"position": cycle.index(label), "period": period, "run_states": list(run_states)} if label in cycle else None


def run_states(scope: Mapping[str, Any] | None, entity_id: str, run: Mapping[str, Any] | None) -> list[str] | None:
    """The region's state label before the run's first step and after each step, all inside the scope; else None."""
    if scope is None or not run or not run.get("steps") or scope.get("initial") is None:
        return None
    seen, current, after_of = [scope["initial"][entity_id]], scope["initial"][entity_id], {}
    for row in scope["rows"]:
        if row["boundary"] == "END":
            break
        before = current
        current = row["contents"][entity_id]
        if current not in seen:
            seen.append(current)
        after_of[row["transition_id"]] = (before, current)
    for step in run["steps"]:
        if step.get("transition_id") not in after_of:
            return None  # a step outside this life and level: never carried across (ruling 3)
    first = after_of[run["steps"][0]["transition_id"]][0]
    labels = [first] + [after_of[step["transition_id"]][1] for step in run["steps"]]
    return [f"S{seen.index(item)}" for item in labels]


def with_phase(observations: dict[str, Any], scope: Mapping[str, Any] | None, entity_id: str,
               orbit: Mapping[str, Any]) -> dict[str, Any]:
    """Name an orbit phase only when the orbit chapter is accepted (COMPLETE) and maps exactly."""
    state = observations.get("current_region_state")
    if state is None:
        return observations
    if orbit.get("status") != "COMPLETE" or not orbit.get("facts"):
        return observations
    run = (orbit["facts"] or {}).get("run") or {}
    states = run_states(scope, entity_id, run)
    if states is None:
        state.update(phase_basis="ORBIT_OUTSIDE_SCOPE")
        return observations
    mapping = phase_mapping(states, (orbit["facts"] or {}).get("period"), state["label"])
    state.update(orbit_phase=None if mapping is None else {"run_id": run.get("run_id"), **mapping},
                 phase_basis="EXACT_ORBIT_MAPPING" if mapping is not None else "NOT_EXACT")
    return observations


def seal(entity_id: str, observations: dict[str, Any]) -> dict[str, Any]:
    observations["digest"] = None if observations["status"] == "NOT_BUILT" else strict_json.digest_record(
        {"entity_id": entity_id, **{key: value for key, value in observations.items() if key != "digest"}})
    return observations


def failed(reason: str, refs: Sequence[Any], scope: Mapping[str, Any] | None) -> dict[str, Any]:
    """R8 for observations: a contradicted or mismatched record leaves nothing stated, only why (and the scope)."""
    return {"status": "FAILED_CLOSED", "basis": reason, "scope": scope, "region": None, "current_region_state": None,
            "persistence": None, "reversal": None, "failure": {"basis": reason, "refs": sorted({str(r) for r in refs})},
            "digest": None}


def fail(observations: dict[str, Any], reason: str, refs: Sequence[Any]) -> None:
    """Fail stored observations closed in place (a no-op when they hold nothing or already failed)."""
    if observations.get("status") == "OBSERVED":
        observations.clear()
        observations.update(failed(reason, refs, None))


# ---- what the limits chapter and the derived chapter read of them ---------------------------------------------

def persistence_reading(observations: Mapping[str, Any] | None) -> str | None:
    """OBSERVED when tested, UNTESTED when not; None when nothing was derived (the product's own value stands)."""
    if not observations or observations.get("status") != "OBSERVED":
        return None
    return "OBSERVED" if observations["persistence"]["status"] == "TESTED" else "UNTESTED"


def reversal_reading(observations: Mapping[str, Any] | None) -> str | None:
    """OBSERVED for a toggle or a cross-reversal (recurrence is not reversal); PROBE_OWED when tested and none was
    seen; UNTESTED with no own effective press and no other lever's press; None when nothing was derived."""
    if not observations or observations.get("status") != "OBSERVED":
        return None
    reversal = observations["reversal"]
    if "OBSERVED" in (reversal["toggle_reversal"]["status"], reversal["cross_reversal"]["status"]):
        return "OBSERVED"
    tested = reversal["toggle_reversal"]["tested"] or reversal["cross_reversal"]["tested"]
    return "PROBE_OWED" if tested else "UNTESTED"


def phase_named(observations: Mapping[str, Any] | None) -> bool:
    state = (observations or {}).get("current_region_state") or {}
    return state.get("orbit_phase") is not None


__all__ = ["CATEGORIES", "OBSERVATION_KEYS", "PHASE_BASES", "RESET_INSIDE_LIFE", "STATUSES", "TERMINAL_STATES",
           "cited_transitions",
           "derive", "evidence_refs",
           "fail", "failed", "not_built", "observe", "persistence_reading", "phase_mapping", "phase_named",
           "reversal_reading", "run_states", "seal", "with_phase"]
