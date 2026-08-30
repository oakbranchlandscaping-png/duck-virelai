"""WO_INDUCED_MAP · the read-side render — ``python -m virelai_v4.weave.map_render``.

Offline, pure read over a captured log (serialized by ``log_io``). Builds the
induced map and prints its two grains (R1) plus the modality read (R3):

    uv run python -m virelai_v4.weave.map_render --log <captured.json> --both-grains

Sandbox-only by construction: it grades nothing live and touches no belief. The
capture run that produces ``<captured.json>`` is the Director's live surface; this
module is a pure read over its output.
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from virelai_v4.weave.induced_map import (
    build_induced_map,
    map_stats,
    render_condensed_grain,
    render_raw_grain,
    render_stats,
)
from virelai_v4.weave.log_io import load_log


def render_report(records: List, *, both_grains: bool) -> str:
    m = build_induced_map(records)
    blocks = [render_raw_grain(m)]
    if both_grains:
        blocks.append(render_condensed_grain(m))
    blocks.append(render_stats(map_stats(m)))
    return "\n\n".join(blocks)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="virelai_v4.weave.map_render",
        description="Render the induced map from a captured route log.",
    )
    parser.add_argument("--log", required=True, help="path to a serialized capture log (JSON)")
    parser.add_argument(
        "--both-grains", action="store_true",
        help="render both the raw fidelity grain and the condensed geometry grain",
    )
    args = parser.parse_args(argv)

    records = load_log(args.log)
    if not records:
        print(f"map_render: empty log at {args.log}", file=sys.stderr)
        return 1
    print(render_report(records, both_grains=args.both_grains))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
