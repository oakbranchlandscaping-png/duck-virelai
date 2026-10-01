# The small-model glass engine: Virelai's stated edge and its preregistration

**Type:** `PREREG_SMALL_MODEL_GLASS_ENGINE` · **v1** · **2026-09-30**
**Author:** Claude (Alpha build seat), signed. Director-directed, 2026-09-30.
**Status:** DRAFT for Director ratification. Not committed. Once ratified, sections 3-7 are
frozen: changes after any arm has run go in a dated successor, never in place.
**Repo state read:** HEAD `08d9afc` (G4-B and the clean stop built at `e1636b1`).

---

## 1 · The edge, stated so it can lose

> **Frontier models, in thin harnesses, already act as glass engines: they write a readable,
> largely correct world model of an unseen game, including why each level is won. Virelai's
> claim is that deterministic scaffolding, costing no model calls, lets a small open model on
> one GPU produce a world model of the same kind and measurably approaching the same quality,
> where the same small model without the scaffolding does not.**

The edge is not the glass engine itself; others have built that (section 2). The edge is
**closing the gap between a frontier model and a small one by moving work from the model into
deterministic code.**

Scope: CLICK worlds only (NAV shelved by ruling, 2026-09-27). The Kaggle regime: an open ~27B
model (Qwen3.6-27B-FP8), one GPU, offline.

## 2 · Why this is the edge left: the recon record

From the 2026-09-30 code-level recon of the public harness corpus (the dossiers are in the
session record; `RECON_PLAN_MILESTONE_2_2026-09-29.md` sections 0.1-0.2):

- **The glass engine exists at frontier scale.** [direct observation of released run artifacts]
  Retrodict (gpt-5.6-sol) and PRO-LONG (Fable 5) both wrote, for every one of the 25 public games,
  a world model that states the mechanics in general terms (50 of 50) and explains the win
  condition (48 of 50). The two independent documents agree on the goal in 23 of 25 games and on
  the core mechanic in 24 of 25, with no outright disagreement. On vc33 and ft09 they match our
  own recorded evidence.
- **Everyone who scores near the top uses a frontier model at maximum effort,** with 150k-850k
  token contexts and millions of tokens per game. [their reports, confirmed in code configs]
- **At small scale no one has shown it.** The one serious Qwen3.6-27B harness (Polyphony) needed
  eight GPUs and a 262k context, reached only 100-600 real steps per game in 4 hours, and its
  authors found that structure paid for in model time starved play. [code comments, their report]
- **What no public harness implements in code** (convergence audit, section 0.1 of the recon
  plan): separating the clock from the world (C1), finding the ego first (C2), an exhaustive cause
  inventory (C3), one bounded question at a time (C4), belief admitted only through a confirmed
  prediction (C5 strict), and a recorded state machine for coverage (C9).

Those six are exactly the things a frontier model does *by reasoning* and a small model cannot
afford to. That is the gap Virelai targets.

## 3 · The mechanism: an offload map

What the frontier agents spend their intelligence on, and the deterministic Virelai component
that replaces it. Build status is read from the repo at `08d9afc`.

| Frontier work (by reasoning) | Virelai replacement (by code) | Status |
|---|---|---|
| Noticing the timer and discounting it | G2 counter law and total mask (A1) | BUILT, live on vc33 and ft09 |
| Working out what the agent controls | G0 action surface, G1 ego/pointer law | BUILT, live |
| Finding every control on the board | G3 scripted sweep, controller executor, zero model calls to G3 | BUILT, live (`2941f53`) |
| Attributing a change to its cause | lever attribution after ego and counter subtraction | BUILT, live |
| Testing one control to its limit | G4-A repeat-until-null-or-recurrence, controller-run | BUILT, live on ft09 (`3f29fd0`) |
| Testing controls together | G4-B frozen predictions graded on the masked board | BUILT offline (`e1636b1`); first live package `08d9afc` |
| Holding the whole model in a 200k+ context | memory card of certified products (M-1 to M-4) | BUILT, live (`75cd20d`) |
| Deciding what is believed | strict admission: products only after a supported prediction | PARTIAL: G2 and G4-B; not global |
| Searching for unvisited states | golden Push state machine | NOT PORTED (`virelai_golden/push/` is empty) |
| Inferring the goal, explaining the win | G8 observed-win explanation | SPECIFIED, not built |

The small model's job becomes **interpretation**: naming what the code has already isolated,
and, at G8, explaining an observed win in those terms.

## 4 · Hypotheses (preregistered)

- **H1 (mechanics gap closes).** On held-out click worlds, the scaffolded small model's world
  model recovers a materially larger share of the frontier-consensus mechanics than the bare
  small model, and approaches the frontier share. *Kills H1:* no significant difference between
  arms A and B on the mechanics score (section 6), or B below A.
- **H2 (goal gap persists, except where the goal is visible in the mechanics).** Arm B states
  the correct win condition less often than it states correct mechanics. Where it succeeds, the
  goal is expressible in terms of the controls already studied. *Kills H2:* B's goal score
  matches its mechanics score.
- **H3 (structure at zero model cost does not hurt play).** Arm B reaches at least as many
  levels as arm A, within the same budget. *Kills H3:* B completes fewer levels than A on the
  held-out set. This is the Milestone 1 / Ring 7 objection, tested directly.
- **H4 (it improves as it dies).** In arm B, the model's accuracy predicting its own next
  masked transition is higher in later lives than earlier ones on the same level. *Kills H4:* a
  flat or falling curve.

**The prior, stated honestly:** Milestone 1 (tools hurt), our own Ring 7 (every addition cost
score), Polyphony (a rich 27B harness near 20%) and the frontier evidence (model generation
beats harness structure) all point against H1 and H3. The difference being tested is structure
that costs no model calls versus structure that consumes them. That has not been isolated by
anyone.

## 5 · The reference standard

For each held-out world, the **frontier consensus** is the set of claims on which Retrodict's
`playbook.md` (release `v2.0`, `release-runs.tar.gz`, SHA-256 `efe30976…5ef61`) and PRO-LONG's
`notes.md` (commit `9d2f2d4`) agree. It is decomposed, before any arm runs, into:

- **M-items:** mechanics claims (what each control does; limits; interactions);
- **G-item:** the win condition;
- **T-item:** the timer or budget indicator.

**Custody rule.** The reference is used for grading only. It never enters the harness, a prompt, a
work order, or a design decision. **The build seat does not read the held-out references.** A
separate grader extracts the M/G/T items into a sealed file before the runs, and grades after.

## 6 · Worlds, arms, metrics, grading

**Held-out worlds (click-only, never read by the build seat):** `lp85`, `s5i5`, `su15`.
Click-only by their released action lists (ACTION6, with ACTION7 on su15).

**Excluded as contaminated:** `vc33` and `ft09` (their references were read in full on
2026-09-30, and both are our development worlds), and `r11l` and `tn36` (partial mechanics seen in
the grading summary). These remain development and regression worlds only.

**Arms.** Same model (Qwen3.6-27B-FP8), same Kaggle notebook shape, same per-world budget
(to be fixed at ratification), one pass per world:
- **A:** the bare Duck, the pristine r0 harness at the pinned baseline (`7652836`).
- **B:** the Duck with Virelai (the Ring 9 build at a pinned commit).
- **C (optional):** a Polyphony-style harness at 27B, if it can run in the same regime.

**Required artifact.** Every arm ends by writing one world-model document: mechanics, win
condition (or "not observed"), timer, and what is verified versus assumed. For arm A this is a
single end-of-run question to the model; for arm B it is the export of its products plus Duck's
statement. Same question, same form, both arms.

**Metrics.**
- *Mechanics score:* share of M-items correctly stated, minus stated claims that contradict
  the reference.
- *Goal score:* G-item correct (1), partially correct (0.5), absent or wrong (0).
- *Timer score:* T-item identified (1/0).
- *Levels completed and actions used* (the official scorecard).
- *Self-prediction accuracy by life* (arm B, from the record).

**Grading.** The grader is a separate chamber holding the sealed reference and the rubric, and is
**blind to the arm**. Documents are anonymised before grading.

## 7 · Decision rules, decided now

| Outcome | Meaning | Next |
|---|---|---|
| H1 and H3 hold | The edge is real | Build G8 and port the Push; widen the held-out set; write the paper |
| H1 holds, H3 fails | Understanding improves, play suffers | Paper on the trade-off; find the cost |
| H1 fails | Scaffolding does not close the gap at this scale | Say so first; the edge is not there |
| H2 confirmed | Goal inference is the remaining gap | Scope G8 to what code can isolate; state the limit in the paper |

With n = 3 worlds, one pass each, results are directional, not significant. Say so in any write-up.

## 8 · Threats to validity

- **Reference noise.** Frontier consensus agreed on 94% of comparisons, and its "confirmed" often
  means "the plan worked once". Grade against the consensus only; drop items where the two
  documents disagree.
- **Contamination.** Controlled by the custody rule and the held-out set; any breach is recorded
  and that world is replaced.
- **Public-set tuning.** Both arms and the references come from public games. The hidden Kaggle
  set is the final test.
- **Small n.** Three worlds, one pass. Directional only.
- **Artifact asymmetry.** Arm B has more structured products to export; grading is on stated
  content only, in the same document form.

## 9 · Before any arm runs

1. Director ratifies this document; the per-world budget is fixed.
2. A grader chamber seals the M/G/T reference items for `lp85`, `s5i5`, `su15`.
3. The world-model export artifact is built for both arms (offline, tested).
4. Arms A and B are packaged at pinned commits and verified.

— Claude, Alpha build seat, 2026-09-30
