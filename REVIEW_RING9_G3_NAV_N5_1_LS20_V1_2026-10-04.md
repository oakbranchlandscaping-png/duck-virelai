# Run review — Ring 9 G3 NAV N5.1 ls20 v1

**Type:** `RUN_REVIEW`
**Package:** `ring9-g3-nav-n5-1-ls20-v1`
**Author:** Sol (Alpha build seat)
**Date:** 2026-10-04
**Status:** reviewed; N5.1 semantic seam passes, G3 remains open

## Direct observations

Kaggle completed the notebook and produced a receipt byte-identical to the frozen package. The
single `ls20-9607627b` run stopped at the 700-second boundary after 51 environment actions in
level 1. It completed no level and scored 0.0. This is a bounded solver stop, not an engine or
manifest failure.

The controller owned all 51 environment actions. G0, G1 and G2 closed. The run installed the
84-cell counter mask, recorded the 16-item eligible roster, and preserved the counter as masked
baseline. G4 remained closed, as required while G3 had open targets.

At E0005/M0019, Duck supplied an accepted `TARGET_REACHABILITY` explanation after the bounded
semantic checkpoint. The sidecar records two completed model requests and `ACCEPTED`. The accepted
meaning was the provisional no-contact-path law: the mapped reachable component is exhausted; the
target is not thereby inert or permanently unreachable; changed reachability inputs reopen it.

The controller then reused that meaning for matching reachability targets, including E0006, E0007
and a later reopened E0005. Those answers were executor `CONTROLLER`, demonstrating that the
semantic cache was used without another Duck explanation.

The final G3 product is `G3_BUDGET_STOPPED`. It reports 16 eligible targets, pending E0007/M0021,
latest lifecycle evidence for E0005, and 11 untouched targets. The artifact is complete and
auditable; it does not claim G3 completion.

## Friction exposed

After the controller reached a G3 target for which it could not compute a deterministic route
step, it handed control to the general Duck loop. That loop used the full 4,096-token reasoning
profile and repeated non-action turns until the server request timed out. The run therefore spent
the remaining boundary on route judgment rather than on the target sweep.

The semantic request log also recorded the agent's default metadata (`thinking=true`,
`max_output_tokens=4096`) even though the N5.1 call path supplied the compact overrides. The
request payload itself carried the required tool choice and omitted the image, but the log could
not prove the override values. This is an observability defect, not evidence that the provider
ignored the overrides.

## Grade

N5.1 passes its own exit criteria:

- the first semantic explanation was bounded and accepted;
- the allowance persisted across solver turns;
- the controller reused the accepted meaning for sibling/reopened targets;
- the bounded G3 product preserved the pending target, evidence and exact roster count;
- G4 stayed closed.

The overall G3 gate does not pass. The lever frontier was not exhausted, no positive lever inventory
was accepted, and the run did not reach G4.

## Next build

N5.2 bounds the specific controller-to-Duck route handoff. It gives one compact action-choice
request for the current certified G3 revision, with required tool use, thinking disabled and a
256-token ceiling. A successful action returns control to the controller after the new frame. A
failed or empty choice emits `G3_ROUTE_RETRY_EXHAUSTED` with a complete G3 product instead of
repeating the full model loop. The request log now records effective override metadata.

— **Sol**
