# Repository mine: G4 lever subtrees and human-readable mechanics

**Type:** `REPO_MINE` · **Date:** 2026-09-25  
**Status:** source and executed-artifact review complete; no G4 code built by this document

## Objective

G3 answers **which visual objects are levers**. G4 must let Duck study each confirmed lever until
it can explain the mechanism as a human would: how it is activated, what it changes, how much and
in which direction, how repeated use behaves, where it stops or reverses, which state conditions
matter, and how its effects relate to other objects. The explanation must be grounded in observed
transitions and then supported by a later prediction.

The current governing use of `G4` is per-lever causal expansion. Some older plans use `G4` for
environmental forces. Those files are historical planning and their numbering is not imported.

## Repository identities and evidence classes

- The active hybrid source is
  `variants/ring9-cybernetic-gates/ARC3-Inference/` inside `virelai-review/duck-virelai`.
- Vendored `virelai_v4` trees are Captain-era prior art. Their algorithms may be ported, but their
  orchestration, confidence thresholds, and identity systems do not govern Ring 9.
- `/Users/stephenkaskin/Desktop/virelai-golden/` is the separate deterministic solver. Its subtree
  questions and arithmetic are useful design evidence; it is not the hybrid runtime.
- Historical run artifacts show what actually executed. Builder reports describe intended or
  reviewed behavior and were checked against the cited code where relevant.
- No downloaded game-engine implementation was inspected.

## Direct findings in the active Ring 9 source

### The G3 handoff is sufficient to seed G4

The active gate machine already provides:

- a `LeverInventory` with confirmed entity ids;
- an immutable positive witness and accepted Duck dossier per confirmed lever;
- exact intervention coordinates/actions;
- counter-masked local and remote residue summaries;
- lossless before/after diffs and evidence references;
- per-entity `G4-READY` lifecycle states;
- a masked-state archive maintained during probing.

The vc33 v8 run live-confirmed this handoff with `E0004` and `E0005`. G4 therefore does not need
to rediscover levers or reconstruct its own object identities.

### Useful G4 machinery is present but disconnected

The following active modules are not consumed by the binding gate path:

| Module | Useful capability | Port decision |
|---|---|---|
| `virelai_semantic/depth_probe.py` | Dynamic one-lever-at-a-time queue; appends new levers without erasing prior evidence; stops on an observed endpoint or confirmed recurrence. | Port the queue discipline and typed budget stop into G4. Replace old semantic-library input with the G3 inventory/entity ledger. |
| `virelai_semantic/depth_adapter.py` | Converts a pointer lever bbox into an ACTION6 click and measures declared effect regions. | Port the CLICK activation pattern. Rebuild its observation input from current G3 evidence. BODY/NAV routing remains new work. |
| `virelai_semantic/typing.py` | Separates mechanism from condition; recognizes exact toggle/cycle recurrence only within uninterrupted activation runs; also records repeated transforms, directional change, and observed deterministic transition tables. | Reuse its epistemic rules. Adapt its transition rows to current entity-keyed evidence. |
| `virelai_semantic/joint_transform.py` | Per-press pixel arithmetic, exact integer rewrites, signed class deltas, conservation, component decomposition, coordinated recolor, directional rewrite fronts, and recurrence fingerprints. | Reuse after confirming production-shaped input. It should read admitted counter-masked residue and never infer purpose. |
| `virelai_semantic/mechanics.py` | Effect-channel grouping and shared/opposed-control candidates. | Port with surgery. Remove its press-count proxy and its private footprint-based identity rejoin; entity identity belongs only to the Ring 9 ledger. |
| `virelai_world_model.py` and `virelai_physics_manual.py` | Project admitted mechanics into compact player-facing grammar. | Reuse as a rendering/projection layer after G4 laws exist. Do not make it another belief store. |
| `virelai_agenda.py` | Names magnitude, conditions, recurrence, and limits as open depth questions. | Use only as vocabulary. It is passive, non-binding, and caused post-G3 confusion in v8. It must not schedule G4. |

The current `LifecycleJournal` stops at `G4-READY`; it has no `EXPANDING`, `LAW_REQUIRED`,
`DEMONSTRATION_REQUIRED`, or `LOCKED` transitions. G4 therefore needs its own per-lever lifecycle
or a deliberate extension of the shared lifecycle. Merely exposing the old depth planner will not
create a gate.

## Verified historical execution evidence

### vc33 controlled depth run

`runs/live-pointer-depth-vc33-v2-20260908/` executed a deterministic Captain diagnostic, not Duck.
It used eight fixed discovery clicks, then studied one lever at a time:

- lever `[24,60,27,63]`: four depth activations, then an observed endpoint;
- lever `[32,60,35,63]`: six depth activations, interrupted by an observed level completion;
- both levers repeatedly affected the same two visible regions in opposite directions;
- one region changed by `+108` under the first lever and `-108` under the second;
- another changed by `-128` under the first and `+128` under the second.

The later player grammar correctly described this as an
`OPPOSED_DIRECTION_CONTROL_BUNDLE` without inventing the purpose of either region. This proves
that repeated per-lever probing plus pixel arithmetic can produce a human-readable description of
vc33's visible mechanism. It does not prove that the current Duck can do so: no model was invoked,
the discovery actions were fixed, and the old semantic compiler supplied the entities.

### ft09 controlled depth run

`runs/live-pointer-depth-ft09-v3-20260908/` found five self-reactive controls. Four were supported
as exact period-2 toggles after uninterrupted observations; the fifth remained unknown when the
run ended. The rendered grammar says each click rewrites the control between integer classes 8 and
9. A later counter-masking replay corrected an earlier false attribution of the independent ticker
to those controls. This is useful evidence for the typing and masking pipeline, while older ft09
claims made before that correction must not be reused uncritically.

## Captain and Golden prior art

The Captain stack contributes these ideas:

- a per-lever queue rather than a global undifferentiated mechanism hunt;
- separate CLICK and NAV-occupancy activation harnesses;
- effect-partner classification rather than classification of a static lever's own pixels;
- toggle, longer cycle, directional change, and observed endpoint as distinct outcomes;
- repeated activation with recurrence confirmation;
- per-subject effect records containing displacement or non-rigid cell-count change;
- joint/coupling analysis kept separate from single-entity laws;
- exact conserved-transfer licensing and prospective prediction.

The Golden subtree charter supplies explicit questions whose witnesses are patterns over the
record. Its useful progression is:

1. Does acting on this entity produce a non-counter effect?
2. Which subjects change?
3. Is the effect the same on a repeated activation?
4. Which activation modality operates it?
5. How are driver and responder deltas related?
6. Does the effect clamp at a reachable limit?
7. Does behavior vary with state, indicating a condition or hidden state?
8. How do multiple levers compose?

Its strongest design rule is that no question closes because a chosen count was reached. A
question closes when its stated witness or falsifier appears. Numeric caps are engineering stops
and must yield an explicit unresolved product.

Do not port Captain confidence bands, fixed press verdicts, correlation thresholds, its private
object identity, the old global all-levers-typed gate, or any mechanism label inferred from a
lever's self-state when the pattern actually lives on a responder.

## The G4 lever subtree

Each confirmed lever receives the same ordered question tree. Child questions open from observed
evidence; unsupported branches remain absent rather than being forced.

### G4.0 — Bind the lever and its known response

**Question:** Which G3 entity, intervention, witness, and effect residue does this subtree study?

**Closure:** exact references resolve to one `G4-READY` entity and its accepted G3 dossier. The
controller creates no new identity and admits no scoped-null entity.

### G4.1 — Effect anatomy

**Question:** What changed when the lever was activated?

For every affected subject or coherent region, record:

- stable entity id where continuity is supported, otherwise a bounded region hypothesis;
- local or remote relation to the lever;
- transformation verb: recolor, move, grow, shrink, birth, death, deform, or coordinated rewrite;
- exact integer rewrite table and signed class-count delta;
- direction/bearing, magnitude, spatial extent, and animation lag where observed;
- counter, ego, and structural-boundary exclusions;
- evidence refs and representation limits.

**Closure:** the full admitted non-counter residue is accounted for by named effect channels or an
explicit representation gap. No changed pixels silently disappear.

### G4.2 — Repetition law

**Question:** What happens when this same lever is activated again from controlled states?

Possible evidence-grounded products include:

- uniform repeated transformation;
- toggle with exact period 2;
- longer exact cycle;
- directional/monotone progression;
- deterministic transition table over the input states observed;
- divergent outcome set requiring condition study;
- unresolved because the sequence ended or the budget stopped.

**Later user ruling, 2026-09-25:** G4.2 is a discovery descent, not final mechanism certification.
Repeat the known lever while it reveals new counter-masked configurations. Return on the first
null masked transition or first exact masked-state recurrence, preserving the whole sequence and
recurrence indices. The product is `NULL_AT_OBSERVED_STATE` or
`OBSERVED_STATE_RECURRENCE(period=N)`, not a global saturation or eternal cycle claim. Later G4
questions may confirm, revise, or condition that first orbit. A fixed activation count never
determines completion.

### G4.3 — Limits, reversal, and persistence

**Question:** Does the effect stop, clamp, reverse, reset, or persist?

Keep mechanism and condition separate. Two confirmed unchanged activations at an endpoint may
support `SATURATED_AT_OBSERVED_STATE`; they do not turn the mechanism type into “saturated.” Test
whether the opposite lever, another action, reset, death, or level transition reverses or preserves
the state only when those operations are available and relevant.

### G4.4 — Conditions

**Question:** Under which world states does the lever produce each observed outcome?

Begin with an outcome ledger:

```text
(lever entity, intervention, masked observable address, known phase) -> set of outcomes
```

Repeated outcomes support the current scoped law. A split outcome is evidence of a missing
condition, hidden state, or mask leak; it is recorded rather than averaged. A conditional law is
accepted only after Duck freezes a discriminating prediction and a later transition supports it.

### G4.5 — Couplings and shared controls

**Question:** How do multiple effect subjects or multiple levers relate?

Record joint edges separately from per-entity laws. Candidate relations include opposed-direction
controls, coordinated transformations, relays, and conserved transfer. Exact conservation and an
out-of-sample prediction may license a conserved relation. Correlation alone may not.

### G4.6 — Human explanation and demonstration

**Question:** Can Duck explain how this lever works and predict a new use?

The answer must say, in ordinary language:

1. what the lever looks like and how Duck operates it;
2. which objects or regions respond;
3. what each response does, using both visual verbs and exact integer arithmetic;
4. how repeated use progresses;
5. what limits, reverses, or conditions the effect;
6. what remains unknown and what observation would falsify the law.

Duck then freezes one novel, checkable prediction. A later action grades it. On support, G4 emits a
versioned `LeverReactionLaw`; on contradiction, it revises or reopens the smallest affected child.

## Example of the target explanation quality

For the historical vc33 evidence, a human-quality explanation would have approximately this form:

> The two magenta rectangles on the right are opposing controls for the same two large regions.
> Clicking the upper control adds 108 cells to the upper region while removing 128 from the lower
> region. Clicking the lower control performs the opposite changes. Repeated upper clicks reach an
> observed endpoint where those regions stop changing. Repeated lower clicks move the state back
> in the opposite direction; in the recorded run, the sixth lower click coincided with an observed
> level completion. The record establishes the visible opposed transformations, but it does not by
> itself prove the hidden purpose of the regions or that the same endpoint always wins.

This is the standard: a meaningful causal description with exact support and honest limits, not a
schema-shaped paragraph that merely repeats field names.

## Recommended build order

1. **G4 contract and lifecycle.** Define the binding goal card, per-lever states, answer product,
   exit criteria, and the rule that passive agenda questions cannot compete with the active gate.
2. **G4 seed adapter.** Consume the live v8 `LeverInventory`, lifecycle records, and exact G3
   evidence for `E0004` and `E0005`; expose a compact callable subtree card.
3. **Effect anatomy.** Port joint pixel arithmetic onto current counter-masked probe outcomes and
   require lossless residue accounting. This alone should let Duck describe what one activation
   does.
4. **Controlled repetition.** Put the one-lever queue behind the gate router and add CLICK
   execution first. Record every state instead of forcing a type.
5. **Mechanism typing and limits.** Reuse run-scoped recurrence, directional change, endpoint, and
   reversal rules. Add prospective answer grading.
6. **Conditions and coupling.** Add the outcome-set ledger, discriminating demonstrations, opposed
   controls, and exact conserved-transfer relations.
7. **NAV/HYBRID activation.** Reuse the demonstrated ego law and existing G3 routing to reach and
   collide with each lever; keep navigation cost separate from activation count.
8. **Live promotion.** First replay v8 evidence offline, then run a focused vc33 G4 rung. Grade the
   explanation and prediction, not game score. Broaden only after that slice passes.

## First slice exit criterion

The first implementation slice should stop after G4.0 and G4.1. From the frozen vc33 v8
artifacts, it must:

- create exactly two G4 subtrees, for `E0004` and `E0005`;
- reject all eight scoped-negative entities as G4 seeds;
- retain each lever's intervention, witness, confirmation, and accepted dossier references;
- decompose every non-counter changed cell in each first witness into named effect channels;
- give Duck a compact card plus callable detail;
- require Duck to explain the first lever's affected subjects and exact observed transformations;
- leave repetition, saturation, conditions, coupling, and winning purpose explicitly open.

Passing this slice means Duck can accurately answer **“what did this lever do on the witnessed
activation?”** It does not yet mean Duck knows the full lever law. That deeper understanding is
earned by the later G4 child gates.
