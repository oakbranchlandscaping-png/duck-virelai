"""The ft09 ladder, offline: real G2 record, then G3, G4.0/G4.1 and G4-A under the recorded law.

Author: Claude (Alpha build seat), 2026-09-28.

The live G2 record of ft09 (57 transitions, Kaggle guided v1) is replayed through G2's closure.
After that the world is simulated by continuing the one law the record shows: clicking a 6x6
control tile toggles it 9<->8 and ticks the bottom bar two cells 12->11; every other click changes
nothing. That continuation is a hypothesis about ft09, not a fact; this test proves only that the
controller can carry such a world from G2 to a satisfied G4-A. Duck is replaced by the simplest
policy the cards allow: fill each answer template, and press the first unfinished lever.

It pins three things before the next live run:
- G3 witnesses both controls as levers (R9-R05: recolour keeps identity);
- every binding card at every gate fits the runtime budget (axiom A6);
- the whole ladder fits the 200-action budget with room to spare.
"""
from __future__ import annotations

from test_bounded_cards import BUDGET, _binding_context_chars, _close_g2_on_ft09
from test_g2_counter_axiom import _outcome
from test_g3_recolor_identity import _control_click

G2_ACTIONS = 57
ACTION_BUDGET = 200
COUNTER_WORDS = "the bottom bar counter changes were excluded by the mask as bookkeeping"


def _answer(machine, view):
    schema = view.get("schema")
    if view.get("answer_templates"):
        template = view["answer_templates"][0]
        machine.submit_answer({
            **template,
            "mechanism_explanation": (
                "Consecutive presses toggled this tile between two colours and back: a period-two "
                "orbit at the observed states."
            ),
            "competing_models": ["The lever may respond differently from another world state."],
            "falsifier": "A repeat from this exact masked state later behaves differently.",
        })
        return
    template = view["answer_template"]
    assert template is not None, f"{machine.gate_id} demands an answer without a template"
    if schema == "virelai-g3-completion-card-v1":
        machine.submit_answer({
            **template,
            "explanation": f"The complete click roster found two self-recolouring tiles; {COUNTER_WORDS}.",
            "competing_models": ["The responses were spontaneous."],
            "falsifier": "A supported click stops producing its response.",
        })
    elif "effect_channels" in template:
        channel = template["effect_channels"][0]
        rewrites = ", ".join(f"{b}->{a}" for b, a, _count in channel["integer_transitions"])
        machine.submit_answer({
            **template,
            "mechanism_explanation": (
                f"Lever {template.get('entity_id')}: {channel['channel_id']} affects the local "
                f"target region through the exact observed rewrite {rewrites}."
            ),
            "competing_models": ["A hidden event coincided with the click."],
            "falsifier": "The same intervention produces a different exact residue.",
        })
    else:
        machine.submit_answer({
            **template,
            "explanation": f"Clicking this tile rewrites its own colour in place; {COUNTER_WORDS}.",
            "competing_models": ["A hidden process changed the tile at the same moment."],
            "falsifier": "A repeat click leaves the tile unchanged.",
        })


def _choose_press(capability):
    levers = capability["target"].get("levers") or []
    unfinished = [
        item for item in levers if item.get("status") in {"NOT_STARTED", "RUNNING", "CONFIRMING"}
    ]
    return (unfinished or levers)[0]["click"]


def _run_ladder():
    machine, grid = _close_g2_on_ft09()
    transition_id = G2_ACTIONS + 1
    worst = {}
    gates_seen = []
    for _step in range(ACTION_BUDGET * 2):
        capability = machine.next_probe_capability()
        view = machine.gate_view()
        key = (machine.gate_id, view.get("schema"))
        worst[key] = max(worst.get(key, 0), _binding_context_chars(machine))
        if machine.gate_id not in gates_seen:
            gates_seen.append(machine.gate_id)
        if capability is not None and not view.get("answer_templates"):
            if capability["purpose"] == "GUIDED_ACTION":
                action = _choose_press(capability)
            else:
                action = capability["actions"][0]
            probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [action])
            grid, outcome = _outcome(grid, transition_id, action, _control_click(grid, action))
            machine.record_outcome(probe, outcome)
            transition_id += 1
            continue
        if view.get("status") == "ANSWER_REQUIRED" or view.get("answer_templates"):
            _answer(machine, view)
            continue
        break
    return machine, transition_id - 1, worst, gates_seen


def test_ft09_ladder_reaches_a_satisfied_g4a_with_both_controls_studied():
    machine, last_transition, _worst, gates_seen = _run_ladder()
    assert gates_seen[:3] == ["G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS"]
    assert machine.gate_id == "G4.2-LEVER-ORBITS"
    assert machine.status == "SATISFIED"
    orbits = machine.target_journal.active_product("G4.2-LEVER-ORBITS").payload
    assert orbits["phase1_status"] == "COMPLETE"
    assert len(orbits["lever_entities"]) == 2
    assert {item["run_status"] for item in orbits["orbits"]} == {"CONFIRMED"}
    assert last_transition < ACTION_BUDGET, f"the ladder used {last_transition} actions"


def test_every_card_on_the_ft09_ladder_fits_the_budget():
    _machine, _last, worst, _gates = _run_ladder()
    assert {gate for gate, _schema in worst} >= {"G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS"}
    over = {key: size for key, size in worst.items() if size >= BUDGET}
    assert not over, over
