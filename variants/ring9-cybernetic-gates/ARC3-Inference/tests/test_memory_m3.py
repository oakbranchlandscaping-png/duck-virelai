"""Memory stage M-3 (R9-R09): the orientation turn, the UNCERTIFIED lane, injected and pulled recall.

Author: Claude (Alpha build seat), 2026-09-29. DESIGN_VIRELAI_MEMORY_v2 §5.2 (the lane), §5.4
(recall), §10 (T4: delivery); memory law M6; ruling D6.

T4 is tested on the production path: the ToolAgent runs ft09 to G3 closure by itself (M-2), then a
scripted model plays Duck, and the assertions read the messages the model was actually sent.
"""
from __future__ import annotations

import json

import pytest

import card_duck
from card_duck import run_ladder
from inference.agent.tool_agent import ControllerContractError, _ChatCompletionResult
from inference.framework.annotation_lane import AnnotationError, orientation_due, submit_notes
from inference.framework.card_builder import SLOT_BUDGETS, build_card, world_model_digest
from inference.framework.controller_executor import next_owned_step
from inference.framework.memory_store import MemoryStore
from inference.framework.recall import UNEXPLORED, recall_key, recall_slot
from ft09_world import V2_RECORD
from test_memory_m2 import Run, _ft09_machine_at


class Script:
    """A model that plays a fixed list of tool calls and records every request it is sent."""

    def __init__(self, *codes: str) -> None:
        self.codes = list(codes)
        self.requests: list[list[dict]] = []

    def __call__(self, messages, **_kwargs):
        self.requests.append(json.loads(json.dumps(messages, default=str)))
        if not self.codes:
            raise RuntimeError("script exhausted")
        code = self.codes.pop(0)
        code = code() if callable(code) else code
        call = {"id": f"c{len(self.requests)}", "type": "function",
                "function": {"name": "python", "arguments": json.dumps({"code": code})}}
        return _ChatCompletionResult(message={"role": "assistant", "content": "", "tool_calls": [call]},
                                     finish_reason="tool_calls", usage={"prompt_tokens": 1, "completion_tokens": 1})

    def user_text(self, index: int) -> str:
        return json.dumps([m.get("content") for m in self.requests[index] if m.get("role") == "user"][-1])

    def tool_text(self, index: int) -> str:
        return json.dumps([m.get("content") for m in self.requests[index] if m.get("role") == "tool"])


def _orient_code(entity: str) -> str:
    notes = [
        {"subject": entity, "kind": "NAME", "text": "a tile that toggles between two colours"},
        {"subject": "WORLD", "kind": "PROPOSAL", "text": "press each lever until it cycles"},
    ]
    return f"import json\nvirelai('orient', notes=json.loads({json.dumps(notes)!r}))"


@pytest.fixture
def at_g4(tmp_path, monkeypatch):
    run = Run(tmp_path, monkeypatch)
    run.until_duck()
    machine = run.agent._gate_machine
    return run, machine, build_card(machine).payload["recall"]["key"]["entity"]


def test_t4_injected_and_pulled_recall_reach_the_messages_duck_is_sent(at_g4, monkeypatch):
    run, machine, entity = at_g4
    script = Script(f"print(virelai('memory', kind='subject', id={entity!r}))", _orient_code(entity))
    monkeypatch.setattr(run.agent, "_chat_completion", script)
    run.turn()
    first = script.user_text(0)
    assert '\\"next_operation\\": \\"SUBMIT_ORIENTATION\\"' in first  # the orientation turn is due
    assert '\\"recall\\"' in first and f"{entity} is a certified lever" in first  # injected (M6)
    assert "If next_operation is SUBMIT_ORIENTATION, submit `virelai('orient'" in first  # told every turn
    pulled = script.tool_text(1)
    assert "subject" in pulled and entity in pulled  # pulled, and delivered in the next request
    assert "truncation_note" not in pulled and "[truncated" not in pulled  # whole: fitted (PULL_CHARS)
    notes = run.rows("_annotations.jsonl")
    assert [(row["subject"], row["kind"], row["source"], row["label"]) for row in notes] == [
        (entity, "NAME", "ORIENTATION", "UNCERTIFIED"), ("WORLD", "PROPOSAL", "ORIENTATION", "UNCERTIFIED"),
    ]
    assert machine.annotations.oriented and not orientation_due(machine)


def test_after_orientation_the_notes_are_shown_labelled_and_the_gate_resumes(at_g4, monkeypatch):
    run, machine, entity = at_g4
    monkeypatch.setattr(run.agent, "_chat_completion", Script(_orient_code(entity)))
    run.turn()
    script = Script()
    monkeypatch.setattr(run.agent, "_chat_completion", script)
    for _ in range(40):  # the controller runs the first lever (D3); Duck is woken to explain it
        run.turn()
        if script.requests:
            break
    after = script.user_text(0)
    assert '\\"next_operation\\": \\"SUBMIT_ORIENTATION\\"' not in after  # the card has moved on
    assert f"[UNCERTIFIED] {entity} NAME: a tile that toggles between two colours" in after
    assert "uncertified_note" in after  # the subject's note is recalled, labelled
    certified = [line for line in world_model_digest(machine) if not line.startswith("[UNCERTIFIED]")]
    assert all("UNCERTIFIED" not in line for line in certified)  # never promoted (D6)


def test_actions_and_answers_wait_for_the_orientation_turn(at_g4):
    run, machine, _entity = at_g4
    with pytest.raises(ControllerContractError, match="orientation"):
        run.agent._gate_probe_begin(run.state_path, machine, {"probe_token": "x"}, [{"action": "ACTION6", "row": 0, "col": 0}], executor="DUCK")
    assert next_owned_step(machine).owner == "DUCK"


def test_a_gate_answer_may_carry_notes_and_a_bad_note_refuses_the_whole_answer(at_g4, monkeypatch):
    """After orientation the controller runs the first lever (D3); Duck explains it, with notes."""
    run, machine, entity = at_g4
    submit_notes(machine, [{"subject": "WORLD", "kind": "HUNCH", "text": "oriented"}], source="ORIENTATION")
    code = "import json\nprint(virelai('gate_answer', answer=json.loads({!r})))"

    def answer(subject):
        card = build_card(machine).payload
        drafted = card_duck._answer({**card, "answer_template": card["answer_template"]}, None, set())
        return code.format(json.dumps({**drafted, "annotations": [
            {"subject": subject, "kind": "HUNCH", "text": "one of a family of tiles"}]}))

    script = Script(lambda: answer("E9999"), lambda: answer(entity))
    monkeypatch.setattr(run.agent, "_chat_completion", script)
    revision = None
    for _ in range(40):
        revision = machine.gate_view()["revision"]
        run.turn()
        if script.requests:
            break
    assert "E9999" in script.tool_text(1)  # the first call was refused, naming the bad note
    assert [note.subject for note in machine.annotations.notes] == ["WORLD", entity]  # E9999 never stored
    assert machine.gate_view().get("revision") != revision or machine.gate_id != "G4-REACTIONS"
    stored = machine.annotations.notes[-1]
    assert (stored.subject, stored.source, stored.gate_id) == (entity, "ANSWER", "G4.2-LEVER-ORBITS")


# ---- the lane and the recall slot, in isolation -------------------------------------------------

def test_notes_are_validated_and_orientation_happens_once():
    machine, _world = _ft09_machine_at("G4.2-LEVER-ORBITS")
    for bad in ([], [{"subject": "NOPE", "kind": "NAME", "text": "x"}],
                [{"subject": "WORLD", "kind": "FACT", "text": "x"}],
                [{"subject": "WORLD", "kind": "NAME", "text": "word " * 61}]):
        with pytest.raises(AnnotationError):
            submit_notes(machine, bad, source="ORIENTATION")
    submit_notes(machine, [{"subject": "G3-LEVERS", "kind": "NAME", "text": "five tiles"}], source="ORIENTATION")
    with pytest.raises(AnnotationError, match="No orientation is due"):
        submit_notes(machine, [{"subject": "WORLD", "kind": "NAME", "text": "again"}], source="ORIENTATION")


def test_the_world_model_shows_notes_only_in_the_room_certified_lines_leave():
    machine, _world = _ft09_machine_at("G4.2-LEVER-ORBITS")
    certified = world_model_digest(machine)
    submit_notes(machine, [{"subject": "WORLD", "kind": "HUNCH", "text": "x"}], source="ORIENTATION")
    for index in range(8):
        submit_notes(machine, [{"subject": "WORLD", "kind": "HUNCH", "text": f"hunch {index} " + "word " * 50}] * 12, source="ANNOTATION")
    digest = world_model_digest(machine)
    assert digest[: len(certified)] == certified  # certified lines are untouched by notes
    assert digest[-1].endswith("virelai('memory', kind='notes')")
    assert len(json.dumps(digest)) <= SLOT_BUDGETS["world_model"]
    assert MemoryStore(machine).query("notes", limit=5)["total"] == 97


def test_recall_is_keyed_on_the_subject_and_says_when_nothing_is_known():
    machine, _world = _ft09_machine_at("G3-LEVERS")
    capability = machine.next_probe_capability()
    key = recall_key(machine.gate_id, machine.gate_view(), capability)
    assert key["entity"] == capability["target"]["entity_id"]
    assert key["site"] == [capability["actions"][0]["row"], capability["actions"][0]["col"]]
    slot = recall_slot(machine, key)
    clicked = MemoryStore(machine).site(*key["site"])["total"]
    assert bool(slot.get("facts")) == bool(clicked)  # this target's site history, if it has one
    assert recall_slot(machine, {"gate": machine.gate_id, "entity": None, "site": [0, 0]})["known"] == UNEXPLORED
    g2, _ = _ft09_machine_at("G2-COUNTER")
    assert recall_slot(g2, recall_key("G2-COUNTER", g2.gate_view(), g2.next_probe_capability())) is None


def test_recall_is_bounded_and_ends_with_a_pull_handle():
    machine = run_ladder(8).machine
    lever = next(item for item in machine._adapters["G4.2-LEVER-ORBITS"].compact_gate_view()["levers"])
    key = {"gate": machine.gate_id, "entity": lever["entity_id"], "site": [lever["click"]["row"], lever["click"]["col"]]}
    full = recall_slot(machine, key)
    assert len(json.dumps(full)) <= SLOT_BUDGETS["recall"]
    small = recall_slot(machine, key, budget=500)
    assert small["remaining"] > 0 and small["pull"] == f"virelai('memory', kind='subject', id={lever['entity_id']!r})"
    assert small == recall_slot(machine, key, budget=500)  # deterministic (M7)


def test_the_one_pull_interface_refuses_an_unknown_kind():
    machine, _world = _ft09_machine_at("G3-LEVERS")
    with pytest.raises(ValueError, match="memory kind must be one of"):
        MemoryStore(machine).query("similar")
    assert MemoryStore(machine).query("products")["kind"] == "products"


def test_recall_keys_a_pending_dossier_and_never_calls_a_witnessed_lever_null():
    """The live v2 record's last state: a lever witnessed and confirmed, its dossier due."""
    from inference.framework.record_replay import load_record, replay

    machine = replay(load_record(V2_RECORD), measure=False).machine
    recall = build_card(machine).payload["recall"]
    assert recall["key"] == {"gate": "G3-LEVERS", "entity": "E0060", "site": [52, 36]}
    kinds = [next(iter(fact)) for fact in recall["facts"]]
    assert kinds[:2] == ["outcome", "outcome"] and "scoped_null" not in kinds


def test_a_scoped_null_subject_is_recalled_as_one():
    machine, _world = _ft09_machine_at("G4.2-LEVER-ORBITS")
    lever = machine._adapters["G3-LEVERS"]
    null_entity = next(
        entity for entity, life in lever.lifecycle_journal.entities.items()
        if life.state == "G3-CLOSED" and not life.witness_refs
    )
    slot = recall_slot(machine, {"gate": machine.gate_id, "entity": null_entity, "site": None})
    kinds = [next(iter(fact)) for fact in slot["facts"]]
    assert "scoped_null" in kinds and f"{null_entity} closed with scoped null evidence" in json.dumps(slot)
