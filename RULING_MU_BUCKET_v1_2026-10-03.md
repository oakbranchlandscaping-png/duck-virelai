# Ruling: the mu bucket, for objects that stump us without stopping us

**Type:** `RULING_MU_BUCKET` · **v1** · **2026-10-03**
**Status:** **RULED by the Director, 2026-10-03.** Recorded by Claude (Alpha build seat), signed.
**Trigger:** `REVIEW_RING9_CARRY_VC33_V6_KAGGLE_2026-10-03.md`. Level 3's G3 found 7 levers and one object it could not attribute, then waited for evidence no move could bring, and the A2 watchdog ended the run.
**Supersedes:** the v5 and v6 reviews' open "G3 end-state" question (option a). The Director chose option (a) plus a return rule, in his words:

> "we need a 'mu' or unsure bucket we can place things in so they dont stump us, but if we do get stuck we have a group of mystery objects to return to with more information."

Asked whether a mystery object that later proves to be a switch joins the switch study on the same level, the Director said **yes** (the full version).

**Versioning:** highest version wins. Amend, never edit.

## 1 · The rule

**M-1. Mu holds what stumps us, never what we have not tried.**
- An object enters the mu bucket only when a gate has tried what it can on it and still cannot answer. In G3 today, that means the bounded ambiguities:
  - an unresolved click owner;
  - an ego-masked response;
  - a contact attempt that ran out of budget.
- A clean null (tried, and only the counter changed) is **not** mu. It closes with scoped evidence, as before.

**M-2. Mu never blocks.**
- A gate that has an answer for some objects and mu for the rest closes as **PARTIAL**: it emits what it knows and lists the mu objects.
- In G3: when at least one lever is certified and only mu objects remain, the controller writes the inventory (levers, clean nulls, mu), and the ladder moves on to study the levers.
- With no certified lever at all, G3 behaves as before.

**M-3. Mu is not a verdict.**
- A mu object carries no role tag and no inertness claim. It carries:
  - the reason it stumped us;
  - its evidence;
  - the masked board it was tried on;
  - its retry condition.
- This keeps the canon intact. `NESTED_TAXONOMY_SPEC_v5`'s "UNKNOWN is absence, never a leaf" still holds, because mu objects carry no tag. `PROBE_STRATEGY_v2`'s "no 'unknown' limbo" targets unknown used as a resting verdict that ends inquiry, and mu is the opposite: a worklist that forces a return. It is that strategy's own rule ("queue what you reveal; return") and its reopenable black swan, made explicit.

**M-4. When stuck, return to mu, but only with more information.**
- **Stuck** means one of two things:
  - the ladder would end the level without a win (every built gate satisfied, a planned stop);
  - the gate state has no legal move (axiom A2).
- Before ending, the controller opens the mu bucket. It retries a mu object **only if the masked board differs from every board that object was already tried on**. The changed board is the new information. Retrying on an unchanged board only spends a scored action and learns nothing.
- The retry clicks the object where it is **now**, at a cell the object currently owns. The board may have moved under the object since the first try.
- An object that occupies no cell any more is settled **ABSENT**: there is nothing left to retry. The entry stays in the level's record.

**M-5. A mystery that turns out to be a lever joins the study.**
- A positive retry goes through G3's normal path: witness, repeat press, dossier. G3 then re-emits its inventory with the new lever.
- **Phase 1 (G4.1 and G4-A):** keeps every answer and run it already has, and studies only the new lever. This is the dynamic queue in `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`, step 5.
- **Phase 2 (G4-B and G4-C):** restarts from scratch. Relations learned without the new lever were learned about a different lever set. The old products stay in the journal as stale history.
- A retry that comes back null closes the object as a scoped null at that board. A retry that is ambiguous again keeps it in mu, with the new board recorded.

**M-6. Mu is per level and is reported.**
- The bucket is built fresh for each level.
- When a level ends, the bucket's contents are frozen into that level's model, including entries never resolved.
- A run that ends genuinely stuck reports its mu list as its open questions.

## 2 · What it changes in the build (R9-R23)

| Item | Change |
|---|---|
| D12 | A level-tier `MuBucket` on the gate machine; G3 files each bounded ambiguity into it with the masked board it was tried on |
| D13 | G3 closes PARTIAL when it has levers plus mu; the controller writes that inventory |
| D14 | A return when stuck: a controller-side check before a planned stop or a dead state, which reopens G3 for mu objects whose board has changed |
| D15 | G4.1 and G4-A take late levers incrementally; G4-B and G4-C restart when the lever set grows |
| D16 | Each frozen level model carries its mu bucket |
| D17 | Code-level fix: the inventory text no longer says remote levers "rewrite their own cells" |

## 3 · Why

**The game is the reason.** On level 3 the mystery object was clicked during a sweep in which other levers were moving blocks around it. Read first-hand from the v6 record:
- by its click at t107, E0028 occupied no cell at all;
- the clicked cell belonged to E0071, a 92-cell object born mid-sweep, so the click's owner could not be resolved.

So the frozen roster's target and the board no longer agreed. That stale geometry is the kind of thing more information fixes. Under M-4 a return on a changed board would settle E0028 ABSENT.

**Open question for the Director, not ruled here.** E0071 itself, an object that appeared during the sweep, is in no roster. `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1` step 5 says such newborn objects are appended and studied. That is a separate rule from mu: newborns are untried, not stumping.

**Studying the levers is what produces that information.** Every lever press changes the board, so the mu return is cheap and well-timed. It happens only when the agent is otherwise done, and only where something has changed.

— Claude, Alpha build seat, 2026-10-03. Ruled by the Director, 2026-10-03.
