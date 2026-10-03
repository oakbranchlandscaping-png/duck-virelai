# Diagnostic: where lever typing belongs (G3 discovery, G4 typing), read-only

**Type:** `DIAGNOSTIC_G3_G4_LEVER_TYPING_BOUNDARY` · **v1** · **2026-10-03**
**Author:** Claude (Alpha build seat), signed
**Trigger:** the Director's direction, 2026-10-03: "levers do something different" is the point of G4, which exists to fully type each lever and find the nuances of its mechanics. The repo and Project already carry this as lever probes and lever typing.
**Ruling taken (Director, 2026-10-03):** diagnostic first, then build R9-R22.
**Code read at:** `623ad58` (Ring 9, `variants/ring9-cybernetic-gates/ARC3-Inference`); v4 prior art at `main` `a3c2800`, `variants/ring7/ARC3-Inference/virelai_v4/` (byte-identical to ring6.3).
**Record:** the v4 live record, level 2 (the v5 record is identical through t47).
**Nothing was changed.** One scratch script fed recorded presses through G4-A's own run recorder. It is described in §3.
**Game-free:** levers are named by entity id only.

## 1 · What the canon says

1. **A lever is identified by one observable.** `FOUNDATIONAL_ARCHETYPES_v2` §3 defines it as an *attributed exogenous effect*: with ego and counter excluded, a press attributed to this object changes other objects. The same section puts these in the lever's **subtree**, which is typing, after identification:
   - "repetition law (identical presses, identical effects? … any divergence a fork-witness for hidden state)";
   - "saturation (does the effect clamp at a wall)".
2. **Discovery comes before typing.** `SOLVER_BLUEPRINT` §4.1 and §4.2 open Lever Discovery with a single first-touch probe; Lever Typing follows it. §3.4 names the mechanisms, including one-shot and directional.
3. **Ring 9's own locked doctrine says the same.** `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`:
   - G3 is "Broad. Find every lever we can".
   - G4-A is "Deepen, one by one … until a masked null or an exact recurrence appears. Read the period. Classify the lever (toggle / cycle / directional / uniform / unknown)".
   - Anything needing a second lever (reversal, persistence, coupling) is Phase 2.
4. **Ring 9's attribution module states the law.** `lever_attribution.py`, module docstring: *"A positive residue proves a lever witness; silence never proves inertness and never retracts an earlier witness."*
5. **The vocabulary is ruled.** Apex's mechanism vocabulary, as quoted in `WO_VIS_01_RETURN` and `WO_MECHANISM_VOCAB_01_RETURN` (2026-08-03):
   - mechanism is one of UNIFORM, TOGGLE, CYCLE, DIRECTIONAL, UNKNOWN;
   - SATURATED is a separate condition that can be cleared, never a type;
   - UNIFORM means the lever "reacted, then held" a state other than the baseline. A run that never leaves the baseline is mechanism UNKNOWN with condition SATURATED.

   The v4 code realizes the type/condition split (`cycle_probe.py` `_commit_pending_type`, WO-E7; tests tc1–tc8). WO-DIVE-01 R1, a Chief Engineer ruling, reserves DIRECTIONAL for the effect subtree and adds UNDETERMINED for a cap with no recurrence.
   **Finding:** I did not find the Apex ruling document itself in the Project, only these two quotations of it. Per §9.5 that is a citation to confirm, not content to assume.

## 2 · What the code does

**G3 asks a typing question and treats the answer as a discovery verdict.** `virelai_gates.py`, G3 confirmation branch (around lines 3030–3115):
- After a positive witness, G3 presses the same click again and predicts the witness's cells.
- `confirmation_supported` requires a positive residue that overlaps the predicted local or remote cells.
- Anything else, outside a boundary, moves the entity from witnessed to AMBIGUOUS ("prospective witness contradicted"). That retracts a witness on a null press, against item 4.

**G4 intake depends on that verdict in two places:**
- **G3's inventory** lists as levers only entities in state G4-READY (around line 3310). Only the SUPPORTED branch reaches G4-READY, through the controller's dossier.
- **G4.1's `_seed`** (around line 4096) requires a confirmation whose status is SUPPORTED.

So a lever whose second press differs from its first never reaches G4, which is the gate built to type it.

**G4-A's class mixes type and condition.** `g4_guided.py` `LeverRun.lever_class()` returns ABSORBING for any run that ends in a confirmed masked null. That covers two cases the ruled vocabulary keeps apart:
- a lever that moved, then held, which is UNIFORM;
- a lever that never moved from this entry state, which is UNKNOWN with condition SATURATED.

v4 separated these in WO-E7 for this reason.

**Two typing readers exist in Ring 9.**
- `virelai_semantic/typing.py::classify_effect_channel` is a port of v4 with mechanism and condition already separate. Its vocabulary is TOGGLE, CYCLE, UNIFORM_TRANSFORM, DETERMINISTIC_STATE_TRANSITION, DIRECTIONAL_CHANGE and UNKNOWN, and it is read only by the semantic library compiler.
- G4-A's `lever_class()` is the one the gates use.

`UNIFORM_TRANSFORM` there means "the same transform on every press", which is not the ruled UNIFORM. The names are close enough to mislead. I am noting this, not ruling on it.

## 3 · What level 2's record shows, read through G4-A's own recorder

The scratch script replayed the v4 record (the controller's own answers, each recorded action through a freshly issued capability). It then fed each lever's two G3 presses, which were consecutive presses of the same click, into `LeverRun` with the live mask law:

| Entity | G3 confirmation | G4-A orbit steps (masked cells) | G4-A reading after two presses |
|---|---|---|---|
| E0004 | CONTRADICTED | NOVEL (140), then NULL (0) | Endpoint pending one confirming press: "moved, then held" |
| E0005 | CONTRADICTED | NOVEL (140), then NOVEL (140) | Run open: two new states |
| E0006 | SUPPORTED | NOVEL (172), then NOVEL (156) | Run open: two new states |
| E0007 | SUPPORTED | NOVEL (156), then NOVEL (172) | Run open: two new states |

**Reading.**
- **G3's SUPPORTED/CONTRADICTED split is an artifact of cell overlap, not behaviour.** By G4's measure, E0005, E0006 and E0007 behave the same way: each second press revealed a third board state. None returned to its start, so none is a toggle so far.
- **E0004 is the only behavioural outlier.** It moved, then held: UNIFORM in the ruled vocabulary, or one-shot in Blueprint §3.4's list, if a third press confirms it.
- **Each witness is a rigid move.** The witness presses' raw deltas swap equal cell counts between two values, and E0005's second press repeats its first press's counts a few columns over. That suggests rigid displacement (Blueprint §3.5), and it is a hypothesis for G4 to test.

**A nuance the build must keep.** G3's two presses are a complete, consecutive run from one entry state. G4-A then starts fresh runs from a later board, after other levers have been pressed.
- From that later board, E0004 may be null on its first press. G4-A would then call it ABSORBING without ever seeing it move.
- Or E0004 may respond again, if another lever's press restored what it needs.

Either way, G3's pair is real typing evidence from a different entry state, and it must not be dropped. Phase 1 types each run from its own entry state. Whether a lever's reading changes because another lever moved the board is a Phase 2 question.

## 4 · The attribution concern, answered

The confirmation press does guard one thing: a witness that is a coincidence (the world moving on its own while the press happened). In Ring 9's click lane that guard is already held three other ways:
- attribution is by pointer at the click site;
- G2's mask removes the counter;
- on this level, the clean nulls show that the board does not move unprompted.

Where the world does move on its own, the confirmation press still helps, but as typing data, not as a veto. A positive second residue anywhere is a second witness. A null second press is "held", which is a mechanism reading.

## 5 · What R9-R22 should do

| Item | Change | Where |
|---|---|---|
| D7 | **An attributed positive witness certifies the lever.** In the click lane, a confirmation outside a boundary never moves the lever to AMBIGUOUS. The record keeps its honest status (SUPPORTED or CONTRADICTED) and gains the pair's reading: `REPEAT_NULL` (held), `REPEAT_RETURNED` (exact inverse; toggle candidate) or `REPEAT_NOVEL` (a third state). The controller's dossier is then written as for a supported confirmation. R9-R21's `_bound_contradicted` becomes dead code and is removed. | G3 confirmation branch; a small pure helper outside `virelai_gates.py` |
| D8 | **G4 intake** accepts any certified lever. It reads the certified confirmation, not only a SUPPORTED one. | G4.1 `_seed` |
| D9 | **G3's pair travels with the lever into G4-A** as typing evidence from its own entry state. Nothing is discarded. | G4-A snapshot and product |
| D10 | **Mechanism and condition are reported separately**, per the ruled vocabulary, next to the unchanged `lever_class()`, so G4-B, G9 and the carry keep working. The run's effective-press count travels with them. DIRECTIONAL stays reserved (WO-DIVE-01 R1). | `g4_guided.py` |
| D11 | **A2 as the general rule.** A state is legal only if it offers a probe, asks for an answer the gate can accept, or declares an end. The declared ends are named once; every other operation is no legal move. | `legal_move_status` |
| D12 | **Pre-flight.** The v4 record must reach G4-A with all four levers queued, and every existing replay fixture must stay legal at every step. | New test plus `tools/check_level_two_g4_entry_from_record.py` |

**Out of scope, for the Chief Engineer:**
- G3's end state when a *genuine* bounded ambiguity remains (ego-masked or budget). Option (a) or (c) from the v5 review. D11 ends such a state cleanly instead of idling.
- The UNIFORM / UNIFORM_TRANSFORM name clash, and the two typing readers (one integrator, per `RULING_OBSERVERS_INTEGRATOR_v1`).
- Locating the Apex vocabulary ruling document.

## 6 · Housekeeping found on the way

`DIAGNOSTIC_G3_CONTRADICTED_CONFIRMATION_v1_2026-10-03.md` is not tracked on `main` (`a3c2800`). It should be committed with R9-R22's documents.

— Claude, Alpha build seat, 2026-10-03
