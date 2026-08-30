"""WO_CLAIM_DECOMPOSER · B2/B3 — decompose the induced map into human-gradable claims.

The graph is fact-checked not by inspecting its structure but by decomposing it into
the physics grammar's own claim shapes:

  - TRANSITION claims (the fork-witness sweep, B2): for a world-node that merged ≥2
    raw grids, if two members take the SAME action to DIFFERENT world-successors, the
    merge is behaviourally contradicted — a fork-witness (clay's vocabulary,
    ``clay.py:121``). Per fork, the recorded HUD mask is overlaid on the cells that
    distinguish the two merged members, and ``mask_accounts_for_difference`` is
    reported as a set-membership FACT (YES = every distinguishing cell is masked;
    NO = none; PARTIAL = some).
  - IDENTITY claims (the contact sheet, B3): for a merged world-node, its raw members'
    settled grids are rendered side by side with the mask marked — the assertion
    "these grids are one room", laid out for a human.

Governing rulings:
  - The code SURFACES claims, never grades them. Every claim carries EMPTY
    ``FIDELITY`` / ``CORRECTNESS`` columns for a human to fill. ``mask_accounts_...``
    is a set-membership fact, not a verdict — the code never rules bad-mask vs
    hidden-state. That collision, rendered, is the whole point.
  - Pure read over (raw map, world map, records, mask): no ``library/`` import, no
    belief write. Mirrors ``frontier_tag`` / ``world_grain`` injection discipline —
    the mask is an injected parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Tuple

from virelai_v4.weave.grid_render import diff_cells, render_diff_overlay, render_grid
from virelai_v4.weave.induced_map import InducedMap, _default_key
from virelai_v4.weave.world_grain import world_key, world_members

Cell = Tuple[int, int]


# ---------------------------------------------------------------------------
# Transition claims — the fork-witness sweep
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ForkClaim:
    """A transition claim: one merged world-node where two members took the same
    action to different world-successors. Carries the FACTS, no verdict."""

    world_node: str
    action: Any
    member_a: str          # raw key
    member_b: str          # raw key
    successor_a: str       # world-successor key (member_a's)
    successor_b: str       # world-successor key (member_b's)
    n_diff_cells: int      # cells distinguishing member_a and member_b
    n_masked_diff: int     # how many of those are in the recorded mask
    mask_accounts_for_difference: str   # YES | NO | PARTIAL — a set-membership FACT


def _account(n_diff: int, n_masked: int) -> str:
    if n_diff == 0:
        return "NO"
    if n_masked == n_diff:
        return "YES"
    if n_masked == 0:
        return "NO"
    return "PARTIAL"


def fork_sweep(
    raw_map: InducedMap, world_map: InducedMap, records, hud_mask: "FrozenSet[Cell]"
) -> List[ForkClaim]:
    """Collect fork-witnesses — never judge them. For each world-node merging ≥2 raw
    members, per action fired by the members, lift each member's raw successor to its
    world-node; if the same action reaches ≥2 distinct world-successors, emit a fork
    claim with the recorded-mask overlay computed by set-membership."""
    members = world_members(world_map, records)
    raw_grid: Dict[str, Any] = {_default_key(r): r.layers[-1] for r in records}

    claims: List[ForkClaim] = []
    for wk, raws in members.items():
        if len(raws) < 2:
            continue
        by_action: Dict[Any, List[Tuple[str, str]]] = {}   # action → [(raw_key, world_successor)]
        for rk in sorted(raws):
            node = raw_map.nodes.get(rk)
            if node is None:
                continue
            for e in node.out_edges:
                succ_grid = raw_grid.get(e.dst)
                succ_world = world_key(succ_grid, hud_mask) if succ_grid is not None else e.dst
                by_action.setdefault(e.label[0], []).append((rk, succ_world))

        for action, lst in by_action.items():
            first_by_successor: Dict[str, str] = {}
            for rk, succ_world in lst:
                first_by_successor.setdefault(succ_world, rk)
            if len(first_by_successor) < 2:
                continue                              # no divergence: not a fork
            (sw_a, rk_a), (sw_b, rk_b) = sorted(first_by_successor.items())[:2]
            g_a, g_b = raw_grid.get(rk_a), raw_grid.get(rk_b)
            diffs = diff_cells(g_a, g_b)
            n_masked = sum(1 for cell in diffs if cell in hud_mask)
            claims.append(ForkClaim(
                world_node=wk, action=action,
                member_a=rk_a, member_b=rk_b,
                successor_a=sw_a, successor_b=sw_b,
                n_diff_cells=len(diffs), n_masked_diff=n_masked,
                mask_accounts_for_difference=_account(len(diffs), n_masked),
            ))
    return claims


# ---------------------------------------------------------------------------
# Identity claims — the contact sheet
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IdentityClaim:
    """An identity claim: a world-node asserts its raw members are one room."""

    world_node: str
    members: Tuple[str, ...]   # raw keys, sorted


def contact_claims(world_map: InducedMap, records) -> List[IdentityClaim]:
    """One identity claim per merged (≥2-member) world-node."""
    members = world_members(world_map, records)
    return [
        IdentityClaim(world_node=wk, members=tuple(sorted(raws)))
        for wk, raws in members.items() if len(raws) >= 2
    ]


# ---------------------------------------------------------------------------
# Rendering — claims with EMPTY grade columns (the human grades)
# ---------------------------------------------------------------------------

def _fmt_action(action: Any) -> str:
    return f"a{action}" if not isinstance(action, tuple) else f"a{action[0]}@{action[1]}"


_EMPTY_GRADE = "  FIDELITY:    [ ]\n  CORRECTNESS: [ ]"


def render_fork_claim(claim: ForkClaim, raw_grid: Dict[str, Any], hud_mask: "FrozenSet[Cell]") -> str:
    g_a, g_b = raw_grid.get(claim.member_a), raw_grid.get(claim.member_b)
    lines = [
        f"FORK CLAIM · world[{claim.world_node[:8]}] · action {_fmt_action(claim.action)}",
        f"  member A [{claim.member_a[:8]}] --{_fmt_action(claim.action)}--> world[{claim.successor_a[:8]}]",
        f"  member B [{claim.member_b[:8]}] --{_fmt_action(claim.action)}--> world[{claim.successor_b[:8]}]",
        f"  distinguishing cells: {claim.n_diff_cells} · masked: {claim.n_masked_diff} · "
        f"mask_accounts_for_difference: {claim.mask_accounts_for_difference}  (fact, not a verdict)",
        "  mask overlay (M=differing∧masked, X=differing∧unmasked, .=same):",
    ]
    overlay = render_diff_overlay(g_a, g_b, hud_mask)
    lines += ["    " + ln for ln in overlay.splitlines()]
    lines.append(_EMPTY_GRADE)
    return "\n".join(lines)


def render_contact_claim(
    claim: IdentityClaim, raw_grid: Dict[str, Any], hud_mask: "FrozenSet[Cell]", *, max_members: int = 4
) -> str:
    lines = [
        f"IDENTITY CLAIM · world[{claim.world_node[:8]}] asserts {len(claim.members)} "
        f"raw grids are ONE room:",
    ]
    for rk in claim.members[:max_members]:
        lines.append(f"  raw [{rk[:8]}] (mask marked):")
        lines += ["    " + ln for ln in render_grid(raw_grid.get(rk), hud_mask).splitlines()]
    if len(claim.members) > max_members:
        lines.append(f"  … +{len(claim.members) - max_members} more members")
    lines.append(_EMPTY_GRADE)
    return "\n".join(lines)


def render_audit_sheet(
    raw_map: InducedMap, world_map: InducedMap, records, hud_mask: "FrozenSet[Cell]",
    *, max_contact: int = 8,
) -> str:
    """The full audit sheet a chamber grades: fork claims (transitions) + contact
    sheets (identities), every grade column empty. The code surfaces; it never rules."""
    recs = list(records)
    raw_grid: Dict[str, Any] = {_default_key(r): r.layers[-1] for r in recs}
    forks = fork_sweep(raw_map, world_map, recs, hud_mask)
    identities = contact_claims(world_map, recs)

    yes = sum(1 for f in forks if f.mask_accounts_for_difference == "YES")
    out = [
        "########## CLAIM AUDIT ##########",
        f"transition claims (forks): {len(forks)}  "
        f"(mask_accounts YES={yes} — the interesting rows: mask claimed inert, behavior diverged)",
        f"identity claims (merged rooms): {len(identities)} · showing up to {max_contact}",
        f"HUD mask cells overlaid: {len(hud_mask)}",
        "grade columns are EMPTY by ruling — the chamber fills FIDELITY / CORRECTNESS.",
        "",
    ]
    for f in forks:
        out.append(render_fork_claim(f, raw_grid, hud_mask))
        out.append("")
    for c in identities[:max_contact]:
        out.append(render_contact_claim(c, raw_grid, hud_mask))
        out.append("")
    return "\n".join(out)
