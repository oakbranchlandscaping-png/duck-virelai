"""Ring 2 -- the Virelai ledger v3: walked-edge record, COUNTER seal, world grain.

Lineage: Ring 1 ledger (walked-edge map, Tier-A subtraction, digest) -> Ring 1.1
(RESET root, batch account, snapshot) -> THIS (per-edge changed-cell record, the
behavioral COUNTER seal, counter-masked world identity, world_changed).

Design origins, READ not copied, cited per R-C (full table: variants/ring2/DESIGN.md):
  mask-then-hash node identity ...... virelai_v4/library/cycle_probe._hud_masked_state_hash
                                      (WO-CP1-FIX-B: unmasked counter tick = the K-cap burn)
  two grains, mask-as-view .......... virelai_v4/weave/world_grain.py (R-H1a(v) shape)
  idempotent fold ................... virelai_v4/weave/induced_map.py
  not-acted-member witness .......... virelai_v4/weave/role_read._marginal_counter_seal
                                      (R-H1a(iii) evidence shape)
  seal-never-threshold .............. AMENDMENT_PROBE_STRATEGY rider par-B
  counter = attribution-quarantine .. rider par-C (the counter stays perceived, always)

Laws honored: no threshold or confidence number anywhere (the seal is four count/
quantifier conjuncts; one counter-witness kills; recomputed every turn -- buckets
drain). RESET is a back-edge, never a transition (G11); level-crossing edges are
boundary events and never enter seal evaluation. Grids are stored (derived-but-
retained, canon 2 par-1 H-ruling) so the world map can re-key when the mask changes.
Loudness: seals, unseals, and boundary events are stated in the digest, never absorbed.

Pre-registered limitation (DESIGN.md): a never-blocked ego moving on every press under
2+ labels with constant magnitude can falsely seal; one STILL edge kills it.

Budget: record ~O(cells) per turn; seal evaluation + world-map fold are cached and
rebuilt only when the record or mask changes. Stdlib only. Firewall: keys are hashes,
labels are action names; no world content leaves the game; the ledger dies with it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from inference.framework import virelai_weave as VW

NEVER_PRUNE = frozenset({"RESET", "MOUSE"})
_MASK_SENTINEL = "\x00MASKED\x00"


def _grid_cells(grid: Any) -> dict:
    """Normalize a grid (list-of-lists) to {(r,c): value}."""
    cells = {}
    try:
        for r, row in enumerate(grid):
            for c, v in enumerate(row):
                cells[(r, c)] = v
    except TypeError:
        cells[(0, 0)] = repr(grid)
    return cells


def raw_key(grid: Any, level: Any) -> str:
    h = hashlib.sha256()
    h.update(repr(level).encode())
    h.update(repr(grid).encode())
    return h.hexdigest()[:16]


def _masked_key(grid_cells: dict, level: Any, mask: frozenset) -> str:
    h = hashlib.sha256()
    h.update(repr(level).encode())
    for rc in sorted(grid_cells):
        v = _MASK_SENTINEL if rc in mask else grid_cells[rc]
        h.update(repr((rc, v)).encode())
    return h.hexdigest()[:16]


@dataclass
class Edge:
    prev_raw: str
    label: str
    new_raw: str
    changed: frozenset          # cells whose value changed
    level: Any
    crossed_level: bool
    coord: Optional[tuple] = None   # (row, col) for MOUSE presses; the acted cell


@dataclass
class ActionRecord:
    tries: int = 0
    changes: int = 0            # world_changed observations (outside-mask change)
    dests: set = field(default_factory=set)


@dataclass
class Node:
    arrivals: int = 0
    actions: dict = field(default_factory=dict)


@dataclass
class CounterSeal:
    cells: frozenset
    bbox: tuple                 # (r0, r1, c0, c1)
    presses: int
    labels: int
    magnitude: int
    click_witness: bool


class VirelaiLedger:
    """v3: append-only raw record + counter seal + masked world view."""

    def __init__(self) -> None:
        # --- the raw record (append-only; the ground truth) ---
        self.grids: dict[str, dict] = {}        # raw_key -> {(r,c): value}
        self.levels: dict[str, Any] = {}        # raw_key -> level
        self.edges: list[Edge] = []
        self.resets: list[str] = []             # raw arrival keys, in order
        self.current_raw: Optional[str] = None
        # --- derived views (recomputed; never authoritative) ---
        self._seal_cache_len: int = -1
        self._seals: list[CounterSeal] = []
        self._mask: frozenset = frozenset()
        self._map_cache_sig: tuple = ()
        self._nodes: dict[str, Node] = {}
        self._root_key: Optional[str] = None
        self._notes: list[str] = []             # loud one-shot digest lines
        self.last_world_changed: Optional[bool] = None
        # --- Ring 2.5: world type, weave, ego ---
        self._roster: set = set()
        self._world_type: Optional[str] = None
        self.weave = VW.Weave()
        self._comp_cache: dict = {}             # (raw_key, mask) -> [Region]
        # counter announce-delay (ring2 feedback): seal id -> edge-count first seen
        self._seal_first_seen: dict = {}
        self._announced: list = []              # announced seal cell-sets
        # --- Ring 3: drains + levers ---
        self._drains: list = []                 # sealed ego-coupled drain regions
        self._drain_announced: list = []
        self._levers: dict = {}                 # target key -> {"witness": n, "effects": [...], "desc": str}
        self._lever_announced: set = set()

    # ------------------------------------------------------------------ record
    def _intern(self, grid: Any, level: Any) -> str:
        k = raw_key(grid, level)
        if k not in self.grids:
            self.grids[k] = _grid_cells(grid)
            self.levels[k] = level
        return k

    def record(self, prev_grid: Any, prev_level: Any, action_label: str,
               new_grid: Any, new_level: Any, coord: Optional[tuple] = None) -> bool:
        """Record one press. Returns world_changed (outside current mask)."""
        label = str(action_label or "").strip().upper()
        pk = self._intern(prev_grid, prev_level)
        nk = self._intern(new_grid, new_level)
        self.current_raw = nk
        if label == "RESET":
            self.resets.append(nk)
            self.last_world_changed = None
            self._thread_edge(pk, nk, "RESET", site_only=True)
            return True
        pc, nc = self.grids[pk], self.grids[nk]
        changed = frozenset(rc for rc in nc if pc.get(rc) != nc[rc])
        if len(pc) != len(nc):  # shape change: treat every cell as changed
            changed = frozenset(set(pc) | set(nc))
        self.edges.append(Edge(pk, label, nk, changed, new_level,
                               prev_level != new_level, coord))
        world_changed = bool(changed - self.mask())
        self.last_world_changed = world_changed
        self._thread_edge(pk, nk, label, site_only=False)
        if label == "MOUSE" and coord is not None and world_changed:
            self._lever_witness(pk, tuple(coord), changed)
        return world_changed

    # ------------------------------------------------------- levers (Ring 3)
    def _lever_witness(self, pk: str, coord: tuple, changed: frozenset) -> None:
        """LEVER is existential: one located click followed by world change is a
        witness; later silence never retracts (canon 2 par-6.2). CLICK-scope only."""
        pc = self.grids[pk]
        if coord not in pc:
            return
        v = pc[coord]
        comp, stack, todo = {coord}, [coord], set(pc)
        while stack:
            r, c = stack.pop()
            for nb in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if nb in todo and nb not in comp and pc.get(nb) == v:
                    comp.add(nb); stack.append(nb)
        effect = changed - self.mask() - frozenset(comp)
        if not effect:
            return
        rs=[r for r,_ in comp]; cs=[c for _,c in comp]
        key = (v, min(rs), max(rs), min(cs), max(cs))
        ent = self._levers.setdefault(key, {"witness": 0, "effect_cells": 0,
            "desc": f"class-{v} object at rows {min(rs)}-{max(rs)} x cols {min(cs)}-{max(cs)}"})
        ent["witness"] += 1
        ent["effect_cells"] = len(effect)
        if key not in self._lever_announced:
            self._lever_announced.add(key)
            self._notes.append(
                f"[LEVER] sealed: clicking the {ent['desc']} changed {len(effect)} "
                f"cells elsewhere. One witness proves a lever; silence never retracts.")

    # ------------------------------------------- ego-coupled drains (Ring 3)
    def _evaluate_drains(self) -> None:
        """DRAIN(ego-motion) seal, the ls20 finding mechanized: >=2 ego-MOVE edges all
        ticking R, >=2 no-ego-move edges all holding R. Counts only; one violation
        kills; recomputed from the record (buckets drain)."""
        egos = self.weave.egos()
        if not egos:
            self._drains = []
            return
        edges = self._eligible_edges()
        if len(edges) < 4:
            self._drains = []
            return
        # which edges saw an ego MOVE: read from each sealed ego's footprint TRAIL
        # (worldline.at: edge_idx -> footprint after that edge) -- per-edge record,
        # never the current footprint (past moves happened at past positions).
        idx_of = {id(e): i for i, e in enumerate(self.edges)}
        moved_idx = set()
        for w in egos:
            moved_idx |= w.moved_at
        move_e = [e for e in edges if idx_of[id(e)] in moved_idx]
        still_e = [e for e in edges if idx_of[id(e)] not in moved_idx]
        ego_cells = frozenset().union(*[w.cells for w in egos])
        for w in egos:
            for fp in w.at.values():
                ego_cells |= fp
        if len(move_e) < 2 or len(still_e) < 2:
            self._drains = []
            return
        drains = []
        for R in self._churn_regions(edges):
            if R & self._mask or R & ego_cells:
                continue
            if all(R & e.changed for e in move_e) and all(not (R & e.changed) for e in still_e):
                drains.append(R)
        for R in drains:
            if not any(R & a for a in self._drain_announced):
                self._drain_announced.append(R)
                rs=[r for r,_ in R]; cs=[c for _,c in R]
                self._notes.append(
                    f"[DRAIN] sealed: the region at rows {min(rs)}-{max(rs)} x cols "
                    f"{min(cs)}-{max(cs)} ticks exactly when you MOVE ({len(move_e)} "
                    f"move edges all ticked; {len(still_e)} non-move edges all held). "
                    f"Moving costs it; blocked and non-move presses are free.")
        self._drain_announced = [a for a in self._drain_announced
                                 if any(a & d for d in drains)]
        self._drains = drains

    # -------------------------------------------------------- the weave (Ring 2.5)
    def _components(self, rk: str):
        key = (rk, self._mask)
        got = self._comp_cache.get(key)
        if got is None:
            got = VW.components(self.grids[rk], exclude=self._mask)
            self._comp_cache[key] = got
        return got

    def _thread_edge(self, pk: str, nk: str, label: str, site_only: bool) -> None:
        """Thread the light weave. Ego search runs only where the roster licenses it
        (NAV/HYBRID -- Director's world-type ruling 2026-08-26); threading itself is
        cheap and runs always, feeding later rungs."""
        try:
            self.weave.thread(self._components(pk), self._components(nk),
                              label, site_only=site_only,
                              edge_idx=(len(self.edges) - 1 if not site_only else None))
            self.weave.settle()      # Ring 5: verdicts + their announcements
        except Exception as exc:  # the weave must never kill a turn -- loud, not fatal
            self._notes.append(f"[WEAVE] threading error ({type(exc).__name__}) -- "
                               f"worldline view degraded this edge; record intact.")

    # ------------------------------------------------------------- the seal
    def _eligible_edges(self) -> list[Edge]:
        lvl = self.levels.get(self.current_raw)
        return [e for e in self.edges if not e.crossed_level and e.level == lvl]

    def _churn_regions(self, edges: list[Edge]) -> list[frozenset]:
        churn = set()
        for e in edges:
            churn |= e.changed
        regions, seen = [], set()
        for start in churn:
            if start in seen:
                continue
            comp, stack = set(), [start]
            while stack:
                rc = stack.pop()
                if rc in comp:
                    continue
                comp.add(rc)
                r, c = rc
                for nb in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if nb in churn and nb not in comp:
                        stack.append(nb)
            seen |= comp
            regions.append(frozenset(comp))
        return regions

    def _evaluate_seals(self) -> None:
        """Recompute COUNTER seals from the record (DESIGN.md conjuncts 1-4)."""
        if len(self.edges) == self._seal_cache_len:
            return
        self._seal_cache_len = len(self.edges)
        old_cells = {s.cells for s in self._seals}
        edges = self._eligible_edges()
        seals: list[CounterSeal] = []
        labels = {e.label for e in edges}
        mouse_edges = [e for e in edges if e.label == "MOUSE"]
        if len(edges) >= 2 and len(labels) >= 2:
            for region in self._churn_regions(edges):
                mags = {len(region & e.changed) for e in edges}
                if len(mags) != 1 or 0 in mags:
                    continue  # conjunct 1 (ticked every press) or 3 (stable) failed
                # conjunct 4: the not-acted-member witness (role_read.
                # _marginal_counter_seal shape): when clicks with known coordinates
                # exist, the seal REQUIRES at least one click that landed OUTSIDE
                # the region while the region still ticked. A region only ever
                # clicked ON is being operated, not scheduling itself -- exactly
                # the "segmented bar mistaken for clickable pieces" case.
                located = [e for e in mouse_edges if e.coord is not None]
                if located:
                    witness = any(tuple(e.coord) not in region for e in located)
                    if not witness:
                        continue
                else:
                    witness = False
                rs = [rc[0] for rc in region]; cs = [rc[1] for rc in region]
                seals.append(CounterSeal(
                    cells=region,
                    bbox=(min(rs), max(rs), min(cs), max(cs)),
                    presses=len(edges), labels=len(labels),
                    magnitude=next(iter(mags)), click_witness=witness,
                ))
        # Announcement identity is by OVERLAP (a sweeping counter grows silently),
        # and -- ring2 feedback refinement -- a seal is ANNOUNCED only after it has
        # survived at least one press beyond its sealing evidence. The MASK applies
        # immediately either way: announcement gates attention, never mechanism.
        new_cells = {s.cells for s in seals}
        n_edges = len(self.edges)
        for s in seals:
            fs_key = next((k for k in self._seal_first_seen if k & s.cells), None)
            if fs_key is None:
                self._seal_first_seen[s.cells] = n_edges
                continue
            first_seen = self._seal_first_seen.pop(fs_key)
            self._seal_first_seen[s.cells] = first_seen
            already = any(s.cells & a for a in self._announced)
            if not already and n_edges > first_seen:
                self._announced.append(s.cells)
                r0, r1, c0, c1 = s.bbox
                self._notes.append(
                    f"[COUNTER] sealed: rows {r0}-{r1} x cols {c0}-{c1} "
                    f"({len(s.cells)} cells so far) ticked on all {s.presses} presses "
                    f"under {s.labels} distinct actions ({s.magnitude} cell/press). Now "
                    f"excluded from state identity. Watch it -- likely your budget.")
        for oc in old_cells:
            if not any(oc & nc for nc in new_cells):
                if any(oc & a for a in self._announced):
                    self._notes.append(
                        f"[COUNTER] UNSEALED: a press where the {len(oc)}-cell region "
                        f"held killed the seal. Its cells re-enter state identity; the "
                        f"map re-derives.")
                self._announced = [a for a in self._announced if not (a & oc)]
                self._seal_first_seen = {k: v for k, v in self._seal_first_seen.items()
                                         if not (k & oc)}
        self._seals = seals
        self._mask = frozenset().union(*new_cells) if new_cells else frozenset()

    def mask(self) -> frozenset:
        self._evaluate_seals()
        return self._mask

    # -------------------------------------------------------- the world view
    def _wkey(self, rk: str) -> str:
        m = self._mask
        if not m:
            return rk
        return _masked_key(self.grids[rk], self.levels[rk], m)

    def _rebuild_map(self) -> None:
        sig = (len(self.edges), len(self.resets), self._mask)
        if sig == self._map_cache_sig:
            return
        self._map_cache_sig = sig
        nodes: dict[str, Node] = {}
        root: Optional[str] = None
        for e in self.edges:
            pw, nw = self._wkey(e.prev_raw), self._wkey(e.new_raw)
            node = nodes.setdefault(pw, Node())
            rec = node.actions.setdefault(e.label, ActionRecord())
            rec.tries += 1
            if e.changed - self._mask:
                rec.changes += 1
            rec.dests.add(nw)
            nodes.setdefault(nw, Node()).arrivals += 1
        for rk in self.resets:
            wk = self._wkey(rk)
            nodes.setdefault(wk, Node()).arrivals += 1
            if root is None:
                root = wk
                self._notes.append("RESET: level start marked on the map.")
            elif wk == root:
                self._notes.append(
                    f"RESET: returned to level start (a known state, "
                    f"visit {nodes[wk].arrivals}).")
            else:
                self._notes.append(
                    "RESET landed on an UNKNOWN state -- boundary event (new level "
                    "or new attempt). Map root re-marked.")
                root = wk
        self._nodes = nodes
        self._root_key = root

    def _sealed_here(self, wk: str) -> list[str]:
        node = self._nodes.get(wk)
        if node is None:
            return []
        return sorted(l for l, r in node.actions.items()
                      if r.tries > 0 and r.changes == 0 and l not in NEVER_PRUNE)

    # ------------------------------------------------------------------ reads
    def menu_and_digest(self, valid_actions: Iterable[str]) -> tuple:
        self._evaluate_seals()
        self._rebuild_map()
        valid = [str(v).strip().upper() for v in (valid_actions or []) if str(v).strip()]
        wk = self._wkey(self.current_raw) if self.current_raw else None
        node = self._nodes.get(wk) if wk else None
        sealed = set(self._sealed_here(wk)) if wk else set()
        pruned = [v for v in valid if v not in sealed]
        playable = [v for v in pruned if v != "RESET"]
        exhausted = bool(sealed) and not playable
        if exhausted:
            pruned = list(valid)

        parts: list[str] = []
        self._evaluate_drains()
        # --- world type: a derivation over the observed roster (announce on change) ---
        prev_roster = frozenset(self._roster)
        self._roster.update(valid)
        wt = VW.world_type(frozenset(self._roster))
        if wt is not None and wt != self._world_type:
            self._world_type = wt
            parts.append(VW.world_type_line(wt, frozenset(self._roster)))
        if self.weave.notes:
            self._notes.extend(self.weave.notes)
            self.weave.notes = []
        if self._notes:
            parts.extend(self._notes)
            self._notes = []
        if node is None or (node.arrivals <= 1 and not node.actions):
            parts.append(f"[MAP] New position (state {wk[:6] if wk else '??'}). "
                         f"{len(self._nodes)} world-states, {len(self.edges)} moves mapped.")
        else:
            parts.append(f"[MAP] Known position (state {wk[:6]}, visit {node.arrivals}). "
                         f"{len(self._nodes)} world-states, {len(self.edges)} moves mapped.")
            bits = []
            for label in sorted(node.actions):
                rec = node.actions[label]
                if rec.changes == 0:
                    bits.append(f"{label}: no world effect x{rec.tries}")
                else:
                    bits.append(f"{label}: changed world {rec.changes}/{rec.tries}"
                                + (f" ({len(rec.dests)} outcomes)" if len(rec.dests) > 1 else ""))
            if bits:
                parts.append("Tried here -- " + "; ".join(bits) + ".")
        removed = sorted(sealed & set(valid)) if not exhausted else []
        if removed:
            parts.append("Menu pruned of proven no-ops here: " + ", ".join(removed) + ".")
        if exhausted:
            parts.append("Every simple action is a proven no-op at this position; "
                         "full menu kept -- consider MOUSE elsewhere or RESET.")
        egos = self.weave.egos()
        if egos:
            spots = []
            for w in egos:
                r0 = min(r for r, _ in w.cells); r1 = max(r for r, _ in w.cells)
                c0 = min(c for _, c in w.cells); c1 = max(c for _, c in w.cells)
                spots.append(f"rows {r0}-{r1} x cols {c0}-{c1}")
            parts.append("[EGO] at " + "; ".join(spots) + ".")
        fl = self._frontier_line(wk, valid)
        if fl:
            parts.append(fl)
        return pruned, " ".join(parts)

    # ---------------------------------------------- the frontier (Ring 3)
    def _untried_at(self, wk: str, roster: set) -> list:
        node = self._nodes.get(wk)
        tried = set(node.actions) if node else set()
        return sorted(l for l in roster if l != "RESET" and l not in tried)

    def _frontier_line(self, wk: Optional[str], valid: list) -> Optional[str]:
        """The win-novelty logic, led with: untried actions across visited states and
        the shortest KNOWN route (BFS over walked edges only -- witnessed presses,
        no terrain assumed; Rung 3.5's fence untouched). Routes are advisory."""
        if wk is None or not self._nodes:
            return None
        roster = set(self._roster)
        here = [l for l in valid if l != "RESET"
                and l not in (self._nodes.get(wk).actions if self._nodes.get(wk) else {})]
        frontier = {k: self._untried_at(k, roster) for k in self._nodes}
        frontier = {k: u for k, u in frontier.items() if u}
        total = sum(len(u) for u in frontier.values())
        if total == 0:
            return ("[FRONTIER] No untried actions remain on the walked map -- the "
                    "frontier is exhausted at the map's current reach. If no win was "
                    "seen, something unrecorded (a coordinate, a state off the map) "
                    "still holds it.")
        line = (f"[FRONTIER] The win lives in the untried: {total} untried actions "
                f"across {len(frontier)} visited states")
        if here:
            line += f" ({len(here)} right here: {', '.join(here)})."
            return line
        # BFS over walked edges (most-recent observed destination per (state,label))
        succ: dict = {}
        for e in self.edges:
            if e.crossed_level:
                continue
            pw, nw = self._wkey(e.prev_raw), self._wkey(e.new_raw)
            succ.setdefault(pw, {})[e.label] = nw
        from collections import deque
        seen = {wk}; q = deque([(wk, [])])
        route = None
        while q:
            cur, path = q.popleft()
            if cur in frontier and cur != wk:
                route = (cur, path); break
            for lab, dst in succ.get(cur, {}).items():
                if dst not in seen:
                    seen.add(dst); q.append((dst, path + [lab]))
        if route:
            tgt, path = route
            shown = path[:6]
            tail = f" ...({len(path)-6} more)" if len(path) > 6 else ""
            line += (f". Nearest frontier state is {len(path)} known presses away: "
                     f"{', '.join(shown)}{tail} -- then try: "
                     f"{', '.join(frontier[tgt][:4])}. (Route replays observed "
                     f"presses; hidden state may divert -- advisory.)")
        else:
            line += (". No walked route reaches a frontier state from here -- "
                     "RESET returns to the level start (a known state).")
        return line

    # ------------------------------------------------------------------ snapshot
    def snapshot(self) -> dict:
        self._evaluate_seals()
        self._rebuild_map()
        egos = []
        for w in self.weave.egos():
            r0 = min(r for r, _ in w.cells); r1 = max(r for r, _ in w.cells)
            c0 = min(c for _, c in w.cells); c1 = max(c for _, c in w.cells)
            egos.append({"bbox": [r0, r1, c0, c1], "class": w.class_id,
                         "cells": len(w.cells),
                         "moves_seen": w.move_count,
                         "observed": {l: sorted(ds) for l, ds in w.moves.items()}})
        _here = self._wkey(self.current_raw) if self.current_raw else None
        return {
            "root": self._root_key,
            "here": _here,
            "level": (self.levels.get(self.current_raw) if self.current_raw else None),
            "untried_here": (self._untried_at(_here, self._roster) if _here else []),
            "states": len(self._nodes),
            "moves": len(self.edges),
            "resets": len(self.resets),
            "world_type": self._world_type,
            "roster": sorted(self._roster),
            "ego": egos or None,
            "worldlines": len(self.weave.worldlines),
            "ego_candidates": len(self.weave.ego_candidates()),
            "drains": ([{"bbox": [min(r for r,_ in R), max(r for r,_ in R),
                                  min(c for _,c in R), max(c for _,c in R)],
                         "cells": len(R)} for R in self._drains] or None),
            "levers": ([dict(desc=e["desc"], witness=e["witness"],
                             effect_cells=e["effect_cells"])
                        for e in self._levers.values()] or None),
            "counter": ([{
                "bbox": list(s.bbox), "cells": len(s.cells),
                "presses": s.presses, "labels": s.labels,
                "cells_per_press": s.magnitude,
            } for s in self._seals] or None),
            "nodes": {
                key: {
                    "arrivals": node.arrivals,
                    "actions": {
                        label: {"tries": rec.tries, "changes": rec.changes,
                                "outcomes": len(rec.dests)}
                        for label, rec in node.actions.items()
                    },
                }
                for key, node in self._nodes.items()
            },
        }
