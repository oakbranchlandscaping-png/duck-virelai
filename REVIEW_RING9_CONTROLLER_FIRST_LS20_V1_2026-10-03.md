# Review: Ring 9 controller-first ls20 v1

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Verdict:** PARTIAL PASS — controller-first mechanics are substantially proven; two ownership
boundaries need repair before another run

## Question tested

Can the deterministic controller move a NAV world through metadata, the exact G1 Delphi sequence,
the prospective ego-law demonstration, and the beginning of ranked G2 pursuit, while reserving Duck
for semantic explanation and genuinely non-computable choices?

This was a bounded checkpoint. Score, level completion, G2 closure, G3 entry, and lever discovery
were explicitly outside its success criteria.

## Executed artifact identity

- Notebook: `stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v1`
- World: `ls20-9607627b`
- Frozen source commit: `0b1a5e4ce45f837ad0da921d3ac308c9ba9e56dd`
- Package SHA-256: `af2de4fb56543be79a875ee81e92feed0cb85f3bae82d0ff81c9d0b381b6d296`
- Source-manifest SHA-256: `ea4af6b4456ba32660b828846a2d394b39e09c46d6b7420afaf557a275bdf83a`
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Limits: 16 environment actions and 1200 behavior seconds
- Result directory: `runs/kaggle-ring9-controller-first-ls20-v1/`

The downloaded execution receipt is byte-identical to the packaged receipt. The run completed
without a crash from 09:47:48 to 10:07:49: 20 minutes, 11 environment actions, zero levels, and a
controlled time-cap stop.

## Preregistered grades

| # | Criterion | Grade | Direct evidence |
|---|---|---|---|
| 1 | G0 closes through the controller with zero model requests. | **PASS** | `gate_answers.jsonl` records `G0-CONTROLLER` with `executor=CONTROLLER`; the first turn-ledger row is already G1 and has zero model requests. |
| 2 | All eight Delphi actions are controller actions in strict order. | **FAIL** | The action order was correct: A1, A1, A2, A2, A3, A3, A4, A4. Seven were controller actions. The first A4 was executed by Duck after a generic low-budget wake fired with ten actions remaining. |
| 3 | Duck explains the embodied ego and movement laws from the evidence. | **PASS** | The accepted G1 answer identifies the 5x5 orange-and-blue ego and states A1/A2/A3/A4 as up/down/left/right translations of five cells. It cites all eight probe records, gives a competing model, falsifier, limitations, and a prospective prediction. |
| 4 | The accepted model and prediction survive into demonstration. | **PARTIAL / STRUCTURALLY SUPPORTED** | The accepted answer contains the model and exact pending `PATTERN_TRANSLATION` prediction. The controller immediately used that prediction. No separate model-facing demonstration-card artifact was emitted, so visual delivery to Duck is not independently auditable in this run. |
| 5 | The controller executes the demonstration and G1 closes from the scoped comparison. | **PASS** | Transition 9 is controller-owned. `demonstration_comparison.outcome=SUPPORTED`, with the exact 25-cell footprint translated `[-5, 0]`; two remote HUD changes are recorded separately and do not reverse the verdict. G1 then transitions to G2. |
| 6 | G2 opens and the deterministic planner executes a `PILOT_TO_CONTACT` action. | **PASS** | The controller executes two G2 pursuit actions, A1 and A3, against ranked target `M0009`. |
| 7 | A remote delta does not erase ego movement or refusal evidence. | **PARTIAL / BEHAVIOR OBSERVED** | G2 action 1 records ego motion plus the two-cell HUD tick. G2 action 2 records only the HUD tick after attempted A3, and the controller still forms the recurrent counter candidate. The artifact does not serialize the internal refused-edge record, so persistence of that edge cannot be audited directly. |
| 8 | The run ends at its explicit cap or another controlled stop without crashing. | **PASS** | The run stops at the 1200-second cap in G2 with state `cancelled`; logs and artifacts are complete. |

Overall: **5 PASS, 2 PARTIAL, 1 FAIL**.

## What the run directly established

The controller carried almost the whole mechanical ladder. It answered G0, executed seven of the
eight Delphi actions, executed the prospective demonstration, closed G1, and executed both G2
pursuit actions. Only one of the eleven environment actions was selected by Duck.

Duck's G1 answer meets the project's human-understanding standard. It did more than locate a moving
region: it described the ego's exact visual composition, mapped every action to a direction and
five-cell displacement, preserved uncertainty about collision and boundary behavior, and noticed
the independent two-cell HUD rewrite without confusing it with ego motion.

The G2 machinery then found the counter very quickly. Two controller actions under different
interventions produced the same `11->3` rewrite of two cells. The resulting candidate
`COUNTER-CANDIDATE-3fce209a36a83900` has an 84-cell full-bar footprint: rows 61–62, columns 13–54,
with a scheduled `EVERY_TRANSITION` pattern. The second observation contained only the two HUD
changes, so the counter detector was not dependent on successful ego motion.

## Friction and diagnosis

### 1. A generic budget wake overrode an exact mandatory action

After six exact Delphi actions, the fixed `actions_remaining <= 10` wake fired because this canary
allowed only sixteen actions. Duck then spent two requests and 72 seconds to perform the already
specified first A4 probe. The controller performed the second A4 immediately afterward.

This is an ownership-policy defect exposed by the fast budget. The controller still knew the exact
next action; therefore the condition for waking Duck was not met. Exact gate actions should outrank
generic budget wakes, and the wake should occur at the next semantic or choice boundary.

### 2. G2 found the counter, then handed a mechanically complete answer to Duck

Once the two recurrent rewrites formed the full-bar candidate, the NAV branch woke Duck for a
counter explanation. Duck produced seven consecutive 4096-token responses without submitting the
gate answer, consuming about 811 seconds. The final request did not complete before the remaining
91 seconds expired. There is no G2 answer artifact.

This is the same architectural boundary in a second form. The controller possessed the candidate,
full footprint, rewrite, recurrence evidence, and trigger classification required by the narrow G2
contract: find and mask the counter so later world deltas become legible. It should submit the
certified G2 answer itself. Duck can later explain uncertain semantics or integrate the counter into
the wider world model, but that synthesis should not stop the mechanical gate from moving.

### 3. Model accounting has two scopes

`summary.txt` reports 15,698 generated tokens. Summing the turn ledger gives 44,370 generated
tokens across 16 completed model responses. `requests.jsonl` contains 17 request events and 16
response events because the final request timed out. The benchmark summary appears to stop
counting after the last environment action, while the turn ledger includes the subsequent G2
answer attempts. These figures should remain separate until the reporter is repaired.

## What the evidence does not establish

- It does not prove full G2 closure or counter masking because no G2 answer was submitted.
- It does not prove G3 pursuit, lever discovery, level completion, or game-solving ability.
- It does not directly prove that the internal refused edge survived; only the observations and
  successful downstream counter-candidate construction are recorded.
- It does not show the exact rendered demonstration card that Duck would have seen.
- Zero score and zero levels do not refute the checkpoint because they were outside its contract.

## Required repair before rerun

1. Give exact controller-owned gate actions priority over generic action/time budget wakes. Wake
   Duck at the next judgment boundary, not in the middle of a known sequence.
2. Port the existing controller-generated G2 answer path into NAV when the evidence already proves
   the counter footprint, rewrite, recurrence, and trigger. This should lock the mask and open G3
   without a model turn.
3. Serialize refused-edge updates or a compact pursuit-state digest so the next live review can
   audit criterion 7 directly.
4. Correct or label token accounting so post-action semantic attempts are not omitted from the
   benchmark total.

Do not rerun the unchanged package. The next checkpoint should first prove that deterministic code
reaches G3 on this same ls20 opening with no Duck-selected mechanical action. Duck should be called
for the accepted G1 human explanation and only for semantics the certified record cannot supply.

**Post-review active-source note:** the ownership repair is implemented in
`BUILD_SLICE_CONTROLLER_OWNERSHIP_PARITY_2026-10-03.md`. This does not alter the frozen run or its
grade; it defines the source that must pass local verification before a new package is created.

— Sol
