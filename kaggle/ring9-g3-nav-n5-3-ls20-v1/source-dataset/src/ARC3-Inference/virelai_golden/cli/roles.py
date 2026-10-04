"""golden.cli.roles — the role commands: ego (G1-01/02), states (G2-02), ground (G3-01), wall (G3-01b),
lever (G3-02). Split from `golden/cli.py` at G3-02 (the 400-line limit, ADR-0006); bodies unchanged."""
from __future__ import annotations

import argparse

from virelai_golden.cli.rung0 import _woven


def _ego(args: argparse.Namespace) -> int:
    """EGO(BODY) over one life of a recording — G1-01's exit observable."""
    from virelai_golden.roles.ego_body import infer_ego_body

    from virelai_golden.roles.ego_pointer import deltas_by_owner, infer_ego_pointer

    from virelai_golden.roles.infer import infer_roles

    record, life, window, wls, _ = _woven(args.recording, args.life)
    read = infer_roles(record, window, wls)   # the ladder's boundaries (life ∪ in-life respawn, G3-03)
    verdicts, maps = infer_ego_body(record, window, wls, read.boundaries)
    pointer, pread = infer_ego_pointer(record, window, wls)
    print(f"########## EGO · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} · "
          f"actions {record.action_channel} ##########")
    if pointer is not None:
        print("  EGO(POINTER) · god mode · no footprint")
        print(f"      basis: {pointer.basis}")
        print(f"      parallax: {pointer.parallax}")
        for own, n, lo, hi in deltas_by_owner(pointer):
            span = f"{lo}" if lo == hi else f"{lo}–{hi}"
            print(f"      · pressed {own} ×{n}: {span} cell(s) changed, unattributed")
    elif pread.presses:
        print(f"  no EGO(POINTER): {len(pread.presses)} targeted press(es), none produced a delta")
    if not verdicts and pointer is None:
        untargeted = sum(1 for n in record.nodes if n.action is not None and n.action[1] is None
                         and n.action[0] != 0 and window[0].node <= n.index <= window[-1].node)
        why = ("the record is action-blind" if record.action_channel.startswith("BLIND") else
               "no non-site-selecting press in this window (every press carried a target cell): "
               "BODY is unaskable here; the pointer ego is G1-02's" if untargeted == 0 else
               f"{untargeted} untargeted press(es) moved no worldline")
        print(f"  no worldline sealed EGO(BODY): {why}")
    for v in verdicts:
        ids = "+".join(f"###{m:03d}" for m in v.members)
        print(f"  EGO({v.kind}) · {ids}")
        print(f"      basis: {v.basis}")
        print(f"      parallax: {v.parallax}")
    print(f"  bearing maps: {len(maps)} worldline(s) observed under some button · boundaries disregarded at nodes "
          f"{sorted(read.boundaries) or 'none'} (life openings and in-life respawns on a counter event)")
    print("########## END EGO ##########")
    return 0


def _ground(args: argparse.Namespace) -> int:
    """GROUND over one life — G3-01's exit observable: the fold read off the sealed ego (R-M)."""
    from virelai_golden.render.roster import collapse
    from virelai_golden.roles.infer import infer_roles

    record, life, window, wls, _ = _woven(args.recording, args.life)
    read = infer_roles(record, window, wls)
    g = read.ground
    ego = sorted(m for v in read.bodies for m in v.members)
    print(f"########## GROUND · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} · "
          f"actions {record.action_channel} ##########")
    print(f"  ego: {'+'.join(f'###{m:03d}' for m in ego) or 'none sealed'} · {g.typed}")
    folded = sum(len(v.members) - 1 for v in g.verdicts)
    print(f"  LIST 2 carries Y={len(wls)} worldline(s); the fold reads Y={len(wls) - folded}")
    by_id = {w.id: w for w in wls}
    for v in g.verdicts:
        print(f"  GROUND · {'+'.join(f'###{m:03d}' for m in v.members)}")
        print(f"      basis: {v.basis}")
        print(f"      parallax: {v.parallax}")
        entries = collapse((n, r) for m in v.members for n, r in by_id[m].steps)
        app = sum(len(e.trail) for e in entries)
        print(f"      as one row: {len(entries)} visual object(s) · {app} appearance(s) · "
              f"{min(len(e.cells) for e in entries)}–{max(len(e.cells) for e in entries)} cells")
        for m in v.members:
            w = by_id[m]
            print(f"      ▪ ###{m:03d} · {len(w.steps)} step(s) · nodes {w.first_node}–{w.last_node}")
    print("########## END GROUND ##########")
    return 0


def _wall(args: argparse.Namespace) -> int:
    """WALL over one life — G3-01b's exit observable: what refused the ego, and what did not count."""
    from virelai_golden.roles.infer import infer_roles

    record, life, window, wls, _ = _woven(args.recording, args.life)
    read = infer_roles(record, window, wls)
    w = read.walls
    print(f"########## WALL · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} · "
          f"actions {record.action_channel} ##########")
    print(f"  {w.typed}")
    for r in w.refusals:
        land = ("unaskable: no agreed bearing" if r.bearing is None else
                f"bearing ({r.bearing[0]:+d},{r.bearing[1]:+d}) · landing on "
                + (", ".join(f"###{k:03d}×{n}" for k, n in sorted(r.holders.items())) or "nothing on the board"))
        print(f"  refused · ###{r.member:03d} · press {r.left}→{r.right} · A{r.action} · {land}")
    for wid, wv in sorted(w.verdicts.items()):
        print(f"  WALL · ###{wid:03d}")
        print(f"      basis: {wv.basis}")
        print(f"      parallax: {wv.parallax}")
    if w.changing_blockers:
        print("  changing blocker(s), not WALL: " + ", ".join(f"###{x:03d}" for x in w.changing_blockers))
    if not w.verdicts:
        print("  no worldline sealed WALL")
    print("########## END WALL ##########")
    return 0


def _lever(args: argparse.Namespace) -> int:
    """LEVER over one life — G3-02's exit observable: the residue, attributed."""
    from virelai_golden.roles.infer import infer_roles

    record, life, window, wls, _ = _woven(args.recording, args.life)
    read = infer_roles(record, window, wls)
    lv = read.levers
    print(f"########## LEVER · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} · "
          f"actions {record.action_channel} ##########")
    print(f"  excluded before the residue: ego {sorted(m for v in read.bodies for m in v.members) or '∅'} · "
          f"ground {sorted(m for v in read.ground.verdicts for m in v.members) or '∅'} · counters {sorted(read.counters) or '∅'}")
    print(f"  {lv.typed}")
    for p in lv.presses:
        if p.attributed and p.residue:
            own = ", ".join(f"###{w:03d}×{n}" for w, n in sorted(p.partners.items())) or "(no surviving owner)"
            print(f"  press {p.left}→{p.right} · A{p.action} · attributed to "
                  f"{'+'.join(f'###{a:03d}' for a in p.attributed)} · residue {len(p.residue)} on {own}")
    for wid, v in sorted(lv.verdicts.items()):
        print(f"  LEVER · ###{wid:03d}")
        print(f"      basis: {v.basis}")
        print(f"      parallax: {v.parallax}")
    for wid, n in sorted(lv.nulls.items()):
        if wid not in lv.verdicts:
            print(f"  pressed, no effect · ###{wid:03d} ×{n} — INERT unfalsified, never proven")
    for p in lv.unattributed_residue:
        own = ", ".join(f"###{w:03d}×{n}" for w, n in sorted(p.partners.items())) or "(no surviving owner)"
        ev = f" · on a counter event ({', '.join(f'###{c:03d}' for c in p.counter_event)})" if p.counter_event else ""
        print(f"  unattributed residue · press {p.left}→{p.right} · A{p.action} · {len(p.residue)} cell(s) on {own}{ev}")
    if not lv.verdicts:
        print("  no worldline sealed LEVER")
    print("########## END LEVER ##########")
    return 0


def _states(args: argparse.Namespace) -> int:
    """The masked state map and the masked pointer deltas — G2-02's exit observable."""
    from virelai_golden.roles.ego_pointer import infer_ego_pointer
    from virelai_golden.roles.infer import infer_roles
    from virelai_golden.roles.mask import counter_cells, masked_delta, state_map

    record, life, window, wls, _ = _woven(args.recording, args.life)
    read = infer_roles(record, window, wls)
    ids = frozenset(read.counters or {})
    cells = counter_cells(window, wls, ids)
    bare = state_map(record, window, {})
    masked = state_map(record, window, cells)
    print(f"########## STATES · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} ##########")
    print(f"  sealed counters: {sorted(ids) or 'none'} · mask at node {window[0].node}: {masked.masked_cells} cell(s)")
    print(f"  unmasked: {bare.distinct} distinct addresses over {len(window)} nodes · {bare.revisits} revisit(s)")
    print(f"  masked:   {masked.distinct} distinct addresses over {len(window)} nodes · {masked.revisits} revisit(s)")
    for a, nodes in sorted(masked.visits.items(), key=lambda kv: (-len(kv[1]), kv[1]))[:6]:
        if len(nodes) > 1:
            print(f"      {a} · nodes {list(nodes)}")
    pointer, pread = infer_ego_pointer(record, window, wls)
    if pointer is not None:
        residual = []
        for p in pread.presses:
            d = masked_delta(p.changed, cells.get(p.node - 1, frozenset()), cells.get(p.node, frozenset()))
            residual.append((p, d))
        n_res = sum(1 for _, d in residual if d)
        print(f"  pointer presses: {len(residual)} · with a delta after the mask: {n_res}")
        by_owner: dict = {}
        for p, d in residual:
            by_owner.setdefault(p.owner_before, []).append(len(d))
        for o, sizes in sorted(by_owner.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
            own = "EMPTY" if o is None else f"###{o:03d}"
            print(f"      pressed {own} ×{len(sizes)}: masked delta {min(sizes)}–{max(sizes)} cell(s)")
    print("########## END STATES ##########")
    return 0


def _coverage(args: argparse.Namespace) -> int:
    """The coverage roster over the WHOLE game (R-H) — G3-03's exit observable (Unlock 3's form)."""
    from virelai_golden.render.coverage import render_coverage
    from virelai_golden.roles.infer import infer_roles
    from virelai_golden.substrate.ledger import cuts
    from virelai_golden.substrate.load import load_recording
    from virelai_golden.weave.rejoin import re_join
    from virelai_golden.weave.worldline import weave_window

    record, _ = load_recording(args.recording)
    window = cuts(record)
    wls = re_join(weave_window(window), window)
    read = infer_roles(record, window, wls)
    print(f"########## COVERAGE · {record.game_id} · {len(window)} nodes · {record.lives} life/lives · "
          f"actions {record.action_channel} ##########")
    print(f"  roles over the whole game: {read.typed}")
    print(render_coverage(record, window, wls, read))
    print("########## END COVERAGE ##########")
    return 0
