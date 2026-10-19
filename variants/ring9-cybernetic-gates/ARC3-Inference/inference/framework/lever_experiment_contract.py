"""The persisted contract of a G4-B limits experiment: identity, kinds, caps and terminal types (WO-G4-DOSSIER-B3 r2).

Author: Claude (Alpha build seat), 2026-10-18. Sol's review of B3 revision 1: the runtime (``lever_experiments``) and
the v9 validator (``lever_experiment_check``) share this small, pure module; the validator never imports the engine.

An experiment's identity is ``G4-B-LEVER-RELATIONS:EXP:{CODE}:{lever}:L{level}P{life}:R{n}`` (``n``: its ordinal
among the game's G4 admissions, B2's numbering); step ``k``'s probe id appends ``:{k}``. Its close names its type in
the reason, ``{TYPE}: detail``: a ``FINISHED`` close one of its kind's finished types, a ``STALE`` close a typed
interruption — never the other's.
"""
from __future__ import annotations

from typing import Any

RELATIONS = "G4-B-LEVER-RELATIONS"
PREFIX = f"{RELATIONS}:EXP:"
# open item -> (kind, probe-id code, maximum steps); dossier order (``lever_dossier_facts.PROBE_OWED``)
KINDS = {"LIMITS_PERSISTENCE": ("PERSISTENCE_TRIAL", "PERSISTENCE", 1),
         "LIMITS_REVERSAL": ("SELF_REVERSAL", "REVERSAL", 8)}  # 8: the existing extra-run bound, MAX_RERUN_PRESSES
CODES = {code: (item, kind, cap) for item, (kind, code, cap) in KINDS.items()}
FINISHED_BY_CODE = {"REVERSAL": ("REVERSAL_OBSERVED", "RECURRENCE_OBSERVED", "CAPPED"),
                    "PERSISTENCE": ("PERSISTENCE_UNCHANGED", "PERSISTENCE_CHANGED", "PERSISTENCE_INCONCLUSIVE")}
FINISHED_TYPES = FINISHED_BY_CODE["REVERSAL"] + FINISHED_BY_CODE["PERSISTENCE"]
STALE_TYPES = ("INTERRUPTED_DEATH", "INTERRUPTED_LEVEL_CHANGE", "STALE_SUBJECT", "CONTRADICTION", "GATE_CHANGED")


def question(level: int, entity_id: str) -> str:
    """The lever's limits question: the agenda's existing row, and the dossier question its chapter answers."""
    from inference.framework.library_agenda import question_id

    return question_id(int(level), "LIBRARY", str(entity_id), "LIMITS")


def experiment_id(code: str, entity_id: str, level: int, life: int, admission: int) -> str:
    return f"{PREFIX}{code}:{entity_id}:L{int(level)}P{int(life)}:R{int(admission)}"


def parse(probe_id: Any) -> dict[str, Any] | None:
    """An experiment step's identity from its probe id; None for any other probe."""
    text = str(probe_id or "")
    parts = text[len(PREFIX):].split(":") if text.startswith(PREFIX) else []
    if len(parts) != 5 or parts[0] not in CODES or not parts[2].startswith("L") or "P" not in parts[2]:
        return None
    level, life = parts[2][1:].split("P", 1)
    if not (level.isdigit() and life.isdigit() and parts[3][1:].isdigit() and parts[4].isdigit()):
        return None
    return {"code": parts[0], "entity_id": parts[1], "level": int(level), "life": int(life),
            "admission": int(parts[3][1:]), "k": int(parts[4]), "experiment_id": text.rsplit(":", 1)[0]}


def terminal_type(reason_text: Any) -> str | None:
    """The type a close names, the reason's leading ``TYPE:``; None when it names none."""
    text = str(reason_text or "")
    head = text.split(":", 1)[0] if ":" in text else ""
    return head if head in FINISHED_TYPES or head in STALE_TYPES else None


def admits(event: str, code: str | None, terminal: str | None) -> bool:
    """Whether a close of ``event`` (``FINISHED`` | ``STALE``) may carry ``terminal`` for an experiment of ``code``
    (None while its kind is unknown: no step was taken)."""
    if event == "STALE":
        return terminal in STALE_TYPES
    return terminal in (FINISHED_BY_CODE.get(code or "", ()) if code is not None else FINISHED_TYPES)


__all__ = ["CODES", "FINISHED_BY_CODE", "FINISHED_TYPES", "KINDS", "PREFIX", "RELATIONS", "STALE_TYPES", "admits",
           "experiment_id", "parse", "question", "terminal_type"]
