#!/usr/bin/env python3
"""Write tests/fixtures/g4_no_choice_golden.json: the no-choice G4 traces (WO-G4-DOSSIER-B, slice B2).

Author: Claude (Alpha build seat), 2026-10-18. Run once from ``0119a74`` code, before any B2 edit; the regression
test then holds B2 (and every later slice) to the same controller steps, probe envelopes, evidence ids and products
whenever no choice is made. Usage (from ARC3-Inference): PYTHONPATH=.:tests:../tufa-arc-agi-framework/src python3 tools/record_g4_no_choice_golden.py
"""
from __future__ import annotations

import json

from g4_no_choice_trace import GOLDEN, traces


def main() -> None:
    golden = traces()
    GOLDEN.write_text(json.dumps(golden, sort_keys=True, indent=1) + "\n")
    controller = golden["ft09_controller"]
    print("ft09_controller steps", len(controller["steps"]), "products", len(controller["products"]),
          "gate", controller["gate"])
    print("ft09_record events", len(golden["ft09_record"]["events"]), "products", len(golden["ft09_record"]["products"]))


if __name__ == "__main__":
    main()
