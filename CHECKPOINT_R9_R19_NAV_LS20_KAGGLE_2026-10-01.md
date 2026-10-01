# R9-R19 ls20 NAV checkpoint

**Builder:** Sol (Alpha build seat), signed
**Source:** `72adbe3`
**World:** `ls20-9607627b`
**Path:** private Kaggle notebook with offline local vLLM
**Model:** `vrfai/Qwen3.6-27B-FP8`
**Package:** `kaggle/ring9-g4-nav-ls20-v1/`
**Scope:** one world, one pass, one concurrent job, 200-action ceiling

## Question

Can the locally completed NAV branch turn G1's observed embodied-control evidence into a stable
control map, route the ego toward one ranked visual target, and record correctly separated
APPROACH and CONTACT_ATTEMPT evidence under the G2 counter mask?

## Grading order

1. G0 assigns NAVIGATION from the displayed action surface.
2. G1 closes with a demonstrated embodied ego and a nonempty evidence-referenced control map.
3. ACTION5 is not promoted to a route bearing without observed stable ego translation.
4. G2 locks the total counter mask and stops treating counter changes as semantic progress.
5. G3 retains one ranked target through its route and labels each controller action APPROACH or
   CONTACT_ATTEMPT.
6. Planned traversal uses only demonstrated stands; an unknown landing is attempted one step at a
   time.
7. A completed contact produces a target-bound ContactEpoch and either a scoped null result, an
   attributable lever witness, a boundary record, or an explicit unresolved result.
8. No step count alone closes a target, proves inertness, or certifies unreachability.
9. If a BODY lever is confirmed, its G3 dossier carries a NAV ContactProcedure into G4.
10. If G4 opens, approach transitions do not advance an orbit or grade a prediction; terminal
    contact transitions do.

The checkpoint succeeds at the deepest criterion directly supported by its artifacts. Later
criteria are not failures if an earlier genuine friction stops the run; that friction becomes the
next build target. A level win is outside this checkpoint's success definition.

— **Sol**

## Launch record

- The paid-model attempt reached the online harness but OpenRouter rejected its first request with
  `402 weight_exceeds_budget`. It executed zero actions and consumed zero tokens.
- The user chose Kaggle rather than the free OpenRouter fallback because recent Kaggle starts have
  been faster. The Kaggle checkpoint uses the exact Qwen model family and packaging path already
  exercised by recent milestones. The OpenRouter attempt remains infrastructure evidence only.
- The frozen package was built from source commit `72adbe3`, passed all eight independent package
  checks, matched the committed source export byte for byte, and contained no detected secret.
