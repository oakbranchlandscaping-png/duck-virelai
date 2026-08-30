"""
virelai_v4/library/diagnostics.py — End-of-Life Diagnostic Renderer.

V3.5-format output: two-tier inventory table, fixed-width columns, plain
ASCII dividers. The terminal is the grading desk — format matches what
worked across 15 V3.5 campaigns.

Four sections per block:
    1. Life boundary header — plain = dividers
    2. Semantic Inventory — FOREGROUND / BACKGROUND split with fixed columns
    3. Tier Assessment — six-tier grid with directive
    4. Exploration stats — single summary line

Public API:
    render_end_of_life_report() — full block as a single string
    render_inventory_objects()  — FOREGROUND / BACKGROUND table, for testability
    render_terminal_summary()   — game-end key-value block

Import sovereignty: imports from library/ and stdlib only.
target_state and routing_directive are passed as objects (duck-typed) to
avoid import coupling with targeting/.
"""

from __future__ import annotations

from typing import List, Optional

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import SemanticLibrary


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

_DIV = "=" * 60

_ACTION_NAMES = {
    0: "RESET",
    1: "ACTION1", 2: "ACTION2", 3: "ACTION3", 4: "ACTION4",
    5: "ACTION5", 6: "ACTION6", 7: "ACTION7",
}

# Tier display names — padded to 18 chars for column alignment
_TIER_DISPLAY = {
    "WORLD_TYPE_EGO":  "World Type + Ego  ",
    "LIFE_COUNTER":    "Life Counter      ",
    "REACTIVE_CELLS":    "Reactive Cells    ",
    "LEVERS":    "Levers            ",
    "LEVER_TYPING":  "Lever Typing      ",
    "CAUSAL_LINKS":    "Causal Links      ",
}

# Roles that belong in FOREGROUND regardless of change_count
_FOREGROUND_ROLES = frozenset({
    LibraryRole.LEVER, LibraryRole.TARGET, LibraryRole.EGO,
})

# Column header for the inventory table
_COL_HEADER = " obj  class  cells   coord       Δ  tag·role              conf"


# ---------------------------------------------------------------------------
# Section 1 — Life boundary header
# ---------------------------------------------------------------------------

def _render_header(
    game_id: str,
    life: int,
    max_lives: Optional[int],
    actions_this_life: int,
    total_actions: int,
    levels_completed: int,
    state: str,
) -> str:
    life_display = f"Life: {life}/{max_lives}" if max_lives is not None else f"Life: {life}"
    return "\n".join([
        _DIV,
        "VIRELAI — END OF LIFE REPORT",
        (
            f"{life_display} | Game: {game_id} | "
            f"Actions: {actions_this_life} ({total_actions} total) | "
            f"Levels: {levels_completed}"
        ),
        f"State: {state}",
        _DIV,
    ])


# ---------------------------------------------------------------------------
# Section 2 — Semantic Inventory (FOREGROUND / BACKGROUND)
# ---------------------------------------------------------------------------

def _is_foreground(obj) -> bool:
    """Decide if an object belongs in the FOREGROUND tier.

    FOREGROUND = causal participants:
      - Objects with a causal role (LEVER, TARGET, EGO)
      - UNKNOWN objects that have changed (causal candidates)
    """
    if obj.role in _FOREGROUND_ROLES:
        return True
    # UNKNOWN but changed → causal candidate, show in FOREGROUND
    if obj.role == LibraryRole.UNKNOWN and obj.change_count > 0:
        return True
    return False


def _centroid_str(obj) -> str:
    """Compute centroid display string for the coord column.

    Returns '*' for objects larger than 500 cells (background centroid
    is meaningless). Returns '(r,c)' otherwise, rounded to nearest integer.
    """
    if obj.cell_count > 500:
        return "*"
    if not obj.cells:
        return "?"
    rows = [c[0] for c in obj.cells]
    cols = [c[1] for c in obj.cells]
    r = round(sum(rows) / len(rows))
    c = round(sum(cols) / len(cols))
    return f"({r},{c})"


def _obj_line(idx: int, obj) -> str:
    """Render one fixed-width object line."""
    # DD gap-1: the role column reads the captain's store (render_read), not
    # Store-B obj.role — the SEMANTIC INVENTORY now prints tag·role(·locality) and
    # a display-string confidence, killing the last split-brain render block.
    from virelai_v4.diagnostics.store_a_readout import render_read
    tag, role, locality, conf = render_read(obj)
    _r = role if role is not None else "UNCLASSIFIED"
    role_disp = f"{tag}·{_r}" + (f"·{locality}" if locality else "")
    role_str = role_disp.ljust(20)
    coord = _centroid_str(obj)
    line = (
        f"{idx:>4}"
        f"{obj.class_id:>7}"
        f"{obj.cell_count:>7}"
        f"{coord:>8}"
        f"{obj.change_count:>8}"
        f"  {role_str}"
        f"  {conf}"
    )
    if role == LibraryRole.COUNTER.value:
        # WO-C5-04: show rate and budget when data available, else candidate label
        if obj.lc_rate != 0.0 or obj.lc_budget_est >= 0:
            budget = f"~{obj.lc_budget_est}" if obj.lc_budget_est >= 0 else "unknown"
            line += f"  [COUNTER rate={obj.lc_rate:.1f}/act budget={budget}]"
        else:
            line += "  [counter candidate]"
    return line


def render_inventory_objects(library: SemanticLibrary) -> str:
    """Render the inventory table in canonical region_id order (WO-OCD-DISPLAY).

    Single flat list — no FOREGROUND/BACKGROUND split, no secondary sort by
    delta or change_count. Row position == canonical order from library
    construction (WO-OCD-CANONICAL: cell count ASC, class value ASC,
    emission order final tiebreaker). Roles are rendered inline as the
    'role' column in each row; they no longer determine section placement.
    """
    lines: List[str] = []
    lines.append(_COL_HEADER)
    if library.objects:
        # library.objects is already in canonical order via WO-OCD-CANONICAL;
        # preserve the dict insertion order — equivalently region_id ASC.
        for obj in library.objects.values():
            lines.append(_obj_line(obj.region_id, obj))
    else:
        lines.append("  (none)")
    lines.append("")

    # FUNCTIONS placeholder
    lines.append("FUNCTIONS: (not yet mapped)")
    lines.append("")

    # UNMAPPED count
    unknown_count = sum(
        1 for o in library.objects.values() if o.role == LibraryRole.UNKNOWN
    )
    lines.append(f"UNMAPPED: {unknown_count} objects")

    return "\n".join(lines)


def _render_inventory_section(library: SemanticLibrary) -> str:
    """Render the full ==> SEMANTIC INVENTORY <== section."""
    h = library.header
    n_objects = len(library.objects)
    n_classes = len({o.class_id for o in library.objects.values()}) if n_objects else 0

    lines: List[str] = [
        "=== SEMANTIC INVENTORY ===",
        f"{n_objects} objects across {n_classes} classes | Actions taken: {h.actions_taken}",
        f"World type: {h.world_type} | Ego: {h.ego_mode}",
        "",
        render_inventory_objects(library),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 3 — Tier Assessment
# ---------------------------------------------------------------------------

def _render_tier_assessment(target_state: object, routing_directive: object) -> str:
    """Render the --- TARGET ASSESSMENT --- section.

    target_state and routing_directive are duck-typed to avoid import
    coupling with targeting/. Accesses .tiers, .status.value, .gap, .focus.
    """
    lines: List[str] = ["--- TARGET ASSESSMENT ---"]
    for t in target_state.tiers:
        display     = _TIER_DISPLAY.get(t.name, t.name.ljust(18))
        status_tag  = f"[{t.status.value}]"
        description = t.gap if t.gap else "confirmed"
        lines.append(f"  Tier {t.tier}  {display} {status_tag:<7}  {description}")

    lines.append(f"  >>> DIRECTIVE: {routing_directive.focus}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section 4 — Exploration stats
# ---------------------------------------------------------------------------

def _render_exploration(library: SemanticLibrary) -> str:
    exp = library.exploration
    eff_pct = exp.efficiency * 100.0
    return (
        f"Exploration: {exp.unique_states} unique / "
        f"{exp.repeated_states} repeated (efficiency: {eff_pct:.1f}%)"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_end_of_life_report(
    game_id: str,
    life: int,
    max_lives: Optional[int],
    actions_this_life: int,
    total_actions: int,
    levels_completed: int,
    state: str,
    library: SemanticLibrary,
    field_card_text: str,
    target_state: object,
    routing_directive: object,
) -> str:
    """Render a complete end-of-life diagnostic block as a single string.

    V3.5-format output: plain = dividers, two-tier inventory, fixed columns,
    tier assessment with directive.

    field_card_text is accepted for signature compatibility but is no longer
    rendered as a separate section — the inventory table replaces it.

    target_state and routing_directive are typed as object to avoid import
    coupling — they are accessed via duck typing only.
    """
    parts: List[str] = []

    # Section 1 — Life boundary header
    parts.append(_render_header(
        game_id=game_id, life=life, max_lives=max_lives,
        actions_this_life=actions_this_life, total_actions=total_actions,
        levels_completed=levels_completed, state=state,
    ))
    parts.append("")

    # Section 2 — Semantic Inventory
    parts.append(_render_inventory_section(library))
    parts.append("")

    # Section 3 — Tier Assessment
    parts.append(_render_tier_assessment(target_state, routing_directive))
    parts.append("")

    # Section 4 — Exploration
    parts.append(_render_exploration(library))
    parts.append("")

    # Closing delimiter
    parts.append(_DIV)

    return "\n".join(parts)


def render_terminal_summary(
    game_id: str,
    terminal_cause: str,
    levels_completed: int,
    total_actions: int,
    won: bool,
) -> str:
    """Render the V3.5-style terminal summary block.

    Printed once at game end, after the final diagnostic block.
    """
    return "\n".join([
        f"  Game: {game_id}",
        f"  Terminal: {terminal_cause}",
        f"  Levels: {levels_completed}",
        f"  Actions: {total_actions}",
        f"  Win: {won}",
    ])
