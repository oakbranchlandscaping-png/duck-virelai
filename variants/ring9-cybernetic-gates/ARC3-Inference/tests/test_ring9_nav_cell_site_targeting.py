"""Production-shaped checks for the G1-to-G3 NAV targeting handoff.

The fixture is the unified ls20 Kaggle canary. Duck correctly described four
motions there but supplied only two representative ego sites and no structured
action laws. The controller must recover the whole moving cell-site family and
begin draining G3's ranked object roster without another Duck turn.

Author: Sol (Alpha build seat), 2026-10-06.
"""
from pathlib import Path

from inference.framework.controller_executor import next_owned_step
from inference.framework.nav_control import compile_nav_control_map
from inference.framework.record_replay import load_record, replay


FIXTURE = Path(__file__).parent / "fixtures" / "ls20_kaggle_unified_v1_record.json.gz"


def test_live_g1_cell_flow_recovers_complete_ego_and_all_bearings():
    result = replay(load_record(FIXTURE), max_steps=12, measure=False)

    assert result.stopped is None and result.machine.gate_id == "G3-LEVERS"
    control = compile_nav_control_map(result.machine.ego)
    assert control.bearing_map() == {
        "ACTION1": (-5, 0),
        "ACTION2": (5, 0),
        "ACTION3": (0, -5),
        "ACTION4": (0, 5),
    }
    assert control.unresolved_actions == ()
    assert len(control.ego_cells) == 25
    assert control.binding_source == "DETERMINISTIC_CELL_SITE_TRANSLATION"
    cells, source = result.machine.ego.embodied_ego_binding()
    assert cells == control.ego_cells
    assert source == control.binding_source


def test_live_g3_roster_resolves_identity_to_current_sites_and_moves_without_duck():
    result = replay(load_record(FIXTURE), max_steps=12, measure=False)
    adapter = result.machine._adapters["G3-LEVERS"]
    capability = result.machine.next_probe_capability()

    assert capability["purpose"] == "PILOT_TO_LEVER_CONTACT"
    target = capability["target"]
    assert target["geometry_source"] == "CURRENT_ENTITY_SIGHTING"
    assert target["cell_count"] == len(target["cells"])
    assert target["anchor"] == min(target["cells"])
    entity = adapter.entity_ledger.entities[target["entity_id"]]
    assert tuple(map(tuple, target["cells"])) == entity.current.cells

    owned = next_owned_step(result.machine)
    assert owned.owner == "CONTROLLER"
    assert owned.kind == "ACTION"
    assert owned.decision["pilot_intent"] in {"APPROACH", "CONTACT_ATTEMPT"}
    assert owned.action["action"] in {"ACTION1", "ACTION2", "ACTION3", "ACTION4"}
