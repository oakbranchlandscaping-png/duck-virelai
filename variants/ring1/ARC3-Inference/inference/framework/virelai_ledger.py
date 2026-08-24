"""Ring 1 — the Virelai ledger: a walked-edge world map over settled grids.

REBUILD-FRESH per ruling R-H1 (Memo No.1, 2026-08-23): orchestration is new code;
nothing here is copied from legacy. Design origins, READ not copied, cited per R-C:

  node key = hash of the settled grid ........ virelai_v4/weave/induced_map.py (RULING F2)
  untried = available - observed ............. induced_map.untried_actions
  labels over (ledger, observation) .......... virelai_v4/weave/frontier_tag.py (shape only)

Delivery law: SUBTRACTION NEVER ANNOTATION. The menu the model sees shrinks; options
are never decorated with advice. The digest is the single sanctioned surface
(<=100 tokens) and states only what the record holds.

Grain: whole-action for the simple actions (UP/DOWN/LEFT/RIGHT/SPACE). MOUSE is
tracked at whole-action grain and NEVER subtracted -- per-coordinate pruning is a
later rung (frontier_tag's own scope rule). RESET is tracked and NEVER subtracted.

Tier A (mechanically certain, ratio-free): at THIS node, the action has been tried
and has NEVER produced a board change here. No count threshold and no confidence
number -- one observed no-op seals; a later observed change at the same node
un-seals, because the seal is recomputed from the full record every turn and the
record never deletes (deprioritize-never-delete holds one rung up; here at Tier A
only the recompute rule is needed).

Fail-open: if subtraction would leave no playable non-RESET action, the menu is
returned unpruned and the digest says the node is exhausted. A pruned-to-nothing
menu would convert a fact into a deadlock.

Post-RESET continuity is free: RESET lands on a grid whose hash is (usually) a
known node, so the ledger reattaches with no prompt memory. That is the amnesia
fix, and it is a property of the key, not a feature of this class.

Budget: one sha256 of the grid repr + dict ops per turn. Stdlib only. Target
<<1 ms against the 50 ms typical / 200 ms hard per-turn law (CHAMBER_BOOTSTRAP).

Everything in-process and per-game: one ledger per GameSolver, dying with it.
The firewall is untouched -- keys are hashes, contents are action labels; no
world name, colour, or content crosses out of the game.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable

# Model-facing labels (see inference/agent/action_names.py). One grain throughout:
# the ledger stores what the menu shows.
NEVER_PRUNE = frozenset({"RESET", "MOUSE"})


def node_key(grid: Any, level: Any) -> str:
    """Identity of a settled frame: hash over (level, grid contents).

    Level is folded in defensively: two levels that happen to render identical
    grids must not merge (the map is per-course, not per-picture).
    """
    h = hashlib.sha256()
    h.update(repr(level).encode())
    h.update(repr(grid).encode())
    return h.hexdigest()[:16]


@dataclass
class ActionRecord:
    tries: int = 0
    changes: int = 0                      # board_changed observations
    dests: set = field(default_factory=set)  # node keys reached


@dataclass
class Node:
    arrivals: int = 0
    actions: dict = field(default_factory=dict)  # label -> ActionRecord


class VirelaiLedger:
    """The walked-edge map. Records what was pressed where and what it did."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: int = 0

    # ------------------------------------------------------------------ record
    def record(self, prev_key: str, action_label: str, new_key: str,
               board_changed: bool) -> None:
        label = str(action_label or "").strip().upper()
        if not label:
            return
        node = self.nodes.setdefault(prev_key, Node())
        rec = node.actions.setdefault(label, ActionRecord())
        rec.tries += 1
        if board_changed:
            rec.changes += 1
        rec.dests.add(new_key)
        self.edges += 1
        self.nodes.setdefault(new_key, Node()).arrivals += 1

    # ------------------------------------------------------------------ reads
    def _sealed_here(self, key: str) -> list[str]:
        """Tier A at this node: tried, never changed the board here, prunable."""
        node = self.nodes.get(key)
        if node is None:
            return []
        return sorted(
            label for label, rec in node.actions.items()
            if rec.tries > 0 and rec.changes == 0 and label not in NEVER_PRUNE
        )

    def menu_and_digest(self, key: str, valid_actions: Iterable[str]) -> tuple[list[str], str]:
        """The pruned menu and the <=100-token digest for the node we are ON."""
        valid = [str(v).strip().upper() for v in (valid_actions or []) if str(v).strip()]
        node = self.nodes.get(key)
        sealed = set(self._sealed_here(key))
        pruned = [v for v in valid if v not in sealed]

        # Fail-open: never hand back a menu with no playable non-RESET action.
        playable = [v for v in pruned if v != "RESET"]
        exhausted = bool(sealed) and not playable
        if exhausted:
            pruned = list(valid)

        parts: list[str] = []
        if node is None or node.arrivals <= 1 and not (node and node.actions):
            parts.append(f"[MAP] New position (state {key[:6]}). "
                         f"{len(self.nodes)} states, {self.edges} moves mapped this game.")
        else:
            parts.append(f"[MAP] Known position (state {key[:6]}, visit {node.arrivals}). "
                         f"{len(self.nodes)} states, {self.edges} moves mapped.")
            tried_bits = []
            for label in sorted(node.actions):
                rec = node.actions[label]
                if rec.changes == 0:
                    tried_bits.append(f"{label}: no effect x{rec.tries}")
                else:
                    tried_bits.append(
                        f"{label}: changed board {rec.changes}/{rec.tries}"
                        + (f" ({len(rec.dests)} outcomes)" if len(rec.dests) > 1 else "")
                    )
            if tried_bits:
                parts.append("Tried here -- " + "; ".join(tried_bits) + ".")
        untried = [v for v in valid if node is None or v not in node.actions]
        untried = [v for v in untried if v != "RESET"]
        if untried:
            parts.append("Untried here: " + ", ".join(untried) + ".")
        removed = sorted(sealed & set(valid)) if not exhausted else []
        if removed:
            parts.append("Menu pruned of proven no-ops here: " + ", ".join(removed) + ".")
        if exhausted:
            parts.append("Every simple action is a proven no-op at this position; "
                         "full menu kept -- consider MOUSE elsewhere or RESET.")
        return pruned, " ".join(parts)
