"""The no-choice trace of a development record: every probe envelope, evidence id and product (WO-G3-DIRECTED).

Author: Claude (Alpha build seat), 2026-10-11. Sol's decision 2 on the directed-G3 design: "An unchanged coverage
path must preserve its existing probe IDs and resulting evidence IDs ... Extend test 0 to compare probe envelopes,
evidence IDs and products on no-choice replays, not just scheduler events."

``no_choice_trace`` replays a record through the production gate path (``record_replay.replay``) and records,
for every outcome the gate machine accepts, the probe id, a hash of the full probe envelope and the evidence id
the gate assigned; then every active product, every frozen level and the G3 lifecycle states. The golden file
(``tests/fixtures/g3_no_choice_golden.json``) was written from ``472aa32`` code by
``tools/record_g3_no_choice_golden.py`` before any directed-G3 edit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import CyberneticGateMachine

FIXTURES = Path(__file__).parent / "fixtures"
RECORDS = {
    "k008": FIXTURES / "ring9_v2_k008_g3_lifecycle_record.json.gz",
    "k013": FIXTURES / "ring9_v2_k013_g3_lifecycle_record.json.gz",
    "carry_v7": FIXTURES / "vc33_kaggle_carry_v7_record.json.gz",
}
GOLDEN = FIXTURES / "g3_no_choice_golden.json"


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def no_choice_trace(path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    original = CyberneticGateMachine.record_outcome

    def traced(self, probe, outcome):
        event = original(self, probe, outcome)
        events.append({"gate_id": probe.gate_id, "probe_id": probe.probe_id, "probe_sha": _sha(asdict(probe)),
                       "evidence_id": event.get("evidence_id")})
        return event

    CyberneticGateMachine.record_outcome = traced
    try:
        result = replay(load_record(path), measure=False)
    finally:
        CyberneticGateMachine.record_outcome = original
    machine = result.machine
    products = [
        {"target_id": contract.target_id, "product_id": product.product_id, "product_type": product.product_type,
         "revision": product.revision, "payload_sha": _sha(product.payload)}
        for contract in machine.target_registry.ordered()
        if (product := machine.target_journal.active_product(contract.target_id)) is not None
    ]
    g3 = machine._adapters["G3-LEVERS"]
    journal = g3.lifecycle_journal
    return {
        "steps_replayed": result.steps_replayed,
        "stopped": result.stopped,
        "events": events,
        "products": products,
        "frozen_levels_sha": _sha(machine.levels),
        "transition_index_sha": _sha(machine.transition_index),
        "g3_lifecycle": {} if journal is None else {eid: item.state for eid, item in sorted(journal.entities.items())},
    }


__all__ = ["GOLDEN", "RECORDS", "no_choice_trace"]
