# Ruling: G4-B and G4-C are controller-first; Duck's budget is per level, and the default after the gates is normal play

**Type:** `RULING_G4_CONTROLLER_FIRST` · **v2** · **2026-10-04**
**Supersedes:** v1, from the same date. v1 left the budget's size and the order after the gates open; v2 settles both.
**Status:** **RULED by the Director, 2026-10-04.** Recorded by Claude (Alpha build seat), signed.
**Versioning:** highest version wins. Amend, never edit.

## 1 · The Director's rulings

**First ruling (v1), the option chosen:** "Broad."

> The controller works out lever relations itself from the recorded presses, with no Duck turn. Duck then confirms or extends them, with a set limit of turns per level, and the gate closes UNRESOLVED when the limit is hit, so it never loops.

**Second ruling (v2), in the Director's words:**

> "id say per level. we dont want to get to a level that needs the duck and not have it avaialbe. it should default to normal play but still have all the data gathered from the gates."

## 2 · What it means

**G-1. The record answers first.** The controller certifies the lever relations from the recorded transitions, with no Duck turn. Each relation cites its evidence.

**G-2. An observed transition is evidence.** This holds whatever prediction, if any, preceded it.

**G-3. Duck's gate budget is per level.**
- Each level opens with a fresh budget of Duck gate turns for G4-B and G4-C. Spending on one level never starves a later level.
- Rejected and cut-off turns count against the budget.
- **Size:** 3 turns, as proposed in v1. The Director did not change it. It is a single named parameter, so it can be changed without a code change elsewhere.

**G-4. A spent budget closes UNRESOLVED.** It is a declared end (axiom A2) and never loops. A G4-C contradiction after the budget is spent does not reopen G4-B.

**G-5. After the gates, the default is normal play.**
- When a level's gates rest (every built gate satisfied, closed or UNRESOLVED), and the mu return has nothing to retry, the run does not stop. Duck plays the level normally.
- Duck plays with everything the gates certified on the card: counter and mask, ego, levers and their types, the coupling map, mu entries and carried levels.
- The gates keep recording every transition. A new level re-opens the ladder.
- This is the same rule as R-2 in `RULINGS_PORT_AND_PILLARS_v1` (GATED versus FREE_PLAY receipts; paper claims cite gated evidence only), now applied per level.

## 3 · Left open

| Item | Status |
|---|---|
| How Duck plays in normal play | R-1 and R-8 in `RULINGS_PORT_AND_PILLARS_v1` apply. One admitted action per turn inside gates; batched scripts only in free play, under the waste guards; known no-op repeats are blocked, with a labelled harness refusal. Whether batched free play lands in R9-R24 or with the port work is to be settled with the seat doing the ports. |
| Time | A submission's per-game time slice still ends the game, whatever the level budgets. |
| What the ladder aims at | Friction F3 (aim at the win) is unchanged. Normal play is where winning is attempted until learn-to-win and `ACT_ON_GOAL` exist. |

— Claude, Alpha build seat, 2026-10-04. Ruled by the Director, 2026-10-04.
