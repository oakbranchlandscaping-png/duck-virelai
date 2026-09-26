# Build slice: G2 counter knowledge and boundary lock

**Date:** 2026-09-22  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Evidence state:** **BUILT, LIVE UNCONFIRMED**

## Director update — 2026-09-23

G2 exists to remove scheduled visual noise from the causal search. It succeeds when Duck can
identify the counter's stable support and two-class exchange, construct a complete reversible
mask, and keep a boundary monitor armed. Exact rate semantics are useful metadata but are not a
blocking truth requirement.

Once the mask is demonstrated, G3 may begin. Ordinary lever probing naturally advances the
counter; a later observed death or respawn at source-minimum/replacement-maximum locks the
counter's boundary role without pausing the lever hunt. Thus G2 has two milestones:

1. **MASK READY:** counter identity and reversible masking are sufficient to subtract noise and
   open G3.
2. **BOUNDARY CONFIRMED:** later direct death/respawn evidence finalizes the boundary field of the
   same `CounterModel`.

This update supersedes the blocking sequence below where it says G2 must remain the sole active
gate until the extremum. The older description remains as implementation provenance.

## Gate question

Can Duck know the counter with the same evidence discipline used for the ego: identify the
controlled visible process, explain its law, predict a future transition, observe that prediction,
and discover the process's limiting consequence before advancing?

The G2 exit is now:

```text
varied actions expose a recurrent two-class exchange
→ Duck explains what changes, what it may track, and why it is bookkeeping
→ Duck freezes the full footprint, rewrite, rate, and isolated demonstration action
→ a later transition supports the prediction
→ a provisional reversible mask is created and G3 may open
→ the counter monitor remains active during lever probing
→ source eventually reaches minimum and replacement reaches maximum
→ platform-observed game-over or verified respawn locks the CounterModel boundary field
```

Rate recurrence alone never establishes counter identity, but an exact general rate law is not
required after the full support, exchange, mask, and eventual extremal consequence are observed.

## Prior art ported

This slice restores the strict boundary state machine already present in the earlier Ring 9 G2
checkpoint source and documented in the counter-boundary thesis. It preserves the newer ranked
CLICK/NAV/HYBRID opening, Duck-piloted collision arm, full-bar inference, masked state archive,
and productive evidence records.

The completed local `ls20` run supplied the production failure case. NAV/HYBRID intentionally has
no precomputed `_probe_actions` because Duck chooses approach controls. The controller had already
stored a refused `ACTION3` move whose only visible delta was the counter. `submit_answer()` checked
`_current_action()` while status was still `ANSWER_REQUIRED`; that helper exposes the stored action
only after the status becomes `DEMONSTRATION_REQUIRED`. The result was a false “no unused
intervention” error.

The repaired code validates `_counter_only_action` directly, freezes the explanation, changes
status, and then exposes that exact action through the ordinary probe capability.

## Duck-visible knowledge contract

G2 now supplies an exact `answer_template`. Duck must provide:

- the tracked visible quantity as a hypothesis;
- the two-class exchange mechanism, geometry, progression, and rate;
- why varied interventions support bookkeeping rather than a target-specific effect;
- the exact candidate witness evidence;
- a competing model, falsifier, conditions, and limitations;
- a prospective `COUNTER_REWRITE` prediction using the controller-selected isolated action;
- the complete counter footprint, observed rewrite, recurrent amount, causal basis, and reason the
  transition is prospective.

The controller checks these values against the evidence. It does not manufacture a successful
answer from schema compliance. The resulting `CounterAnswer` retains Duck's canonical prediction.

## Boundary discipline

A supported future recurrence creates:

- a full-footprint reversible `MaskLaw`;
- a `CounterModel` marked `PROVISIONAL_BOUNDARY_PENDING`;
- a retroactive raw/world state archive;
- an open obligation naming the min/max question.

This creates the blocking G2 product and may open G3. The cross-gate counter monitor then watches
ordinary G3 probes. The boundary field locks only on direct evidence of:

- game-over while source occupancy is zero and replacement occupancy fills the footprint; or
- a reset from an extremal standing to higher source and lower replacement occupancy.

An unfinished boundary monitor does not invent an extremal consequence. It may still supply a
valid mask-ready G2 product for G3. All raw grids remain authoritative, and masking remains a
derived reversible view.

## Validation

- Focused G2 controller and evaluator suite: **20 passed**.
- Full active suite: **289 passed**.
- Ruff: passed on changed runtime and tests.
- Live-shaped NAV regression: passed for mixed ego/counter witness, counter-only refused move,
  structured answer, prospective recurrence, provisional mask, continued G2 focus, and game-over
  at the full exchange boundary.
- Existing evaluator tests still require exact prospective timing, complete mask coverage,
  counter-only confirmation, boundary evidence, and receipt-bound human review.

## Prepared live checkpoint

`configs/g2-counter-lock-live-pilot.json` is a one-world online `ls20` configuration with:

- the same `Qwen/Qwen3.6-27B` model and ontology prompt;
- one pass and one concurrent world;
- 48 maximum actions;
- 30 minutes per world and 32 minutes for the experiment.

The larger action allowance exists because G2 must observe the bar's extremum instead of handing
the obligation to an unbuilt later gate. This configuration is prepared only; no live run has been
started from the new source.

## Claim boundary

The synthetic regression proves the state machine can represent and enforce the intended
knowledge sequence. It does not prove that the served Duck will submit the template correctly,
that `ls20` will reach its extremum within 48 actions, or that its observed consequence will be
game-over rather than respawn. Those are the next live checkpoint questions.
