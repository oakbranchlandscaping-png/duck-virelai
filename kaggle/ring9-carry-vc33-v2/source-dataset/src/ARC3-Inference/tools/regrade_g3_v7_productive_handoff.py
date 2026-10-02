#!/usr/bin/env python3
"""Regrade the frozen vc33 v7 trace under productive G3 handoff policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inference.framework.virelai_gates import GateContractError
from replay_g3_v6_completion import STEM, _prepare_machine, _rows


def replay(artifact_dir: Path) -> dict[str, Any]:
    outcomes = _rows(artifact_dir / f"{STEM}_probe_outcomes.jsonl")
    events = _rows(artifact_dir / f"{STEM}_gate_events.jsonl")
    answers = _rows(artifact_dir / f"{STEM}_gate_answers.jsonl")
    if len(outcomes) != 15 or len(events) != 15:
        raise ValueError("expected the completed 15-transition vc33 v7 trace")

    machine = _prepare_machine(outcomes, events)
    dossier_by_member = {
        str(answer["target_member_id"]): answer
        for answer in answers
        if answer.get("answer_kind") == "LEVER_DOSSIER"
    }
    replayed_probe_ids: list[str] = []
    dispositions: dict[str, str] = {}
    for outcome in outcomes[3:]:
        replay_outcome = {
            key: value for key, value in outcome.items() if key != "evidence_id"
        }
        capability = machine.next_probe_capability()
        if capability is None:
            raise ValueError(f"replay had no capability for {outcome['probe_id']}")
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        if probe.probe_id != outcome["probe_id"]:
            raise ValueError(
                f"probe mismatch: expected {outcome['probe_id']}, got {probe.probe_id}"
            )
        event = machine.record_outcome(probe, replay_outcome)
        replayed_probe_ids.append(probe.probe_id)
        dispositions[probe.probe_id] = str(
            (event.get("attribution") or {}).get("disposition") or ""
        )
        lever = machine._adapters["G3-LEVERS"]
        if lever._pending_dossier is not None:
            member_id = str(lever._pending_dossier["target_member_id"])
            machine.submit_answer(dossier_by_member[member_id])

    if machine.next_probe_capability() is not None:
        raise ValueError("v7 replay did not exhaust the G3 roster")
    pre_answer = machine.gate_view()
    template = dict(pre_answer["answer_template"])
    accepted = machine.submit_answer({
        **template,
        "explanation": (
            "The exhaustive click roster found two prospectively confirmed remote levers. "
            "Every remaining tested object produced no non-counter lever residue in its "
            "recorded state; these are scoped responses and not inertness claims."
        ),
        "competing_models": [
            "A scoped-null target may respond after a later visible or hidden state change."
        ],
        "falsifier": (
            "A later intervention on a scoped-null target produces attributed local or remote "
            "residue outside the counter mask."
        ),
    })
    card = machine.gate_view()
    revision = int(card["revision"])
    duplicate_rejected = False
    try:
        machine.submit_answer(template)
    except GateContractError as exc:
        duplicate_rejected = "already accepted" in str(exc)

    handles = [item["query"] for item in card["expand"]]
    last_three = [f"G3-LEVERS:CLICK:{rank}" for rank in (8, 9, 10)]
    checks = {
        "all_v7_probes_replayed": replayed_probe_ids == [
            outcome["probe_id"] for outcome in outcomes[3:]
        ],
        "last_three_are_counter_only": all(
            dispositions.get(probe_id) == "COUNTER_ONLY_RESPONSE"
            for probe_id in last_three
        ),
        "clean_inventory_accepted": accepted.answer_kind == "LEVER_INVENTORY",
        "partition_regraded": (
            card["confirmed_levers"]["total"] == 2
            and card["scoped_nulls"]["total"] == 8
            and card["bounded_unknowns"]["total"] == 0
            and card["completion"]["counter_excluded_count"] == 1
        ),
        "g3_product_emitted": (
            machine.target_journal.active_product("G3-LEVERS") is not None
            and card["status"] == "SATISFIED"
            and card["next_operation"] == "WAIT_FOR_NEXT_TARGET"
        ),
        "accepted_answer_is_terminal": (
            card["answer_template"] is None
            and duplicate_rejected
            and machine.gate_view()["revision"] == revision
        ),
        "expansion_handles_are_executable_shape": handles == [
            "virelai('inventory', offset=0, limit=10)",
            "virelai('entity', id=entity_id, offset=0, limit=128)",
            "virelai('evidence', id=evidence_id)",
        ],
    }
    return {
        "schema": "virelai-g3-v7-productive-handoff-regrade-v1",
        "artifact_dir": str(artifact_dir),
        "replayed_probe_count": len(replayed_probe_ids),
        "last_three_dispositions": {
            probe_id: dispositions.get(probe_id) for probe_id in last_three
        },
        "partition": {
            "confirmed_levers": card["confirmed_levers"]["total"],
            "scoped_nulls": card["scoped_nulls"]["total"],
            "bounded_unknowns": card["bounded_unknowns"]["total"],
            "counter_exclusions": card["completion"]["counter_excluded_count"],
        },
        "completion": card["completion"],
        "gate_status": card["status"],
        "next_operation": card["next_operation"],
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args()
    result = replay(args.artifact_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
