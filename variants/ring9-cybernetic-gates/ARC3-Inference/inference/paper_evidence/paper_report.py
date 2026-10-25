"""``paper_report.md``: the paper's per-world report, rendered from ``paper_evidence.json`` (WO-PE-03B/D).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.4.

The fixed six sections (``THESIS_v1``): self · time · response · players · model · value. Each line names who stated it
and what happened to it: the gate's certified state, the controller's proposal, or Duck's proposal (admitted or
refused). Gaps are counted, never hidden. A world whose provenance is not sealed and complete says so first. The
report is read by people and never parsed; the grader reads only the JSON.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

SECTIONS = (
    ("Self", lambda c: c["subject"]["type"] in ("AGENT", "ACTION") or (c["predicate"] == "ROLE_IS" and c["object"] == "EGO")),
    ("Time", lambda c: c["subject"]["type"] == "COUNTER" or c["predicate"].startswith("COUNTER_")),
    ("Response", lambda c: c["family"] in ("TRANSFORMATION",) or c["predicate"] in ("EFFECT_LOCALITY", "EFFECT_TRANSFORM",
                                                                                     "NO_OBSERVED_EFFECT")),
    ("Players", lambda c: c["family"] in ("ROLE", "RELATION") or c["predicate"] in ("LEVER_CLASS", "ORBIT_PERIOD",
                                                                                    "ORBIT_STOP")),
    ("Model", lambda c: c["family"] in ("LAW", "PREDICTION", "CONDITION") and c["predicate"] != "LEVEL_CLEARED_BY"),
    ("Value", lambda c: c["predicate"] in ("LEVEL_CLEARED_BY",)),
)
SHOWN = 12  # lines per section before the rest is summarized; the JSON holds every claim


def who(claim: Mapping[str, Any]) -> str:
    if claim["executor"] == "SYSTEM":
        return "certified" if claim["status"] in ("CERTIFIED",) else "observed"
    return f"{claim['executor'].lower()}, {claim['admission'].lower()}"


def _value(value: Any) -> str:
    text = value.get("handle") if isinstance(value, Mapping) and "handle" in value else value
    text = str(text).replace("\n", " ")
    return text if len(text) <= 110 else text[:107] + "..."


def line(claim: Mapping[str, Any], grade: str | None = None) -> str:
    mark = f" **{grade}**" if grade else ""
    return (f"- [{who(claim)}]{mark} {claim['subject']['handle']} · {claim['predicate']} · {_value(claim['object'])}"
            f" ({claim['status'].lower()})")


def _section(name: str, claims: Sequence[Mapping[str, Any]], grades: Mapping[str, str]) -> list[str]:
    out = [f"### {name}", ""]
    if not claims:
        return out + ["- nothing stated", ""]
    ordered = sorted(claims, key=lambda c: (c["executor"] != "SYSTEM", -int((c.get("measures") or {}).get("count") or 0)))
    out += [line(claim, grades.get(claim["assertion_id"])) for claim in ordered[:SHOWN]]
    if len(ordered) > SHOWN:
        out.append(f"- … {len(ordered) - SHOWN} more in paper_evidence.json")
    return out + [""]


def _gaps(audits: Sequence[Mapping[str, Any]]) -> list[str]:
    tally = Counter((a["predicate"], _audit_kind(a["object"])) for a in audits)
    return ["### What the model does not know", ""] + [f"- {p} {r}: {n}" for (p, r), n in sorted(tally.items())] + [""]


def _audit_kind(obj: Any) -> str:
    if isinstance(obj, Mapping):
        return " ".join(str(obj[key]) for key in ("reason", "chapter", "status", "gate_id", "outcome") if obj.get(key))
    return str(obj)


def render(packet: Mapping[str, Any], grades: Mapping[str, str] | None = None) -> str:
    stamp, claims, grades = packet["stamp"], packet["claims"], grades or {}
    out = [f"# Paper report — {stamp['game_id']}", "",
           f"Model `{stamp['content_sha256']}` ({stamp['model_schema']}). Provenance: {stamp['integrity']} / "
           f"{stamp['completeness']}{' — not sealed and complete; counted as measured output' if not stamp['provenance_sealed'] else ''}.",
           ""]
    for level in sorted({claim["level"] for claim in claims}):
        mine = [claim for claim in claims if claim["level"] == level]
        props = [claim for claim in mine if claim["kind"] == "PROPOSITION"]
        out += [f"## Level {level}", ""]
        for name, test in SECTIONS:
            out += _section(name, [claim for claim in props if test(claim)], grades)
        out += _gaps([claim for claim in mine if claim["kind"] == "AUDIT"])
    return "\n".join(out).rstrip() + "\n"


__all__ = ["render"]
