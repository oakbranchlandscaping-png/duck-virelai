"""WO_INDUCED_MAP_RENDER_FROM_RECORDING · the offline entry — an official
recording into the two-grain induced map.

Source-blind by design. The core renders any ``FrameRecordLog`` — the live
in-process ``ctx.frame_record_log`` OR one rebuilt offline from a recording —
whether a captain or a human produced it (both emit the same
``*.recording.jsonl``). It skips the persisted-JSON path (``log_io``) entirely:
the induced map is built straight from the capture log, in memory.

Path::

    live run → ``self.recorder`` writes ``<name>.recording.jsonl``
             → ``capture.ledger_build.load_capture`` → ``FrameRecordLog``
             → ``build_induced_map`` → two-grain render

Fences: the stdlib-only induced-map layer is imported at module scope; the
perception-dependent ``load_capture`` is deferred to call time, so the
source-blind core stays importable where scipy is absent. Imports nothing from
``log_io`` (the broken-reconstruction path, HL rung-2) and edits no sealed
capture.
"""

from __future__ import annotations

import argparse

from virelai_v4.weave.induced_map import (
    build_induced_map,
    map_stats,
    render_condensed_grain,
    render_raw_grain,
    render_stats,
)


def render_capture_log(log, *, both_grains: bool = True) -> str:
    """The source-blind core: a ``FrameRecordLog`` (live or offline, duck-typed
    ``.records``) → two-grain induced-map text. Pure over the capture log —
    stdlib-only, no perception dependency."""
    m = build_induced_map(log.records)
    blocks = [render_raw_grain(m)]
    if both_grains:
        blocks.append(render_condensed_grain(m))
    blocks.append(render_stats(map_stats(m)))
    return "\n\n".join(blocks)


def render_recording(path: str, *, both_grains: bool = True) -> str:
    """Offline entry: an official ``*.recording.jsonl`` → two-grain induced map.
    Defers ``load_capture`` (perception/scipy-dependent) to call time so this
    module imports cleanly without the solver's scientific stack."""
    from virelai_v4.capture.ledger_build import load_capture
    return render_capture_log(load_capture(path), both_grains=both_grains)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="virelai_v4.weave.render_from_recording",
        description="Render the two-grain induced map from an official recording.",
    )
    parser.add_argument(
        "--recording", required=True, help="path to an official *.recording.jsonl"
    )
    parser.add_argument(
        "--raw-only", action="store_true", help="render only the raw fidelity grain"
    )
    args = parser.parse_args(argv)
    print(render_recording(args.recording, both_grains=not args.raw_only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
