"""The answer-key contract and its validator (WO-PE-03C; Sol D9, D16, ruling C).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §3.

A key is the Director's statement of what is true in a world, authored from play, never from a run's output. The build
seat authors no key item (the only exception is a synthetic key marked ``method: SYNTHETIC_TEST``, which the formal
validator refuses). Subjects are addressed the way a person sees them: a readable handle plus the geometry of the
object in the level's **entry frame** (class, anchor, inclusive bbox, cell count). An object first seen later is
``frame: LATER`` with a description, and its mapping is a human confirmation. The key cites the entry-frame board hash
of every level it covers. The grader checks those hashes against the run, and a mismatched level is excluded with a
typed reason.

The validator checks structure, vocabulary, unique content-derived ``key_id``s, the attestation fields and, given a
repository and the evidence commit, that the key's freezing commit is an ancestor. It does not and cannot prove that
nobody opened a report before the freeze: ``blind_to_reports`` is the Director's attestation (Sol, ruling C).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.paper_evidence import claims as c

SCHEMA = "virelai-paper-key-v1"
METHODS = ("PLAY", "RECORDING_REVIEW", "SYNTHETIC_TEST")
HEX64, HEX40, DATE = re.compile(r"^[0-9a-f]{64}$"), re.compile(r"^[0-9a-f]{40}$"), re.compile(r"^\d{4}-\d{2}-\d{2}$")
TEXT = object()  # any non-empty string
INT = object()   # a positive integer
# The closed vocabulary: what the sealed v11 model can state (projection §2.2), so a key item can join exactly.
VOCABULARY: dict[str, dict[str, Any]] = {
    "ROLE": {"ROLE_IS": ("EGO", "COUNTER", "LEVER")},
    "LAW": {"CONTROL_MODE": ("POINTER", "EMBODIED"), "ACTION_EFFECT": TEXT, "COUNTER_REWRITE": TEXT,
            "COUNTER_TRIGGER": ("EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY"), "COUNTER_PERIOD": INT,
            "EFFECT_LOCALITY": ("LOCAL", "REMOTE"), "EFFECT_TRANSFORM": ("UNIFORM_VALUE_REWRITE",
                                                                       "COORDINATED_VALUE_REWRITE"),
            "LEVER_CLASS": ("ABSORBING", "CYCLE", "DIVERGENT"), "ORBIT_PERIOD": INT, "MECHANISM": TEXT},
    "RELATION": {"COUPLED_WITH": "SUBJECT", "SHARES_REGION_WITH": "SUBJECT", "RECORDED_EFFECT": TEXT},
    "CONDITION": {"NO_OBSERVED_EFFECT": TEXT, "LEVEL_CLEARED_BY": "ANY", "WIN_CONDITION": TEXT},
    "TRANSFORMATION": {"OBSERVED_CHANGE": "ANY"},
}
# A single-valued fact: a different value from the same subject is a contradiction, not another fact.
SINGLE_VALUED = frozenset({"ROLE_IS", "CONTROL_MODE", "COUNTER_REWRITE", "COUNTER_TRIGGER", "COUNTER_PERIOD",
                           "LEVER_CLASS", "ORBIT_PERIOD"})


class KeyError_(ValueError):
    """A key that fails validation; ``reasons`` lists every failure found."""

    def __init__(self, reasons: Sequence[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = list(reasons)


def item_id(item: Mapping[str, Any]) -> str:
    """The content-derived key id: full SHA-256 of the item without its id (D17)."""
    return c.sha256({key: value for key, value in item.items() if key != "key_id"})


def _geometry_problems(where: str, subject: Mapping[str, Any]) -> list[str]:
    geometry = subject.get("geometry")
    if subject.get("type") != "OBJECT":
        return []
    if geometry is None:
        return [] if subject.get("description") else [f"{where}: an OBJECT needs geometry or a description"]
    if geometry.get("frame") == "LATER":
        return [] if subject.get("description") else [f"{where}: a LATER object needs a description"]
    out = [] if geometry.get("frame") == "ENTRY" else [f"{where}: geometry frame must be ENTRY or LATER"]
    anchor, bbox, count = geometry.get("anchor"), geometry.get("bbox"), geometry.get("cell_count")
    if not (isinstance(anchor, list) and len(anchor) == 2 and isinstance(bbox, list) and len(bbox) == 4
            and isinstance(count, int) and count > 0 and all(isinstance(v, int) for v in [*anchor, *bbox])):
        return out + [f"{where}: ENTRY geometry needs integer anchor [r,c], bbox [r0,c0,r1,c1] and cell_count"]
    if not (bbox[0] <= bbox[2] and bbox[1] <= bbox[3] and anchor == bbox[:2]):
        out.append(f"{where}: bbox must be ordered and anchored at its top-left")
    return out


def _object_problems(where: str, family: str, predicate: str, value: Any) -> list[str]:
    allowed = (VOCABULARY.get(family) or {}).get(predicate, None)
    if allowed is None:
        return [f"{where}: {family} has no predicate {predicate!r}"]
    if allowed is TEXT and not (isinstance(value, str) and value.strip()):
        return [f"{where}: {predicate} needs text"]
    if allowed is INT and not (isinstance(value, int) and not isinstance(value, bool) and value > 0):
        return [f"{where}: {predicate} needs a positive integer"]
    if isinstance(allowed, tuple) and value not in allowed:
        return [f"{where}: {predicate} must be one of {list(allowed)}"]
    if allowed == "SUBJECT" and not (isinstance(value, Mapping) and value.get("type") in c.SUBJECT_TYPES):
        return [f"{where}: {predicate} needs a subject"]
    return []


def _item_problems(index: int, item: Mapping[str, Any], levels: set[int]) -> list[str]:
    where = f"items[{index}]"
    out: list[str] = []
    if item.get("level") not in levels:
        out.append(f"{where}: level {item.get('level')!r} is not in the key's levels")
    if not isinstance(item.get("required"), bool):
        out.append(f"{where}: required must be true or false")
    if item.get("kind", "PROPOSITION") != "PROPOSITION":
        out.append(f"{where}: key items are propositions")
    subject = item.get("subject") or {}
    if subject.get("type") not in c.SUBJECT_TYPES or not subject.get("handle"):
        out.append(f"{where}: subject needs a type and a handle")
    out += _geometry_problems(where, subject)
    out += _object_problems(where, str(item.get("family")), str(item.get("predicate")), item.get("object"))
    for alt in item.get("accepted_alternatives") or ():
        out += _object_problems(f"{where}.alternative", str(item.get("family")), str(alt.get("predicate")), alt.get("object"))
    if item.get("key_id") and item["key_id"] != item_id(item):
        out.append(f"{where}: key_id does not match its content")
    return out


def _construction_problems(key: Mapping[str, Any], formal: bool) -> list[str]:
    built = key.get("construction") or {}
    out = [f"construction.{name} is missing" for name in ("author", "method", "frozen_on", "blind_to_reports")
           if name not in built]
    if built.get("method") not in METHODS:
        out.append(f"construction.method must be one of {list(METHODS)}")
    if formal and built.get("method") == "SYNTHETIC_TEST":
        out.append("a SYNTHETIC_TEST key is for code tests only and is refused for formal grading")
    if formal and not HEX40.match(str(built.get("commit") or "")):
        out.append("construction.commit must be the 40-hex commit the key was frozen at")
    if not DATE.match(str(built.get("frozen_on") or "")):
        out.append("construction.frozen_on must be YYYY-MM-DD")
    if not isinstance(built.get("blind_to_reports"), bool):
        out.append("construction.blind_to_reports must be the Director's true/false attestation")
    frames = built.get("entry_frames") or {}
    for level in key.get("levels") or ():
        if not HEX64.match(str(frames.get(str(level)) or "")):
            out.append(f"construction.entry_frames[{level}] must be the 64-hex entry board hash")
    return out


def _single_value_problems(items: Sequence[Mapping[str, Any]]) -> list[str]:
    """Refuse contradictory truths for one single-valued subject fact.

    Genuine ambiguity belongs in one item's ``accepted_alternatives``.  Two
    key items that assert different values would otherwise let the automatic
    grader call either value both CORRECT and contradictory.
    """
    seen: dict[tuple[int, str, str, str], tuple[str, Any]] = {}
    out: list[str] = []
    for index, item in enumerate(items):
        predicate = item.get("predicate")
        if predicate not in SINGLE_VALUED:
            continue
        subject = item.get("subject")
        if not isinstance(subject, Mapping) or not isinstance(item.get("level"), int):
            continue
        key = (item["level"], c.sha256(c.identity_subject(subject)), str(item.get("family")), str(predicate))
        value = c.sha256(item.get("object"))
        previous = seen.get(key)
        if previous is not None and previous[0] != value:
            out.append(f"items[{index}]: conflicting single-valued {predicate} for the same subject; "
                       f"use accepted_alternatives for ambiguity")
        else:
            seen[key] = (value, item.get("object"))
    return out


def problems(key: Mapping[str, Any], *, formal: bool = True) -> list[str]:
    """Every reason the key fails; an empty list means it validates."""
    if key.get("schema") != SCHEMA:
        return [f"schema must be {SCHEMA}"]
    levels = {level for level in key.get("levels") or () if isinstance(level, int)}
    out = [] if key.get("game_id") and levels else ["game_id and levels are required"]
    out += _construction_problems(key, formal)
    ids = [item.get("key_id") or item_id(item) for item in key.get("items") or ()]
    out += [f"duplicate key item {value}" for value in sorted({v for v in ids if ids.count(v) > 1})]
    items = key.get("items") or ()
    for index, item in enumerate(items):
        out += _item_problems(index, item, levels)
    out += _single_value_problems(items)
    return out


def validate(key: Mapping[str, Any], *, formal: bool = True) -> dict[str, Any]:
    """The key with every ``key_id`` filled, or :class:`KeyError_` listing every failure."""
    found = problems(key, formal=formal)
    if found:
        raise KeyError_(found)
    return {**key, "items": [{**item, "key_id": item_id(item)} for item in key.get("items") or ()]}


def excluded_levels(key: Mapping[str, Any], stamp: Mapping[str, Any]) -> dict[str, str]:
    """Levels the run cannot be graded on: the key's entry frame differs from the run's, or the run never reached it."""
    frames, run = (key.get("construction") or {}).get("entry_frames") or {}, stamp.get("entry_frames") or {}
    out: dict[str, str] = {}
    for level in key.get("levels") or ():
        if str(level) not in run:
            out[str(level)] = "LEVEL_NOT_REACHED"
        elif run[str(level)] != frames.get(str(level)):
            out[str(level)] = "ENTRY_FRAME_MISMATCH"
    return out


def commit_is_ancestor(repo: str | Path, key_commit: str, evidence_commit: str) -> bool:
    """True when the key was frozen at or before the evidence commit (``git merge-base --is-ancestor``)."""
    done = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", key_commit, evidence_commit],
                          capture_output=True, check=False)
    return done.returncode == 0


__all__ = ["KeyError_", "METHODS", "SCHEMA", "SINGLE_VALUED", "VOCABULARY", "commit_is_ancestor", "excluded_levels",
           "item_id", "problems", "validate"]
