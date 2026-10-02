# Review: R9-R19 G4 NAV ls20 Kaggle checkpoint v3

**Reviewer:** Sol (Alpha build seat), signed  
**Notebook:** `stephenkaskin/taaf-virelai-ring9-g4-nav-ls20-v3`  
**World:** `ls20-9607627b`, pass 0  
**Source commit:** `72adbe3fc644da536950b2d8af1341ecb8e9f0e4`  
**Result:** G0, G1 and G2 pass; G3 is materially demonstrated but does not close; G4 is not reached

## Receipt and run facts

- The downloaded execution receipt is byte-identical to the frozen package receipt. Both have
  SHA-256 `3aa3409df02e5329b48fb5337b3741e2532c1b7ba04e48836cda37224bed63ac`.
- The repaired model mount, source mount and wheelhouse all worked. Qwen3.8-27B-FP8 started and the
  run produced the complete behavioral artifact family.
- The run ended in the harness state `gave_up` at the explicit 200-action cap. It did not crash.
- It cleared 0 of 7 levels and scored 0. This checkpoint grades the cybernetic gates, so that score
  is reported but is not the gate verdict.
- Wall time was 2h 20m 29s. The run generated 333,882 tokens.
- Artifacts contain 3 gate answers, 199 gate events and probe envelopes, 398 before/after probe
  frames, and 244 turn-ledger rows.

## Gate verdicts

| Criterion | Verdict | Evidence-supported reading |
| --- | --- | --- |
| I0 package guard | PASS | The receipt binds the run to the preregistered guarded package. |
| I1 NAV assignment and controller | PASS | G0 assigned `NAVIGATION`; 178 of 199 probes were executed by the controller. |
| I2 receipt identity | PASS | Frozen and downloaded receipt digests are identical. |
| I3 memory artifacts | PASS | Gate answers, turn ledger, probe envelopes, control evidence and contact epochs were written. |
| I4 approach/contact separation | PARTIAL | Ordinary G3 routes distinguish `APPROACH` and `CONTACT_ATTEMPT`, but the confirmation path graded an approach move as the confirmation itself. |
| G0 | PASS | Duck read ACTION1-ACTION4 as non-coordinate controls, assigned NAVIGATION and did not invent their semantics. |
| G1 | PASS | Duck identified and described the 5x5 orange/blue embodied ego patch and learned the exact stride map: ACTION1 up 5, ACTION2 down 5, ACTION3 left 5, ACTION4 right 5. Its later ACTION1 prediction was demonstrated. |
| G2 | PASS | Duck identified the total two-row counter footprint at rows 61-62, columns 13-54, learned the `11 -> 3` two-cell rewrite, predicted its next tick, and installed mask law `MASK-V1-1ad0a385e935ba34`. Later counter-only changes did not count as lever evidence. |
| G3-1 target binding | PASS | Five ranked entities were pursued without target drift. Every G3 action named its bound target and carried approach/contact intent. |
| G3-2 demonstrated traversal | PARTIAL | The controller used the demonstrated action map, but it repeatedly retried the same failed frontier direction from an unchanged stand instead of learning a blocked edge. |
| G3-3 contact evidence | PASS | Four terminal contacts created target-bound contact epochs: one `ENTERED`, two `DISPLACED`, and one `REFUSED`. The refused contact became a scoped null; ambiguous contacts remained explicit rather than becoming false inertness. |
| G3-4 confirmed lever handoff | NOT ACHIEVED | The first contact produced a real local-plus-remote BODY lever witness, but the following confirmation was not a contact and was marked contradicted. No lever was confirmed or carried into G4. |
| G4-A/B/C | UNGRADED | The run never entered G4. This is not evidence that G4 NAV fails. |
| E bounded ending | PASS | The run ended at the explicit action cap without a crash. |

## What Duck actually understood

G1 is a strong semantic result rather than schema compliance. Duck named the controlled object, its
internal color pattern, its fixed five-cell lattice, the four action directions, the static parts of
the larger bird, a competing autonomous-motion model, a falsifier and an untested boundary limit.
Its prospective prediction was tested in a later state and supported.

G2 also met the intended gate thesis. Duck described the full bar, the direction of replacement,
the rate, the tracked variable, the reason it was bookkeeping noise, a competing effective-step-only
model and the still-unobserved min/max consequence. The installed mask then separated 152
counter-only G3 transitions from semantic progress. The missing boundary consequence did not block
the lever hunt, which is the intended policy.

## G3 findings

The run reached five ranked targets:

1. `M0009`, a one-cell entity at `[32,20]`: one approach followed by a target-bound contact. The
   contact entered the target and produced a local residue at `[32,20]` plus eight remote residue
   cells in the lower-left status area. This was recorded as `LOCAL_AND_REMOTE_LEVER_WITNESS`.
2. `M0010`, a one-cell entity at `[33,21]`: the contact displaced the target and remained explicitly
   unresolved, then closed as bounded ambiguity.
3. `M0006`, a one-cell entity at `[13,35]`: six approach moves and one terminal contact. The contact
   was refused and became the run's scoped null.
4. `M0008`, a three-cell entity around `[31,21]`: five approach moves and one displaced, unresolved
   contact, then bounded ambiguity.
5. `M0019`, a 2x2 integer-8 entity at rows 61-62, columns 56-57: 168 approach probes, no terminal
   contact, and no advance to another target. After the ego stopped translating, most transitions
   changed only the masked counter.

Across G3 there were 181 approach probes and four contact attempts. Attribution recorded one
local-plus-remote witness, one scoped null, seven unresolved outcomes, 23 ego-confounded approach
outcomes, 152 counter-only outcomes and one deferred boundary.

## Two defects exposed by the live run

### Confirmation is not a NAV contact procedure

The first witness was strong enough to open confirmation. The frozen confirmation envelope then
accepted any movement action with either pilot intent. The controller chose ACTION1 and labelled it
`APPROACH`; the gate nevertheless graded that transition immediately as the confirmation. It saw no
repeat of the predicted remote residue and marked the witness `CONTRADICTED`.

This is a control defect, not evidence against the lever. A NAV confirmation must preserve the
pending witness while routing, leave the prediction pending across approach frames, and grade only
the terminal target-bound contact. It should reuse the recorded `ContactProcedure` where possible.

### Failed approach movement does not become terrain knowledge

The fifth target lies in the lower status strip, outside the certified counter footprint. The
controller eventually issued ACTION2 repeatedly while the ego no longer moved. Those transitions
were correctly classified as counter-only, but the refused-edge set is updated only when the probe
already has `CONTACT_ATTEMPT` intent. Because these were labelled `APPROACH`, the router never learned
that the attempted edge was blocked and kept choosing it until the action cap.

The frame evidence supports “no ego translation on the repeated attempted bearing.” Treating the
integer-8 object as a HUD icon, or proving that it is globally unreachable, requires an additional
world/HUD and terrain argument. The run itself does not establish either claim.

## Runtime friction

The controller performed 178 probes without a model call, so the deterministic executor is already
reducing cost after a decision is available. The Duck side still consumed 333,882 generated tokens
across 92 model requests. Forty-two turn-ledger rows ended on the turn time budget, and the largest
recorded prompt reached 48,881 tokens. Most of the two-hour runtime accumulated before the later
controller-only action burst.

This does not erase the strong G1/G2 answers, but it makes Kaggle too slow for ordinary repair
cycles. The next change should be checked on the fast OpenRouter rung first, then frozen for one
receipt-bound Kaggle canary.

## Next repair slice

The next slice should remain inside G3 NAV and combine two tightly related mechanics:

1. Turn G3 NAV confirmation into a target-bound route/contact state machine. Approach frames must
   preserve the frozen prediction; only terminal contact may support or contradict it.
2. Learn floor and wall from every demonstrated movement attempt. A successful expected ego
   translation certifies a traversable stand. A movement action with no ego translation after the
   counter is masked certifies a refused edge even during `APPROACH`. The route planner must consume
   those edges and move to another frontier rather than retry forever.
3. Record a bounded `CURRENTLY_UNREACHABLE` routing result only from exhausted demonstrated paths
   and refused edges. It is a routing conclusion, not an inertness claim.
4. Keep world objects and stable interface objects distinct in the roster, while preserving the
   “collide with every world object” protocol.

Exit criteria for that slice: the original `M0009` witness receives a real later contact
confirmation; an unchanged approach action becomes a blocked edge; the planner does not repeat the
same failed `(stand, action)` pair; and G3 either closes with a confirmed lever or advances past an
unreachable ranked target without claiming it inert.

The detailed terrain, reachability-certificate and Duck-explanation contract is frozen in
`BUILD_SLICE_G3_NAV_TERRAIN_REACHABILITY_v1_2026-10-02.md`.

— **Sol**
