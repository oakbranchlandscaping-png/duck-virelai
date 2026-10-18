"""Duck's semantic world description: the DESC-A ledger, compacted into statements a reader can use.

Author: Claude (Alpha build seat), 2026-10-13. WO-DESC-B (INTERFACE_WO_DESC_B_v3_2026-10-13; Sol's rulings on v1,
his review of v2, and PRIOR_ART_WEAVE_COMPACTION_TRANSFORMATION_LIBRARY_v1).

A pure projection of one validated v3 model. It writes nothing, stores nothing and certifies nothing.

**Folding needs evidence.** An event folds into a primary statement only when it is provably the complementary
reading of the same change:

- ``OWNER_EXCHANGE`` (adapted from Ring 7 ``weave/provenance.py::complement_verdict``): the event's subject
  continues across the transition, it has no intrinsic (retained, rewritten) changed cell, and every changed cell
  it gave up or took was taken or given up by an already-primary, continuing event;
- ``G2_MASK_REWRITE``: both it and its primary partners are explained by the same certified G2 mask law, so the
  gate's receipt, not continuing identity, supplies the relation. Only this path folds a boundary event.

Coverage alone never folds, and nothing is hidden: the primary events' changed sites equal every changed site.

**Identity, not rank.** A pattern is the primary events sharing an appearance key (class, anchor and shape of a
track's first sighting), a verb and a rewrite set; its id is a hash of those, so it survives a growing record. An
appearance group is presentation only: identities are not joined, and roles, explanations and receipts stay on the
tracks and events they belong to. A role name appears only through a binding.

**Words.** The nine accepted verbs, per-action co-occurrence ("on ACTION1 transitions"), DESC-A's explanation
codes, and the observed effect type of ``effect_typing``. No causal word is rendered.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.descriptive_events import cell_runs, run_cells
from inference.framework.effect_typing import classify_effect_channel
from inference.framework.world_model_v2 import WorldModelV2Error

DOSSIER_CHAPTERS = ("identity", "anatomy", "orbit", "limits", "relations", "law_tests", "open_items")
# WO-G4-DOSSIER-A (R9): the digest's one findings line of chapter counts, and the selected lever's chapters when it is named
DOSSIER_CODES = {"COMPLETE": "C", "PRODUCT_PENDING": "P", "IN_PROGRESS": "O", "CLOSED_UNRESOLVED": "X",
                 "INTERRUPTED": "I", "NOT_BUILT": "U"}
DOSSIER_LEGEND = "C complete, P pending, O open, X closed, I interrupted, U unbuilt"

VIEW_SCHEMA = "virelai-world-view-v1"
FOLD_BASES = ("OWNER_EXCHANGE", "G2_MASK_REWRITE")
QUESTION_KIND = "UNEXPLAINED_TRANSFORMATION"
CAUSAL_WORDS = ("causes", "caused", "because", "makes", "controls", "drives", "triggers", "so that")
ROLE_NAMES = ("EGO", "COUNTER", "LEVER")
STRENGTH = {"EXPLAINED": 0, "PARTLY_EXPLAINED": 1, "UNEXPLAINED": 2}
KIND = {"MOVE": 0, "RECOLOR": 0, "BIRTH": 0, "DEATH": 0, "AMBIGUOUS": 0, "GROW": 1, "SHRINK": 1, "DEFORM": 2}
TYPING_MIN_PAIRS = 4  # the effect classifier needs a run of paired observations to say anything useful
G1_NOTE = "G1 product recorded; structured movement law unavailable"
G2_NOTE_NO_MASK = "G2 product recorded; no structured mask law stored"
OTHER_NOTE = "product recorded; no structured law stored in schema v3"
Cell = tuple[int, int]


def _fail(message: str) -> None:
    raise WorldModelV2Error(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:12]


# ---- ownership read from DESC-A footprints ----------------------------------------------------------------------

def _cells(event: Mapping[str, Any], group: str, changed_only: bool) -> dict[Cell, tuple[int, int]]:
    out: dict[Cell, tuple[int, int]] = {}
    groups = ((event.get("delta") or {}).get("footprint") or {}).get("membership_groups") or {}
    for item in groups.get(group) or ():
        if changed_only and item["before_class"] == item["after_class"]:
            continue
        for cell in run_cells(item["cell_runs"]):
            out[cell] = (int(item["before_class"]), int(item["after_class"]))
    return out


def _continuing(event: Mapping[str, Any]) -> bool:
    """Seen at both ``t-1`` and ``t``: a boundary event (birth, death, ambiguity, terminal deform, a resumed
    bridge) is never continuing."""
    return event["before"] is not None and event["after"] is not None and "gap_from" not in event["correspondence"]


def _mask_ref(event: Mapping[str, Any], receipts: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]] | None:
    if event["explanation"]["basis"] != "G2_MASK_LAW":
        return None
    for ref in event["explanation"]["refs"]:
        mask = ((receipts.get("products") or {}).get(ref) or {}).get("mask")
        if mask:
            return ref, mask
    return None


def _source_side(event: Mapping[str, Any], receipts: Mapping[str, Any]) -> bool:
    found = _mask_ref(event, receipts)
    return bool(found and event["before"] and event["before"]["class"] == found[1]["rewrite"]["from"])


def _changed(event: Mapping[str, Any]) -> tuple[dict, dict, dict]:
    return (_cells(event, "prior_footprint_only", True), _cells(event, "later_footprint_only", True),
            _cells(event, "retained_rewritten", True))


def _license(event, primary: set[str], by_id, gave, took, receipts) -> tuple[str, dict[str, set[Cell]]] | None:
    """The evidence that folds ``event`` into already-primary events, or None (it stays primary)."""
    lost, gained, kept = _changed(event)
    if not (lost or gained) or kept:
        return None
    pairs = [(cell, took.get(cell)) for cell in lost] + [(cell, gave.get(cell)) for cell in gained]
    if any(partner not in primary for _cell, partner in pairs):
        return None
    partners: dict[str, set[Cell]] = {}
    for cell, partner in pairs:
        partners.setdefault(partner, set()).add(cell)
    if _continuing(event) and all(_continuing(by_id[partner]) for partner in partners):
        return "OWNER_EXCHANGE", partners
    mine = _mask_ref(event, receipts)
    if mine and all((_mask_ref(by_id[partner], receipts) or ("",))[0] == mine[0] for partner in partners):
        return "G2_MASK_REWRITE", partners
    return None


def fold_transition(record: Mapping[str, Any], receipts: Mapping[str, Any],
                    born: Mapping[str, int]) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    """One verified transition's primary events, in display order, and its licensed folds."""
    events = [e for e in record["events"] if e["verb"] != "STILL"]
    by_id = {e["event_id"]: e for e in events}
    gave = {cell: e["event_id"] for e in events for cell in _cells(e, "prior_footprint_only", False)}
    took = {cell: e["event_id"] for e in events for cell in _cells(e, "later_footprint_only", False)}
    order = sorted(events, key=lambda e: (
        not e["subject"]["roles"], STRENGTH[e["explanation"]["status"]], not _source_side(e, receipts),
        KIND[e["verb"]], born[e["subject"]["track_id"]], e["subject"]["track_id"]))
    primary: list[Mapping[str, Any]] = []
    primary_ids: set[str] = set()
    folds: list[dict[str, Any]] = []
    for event in order:
        verdict = _license(event, primary_ids, by_id, gave, took, receipts)
        if verdict is None:
            primary.append(event)
            primary_ids.add(event["event_id"])
            continue
        basis, partners = verdict
        folds.append({"event_id": event["event_id"], "transition_id": record["transition_id"],
                      "track_id": event["subject"]["track_id"], "basis": basis, "mirror_of": sorted(partners),
                      "cells": cell_runs(set().union(*partners.values())),
                      "explanation": {"status": event["explanation"]["status"], "basis": event["explanation"]["basis"]}})
    return primary, folds


# ---- objects, patterns and questions ----------------------------------------------------------------------------

def _first(track: Mapping[str, Any]) -> Mapping[str, Any]:
    return track["segments"][0]


def appearance(track: Mapping[str, Any]) -> tuple[str, str, list[Any]]:
    """(handle, name, key) of a track's first sighting: what an unbound object is called, never a role."""
    first = _first(track)
    top, left, bottom, right = first["bbox"]
    handle = f"c{first['class_id']}@{first['anchor'][0]},{first['anchor'][1]}"
    name = (f"class-{first['class_id']} {bottom - top + 1}x{right - left + 1} object, {first['cell_count']} cells, "
            f"first seen at ({first['anchor'][0]},{first['anchor'][1]})")
    return handle, name, [first["class_id"], list(first["anchor"]), first["shape_hash"]]


def _role_name(role: Mapping[str, Any]) -> str:
    return f"LEVER {role['role_ref']}" if role["role"] == "LEVER" else str(role["role"])


def _delta_key(event: Mapping[str, Any]) -> str:
    """The scalar delta an action table counts; a verb with none (BIRTH, DEATH, a shapeless DEFORM) counts as itself."""
    delta = event["delta"]
    value = delta.get("translation") or delta.get("count") or delta.get("class")
    return event["verb"] if value is None else json.dumps(value)


def _rewrites(event: Mapping[str, Any]) -> list[list[int]]:
    lost, gained, kept = _changed(event)
    return [list(pair) for pair in sorted({*lost.values(), *gained.values(), *kept.values()})]


def _effect_types(rows_by_track: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out = []
    for track_id, rows in sorted(rows_by_track.items()):
        if len(rows) < TYPING_MIN_PAIRS:
            continue
        reading = classify_effect_channel(rows)
        item = {"track_id": track_id, "type": reading["mechanism"], "status": reading["status"],
                "witness_count": reading["witness_count"], "condition": reading.get("condition")}
        if reading.get("period") is not None:
            item["period"] = reading["period"]
        out.append(item)
    return out


def _sentence(pattern: Mapping[str, Any]) -> str:
    obj = pattern["object"]
    tracks = len(obj["tracks"])
    actions = "; ".join(
        f"on {action} transitions: " + ", ".join(f"{delta} x{n}" for delta, n in sorted(deltas.items(), key=lambda kv: (-kv[1], kv[0]))[:2])
        for action, deltas in sorted(pattern["by_action"].items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))[:3])
    explained = ", ".join(f"{basis} x{n}" for basis, n in sorted(pattern["explanations"].items(), key=lambda kv: (-kv[1], kv[0])))
    sites = ",".join(f"{a}>{b}" for a, b in pattern["sites"]) or "none"
    return (f"{obj['name']} [{obj['handle']}]: {pattern['verb']} x{pattern['count']} "
            f"({tracks} {'track' if tracks == 1 else 'tracks'}, lives {','.join(map(str, obj['lives']))}); "
            f"sites {sites}; {actions}; {explained}; t{pattern['transitions'][0]}-t{pattern['transitions'][-1]}")


def _add_event(group: dict[str, Any], record: Mapping[str, Any], event: Mapping[str, Any],
               evidence: Mapping[str, Any]) -> None:
    """Accumulate one primary event into its pattern group."""
    group["tracks"].add(event["subject"]["track_id"])
    group["lives"].add(int(event["life"]))
    group["roles"].append(tuple(sorted(json.dumps(role, sort_keys=True) for role in event["subject"]["roles"])))
    group["events"].append(event["event_id"])
    group["transitions"].append(int(record["transition_id"]))
    action = str((record.get("action") or {}).get("action") or "NONE")
    bucket = group["by_action"].setdefault(action, {})
    bucket[_delta_key(event)] = bucket.get(_delta_key(event), 0) + 1
    group["explanations"][event["explanation"]["basis"]] += 1
    group["refs"].update(ref for ref in event["explanation"]["refs"] if ref not in evidence)
    if event["before"] and event["after"]:
        group["typing_rows"].setdefault(event["subject"]["track_id"], []).append({
            "left_node": int(record["transition_id"]) - 1, "right_node": int(record["transition_id"]),
            "before": [event["before"]["class"], event["before"]["cell_count"], event["before"]["anchor"]],
            "after": [event["after"]["class"], event["after"]["cell_count"], event["after"]["anchor"]]})


def _group_primary(level: Mapping[str, Any], primary: Sequence[tuple[Mapping, Mapping]],
                   tracks: Mapping[str, Mapping]) -> dict[str, dict[str, Any]]:
    """Primary events grouped by content id: level, first appearance, verb and pixel rewrites."""
    groups: dict[str, dict[str, Any]] = {}
    evidence = level["receipts"].get("evidence") or {}
    for record, event in primary:
        handle, name, key = appearance(tracks[event["subject"]["track_id"]])
        rewrites = _rewrites(event)
        pattern_id = "P-" + _digest([level["level"], key, event["verb"], rewrites])
        group = groups.setdefault(pattern_id, {
            "pattern_id": pattern_id, "handle": handle, "name": name, "verb": event["verb"], "sites": rewrites,
            "tracks": set(), "lives": set(), "roles": [], "events": [], "transitions": [],
            "by_action": {}, "explanations": Counter(), "refs": set(), "typing_rows": {}})
        _add_event(group, record, event, evidence)
    return groups


def _mirrors_by_pattern(groups: Mapping[str, Mapping[str, Any]],
                        folds: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    owner = {event_id: pattern_id for pattern_id, group in groups.items() for event_id in group["events"]}
    mirrors: dict[str, list[Mapping[str, Any]]] = {}
    for fold in folds:
        for pattern_id in sorted({owner[partner] for partner in fold["mirror_of"]}):
            mirrors.setdefault(pattern_id, []).append(fold)
    return mirrors


def _finish_pattern(group: Mapping[str, Any], mine: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    roles = set(group["roles"])
    role = json.loads(next(iter(roles))[0]) if len(roles) == 1 and len(next(iter(roles))) == 1 else None
    obj = {"handle": group["handle"], "name": _role_name(role) if role else group["name"],
           "tracks": sorted(group["tracks"]), "lives": sorted(group["lives"]), "role": role}
    pattern = {
        "pattern_id": group["pattern_id"], "object": obj, "verb": group["verb"], "sites": group["sites"],
        "events": group["events"], "transitions": group["transitions"], "count": len(group["events"]),
        "by_action": {k: dict(sorted(v.items())) for k, v in sorted(group["by_action"].items())},
        "explanations": dict(sorted(group["explanations"].items())), "refs": sorted(group["refs"]),
        "mirrors": [fold["event_id"] for fold in mine],
        "mirror_explanations": dict(sorted(Counter(f["explanation"]["basis"] for f in mine).items())),
        "mirror_basis": dict(sorted(Counter(f["basis"] for f in mine).items())),
        "observed_effect_type": _effect_types(group["typing_rows"]),
    }
    pattern["sentence"] = _sentence(pattern)
    return pattern


def _patterns(level: Mapping[str, Any], primary: Sequence[tuple[Mapping, Mapping]],
              folds: Sequence[Mapping[str, Any]], tracks: Mapping[str, Mapping]) -> list[dict[str, Any]]:
    groups = _group_primary(level, primary, tracks)
    mirrors = _mirrors_by_pattern(groups, folds)
    out = [_finish_pattern(group, mirrors.get(pattern_id, [])) for pattern_id, group in groups.items()]
    out.sort(key=lambda p: (-p["count"], p["object"]["handle"], p["pattern_id"]))
    for rank, pattern in enumerate(out, start=1):
        pattern["rank"] = rank
    return out


def _gap_indices(gaps: Sequence[Mapping[str, Any]], subjects: Iterable[str]) -> list[int]:
    """Gaps cited only through an exact subject reference already in the model: never by resemblance."""
    wanted = set(subjects)
    return [index for index, gap in enumerate(gaps) if str(gap.get("subject")) in wanted]


def _questions(level: Mapping[str, Any], patterns: Sequence[Mapping[str, Any]], events: Mapping[str, Mapping]) -> list[dict[str, Any]]:
    out = []
    for pattern in patterns:
        unexplained = sum(1 for event_id in pattern["events"] if events[event_id]["explanation"]["status"] == "UNEXPLAINED")
        if not unexplained:
            continue
        out.append({
            "question_id": "Q-" + _digest([level["level"], pattern["pattern_id"], QUESTION_KIND]),
            "pattern_id": pattern["pattern_id"], "kind": QUESTION_KIND,
            "text": f"What changes the {pattern['object']['name']} [{pattern['object']['handle']}]? "
                    f"{pattern['verb']} x{unexplained} unexplained of {pattern['count']}.",
            "unexplained": unexplained, "last_transition": pattern["transitions"][-1],
            "gaps": _gap_indices(level.get("gaps") or (), pattern["object"]["tracks"] + pattern["events"]),
        })
    out.sort(key=lambda q: (-q["unexplained"], -q["last_transition"], q["question_id"]))
    for rank, question in enumerate(out, start=1):
        question["rank"] = rank
    return out


# ---- laws, dossiers, scene and census -----------------------------------------------------------------------------

def _laws(level: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Stored evidence only: a product receipt, and the structured law schema v3 stores for it, if any."""
    roles = {role.get("product_id"): role for role in level["certified"]["roles"] if role.get("product_id")}
    rows = []
    for product_id, receipt in sorted((level["receipts"].get("products") or {}).items()):
        gate = receipt["gate_id"]
        role = roles.get(product_id) or {}
        mask = receipt.get("mask")
        note = G1_NOTE if gate == "G1-EGO" else (None if mask else G2_NOTE_NO_MASK) if gate == "G2-COUNTER" else OTHER_NOTE
        rows.append({"gate_id": gate, "product_id": product_id, "product_type": receipt.get("product_type"),
                     "revision": receipt.get("revision"), "payload_sha256": receipt.get("payload_sha256"),
                     "mode": role.get("mode"), "evidence_refs": list(role.get("evidence_refs") or ()),
                     "structured_law": mask if gate == "G2-COUNTER" else None, "note": note})
    return rows


def _dossiers(level: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One stable row per certified lever: its stored v6 dossier's chapter statuses (a v3-v5 level keeps the
    ``NOT_BUILT`` stub, which WO-G4-DOSSIER-A replaces wherever a dossier is stored); the handle does not change."""
    stored = level.get("lever_dossiers")
    rows = []
    if stored is None:
        for role in level["certified"]["roles"]:
            if role["role"] == "LEVER":
                rows.append({"id": role["entity_id"], "status": "NOT_BUILT", "witnesses": list(role.get("witness_refs") or ()),
                             "handle": f"virelai('library', kind='dossiers', id={role['entity_id']!r})"})
        return sorted(rows, key=lambda row: row["id"])
    for entity_id, dossier in sorted(stored.items()):
        chapters = dossier["chapters"]
        identity = chapters["identity"].get("facts") or {}
        rows.append({"id": entity_id,
                     "status": "; ".join(f"{name} {chapters[name]['status']}" for name in DOSSIER_CHAPTERS),
                     "witnesses": [row["witness_id"] for row in identity.get("witnesses") or ()],
                     "track_id": dossier["track_join"].get("track_id"), "census": dossier["census_context"],
                     "handle": f"virelai('library', kind='dossiers', id={entity_id!r})"})
    return rows


def _n(value: Any) -> str:
    return "n/a" if value is None else str(value)


def _chapter_summary(name: str, chapter: Mapping[str, Any]) -> str:
    """A deterministic rendering of stored chapter facts (never new facts)."""
    facts = chapter.get("facts")
    if chapter["integrity"]["status"] == "FAILED_CLOSED":
        return f"failed closed ({', '.join(chapter['integrity']['reasons'])}; was {chapter['prior_status']})"
    if facts is None:
        return "no facts"
    if name == "identity":
        activation, actor = facts.get("activation") or {}, facts.get("actor") or {}
        return (f"witnesses {len(facts['witnesses'])}; inventory {_n(facts.get('inventory_status'))}; "
                f"activation {_n(activation.get('source'))}; chosen by {_n(actor.get('chooser'))}; "
                f"executed by {_n(actor.get('executor'))} ({_n(actor.get('status'))})")
    if name == "anatomy":
        residue, channels = facts["residue"], dossier_channels(facts)
        shown = "; ".join(channel["text"] for channel in channels[:2])
        more = f"; {len(channels) - 2} more channels" if len(channels) > 2 else ""
        return (f"channels {len(facts['channels'])}; residue {_n(residue['total'])} cells "
                f"({_n(residue['local'])} local, {_n(residue['remote'])} remote)" + (f"; {shown}" if shown else "") + more)
    if name == "orbit":
        run = facts.get("run") or {}
        return (f"run {_n(run.get('run_id'))} {_n(run.get('run_status'))}; stop {_n(run.get('stop_disposition'))}; "
                f"period {_n(facts.get('period'))}; class {_n(facts.get('lever_class'))}; other runs {len(chapter['history'])}")
    if name == "limits":
        endpoint = facts["endpoint"]
        return (f"endpoint {_n(endpoint['stop_disposition'])} ({_n(endpoint['confirmation'])}); "
                f"persistence {facts['persistence']}; reversal {facts['reversal']}")
    if name in ("relations", "law_tests"):
        tests = facts["tests"]
        tally = {status: sum(1 for t in tests if t["status"] == status) for status in ("SUPPORTED", "CONTRADICTED")}
        tail = (f"relations {len(facts['relations'])}; withdrawn {len(chapter['history'])}" + _submitted(facts)
                if name == "relations" else f"law {_n(facts.get('law_status'))}")
        return (f"tests {len(tests)} ({tally['SUPPORTED']} supported, {tally['CONTRADICTED']} contradicted); " + tail)
    return (f"incomplete {len(facts['incomplete_chapters'])}; contradictions {len(facts['contradictions'])}; "
            f"probes owed {len(facts['probe_owed'])}; next {facts['next_test']['kind']}")


def _submitted(facts: Mapping[str, Any]) -> str:
    """Revision 2 (blocker 2): who submitted the relation set and which gate certified it."""
    item = facts.get("submission")
    if not item:
        return ""
    return (f"; submitted by {_n(item['submission_source'])} ({item['status']}); certifier {item['certifier']} "
            f"({item['certification_origin']})")


def dossier_channels(facts: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Revision 2 (blockers 3, 4): each anatomy channel's affected subject and exact observed events, as text and the
    stored ids it cites (never an inferred mechanism)."""
    out = []
    for channel in (facts or {}).get("channels") or ():
        subject, events = channel.get("subject") or {}, channel.get("events") or ()
        who = (f"track {subject['track_id']}" if subject.get("status") == "EXACT_TRACK"
               else f"unresolved region ({_n(subject.get('reason'))})")
        seen = ", ".join(f"{ref['event_id']} {ref['verb']} t{ref['transition_id']}" for ref in events[:3])
        seen += f", {len(events) - 3} more" if len(events) > 3 else ""
        observed = f"observed events {seen}" if events else f"no observed event ({_n(channel.get('event_status'))})"
        refs = [ref["event_id"] for ref in events[:3]] + ([subject["track_id"]] if subject.get("status") == "EXACT_TRACK" else [])
        out.append({"text": f"{channel['channel_id']} ({channel['locality']}): {who}; {observed}", "refs": refs})
    return out


def dossier_chapters(level: Mapping[str, Any], entity_id: str) -> list[dict[str, Any]]:
    """The page rows of one stored dossier, chapter by chapter (the report renders the same rows)."""
    chapters = level["lever_dossiers"][entity_id]["chapters"]
    rows = []
    for name in DOSSIER_CHAPTERS:
        chapter = chapters[name]
        rows.append({"chapter": name, "status": chapter["status"], "basis": chapter["basis"],
                     "prior_status": chapter["prior_status"], "source": chapter["source"],
                     "product_id": (chapter["product_ref"] or {}).get("product_id"),
                     "answer_id": (chapter["answer_ref"] or {}).get("answer_id"),
                     "evidence_refs": list(chapter["evidence_refs"]), "summary": _chapter_summary(name, chapter),
                     "facts": chapter["facts"], "open": list(chapter["open"])})
    return rows


def dossier_digest_lines(level: Mapping[str, Any], subject: Any) -> list[str]:
    """R9: compact chapter counts, and the selected lever's chapters only when the selected question names it."""
    dossiers = level.get("lever_dossiers") or {}
    if not dossiers:
        return []
    counts = []
    for name in DOSSIER_CHAPTERS:
        tally: dict[str, int] = {}
        for dossier in dossiers.values():
            code = DOSSIER_CODES[dossier["chapters"][name]["status"]]
            tally[code] = tally.get(code, 0) + 1
        counts.append(f"{name.replace('_items', '').replace('_tests', '')} "
                      + " ".join(f"{code}{tally[code]}" for code in "CPOXIU" if code in tally))
    lines = [f"DOSSIERS x{len(dossiers)} ({DOSSIER_LEGEND}): " + "; ".join(counts)]
    if subject in dossiers:
        chapters = dossiers[subject]["chapters"]
        lines.append(f"SELECTED LEVER {subject}: " + "; ".join(
            f"{name} {DOSSIER_CODES[chapters[name]['status']]}"
            + ("" if chapters[name]["status"] in ("COMPLETE", "NOT_BUILT") else f" {chapters[name]['basis']}")
            for name in DOSSIER_CHAPTERS))
    return lines


def _scene(level: Mapping[str, Any], tracks: Mapping[str, Mapping]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    description = level["description"]
    scene = description["scene"]
    summary = {"as_of_transition": scene["as_of_transition"], "life": scene["life"],
               "objects_present": len(scene["present"]), "objects_departed": len(scene["departed"]),
               "unverified_objects": len(scene["unverified_tracks"]), "record_mismatch": scene["record_mismatch"],
               "integrity": description["integrity"]}
    objects = []
    for item in scene["present"]:
        handle, name, _key = appearance(tracks[item["track_id"]])
        roles = item["roles"] if isinstance(item["roles"], list) else []
        objects.append({"track_id": item["track_id"], "handle": handle,
                        "name": _role_name(roles[0]) if len(roles) == 1 else name,
                        "roles": roles, "class": item["class"], "anchor": item["anchor"], "cell_count": item["cell_count"]})
    objects.sort(key=lambda o: (not o["roles"], o["handle"], o["track_id"]))
    return summary, objects


def _open_identity(level: Mapping[str, Any]) -> list[dict[str, Any]]:
    gaps = level.get("gaps") or ()
    return [{**item, "gaps": [index for index, gap in enumerate(gaps) if gap.get("reason") == "IDENTITY_UNRESOLVED"
                              and str(gap.get("subject")) == item["subject"]]}
            for item in level["description"]["scene"]["open_identity"]]


def describe_level_view(level: Mapping[str, Any]) -> dict[str, Any]:
    """One level's semantic view, from its validated v3 payload alone."""
    tracks = {track["track_id"]: track for track in level["observation"]["tracks"]}
    born = {track_id: int(_first(track)["first"].get("transition_id", -1)) for track_id, track in tracks.items()}
    receipts = level["receipts"]
    primary: list[tuple[Mapping, Mapping]] = []
    folds: list[dict[str, Any]] = []
    census_verbs: Counter = Counter()
    census_expl: Counter = Counter()
    still_omitted = 0
    events: dict[str, Mapping] = {}
    for record in level["description"]["transitions"]:
        if record["record_status"] != "VERIFIED":
            continue
        still_omitted += int(record["still_omitted"])
        for event in record["events"]:
            census_verbs[event["verb"]] += 1
            census_expl[event["explanation"]["basis"]] += 1
            events[event["event_id"]] = event
        kept, folded = fold_transition(record, receipts, born)
        primary.extend((record, event) for event in kept)
        folds.extend(folded)
    patterns = _patterns(level, primary, folds, tracks)
    scene, objects = _scene(level, tracks)
    return {
        "level": level["level"], "scene": scene, "objects": objects, "patterns": patterns, "folds": folds,
        "questions": _questions(level, patterns, events), "open_identity": _open_identity(level),
        "census": {"verbs": dict(sorted(census_verbs.items())), "explanations": dict(sorted(census_expl.items())),
                   "primary": len(primary), "folded": len(folds), "still_omitted": still_omitted},
        "laws": _laws(level), "dossiers": _dossiers(level),
    }


def describe_world(model: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema": VIEW_SCHEMA, "content_sha256": model.get("content_sha256"),
            "levels": [describe_level_view(level) for level in model["levels"]]}


# ---- the validator --------------------------------------------------------------------------------------------------

def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def validate_level_view(view: Mapping[str, Any], level: Mapping[str, Any]) -> None:
    """Refuse a view that is not exactly what the level's DESC-A ledger, roles and receipts give."""
    events = {e["event_id"]: e for r in level["description"]["transitions"] if r["record_status"] == "VERIFIED"
              for e in r["events"]}
    tracks = {track["track_id"]: track for track in level["observation"]["tracks"]}
    for text in _strings({k: v for k, v in view.items() if k not in ("laws",)}):
        lowered = text.lower()
        _require(not any(word in lowered for word in CAUSAL_WORDS), f"the view says something causal: {text[:80]!r}")
    seen: set[str] = set()
    for pattern in view.get("patterns") or ():
        for event_id in pattern["events"]:
            _require(event_id in events, f"pattern {pattern['pattern_id']} cites {event_id!r}, no verified event")
            _require(event_id not in seen, f"event {event_id} is in two patterns")
            seen.add(event_id)
        _require(pattern["count"] == len(pattern["events"]) == len(pattern["transitions"]),
                 f"pattern {pattern['pattern_id']}: its count disagrees with its events")
        _require(sum(pattern["explanations"].values()) == pattern["count"],
                 f"pattern {pattern['pattern_id']}: its explanation counts disagree with DESC-A")
        obj = pattern["object"]
        if obj["role"] is None:
            names = {appearance(tracks[t])[1] for t in obj["tracks"]}
            _require(obj["name"] in names and not any(name in obj["name"].split() for name in ROLE_NAMES),
                     f"pattern {pattern['pattern_id']}: an unbound object is named only by its appearance")
    for fold in view.get("folds") or ():
        _require(fold["basis"] in FOLD_BASES, f"fold {fold['event_id']}: unknown basis {fold['basis']!r}")
        _require(fold["event_id"] in events and all(m in seen for m in fold["mirror_of"]),
                 f"fold {fold['event_id']} cites a partner that is not a primary event")
    gaps = level.get("gaps") or ()
    for question in view.get("questions") or ():
        for index in question["gaps"]:
            _require(isinstance(index, int) and 0 <= index < len(gaps), f"question {question['question_id']} cites a missing gap")
    expected = describe_level_view(level)
    for key in expected:
        _require(view.get(key) == expected[key], f"the view's {key} is not what the level's ledger and receipts give")
    _require(set(view) == set(expected), "the view carries keys the description does not define")


def validate_view(view: Mapping[str, Any], model: Mapping[str, Any]) -> None:
    _require(view.get("schema") == VIEW_SCHEMA and view.get("content_sha256") == model.get("content_sha256"),
             "the view names its model by content hash")
    _require(len(view.get("levels") or ()) == len(model["levels"]), "the view describes every level once")
    for level_view, level in zip(view["levels"], model["levels"]):
        validate_level_view(level_view, level)


__all__ = ["CAUSAL_WORDS", "DOSSIER_CHAPTERS", "FOLD_BASES", "VIEW_SCHEMA", "appearance", "describe_level_view",
           "describe_world", "dossier_channels", "dossier_chapters", "dossier_digest_lines", "fold_transition", "validate_level_view",
           "validate_view"]
