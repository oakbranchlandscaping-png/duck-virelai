#!/usr/bin/env python3
"""Write tests/fixtures/g3_no_choice_golden.json: the no-choice trace of each development record (WO-G3-DIRECTED).

Author: Claude (Alpha build seat), 2026-10-11. Run once from ``472aa32`` code, before any directed-G3 edit; the
regression test then holds every later slice to the same probe envelopes, evidence ids and products whenever no
choice is made. Usage (from ARC3-Inference): PYTHONPATH=.:tests:../tufa-arc-agi-framework/src python3 tools/record_g3_no_choice_golden.py
"""
from __future__ import annotations

import json

from g3_no_choice_trace import GOLDEN, RECORDS, no_choice_trace


def main() -> None:
    golden = {name: no_choice_trace(path) for name, path in RECORDS.items()}
    GOLDEN.write_text(json.dumps(golden, sort_keys=True, indent=1) + "\n")
    for name, trace in golden.items():
        print(name, "steps", trace["steps_replayed"], "events", len(trace["events"]), "products", len(trace["products"]))


if __name__ == "__main__":
    main()
