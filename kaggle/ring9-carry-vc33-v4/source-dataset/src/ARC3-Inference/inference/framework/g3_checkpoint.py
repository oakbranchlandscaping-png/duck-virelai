"""Offline evaluator for a served G3 cybernetic checkpoint trace.

The evaluator grades only G3 products.  It never uses game score, a claimed win,
or prose alone as evidence of a lever or a G4 handoff.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


ALLOWED_TERMINAL_STATES = frozenset({"G3-CLOSED", "G4-READY"})


@dataclass(frozen=True)
class G3CheckpointCertificate:
    schema: str
    status: str
    world_type: str | None
    arm: str | None
    checks: tuple[Mapping[str, Any], ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _events(trace: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for item in trace:
        if not isinstance(item, Mapping):
            continue
        row = item.get("event")
        rows.append(row if isinstance(row, Mapping) else item)
    return rows


def _check(name: str, passed: bool, reason: str, *, evidence: Iterable[str] = ()) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "reason": reason,
        "evidence_refs": [str(ref) for ref in evidence if str(ref)],
    }


def evaluate_g3_checkpoint(
    trace: Iterable[Mapping[str, Any]],
    *,
    world_type: str | None = None,
    final_snapshot: Mapping[str, Any] | None = None,
) -> G3CheckpointCertificate:
    """Grade a completed G3 trace against the live checkpoint contract."""
    rows = _events(trace)
    snapshot = final_snapshot or {}
    scheduler = snapshot.get("scheduler") if isinstance(snapshot.get("scheduler"), Mapping) else {}
    inferred_world = str(world_type or snapshot.get("world_type") or "").upper() or None
    arm = {
        "CLICK_GOD_MODE": "CLICK",
        "NAVIGATION": "NAV",
        "HYBRID": "HYBRID",
    }.get(inferred_world)
    checks: list[dict[str, Any]] = []
    evidence_refs: list[str] = []

    checks.append(_check(
        "metadata_world_type_arm",
        inferred_world in {"CLICK_GOD_MODE", "NAVIGATION", "HYBRID"} and arm is not None,
        "metadata must select one supported G3 world arm",
    ))

    frontier = (
        snapshot.get("inherited_frontier")
        if isinstance(snapshot.get("inherited_frontier"), Mapping) else {}
    )
    candidates = frontier.get("candidates") if isinstance(frontier.get("candidates"), list) else []
    exclusions = (
        frontier.get("excluded_candidates")
        if isinstance(frontier.get("excluded_candidates"), list) else []
    )
    original_count = int(frontier.get("original_candidate_count") or 0)
    source_ranks = sorted(
        int(item.get("source_rank") or 0)
        for item in candidates + exclusions
        if isinstance(item, Mapping)
    )
    eligible_ranks = sorted(
        int(item.get("eligible_rank") or 0)
        for item in candidates
        if isinstance(item, Mapping)
    )
    mask_version = str(frontier.get("mask_law_version_id") or "")
    exclusion_rows_valid = all(
        isinstance(item, Mapping)
        and str(item.get("disposition") or "") == "COUNTER_ROLE_EXCLUDED"
        and bool(item.get("member_id"))
        and int(item.get("source_rank") or 0) > 0
        and str(item.get("mask_law_version_id") or "") == mask_version
        and bool(item.get("evidence_refs"))
        for item in exclusions
    )
    frontier_ok = (
        frontier.get("schema") == "virelai-g3-mask-filtered-frontier-v1"
        and bool(mask_version)
        and str(snapshot.get("mask_law_ref") or "") == mask_version
        and bool(frontier.get("accounting_complete"))
        and original_count == len(candidates) + len(exclusions)
        and int(frontier.get("candidate_count") or 0) == len(candidates)
        and int(frontier.get("excluded_candidate_count") or 0) == len(exclusions)
        and source_ranks == list(range(1, original_count + 1))
        and eligible_ranks == list(range(1, len(candidates) + 1))
        and exclusion_rows_valid
    )
    checks.append(_check(
        "counter_role_frontier_accounting",
        frontier_ok,
        "every frozen G2 object must be scheduled once or explicitly excluded by the same sealed counter law",
        evidence=(
            str(ref)
            for item in exclusions if isinstance(item, Mapping)
            for ref in item.get("evidence_refs", ())
        ),
    ))

    target_rows = [row for row in rows if row.get("gate_id") == "G3-LEVERS" and row.get("target")]
    ordered_rows = [
        row for row in target_rows
        if str(row.get("probe_id") or "").find(":CONFIRM:") < 0
    ]
    ranks = [int((row.get("target") or {}).get("rank") or 0) for row in ordered_rows]
    ranking_ok = bool(target_rows) and all(rank > 0 for rank in ranks)
    if arm == "HYBRID" and ranking_ok:
        click = [int((row.get("target") or {}).get("rank") or 0) for row in ordered_rows if row.get("scheduler", {}).get("phase") == "CLICK"]
        nav = [int((row.get("target") or {}).get("rank") or 0) for row in ordered_rows if row.get("scheduler", {}).get("phase") == "NAV"]
        ranking_ok = click == list(range(1, len(click) + 1)) and nav == list(range(1, len(nav) + 1))
    elif ranking_ok:
        ranking_ok = ranks == list(range(1, len(ranks) + 1))
    checks.append(_check(
        "strict_target_ranking",
        ranking_ok,
        "target ranks must be contiguous in the selected arm; HYBRID must reset only at its NAV arm",
        evidence=[str(row.get("evidence_id") or "") for row in target_rows],
    ))
    evidence_refs.extend(str(row.get("evidence_id") or "") for row in target_rows)

    attribution_rows = [row for row in target_rows if isinstance(row.get("attribution"), Mapping)]
    mask_ok = bool(attribution_rows) and all(
        "counter_masked_cells" in row["attribution"]
        and (row.get("counter_baseline") or {}).get("policy") == "MASK_AND_IGNORE_AFTER_G2"
        for row in attribution_rows
    )
    checks.append(_check(
        "counter_masked_and_ignored",
        mask_ok and bool(snapshot.get("mask_law_ref") or snapshot.get("mask_law")),
        "every attributed transition must expose counter masking and the stable ignore policy",
    ))

    dossier_ok = bool(target_rows) and all(
        (row.get("target") or {}).get("entity_id") and isinstance(row.get("dossier"), Mapping)
        for row in target_rows
    )
    checks.append(_check(
        "persistent_entity_dossiers",
        dossier_ok,
        "each scheduled target must retain an entity id and evidence dossier",
    ))

    positive_refs = {
        str(row.get("evidence_id") or "")
        for row in attribution_rows
        if ":CONFIRM:" not in str(row.get("probe_id") or "")
        if str((row.get("attribution") or {}).get("disposition") or "") in {
            "LOCAL_LEVER_WITNESS", "REMOTE_LEVER_WITNESS", "LOCAL_AND_REMOTE_LEVER_WITNESS",
        }
    }
    confirmations = [row for row in rows if row.get("confirmation")]
    graded_refs = {
        str((row.get("confirmation") or {}).get("witness_evidence_ref") or "")
        for row in confirmations
        if (row.get("confirmation") or {}).get("status") in {
            "SUPPORTED", "CONTRADICTED", "BOUNDARY_DEFERRED",
        }
    }
    answers = (snapshot.get("attribution_contract") or {}).get("dossier_answers", [])
    answered_refs = {
        str(ref)
        for answer in answers
        if isinstance(answer, Mapping)
        for ref in answer.get("evidence_refs", ())
    }
    explanation_ok = bool(positive_refs) and positive_refs <= graded_refs and positive_refs <= answered_refs
    checks.append(_check(
        "witness_confirmation_and_explanation",
        explanation_ok,
        "every positive witness must have a graded later confirmation and an evidence-bound Duck dossier",
        evidence=sorted(positive_refs),
    ))

    typed_dossiers_ok = bool(answers) and all(
        isinstance(answer, Mapping)
        and str(answer.get("answer_kind") or "") == "LEVER_DOSSIER"
        and bool(answer.get("target_member_id"))
        and isinstance(answer.get("intervention"), Mapping)
        and bool(answer.get("intervention"))
        and isinstance(answer.get("competing_models"), (list, tuple))
        and not isinstance(answer.get("competing_models"), str)
        and bool(answer.get("competing_models"))
        and isinstance(answer.get("effect_summary"), Mapping)
        and answer["effect_summary"].get("schema") == "virelai-g3-effect-summary-v1"
        and answer["effect_summary"].get("causal_scope") == "NON_COUNTER_RESIDUE_ONLY"
        and answer["effect_summary"].get("counter_treatment")
        == "COUNTER_CHANGES_EXCLUDED_FROM_LEVER_CAUSALITY"
        for answer in answers
    )
    checks.append(_check(
        "typed_mask_consistent_dossiers",
        typed_dossiers_ok,
        "each lever explanation must bind the confirmed intervention to the exact counter-masked effect summary",
        evidence=sorted(answered_refs),
    ))

    prospective_ok = bool(confirmations) and bool(positive_refs)
    for row in confirmations:
        confirmation = row.get("confirmation") or {}
        declared = int(confirmation.get("declared_at_transition") or -1)
        graded = int(confirmation.get("graded_at_transition") or -1)
        if declared < 0 or graded <= declared:
            prospective_ok = False
            break
    checks.append(_check(
        "strict_prospectivity",
        prospective_ok,
        "every confirmation transition must occur strictly after its frozen declaration",
        evidence=[str(row.get("evidence_id") or "") for row in confirmations],
    ))

    complete = scheduler.get("complete_reason") in {"CLICK_ENUMERATION_COMPLETE", "NAV_ENUMERATION_COMPLETE"}
    checks.append(_check(
        "enumeration_completion",
        complete and scheduler.get("pending_confirmation") is None,
        "the sweep must finish only after confirmation obligations are empty",
    ))

    attribution_contract = (
        snapshot.get("attribution_contract")
        if isinstance(snapshot.get("attribution_contract"), Mapping) else {}
    )
    inventory = attribution_contract.get("inventory_answer")
    inventory_subjects = {
        str(item) for item in (inventory or {}).get("subjects", ())
    } if isinstance(inventory, Mapping) else set()
    checks.append(_check(
        "accepted_lever_inventory",
        snapshot.get("status") == "SATISFIED"
        and isinstance(inventory, Mapping)
        and str(inventory.get("answer_kind") or "") == "LEVER_INVENTORY"
        and bool(inventory_subjects),
        "the exhaustive probe protocol must produce an accepted evidence-bound LeverInventory",
        evidence=(inventory or {}).get("evidence_refs", ()) if isinstance(inventory, Mapping) else (),
    ))

    unresolved_honest = all(
        not bool((row.get("attribution") or {}).get("inertness_claim_permitted"))
        for row in attribution_rows
    )
    checks.append(_check(
        "unresolved_effects_deferred",
        unresolved_honest,
        "null, ambiguous, and boundary observations must not become inertness claims",
    ))

    win_claimed = any(
        bool(row.get("win_guessed") or row.get("win_claimed"))
        or str(row.get("disposition") or "").upper() == "WIN_GUESSED"
        for row in rows
    )
    checks.append(_check("no_win_guessed", not win_claimed, "G3 grades exploration products, never a guessed win"))

    lifecycle = snapshot.get("lifecycle_journal") if isinstance(snapshot.get("lifecycle_journal"), Mapping) else {}
    lifecycle_entities = lifecycle.get("entities") or {}
    targeted_entity_ids = {
        str((row.get("target") or {}).get("entity_id") or "") for row in target_rows
        if str((row.get("target") or {}).get("entity_id") or "")
    }
    states = [
        str((lifecycle_entities.get(entity_id) or {}).get("state") or "")
        for entity_id in sorted(targeted_entity_ids)
    ]
    handoff_ok = bool(states) and all(state in ALLOWED_TERMINAL_STATES for state in states)
    g4_ready = {
        entity_id for entity_id, item in lifecycle_entities.items()
        if str((item or {}).get("state") or "") == "G4-READY"
    }
    supported_handoff_ok = bool(g4_ready) and g4_ready == inventory_subjects and all(
        bool((lifecycle_entities.get(entity_id) or {}).get("witness_refs"))
        and bool((lifecycle_entities.get(entity_id) or {}).get("answer_refs"))
        for entity_id in g4_ready
    )
    checks.append(_check(
        "g4_handoff_certificate",
        handoff_ok and supported_handoff_ok,
        "every probed entity must close cleanly, and every inventory lever must have witness plus explanation before G4",
    ))

    limitations = (
        "This certificate grades a supplied trace and snapshot; it does not establish that the trace came from a served model.",
        "Game score and level completion are outside G3 scope.",
    )
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return G3CheckpointCertificate(
        schema="virelai-g3-checkpoint-certificate-v1",
        status=status,
        world_type=inferred_world,
        arm=arm,
        checks=tuple(checks),
        evidence_refs=tuple(dict.fromkeys(ref for ref in evidence_refs if ref)),
        limitations=limitations,
    )


__all__ = ["G3CheckpointCertificate", "evaluate_g3_checkpoint"]
