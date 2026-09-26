#!/usr/bin/env python3
"""Evaluate executed G2 counter artifacts without mistaking schema for understanding.

Grades the Ring 9 G0-G2 counter checkpoint per world from the executed artifacts
alone.  Every arithmetic claim (witness recurrence, conservation, footprint
purity, the HUD/world partition, shared world addresses)
is recomputed from the lossless probe outcomes rather than trusted from the
candidate or mask rows.  Semantic correctness is only ever established by a
human frame review bound to the exact execution receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

OPAQUE_ACTION = re.compile(r"^ACTION[0-9]+$")
GATE_ID = "G2-COUNTER"
RECEIPT_SCHEMAS = frozenset({
    "virelai-g2-execution-receipt-v1",
    "virelai-g2-reliability-execution-receipt-v2",
})
REVIEW_SCHEMA = "virelai-g2-human-review-v1"
REPORT_SCHEMA = "virelai-g2-checkpoint-evaluation-v1"
PACKET_SCHEMA = "virelai-g2-human-review-packet-v1"
MASK_SENTINEL = "<COUNTER_MASKED>"
REVIEW_VERDICTS = (
    "tracked_variable_matches_frames",
    "footprint_holds_only_bookkeeping_no_world_object",
    "bookkeeping_interpretation_justified_by_varied_interventions",
    "mask_scope_complete_and_reversible",
    "confirmation_action_was_counter_only",
)
REVIEW_QUESTIONS = (
    "Does the tracked variable match what visibly changes in the frames?",
    "Does the inferred full footprint contain only the two counter integer classes "
    "and no causal world object?",
    "Was the rate prediction recorded before its confirming transition, and was the "
    "confirmation action counter-only rather than a novel-target click?",
    "Does the mask cover the complete bar, do counter-only frames share one world "
    "state, and does simultaneous outside-mask change remain visible?",
)


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _stems(artifacts: Path) -> list[str]:
    suffixes = (
        "_gate_answers.jsonl", "_probe_envelopes.jsonl", "_gate_events.jsonl",
        "_probe_outcomes.jsonl", "_probe_frames.jsonl",
    )
    return sorted({
        path.name.removesuffix(suffix)
        for suffix in suffixes
        for path in artifacts.glob(f"*{suffix}")
    })


def _world_matches(stem: str, world: str) -> bool:
    return stem == world or stem.startswith(f"{world}_p")


def _check(value: Any, detail: str) -> dict[str, Any]:
    return {"passed": bool(value), "detail": detail}


def _grade(checks: Mapping[str, dict[str, Any]], *, pending: bool = False) -> dict[str, Any]:
    status = "REVIEW_REQUIRED" if pending else (
        "PASS" if checks and all(item["passed"] for item in checks.values()) else "FAIL"
    )
    return {"status": status, "checks": dict(checks)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_optional(run_dir: Path, supplied: Path | None, name: str) -> Path | None:
    if supplied is not None:
        return supplied
    for candidate in (run_dir / name, run_dir.parent / name):
        if candidate.is_file():
            return candidate
    return None


def _cell(value: Any) -> tuple[int, int] | None:
    if isinstance(value, Mapping) and value.get("row") is not None:
        return int(value["row"]), int(value["col"])
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return int(value[0]), int(value[1])
    return None


def _cells(values: Any) -> set[tuple[int, int]]:
    found: set[tuple[int, int]] = set()
    for item in values or ():
        cell = _cell(item)
        if cell is not None:
            found.add(cell)
    return found


def _pair(rewrite: str) -> tuple[int, int] | None:
    try:
        left, right = str(rewrite).split("->", 1)
        return int(left), int(right)
    except (TypeError, ValueError):
        return None


def _changed_by_rewrite(outcome: Mapping[str, Any], rewrite: str) -> set[tuple[int, int]]:
    found: set[tuple[int, int]] = set()
    for item in outcome.get("changed_cells") or ():
        if not isinstance(item, Mapping):
            continue
        if f"{item.get('before')}->{item.get('after')}" == rewrite:
            found.add((int(item["row"]), int(item["col"])))
    return found


def _site_values(outcome: Mapping[str, Any], field: str) -> dict[tuple[int, int], int] | None:
    """Total site ledger for one side of a transition, or None when coverage is partial."""
    shape = outcome.get("shape_before")
    transitions = outcome.get("site_transitions")
    if (
        not isinstance(shape, (list, tuple)) or len(shape) != 2
        or not isinstance(transitions, (list, tuple))
    ):
        return None
    rows, cols = int(shape[0]), int(shape[1])
    values: dict[tuple[int, int], int] = {}
    for item in transitions:
        if not isinstance(item, Mapping) or item.get(field) is None:
            return None
        values[(int(item["row"]), int(item["col"]))] = int(item[field])
    if len(values) != rows * cols:
        return None
    return values


def _standing(
    values: Mapping[tuple[int, int], int] | None,
    footprint: set[tuple[int, int]],
    source: int,
    replacement: int,
) -> tuple[int, int] | None:
    if values is None or any(cell not in values for cell in footprint):
        return None
    return (
        sum(values[cell] == source for cell in footprint),
        sum(values[cell] == replacement for cell in footprint),
    )


def _masked_view(
    values: Mapping[tuple[int, int], int], mask: set[tuple[int, int]]
) -> tuple[tuple[Any, ...], ...]:
    rows = max(cell[0] for cell in values) + 1
    cols = max(cell[1] for cell in values) + 1
    return tuple(
        tuple(
            MASK_SENTINEL if (row, col) in mask else values[(row, col)]
            for col in range(cols)
        )
        for row in range(rows)
    )


def _execution_receipt(
    path: Path | None, stems: list[str], expected_games: list[str] | None,
) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    parse_ok = False
    if path and path.is_file():
        try:
            value = json.loads(path.read_text())
            raw = value if isinstance(value, dict) else {}
            parse_ok = isinstance(value, dict)
        except (OSError, json.JSONDecodeError):
            pass
    package = raw.get("package") if isinstance(raw.get("package"), dict) else {}
    model = raw.get("model") if isinstance(raw.get("model"), dict) else {}
    budgets = raw.get("budgets") if isinstance(raw.get("budgets"), dict) else {}
    worlds = raw.get("worlds") if isinstance(raw.get("worlds"), list) else []
    required_worlds = expected_games or stems
    alignment = (
        len(worlds) == len(required_worlds)
        and all(any(_world_matches(stem, str(world)) for stem in stems) for world in worlds)
        and all(any(_world_matches(stem, str(world)) for world in worlds) for stem in stems)
    )
    checks = {
        "receipt_present_and_json": _check(parse_ok, "Execution receipt exists and is a JSON object."),
        "schema": _check(
            raw.get("schema") in RECEIPT_SCHEMAS,
            "schema must be a supported G2 execution receipt: "
            + ", ".join(sorted(RECEIPT_SCHEMAS)) + ".",
        ),
        "package_identity": _check(
            bool(package.get("name"))
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(package.get("sha256") or "")))
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(package.get("manifest_sha256") or ""))),
            "Package name, package SHA-256, and manifest SHA-256 are required.",
        ),
        "model_identity": _check(bool(model.get("id")), "Exact model id is required."),
        "budgets": _check(
            isinstance(budgets.get("max_environment_actions_per_world"), int)
            and budgets.get("max_environment_actions_per_world", 0) > 0
            and isinstance(budgets.get("max_runtime_seconds_per_world"), int)
            and budgets.get("max_runtime_seconds_per_world", 0) > 0
            and isinstance(budgets.get("context_window_tokens"), int)
            and budgets.get("context_window_tokens", 0) > 0
            and (
                (
                    isinstance(budgets.get("max_output_tokens_per_turn"), int)
                    and budgets.get("max_output_tokens_per_turn", 0) > 0
                )
                or budgets.get("max_output_tokens_per_turn") == "server_default"
            )
            and isinstance(budgets.get("tool_output_tokens"), int)
            and budgets.get("tool_output_tokens", 0) > 0,
            "Action, runtime, context, model-output, and tool-output limits are required.",
        ),
        "passes": _check(
            isinstance(raw.get("passes"), int) and raw.get("passes", 0) > 0,
            "Pass count is required.",
        ),
        "concurrency": _check(
            isinstance(raw.get("concurrency"), int) and raw.get("concurrency", 0) > 0,
            "Concurrency is required.",
        ),
        "gated_mode": _check(raw.get("mode") == "gated", "Receipt mode must be gated."),
        "world_alignment": _check(
            alignment, "Receipt worlds must match this evaluation's artifact worlds exactly."
        ),
    }
    grade = _grade(checks)
    grade.update({
        "path": str(path) if path else None,
        "sha256": _sha256(path) if path and path.is_file() else None,
        "configuration": raw,
    })
    return grade


def _reviews(
    path: Path | None, receipt_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    raw: dict[str, Any] = {}
    if path and path.is_file():
        try:
            value = json.loads(path.read_text())
            raw = value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
    rows = raw.get("reviews") if isinstance(raw.get("reviews"), list) else []
    checks = {
        "schema": _check(
            raw.get("schema") == REVIEW_SCHEMA, f"schema must be {REVIEW_SCHEMA}."
        ),
        "receipt_binding": _check(
            bool(receipt_sha256)
            and raw.get("execution_receipt_sha256") == receipt_sha256,
            "Review must bind to this exact execution receipt.",
        ),
        "unique_games": _check(
            len(rows) == len({str(row.get("game")) for row in rows}),
            "One review row per game.",
        ),
    }
    valid_header = all(item["passed"] for item in checks.values())
    return {
        "path": str(path) if path else None,
        "status": "PASS" if valid_header else ("MISSING" if path is None else "FAIL"),
        "checks": checks,
    }, ({str(row.get("game")): row for row in rows} if valid_header else {})


def _g1_closed(answers: list[dict[str, Any]]) -> bool:
    for row in answers:
        if row.get("gate_id") != "G1-EGO":
            continue
        law = row.get("ego_law")
        if isinstance(law, dict) and law.get("status") in {"INTERFACE_AXIOM", "OBSERVED"}:
            return True
    return False


def _g2_disposition(
    g2_probes: list[dict], g2_events: list[dict], g1_closed: bool,
) -> tuple[str | None, str]:
    if not g2_probes and not g2_events:
        reason = (
            "No G2 artifacts; G1 closed but G2 never received a probe or answer."
            if g1_closed else
            "No G2 artifacts because the G1 prerequisite never closed."
        )
        return "NOT_REACHED", reason
    last_status = str(g2_events[-1].get("gate_status_after") or "") if g2_events else ""
    if last_status == "CLOSED":
        search = next(
            (row.get("search_disposition") for row in reversed(g2_events)
             if isinstance(row.get("search_disposition"), dict)),
            None,
        )
        if isinstance(search, dict) and search.get("status") == "COUNTER_NOT_OBSERVED_WITHIN_OPENING":
            return "COUNTER_NOT_OBSERVED", (
                "The complete ranked opening observed no recurrent counter process; this is a "
                "scoped handoff with later monitoring, not a claim of global absence."
            )
        model = next(
            (row.get("counter_model") for row in reversed(g2_events)
             if isinstance(row.get("counter_model"), dict)),
            None,
        )
        return None, "G2 closed; grading its full chain."
    comparison = next(
        (row.get("counter_comparison") for row in reversed(g2_events)
         if isinstance(row.get("counter_comparison"), dict)),
        None,
    )
    if isinstance(comparison, dict) and comparison.get("outcome") == "INDETERMINATE":
        return "REPRESENTATION_GAP", (
            "The prospective comparison was INDETERMINATE; the evidence could not "
            "resolve the declared claim."
        )
    if last_status == "UNRESOLVED":
        return "BUDGET_EXHAUSTED", (
            "G2 ended UNRESOLVED within its bounded probes; the gate stays open and "
            "is not graded FAIL."
        )
    return "BUDGET_EXHAUSTED", (
        f"The run ended with G2 mid-gate (status {last_status or 'UNKNOWN'})."
    )


def _g2_grades(
    answers: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    events: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    review: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    findings: list[str] = []
    answer = next(
        (row for row in reversed(answers) if row.get("gate_id") == GATE_ID), {}
    )
    candidate = answer.get("counter_candidate") if isinstance(answer.get("counter_candidate"), dict) else {}
    prediction = answer.get("pending_prediction") if isinstance(answer.get("pending_prediction"), dict) else {}
    rewrite = str(candidate.get("rewrite") or "")
    pair = _pair(rewrite)
    source, replacement = pair if pair else (None, None)
    support = _cells(candidate.get("observed_support"))
    footprint = _cells(candidate.get("full_bar_footprint")) or set(support)
    geometry = str(candidate.get("footprint_geometry") or "")
    witness_refs = [str(item) for item in candidate.get("witness_evidence_refs") or []]
    amounts = [int(item) for item in candidate.get("amount_per_transition") or []]
    intervention_keys = [str(item) for item in candidate.get("intervention_keys") or []]

    by_evidence = {str(row.get("evidence_id") or ""): row for row in outcomes}
    probe_ids = [str(row.get("probe_id") or "") for row in probes]
    event_probe_ids = [str(row.get("probe_id") or "") for row in events]
    outcome_probe_ids = [str(row.get("probe_id") or "") for row in outcomes]
    frame_evidence = {str(row.get("evidence_id") or "") for row in frames}
    event_evidence = [str(row.get("evidence_id") or "") for row in events]
    purposes = {
        str(row.get("probe_id") or ""): str(row.get("purpose") or "") for row in probes
    }
    witnesses = [by_evidence[ref] for ref in witness_refs if ref in by_evidence]

    comparison = next(
        (row.get("counter_comparison") for row in reversed(events)
         if isinstance(row.get("counter_comparison"), dict)),
        {},
    ) or {}
    boundary = next(
        (row.get("counter_boundary") for row in reversed(events)
         if isinstance(row.get("counter_boundary"), dict)),
        {},
    ) or {}
    mask_law = next(
        (row.get("mask_law") for row in reversed(events)
         if isinstance(row.get("mask_law"), dict)),
        {},
    ) or {}
    mask = _cells(mask_law.get("cells"))
    demo_outcome = by_evidence.get(str(comparison.get("evidence_ref") or ""), {})
    demo_event = next(
        (row for row in events
         if str(row.get("evidence_id")) == str(comparison.get("evidence_ref") or "")),
        {},
    )
    boundary_outcome = by_evidence.get(str(boundary.get("evidence_ref") or ""), {})
    last_status = str(events[-1].get("gate_status_after") or "") if events else ""

    protocol = _grade({
        "g1_closed_before_g2": _check(
            True, "Checked at disposition time; G2 artifacts imply an opened gate."
        ),
        "one_g2_answer": _check(
            bool(answer), "The latest accepted G2 answer is graded."
        ),
        "unique_probe_ids": _check(
            bool(probe_ids) and len(probe_ids) == len(set(probe_ids)) and all(probe_ids),
            "G2 probe ids are nonempty and unique.",
        ),
        "exact_probe_event_join": _check(
            sorted(probe_ids) == sorted(event_probe_ids),
            "Every admitted G2 probe has exactly one compact event.",
        ),
        "exact_probe_outcome_join": _check(
            sorted(probe_ids) == sorted(outcome_probe_ids),
            "Every admitted G2 probe has exactly one lossless outcome.",
        ),
        "opaque_actions_only": _check(
            all(
                isinstance(item, Mapping)
                and bool(OPAQUE_ACTION.fullmatch(str(item.get("action") or "")))
                for row in probes for item in (row.get("actions") or ())
            ) and bool(probes),
            "All executed G2 probe actions retain opaque ids.",
        ),
        "frame_archive_present": _check(
            bool(event_evidence) and set(event_evidence) <= frame_evidence,
            "Raw frames are archived for every G2 evidence record.",
        ),
    })

    full_coverage = {
        ref: (_site_values(by_evidence[ref], "before"), _site_values(by_evidence[ref], "after"))
        for ref in by_evidence
    }
    witness_ledgers_ok = bool(witnesses) and all(
        full_coverage.get(str(row.get("evidence_id")), (None, None))[0] is not None
        for row in witnesses
    )
    if geometry != "OBSERVED_REWRITE_SUPPORT" and not witness_ledgers_ok:
        findings.append(
            "A full-footprint geometry was claimed without a total site ledger on every "
            "witness; the footprint cannot be recomputed."
        )

    def _witness_ok(index: int, row: Mapping[str, Any]) -> bool:
        cells = _changed_by_rewrite(row, rewrite)
        if index < len(amounts) and len(cells) != amounts[index]:
            return False
        for item in row.get("changed_cells") or ():
            if not isinstance(item, Mapping):
                continue
            cell = (int(item["row"]), int(item["col"]))
            if cell in cells and (
                int(item.get("before")) != source or int(item.get("after")) != replacement
            ):
                return False
        return bool(cells)

    def _conserved(row: Mapping[str, Any], index: int) -> bool:
        before, after = full_coverage.get(str(row.get("evidence_id")), (None, None))
        left = _standing(before, footprint, source, replacement) if pair else None
        right = _standing(after, footprint, source, replacement) if pair else None
        if left is None or right is None:
            return geometry == "OBSERVED_REWRITE_SUPPORT"
        amount = amounts[index] if index < len(amounts) else None
        return (
            amount is not None
            and left[0] - right[0] == amount
            and right[1] - left[1] == amount
        )

    def _footprint_pure(row: Mapping[str, Any]) -> bool:
        before, after = full_coverage.get(str(row.get("evidence_id")), (None, None))
        if before is None or after is None:
            return geometry == "OBSERVED_REWRITE_SUPPORT"
        return all(
            values.get(cell) in (source, replacement)
            for values in (before, after) for cell in footprint
        )

    acted_sites = {
        cell for row in witnesses
        if (cell := _cell(row.get("acted_site"))) is not None
    }
    discovery = _grade({
        "candidate_present": _check(
            bool(candidate) and bool(rewrite) and pair is not None,
            "A structured counter candidate with an integer rewrite is persisted.",
        ),
        "varied_interventions": _check(
            len(witness_refs) >= 2 and len(set(intervention_keys)) >= 2,
            "At least two witnesses under at least two distinct interventions.",
        ),
        "witnesses_resolve": _check(
            len(witnesses) == len(witness_refs) and bool(witness_refs),
            "Every cited witness resolves to a lossless outcome.",
        ),
        "recurrence_recomputed": _check(
            bool(witnesses) and pair is not None
            and all(_witness_ok(i, row) for i, row in enumerate(witnesses)),
            "The exact rewrite recurs on every witness with the recorded amount.",
        ),
        "remote_from_acted_sites": _check(
            bool(witnesses) and not (acted_sites & footprint),
            "No witness acted inside the candidate footprint.",
        ),
        "support_within_footprint": _check(
            bool(support) and support <= footprint,
            "Observed support lies inside the claimed footprint.",
        ),
        "footprint_holds_only_counter_integers": _check(
            bool(witnesses) and all(_footprint_pure(row) for row in witnesses),
            "On every fully-covered witness the footprint holds only the two counter integers.",
        ),
        "conservation_recomputed": _check(
            bool(witnesses) and all(_conserved(row, i) for i, row in enumerate(witnesses)),
            "Source loss equals replacement gain on every fully-covered witness.",
        ),
    })

    explanation = _grade({
        "tracked_variable": _check(
            len(str(answer.get("tracked_variable") or "").split()) >= 3,
            "The tracked visible quantity is explained, not labeled.",
        ),
        "mechanism_and_bookkeeping": _check(
            len(str(answer.get("mechanism") or "").split()) >= 5
            and len(str(answer.get("bookkeeping_reason") or "").split()) >= 5,
            "Both the visible mechanism and the bookkeeping argument are explained.",
        ),
        "alternative_and_falsifier": _check(
            bool(answer.get("competing_models"))
            and len(str(answer.get("falsifier") or "").split()) >= 3,
            "A competing model and a falsifier are preserved.",
        ),
        "explains_active_candidate": _check(
            bool(candidate) and str(answer.get("candidate_id") or "")
            == str(candidate.get("candidate_id") or "x"),
            "The answer explains the active candidate.",
        ),
        "cites_exact_witnesses": _check(
            bool(witness_refs)
            and sorted(str(item) for item in answer.get("evidence_refs") or [])
            == sorted(witness_refs),
            "Evidence references are exactly the candidate witnesses.",
        ),
    })

    demo_purpose = purposes.get(str(demo_event.get("probe_id") or ""), "")
    demo_changed = _cells(demo_outcome.get("changed_cells"))
    demo_acted = _cell(demo_outcome.get("acted_site"))
    prediction_grade = _grade({
        "prospective_claim_persisted": _check(
            bool(prediction)
            and str(prediction.get("candidate_id") or "")
            == str(candidate.get("candidate_id") or "x"),
            "The prediction was journaled with the accepted answer.",
        ),
        "predicts_candidate_rewrite": _check(
            str(prediction.get("expected_rewrite") or "") == rewrite
            and int(prediction.get("expected_amount") or -1) in amounts,
            "The frozen prediction names the candidate rewrite at an observed rate.",
        ),
        "declared_before_observation": _check(
            bool(comparison)
            and int(comparison.get("transition_id") or -1)
            > int(prediction.get("declared_at_transition") or 1 << 60),
            "The prediction precedes the transition that graded it.",
        ),
        "comparison_supported_at_rate": _check(
            comparison.get("outcome") == "SUPPORTED"
            and int(comparison.get("observed_amount") or -1)
            == int(prediction.get("expected_amount") or -2),
            "The prospective comparison was SUPPORTED at the expected amount.",
        ),
        "demonstration_probe_purpose": _check(
            demo_purpose == "DEMONSTRATE",
            "The confirming transition came from a DEMONSTRATE probe.",
        ),
        "confirmation_counter_only": _check(
            bool(demo_outcome) and bool(mask)
            and bool(demo_changed) and demo_changed <= mask
            and (demo_acted is None or demo_acted not in mask),
            "The confirming action changed only masked cells and did not target the counter.",
        ),
    })

    counter_model = next(
        (row.get("counter_model") for row in reversed(events)
         if isinstance(row.get("counter_model"), dict)),
        {},
    ) or {}
    baseline_lock = _grade({
        "stable_baseline_status": _check(
            str(counter_model.get("status") or "") in {
                "LOCKED_AS_MASK_BASELINE", "LOCKED_BY_EXTREMUM_BOUNDARY"
            },
            "The supported recurrence is locked as the stable subtraction baseline.",
        ),
        "gate_closed": _check(
            last_status == "CLOSED",
            "G2 closed after its prospective recurrence demonstration.",
        ),
        "mask_law_present_and_bound": _check(
            bool(mask) and str(mask_law.get("rewrite") or "") == rewrite
            and str(mask_law.get("demonstration_ref") or "")
            == str(comparison.get("evidence_ref") or "x")
            and str(mask_law.get("reversibility") or "")
            == "RAW_GRID_PRESERVED_MASK_IS_DERIVED_VIEW",
            "The mask law matches the rewrite, binds the demonstration, and is a derived view.",
        ),
        "mask_covers_footprint": _check(
            bool(mask) and footprint <= mask,
            "The mask covers the complete inferred footprint, not only the moved front.",
        ),
    })

    partition_ok = True
    counter_only_shared = True
    world_change_distinct = True
    in_mask_legal = True
    covered = 0
    for row in outcomes:
        before, after = full_coverage.get(str(row.get("evidence_id")), (None, None))
        if before is None or after is None or not mask:
            continue
        covered += 1
        raw_delta = {cell for cell in before if before[cell] != after[cell]}
        hud = raw_delta & mask
        world = raw_delta - mask
        if hud | world != raw_delta or hud & world:
            partition_ok = False
        same_view = _masked_view(before, mask) == _masked_view(after, mask)
        if not world and raw_delta and not same_view:
            counter_only_shared = False
        if world and same_view:
            world_change_distinct = False
        for cell in hud:
            arc = (before[cell], after[cell])
            if arc != (source, replacement) and arc != (replacement, source):
                in_mask_legal = False
    both_classes_seen = any(
        (standing := _standing(
            full_coverage.get(str(row.get("evidence_id")), (None, None))[1],
            footprint, source, replacement,
        )) is not None and standing[0] > 0 and standing[1] > 0
        for row in outcomes
    ) if pair else False
    mask_and_state = _grade({
        "recomputable_transitions_exist": _check(
            covered >= 2,
            "At least two G2 transitions carry the total site ledger for recomputation.",
        ),
        "exact_partition": _check(
            partition_ok,
            "Raw delta partitions exactly into disjoint HUD and world cells.",
        ),
        "counter_only_shares_world_address": _check(
            counter_only_shared,
            "Counter-only transitions leave the masked world view identical.",
        ),
        "world_change_stays_visible": _check(
            world_change_distinct,
            "Outside-mask change always changes the masked world view.",
        ),
        "no_causal_change_inside_mask": _check(
            in_mask_legal,
            "Every in-mask change is the counter exchange or its respawn reversal.",
        ),
        "mask_covers_both_objects": _check(
            both_classes_seen,
            "Both integer classes were observed inside the mask together; the mask is "
            "not one-sided.",
        ),
    })

    if review is not None:
        verdicts = review.get("verdicts") if isinstance(review.get("verdicts"), dict) else {}
        reviewed_refs = {str(item) for item in review.get("evidence_refs_reviewed") or []}
        required_refs = set(witness_refs)
        for ref in (comparison.get("evidence_ref"),):
            if ref:
                required_refs.add(str(ref))
        checks = {
            "reviewer": _check(
                bool(str(review.get("reviewer") or "").strip()),
                "Reviewer identity is recorded.",
            ),
            "reviewed_at": _check(
                bool(str(review.get("reviewed_at") or "").strip()),
                "Review time is recorded.",
            ),
            "evidence_reviewed": _check(
                bool(reviewed_refs) and required_refs <= reviewed_refs,
                "Review names every witness and demonstration record inspected.",
            ),
        }
        for name in REVIEW_VERDICTS:
            checks[name] = _check(
                verdicts.get(name) is True, f"Reviewer confirms {name.replace('_', ' ')}."
            )
        correctness = _grade(checks)
    else:
        correctness = _grade({
            "human_review": _check(
                False, "A human must inspect the supplied frames and claims."
            )
        }, pending=True)

    grades = {
        "protocol": protocol,
        "discovery": discovery,
        "explanation": explanation,
        "prediction": prediction_grade,
        "baseline_lock": baseline_lock,
        "mask_and_state": mask_and_state,
        "correctness": correctness,
    }
    packet = {
        "answer": answer or None,
        "candidate": candidate or None,
        "pending_prediction": prediction or None,
        "comparison": comparison or None,
        "boundary": boundary or None,
        "mask_law": mask_law or None,
        "witness_outcomes": witnesses,
        "demonstration_outcome": demo_outcome or None,
        "boundary_outcome": boundary_outcome or None,
        "frames": frames,
        "review_questions": list(REVIEW_QUESTIONS),
    }
    return grades, packet, findings


def evaluate(
    run_dir: Path,
    expected_games: list[str] | None = None,
    *,
    receipt_path: Path | None = None,
    human_review_path: Path | None = None,
) -> dict[str, Any]:
    artifacts = run_dir / "artifacts" if (run_dir / "artifacts").is_dir() else run_dir
    discovered = _stems(artifacts)
    if expected_games:
        stems = [
            next((s for s in discovered if _world_matches(s, game)), f"{game}_p0")
            for game in expected_games
        ]
    else:
        stems = discovered

    receipt_path = _resolve_optional(run_dir, receipt_path, "execution_receipt.json")
    receipt = _execution_receipt(receipt_path, stems, expected_games)
    human_review_path = _resolve_optional(run_dir, human_review_path, "human_review.json")
    review_header, review_by_game = _reviews(human_review_path, receipt.get("sha256"))

    games: list[dict[str, Any]] = []
    review_packets: list[dict[str, Any]] = []
    for stem in stems:
        answers = _rows(artifacts / f"{stem}_gate_answers.jsonl")
        probes = _rows(artifacts / f"{stem}_probe_envelopes.jsonl")
        events = _rows(artifacts / f"{stem}_gate_events.jsonl")
        outcomes = _rows(artifacts / f"{stem}_probe_outcomes.jsonl")
        frames = _rows(artifacts / f"{stem}_probe_frames.jsonl")
        g2_answers = [row for row in answers if row.get("gate_id") == GATE_ID]
        g2_probes = [row for row in probes if row.get("gate_id") == GATE_ID]
        g2_events = [row for row in events if row.get("gate_id") == GATE_ID]
        g2_outcomes = [
            row for row in outcomes
            if str(row.get("probe_id") or "").startswith(f"{GATE_ID}:")
        ]
        g2_frames = [
            row for row in frames
            if str(row.get("probe_id") or "").startswith(f"{GATE_ID}:")
        ]
        counts = {
            "answers": len(g2_answers), "probes": len(g2_probes),
            "events": len(g2_events), "outcomes": len(g2_outcomes),
            "frames": len(g2_frames),
        }
        g1_closed = _g1_closed(answers)
        disposition, reason = _g2_disposition(
            g2_probes or g2_answers, g2_events, g1_closed
        )
        if disposition is not None:
            games.append({
                "game": stem, **counts,
                "disposition": disposition,
                "disposition_reason": reason,
                "g1_closed": g1_closed,
                "passed": False,
            })
            continue

        review = review_by_game.get(stem)
        grades, packet, findings = _g2_grades(
            g2_answers, g2_probes, g2_events, g2_outcomes, g2_frames, review
        )
        automated_names = (
            "protocol", "discovery", "explanation",
            "prediction", "baseline_lock", "mask_and_state",
        )
        automated = all(grades[name]["status"] == "PASS" for name in automated_names)
        satisfied = automated and grades["correctness"]["status"] == "PASS"
        gap = any(
            "cannot be recomputed" in item for item in findings
        ) or not grades["mask_and_state"]["checks"][
            "recomputable_transitions_exist"
        ]["passed"]
        games.append({
            "game": stem, **counts,
            "disposition": (
                "PASS" if satisfied
                else "REPRESENTATION_GAP" if gap and not automated
                else "FAIL" if not automated
                else "REVIEW_REQUIRED"
            ),
            "disposition_reason": reason,
            "g1_closed": g1_closed,
            "grades": grades,
            "automated_acceptance": automated,
            "g2_satisfied": satisfied,
            "findings": findings,
            "passed": satisfied,
        })
        review_packets.append({"game": stem, **packet})

    unexpected = [stem for stem in discovered if stem not in stems] if expected_games else []
    receipt_pass = receipt["status"] == "PASS"
    passed = (
        bool(games) and not unexpected and receipt_pass
        and all(game["passed"] for game in games)
    )
    return {
        "schema": REPORT_SCHEMA,
        "stage": "G2",
        "run_dir": str(run_dir),
        "expected_games": expected_games or [],
        "unexpected_artifact_games": unexpected,
        "execution_receipt": receipt,
        "human_review": review_header,
        "games": games,
        "passed": passed,
        "human_review_required": any(
            game.get("grades", {}).get("correctness", {}).get("status") != "PASS"
            for game in games if "grades" in game
        ),
        "review_packet": {
            "schema": PACKET_SCHEMA,
            "execution_receipt_sha256": receipt.get("sha256"),
            "games": review_packets,
        },
        "claim_limit": (
            "Automated grades establish protocol, recomputed counter arithmetic, "
            "prospectivity, boundary locking, and mask/state invariants over executed "
            "artifacts. Only a receipt-bound human frame review can establish that the "
            "tracked variable, footprint scope, and bookkeeping interpretation are "
            "semantically correct. A PASS here is never a level-completion or "
            "lever-understanding claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-packet-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--human-review", type=Path)
    parser.add_argument("--expected-game", action="append", default=[])
    args = parser.parse_args()
    report = evaluate(
        args.run_dir.resolve(),
        args.expected_game or None,
        receipt_path=args.receipt,
        human_review_path=args.human_review,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    if args.review_packet_output and report.get("review_packet"):
        args.review_packet_output.write_text(
            json.dumps(report["review_packet"], indent=2, sort_keys=True) + "\n"
        )
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
