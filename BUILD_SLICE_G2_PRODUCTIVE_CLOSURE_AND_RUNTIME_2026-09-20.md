# Build slice: G2 productive closure and runtime feasibility

**Date:** 2026-09-20  
**Active source:** `variants/ring9-cybernetic-gates/`  
**Status:** Historical frozen slice; launched as ls20 notebook version 1

> **Superseded active semantics (2026-09-22):** this document accurately describes the frozen
> package and the decision tested on September 20. It is not the current G2 exit contract. The
> active source now keeps G2 open until an extremal game-over or verified respawn is observed; see
> `BUILD_SLICE_G2_COUNTER_KNOWLEDGE_AND_BOUNDARY_LOCK_2026-09-22.md`.

## Failure evidence addressed

The completed G2-v2 run established three distinct controller failures:

1. vc33 found and prospectively supported its recurrent counter after three actions, then spent 45
   actions repeating one intervention without reaching the extremum;
2. ft09 completed its bounded zero-delta opening and then consumed time without another admissible
   experiment or terminal handoff;
3. the notebook promised 1,800 seconds to each of three sequential worlds while its deployment
   supplied only a 1,500-second benchmark window after reserve.

These are direct observations from the frozen execution. They do not show that vc33 lacks a
boundary consequence, ft09 lacks a counter globally, or ls20 failed G1/G2; ls20 was never reached.

## Productive G2 closure

After two varied witnesses and one supported prospective recurrence, the controller now creates:

- a reversible `MaskLaw` over the proved footprint;
- a `CounterModel` with status `PROVISIONAL_BOUNDARY_PENDING`;
- a masked state archive replaying the retained lossless G2 transitions;
- an explicit boundary obligation asking what happens at source minimum and replacement maximum;
- a monitor policy that checks later productive transitions instead of demanding blind repetition.

This closes the bounded counter-identification target and records a `CounterGateProduct`, but it
does not call the counter locked. Only observed game-over at the extremum or a verified extremal
respawn upgrades the model to `LOCKED_BY_EXTREMUM_BOUNDARY`. If the prospective demonstration
itself reaches that boundary, the model locks immediately.

The evaluator distinguishes these states. `BOUNDARY_PENDING` is neither a semantic pass nor a
failure. A full G2 `PASS` still requires recomputable min/max boundary evidence and receipt-bound
human review.

## Quiet-opening closure

When the complete ranked opening produces no recurrent visible process, G2 now records:

```text
COUNTER_NOT_OBSERVED_WITHIN_OPENING
scope = BOUNDED_RANKED_OPENING_ONLY
later policy = reopen if a recurrent remote rewrite appears
```

This advances the controller without claiming that the world has no counter. The product retains
every evidence reference and states the bounded epistemic limit. The evaluator reports
`COUNTER_NOT_OBSERVED` rather than treating this result as semantic failure.

## Runtime preflight

`checkpoint_runtime.py` computes the actual schedule from:

- deployment runtime;
- non-benchmark/shutdown reserve;
- world count and passes;
- concurrency;
- requested per-world allowance.

It derives the number of execution waves, benchmark soft budget, required benchmark time, and
maximum feasible per-world allowance. Package freeze fails if the allocation is impossible.

For the completed v2 configuration the calculation is:

```text
deployment 2100 - reserve 600 = soft budget 1500 seconds
3 sequential waves * 1800 seconds = 5400 seconds required
result: impossible; maximum feasible allowance is 500 seconds per world
```

## Frozen next checkpoint

The locally frozen package is:

`kaggle/ring9-g2-reliability-ls20-v1/`

It contains only `ls20-9607627b`, because the embodied Duck-piloting arm is the untested branch and
a single-world checkpoint makes the time promise realizable:

```text
deployment runtime: 2100 seconds
reserve: 600 seconds
soft budget: 1500 seconds
one execution wave: 1200 seconds requested
```

The notebook recomputes those values from the mounted deployment target before `bm.run`, compares
them with the execution receipt, rejects an impossible allocation, and derives its soft deadline
from the same receipt-bound budget.

Package identities:

- package-manifest SHA-256: `c48ee329cc4f90d908cd9ae9cad8114939814524cfdf7d66ed45c8fa394c9586`
- source-manifest SHA-256: `e4005f1722aacd79948f1ca1b0c645757f24b943dfa2573133995b61c904a47e`
- source-manifest entries: 177
- package-manifest entries: 184
- `src.zip` entries: 168

The private dataset reached `ready`. Kaggle notebook version 1 was pushed on 2026-09-20 and was
`KernelWorkerStatus.QUEUED` at the last launch check. See
`runs/kaggle-ring9-g2-reliability-ls20-v1/LAUNCH_RECORD.md`.

## Verification

- Complete Ring 9 suite: **280 passed**, with 14 dependency warnings.
- Targeted Ruff checks passed.
- Every source and package manifest digest matched.
- Every notebook code cell compiled.
- The notebook contains one receipt comparison and one receipt-success marker.
- The runtime receipt binds one wave, 1,200 seconds required, and 1,500 seconds available.

## Remaining boundary

G3 is not yet registered, so the cross-gate monitor entry point exists but has no productive later
gate feeding it live transitions. The ls20 checkpoint evaluates G1 and embodied G2 behavior. It
cannot validate deferred boundary monitoring across G3 until the lever gate is built.
