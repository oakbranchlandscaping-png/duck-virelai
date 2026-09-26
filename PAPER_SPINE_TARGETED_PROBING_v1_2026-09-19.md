# Paper spine: targeted probing and the growing world model

**Type:** `PAPER_SPINE_TARGETED_PROBING` · **v1** · **2026-09-19**
**Author:** collaborator seat (Cowork), for the Director
**Evidence as of:** Ring 9 local suite 269 passed (direct observation, this session, Linux
CPython 3.12.14 against the mounted tree); the Ring 9 G0–G2 Kaggle checkpoint QUEUED, package
`ff0b5553…d4fe`, ungraded. Every numeric claim below carries its evidence class per the
provenance discipline: **direct observation / builder report / hypothesis**.

---

## 1 · The thesis, and the shape of the argument

The Director's thesis, verbatim:

> Intelligence comes from targeted probing of a novel world along with a growing internal world
> model — probing to understand the world, building an internal model, and then observing a win
> and describing the goal in the language of that internal model.

A thesis is not a paper claim. The paper argues it by demonstration: a deterministic controller
(Virelai) that forces a frontier LLM agent (Duck) to behave like a cybernetic scientist —
one bounded epistemic target at a time, evidence before belief, prediction before observation,
the win observed rather than guessed — and the measurements of what that discipline produces.
The argumentative shape is a ladder of five claims, each independently falsifiable, each tagged
with what currently supports it.

## 2 · Positioning

ARC-AGI-3 is interactive with no rules explained; the agent must discover the goal itself. The
current field baseline is Tufa Labs' Duck harness — the open-source winner of Milestone 1 at
1.21% on Qwen 3.6 27B — and before it the preview-competition winners (StochasticGoose, Blind
Squirrel), which the benchmark authors themselves characterize as informed search: exploring as
much of the action space as possible in the hope of encountering a winning combination by
chance (`ARC_3_Official.pdf`, §6.1). The paper's position: the alternative to search-by-chance
is uncertainty reduction by structured interaction — and rather than replacing the LLM, we
govern it. Duck keeps the reasoning; Virelai owns the epistemics. This builds *on* the winning
harness (its prompt discipline, tool sandbox, and action bridge are the enforcement points,
handoff §5.1) rather than beside it, which makes the comparison clean: same model, same harness
lineage, gated versus ungated.

## 3 · The claim ladder

**C1 — Enforceable scientific method.** A deterministic controller can constrain an LLM agent's
investigation to a gated target sequence (G0–G9) with server-authored capability tokens, exact
action binding, lossless before/after evidence joins, prospective predictions, and scoped
verification — such that the software never answers the semantic question on Duck's behalf and
confident prose cannot skip a demonstration.
*Evidence:* direct observation — the Ring 9 source and its 269-test suite ran green in this
session (`variants/ring9-cybernetic-gates/ARC3-Inference`); gate contracts reject label-only
answers, mismatched evidence citations, stale tokens, and out-of-order probes
(`tests/test_counter_gate.py`, `tests/test_virelai_gates.py`). Builder report — the G0 Kaggle
checkpoint completed on three worlds with exact protocol compliance
(`CURRENT_BUILD_MAP_CYBERNETIC_DUCK_2026-09-19.md`).

**C2 — Targeted probing beats enumeration.** Representative-first coverage with explicit
unknowns replaces exhaustive coordinate sweeps without licensing false inertness claims.
*Evidence:* builder report — recorded ft09 coverage falls from 65 automatic coordinate probes to
8 initial representatives with expansion only on within-class disagreement
(`BUILD_SLICE_H4_ADAPTIVE_DELPHI_COVERAGE_2026-09-19.md`); the cancelled vc33 G1 pilot is the
negative control, where the pre-repair controller forced a coordinate sweep a click-only action
surface had already answered (handoff §7.2).

**C3 — The growing world model is evidence-linked, falsifiable machinery, not record
accumulation.** Counter discovery as a conserved two-object exchange over the total site ledger;
a prospective rate prediction frozen before its confirming transition; a min/max boundary lock
requiring an observed consequence; a reversible mask that never mutates the raw grid; quotient
state identity that stops bookkeeping noise from minting false novelty.
*Evidence:* direct observation — implemented and verified in the suite this session
(`counter_verification.py`, `masked_world_state.py`, `test_counter_gate.py`,
`test_masked_world_state.py`). Builder report — the continuity-shadow key replay graded 13/13
correct identity judgments versus 8/13 for a shape-hash comparator, zero false links, on a
two-world key (narrow result, stated as such;
`runs/ring8-golden-weave-key-replay-v4-20260907/continuity_grade.json`). The historical failure
ledger (silent retrieval, undelivered cards, 1,501-question agendas with zero mechanics) is the
paper's motivation section: record accumulation is not model growth (handoff §9; institutional
memory §7).

**C4 — Live semantic understanding under the gate. THE LINCHPIN, PENDING.** Duck, gated,
correctly identifies and explains its ego and the world's bookkeeping process in live worlds —
explanation, competing model, falsifier, prospective demonstration, boundary lock — graded by a
receipt-bound evaluator and a human frame review.
*Evidence:* none yet. The G0–G2 checkpoint (vc33, ft09, ls20; 48 actions and 1,800 s per world;
Qwen 3.6 27B; gated) is QUEUED as notebook v1. The grading instrument now exists:
`tools/evaluate_g2_counter_checkpoint.py` (this session; spec at
`BUILD_SPEC_G2_EVALUATOR_v1_2026-09-19.md`), joining `tools/evaluate_gated_checkpoint.py` for
G0/G1. Dispositions are `PASS / FAIL / REPRESENTATION_GAP / BUDGET_EXHAUSTED / NOT_REACHED`,
and a later gate is never graded failed when its prerequisite never closed. The paper cannot
ship its central demonstration until this run (or a successor) is graded.

**C5 — Behavioral and score consequence. NOT CLAIMED in v1.** Single stochastic runs establish
no treatment effect (Ring 8 effects/clock evaluations; decision-controller v2's two ft09 levels).
The paper reports these as exploratory measurements with their caveats, or omits them. Score
claims require identical-cohort repeated runs — future work, stated plainly.

## 4 · Honest ledger for the paper

The paper may not say: that any prior system had universally zero level-2 success (falsified by
the decision-controller v2 benchmark); that local tests demonstrate live understanding; that
local score sums are leaderboard percentages; that the continuity key result generalizes past
its two-world key; that H4's probe reduction has demonstrated live semantic benefit; that the
mask/state machinery has ever run against a live Kaggle world. Every one of these has been true
in draft form somewhere in the archive at some point — the version discipline exists because
coherent prose outruns evidence.

## 5 · Proposed section skeleton

1. Introduction — the thesis; search-by-chance versus structured uncertainty reduction.
2. Related work — ARC-AGI-3, the Duck harness, preview-competition winners, world-model agents.
3. Architecture — the cybernetic target tree; the gate contract anatomy (token, probe, evidence
   join, answer contract, prospective demonstration, product, reopening).
4. The evidence substrate — flip-book ontology, pixel arithmetic, total site ledger, HUD/world
   quotient (C3).
5. Targeted probing — adaptive representative-first coverage (C2).
6. Live evaluation — the checkpoint protocol, receipt binding, six-grade evaluation, human
   review (C4, the results section).
7. Failure museum — the historical failure classes as design forces (this is a strength of the
   paper, not an embarrassment: twelve named classes, each with a structural repair).
8. Limitations and non-claims (C5, the honest ledger).
9. Future work — G3–G9, observed-win explanation, cross-level transfer.

## 6 · What upgrades what

Grading the queued run upgrades C4 from hypothesis to direct observation (in either direction —
a FAIL with named checks is a publishable negative result under this design). A second identical
gated-versus-ungated cohort begins C5. G3 lever laws extend C3 from bookkeeping to causal
structure. Nothing else in the ladder waits on anything remote: C1–C3 are citable today at the
evidence classes stated above.

---

*The spine is the deliverable of this slice. The next paper action after run grading: draft §6
from the evaluator's JSON report and review packet, whatever the dispositions are.*
