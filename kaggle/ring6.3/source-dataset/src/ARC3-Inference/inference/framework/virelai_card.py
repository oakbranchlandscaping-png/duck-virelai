"""Ring 4 -- the field card: a natural-language projection of the library.

TRANSCRIBED SHAPE, cited per R-C. Origin buys attention, never trust:

  virelai_v4/library/field_card.py (617 lines) -- "The field card is a VIEW, not data.
  It reads the library. It does not modify it. It produces a string. The string is not
  stored in the library." Carried: the ordered sections, omit-when-empty for optional
  sections, GAPS always present, counts in section headers, observation counts attached
  to causal claims, canonical ordering, and _render_unknowns' refusal to group by
  anything that is not a classification input.
  NOT carried: its confidence floats (banned epistemology), its efficiency percentage,
  and _render_background / _render_captain_target / _render_plan_status, which have no
  observed basis here -- each is a GAPS line instead.

  QSPI_v1.0.md Sec.3 (the World Intelligence Brief) -- the firewall on a bounded brief:
  "No raw grid. No pixel coordinates. No SDK internals. Everything must be frame-derived."
  Its Sec.G friction snapshot (goal entropy, mean Fpx/Fobj/Ftopo) is REFUSED: confidence
  scalars. Port the brief, not the ratchet.

  FRICTION-004 -- "Name the consumer before building the producer." The consumer is the
  model, and it must CALL this. A card that renders and is never read is FRICTION-004
  one layer up.

THE LAW THIS RENDERER OBEYS (Director, 2026-08-27, STRATEGY.md Sec.6 constraint 5):
THE CARD'S INPUT IS OBSERVED, NOT CONCLUDED. Every line states what the record shows
and what would falsify it. No line says "is YOU". No line says "never doubt". The
reader concludes.

EXECUTION: this module's source is spliced into the sandbox bootstrap by
python_tool_sandbox.py (mirroring __SEGMENTATION_SOURCE__) and runs INSIDE the sandbox
subprocess as a pure function over the `virelai` dict already shipped there. It adds
nothing to the payload and it never touches the ledger: unread means unrendered.
Stdlib-free by construction -- the sandbox restricts builtins.
"""


def _bbox(b):
    if not b or len(b) < 4:
        return "unknown position"
    return "rows %s-%s x cols %s-%s" % (b[0], b[1], b[2], b[3])


def _situation(s):
    wt = s.get("world_type") or "UNDERIVED"
    roster = s.get("roster") or []
    lines = ["=== SITUATION ==="]
    if roster:
        lines.append("  %s world, derived from the action roster: %s"
                     % (wt, ", ".join([str(r) for r in roster])))
    else:
        lines.append("  world type UNDERIVED -- no action roster observed yet")
    lvl = s.get("level")
    bits = []
    if lvl is not None:
        bits.append("level %s" % lvl)
    bits.append("%s states walked" % s.get("states", 0))
    bits.append("%s moves recorded" % s.get("moves", 0))
    bits.append("%s resets" % s.get("resets", 0))
    lines.append("  " + " | ".join(bits))
    here = s.get("here")
    if here:
        node = (s.get("nodes") or {}).get(here) or {}
        lines.append("  you are at state %s (arrived %s time(s))"
                     % (str(here)[:6], node.get("arrivals", 0)))
    return "\n".join(lines)


def _objects(s):
    egos = s.get("ego") or []
    ctrs = s.get("counter") or []
    drains = s.get("drains") or []
    levers = s.get("levers") or []
    sealed = len(egos) + len(ctrs) + len(drains) + len(levers)
    if sealed == 0:
        return None
    wl = s.get("worldlines", 0)
    out = ["=== OBJECTS (%s sealed, %s worldlines threaded) ===" % (sealed, wl)]

    for e in sorted(egos, key=lambda x: (x.get("cells", 0), str(x.get("class")))):
        out.append("  EGO-SEALED  %s-cell class-%s at %s"
                   % (e.get("cells", "?"), e.get("class"), _bbox(e.get("bbox"))))
        obs = e.get("observed") or {}
        if obs:
            parts = []
            for label in sorted(obs):
                for d in obs[label]:
                    parts.append("%s->(%s,%s)" % (label, d[0], d[1]))
            out.append("      observed moving: " + "; ".join(parts))
        ms = e.get("moves_seen")
        if ms is not None:
            out.append("      moved on %s recorded presses" % ms)
        out.append("      That is what the record shows moved with WHICH press. It is a "
                   "reading, not a guarantee -- falsified if another shape shows the same "
                   "signature, or if this one moves when you did not press.")

    for c in sorted(ctrs, key=lambda x: x.get("cells", 0)):
        out.append("  COUNTER-SEALED  %s-cell region at %s"
                   % (c.get("cells", "?"), _bbox(c.get("bbox"))))
        out.append("      observed: changed on %s presses under %s distinct action labels, "
                   "%s cells per press"
                   % (c.get("presses", "?"), c.get("labels", "?"),
                      c.get("cells_per_press", "?")))
        out.append("      It moved on THAT any action occurred, not on WHICH. Its cells are "
                   "excluded from state identity so the map can converge. Falsified if a "
                   "press leaves it unchanged.")

    for d in sorted(drains, key=lambda x: x.get("cells", 0)):
        out.append("  DRAIN-SEALED  %s-cell region at %s"
                   % (d.get("cells", "?"), _bbox(d.get("bbox"))))
        out.append("      observed changing when the sealed ego moved, and not otherwise. "
                   "Falsified by a change with no ego movement.")

    for l in sorted(levers, key=lambda x: -(x.get("effect_cells") or 0)):
        out.append("  LEVER-WITNESSED  %s" % l.get("desc", "object"))
        out.append("      observed: clicking it changed %s cells elsewhere, on %s witness(es)."
                   % (l.get("effect_cells", "?"), l.get("witness", "?")))
        out.append("      One witness proves a lever; silence afterwards does not retract it. "
                   "But one witness cannot separate a lever from a coincidence -- falsified, "
                   "or confirmed, by clicking it again and seeing whether the effect repeats.")
    return "\n".join(out)


def _unknowns(s):
    wl = s.get("worldlines", 0)
    sealed = len(s.get("ego") or []) + len(s.get("drains") or [])
    rest = wl - sealed
    if wl == 0 or rest <= 0:
        return None
    return ("=== UNKNOWNS (%s remaining) ===\n"
            "  %s threaded worldlines carry no sealed role. Nothing is claimed about them."
            % (rest, rest))


def _actions(s):
    here = s.get("here")
    nodes = s.get("nodes") or {}
    node = nodes.get(here) if here else None
    acts = (node or {}).get("actions") or {}
    untried = s.get("untried_here") or []
    if not acts and not untried:
        return None
    out = ["=== ACTIONS AT THIS STATE ==="]
    for label in sorted(acts):
        r = acts[label]
        out.append("  %-8s tried %s, changed the board %s, reached %s distinct outcome(s)"
                   % (label, r.get("tries", 0), r.get("changes", 0), r.get("outcomes", 0)))
    if untried:
        out.append("  never tried here: " + ", ".join([str(u) for u in untried]))
    return "\n".join(out)


def _exploration(s):
    if not s.get("states"):
        return None
    nodes = s.get("nodes") or {}
    revisits = 0
    for k in nodes:
        a = nodes[k].get("arrivals", 0)
        if a > 1:
            revisits += a - 1
    return ("=== EXPLORATION ===\n"
            "  %s states walked, %s moves recorded, %s revisits, %s resets\n"
            "  Every state in this list has been visited and did not win. The win, if this "
            "level has one, is reached by an action not yet taken."
            % (s.get("states", 0), s.get("moves", 0), revisits, s.get("resets", 0)))


def _causal(s):
    levers = s.get("levers") or []
    if not levers:
        return None
    out = ["=== CAUSAL MAP ==="]
    for l in sorted(levers, key=lambda x: -(x.get("effect_cells") or 0)):
        out.append("  %s -> %s cells changed elsewhere (%s observation(s))"
                   % (l.get("desc", "object"), l.get("effect_cells", "?"),
                      l.get("witness", "?")))
    return "\n".join(out)


def _gaps(s):
    gaps = []
    if not s.get("world_type"):
        gaps.append("world type UNDERIVED -- no action roster observed yet")
    if not (s.get("ego") or []):
        wt = s.get("world_type")
        if wt in ("NAV", "HYBRID"):
            gaps.append("no ego sealed -- nothing has yet moved under two distinct "
                        "directional labels with two distinct bearings")
        elif wt == "CLICK":
            gaps.append("no ego expected -- CLICK world, your clicks are the hand")
    if not (s.get("counter") or []):
        gaps.append("no counter sealed -- nothing observed changing on THAT any action "
                    "occurred rather than on WHICH")
    if not (s.get("levers") or []):
        gaps.append("no lever witnessed -- no click has yet been followed by a change "
                    "elsewhere")
    cand = s.get("ego_candidates") or 0
    ego_n = len(s.get("ego") or [])
    if cand > ego_n:
        gaps.append("%s worldline(s) moved under two or more buttons but did not cross a "
                    "stationary partner -- NOT sealed as ego. Something the ego pushes is "
                    "a lever, not a self." % (cand - ego_n))
    wl = s.get("worldlines", 0)
    sealed = len(s.get("ego") or []) + len(s.get("drains") or [])
    if wl - sealed > 0:
        gaps.append("%s threaded worldlines carry no sealed role" % (wl - sealed))
    roster = s.get("roster") or []
    if roster:
        tried = set()
        for k in (s.get("nodes") or {}):
            for lbl in ((s.get("nodes") or {})[k].get("actions") or {}):
                tried.add(lbl)
        never = [r for r in roster
                 if str(r).upper() not in tried and str(r).upper() != "RESET"]
        if never:
            gaps.append("%s roster action(s) never tried anywhere: %s"
                        % (len(never), ", ".join([str(n) for n in never])))
    gaps.append("terrain unmeasured -- no ground or wall labels exist, so no claim is "
                "made about what is reachable")
    gaps.append("destructibility unmeasured -- appearance and disappearance are computed "
                "per edge and not retained, so nothing is claimed about what can be removed")
    gaps.append("no win has been observed in this game yet, so no win condition is described")
    lines = ["=== GAPS (what the record does NOT show) ==="]
    for g in gaps:
        lines.append("  - " + g)
    return "\n".join(lines)


def render_card(snapshot):
    """The field card. Pure function of the snapshot. Returns a string."""
    if not isinstance(snapshot, dict) or not snapshot:
        return ("=== SITUATION ===\n  The library is empty -- nothing has been recorded "
                "yet.\n\n=== GAPS (what the record does NOT show) ===\n"
                "  - everything: no action has been recorded in this game")
    parts = [_situation(snapshot), ""]
    for fn in (_objects, _unknowns, _actions, _exploration, _causal):
        r = fn(snapshot)
        if r is not None:
            parts.append(r)
            parts.append("")
    parts.append(_gaps(snapshot))
    return "\n".join(parts)
