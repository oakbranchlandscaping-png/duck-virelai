# Build slice WO-L1a: the click-only (pointer) G1 contract

**Date:** 2026-10-10
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v1_2026-10-09` §3 (the finding) and §5 (WO-L1a);
- rulings 6, 15 and 21 (`RULINGS_CONSOLIDATION_v2`, `v3`);
- ruling 22's sharpened G1 goal: identify the control locus, closing it deterministically where possible.

**Base:** `ring9-unified` @ `06b44ed5b250564fc10b45cd5df78e60b35f77e6` (short: `06b44ed`).
**Shared file:** `virelai_gates.py`. The single authoritative declaration is `NOTE_SHARED_FILE_WO_L1A_2026-10-10.md`.
**Altitude:** code-level. This is a contract defect, not an architecture change.

## 0 · In one paragraph

In a click-only world, G1's pointer answer template wrote an `action_laws` entry for every available action, each as "selects the supplied grid coordinate" (`virelai_gates.py:7049-7056` at the base). But `submit_answer` (`:728-730`) and `ego_law_from_interface` (`ego_verification.py:718`) accept exactly `{"ACTION6"}`.

So in a world that also offers ACTION5 or ACTION7:
1. The controller submitted the template verbatim, and G1 refused it.
2. Duck copied the same template, and G1 refused it again.
3. The contract loop ended the study at 0 actions.

The saved v2 rehearsal report identifies this failure in `k022`, twice on successive levels, and in `k023`. The template also claimed that ACTION5 and ACTION7 select a coordinate, which no evidence supported.

Now the template explains ACTION6 alone, as the axiom does. Every other action is listed as an open obligation for later gates. The controller closes pointer G1 at 0 actions, and Duck is never asked.

## 1 · Changes

| File | Change |
|---|---|
| `inference/framework/virelai_gates.py` | The pointer template's `action_laws` come from the new `_pointer_action_laws(available_actions)`, which returns ACTION6 only. Its `limitations` come from the new `_pointer_open_actions(available_actions)`: "ACTIONn: not explained by the interface axiom; its effect is an open obligation for later gates". The compact pointer template keeps `limitations` when it is non-empty. In an ACTION6-only world it is empty and still stripped, so that world's card is unchanged. +19 −9. |
| `tests/test_l1a_pointer_g1_contract.py` | New: 7 test cases (§2) |

The controller's answer is still the template, verbatim (`controller_executor.py:372-375`). The open actions therefore reach the G1 product: `EgoLaw.limitations` (`ego_verification.py:743`), where the census (WO-L2) will read them as typed gaps.

## 2 · Tests: fail first, then pass

These are **synthetic contract regressions** using the action rosters observed in the saved runs: ACTION6-only, the `k023` shape (ACTION6 + ACTION7), and the `k022` shape (ACTION5 + ACTION6 + ACTION7). They exercise the production controller and gate machine and prove zero environment actions are required. They are not a replay of saved `k022`/`k023` frame artifacts; live/saved-run confirmation remains owed to the next packaged rehearsal.

| Test (parametrized over {ACTION6}, {ACTION6, ACTION7} and {ACTION5, ACTION6, ACTION7}) | At the base | With WO-L1a |
|---|---|---|
| `test_the_controller_closes_pointer_g1_at_zero_actions`: the first G1 step belongs to the controller (ruling 6), its answer is accepted, and the router reaches G2 | 2 cases fail with the rehearsal's own message: "Click-only G1 must explain ACTION6 as the site-selecting control locus." {ACTION6} passes. | All pass |
| `test_the_pointer_template_explains_action6_only`: `action_laws` is {ACTION6}; each other action is an open obligation in `limitations`; no other action has a coordinate law | 2 fail; {ACTION6} passes | All pass |
| `test_the_g1_product_carries_the_open_non_pointer_actions`: the EgoLaw holds ACTION6's law alone, plus ACTION5 and ACTION7 as open obligations | fails | passes |

At the base: **5 failed, 2 passed.** With WO-L1a: **7 passed.**

## 3 · Verification

| Check | Result |
|---|---|
| The WO-L1a tests | 5 failed at the base; all 7 pass with the fix |
| Neighbouring suites (counter gate, cybernetic gates, adaptive ego coverage, bounded cards, replay fidelity) | 64 passed, 1 skipped |
| Mac floor, excluding the separately governed `test_physics_grammar_contract.py` | **637 passed, 1 skipped**, 14 third-party deprecation warnings, 465.90s |
| ruff | No new findings. Two findings already present at the base are unchanged: F402 at `:3234` and F601, both outside this slice. |

## 4 · What it does not do

- It doesn't touch the embodied (NAV or HYBRID) G1 template or its validation. Those 9 rests are WO-L1a-NAV, Sol's (ruling 21).
- It doesn't change the validator or the EgoLaw constructor; both already said what the axiom covers.
- It assigns no meaning to ACTION5 or ACTION7. Which gate studies them is WO-L2-00's question 5.

## 5 · Next

1. **Commit** the four explicit WO-L1a paths on `ring9-unified`; the Mac floor has passed at 637 passed, 1 skipped with `test_physics_grammar_contract.py` excluded under its separate ruling.
2. **Package v3** takes WO-L1a, plus the census and SUB-4 as they land. Its rehearsal grades G1-a: no G1 stop at 0 actions in a click-only world.

— Claude, Alpha build seat (click line), 2026-10-10
