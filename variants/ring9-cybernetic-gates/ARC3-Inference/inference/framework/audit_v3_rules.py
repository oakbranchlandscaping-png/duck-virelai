"""Audit journal v3: the recovery vocabulary and its sequence rules (WO-RUNTIME-01 §10, ruling C).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Interface v3 §6.1, as built (the build note:
the recovery links ride in ``submitted``, which every v2 row already has, rather than in new ``refs`` keys, so the v2
row shape and every v1/v2 writer and reader are untouched).

v3 is v2 unchanged plus two operations:

* ``TURN`` — ``OUTCOME`` (Duck: ``RECOVERABLE_NO_ACTION``, ``EXPLICIT_DECLINE``) and ``RECOVERY`` (the controller:
  ``CONTROLLER_ACTION``, ``DUCK_REWOKEN``, ``CLOSED_UNRESOLVED``, ``NO_CONTROLLER_ACTION``);
* ``GATE`` — ``CLOSE`` (``CLOSED_UNRESOLVED``), ``RECOVERY_CHECK`` (``NO_LEGAL_MOVE``, ``CONTROLLER_STALLED``) and,
  revision 2, ``LAST_RESORT`` (``NORMAL_PLAY_ENTERED``).

The rules, checked on every row the writer appends and every row a reader verifies:

1. a Duck ``OUTCOME`` is resolved by exactly one ``RECOVERY`` before the next ``OUTCOME`` or the seal;
2. a ``RECOVERY`` names the open outcome it resolves and, when it took an action or closed something, an earlier row
   of the controller of the right kind (an admitted controller probe, a ``GATE CLOSE``);
3. a ``CONTROLLER_ACTION`` in ``PLAY-NORMAL`` names a ``PLAY-NORMAL`` admission and the question ``FREE_PLAY``;
4. a budget close cites exactly its budget of same-class failures on its question, with no executed probe or admitted
   answer of that level and life between the first and the close (Director ruling Q1);
5. a decline close cites exactly one ``EXPLICIT_DECLINE`` on its question; a D22 or D-2 close cites its checks;
6. ``FREE_PLAY_FRONTIER_EXHAUSTED`` carries its proof: every legal action tried or barred (ruling Q4);
7. (revision 2) a ``GATE LAST_RESORT`` / ``NORMAL_PLAY_ENTERED`` row is G0's and cites its ``RECOVERY_CHECK`` rows.

WO-RUNTIME-01A tightens rules 2, 4 and 5 to what they always meant (``INTERFACE_WO_RUNTIME_01A_v1`` §4.3; no row shape,
operation or field changes, and nothing refused before is accepted now):

* rule 5 (scope): every row a ``GATE CLOSE`` cites is of the close's own level, life and gate;
* rule 5 (class): ``HARD_BUDGET_SPENT`` is the ``HARD`` class's close and ``CLOCK_BUDGET_SPENT`` the ``CLOCK``
  class's; every other cause has no class;
* rule 4 (once): a Duck ``OUTCOME`` is consumed by at most one close;
* rule 2 (match and name): a ``CLOSED_UNRESOLVED`` recovery's close is of its outcome's level, life, gate and question,
  and a close that consumed Duck outcomes (a budget or a decline close) is named by exactly one such recovery before
  the seal.

A ``GATE CLOSE`` of ``scope`` ``CHAPTER`` (revision 2) closes one G4.1 or G4.2 lever chapter; its ``refs.subject`` is
the lever.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

TURN_DISPOSITIONS = {
    "OUTCOME": frozenset({"RECOVERABLE_NO_ACTION", "EXPLICIT_DECLINE"}),
    "RECOVERY": frozenset({"CONTROLLER_ACTION", "DUCK_REWOKEN", "CLOSED_UNRESOLVED", "NO_CONTROLLER_ACTION"}),
}
GATE_DISPOSITIONS = {
    "CLOSE": frozenset({"CLOSED_UNRESOLVED"}),
    "RECOVERY_CHECK": frozenset({"NO_LEGAL_MOVE", "CONTROLLER_STALLED"}),
    "LAST_RESORT": frozenset({"NORMAL_PLAY_ENTERED"}),  # r2 ruling 2.5: G0 only, nothing downstream constructible
}
VALID = {"TURN": TURN_DISPOSITIONS, "GATE": GATE_DISPOSITIONS}
REASONED = frozenset({disposition for table in VALID.values() for group in table.values() for disposition in group})
HARD_REASONS = frozenset({"READ_ONLY_REPEAT", "NO_TOOL_CALL", "MALFORMED_ACTION", "ACTION_REFUSED", "STALE_CHOICE",
                          "SUBJECT_INADMISSIBLE", "PYTHON_ERROR", "CONTRACT_REPAIR_EXHAUSTED", "ROUTE_RETRY_EXHAUSTED",
                          "CONTEXT_OVERFLOW", "TOOL_STEP_LIMIT"})
CLOCK_REASONS = frozenset({"TURN_CLOCK", "MODEL_TIMEOUT", "MODEL_REQUEST_FAILED"})
REASON_CODES = HARD_REASONS | CLOCK_REASONS | frozenset({
    "NO_LEGAL_CONTROLLER_MOVE", "CONTROLLER_STALLED", "DECLINED", "HARD_BUDGET_SPENT", "CLOCK_BUDGET_SPENT",
    "UPSTREAM_UNRESOLVED", "DUCK_BUDGET_SPENT", "FREE_PLAY_FRONTIER_EXHAUSTED", "NO_CONSTRUCTIBLE_GATE",
    "PLANNED_STOP", "RUN_ENDED"})
BUDGETS = {"HARD": 2, "CLOCK": 4}
CLOSE_CLASS = {"HARD_BUDGET_SPENT": "HARD", "CLOCK_BUDGET_SPENT": "CLOCK"}  # 01A: every other close has no class
SCOPES = frozenset({"GATE", "ENTITY", "CHAPTER", "EXPERIMENT"})
PLAY, FREE_PLAY, G0 = "PLAY-NORMAL", "FREE_PLAY", "G0-ACTION-METADATA"


def _where(row: Mapping[str, Any]) -> tuple:
    return row["level"], row["life"], row["gate_id"], row["refs"]["question_id"]


def _class(code: str | None) -> str | None:
    return "HARD" if code in HARD_REASONS else "CLOCK" if code in CLOCK_REASONS else None


@dataclass
class V3State:
    """What a v3 prefix has established for the recovery rules (kept on the reader's and the writer's chain)."""

    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    open: dict[str, dict[str, Any]] = field(default_factory=dict)
    resets: list[tuple[int, Any, Any]] = field(default_factory=list)  # (seq, level, life) of progress rows
    consumed: dict[str, str] = field(default_factory=dict)  # 01A: outcome event_id -> the close that consumed it
    unnamed: dict[str, int] = field(default_factory=dict)  # 01A: consuming closes not yet named by a recovery

    def check(self, row: Mapping[str, Any], fail: Callable[[str], None]) -> None:
        operation, event = row["operation"], row["event"]
        if operation == "TURN" and event == "OUTCOME":
            if row["executor"] != "DUCK" or self.open:
                fail("an OUTCOME is Duck's, and the previous OUTCOME must be resolved first (rule 1)")
        elif operation == "TURN" and event == "RECOVERY":
            self._check_recovery(row, fail)
        elif operation == "GATE":
            if row["executor"] != "CONTROLLER":
                fail("a GATE row is the controller's")
            if event == "CLOSE":
                self._check_close(row, fail)
            elif event == "LAST_RESORT":
                self._check_last_resort(row, fail)

    def _check_recovery(self, row: Mapping[str, Any], fail: Callable[[str], None]) -> None:
        submitted = row["submitted"]
        if row["executor"] != "CONTROLLER" or not isinstance(submitted, Mapping):
            return fail("a RECOVERY is the controller's and names what it resolves")
        outcome = self.open.get(str(submitted.get("turn_event_id")))
        if outcome is None:
            return fail("a RECOVERY resolves an open OUTCOME (rule 2)")
        disposition, resulting = row["disposition"], self.rows.get(str(submitted.get("resulting_event_id")))
        if disposition == "CONTROLLER_ACTION":
            if resulting is None or (resulting["operation"], resulting["event"], resulting["disposition"],
                                     resulting["executor"]) != ("PROBE", "ADMISSION", "ADMITTED", "CONTROLLER"):
                return fail("a CONTROLLER_ACTION names the controller's admitted probe (rule 2)")
            if outcome["gate_id"] == PLAY and (resulting["gate_id"] != PLAY or row["refs"]["question_id"] != FREE_PLAY):
                return fail("a free-play recovery names a PLAY-NORMAL admission and FREE_PLAY (rule 3)")
        elif disposition == "CLOSED_UNRESOLVED":
            if resulting is None or (resulting["operation"], resulting["event"]) != ("GATE", "CLOSE"):
                return fail("a CLOSED_UNRESOLVED recovery names its GATE CLOSE (rule 2)")
            if _where(resulting) != _where(outcome):
                return fail("a CLOSED_UNRESOLVED recovery's close is of its outcome's level, life, gate and question "
                            "(rule 2)")
        elif (row["reason"] or {}).get("code") == "FREE_PLAY_FRONTIER_EXHAUSTED":
            proof = submitted.get("proof")
            if not (isinstance(proof, Mapping) and proof.get("legal") and proof.get("complete") is True
                    and all(item.get("tried") or item.get("barred") for item in proof["legal"])):
                return fail("FREE_PLAY_FRONTIER_EXHAUSTED carries a complete proof (rule 6)")
        return None

    def _check_close(self, row: Mapping[str, Any], fail: Callable[[str], None]) -> None:
        submitted = row["submitted"]
        if not isinstance(submitted, Mapping) or submitted.get("scope") not in SCOPES \
                or not isinstance(submitted.get("history"), list):
            return fail("a GATE CLOSE names its scope and its history")
        code, history = (row["reason"] or {}).get("code"), [self.rows.get(str(item)) for item in submitted["history"]]
        if any(item is None for item in history):
            return fail("a GATE CLOSE cites earlier rows only")
        kind = submitted.get("class")
        if self._scope_or_class_fails(row, history, code, kind, fail):
            return None
        if kind in BUDGETS:
            first = min((item["seq"] for item in history), default=row["seq"])
            if len(history) != BUDGETS[kind] or submitted.get("budget") != BUDGETS[kind] or any(
                    item["event"] != "OUTCOME" or _class((item["reason"] or {}).get("code")) != kind
                    or item["refs"]["question_id"] != row["refs"]["question_id"] for item in history) \
                    or any(seq > first and (level, life) == (row["level"], row["life"])
                           for seq, level, life in self.resets):
                return fail("a budget close cites exactly its budget of consecutive same-class failures (rule 4)")
        elif code == "DECLINED" and (len(history) != 1 or history[0]["disposition"] != "EXPLICIT_DECLINE"):
            return fail("a decline close cites its one EXPLICIT_DECLINE (rule 5)")
        elif code in {"NO_LEGAL_CONTROLLER_MOVE", "CONTROLLER_STALLED"} and (
                not history or any(item["event"] != "RECOVERY_CHECK" for item in history)):
            return fail("a D22 or D-2 close cites its recovery checks (rule 5)")
        return None

    def _scope_or_class_fails(self, row: Mapping[str, Any], history: list, code: Any, kind: Any,
                              fail: Callable[[str], None]) -> bool:
        """01A: a close cites rows of its own level, life and gate (rule 5); its cause is its class's (rule 5); an
        outcome is consumed once (rule 4)."""
        if any((item["level"], item["life"], item["gate_id"]) != (row["level"], row["life"], row["gate_id"])
               for item in history):
            fail("a GATE CLOSE cites rows of its own level, life and gate only (rule 5)")
        elif CLOSE_CLASS.get(code) != kind:
            fail(f"a {code} close is of class {CLOSE_CLASS.get(code)}, not {kind} (rule 5)")
        elif any(item["event"] == "OUTCOME" and item["event_id"] in self.consumed for item in history):
            fail("an OUTCOME is consumed by one close only (rule 4)")
        else:
            return False
        return True

    def _check_last_resort(self, row: Mapping[str, Any], fail: Callable[[str], None]) -> None:
        """Rule 7 (revision 2): normal play from a stuck G0 only, citing the recovery checks that found it stuck."""
        history = [self.rows.get(str(item)) for item in (row["submitted"] or {}).get("history") or ()]
        if row["gate_id"] != G0 or not history or any(item is None or item["event"] != "RECOVERY_CHECK"
                                                       for item in history):
            fail("a LAST_RESORT is G0's and cites its recovery checks (rule 7)")

    def accept(self, row: Mapping[str, Any]) -> None:
        keep = {key: row[key] for key in ("seq", "operation", "event", "disposition", "executor", "gate_id", "level",
                                          "life", "refs", "reason", "at_transition", "event_id")}
        self.rows[row["event_id"]] = keep
        self._account(row)
        if (row["operation"], row["event"]) == ("TURN", "OUTCOME"):
            self.open[row["event_id"]] = keep
        elif (row["operation"], row["event"]) == ("TURN", "RECOVERY"):
            self.open.pop(str((row["submitted"] or {}).get("turn_event_id")), None)
        elif (row["operation"], row["event"], row["disposition"]) in {("PROBE", "EXECUTION", "EXECUTED"),
                                                                       ("ANSWER", "ADMISSION", "ADMITTED")}:
            self.resets.append((row["seq"], row["level"], row["life"]))

    def _account(self, row: Mapping[str, Any]) -> None:
        """01A: which outcomes a close consumed, and which consuming closes still await the recovery naming them."""
        operation, event, submitted = row["operation"], row["event"], row["submitted"]
        if (operation, event) == ("GATE", "CLOSE"):
            outcomes = [item for item in submitted["history"] if self.rows[str(item)]["event"] == "OUTCOME"]
            self.consumed.update({str(item): row["event_id"] for item in outcomes})
            if outcomes:
                self.unnamed[row["event_id"]] = row["seq"]
        elif (operation, event, row["disposition"]) == ("TURN", "RECOVERY", "CLOSED_UNRESOLVED"):
            self.unnamed.pop(str(submitted.get("resulting_event_id")), None)

    def check_seal(self, fail: Callable[[str], None]) -> None:
        if self.open:
            fail(f"a sealed journal leaves no OUTCOME unresolved (rule 1): {sorted(self.open)}")
        elif self.unnamed:
            fail(f"a close that consumed Duck outcomes is named by its CLOSED_UNRESOLVED recovery (rule 2): "
                 f"{sorted(self.unnamed)}")


__all__ = ["BUDGETS", "CLOCK_REASONS", "CLOSE_CLASS", "HARD_REASONS", "REASONED", "REASON_CODES", "V3State", "VALID"]
