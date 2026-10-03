"""golden.cli.rung0 — the Rung 0 commands: scan, record, ledger, weave, replay, roster, play, diff.
Split from `golden/cli.py` at G3-02 (the 400-line limit, ADR-0006); bodies unchanged."""
from __future__ import annotations

import argparse


class NotBuilt(RuntimeError):
    pass


def _scan(args: argparse.Namespace) -> int:
    """Frame-0 region census of a recording — G0-01's exit observable. Reads node 0 of the
    Record (G0-02); the recording's node 0 is not the game's initial frame (F-0002)."""
    from virelai_golden.substrate.grid import grid_total
    from virelai_golden.substrate.load import load_recording
    from virelai_golden.substrate.scan import INTERIM_O8, partition_breaches, scan_grid

    record, _ = load_recording(args.recording)
    grid = record.nodes[0].settled
    regions = scan_grid(grid)
    breaches = partition_breaches(grid, regions)
    h, w = grid.shape
    print(f"frame 0 · {h}x{w} · total {grid_total(grid)} · {len(regions)} regions · {INTERIM_O8}")
    for r in regions:
        print(f"  R{r.region_id:<3d} class {r.value:<2d} · {r.area:>5d} cells · NW {r.anchor}")
    print(f"partition: {'PASS' if not breaches else 'FAIL'}" + (f" {breaches}" if breaches else ""))
    return 0 if not breaches else 1


def _record(args: argparse.Namespace) -> int:
    """The Record's header and DELIVERY ROSTER — G0-02's exit observable."""
    from virelai_golden.render.delivery import render_delivery_roster, render_record_header
    from virelai_golden.substrate.delivery import deliveries
    from virelai_golden.substrate.load import load_recording

    record, skipped = load_recording(args.recording)
    print(render_record_header(record, skipped))
    print(render_delivery_roster(deliveries(record), len(record)))
    return 0


def _ledger(args: argparse.Namespace) -> int:
    """PRISTINE, conservation and distinct-object counts — G0-03's exit observable."""
    from virelai_golden.render.ledger import render_conservation, render_distinct, render_pristine
    from virelai_golden.substrate.ledger import conservation, cuts, distinct_objects, grade_pristine
    from virelai_golden.substrate.load import load_recording

    record, _ = load_recording(args.recording)
    node_cuts = cuts(record)
    verdict = grade_pristine(record, node_cuts)
    transitions = conservation(record)
    print(render_pristine(verdict))
    print(render_conservation(transitions))
    print(render_distinct(distinct_objects(record, node_cuts)))
    return 0 if verdict.passed and all(t.closes for t in transitions) else 1


def _weave(args: argparse.Namespace) -> int:
    """Worldlines per life and whole-game — G0-04's exit observable (Y per last life = v4)."""
    from collections import Counter

    from virelai_golden.substrate.ledger import cuts
    from virelai_golden.substrate.load import load_recording
    from virelai_golden.weave.edge import INTERIM_O9
    from virelai_golden.weave.rejoin import re_join
    from virelai_golden.weave.worldline import weave_window, window_edges

    record, _ = load_recording(args.recording)
    node_cuts = cuts(record)
    print(f"########## WEAVE · {record.game_id} · {INTERIM_O9} ##########")
    for life in range(1, record.lives + 1):
        window = [c for c, n in zip(node_cuts, record.nodes) if n.life == life]
        raw = weave_window(window)
        joined = re_join(raw, window)
        verbs = Counter(e.verb.value for _, _, e in window_edges(window))
        played = "played" if any(n.ends_life for n in record.nodes if n.life == life) else "unplayed"
        print(f"  life {life} ({played}) · nodes {window[0].node}–{window[-1].node} · "
              f"threaded {len(raw)} → rejoined Y={len(joined)} · verbs "
              + " ".join(f"{k}:{v}" for k, v in sorted(verbs.items())))
    whole = re_join(weave_window(node_cuts), node_cuts)
    print(f"  whole game (R-H) · nodes 0–{node_cuts[-1].node} · Y={len(whole)} · NOT_GRADED (v4 wove per life)")
    print("########## END WEAVE ##########")
    return 0


def _last_played(record, node_cuts):
    """The last life that ended (v4's roster window). A trailing unplayed frame is not a life."""
    life = max((n.life for n in record.nodes if n.ends_life), default=record.lives)
    return life, [c for c, n in zip(node_cuts, record.nodes) if n.life == life]


def _woven(path: str, life: int | None = None):
    from virelai_golden.substrate.ledger import cuts
    from virelai_golden.substrate.load import load_recording
    from virelai_golden.weave.rejoin import re_join
    from virelai_golden.weave.worldline import weave_window

    record, _ = load_recording(path)
    node_cuts = cuts(record)
    if life is None:
        life, window = _last_played(record, node_cuts)
    else:
        window = [c for c, n in zip(node_cuts, record.nodes) if n.life == life]
    if not window:
        raise SystemExit(f"golden: no nodes in life {life} of {path}")
    played = sum(1 for n in record.nodes if n.ends_life)
    return record, life, window, re_join(weave_window(window), window), played


def _roster(args: argparse.Namespace) -> int:
    """LIST 1 / LIST 2 for one life of a recording (default: the last played) — Unlock 0."""
    from virelai_golden.render.roster import render_lists

    from virelai_golden.render.roster import render_list3
    from virelai_golden.roles.infer import infer_roles

    record, life, window, wls, played = _woven(args.recording, args.life)
    print(f"########## ROSTER · {record.game_id} · life {life} · nodes {window[0].node}–{window[-1].node} ##########")
    print(render_lists(wls, verbose=args.verbose, lives_observed=played))
    print(render_list3(infer_roles(record, window, wls), wls))
    print(f"########## END ROSTER · {len(wls)} ### ##########")
    return 0


def _replay(args: argparse.Namespace) -> int:
    """The whole Rung 0 pipeline over a recording: record → ledger → weave → roster."""
    from virelai_golden.render.delivery import render_delivery_roster, render_record_header
    from virelai_golden.render.ledger import render_conservation, render_distinct, render_pristine
    from virelai_golden.render.roster import render_lists
    from virelai_golden.substrate.delivery import deliveries
    from virelai_golden.substrate.ledger import conservation, cuts, distinct_objects, grade_pristine
    from virelai_golden.substrate.load import load_recording
    from virelai_golden.weave.rejoin import re_join
    from virelai_golden.weave.worldline import weave_window

    record, skipped = load_recording(args.recording)
    node_cuts = cuts(record)
    verdict = grade_pristine(record, node_cuts)
    print(render_record_header(record, skipped))
    print(render_delivery_roster(deliveries(record), len(record)))
    print(render_pristine(verdict))
    print(render_conservation(conservation(record)))
    print(render_distinct(distinct_objects(record, node_cuts)))
    if not verdict.passed:
        return 1
    from virelai_golden.render.roster import render_list3
    from virelai_golden.roles.infer import infer_roles

    life, window = _last_played(record, node_cuts)
    wls = re_join(weave_window(window), window)
    played = sum(1 for n in record.nodes if n.ends_life)
    print(f"########## ROSTER · life {life} · nodes {window[0].node}–{window[-1].node} ##########")
    print(render_lists(wls, verbose=args.verbose, lives_observed=played))
    print(render_list3(infer_roles(record, window, wls), wls))
    print(f"########## END ROSTER · {len(wls)} ### ##########")
    return 0


def _play(args: argparse.Namespace) -> int:
    """Play one game live through the SDK and write the golden record (G0-06)."""
    from virelai_golden.adapter import PlayLimits, play

    limits = PlayLimits(max_lives=args.max_lives, max_actions=args.max_actions)
    path = play(args.game, seed=args.seed, env_seed=args.env_seed, out_dir=args.out, limits=limits,
                policy=args.policy)
    print(path)
    return 0


def _diff(args: argparse.Namespace) -> int:
    """Two recordings, last played life each: objects and worldline signatures in common."""
    from virelai_golden.render.diff import render_diff

    _, _, _, wa, _ = _woven(args.a)
    _, _, _, wb, _ = _woven(args.b)
    print(render_diff(args.a.rsplit("/", 1)[-1][:24], wa, args.b.rsplit("/", 1)[-1][:24], wb))
    return 0
