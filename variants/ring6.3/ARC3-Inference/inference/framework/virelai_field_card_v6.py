"""virelai_field_card_v6.py -- v3.5's field card, fed by the v4 weave.

RING 6. A PORT, not a redesign. Origin: Universal_Solver_v3_5
`observer/field_card_renderer.py` (WO-FIELDCARD-01 / -MIG-02 / -03). Per R-C the
code is re-implemented in a new file rather than copied; what is NOT changed is
the thing that was proven: the seven questions, their headers, the vocabulary,
the ordinal labels, the word ceiling and its three compression passes, and every
fallback sentence.

WHAT CHANGED, AND ONLY THIS: the data source. v3.5 read `SemanticLibrary`. This
reads the WEAVE. Measured on ls20 2026-08-28: v4's library reported 178
"classified, 0 unknown" objects for a world holding 27 worldlines, because it
mints a region every time anything changes (19 -> 87 -> 156 -> 171 -> 178 inside
one run). LIST 3 / `infer_roles` is the right altitude and the roster's own
header says so (WO-ROSTER-SEVER-01).

EXTENSIONS TO v3.5's ONTOLOGY, declared as extensions rather than smuggled in:
  * GROUND and WALL are v4 FIELDS with no v3.5 equivalent -- "(the floor you
    walk on)" and "(a wall)". v3.5 had no world with a named floor.
  * REACTIVE and REACTIVE-DRIVEN are v4 ROLES v3.5 lacked.
  * `_conf` reads a SEAL, not a float. v3.5 had confidences; v4 has FIRM /
    PROVISIONAL. Mapping the seal onto a number and the number back onto a word
    would invent a quantity nobody measured, so the seal maps straight to
    v3.5's word.

WHAT v4 CANNOT FEED, named rather than faked:
  * `_shape` needs a bounding box. The weave's closing summary prints an NW
    anchor and a cell count only, so shape is UNAVAILABLE on the log path and
    `_desc` falls back to "object". The live path has the cells and can restore it.
  * `_pos` is computed from the NW anchor where v3.5 used a centroid.
  * §6's `lc_rate` / `lc_budget_est` do not exist in v4. The section reports the
    counter's measured growth and keeps v3.5's caveat that it may not be a budget.

FIREWALL: no colour name, no class id, no world name, no `###` id reaches the
output. Sizes and positions render as words, and the size buckets are VOCABULARY
-- nothing branches on a role, seal or verdict because of a size, and no role is
elected by size or position anywhere.

Pure. Stdlib only. Reads a dict, returns a FieldCard, stores nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_WORD_CEILING = 800
_LEVER_LABELS = ("A", "B", "C", "D")


# -- Vocabulary helpers -- ported verbatim in behaviour -----------------------

def _size(area: int) -> str:
    if area < 20:
        return "tiny"
    if area < 100:
        return "small"
    return "medium" if area < 500 else "large"


def _shape(obj: dict) -> Optional[str]:
    """v3.5's shape namer. Returns None when no bounding box was recorded --
    the log path has anchors only. A missing shape is an absence, not a guess."""
    bbox = obj.get("bbox")
    if not bbox:
        return None
    r0, c0, r1, c1 = bbox
    w, h = c1 - c0 + 1, r1 - r0 + 1
    if w <= 0 or h <= 0:
        return "point"
    ratio = max(w, h) / max(min(w, h), 1)
    if ratio > 4:
        return "thin horizontal bar" if w > h else "thin vertical bar"
    if ratio > 2:
        return "wide rectangle" if w > h else "tall rectangle"
    return "square" if 0.8 <= w / max(h, 1) <= 1.2 else "rectangle"


def _pos(obj: dict, gs: Tuple[int, int] = (64, 64)) -> str:
    """v3.5's arena-relative position, from the NW anchor rather than a centroid."""
    anchor = obj.get("anchor") if isinstance(obj, dict) else None
    if not anchor:
        return "arena"
    row, col = anchor
    rf, cf = row / max(gs[0], 1), col / max(gs[1], 1)
    v = "top" if rf < 0.25 else ("bottom" if rf > 0.75 else "middle")
    h = "left" if cf < 0.25 else ("right" if cf > 0.75 else "center")
    if v == "middle" and h == "center":
        return "center of the arena"
    if h == "center":
        return "%s portion of the arena" % v
    if v == "middle":
        return "%s side of the arena" % h
    return "%s-%s area" % (v, h)


def _conf(seal: Optional[str]) -> str:
    """v3.5's three words, keyed on v4's seal instead of v3.5's float."""
    if seal == "FIRM":
        return "verified"
    return "likely" if seal == "PROVISIONAL" else "suspected"


_ROLE_HINT = {
    "EGO": " (your body)",
    "LEVER": " (a lever)",
    "TARGET": " (reactive)",
    "COUNTER": " (life counter)",
    "STATIC": " (obstacle)",
    "SIGNAL": " (signal)",
    # -- v4 roles v3.5 did not have --
    "REACTIVE": " (reactive)",
    "REACTIVE-DRIVEN": " (driven by something else)",
    "INERT": " (inert)",
}

_FIELD_HINT = {
    "GROUND": " (the floor you walk on)",
    "WALL": " (a wall)",
}


def _role_hint(obj: dict) -> str:
    """A field outranks a role in the hint, because the floor and the walls are
    what a player needs named first. Both are reported; only one is hinted."""
    for f in ("GROUND", "WALL"):
        if f in (obj.get("fields") or ()):
            return _FIELD_HINT[f]
    return _ROLE_HINT.get(obj.get("role") or "", "")


def _desc(obj: dict, gs: Tuple[int, int]) -> str:
    nc = obj.get("num_components", 1)
    rh = _role_hint(obj)
    sz = _size(obj.get("cells", (0, 0))[1])
    if nc > 1:
        return "A cluster of %d %s pieces%s in the %s" % (nc, sz, rh, _pos(obj, gs))
    shape = _shape(obj) or "object"
    return "A %s %s%s in the %s" % (sz, shape, rh, _pos(obj, gs))


def _zone(obj: dict, gs: Tuple[int, int]) -> str:
    z = obj.get("zone")
    if z == "HUD":
        return "HUD"
    anchor = obj.get("anchor")
    if not anchor:
        return "arena"
    return "border" if anchor[0] == 0 or anchor[1] == 0 else "arena"


def _objs(d) -> List[dict]:
    return d.get("worldlines") or []


def _by_role(d, role) -> List[dict]:
    return [o for o in _objs(d) if o.get("role") == role]


def _by_field(d, field) -> List[dict]:
    return [o for o in _objs(d) if field in (o.get("fields") or ())]


# -- FieldCard data contract -- v3.5's, unchanged -----------------------------

@dataclass(frozen=True)
class FieldCard:
    """The solver's natural language self-description of a world. WO-FIELDCARD-01."""
    ego_section: str
    spatial_section: str
    lever_section: str
    reactive_section: str
    uncertainty_section: str
    budget_section: str
    discovery_section: str
    game_id: str
    world_type: str
    render_moment: str
    word_count: int

    def __str__(self) -> str:
        _HEADERS = [
            ("§1 — What Am I?", self.ego_section),
            ("§2 — What Do I See?", self.spatial_section),
            ("§3 — What Can I Do?", self.lever_section),
            ("§4 — What Changes When I Act?", self.reactive_section),
            ("§5 — What Don't I Know?", self.uncertainty_section),
            ("§6 — How Much Time Do I Have?", self.budget_section),
            ("§7 — What Have I Tried?", self.discovery_section),
        ]
        lines = ["=== FIELD CARD — %s ===" % self.game_id, ""]
        for hdr, body in _HEADERS:
            lines += [hdr, body, ""]
        lines.append("[%d words | %s]" % (self.word_count, self.render_moment))
        return "\n".join(lines)


# -- 1 Ego --------------------------------------------------------------------

def _render_ego_section(d: dict) -> str:
    mode = d.get("ego_mode") or "UNKNOWN"
    if mode == "UNKNOWN":
        return "Ego mode has not been determined yet."
    ego = d.get("ego") or {}
    parts: List[str] = []
    if mode == "GOD_MODE":
        parts.append("You are in God Mode — you can click anywhere on the grid.")
    elif mode == "EMBODIED":
        model = ego.get("model") or {}
        strides = {abs(v[0]) or abs(v[1]) for v in model.values()} or set()
        stride = strides.pop() if len(strides) == 1 else None
        stride_str = " by %d pixels per step" % stride if stride else ""
        area = ego.get("footprint")
        tones = len(ego.get("sealed") or ())
        if area:
            body = ("You have a body — a %s cluster of pixels that moves%s when "
                    "you press directional actions." % (_size(area), stride_str))
            if tones > 1:
                body += (" It is made of %d kinds of pixel that were measured moving "
                         "together; treat them as one thing." % tones)
            parts.append(body)
        else:
            parts.append("You have a body that moves%s when you press directional "
                         "actions." % stride_str)
    elif mode == "COMBINATORIAL":
        parts.append("You can both move a body and click on the grid — a hybrid "
                     "interaction mode.")
    else:
        parts.append("Your interaction mode is not yet determined.")

    seal = d.get("ego_seal")
    if seal == "FIRM":
        parts.append("This assessment has high confidence.")
    elif seal == "PROVISIONAL":
        parts.append("This assessment has moderate confidence.")
    else:
        parts.append("This assessment is uncertain — more evidence is needed.")

    # v3.5's NOOP sentence, split in two because v4 distinguishes two absences.
    model = (d.get("ego") or {}).get("model") or {}
    observed = set((d.get("ego") or {}).get("observed") or ())
    unsettled = sorted(a for a in observed if a not in model)
    silent = sorted(a for a in (d.get("roster") or ()) if a not in model
                    and a not in observed)
    if silent:
        one = len(silent) == 1
        parts.append("Action%s %s %s available but produced no observable effect "
                     "during probing — %s may require an undiscovered precondition."
                     % ("" if one else "s", " and ".join(str(a) for a in silent),
                        "is" if one else "are", "it" if one else "they"))
    if unsettled:
        one = len(unsettled) == 1
        parts.append("Action%s %s did move you, but not the same way each time, so no "
                     "single effect can be stated for %s — live and unsettled, "
                     "not dead."
                     % ("" if one else "s", " and ".join(str(a) for a in unsettled),
                        "it" if one else "them"))
    return " ".join(parts)


# -- 2 Spatial ----------------------------------------------------------------

def _render_spatial_section(d: dict) -> str:
    objs = _objs(d)
    if not objs:
        return "Spatial layout has not been analyzed yet."
    gs = d.get("grid") or (64, 64)
    parts = ["The grid contains %d distinct objects." % len(objs)]

    # The floor and the walls are named FIRST -- they are the terrain a player
    # stands on and cannot pass, and v3.5 had no world that needed them said.
    for o in _by_field(d, "GROUND"):
        s = "A %s region in the %s is the floor you walk on." % (
            _size(o.get("cells", (0, 0))[1]), _pos(o, gs))
        note = d.get("ground_note")
        if note:
            s += (" It deformed on %s separate steps and every one of those was your "
                  "own body passing through it — nothing else moved it." % note)
        parts.append(s)
    walls = _by_field(d, "WALL")
    if walls:
        where = " and ".join("a %s one in the %s" % (_size(w.get("cells", (0, 0))[1]),
                                                     _pos(w, gs)) for w in walls[:3])
        cov = max((w.get("cov") or 0) for w in walls)
        parts.append("%d %s a wall you cannot pass — %s. %s changed in any of %d "
                     "observations."
                     % (len(walls), "region is" if len(walls) == 1 else "regions are each",
                        where, "It never" if len(walls) == 1 else "Neither" if len(walls) == 2
                        else "None of them", cov))

    named = [o for o in objs if o.get("role") or o.get("fields")]
    rest = [o for o in named if not (set(o.get("fields") or ()) & {"GROUND", "WALL"})]
    groups: Dict[Any, list] = {}
    for o in rest:
        groups.setdefault((o.get("role"), _size(o.get("cells", (0, 0))[1])), []).append(o)
    shown = 0
    for _key, group in groups.items():
        if shown >= 6:
            break
        if len(group) == 1:
            parts.append(_desc(group[0], gs) + ".")
        else:
            rep = group[0]
            parts.append("%d %s objects of the same type%s spread across the arena."
                         % (len(group), _size(rep.get("cells", (0, 0))[1]),
                            _role_hint(rep)))
        shown += 1

    hud = [o for o in objs if _zone(o, gs) == "HUD"]
    if hud:
        parts.append("One object sits in the HUD area at the %s." % _pos(hud[0], gs)
                     if len(hud) == 1 else
                     "%d objects are in the HUD display area." % len(hud))
    border = [o for o in objs if _zone(o, gs) == "border"]
    if border:
        parts.append("%d object%s sit%s against the grid border."
                     % (len(border), "" if len(border) == 1 else "s",
                        "s" if len(border) == 1 else ""))
    bare = [o for o in objs if not o.get("role") and not o.get("fields")]
    if bare:
        parts.append("%d object%s have earned no role from anything observed so far."
                     % (len(bare), "" if len(bare) == 1 else "s"))
    return " ".join(parts)


# -- 3 Levers -----------------------------------------------------------------

def _render_lever_section(d: dict) -> str:
    levers = _by_role(d, "LEVER")
    if not levers:
        return "No levers have been discovered yet."
    gs = d.get("grid") or (64, 64)
    walkable = (d.get("ego_mode") == "EMBODIED")
    verb = "Stepping on" if walkable else "Clicking"
    n = len(levers)
    parts: List[str] = []
    if walkable:
        parts.append("There is one button you can step on." if n == 1
                     else "There are %d buttons you can step on." % n)
    else:
        parts.append("There is one clickable button." if n == 1
                     else "There are %d clickable buttons." % n)
    multi = n > 1
    for i, act in enumerate(levers[:4]):
        label = "Lever %s: " % _LEVER_LABELS[i] if multi else ""
        p = _pos(act, gs)
        if "GROUND" in (act.get("fields") or ()):
            parts.append("%s%s a %s lever in the %s is the same act as walking on it "
                         "— the floor and the lever are one object, responding on "
                         "%d observations."
                         % (label, verb, _conf(act.get("seal")), p, act.get("cov") or 0))
        else:
            parts.append("%s%s a %s lever in the %s changed something on %d "
                         "observations." % (label, verb, _conf(act.get("seal")), p,
                                            act.get("cov") or 0))
        effects = act.get("effects") or []
        for effect in effects[:3]:
            target = "a %s region in the %s" % (
                _size(int(effect.get("cells") or 0)),
                _pos(effect, gs),
            )
            mechanism = str(effect.get("mechanism") or "UNKNOWN").upper()
            if mechanism == "TOGGLE":
                law = "alternated between previously observed states"
            elif mechanism == "CYCLE":
                law = "returned on a period longer than two"
            elif mechanism == "DIRECTIONAL":
                law = "changed monotonically in one direction"
            elif mechanism == "SATURATED":
                law = "stopped changing after repeated activation"
            elif mechanism == "ONE_SHOT":
                law = "changed once and did not repeat"
            else:
                law = "changed, but its response law remains unknown"
            parts.append("Its attributed affected region is %s; that region %s."
                         % (target, law))
    return " ".join(parts)


# -- 4 Reactive ---------------------------------------------------------------

def _render_reactive_section(d: dict) -> str:
    objs = _objs(d)
    if not objs:
        return "No reactive regions have been identified yet."
    gs = d.get("grid") or (64, 64)
    reactive = _by_role(d, "REACTIVE") + _by_role(d, "TARGET")
    driven = _by_role(d, "REACTIVE-DRIVEN")
    if not reactive and not driven:
        return "No reactive regions have been identified yet."
    parts: List[str] = []
    for obj in reactive[:3]:
        parts.append("A %s region in the %s responds, but what drives it is not "
                     "established." % (_size(obj.get("cells", (0, 0))[1]), _pos(obj, gs)))
    if driven:
        one = len(driven) == 1
        parts.append("%d region%s change%s only when something else acts on %s; %s "
                     "never been seen to act first."
                     % (len(driven), "" if one else "s", "s" if one else "",
                        "it" if one else "them", "it has" if one else "they have"))
    return " ".join(parts)


# -- 5 Uncertainty ------------------------------------------------------------

def _render_uncertainty_section(d: dict) -> str:
    objs = _objs(d)
    if not objs:
        observed = d.get("observed_transition") or {}
        if observed:
            return (
                "The environment itself reported advancement from level %s to level %s "
                "after %s. This is an observed winning transition, not a guessed goal. "
                "No object model was retained for that observation."
                % (observed.get("from_level", "?"), observed.get("to_level", "?"),
                   observed.get("action", "an action"))
            )
        return "Uncertainty assessment is not available yet."
    unk = [o for o in objs if not o.get("role") and not o.get("fields")]
    low = [o for o in objs if o.get("role") and o.get("seal") == "PROVISIONAL"]
    multi = [o for o in objs if o.get("multi")]
    parts: List[str] = []
    if unk:
        parts.append("%d object%s unknown purpose."
                     % (len(unk), " has" if len(unk) == 1 else "s have"))
    if low:
        parts.append("%d object%s tentative classifications that have not been "
                     "verified." % (len(low), " has" if len(low) == 1 else "s have"))
    if multi:
        parts.append("%d record%s flagged as a possibly split identity — one "
                     "thing may be recorded as several."
                     % (len(multi), " is" if len(multi) == 1 else "s are"))
    # same-anchor collision: measured, reported, never silently merged
    seen: Dict[Any, list] = {}
    for o in objs:
        if o.get("anchor"):
            seen.setdefault(o["anchor"], []).append(o)
    for anchor, group in sorted(seen.items()):
        if len(group) > 1:
            roles = sorted({(o.get("role") or "no role") for o in group})
            parts.append("%d separate records sit at one spot in the %s carrying %s "
                         "(%s) — likely one thing recorded several ways."
                         % (len(group), _pos(group[0], d.get("grid") or (64, 64)),
                            "%d different verdicts" % len(roles) if len(roles) > 1
                            else "one verdict",
                            ", ".join(r.lower() for r in roles)))
    known = [o for o in objs if o.get("role") or o.get("fields")]
    parts.append("Coverage: approximately %d%% of objects have confirmed roles."
                 % int(100 * len(known) / max(len(objs), 1)))
    observed = d.get("observed_transition") or {}
    if observed:
        parts.append(
            "The environment itself reported advancement from level %s to level %s "
            "after %s. This is an observed winning transition, not a guessed goal."
            % (observed.get("from_level", "?"), observed.get("to_level", "?"),
               observed.get("action", "an action"))
        )
    elif not d.get("win_seen"):
        parts.append("No state has ever been observed as a win. Nothing here is known "
                     "to end the level.")
    return " ".join(parts) if parts else \
        "All objects have been classified with reasonable confidence."


# -- 6 Budget -----------------------------------------------------------------

def _render_budget_section(d: dict) -> str:
    counters = _by_role(d, "COUNTER")
    if not counters:
        return ("No life counter has been detected. The budget may be unlimited or "
                "enforced by the server.")
    gs = d.get("grid") or (64, 64)
    obj = counters[0]
    lo, hi = obj.get("cells", (0, 0))
    ticks = obj.get("ticks") or 0
    parts = ["A %s counter sits in the %s." % (_conf(obj.get("seal")), _pos(obj, gs))]
    if ticks and hi > lo:
        parts.append("It grew from %d pixels to %d over %d ticks — about %.1f "
                     "pixels a tick." % (lo, hi, ticks, (hi - lo) / float(ticks)))
    rv, cov = obj.get("revisit"), obj.get("cov") or 0
    if rv is not None and cov:
        parts.append("It goes one way: on only %d of its %d observations did it return "
                     "to a state it had already held." % (rv, cov))
    parts.append("No depletion rate and no remaining budget were computed, so how many "
                 "actions this leaves you is not known — and whether it is a "
                 "budget at all, rather than part of the world, has not been "
                 "established.")
    if len(counters) > 1:
        parts.append("%d counters were sealed; check whether they are one object "
                     "recorded more than once." % len(counters))
    return " ".join(parts)


# -- 7 Discovery --------------------------------------------------------------

def _render_discovery_section(d: dict) -> str:
    f = d.get("frontier") or {}
    if not f:
        return "Discovery summary is not available yet."
    gs = d.get("grid") or (64, 64)
    parts = ["%d objects are queued as targets: %d touched, %d never attempted, %d "
             "queued but not reached, %d ruled unreachable — and that last count "
             "was measured, not assumed."
             % (f.get("queued", 0), f.get("touched", 0), f.get("never", 0),
                f.get("not_reached", 0), f.get("unreachable", 0))]
    targets = [t for t in (f.get("targets") or ())
               if t.get("state") == "NEVER ATTEMPTED"]
    if not targets:
        parts.append("Nothing is currently listed as untried.")
        return " ".join(parts)
    seen, rows = set(), []
    for t in sorted(targets, key=lambda t: (t.get("cells", 0), t.get("anchor") or ())):
        key = (t.get("anchor"), t.get("cells"))
        if key in seen:
            continue
        seen.add(key)
        rows.append("target %s, a %s object in the %s"
                    % (_LEVER_LABELS[len(rows)] if len(rows) < len(_LEVER_LABELS)
                       else str(len(rows) + 1), _size(t.get("cells", 0)), _pos(t, gs)))
        if len(rows) >= 4:
            break
    parts.append("Smallest untried first: " + "; ".join(rows) + ".")
    return " ".join(parts)


# -- Word ceiling -- v3.5's three passes, unchanged ---------------------------

def _compress(sections: Dict[str, str]) -> Dict[str, str]:
    """Compress to stay under the ceiling. Never compress ego/lever/budget."""
    total = sum(len(s.split()) for s in sections.values())
    if total <= _WORD_CEILING:
        return sections
    original = total
    r = dict(sections)
    sents = r["spatial"].split(". ")
    if len(sents) > 3:
        r["spatial"] = ". ".join([sents[0]] + sents[-2:])
    total = sum(len(s.split()) for s in r.values())
    if total > _WORD_CEILING:
        sents = r["reactive"].split(". ")
        if len(sents) > 3:
            r["reactive"] = ". ".join(sents[:2]) + ". " + sents[-1]
        total = sum(len(s.split()) for s in r.values())
    if total > _WORD_CEILING:
        sents = r["uncertainty"].split(". ")
        if len(sents) > 1:
            r["uncertainty"] = sents[0] + "."
    final = sum(len(s.split()) for s in r.values())
    if final < original:
        print("[FIELDCARD-TRIM] trimmed from %d to %d words" % (original, final))
    return r


# -- Public API ---------------------------------------------------------------

_FALLBACK = dict(
    ego="Ego mode has not been determined yet.",
    spatial="Spatial layout has not been analyzed yet.",
    lever="No levers have been discovered yet.",
    reactive="No reactive regions have been identified yet.",
    uncertainty="Uncertainty assessment is not available yet.",
    budget="No life counter has been detected. The budget may be unlimited or "
           "enforced by the server.",
    discovery="Discovery summary is not available yet.",
)

_RENDERERS = (
    ("ego", _render_ego_section),
    ("spatial", _render_spatial_section),
    ("lever", _render_lever_section),
    ("reactive", _render_reactive_section),
    ("uncertainty", _render_uncertainty_section),
    ("budget", _render_budget_section),
    ("discovery", _render_discovery_section),
)


def render_field_card(d: dict, game_id: str = "",
                      render_moment: str = "opening_handover") -> FieldCard:
    """Pure function: weave-derived dict in, FieldCard out.

    Every section falls back to v3.5's own sentence rather than rendering blank,
    and a fault in one section costs that section and never the card.
    """
    sec = {}
    for key, fn in _RENDERERS:
        try:
            sec[key] = fn(d) or _FALLBACK[key]
        except Exception:
            sec[key] = _FALLBACK[key]
    sec = _compress(sec)
    return FieldCard(
        ego_section=sec["ego"], spatial_section=sec["spatial"],
        lever_section=sec["lever"], reactive_section=sec["reactive"],
        uncertainty_section=sec["uncertainty"], budget_section=sec["budget"],
        discovery_section=sec["discovery"],
        game_id=game_id or d.get("game_id", ""),
        world_type=d.get("world_type", ""), render_moment=render_moment,
        word_count=sum(len(s.split()) for s in sec.values()),
    )


def render_card(d: dict) -> str:
    """String form, for callers that want the text and not the dataclass."""
    return str(render_field_card(d, d.get("game_id", "")))


def render_probe_report(report: dict, game_id: str = "") -> str:
    """Render a bounded multi-life, multi-level Captain handoff.

    Each snapshot remains a normal seven-section V3.5 field card.  The wrapper
    supplies lifecycle provenance that a single final V4 context cannot retain
    after level and life resets.  No snapshots are merged: two observations are
    shown as two observations rather than silently reconciled into one claim.
    """
    snapshots = list(report.get("snapshots") or ())
    lines = [
        "=== CAPTAIN PROBE REPORT — %s ===" % (game_id or report.get("game_id", "")),
        "",
        ("The Captain acted before the model: %d actions, %d lives consumed. "
         "Stop reason: %s. The current live frame is the state after this probe phase."
         % (int(report.get("actions") or 0), int(report.get("lives") or 0),
            report.get("stop_reason") or "UNKNOWN")),
    ]
    fault = report.get("fault")
    if fault:
        lines.append("The probe ended with a contained %s; missing sections are honest gaps."
                     % fault)
    if not snapshots:
        snapshots = [{"reason": "fallback", "level": 1, "life": 1, "card": {}}]
    for index, snapshot in enumerate(snapshots, start=1):
        reason = str(snapshot.get("reason") or "snapshot").replace("_", " ")
        lines.extend([
            "",
            "--- Probe snapshot %d · level %s · life %s · %s ---"
            % (index, snapshot.get("level", "?"), snapshot.get("life", "?"), reason),
            str(render_field_card(
                snapshot.get("card") or {},
                game_id=game_id or report.get("game_id", ""),
                render_moment="captain_%s" % reason.replace(" ", "_"),
            )),
        ])
    lines.extend([
        "",
        "=== END CAPTAIN PROBE REPORT ===",
        "Use the report as evidence. Preserve its stated uncertainties and test any "
        "claim whose prediction fails on the current frame.",
    ])
    return "\n".join(lines)
