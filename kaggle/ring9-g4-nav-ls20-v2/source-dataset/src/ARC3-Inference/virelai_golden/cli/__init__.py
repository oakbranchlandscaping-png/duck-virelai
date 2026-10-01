"""golden — the command line. Every subcommand not yet built fails loudly with NOT_BUILT.
Commands live in `cli/rung0.py` (the substrate and weave reads, play, diff) and `cli/roles.py`
(the role reads); this file is the parser."""
from __future__ import annotations

import argparse
import sys

from virelai_golden.cli.roles import _coverage, _ego, _ground, _lever, _states, _wall
from virelai_golden.cli.rung0 import (  # noqa: F401 — re-exported for tests and scripts
    NotBuilt, _diff, _last_played, _ledger, _play, _record, _replay, _roster, _scan, _weave, _woven,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="golden", description="the Virelai golden run")
    sub = p.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("scan", help="frame-0 region census of a recording (G0-01)")
    sc.add_argument("recording")
    sc.set_defaults(fn=_scan)

    rc = sub.add_parser("record", help="record header + DELIVERY ROSTER of a recording (G0-02)")
    rc.add_argument("recording")
    rc.set_defaults(fn=_record)

    lg = sub.add_parser("ledger", help="PRISTINE + conservation over every node/edge (G0-03)")
    lg.add_argument("recording")
    lg.set_defaults(fn=_ledger)

    wv = sub.add_parser("weave", help="worldlines per life and whole-game (G0-04)")
    wv.add_argument("recording")
    wv.set_defaults(fn=_weave)

    r = sub.add_parser("replay", help="record → ledger → weave → roster, from a recording (Rung 0 whole)")
    r.add_argument("recording")
    r.add_argument("--verbose", action="store_true", help="append each object's cell set")
    r.set_defaults(fn=_replay)

    ro = sub.add_parser("roster", help="LIST 1 / LIST 2 for one life (default: last played) — Unlock 0")
    ro.add_argument("recording")
    ro.add_argument("--life", type=int, default=None)
    ro.add_argument("--verbose", action="store_true", help="append each object's cell set")
    ro.set_defaults(fn=_roster)

    st = sub.add_parser("states", help="masked state addresses + masked pointer deltas (G2-02)")
    st.add_argument("recording")
    st.add_argument("--life", type=int, default=None)
    st.set_defaults(fn=_states)

    eg = sub.add_parser("ego", help="EGO(BODY) verdicts for one life (default: last played) (G1-01)")
    eg.add_argument("recording")
    eg.add_argument("--life", type=int, default=None)
    eg.set_defaults(fn=_ego)

    gr = sub.add_parser("ground", help="GROUND: the fold read off the sealed ego, one life (G3-01, R-M)")
    gr.add_argument("recording")
    gr.add_argument("--life", type=int, default=None)
    gr.set_defaults(fn=_ground)

    wa = sub.add_parser("wall", help="WALL: what refused the sealed ego, one life (G3-01b)")
    wa.add_argument("recording")
    wa.add_argument("--life", type=int, default=None)
    wa.set_defaults(fn=_wall)

    le = sub.add_parser("lever", help="LEVER: the residue after ego/ground/counter, attributed (G3-02, R-G)")
    le.add_argument("recording")
    le.add_argument("--life", type=int, default=None)
    le.set_defaults(fn=_lever)

    cv = sub.add_parser("coverage", help="TOUCHED / NOT REACHED / NEVER ATTEMPTED / GROUND, whole game (G3-03)")
    cv.add_argument("recording")
    cv.set_defaults(fn=_coverage)

    pl = sub.add_parser("play", help="play a game live via the arc_agi SDK; write the golden record (G0-06)")
    pl.add_argument("game", help="game id, e.g. ls20")
    pl.add_argument("--seed", type=int, default=0, help="policy seed (written to the record)")
    pl.add_argument("--env-seed", type=int, default=0, help="environment seed passed to arc.make")
    pl.add_argument("--max-lives", type=int, default=2)
    pl.add_argument("--max-actions", type=int, default=400)
    pl.add_argument("--out", default="recordings")
    pl.add_argument("--policy", choices=["opening", "sweep", "cycle"], default="opening",
                    help="opening (canon 03 §5, default), sweep (G3-03: opening then enumeration) or the CYCLE-v0 scaffold")
    pl.set_defaults(fn=_play)

    d = sub.add_parser("diff", help="two recordings: objects and worldline signatures in common")
    d.add_argument("a")
    d.add_argument("b")
    d.set_defaults(fn=_diff)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except NotBuilt as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
