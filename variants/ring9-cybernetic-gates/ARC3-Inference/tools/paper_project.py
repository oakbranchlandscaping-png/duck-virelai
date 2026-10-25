#!/usr/bin/env python3
"""Project a sealed v11 world model into ``paper_evidence.json`` and the ungraded ``paper_report.md`` (WO-PE-03B).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.

    python tools/paper_project.py WORLD_MODEL.json --out DIR

Offline only (Sol, D21). The packet is deterministic: two runs on one model write identical bytes. A model that cannot
be formal is refused with a typed reason and exit status 2; nothing is written.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inference.paper_evidence import paper_report, projection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("model", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        packet = projection.project(json.loads(args.model.read_text()))
    except projection.ProjectionRefused as exc:
        print(f"REFUSED {exc.code}: {exc.detail}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "paper_evidence.json").write_bytes(projection.evidence_bytes(packet))
    (args.out / "paper_report.md").write_text(paper_report.render(packet))
    stamp, counts = packet["stamp"], packet["counts"]
    print(f"{stamp['game_id']} {stamp['content_sha256'][:16]} claims {counts['claims']} "
          f"(propositions {counts['propositions']}, audits {counts['audits']}) provenance {stamp['integrity']}/"
          f"{stamp['completeness']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
