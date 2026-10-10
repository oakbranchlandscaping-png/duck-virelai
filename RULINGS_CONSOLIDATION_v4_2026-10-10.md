# Rulings: consolidation of the build (v4, 2026-10-10)

**Type:** `RULINGS_CONSOLIDATION` · **v4** · **2026-10-10**
**Status:** recorded by Claude, acting with Apex authority granted by the Director on 2026-10-10. Ruling 22 is **Director-ratified in the Director's own wording** (2026-10-10). It was proposed by Apex and revised by the Director before ratification.
**Supersedes:** v3 (same day). v1–v3 stay in place as history. Rulings 1–21 stand unchanged. v4 adds ruling 22 only.
**Not settled here:** the proposed rulings 23 (who owns the G3 lifecycle crash) and 24 (SUB-4, free-play restart). The Director ratified 22 only, and those two are separate decisions.
**Declared conflict.** As in v3, Apex is ruling on its own build seat's proposals. Ruling 22 takes effect on the Director's ratification.

---

22. **The model's role.**

    The active gate names the current knowledge gap and defines a bounded set of admissible experiments. The controller performs the steps it can determine from the record. Where a choice requires judgment, Duck may select an experiment from that set. If Duck does not choose within its turn budget, the controller takes the next admissible step in coverage order.

    Each selected experiment is bound to its target and admitted by the gate before execution, and its action receives a GATED receipt. Deterministic code records every result and certifies into the growing semantic library only the findings the evidence supports. Duck can read the library as it explores. Duck's assertions alone certify nothing.

    At G3, one attributed activation with masked residue establishes a lever. G4 adds repetition, mechanism and conditions to its dossier.

    FREE_PLAY remains the fallback when no gate can act. R-2 is unchanged.

    **Duck is called only when choosing an experiment requires judgment.** The controller keeps taking routine coverage steps without waiting for Duck on each one.

    **The gate goals, sharpened:**
    - **G1:** identify the control locus. Close it deterministically where possible; NAV worlds can need probes.
    - **G2:** identify and characterize the counter. It may change with actions, not only on its own.
    - **G3:** find the levers, then the remaining grammar chapters.

    The library's object census and evidence links must exist in a minimal readable form as Duck starts exploring. They are built alongside directed G3 play, then expanded.

    **Two binding implementation cautions:**

    1. **No repair loops.** An answer is checked once and its refusal is recorded. The gate advances only on a valid close or an explicit unresolved disposition. A rejected answer alone does not settle its knowledge question.
    2. **Directed G3 (WO-G3-DIRECTED).** Widening `validate_probe` (`virelai_gates.py:3724`) alone is insufficient. The chosen candidate must become the bound probe that `record_outcome` checks, so that its result cannot be attributed to the old head of the roster.

       Before the live gate changes, tests must cover two cases:
       - a model choice away from the head of the roster;
       - the controller's choice when Duck's turn times out.

---

**Evidence on record when 22 was ratified** (the v2 rehearsal, `REPORT_RING9_SUBMISSION_V2_REHEARSAL_2026-10-10.md`, and its turn ledgers):

| Measure | Value |
|---|---|
| Controller steps | about 92% of environment actions |
| Duck turns | 873, averaging about 78 s |
| Duck turns ending on the turn budget | 499 |
| Executed Duck steps, across 33 active games | 217 |
| The G3 lever certification path | `virelai_gates.py:4138` ("one attributed activation with masked world residue is the durable existential lever witness … Repetition, mechanism and conditions belong to G4") |

**Not established when 22 was ratified:** who made the move at each level clear. No claim about which actor produced the clears rests on this ruling.

— Claude, Apex authority (granted by the Director 2026-10-10), signed. Ruling 22 ratified by the Director in his wording, 2026-10-10.
