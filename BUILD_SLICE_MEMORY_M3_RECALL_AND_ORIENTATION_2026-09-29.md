# Build slice R9-R09: memory stage M-3, recall and the orientation turn

**Revision label:** `R9-R09`
**Date:** 2026-09-29
**Author:** Claude (Alpha build seat), signed
**Governing design:** `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md`:
- §5.2, the UNCERTIFIED lane;
- §5.4, recall;
- §5.5, the orientation row;
- §10, T4 (delivery).

**Law:** M6. **Ruling:** D6.
**Base:** `2941f53` (R9-R08). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## The result in one line

When the controller closes G3, Duck's first turn is now an **orientation turn**. The card says so
(`next_operation: SUBMIT_ORIENTATION`) and shows the certified world model. Duck names what it
sees, records hunches and proposes what to study; the notes go to an **UNCERTIFIED lane** that no
gate reads. From then on, every card carries **injected recall** about the current subject. Duck
can **pull** anything through one interface, `virelai('memory', …)`, and every pull now reaches it
whole.

## What was built

| File | What |
|---|---|
| `inference/framework/annotation_lane.py` (new) | **The UNCERTIFIED lane (D6).** A note has a subject (an entity, a certified gate, or `WORLD`), a kind (`NAME`, `HUNCH` or `PROPOSAL`) and at most 60 words. Notes are validated against what exists; they are stored, labelled `UNCERTIFIED` wherever shown, and never read by a gate. **The orientation turn** is due once G3's inventory is certified and Duck has not oriented; it happens once. |
| `inference/framework/recall.py` (new) | **Injected recall (M6).** The key is structural: the subject entity, its click site, the gate. It comes from G3's current target or pending dossier, G4's current lever, or G4-A's active lever. Facts come in the design's order: open contradictions, certified lines, the subject's own outcomes (newest first), other outcomes at the site, scoped nulls, then Duck's notes about it (labelled). They are filled to 2,000 characters with a remainder count and a pull handle. If nothing is known, one line says the subject is unexplored. A step with no subject and no site (G0, G1, G2's open search) gets no recall slot. |
| `inference/framework/memory_store.py` | **`query(kind, …)`, the one pull interface**, over the kinds products, product, transitions, transition, site, evidence, subject and notes. **`PULL_CHARS = 1,800`**: a pulled result is fitted so it reaches Duck whole (see "Found by T4"). A page shrinks first, then the largest fields become pull handles. A subject can be pulled one field at a time. The subject's transitions are now newest first. `cell_bbox` is now the one shared bbox helper. |
| `inference/agent/memory_queries.py` (new) | Serves `virelai('memory')`, plus `virelai('orient')` and `virelai('annotate')`, persisted to `{stem}_annotations.jsonl`. The seven older read views (`gate_audit`, `inventory`, `entity`, `reaction`, `orbit`, `limit`, `evidence`) are kept as aliases and moved here unchanged from `tool_agent.py`. |
| `card_builder.py` | Adds the `recall` slot, and an `orientation` slot (600 characters) while the turn is due. `world_model` adds Duck's notes, newest first, only in the room the certified lines leave. The card budget goes from 15,600 to **16,200**. |
| `tool_agent.py` | While orientation is due, actions and gate answers are refused, naming the orientation. A gate answer may carry `annotations`. They are validated *before* the answer is submitted, so a bad note refuses the whole call, and stored under the answering gate once it is accepted. |
| `virelai_gates.py` | `machine.annotations`, which no gate reads. `_cell_bbox` now uses the shared helper. |
| `tests/card_duck.py` | The card-only Duck submits its orientation when the card asks. It still carries 2, 8 and 20 levers to a satisfied G4-A. |

## Found by T4: a pull that could not reach Duck

The first delivery test pulled a lever's file, `virelai('memory', kind='subject', id=…)`. The file
was 6,400 characters compact. The sandbox prints every query as indented JSON (12,500 characters)
and the tool result is capped near 4,096, so Duck would have received a truncated fragment. This
is the Ring 8 failure class, "computed but omitted", found offline this time. The fix is
`PULL_CHARS`: every pulled result is fitted before it leaves `MemoryStore`, and the test asserts the
pulled content arrives with no truncation.

## Measured

| Card | R9-R08 | R9-R09 |
|---|---|---|
| Stress world, largest per gate, 2 → 20 levers | — | G2 5,790→5,791 · G3 4,928→4,680 · G4.1 5,955→5,771 · G4-A 7,038→7,552 |
| v2 record, final card (G3 dossier due) | 3,795 | 4,494 (recall added: the lever's two confirmations) |
| Card budget (all slots at budget) | 15,600 | 16,200 |

Every card stays within its budget and grows less than 1,000 characters from 2 levers to 20. No
slot is over budget.

## Tests (`tests/test_memory_m3.py`, 11 new)

**T4, on the production path.** The ToolAgent runs ft09 to G3 closure by itself, then a scripted
model plays Duck. The first message it is sent carries `SUBMIT_ORIENTATION` and injected recall
naming the lever as certified. The subject it pulls arrives in the next request, whole. Its
orientation notes are persisted with the label `UNCERTIFIED`.

The other ten tests:
- After orientation, the notes appear labelled in `world_model` and in the subject's recall, the
  gate resumes, and no certified line contains them.
- Actions and answers wait for the orientation turn.
- A gate answer may carry notes; a bad note refuses the whole answer before it is submitted.
- Note validation (subject, kind, length). Orientation happens once.
- Notes use only the room certified lines leave; the certified digest is byte-identical, and the
  digest stays in budget with 97 notes.
- Recall is keyed on the subject. An unclicked site says "unexplored". G2's open search gets no
  slot.
- Recall is bounded and ends with a pull handle, deterministically.
- The pull interface refuses an unknown kind.
- **A regression on the live v2 record:** recall keys the pending dossier's lever (E0060 at 52,36)
  and never calls a witnessed lever a scoped null. (The first draft did; this test caught it.)
- A real scoped-null subject is recalled as one.

**Suite:** cloud **460 passed, 1 skipped** (461 tests: 450 + 11). Ruff is clean on every changed
file. **Mac expected: 461 passed.**

## Ratchet

| | R9-R08 | R9-R09 |
|---|---|---|
| `tool_agent.py` | 2,861 | **2,777** |
| `ToolAgent._run_python_tool` | 420 | **327** |
| `ToolAgent.analyze` | 414 | 414 |
| `virelai_gates.py` | 5,803 | **5,800** |
| `card_builder.py` | 464 | 480 (not a tier violation) |

## What this does not do

- **Notes do not steer anything.** A PROPOSAL does not reorder G4-A. Any use of Duck's notes by the
  controller needs a gate, by D6.
- **Recall is keyed, not searched.** A fact about a different object that resembles this one is
  not recalled. That is G9's concern (carry across levels), not this stage's.
- **G4 economy (M-4) is next:** the G4.1 split, the G4-A split and the lives rule.

— Claude, Alpha build seat, 2026-09-29
