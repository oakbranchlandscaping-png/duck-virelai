"""The UNCERTIFIED lane: Duck's names, hunches and proposals, kept apart from certified memory.

Author: Claude (Alpha build seat), 2026-09-29. R9-R09 (DESIGN_VIRELAI_MEMORY_v2 §5.2, stage M-3;
ruling D6: "clearly labelled and never promoted without a gate").

Duck contributes language, not facts. A note names a subject (an entity, a gate, or the world),
says what kind of contribution it is, and says it in a sentence. The controller stores it, labels
it UNCERTIFIED wherever it is shown, and never lets it into the certified world model: only a gate
certifies. Notes arrive two ways: the orientation turn (Duck's first turn when the controller ran
G0 through G4.1), and an optional ``annotations`` list on any gate answer.

The orientation turn is due once G4.1's anatomy set is certified and Duck has not yet oriented
(R9-R10 moved it from G3 close: the controller now certifies the anatomy too). While
it is due, the card's next operation is SUBMIT_ORIENTATION and actions and answers wait for it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

NOTE_KINDS = ("NAME", "HUNCH", "PROPOSAL")
WORLD = "WORLD"
MAX_NOTE_WORDS = 60
MAX_NOTES_PER_SUBMISSION = 12
LABEL = "UNCERTIFIED: Duck's note; only a gate certifies"
ORIENTATION_GATE = "G4-REACTIONS"


class AnnotationError(ValueError):
    pass


@dataclass(frozen=True)
class Note:
    note_id: str
    subject: str
    kind: str
    text: str
    gate_id: str
    after_transition: int
    source: str  # ORIENTATION | ANNOTATION | ANSWER

    def line(self) -> str:
        return f"[UNCERTIFIED] {self.subject} {self.kind}: {self.text}"


class AnnotationLane:
    def __init__(self) -> None:
        self.notes: list[Note] = []
        self.oriented = False

    def about(self, subject: str) -> list[Note]:
        return [note for note in self.notes if note.subject == subject]

    def snapshot(self) -> dict[str, Any]:
        return {"oriented": self.oriented, "notes": [asdict(note) for note in self.notes]}


def orientation_due(machine: Any) -> bool:
    lane = getattr(machine, "annotations", None)
    return (
        lane is not None and not lane.oriented
        and machine.target_journal.active_product(ORIENTATION_GATE) is not None
    )


def known_subjects(machine: Any) -> set[str]:
    subjects = {WORLD, *(row["gate_id"] for row in machine.completed_gate_rows())}
    ledger = getattr(machine._adapters.get("G3-LEVERS"), "entity_ledger", None)
    if ledger is not None:
        subjects.update(ledger.entities)
    return subjects


def validate_notes(machine: Any, raw: Any, source: str, gate_id: str | None = None) -> list[Note]:
    """Check notes without storing them (so a gate answer is never accepted with a bad note)."""
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or not raw:
        raise AnnotationError("notes must be a non-empty list of {subject, kind, text} objects.")
    if len(raw) > MAX_NOTES_PER_SUBMISSION:
        raise AnnotationError(f"at most {MAX_NOTES_PER_SUBMISSION} notes per submission.")
    subjects = known_subjects(machine)
    lane: AnnotationLane = machine.annotations
    notes: list[Note] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise AnnotationError("each note is an object with subject, kind and text.")
        subject = str(item.get("subject") or "").strip()
        kind = str(item.get("kind") or "").strip().upper()
        text = " ".join(str(item.get("text") or "").split())
        if subject not in subjects:
            raise AnnotationError(
                f"note subject {subject!r} is not an entity id, a certified gate id, or {WORLD}."
            )
        if kind not in NOTE_KINDS:
            raise AnnotationError(f"note kind must be one of {list(NOTE_KINDS)}.")
        if not text or len(text.split()) > MAX_NOTE_WORDS:
            raise AnnotationError(f"note text must be one to {MAX_NOTE_WORDS} words.")
        notes.append(Note(
            note_id=f"N{len(lane.notes) + len(notes) + 1:04d}", subject=subject, kind=kind, text=text,
            gate_id=gate_id or machine.gate_id, after_transition=int(machine.observed_through_step), source=source,
        ))
    return notes


def submit_notes(machine: Any, raw: Any, *, source: str, gate_id: str | None = None) -> list[Note]:
    """Validate and store Duck's notes; an ORIENTATION submission completes the orientation turn.

    ``source`` is ORIENTATION, ANNOTATION (``virelai('annotate')``) or ANSWER (a gate answer's
    ``annotations``, stored under the answering ``gate_id`` once the answer is accepted).
    """
    if source == "ORIENTATION" and not orientation_due(machine):
        raise AnnotationError("No orientation is due: it opens once G4.1's anatomy set is certified, once.")
    notes = validate_notes(machine, raw, source, gate_id)
    machine.annotations.notes.extend(notes)
    if source == "ORIENTATION":
        machine.annotations.oriented = True
    return notes


def split_annotations(answer: Any) -> tuple[Any, Any]:
    """An answer's optional ``annotations`` list, separated from what the gate validates."""
    if not isinstance(answer, Mapping) or "annotations" not in answer:
        return answer, None
    return {key: value for key, value in answer.items() if key != "annotations"}, answer["annotations"]


def orientation_block(machine: Any, then: Any) -> dict[str, Any]:
    return {
        "why": (
            "The controller ran G0 through G4.1 without you. world_model is everything certified so far. "
            "This turn is yours: name what you see, record hunches, propose what to study next. "
            "Notes are stored UNCERTIFIED; only a gate certifies."
        ),
        "submit": "virelai('orient', notes=[{'subject': ENTITY_OR_GATE_OR_WORLD, 'kind': 'NAME', 'text': '...'}])",
        "note_kinds": list(NOTE_KINDS),
        "subjects": f"an entity id, a certified gate id, or {WORLD}",
        "then": then,
    }


__all__ = [
    "AnnotationError", "AnnotationLane", "LABEL", "NOTE_KINDS", "Note", "WORLD", "known_subjects",
    "orientation_block", "orientation_due", "split_annotations", "submit_notes", "validate_notes",
]
