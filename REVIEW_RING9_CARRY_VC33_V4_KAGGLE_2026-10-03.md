# Review: ring9-carry-vc33-v4 (Kaggle, 2026-10-03)

**Author:** Claude (Alpha build seat), signed
**Run:** notebook `stephenkaskin/taaf-virelai-ring9-carry-vc33-v4` v1
**Package:** `b2f40266…9ade`, source `fbea80c` (fbbc7f4 + R9-R20), pinned image
**Output:** `runs/kaggle-ring9-carry-vc33-v4/output/`
**Evidence basis:** artifact state (turn ledger, gate events and answers) and the logs.

## Verdict

**What worked:**
- **The pin:** Python 3.12, and setup identical to v2.
- **Level 1:** identical to v2 and the exit run.
- **R9-R20:** level 2 opened, and the run reached G3 on level 2's board.
- **The carry, the headline:** all 4 level-1 lever predictions were graded on level 2, and **all 4 were RECONFIRMED**.

**What failed:** the run then **stalled at level 2's G3 for about 2.7 hours** (47 actions in all, 75 Duck turns with no action). This is a new deadlock, different from v2's:
- G3's lever-inventory answer is refused because two levers are `AMBIGUOUS`.
- G3's enumeration is complete, so no probe exists that could resolve them.
- The axiom-A2 watchdog stays silent, because an answer template exists.

## Grades

| Criterion | Result | Evidence |
|---|---|---|
| **I8** pinned environment | **PASS** | The log has only `python3.12` paths; the 174-wheel install succeeded |
| **I5** self-hosted setup | **PASS** | Both of the Director's dataset paths; smoke test "2 + 2 equals 4."; model 33.66 GiB, KV cache 43.62 GiB, as before. Weight loading took 443 s |
| **I6** comparability | **PASS** | The first 26 gate events are byte-identical to v2's (and so to the exit run's) |
| **X-1** level freeze | **PASS** | As in v2 |
| **I7** level entry | **Partial** | No G1 deadlock: G1 by the controller, then G2 by the controller (counter certified in 3 actions, t27–t29), then G3. But **G0 on level 2 was answered by Duck** (`G0-ACTION-SURFACE-v1`): the level-completed boundary wake gave Duck the first level-2 turn, before the controller's G0. That was the predicted "one extra Duck turn at level entry" (v1 risk 4). It is harmless here, but I7 as written is not met |
| **X-2** carry | **PASS: 4 of 4 RECONFIRMED** | The card's carry line moved from `4 UNCONFIRMED` through `1 RECONFIRMED` and `2 RECONFIRMED` to `4 RECONFIRMED`. Level 2's four same-type objects are at column 0, rows 16, 24, 36 and 44. G3's own clicks of them (t33–t40, after G2's mask was certified at t29) each rewrote 141–173 cells elsewhere on the board: the same REMOTE reaction as level 1's levers |
| **X-3** no verdict carried | **PASS** | Level-2 levers were certified by G3's own dossiers, answered by the controller from level-2 evidence |
| L-1 lives | Vacuous | No death occurred |
| **N-1** (axiom A2) | **FAIL** | G3 idled from t47 to the 3-hour limit. Two different hand-offs both left Duck with no move: "G3-LEVERS refused the controller's answer at this revision" (76 times), and Duck's actions were refused with "G3 enumeration is complete; no further target probe is admissible" |
| E ending | Time budget, no crash | 47 of 200 actions used |

## The new stall: what the record shows

1. **t33, the first press of (16,0):** 141 cells changed elsewhere.
2. **t34, the controller's `CONFIRM_LEVER_WITNESS`, the same click:** 1 cell changed, the counter only. The confirmation is **CONTRADICTED**, so the controller hands the turn to Duck. That object behaves like level 1's E0004: the first press changes the board and a repeat press does nothing (ABSORBING).
3. **(24,0), (36,0) and (44,0):** each changed the board on both presses.
4. **The refusal:** the controller's G3 inventory answer was refused with `G3 coverage cannot be reported with unbounded probe results: {'E0004': 'AMBIGUOUS', 'E0005': 'AMBIGUOUS'}`. The ids are level 2's own.
5. **The dead end:** G3 then offers no probe ("enumeration is complete") and accepts no inventory while two entities are AMBIGUOUS. Duck can neither act nor answer.

**The mechanism to confirm.** G3's witness-then-confirm design assumes a lever's effect repeats. A stateful lever (absorbing or one-shot) contradicts its own confirmation and lands in AMBIGUOUS. Once G3's enumeration is complete, the state has no way out: no re-probe, and no answer class for it.

On level 1 this never surfaced, apparently because the order of witness and confirmation differed. That is to be verified, not assumed.

## Altitude and next step

- **The A2 hole is code-level.** "An answer is demanded, a template exists, but every answer the state admits is refused, and no probe exists" is a deadlock the watchdog must see. The second-signature fix: the controller's refusal at the same revision, with no admissible probe, counts as no legal move. R9-R20's D2 covered the waiting variant only.
- **The AMBIGUOUS resolution is probably architectural.** There are two candidates: give G3 a bounded re-probe of an AMBIGUOUS entity, or let G3's inventory carry AMBIGUOUS (stateful) levers as a declared class. Choosing between them decides how G3 treats state-dependent levers, which vc33 has on both levels. That is a Chief Engineer ruling, not something to patch inside a work order.
- **First, a diagnostic before any fix.** A read-only replay of this v4 record (47 transitions) to confirm the mechanism above and why level 1 escaped it. Then a test-first slice (R9-R21) on whatever the ruling is.

## What this run settles

The cross-level chain from R9-R16 to R9-R20 now works live end to end:
- a level is frozen with its win recorded as an untested hypothesis;
- the ladder restarts on the next level;
- the carried lever type is tested by that level's own probes under its own counter mask.

On vc33 the transfer held 4 for 4. Whether same-type objects also share *state behaviour* is a separate question. The (16,0) object suggests they can differ (absorbing versus repeatable), and that is exactly what G3 could not represent.

— Claude, Alpha build seat, 2026-10-03
