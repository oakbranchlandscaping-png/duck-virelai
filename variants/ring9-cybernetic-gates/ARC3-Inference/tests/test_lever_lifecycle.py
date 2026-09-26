import pytest

from inference.framework.lever_lifecycle import LifecycleError, LifecycleJournal


def test_entity_lifecycle_requires_evidence_and_preserves_witness():
    journal = LifecycleJournal(["E1"])
    journal.attempt("E1", evidence_ref="P1")
    journal.response("E1", positive=True, evidence_ref="P1")
    journal.witness("E1", witness_ref="LEVER-1")
    journal.close("E1", evidence_ref="LEVER-1")
    journal.answer("E1", answer_ref="ANSWER-1")
    journal.ready_for_g4("E1", evidence_ref="LEVER-1")
    row = journal.snapshot()["entities"]["E1"]
    assert row["state"] == "G4-READY"
    assert row["witness_refs"] == ["LEVER-1"]
    assert [event["to_state"] for event in row["events"]] == [
        "ATTEMPTED", "RESPONDED", "WITNESSED", "G3-CLOSED", "G4-READY"
    ]


def test_null_response_closes_without_claiming_inertness():
    journal = LifecycleJournal(["E1"])
    journal.attempt("E1", evidence_ref="P1")
    journal.response("E1", positive=False, evidence_ref="P1")
    journal.close("E1", evidence_ref="P1")
    assert journal.entities["E1"].state == "G3-CLOSED"
    assert journal.entities["E1"].witness_refs == []


def test_contradiction_reopens_only_the_affected_entity():
    journal = LifecycleJournal(["E1", "E2"])
    for entity in ("E1", "E2"):
        journal.attempt(entity, evidence_ref=f"{entity}-P")
        journal.response(entity, positive=True, evidence_ref=f"{entity}-P")
        journal.witness(entity, witness_ref=f"{entity}-W")
        journal.close(entity, evidence_ref=f"{entity}-W")
        journal.answer(entity, answer_ref=f"{entity}-A")
        journal.ready_for_g4(entity, evidence_ref=f"{entity}-W")
    journal.reopen("E1", evidence_ref="E1-C", reason="new transition contradicted law")
    assert journal.entities["E1"].state == "REOPENED"
    assert journal.entities["E2"].state == "G4-READY"
    assert journal.entities["E1"].witness_refs == ["E1-W"]


def test_illegal_transition_and_missing_evidence_fail_closed():
    journal = LifecycleJournal(["E1"])
    with pytest.raises(LifecycleError, match="evidence_ref"):
        journal.attempt("E1", evidence_ref="")
    with pytest.raises(LifecycleError, match="G3 closes"):
        journal.close("E1", evidence_ref="bad")


def test_null_or_unexplained_entity_cannot_become_g4_ready():
    null = LifecycleJournal(["E1"])
    null.attempt("E1", evidence_ref="P1")
    null.response("E1", positive=False, evidence_ref="P1")
    null.close("E1", evidence_ref="P1")
    null.answer("E1", answer_ref="A1")
    with pytest.raises(LifecycleError, match="positive witness"):
        null.ready_for_g4("E1", evidence_ref="P1")

    positive = LifecycleJournal(["E2"])
    positive.attempt("E2", evidence_ref="P2")
    positive.response("E2", positive=True, evidence_ref="P2")
    positive.witness("E2", witness_ref="W2")
    positive.close("E2", evidence_ref="W2")
    with pytest.raises(LifecycleError, match="evidence-bound G3 answer"):
        positive.ready_for_g4("E2", evidence_ref="W2")
