"""The descriptive event ledger: what every tracked object did at every recorded transition, never why.

Author: Claude (Alpha build seat), 2026-10-13. WO-DESC-A (INTERFACE_WO_DESC_A_v2_2026-10-13; Sol's review of v1,
"proceed with amendments").

A pure projection, compiled where the census is compiled (H1, H2, the live view), never on the action path.

**Identity is the census's.** The census threads each life's cuts with the accepted weave
(``weave_window`` then ``re_join``). An event's subject is the census track that owns the sighting; a
continuation or bridge verb is that line's own edge. ``weave_window`` keeps only continue verbs, so a
sighting's terminal verdict (DEATH, AMBIGUOUS or an unmatched DEFORM) is recovered by replaying the same
deterministic ``weave_edge`` on the same two cuts. No other matcher, no threshold, no join is introduced.

**Explanations are recomputed, never asserted.** ``explain`` derives an event's explanatory status from the
certified tier and the receipt index alone; the validator calls the same function and refuses any stored
explanation that differs. Every event's status is ``OBSERVED``: causal language belongs to G4 dossiers.

**The verified prefix.** From the first contradicted, duplicated or missing record on, records carry no
events and the scene is the last verified board: nothing is derived from a board rebuilt after a break.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.virelai_continuity import (
    ComponentObservation,
    NodeCut,
    _cell_runs,
    _cut_values,
    _rewrite_groups,
    _translation,
    weave_edge,
)
from inference.framework.world_model_v2 import WorldModelV2Error

DESCRIPTION_SCHEMA = "virelai-description-v1"
CONTINUITY_BASIS = "virelai-golden-weave-v1:weave_window+re_join"
VERBS = ("STILL", "RECOLOR", "MOVE", "GROW", "SHRINK", "BIRTH", "DEATH", "DEFORM", "AMBIGUOUS")
NINE = frozenset(VERBS)
TERMINAL_VERBS = frozenset({"DEATH", "AMBIGUOUS", "DEFORM"})
EXPLANATIONS = ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED")
MISMATCH_REASONS = ("DUPLICATE_TRANSITION", "MISSING_TRANSITION", "BEFORE_ENTRY", "CONTRADICTED_BEFORE_VALUE",
                    "JOURNAL_CHECK")  # at one id, the earlier-listed record fault ranks first
CHANGE_GROUPS = ("retained_rewritten", "prior_footprint_only", "later_footprint_only")
UNRESOLVED_OBJECT = "UNRESOLVED_OBJECT"
Cell = tuple[int, int]


def _fail(message: str) -> None:
    raise WorldModelV2Error(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def cell_runs(cells: Iterable[Cell]) -> list[list[int]]:
    """Lossless row runs ``[row, first_col, last_col]`` (the accepted ``_cell_runs``), JSON-shaped."""
    return [list(run) for run in _cell_runs(tuple(sorted(cells)))]


def run_cells(runs: Iterable[Sequence[int]]) -> set[Cell]:
    return {(int(row), col) for row, first, last in runs for col in range(int(first), int(last) + 1)}


def event_id(level: int, transition_id: int, track_id: str, verb: str) -> str:
    return "EV-" + hashlib.sha256(json.dumps([level, transition_id, track_id, verb]).encode()).hexdigest()[:16]


def witness_sha256(witness_id: str, receipt: Mapping[str, Any]) -> str:
    """The hash binding a witness receipt's ids, transition and residue together (its own hash field excluded)."""
    body = {key: value for key, value in receipt.items() if key != "witness_sha256"}
    return hashlib.sha256(json.dumps([witness_id, body], sort_keys=True, default=str).encode()).hexdigest()


# ---- the explanation rule (shared by the compiler and the validator) -------------------------------------------

def changed_sites(event: Mapping[str, Any]) -> tuple[set[Cell], set[tuple[int, int]]]:
    """The sites the subject gained, lost or rewrote whose integer changed, and the rewrites they performed."""
    groups = ((event.get("delta") or {}).get("footprint") or {}).get("membership_groups") or {}
    sites: set[Cell] = set()
    rewrites: set[tuple[int, int]] = set()
    for name in CHANGE_GROUPS:
        for group in groups.get(name) or ():
            if group["before_class"] != group["after_class"]:
                sites |= run_cells(group["cell_runs"])
                rewrites.add((int(group["before_class"]), int(group["after_class"])))
    return sites, rewrites


def _verdict(status: str, refs: Sequence[str], basis: str) -> dict[str, Any]:
    return {"status": status, "refs": sorted(refs), "basis": basis}


def _mask_explains(sites: set[Cell], rewrites: set[tuple[int, int]], mask: Mapping[str, Any]) -> bool:
    rewrite = mask.get("rewrite") or {}
    return bool(sites) and sites <= run_cells(mask.get("cell_runs") or ()) and rewrites == {
        (int(rewrite.get("from", -1)), int(rewrite.get("to", -1)))}


def _witness_cells(witness: Mapping[str, Any]) -> set[Cell] | None:
    residue = witness.get("residue")
    if not isinstance(residue, Mapping):
        return None
    return run_cells(residue.get("local_runs") or ()) | run_cells(residue.get("remote_runs") or ())


def explain(event: Mapping[str, Any], record: Mapping[str, Any], receipts: Mapping[str, Any],
            roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """An event's explanatory status, from the certified roles and the receipt index alone (first match wins).

    - EXPLAINED: a certified COUNTER's G2 mask law predicts every changed site: all lie in the mask and all
      perform exactly its source -> replacement rewrite. No inverse rewrite, refill, trigger or quantity. The
      transition must carry its own evidence receipt; the explanation cites the product and that receipt.
    - PARTLY_EXPLAINED: a G3 witness at this transition, cited by a certified LEVER, recorded residue that
      covers every changed site; or the event is a MOVE of the certified EGO's exact, still-bound track.
    - UNEXPLAINED: everything else, every STILL included.

    ``basis`` names the rule that matched: G2_MASK_LAW, G3_WITNESS_RESIDUE (an attributed activation; the
    mechanism is G4's), G1_EGO_MOVE (G1's displacement law is prose), NO_CHANGE (a STILL) or NOT_COVERED.
    """
    if event["verb"] == "STILL":
        return _verdict("UNEXPLAINED", [], "NO_CHANGE")
    transition = int(event["transition_id"])
    sites, rewrites = changed_sites(event)
    evidence = record.get("evidence_ref")
    witnessed = bool(evidence) and (receipts.get("evidence") or {}).get(evidence, {}).get("transition_id") == transition
    for role in sorted((r for r in roles if r.get("role") == "COUNTER"), key=lambda r: str(r.get("product_id"))):
        mask = ((receipts.get("products") or {}).get(role.get("product_id")) or {}).get("mask")
        if witnessed and isinstance(mask, Mapping) and _mask_explains(sites, rewrites, mask):
            return _verdict("EXPLAINED", [str(role["product_id"]), str(evidence)], "G2_MASK_LAW")
    cited = {str(ref) for role in roles if role.get("role") == "LEVER" for ref in role.get("witness_refs") or ()}
    witnesses = [ref for ref, witness in sorted((receipts.get("witnesses") or {}).items())
                 if ref in cited and witness.get("transition_id") == transition and sites
                 and sites <= (_witness_cells(witness) or set())]
    if witnesses:
        return _verdict("PARTLY_EXPLAINED", witnesses, "G3_WITNESS_RESIDUE")
    ego = [role for role in event["subject"]["roles"] if role["role"] == "EGO"]
    if ego and event["verb"] == "MOVE":
        return _verdict("PARTLY_EXPLAINED", [str(ego[0]["role_ref"])], "G1_EGO_MOVE")
    return _verdict("UNEXPLAINED", [], "NOT_COVERED")


# ---- compiling one level ----------------------------------------------------------------------------------------

def _fingerprint(snapshot: Mapping[str, Any] | None) -> tuple[Any, ...] | None:
    if snapshot is None:
        return None
    return snapshot["class"], snapshot["shape_hash"], tuple(snapshot["anchor"]), snapshot["cell_count"]


def _snapshot(region: ComponentObservation | None) -> dict[str, Any] | None:
    """The sighting as the census's segments state it; the exact changed sites live in the footprint groups."""
    if region is None:
        return None
    return {"class": region.class_id, "anchor": list(region.anchor), "bbox": list(region.bbox),
            "cell_count": region.cell_count, "shape_hash": region.shape_hash}


def _groups(cells: set[Cell], before: dict[Cell, int], after: dict[Cell, int]) -> list[dict[str, Any]]:
    return [{**group, "cell_runs": [list(run) for run in group["cell_runs"]]}
            for group in _rewrite_groups(cells, before, after)]


def footprint(prev: ComponentObservation | None, now: ComponentObservation | None,
              before: dict[Cell, int], after: dict[Cell, int]) -> dict[str, Any]:
    """``arithmetic_signature``'s membership groups, valued at the event's two cuts from values read once per
    transition (a held retained site is a count only). A regression test pins equality with the accepted helper."""
    prior, later = set(prev.cells) if prev is not None else set(), set(now.cells) if now is not None else set()
    shared = prior & later
    same = {cell for cell in shared if before[cell] == after[cell]}
    return {"membership_groups": {"retained_rewritten": _groups(shared - same, before, after),
                                  "prior_footprint_only": _groups(prior - later, before, after),
                                  "later_footprint_only": _groups(later - prior, before, after)},
            "retained_same_value_cells": len(same)}


def _delta(prev: ComponentObservation | None, now: ComponentObservation | None, footprint: Any) -> dict[str, Any]:
    delta: dict[str, Any] = {"footprint": footprint}
    if prev is None or now is None:
        return delta
    if prev.class_id != now.class_id:
        delta["class"] = [prev.class_id, now.class_id]
    if now.cell_count != prev.cell_count:
        delta["count"] = now.cell_count - prev.cell_count
    translation = _translation(prev, now)
    if translation is not None:
        delta["translation"] = list(translation)
    entered, departed = set(now.cells) - set(prev.cells), set(prev.cells) - set(now.cells)
    if entered:
        delta["entered_sites"] = {"count": len(entered)}
    if departed:
        delta["departed_sites"] = {"count": len(departed)}
    return delta


def _pixel_rewrite(left: NodeCut, right: NodeCut, values: tuple[dict[Cell, int], dict[Cell, int]]) -> dict[str, Any]:
    if left.geometry != right.geometry:
        return {"coverage_status": "UNDEFINED_ACROSS_GEOMETRY_CHANGE", "changed": [], "held_cells": None,
                "signed_class_delta": []}
    before, after = values
    changed = {cell for cell, value in before.items() if after[cell] != value}
    groups = _rewrite_groups(changed, before, after)
    signed: dict[int, int] = {}
    for group in groups:
        signed[group["before_class"]] = signed.get(group["before_class"], 0) - group["cell_count"]
        signed[group["after_class"]] = signed.get(group["after_class"], 0) + group["cell_count"]
    return {"coverage_status": "TOTAL", "changed": [{**g, "cell_runs": [list(r) for r in g["cell_runs"]]} for g in groups],
            "held_cells": len(before) - len(changed), "signed_class_delta": [[k, v] for k, v in sorted(signed.items()) if v]}


def verified_node(node: int, entry_node: int, limit: int | None) -> bool:
    """A board the description may read: the entry board always (it precedes every recorded transition, even one
    numbered before it), then each later board before the first mismatch."""
    return node == entry_node or (node > entry_node and (limit is None or node < limit))


def first_mismatch(rows: Sequence[Mapping[str, Any]], discontinuities: Sequence[Mapping[str, Any]],
                   entry_node: int) -> dict[str, Any] | None:
    """The earliest record the board cannot be trusted from. The level's ids run contiguously from the transition
    after its entry board, so the faults are: a duplicated id; a missing id, the first one included; an id at or
    before the entry board; a before-value the replayed board contradicts. At one id, a record fault ranks first."""
    rank = {reason: index for index, reason in enumerate(MISMATCH_REASONS)}
    found: list[tuple[int, int]] = []
    seen: set[int] = set()
    for tid in (int(row["transition_id"]) for row in rows):
        if tid in seen:
            found.append((tid, rank["DUPLICATE_TRANSITION"]))
        seen.add(tid)
    distinct = sorted(seen)
    if distinct and distinct[0] > entry_node + 1:
        found.append((entry_node + 1, rank["MISSING_TRANSITION"]))
    found.extend((tid, rank["BEFORE_ENTRY"]) for tid in distinct if tid <= entry_node)
    found.extend((low + 1, rank["MISSING_TRANSITION"]) for low, high in zip(distinct, distinct[1:]) if high != low + 1)
    found.extend((int(item["transition_id"]), rank["CONTRADICTED_BEFORE_VALUE"]) for item in discontinuities)
    if not found:
        return None
    tid, index = min(found)
    return {"transition_id": tid, "reason": MISMATCH_REASONS[index]}


def _bindings(certified: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """The certified roles bound to one exact track (the gate certified them; the description only reads)."""
    out = []
    for role in (certified or {}).get("roles") or ():
        identity = role.get("identity") or {}
        if identity.get("status") == "EXACT_ONE_TO_ONE" and identity.get("track_id"):
            out.append({"role": role["role"], "gate_id": role["gate_id"], "role_ref": role_ref(role),
                        "track_id": identity["track_id"], "ends_at_transition": None})
    return sorted(out, key=lambda b: (b["role"], str(b["role_ref"]), b["track_id"]))


def role_ref(role: Mapping[str, Any]) -> str:
    return str(role.get("entity_id") if role.get("role") == "LEVER" else role.get("product_id"))


def _bound(bindings: Sequence[Mapping[str, Any]], track_id: str, transition: int) -> list[dict[str, Any]]:
    """Roles bound to the track just before ``transition`` (a binding that ends there still held before it)."""
    return [{"role": b["role"], "gate_id": b["gate_id"], "role_ref": b["role_ref"]} for b in bindings
            if b["track_id"] == track_id and (b["ends_at_transition"] is None or b["ends_at_transition"] >= transition)]


class _Compiler:
    """One level's ledger: the window cuts and lines the census built, read pair by pair."""

    def __init__(self, level: int, projection: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
                 certified: Mapping[str, Any] | None, receipts: Mapping[str, Any] | None):
        self.level = level
        self.projection = projection
        self.rows = {int(row["transition_id"]): row for row in rows}
        self.roles = list((certified or {}).get("roles") or ())
        self.receipts = receipts or {"evidence": {}, "products": {}, "witnesses": {}}
        self.bindings = _bindings(certified)
        self.mismatch = first_mismatch(rows, projection["discontinuities"], projection["windows"][0]["cuts"][0].node_index)
        self.limit = self.mismatch["transition_id"] if self.mismatch else None
        self.entry_node = projection["windows"][0]["cuts"][0].node_index
        self.owner: dict[tuple[int, int], tuple[str, Any, int]] = {}
        for window in projection["windows"]:
            for track_id, line in window["lines"]:
                for index, step in enumerate(line.steps):
                    self.owner[(step.node_index, step.component_id)] = (track_id, line, index)
        self.last_before: dict[str, Any] = {}

    def verified(self, node: int) -> bool:
        return verified_node(node, self.entry_node, self.limit)

    def records(self) -> list[dict[str, Any]]:
        built: dict[int, dict[str, Any]] = {}
        windows = self.projection["windows"]
        for position, window in enumerate(windows):
            cuts = window["cuts"]
            if position > 0 and self.verified(cuts[0].node_index):
                built[cuts[0].node_index] = self._reset(windows[position - 1], window)
            for left, right in zip(cuts, cuts[1:]):
                if self.verified(right.node_index) and right.node_index not in built:
                    built[right.node_index] = self._pair(left, right)
        return [built.get(tid) or self._unverified(tid) for tid in sorted(self.rows)]

    def _base(self, tid: int) -> dict[str, Any]:
        row = self.rows[tid]
        action = row.get("action")
        return {"transition_id": tid, "level": self.level, "life": int(row.get("life") or 0),
                "kind": row.get("kind"), "action": dict(action) if action else None,
                "actor": row.get("gate_id") or row.get("kind"), "evidence_ref": row.get("evidence_id")}

    def _unverified(self, tid: int) -> dict[str, Any]:
        return {**self._base(tid), "pixel_rewrite": None, "still_total": 0, "still_emitted": 0, "still_omitted": 0,
                "events": [], "boundary": None, "record_status": "UNVERIFIED_AFTER_MISMATCH"}

    def _reset(self, before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
        left, right = before["cuts"][-1], after["cuts"][0]
        started = [t for t in self.projection["tracks"] if t["life"] == after["life"]
                   and t["segments"][0]["first"].get("transition_id") == right.node_index]
        boundary = {"kind": "RESET", "life_before": before["life"], "life_after": after["life"],
                    "tracks_ended": len(left.regions), "tracks_started": len(started),
                    "possible_correspondences": sum(1 for t in started if t.get("possible_correspondence"))}
        values = (_cut_values(left), _cut_values(right))
        return {**self._base(right.node_index), "pixel_rewrite": _pixel_rewrite(left, right, values),
                "still_total": 0, "still_emitted": 0, "still_omitted": 0, "events": [], "boundary": boundary,
                "record_status": "VERIFIED"}

    def _acted_track(self, left: NodeCut, tid: int) -> str | None:
        site = self.rows[tid].get("acted_site")
        if not isinstance(site, Mapping) or site.get("row") is None:
            return None
        cell = (int(site["row"]), int(site["col"]))
        region = next((r for r in left.regions if cell in set(r.cells)), None)
        return None if region is None else self.owner[(left.node_index, region.component_id)][0]

    def _pair(self, left: NodeCut, right: NodeCut) -> dict[str, Any]:
        """One woven transition: its pixel rewrite, one event per track it touched, and their explanations."""
        tid = right.node_index
        values = (_cut_values(left), _cut_values(right))
        record = {**self._base(tid), "pixel_rewrite": _pixel_rewrite(left, right, values)}
        events, still_total = self._arrivals(record, left, right, values)
        events += self._departures(record, left, right, values)
        events.sort(key=lambda e: (e["subject"]["track_id"], e["verb"]))
        emitted = sum(1 for e in events if e["verb"] == "STILL")
        for event in events:  # a class change ends its bindings here, after the event itself carried them
            if event["verb"] == "RECOLOR":
                for binding in self.bindings:
                    if binding["track_id"] == event["subject"]["track_id"] and binding["ends_at_transition"] is None:
                        binding["ends_at_transition"] = tid
                        event["flags"]["role_binding_ends"] = True
            event["explanation"] = explain(event, record, self.receipts, self.roles)
        return {**record, "still_total": still_total, "still_emitted": emitted, "still_omitted": still_total - emitted,
                "events": events, "boundary": None, "record_status": "VERIFIED"}

    def _arrivals(self, record: Mapping[str, Any], left: NodeCut, right: NodeCut,
                  values: tuple[dict[Cell, int], dict[Cell, int]]) -> tuple[list[dict[str, Any]], int]:
        """Each track seen at ``t``: its first sighting (BIRTH) or its line's own edge (a continuation or bridge).
        A STILL is counted; it is emitted only for a bound track or the track under the acted site."""
        tid, acted = right.node_index, self._acted_track(left, right.node_index)
        events, still_total = [], 0
        for region in right.regions:
            track_id, line, index = self.owner[(tid, region.component_id)]
            if index == 0:
                events.append(self._event(record, track_id, "BIRTH", None, region, left, right, values,
                                          {"source": "NONE", "witness": "golden_cascade", "ambiguity": None}))
                continue
            edge, prev = line.edges[index - 1], line.steps[index - 1]
            correspondence = {"source": edge.anchor, "witness": edge.witness, "ambiguity": None}
            if prev.node_index != left.node_index:
                correspondence["gap_from"] = prev.node_index
            if edge.verb == "STILL":
                still_total += 1
                if track_id != acted and not _bound(self.bindings, track_id, tid):
                    continue
            events.append(self._event(record, track_id, edge.verb, prev, region, left, right, values, correspondence))
        return events, still_total

    def _departures(self, record: Mapping[str, Any], left: NodeCut, right: NodeCut,
                    values: tuple[dict[Cell, int], dict[Cell, int]]) -> list[dict[str, Any]]:
        """Each track seen at ``t-1`` and not at ``t``: the replayed ``weave_edge`` cascade's verdict on it."""
        cascade = {(edge.prev.node_index, edge.prev.component_id): edge
                   for edge in weave_edge(left.regions, right.regions) if edge.prev is not None}
        events = []
        for region in left.regions:
            track_id, line, index = self.owner[(left.node_index, region.component_id)]
            following = line.steps[index + 1] if index + 1 < len(line.steps) else None
            if following is not None and following.node_index == right.node_index:
                continue
            edge = cascade[(left.node_index, region.component_id)]
            correspondence = {"source": "NONE", "witness": "golden_cascade_unmatched" if edge.verb == "DEFORM"
                              else edge.witness, "ambiguity": "MULTIPLE_LICENSED_SUCCESSORS"
                              if edge.verb == "AMBIGUOUS" else None}
            if following is not None and self.verified(following.node_index):
                correspondence["resumes_at"] = following.node_index
            events.append(self._event(record, track_id, edge.verb, region, None, left, right, values, correspondence))
        return events

    def _event(self, record: Mapping[str, Any], track_id: str, verb: str, prev: ComponentObservation | None,
               now: ComponentObservation | None, left: NodeCut, right: NodeCut,
               values: tuple[dict[Cell, int], dict[Cell, int]], correspondence: dict[str, Any]) -> dict[str, Any]:
        tid = record["transition_id"]
        if verb not in TERMINAL_VERBS | {"BIRTH"} and (prev is None or now is None):
            raise RuntimeError(f"the accepted weave joined no sighting pair for a {verb} edge")  # never: an invariant
        before, after = _snapshot(prev), _snapshot(now)
        returns = False
        if verb != "STILL":  # A -> B -> A: the subject is back to the state its previous change started from
            returns = after is not None and _fingerprint(after) == _fingerprint(self.last_before.get(track_id))
            self.last_before[track_id] = before
        return {
            "event_id": event_id(self.level, tid, track_id, verb), "transition_id": tid, "level": self.level,
            "life": record["life"], "subject": {"track_id": track_id, "roles": _bound(self.bindings, track_id, tid)},
            "verb": verb, "before": before, "after": after,
            "delta": _delta(prev, now, footprint(prev, now, *values) if left.geometry == right.geometry else None),
            "correspondence": correspondence,
            "flags": {"recolor": verb == "RECOLOR", "returns_to_prior_state": bool(returns),
                      "reopens_role_typing": verb == "RECOLOR", "role_binding_ends": False},
            "status": "OBSERVED",
        }


def _presence(projection: Mapping[str, Any], limit: int | None) -> dict[str, list[list[int]]]:
    """Each track's verified sighting spans: consecutive nodes merged, a gap (occlusion, return) kept."""
    out: dict[str, list[list[int]]] = {}
    entry_node = projection["windows"][0]["cuts"][0].node_index
    for window in projection["windows"]:
        for track_id, line in window["lines"]:
            spans: list[list[int]] = []
            for step in line.steps:
                node = step.node_index
                if not verified_node(node, entry_node, limit):
                    break
                if spans and spans[-1][1] == node - 1:
                    spans[-1][1] = node
                else:
                    spans.append([node, node])
            if spans:
                out[track_id] = spans
    return dict(sorted(out.items()))


def describe_level(level: int, entry_board: Any, entry: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], *,
                   entry_life: int = 1, certified: Mapping[str, Any] | None = None,
                   receipts: Mapping[str, Any] | None = None, projection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One level's description chapter (schema ``virelai-description-v1``), from the census projection."""
    if projection is None:
        from inference.framework.library_census import project_tracks

        projection = project_tracks(level, entry_board, entry, rows, entry_life=entry_life)
    rows = sorted(rows, key=lambda row: int(row["transition_id"]))
    compiler = _Compiler(level, projection, rows, certified, receipts)
    records = compiler.records()
    windows = projection["windows"]
    description = {
        "schema": DESCRIPTION_SCHEMA,
        "basis": {"continuity": CONTINUITY_BASIS, "entry_node": windows[0]["cuts"][0].node_index,
                  "windows": [{"life": w["life"], "from_node": w["cuts"][0].node_index,
                               "to_node": w["cuts"][-1].node_index} for w in windows]},
        "integrity": "RECORD_MISMATCH" if compiler.mismatch else "VERIFIED",
        "first_mismatch": compiler.mismatch,
        "transitions": records,
        "presence": _presence(projection, compiler.limit),
        "role_bindings": compiler.bindings,
    }
    description["scene"] = scene_at(description, projection["tracks"], compiler.roles)
    return description


# ---- the scene, and H2's restriction --------------------------------------------------------------------------------

def _segment_at(track: Mapping[str, Any], node: int, entry_node: int) -> Mapping[str, Any]:
    def at(source: Mapping[str, Any]) -> int:
        return int(source["transition_id"]) if source.get("source") == "TRANSITION" else entry_node

    return next(s for s in track["segments"] if at(s["first"]) <= node <= at(s["last"]))


def _as_of(description: Mapping[str, Any]) -> tuple[int | None, int]:
    verified = [r["transition_id"] for r in description["transitions"] if r["record_status"] == "VERIFIED"]
    as_of = max(verified) if verified else None
    return as_of, (as_of if as_of is not None else int(description["basis"]["entry_node"]))


def open_identities(roles: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(({"role": r["role"], "gate_id": r["gate_id"], "subject": str(r.get("entity_id") or r["role"])}
                   for r in roles if (r.get("identity") or {}).get("status") == "UNRESOLVED"),
                  key=lambda item: (item["role"], item["subject"]))


def scene_at(description: Mapping[str, Any], tracks: Sequence[Mapping[str, Any]],
             roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The board as of the last verified transition (the entry board when none is verified)."""
    as_of, node = _as_of(description)
    entry_node = int(description["basis"]["entry_node"])
    life = next((w["life"] for w in description["basis"]["windows"] if w["from_node"] <= node <= w["to_node"]),
                description["basis"]["windows"][0]["life"])
    presence = description["presence"]
    present, departed, unverified = [], [], []
    for track in sorted(tracks, key=lambda t: t["track_id"]):
        track_id = track["track_id"]
        spans = presence.get(track_id)
        if not spans:
            unverified.append(track_id)
        elif any(a <= node <= b for a, b in spans):
            segment = _segment_at(track, node, entry_node)
            bound = [{"role": b["role"], "gate_id": b["gate_id"], "role_ref": b["role_ref"]}
                     for b in description["role_bindings"] if b["track_id"] == track_id
                     and (b["ends_at_transition"] is None or b["ends_at_transition"] > node)]
            present.append({"track_id": track_id, "class": segment["class_id"], "anchor": list(segment["anchor"]),
                            "bbox": list(segment["bbox"]), "cell_count": segment["cell_count"],
                            "roles": bound or UNRESOLVED_OBJECT})
        else:
            departed.append({"track_id": track_id, "last_seen_node": max(b for _a, b in spans),
                             "end_reason": "LIFE_ENDED" if track["life"] != life else "DEPARTED"})
    verified = [r for r in description["transitions"] if r["record_status"] == "VERIFIED"]
    counts: dict[str, int] = {}
    for record in verified:
        for event in record["events"]:
            counts[event["verb"]] = counts.get(event["verb"], 0) + 1
    return {
        "as_of_transition": as_of, "as_of_node": node, "life": life,
        "record_mismatch": description["first_mismatch"],
        "present": present, "departed": departed, "unverified_tracks": unverified,
        "verb_counts": dict(sorted(counts.items())),
        "unexplained": [e["event_id"] for r in verified for e in r["events"]
                        if e["verb"] != "STILL" and e["explanation"]["status"] == "UNEXPLAINED"],
        "open_identity": open_identities(roles),
    }


def restrict_description(description: Mapping[str, Any], tracks: Sequence[Mapping[str, Any]],
                         roles: Sequence[Mapping[str, Any]], receipts: Mapping[str, Any],
                         truncate_at: int | None = None) -> dict[str, Any]:
    """H2's verdicts applied: a journal mismatch truncates the verified prefix at ``truncate_at``, a withdrawn
    role is withdrawn from every event, and explanations and the scene are recomputed. Returns a copy."""
    out = copy.deepcopy(dict(description))
    current = out["first_mismatch"]["transition_id"] if out["first_mismatch"] else None
    if truncate_at is not None and (current is None or truncate_at < current):
        out["first_mismatch"], out["integrity"] = {"transition_id": truncate_at, "reason": "JOURNAL_CHECK"}, "RECORD_MISMATCH"
        current = truncate_at
    if current is not None:
        upper = max(current - 1, int(out["basis"]["entry_node"]))  # the entry board stays trusted
        out["presence"] = {t: clipped for t, spans in out["presence"].items()
                           if (clipped := [[a, min(b, upper)] for a, b in spans if a <= upper])}
    kept = {(b["role"], b["gate_id"], b["role_ref"], b["track_id"]) for b in _bindings({"roles": roles})}
    bindings = []
    for binding in out["role_bindings"]:
        if (binding["role"], binding["gate_id"], binding["role_ref"], binding["track_id"]) in kept:
            ends = binding["ends_at_transition"]
            bindings.append({**binding, "ends_at_transition": None if current is not None and ends is not None
                             and ends >= current else ends})
    out["role_bindings"] = bindings
    for index, record in enumerate(out["transitions"]):
        tid = record["transition_id"]
        if current is not None and tid >= current:
            row = {k: record[k] for k in ("transition_id", "level", "life", "kind", "action", "actor", "evidence_ref")}
            out["transitions"][index] = {**row, "pixel_rewrite": None, "still_total": 0, "still_emitted": 0,
                                         "still_omitted": 0, "events": [], "boundary": None,
                                         "record_status": "UNVERIFIED_AFTER_MISMATCH"}
            continue
        for event in record["events"]:
            track_id = event["subject"]["track_id"]
            event["subject"]["roles"] = _bound(bindings, track_id, tid)
            event["flags"]["role_binding_ends"] = any(b["track_id"] == track_id and b["ends_at_transition"] == tid
                                                      for b in bindings)
            if current is not None and event["correspondence"].get("resumes_at", -1) >= current:
                del event["correspondence"]["resumes_at"]
            event["explanation"] = explain(event, record, receipts, roles)
    out["scene"] = scene_at(out, tracks, roles)
    return out


# ---- the validator ------------------------------------------------------------------------------------------------

def _expected_bindings(roles: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = _bindings({"roles": roles})
    ends = {(r["role"], role_ref(r), (r.get("identity") or {}).get("track_id")): r.get("binding_ends_at") for r in roles}
    for binding in out:
        binding["ends_at_transition"] = ends[(binding["role"], binding["role_ref"], binding["track_id"])]
    return out


def _validate_event(event: Mapping[str, Any], record: Mapping[str, Any], pixels: Mapping[Cell, tuple[int, int]],
                    context: Mapping[str, Any]) -> None:
    tid = record["transition_id"]
    _require("causal" not in event and event.get("status") == "OBSERVED",
             f"event {event.get('event_id')} claims {event.get('status')!r}: the ledger is observational; a causal "
             "claim needs a G4 gate receipt and lives in a dossier (WO-G4-DOSSIER-A)")
    _require(event.get("transition_id") == tid, f"event {event.get('event_id')} sits under transition {tid}")
    _require(event.get("verb") in NINE, f"unknown observation verb {event.get('verb')!r}")
    track_id = (event.get("subject") or {}).get("track_id")
    _require(track_id in context["tracks"], f"event {event.get('event_id')} names no census track")
    _require(event.get("event_id") == event_id(event.get("level"), tid, track_id, event["verb"]),
             f"event id {event.get('event_id')} is not the hash of its key")
    _require(event["subject"].get("roles") == _bound(context["bindings"], track_id, tid),
             f"event {event['event_id']} carries roles that are not bound to its track at {tid}")
    ends = any(b["track_id"] == track_id and b["ends_at_transition"] == tid for b in context["bindings"])
    _require(bool(event["flags"].get("role_binding_ends")) == ends, f"event {event['event_id']} misstates a binding end")
    sites, _rewrites = changed_sites(event)
    groups = ((event.get("delta") or {}).get("footprint") or {}).get("membership_groups") or {}
    for name in CHANGE_GROUPS:
        for group in groups.get(name) or ():
            if group["before_class"] != group["after_class"]:
                for cell in run_cells(group["cell_runs"]):
                    _require(pixels.get(cell) == (group["before_class"], group["after_class"]),
                             f"event {event['event_id']} claims a pixel rewrite at {cell} the record does not hold")
    explanation = event.get("explanation") or {}
    _require(explanation.get("status") in EXPLANATIONS, "an explanation status is EXPLAINED, PARTLY_EXPLAINED or UNEXPLAINED")
    known = set(context["receipts"]["evidence"]) | set(context["receipts"]["products"]) | set(context["receipts"]["witnesses"])
    for ref in explanation.get("refs") or ():
        _require(ref in known, f"event {event['event_id']} cites {ref!r}, which no receipt resolves")
    _require(explanation == explain(event, record, context["receipts"], context["roles"]),
             f"event {event['event_id']}'s explanation is not what its receipts and certified roles give")


def _validate_records(description: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    limit = (description.get("first_mismatch") or {}).get("transition_id")
    seen: dict[str, Mapping[str, Any]] = {}
    for record in description["transitions"]:
        tid = record["transition_id"]
        verified = limit is None or tid < limit
        _require(record.get("record_status") == ("VERIFIED" if verified else "UNVERIFIED_AFTER_MISMATCH"),
                 f"record {tid} misstates whether it lies in the verified prefix")
        stills = [record.get(k) for k in ("still_total", "still_emitted", "still_omitted")]
        _require(all(isinstance(v, int) and v >= 0 for v in stills) and stills[0] == stills[1] + stills[2],
                 f"record {tid}: still_total must equal still_emitted + still_omitted")
        if not verified:
            _require(not record["events"] and record.get("pixel_rewrite") is None and stills[0] == 0,
                     f"record {tid} lies after the verified prefix and may describe nothing")
            continue
        _require(stills[1] == sum(1 for e in record["events"] if e.get("verb") == "STILL"),
                 f"record {tid}: still_emitted must count its STILL events")
        pixels = {cell: (g["before_class"], g["after_class"]) for g in (record.get("pixel_rewrite") or {}).get("changed") or ()
                  for cell in run_cells(g["cell_runs"])}
        for event in record["events"]:
            _require(event.get("event_id") not in seen, f"event id {event.get('event_id')} is not unique")
            _validate_event(event, record, pixels, context)
            seen[event["event_id"]] = event
    return seen


def _validate_bindings(description: Mapping[str, Any], events: Mapping[str, Mapping[str, Any]],
                       context: Mapping[str, Any], gaps: Sequence[Mapping[str, Any]] | None) -> None:
    _require(description.get("role_bindings") == context["bindings"],
             "the description's role bindings disagree with the certified roles' identities and binding ends")
    limit = (description.get("first_mismatch") or {}).get("transition_id")
    for binding in context["bindings"]:
        ends = binding["ends_at_transition"]
        if ends is None:
            continue
        _require(limit is None or ends < limit, "a binding cannot end after the verified prefix")
        _require(any(e["verb"] == "RECOLOR" and e["transition_id"] == ends and e["subject"]["track_id"] == binding["track_id"]
                     for e in events.values()), f"the {binding['role']} binding ends at {ends} without a class change")
        if gaps is not None:
            _require(any(g.get("reason") == "CLASS_CHANGED" and g.get("track_id") == binding["track_id"]
                         and ends in (g.get("transitions") or ()) for g in gaps),
                     f"the {binding['role']} binding ended at {ends} with no CLASS_CHANGED gap")


def _validate_scene(description: Mapping[str, Any], events: Mapping[str, Mapping[str, Any]],
                    context: Mapping[str, Any], gaps: Sequence[Mapping[str, Any]] | None) -> None:
    scene = description.get("scene") or {}
    as_of, node = _as_of(description)
    _require(scene.get("as_of_transition") == as_of and scene.get("as_of_node") == node,
             "the scene is taken at the last verified transition")
    _require(scene.get("record_mismatch") == description.get("first_mismatch"), "the scene states the record mismatch")
    presence = description.get("presence") or {}
    limit = (description.get("first_mismatch") or {}).get("transition_id")
    entry_node = int(description["basis"]["entry_node"])
    for track_id, spans in presence.items():
        _require(track_id in context["tracks"], f"presence names an unknown track {track_id}")
        _require(all(verified_node(a, entry_node, limit) and verified_node(b, entry_node, limit) and a <= b
                     for a, b in spans), "presence spans lie in the verified prefix")
    present = [item["track_id"] for item in scene.get("present") or ()]
    departed = [item["track_id"] for item in scene.get("departed") or ()]
    unverified = list(scene.get("unverified_tracks") or ())
    listed = present + departed + unverified
    _require(len(listed) == len(set(listed)) and set(listed) == set(context["tracks"]),
             "the scene's present, departed and unverified tracks must partition the level's tracks")
    _require(set(present) == {t for t, s in presence.items() if any(a <= node <= b for a, b in s)},
             "the scene's present tracks are those seen at its verified node (partition)")
    _require(set(unverified) == set(context["tracks"]) - set(presence), "unverified tracks are those never seen verified (partition)")
    expected = [i for i, e in events.items() if e["verb"] != "STILL" and e["explanation"]["status"] == "UNEXPLAINED"]
    _require(list(scene.get("unexplained") or ()) == expected, "the scene's unexplained list must name exactly its unexplained events")
    _require(scene.get("open_identity") == open_identities(context["roles"]), "the scene's open_identity must name the unresolved roles")
    if gaps is not None:
        for item in scene["open_identity"]:
            _require(any(g.get("reason") == "IDENTITY_UNRESOLVED" and str(g.get("subject")) == item["subject"] for g in gaps),
                     f"open_identity {item['subject']} resolves to no IDENTITY_UNRESOLVED gap")
        if description.get("first_mismatch"):
            _require(any(g.get("reason") == "RECORD_MISMATCH" for g in gaps), "a description cut short carries a RECORD_MISMATCH gap")


def validate_description(description: Mapping[str, Any], *, recorded: Iterable[int], tracks: Iterable[Any],
                         receipts: Mapping[str, Any], roles: Sequence[Mapping[str, Any]],
                         gaps: Sequence[Mapping[str, Any]] | None = None) -> None:
    """Refuse a description that is not exactly what its records, tracks, roles and receipts support."""
    _require(isinstance(description, Mapping) and description.get("schema") == DESCRIPTION_SCHEMA,
             f"a v3 level carries a {DESCRIPTION_SCHEMA} description")
    ids = sorted({int(tid) for tid in recorded})
    _require([r.get("transition_id") for r in description.get("transitions") or ()] == ids,
             "the description holds exactly one record per recorded transition, ascending")
    mismatch = description.get("first_mismatch")
    _require((description.get("integrity") == "VERIFIED") == (mismatch is None)
             and description.get("integrity") in {"VERIFIED", "RECORD_MISMATCH"}, "integrity states the first mismatch")
    if mismatch is not None:
        _require(mismatch.get("reason") in MISMATCH_REASONS and isinstance(mismatch.get("transition_id"), int),
                 "first_mismatch names a transition and a reason")
    entry_node = int((description.get("basis") or {}).get("entry_node", -1))
    verified = [tid for tid in ids if mismatch is None or tid < mismatch["transition_id"]]
    _require(verified == list(range(entry_node + 1, entry_node + 1 + len(verified))),
             "the verified records run contiguously from the transition after the entry board")
    for ref, witness in (receipts.get("witnesses") or {}).items():
        if "witness_sha256" in witness:
            _require(witness["witness_sha256"] == witness_sha256(ref, witness), f"witness receipt {ref} disagrees with its hash")
    context = {"tracks": {t if isinstance(t, str) else t["track_id"] for t in tracks}, "receipts": receipts,
               "roles": list(roles), "bindings": _expected_bindings(roles)}
    events = _validate_records(description, context)
    _validate_bindings(description, events, context, gaps)
    _validate_scene(description, events, context, gaps)


__all__ = ["DESCRIPTION_SCHEMA", "NINE", "VERBS", "cell_runs", "changed_sites", "describe_level", "event_id", "explain",
           "first_mismatch", "open_identities", "restrict_description", "role_ref", "run_cells", "scene_at",
           "validate_description", "witness_sha256"]
