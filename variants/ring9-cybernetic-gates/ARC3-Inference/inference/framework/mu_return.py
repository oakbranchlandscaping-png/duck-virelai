"""Filing to the mu bucket and returning to it when stuck (R9-R23, D12-D15).

Author: Claude (Alpha build seat), 2026-10-03. RULING_MU_BUCKET_v1_2026-10-03 (Director-ruled).

G3 files every bounded ambiguity into the level's ``MuBucket`` with the counter-masked board it was tried
on and the entity that owned the clicked cell. When the ladder is otherwise stuck, ``return_to_mu``
retries only the entries whose board has changed (M-4): an entry whose object no longer occupies any
cell is settled ABSENT; the rest reopen G3, which clicks each object where it is now. A positive retry
follows G3's ordinary witness, repeat and dossier path; G3 then re-emits its inventory, G4.1 and G4-A
keep what they have and take the late lever, and Phase 2 (G4-B, G4-C) restarts on the larger lever set.
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework.masked_world_state import grids_from_probe_outcome, raw_address, world_address
from inference.framework.mu_bucket import ABSENT, RESOLVED_LEVER, RESOLVED_NULL

LEVERS = "G3-LEVERS"


def _address(grid: Any, machine: Any) -> str | None:
    if grid is None:
        return None
    rows = tuple(tuple(int(cell) for cell in row) for row in grid)
    law = machine.counter.mask_law
    return raw_address(rows) if law is None else world_address(rows, law)


def world_address_now(machine: Any) -> str | None:
    from inference.framework.card_builder import _current_grid

    return _address(_current_grid(machine), machine)


def seeded(adapter: Any, upstream_gate_id: str) -> bool:
    """Whether a G4 adapter already holds its upstream product's lever set (D15)."""
    if not adapter._ordered_entities:
        return False
    product = adapter.machine.target_journal.active_product(upstream_gate_id)
    return product is None or product.product_id == adapter._seeded_from


def after_g3_outcome(g3: Any, probe: Any, event: Mapping[str, Any], lossless: Mapping[str, Any], owner: str | None) -> None:
    """File a new bounded ambiguity into mu (D12); a finished mu retry leaves the revisit queue (D14)."""
    record = event.get("bounded_ambiguity")
    if record:
        grids = grids_from_probe_outcome(lossless)
        g3.machine.mu.file(
            record, gate_id=LEVERS, tried_address=None if grids is None else _address(grids[0], g3.machine),
            transition_id=int(lossless.get("transition_id") or 0), clicked_owner=owner,
        )
    entity_id = str((probe.target or {}).get("entity_id") or "")
    if probe.purpose == "MU_REVISIT" and entity_id in g3._mu_revisit:
        g3._mu_revisit.remove(entity_id)


def settle_after_inventory(g3: Any) -> None:
    """An accepted inventory settles the mu entries G3 has since answered."""
    journal = g3.lifecycle_journal
    for entity_id in g3.machine.mu.entity_ids():
        state = journal.entities[entity_id].state if journal is not None and entity_id in journal.entities else None
        if state == "G4-READY":
            g3.machine.mu.settle(entity_id, RESOLVED_LEVER, "a retry on a changed board witnessed and certified it")
        elif state == "G3-CLOSED" and not journal.entities[entity_id].witness_refs:
            g3.machine.mu.settle(entity_id, RESOLVED_NULL, "a retry on a changed board closed it with scoped null evidence")


def _owned_cells(ledger: Any, entity_id: str) -> list[tuple[int, int]]:
    return sorted(cell for cell in ledger.cells_for(entity_id) if ledger.entity_at(cell) == entity_id)


def return_to_mu(machine: Any) -> list[str]:
    """Reopen G3 for the mu entries a changed board makes worth retrying; return their entity ids."""
    g3 = machine._adapters[LEVERS]
    if g3._mu_revisit:
        return list(g3._mu_revisit)
    entries = machine.mu.revisitable(world_address_now(machine))
    if not entries:
        return []
    ledger = g3._ensure_entity_ledger()
    retry = []
    for entry in entries:
        if _owned_cells(ledger, entry["entity_id"]):
            retry.append(entry["entity_id"])
        else:
            machine.mu.settle(entry["entity_id"], ABSENT, "the object occupies no cell on the current board")
    if not retry:
        return []
    journal = g3.lifecycle_journal
    for entity_id in retry:
        if journal.entities[entity_id].state == "BUDGET_STOPPED":
            journal.reopen(entity_id, evidence_ref="MU-RETURN", reason="mu return on a changed board")
        g3._bounded_ambiguities.pop(entity_id, None)
    g3._mu_revisit = retry
    g3._complete_reason, g3._inventory_answer, g3._bounded_coverage_answer = None, None, None
    g3.revision += 1
    machine.target_journal.invalidate(LEVERS, include_self=True)
    from inference.framework.g4c_gate import later_adapters

    machine._adapters.update(later_adapters(machine))  # Phase 2 restarts on the larger lever set (M-5)
    return retry


def revisit_probe(g3: Any, ledger: Any, entity_id: str) -> Any:
    """Click a mu object where it is now, at a cell it owns (M-4)."""
    from inference.framework.virelai_gates import ProbeEnvelope

    cells = _owned_cells(ledger, entity_id)
    site = cells[len(cells) // 2]
    entry = g3.machine.mu.entries[entity_id]
    rows, cols = [cell[0] for cell in cells], [cell[1] for cell in cells]
    from inference.framework.card_builder import _current_grid

    grid = _current_grid(g3.machine)
    target = {
        "rank": 0, "eligible_rank": None, "source_rank": None, "member_id": entry["member_id"],
        "entity_id": entity_id, "anchor": list(site), "bbox": [min(rows), min(cols), max(rows), max(cols)],
        "cells": [list(cell) for cell in cells], "integer": None if grid is None else grid[site[0]][site[1]],
        "cell_count": len(cells), "shape_family": "MU_RETURN", "mask_relation": "DISJOINT_FROM_COUNTER",
    }
    return ProbeEnvelope(
        probe_id=f"{LEVERS}:MU:{entity_id}:{len(entry['tries']) + 1}",
        gate_id=LEVERS,
        purpose="MU_REVISIT",
        question="Retry this mystery object on the changed board: does clicking it now produce an attributable response?",
        actions=({"action": "ACTION6", "row": site[0], "col": site[1]},),
        live_alternatives=("local target response", "remote response", "counter-only change", "still unresolved"),
        outcome_partition=("changed", "unchanged", "boundary event"),
        declared_at_transition=g3.machine.observed_through_step,
        target=target,
    )


__all__ = ["after_g3_outcome", "return_to_mu", "revisit_probe", "seeded", "settle_after_inventory", "world_address_now"]
