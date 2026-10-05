"""G4-B certified by the controller from the level's record (R9-R24, D19; ruling G-1 and G-2).

Author: Claude (Alpha build seat), 2026-10-04. RULING_G4_CONTROLLER_FIRST_v2_2026-10-04 (Director-ruled).

The relations G4-B asked Duck to rediscover press by press were already on the record (v7 level 3:
certifiable at t140 with zero Duck turns; Duck's 24 predictions found one relation). Here the
controller renders them from the recorded presses (``level_record.presses``): one relation per lever,
every effect it was seen to have with the transitions that showed it, which levers act on one shared
region, which regions change each other, and the one-way reaches. Each clause cites its
transitions; nothing is generalised beyond them. Deterministic: the same record renders the same
bytes (M7).

Levers whose regions are the same cells are reported as controls of one shared region, never as a
coupling: a press that changes a shared region necessarily "changes" every lever on it (v7 level 3:
E0010 and E0011 share all 35 cells; E0012 and E0013 all 36).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from inference.framework.level_record import Press

RECORD_KIND = "LEVER_RELATIONS_FROM_RECORD"


def _set(names: Sequence[str]) -> str:
    return "{" + ",".join(names) + "}"


def shared_regions(regions: Sequence[Any]) -> dict[str, tuple[str, ...]]:
    """Each lever's region label: the sorted levers whose regions are exactly the same cells."""
    by_cells: dict[frozenset, list[str]] = {}
    for region in regions:
        by_cells.setdefault(frozenset(region.cells), []).append(region.entity_id)
    return {lever: tuple(sorted(group)) for group in by_cells.values() for lever in group}


def _label(levers: tuple[str, ...]) -> str:
    return levers[0] if len(levers) == 1 else "{" + "=".join(levers) + "}"


def _changed(press: Press, label: Mapping[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted({label[name] for name in press.changed_levers}))


def _effects(found: Sequence[Press], lever: str, label: Mapping[str, tuple[str, ...]]) -> list[tuple]:
    groups: dict[tuple, list[Press]] = {}
    for press in found:
        if press.lever == lever:
            groups.setdefault((_changed(press, label), press.elsewhere), []).append(press)
    return [(changed, elsewhere, items) for (changed, elsewhere), items in groups.items()]


def _relation(lever: str, found: Sequence[Press], label: Mapping[str, tuple[str, ...]]) -> dict[str, Any]:
    parts, refs, transitions, touched = [], [], [], {lever}
    for changed, elsewhere, items in _effects(found, lever, label):
        what = "nothing" if not changed and not elsewhere else (
            ("[" + ", ".join(_label(item) for item in changed) + "]" if changed else "") + ("+elsewhere" if elsewhere else "")
        )
        parts.append(f"{what} x{len(items)}")
        refs += [item.evidence_ref for item in items]
        transitions += [item.transition_id for item in items]
        touched.update(name for group in changed for name in group)
    return {
        "levers": [lever, *sorted(touched - {lever})],
        "claim": f"pressing {lever} changed " + "; ".join(parts),
        "evidence_refs": refs,
        "transitions": sorted(transitions),
        "kind": "RECORDED_EFFECTS",
    }


def _couplings(found: Sequence[Press], label: Mapping[str, tuple[str, ...]]) -> tuple[list[list[str]], dict[str, list[str]]]:
    """Groups of regions that each change the other (mutual), and one-way reaches, by region label."""
    edges = {(_label(label[press.lever]), _label(other)) for press in found for other in _changed(press, label)}
    edges = {(a, b) for a, b in edges if a != b}
    mutual = {pair for pair in edges if (pair[1], pair[0]) in edges}
    nodes = sorted({_label(group) for group in label.values()})
    parent = {node: node for node in nodes}

    def root(name: str) -> str:
        while parent[name] != name:
            name = parent[name]
        return name

    for a, b in mutual:
        parent[root(a)] = root(b)
    groups: dict[str, list[str]] = {}
    for node in nodes:
        groups.setdefault(root(node), []).append(node)
    coupled = sorted(sorted(group) for group in groups.values() if len(group) > 1)
    reaches: dict[str, list[str]] = {}
    for a, b in sorted(edges - mutual):
        if root(a) != root(b):
            reaches.setdefault(a, []).append(b)
    return coupled, reaches


def record_relations(regions: Sequence[Any], found: Sequence[Press], conditions: Sequence[dict]) -> dict[str, Any] | None:
    """The controller's G4-B answer, or None while a lever has no recorded press on this level."""
    levers = [region.entity_id for region in regions]
    pressed = {press.lever for press in found}
    if not levers or any(lever not in pressed for lever in levers):
        return None
    label = shared_regions(regions)
    relations = [_relation(lever, found, label) for lever in levers]
    coupled, reaches = _couplings(found, label)
    shared = sorted({group for group in label.values() if len(group) > 1})
    effective = {lever: sum(1 for p in found if p.lever == lever and not p.null) for lever in levers}
    spent = [lever for lever in levers if any(p.lever == lever and p.null for p in found)]
    sentences = [
        f"{len(levers)} levers, {len(found)} recorded presses on this level.",
        "Levers acting on one shared region: " + (", ".join(_label(group) for group in shared) or "none") + ".",
        "Regions that change each other: " + (", ".join(_set(group) for group in coupled) or "none") + ".",
        "One-way reach: " + ("; ".join(f"{a}->{','.join(b)}" for a, b in reaches.items()) or "none") + ".",
        "Presses that changed nothing outside the counter: " + (_set(spent) if spent else "none") + ".",
        "Effective presses per lever: " + ", ".join(f"{k} {v}" for k, v in effective.items()) + ".",
    ]
    if conditions:
        sentences.append(f"{len(conditions)} presses had different outcomes from the same masked board (missing conditions).")
    description = " ".join(sentences)
    seed = json.dumps({  # transitions, not evidence ids: the same record replayed is the same answer
        "relations": [{key: item[key] for key in ("levers", "claim", "transitions")} for item in relations],
        "description": description,
    }, sort_keys=True)
    return {
        "answer_kind": RECORD_KIND,
        "answer_id": "G4B-REC-" + hashlib.sha256(seed.encode()).hexdigest()[:16],
        "description": description,
        "relations": relations,
        "shared_regions": [list(group) for group in shared],
        "coupled_groups": coupled,
        "one_way_reach": reaches,
        "missing_conditions": [dict(item) for item in conditions],
        "evidence_basis": "RECORDED_TRANSITIONS",
        "epistemic_limit": (
            "Each relation is the recorded effects of one lever's presses on this level, from the boards "
            "they were taken on; it is not a law for boards not yet seen."
        ),
    }


def digest_lines(answer: dict[str, Any]) -> list[str]:
    shared = ", ".join(_label(tuple(group)) for group in answer.get("shared_regions") or ()) or "none"
    coupled = ", ".join(_set(group) for group in answer.get("coupled_groups") or ()) or "none"
    reach = "; ".join(f"{a}->{','.join(b)}" for a, b in (answer.get("one_way_reach") or {}).items()) or "none"
    return [f"relations (from the record): shared regions {shared} · mutual {coupled} · one-way {reach}"] + [
        item["claim"][:160] for item in answer.get("relations") or ()
    ]


__all__ = ["RECORD_KIND", "digest_lines", "record_relations"]
