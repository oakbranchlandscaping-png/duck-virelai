"""An object that changes colour in place keeps its identity; G3 can then witness it as a lever.

Author: Claude (Alpha build seat), 2026-09-28.

Found offline while preparing ring9-g4-ft09-guided-v2, before any live run. On the real ft09
record, each control is a 6x6 tile that toggles between two colours when clicked, and the board
holds other 6x6 tiles of both colours. The entity ledger treated every unchanged same-shape,
same-colour tile elsewhere as a possible translation source for the recoloured tile, so the
recolour became an ambiguous birth and the control's identity was lost. At G3 the control's
member had no cells, pointer ownership could not resolve, and both controls filed as
UNRESOLVED_ATTRIBUTION: G3 would have closed with zero levers, and G4 could not open.

The contract (CONTRACT_G3_ENTITY_LIFECYCLE_v1 §1, BUILD_SLICE_G3_ENTITY_OBSERVATION_ADAPTER) already
requires identity to survive a recolour, and requires a genuine ambiguity to abstain rather than
be silently assigned. Two exact structural rules restore both:

1. A prior entity whose exact (integer, cells) key is still present in the after frame is STILL;
   it cannot also be the source of a translation.
2. When a same-footprint predecessor and a translation source both remain, the match abstains
   (AMBIGUOUS) instead of silently choosing the translation.
"""
from __future__ import annotations

from inference.framework.entity_observation import EntityLedger
from test_bounded_cards import _close_g2_on_ft09
from test_entity_observation import transition
from test_g2_counter_axiom import _outcome

# Two 1x2 tiles: A (colour 9) at row 0, B (colour 8) at row 2; background 4.
BEFORE = ((9, 9, 4), (4, 4, 4), (8, 8, 4))


def test_recolour_in_place_keeps_identity_when_a_same_shape_tile_of_the_new_colour_stays_put():
    ledger = EntityLedger(BEFORE)
    a = ledger.entity_at((0, 0))
    b = ledger.entity_at((2, 0))
    after = ((8, 8, 4), (4, 4, 4), (8, 8, 4))
    result = ledger.observe(transition(BEFORE, after))
    assert (a, "RECOLOR", "PRESENT") in result.relations
    assert (b, "STILL", "PRESENT") in result.relations
    assert ledger.cells_for(a) == ((0, 0), (0, 1))
    assert not any(item.ambiguity_refs for item in ledger.entities.values())


def test_recolour_and_toggle_back_keep_one_identity():
    ledger = EntityLedger(BEFORE)
    a = ledger.entity_at((0, 0))
    once = ((8, 8, 4), (4, 4, 4), (8, 8, 4))
    ledger.observe(transition(BEFORE, once))
    ledger.observe(transition(once, BEFORE, transition_id=2))
    assert ledger.entity_at((0, 0)) == a
    assert ledger.entities[a].status == "PRESENT"


def test_recolour_versus_a_vanished_translation_source_abstains():
    """A vanished and an 8-tile appeared where A was, while B also vanished: A recoloured, or B moved."""
    ledger = EntityLedger(BEFORE)
    a = ledger.entity_at((0, 0))
    b = ledger.entity_at((2, 0))
    after = ((8, 8, 4), (4, 4, 4), (4, 4, 4))
    result = ledger.observe(transition(BEFORE, after))
    relations = {entity: relation for entity, relation, _ in result.relations}
    assert relations.get(a) != "RECOLOR" and relations.get(b) != "MOVE"
    assert any(relation == "AMBIGUOUS" for _, relation, _ in result.relations)


def _control_click(grid, action):
    """The recorded ft09 control law, continued: a control tile toggles 9<->8 and the bar ticks."""
    for r0, c0 in ((36, 36), (36, 44)):
        if r0 <= action["row"] < r0 + 6 and c0 <= action["col"] < c0 + 6:
            before = grid[r0][c0]
            after = 8 if before == 9 else 9
            changed = [[r, c, before, after] for r in range(r0, r0 + 6) for c in range(c0, c0 + 6)]
            twelves = sorted(c for c in range(64) if grid[63][c] == 12)[-2:]
            return changed + [[63, c, 12, 11] for c in twelves]
    return []


def test_ft09_controls_keep_their_g2_member_identity_at_g3_entry():
    machine, _grid = _close_g2_on_ft09()
    ledger = machine._adapters["G3-LEVERS"]._ensure_entity_ledger()
    for member, anchor in (("M0040", (36, 36)), ("M0041", (36, 44))):
        entity = ledger.entity_for_member(member)
        assert ledger.entities[entity].status == "PRESENT", member
        assert len(ledger.cells_for(entity)) == 36, member
        assert ledger.entity_at(anchor) == entity, member


def test_ft09_g3_sweep_witnesses_both_controls_as_levers():
    machine, grid = _close_g2_on_ft09()
    transition_id = 58
    dispositions = {}
    while machine.gate_id == "G3-LEVERS":
        capability = machine.next_probe_capability()
        if capability is None:
            break
        action = capability["actions"][0]
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [action])
        grid, outcome = _outcome(grid, transition_id, action, _control_click(grid, action))
        event = machine.record_outcome(probe, outcome)
        if event.get("attribution"):
            dispositions.setdefault(
                (action["row"], action["col"]), []
            ).append(event["attribution"]["disposition"])
        transition_id += 1
        if machine.gate_view().get("status") == "ANSWER_REQUIRED" and machine.gate_view().get(
            "schema"
        ) != "virelai-g3-completion-card-v1":
            template = machine.gate_view()["answer_template"]
            machine.submit_answer({
                **template,
                "explanation": (
                    "Clicking this tile rewrites the tile's own colour in place; the bottom bar "
                    "counter changes were excluded by the mask as bookkeeping."
                ),
                "competing_models": ["A hidden process changed the tile at the same moment."],
                "falsifier": "A repeat click leaves the tile unchanged.",
            })
    for anchor in ((36, 36), (36, 44)):
        assert dispositions[anchor][0] == "LOCAL_LEVER_WITNESS", (anchor, dispositions[anchor])
    view = machine.gate_view()
    assert view["schema"] == "virelai-g3-completion-card-v1"
    assert view["confirmed_levers"]["total"] == 2
    assert len(view["answer_template"]["lever_entities"]) == 2
    assert view["bounded_unknowns"]["total"] == 0
