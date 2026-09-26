# Virelai–Duck: evidence-driven exploration agenda

Date: 2026-09-11
Status: proposed implementation plan, prepared from repository review and user discussion. No implementation or deployment is implied by this document.

## Objective

Make Virelai's method the organizing structure of Duck's play. The semantic library maintains the current understanding of the world and the questions that remain. Duck reasons about which question to investigate and how to perform the experiment. Every interaction feeds the library and changes the next agenda.

The intended loop is:

record → semantic library → unresolved questions → Duck's experiment → observation → revised library

Before the first observed win, exploration aims to understand mechanics and extend coverage. After a win, the same language expresses candidate success conditions and supports their investigation and reconstruction on subsequent levels. The grammar develops throughout exploration; neither a complete grammar nor finished exploration is required before capturing a win.

This is a hybrid extension of Virelai, not a replacement for the separate deterministic golden-run experiment. It changes the agent around the LLM; it does not train or change model weights.

## Parent and isolation

Use `variants/ring8-world-model-ontology` as the code parent. Record its exact source manifest and hashes when implementation begins: current variants include untracked files, so a Git commit alone is insufficient. Create a sibling `variants/ring8-cybernetic-agenda`. Preserve the parent and running Kaggle experiment.

Keep the model, decoding configuration, game fixtures, environment seeds, runtime budgets, and existing world-model implementation fixed initially. Record any necessary semantic corrections as separate changes and apply them to matched experiment arms; do not attribute their effects to the agenda.

All paths below are relative to the new variant's `ARC3-Inference/` unless stated otherwise.

## Responsibilities and boundaries

| Component | Owns |
|---|---|
| Immutable interaction journal | Delivered frames, action metadata, boundaries, exact before/after evidence |
| Semantic library | Derived entities, relations, scoped mechanics, current values, evidence and uncertainty |
| Exploration agenda | Questions derivable from current knowledge and coverage; evidence-based dispositions |
| Duck LLM | Choosing useful investigations, navigation, experimental design, proposals and later plans |
| Duck runtime | Tool execution, action transport, refreshed observations, existing limits and stopping behavior |

Duck remains the only gameplay actor in this variant. No golden Captain or pointer adapter executes actions behind it. The agenda is guidance with persistent progress, not an action veto. A model can depart from the suggested focus; record that departure and its stated reason rather than blocking it.

Facts, inferred interpretations, candidate explanations, and working intentions must remain distinguishable. The agenda is a derived view of the canonical library and journal, not another semantic store. Raw evidence remains available when the library is wrong or incomplete. A proposal from the LLM never makes a question evidentially closed by itself.

## The method as an agenda

1. Establish the channel of control: embodied ego, pointer interaction, or evidence for both. An offered action supports an interface hypothesis; it is not by itself proof of a behavioral role.
2. Resolve counter/autonomous-process candidates. Separate supported recurring changes from attributed effects while retaining the process and any resource significance in the model. Changes on most actions alone do not establish independence.
3. Discover interactions and lever candidates after accounting for known control and autonomous effects. Distinguish reaching a target, successfully interacting, and observing an effect.
4. Deepen ego, counter, and lever subtrees: magnitude, conditions, recurrence, limits, joint effects, reversibility, and unexplained outcomes.
5. Resolve static/inert and ground/wall relationships as evidence accrues. These can be learned incidentally earlier; they are not exclusive labels or an instruction to postpone navigation knowledge.
6. Capture any observed win immediately. Use its standing conditions, terminal interaction, and eligible non-winning evidence to formulate competing explanations.
7. At the next level, bind those explanations to new entities and reconfirm relevant mechanics. New mechanisms reopen investigation locally.

This is an ordering of attention, not a ban on observing later-stage evidence. Missing or unresolved roles cannot deadlock the run. Where a prerequisite cannot be resolved with supported tests, retain it as unknown/deferred and allow other informative coverage. No hard-coded number of actions establishes that a role is absent.

The schema must reserve SEARCH as coverage-directed exploration after relative saturation. Do not claim golden's full saturation or completeness certificate before the required subtrees and frontier are implemented. An empty current agenda is not proof of a complete world model.

## Data contract

Add `inference/framework/virelai_agenda.py` with a pure compiler and immutable question/snapshot types. Names are proposed interfaces, not claims that they already exist.

`compile_agenda(model, evidence_index) -> AgendaSnapshot`

Snapshot fields:
- schema, game/level namespace, model version, observed-through and compiled-through boundaries;
- current focus and reason, first-win-observed state, candidate goal references;
- active questions, deferred questions, resolved questions, newly reopened questions;
- freshness and compiler limitations.

Question fields:
- stable ID anchored to entity/relation identity and question kind, independent of inferred role names;
- subject references, question kind, plain-language question;
- prerequisites and current evidence references;
- disposition: OPEN, CLOSED_BY_DATA, CLOSED_BY_PROBE, DEFERRED;
- recorded support and counterexamples; scope and remaining limitations;
- distinguishable outcomes where the current representation can express them;
- activation constraints and reachability uncertainty, without a mandatory action;
- an explanation of why this question is currently useful.

Reopening is a recorded disposition change when new evidence invalidates the prior answer's scope. Entity regrouping needs aliases/versioned references; recomputation must not silently assign old progress to a different object. Across levels, question templates can recur, but bindings and confirmation are fresh.

An experiment-intent record contains question IDs, proposed interaction/route, predicted alternatives or explicit UNKNOWN, and an optional reason for choosing another question. It is a separately typed record of intent, not world evidence. Malformed or missing intent is logged; it does not block play in this first implementation.

## Ordered implementation work

### A0 — Freeze the experiment and inventory producers

Create the isolated variant and source manifest. Map each first-slice question to existing fields in `virelai_world_model.py`, `virelai_semantic/compiler.py`, `mechanics.py`, golden-derived role readers, and the journal. Mark each field available, derivable, probe-required, or unavailable.

Read the ontology-run evaluation when available, but do not let a running notebook block offline implementation. Do not change or stop that run.

Gate: every first-slice question has an explicit producer and a documented meaning for insufficient evidence. Baseline tests and comparison fixtures are recorded.

### A1 — Build one read-only agenda vertically

Start with control identification, autonomous-process uncertainty, and one lever effect question. Use existing admitted observations and candidates. Preserve source candidate status; an agenda subject is not thereby an established lever.

Reuse the question/depth structure in `virelai_semantic/depth_probe.py` as design material. Do not wire its action adapter into gameplay or automatically promote its recurrence/saturation labels to truth. Its fixed observation criteria require independent grading.

Expose `virelai('agenda')` and a focused `virelai('question', id=...)` through `virelai_runtime.py`. Retain evidence queries.

Gate: recorded prefixes generate deterministic questions, existing evidence can close a question without another action, and unavailable evidence produces an explicit unknown rather than a fabricated answer.

### A2 — Supply working context automatically

Add `inference/framework/virelai_agenda_view.py`: a pure renderer of the agenda and canonical model. In `agent/tool_agent.py::_build_user_prompt`, insert a compact current focus, up to three useful questions, relevant entities/relationships, and changes since the previous snapshot. Provide focused retrieval for omitted detail.

Every rendered claim refers to the snapshot used. Compile at most once per journal boundary and share the result with existing queries. Start by measuring the current synchronous compiler; for longer records use an incremental cache or a last-complete snapshot with explicit staleness. Never describe a stale position as a current targeting coordinate. Refresh lightweight agenda state after action results; stop relying on a snapshot after a level boundary.

Provisional engineering budget: default agenda addition ≤600 tokens, no silent truncation, and compilation/query time ≤5% of per-game wall budget on representative replay. These are explicit budgets to measure and revise, not epistemic thresholds. Failed observer work must preserve the journal and leave Duck able to inspect the environment.

Gate: normal turns and new-level turns receive the appropriate view without requiring a ceremonial tool call; no duplicate compilation per evidence boundary; errors and staleness are visible.

### A3 — Reconcile the entire prompt policy

Create `agent/virelai_strategy.py` for the operational procedure. Update `virelai_ontology.py`, prompt constants, `_build_system_prompt`, `_build_user_prompt`, tool descriptions, and no-tool follow-up messages together.

Remove contradictory hybrid guidance: unconditional goal guessing before a first win, shape-hash equality as identity proof, appearance-based background/counter verdicts, and reconstruction of a competing authoritative prose world model. Retain basic tool instructions, raw observation access, and useful computational methods.

Clarify ontology ambiguities: pointer ego versus absence of an embodied body; roles as supported, potentially overlapping relations; visible address versus hidden state; and recurrence/conservation as scoped evidence rather than universal proof. Express golden's premises as the hybrid's chosen method, not undocumented benchmark guarantees.

Keep LLM working notes as hypotheses and intentions referencing library claims. Replace retry steering with the current agenda question or post-win explanation task. Preserve baseline/off-mode behavior where that mode remains supported.

Gate: inspect fully assembled initial, ordinary, retry, and level-transition prompts. Tests assert both required procedure and removal of conflicting instructions; adding the words 'Virelai' or 'ontology' is not sufficient.

### A4 — Close the question/action/result loop

Add an optional structured `virelai('intent', ...)` route, explicitly separate from read-only queries. Extend the sandbox bridge and observer dispatch only for this typed intent message. Associate it with subsequent executed transitions until replaced or ended. Record planned and actual action counts, interrupted batches, and model-version references.

After interactions, derive outcomes from evidence: not reached, interaction attempted with no observed effect, changed, contradiction, unresolved. Compare structured predictions only where evaluators exist; otherwise mark the comparison unevaluated. A new observation alone does not prove the question was answered.

Navigation, resets, necessary repetition, and incidental discovery remain allowed. An intent does not license a blind long batch. Existing terminal stops stay intact, and prompts require checking state when conditions change.

Gate: fixtures distinguish failed access from an inert response; an LLM claim of success cannot close a question; contradictory observations reopen the appropriate scope; intent transport cannot trigger a game action.

### A5 — Extend the subtree coverage

Add questions by producer maturity: control bearings and refusal conditions; autonomous schedules and exceptions; lever targets and joint updates; repeated response versus cycle; observed limits versus conditional inactivity; opposing changes versus true reversibility; relevant ground and wall relations.

Carry grouped entities, self-reactive channels, and shared-control relations through the canonical adapter where currently omitted. Grade each addition separately. Keep unresolved target identity and bounding-box-only correspondence explicit; neither can establish exact effect-support identity.

Gate: each exposed answer predicts a checkable outcome or states its limitation. Use held-out chronological prefixes: inference sees only the prefix, evaluation sees the subsequent interaction. A fitted replay is not evidence of novel prediction.

### A6 — Join observed wins and next-level reconstruction

Use existing win capsules and lessons as inputs. Record whether the actual winning render is available; never mistake successor spawn for the winning configuration. Add hypothesis structures referencing entities, variables, relationships, standing conditions, and terminal updates. Evaluate eligible earlier non-winning states, retaining alternatives and UNKNOWN evaluations.

Do not turn several surviving alternative predicates into a proven conjunction. One win need not identify a necessary or sufficient condition. Preserve any unexplained part of the boundary.

At a level change, reopen binding and mechanism questions locally. Only a confirmed new-level instantiation can test the transferred schema; visual resemblance alone is insufficient. A changed mechanic must not erase unrelated supported history.

Gate: a prefix ending before a win has no observed-win explanation; a boundary creates an explanation task even with unfinished subtrees; next-level bindings begin unconfirmed; raw record and prior evidence survive.

## Tests and evaluation

Use and extend the existing tests for native observer integration, world model, semantic library, lever depth, transition briefings, level carry, and win capsules. Add `tests/test_virelai_agenda.py` and `tests/test_virelai_strategy.py` for the new behavior.

Required fixtures include an embodied and a pointer world; an unresolved autonomous process; a blocked target; a zero-effect interaction; ambiguous identity; a surprising outcome; reset; a win during unfinished exploration; and a new-level mechanic change. Include authored controlled fixtures for causal distinctions that existing recordings cannot establish. Do not inspect hidden game implementations to supply the agent with answers.

Primary measurements:
- agenda correctness against a hand-labeled question/evidence key;
- whether answers are derivable from the cited prefix;
- useful question resolution per action, including wasted repeats with navigation separated;
- unsupported assertions and incorrect identity/role promotions;
- held-out transition predictions and appropriate abstention;
- observed use of library claims in model decisions, not just call counts;
- next-level transfer and action efficiency, with level difficulty acknowledged;
- token cost, latency, staleness, archive integrity, and observer failures.

Freeze a small diagnostic set before live tests, then evaluate broader unseen worlds to detect tuning to the familiar canaries. Keep model and budgets matched. Pair environment seeds and repeat runs; record model nondeterminism rather than assuming a seed removes it.

Comparison arms:
1. Existing ontology/manual variant: immediate control.
2. Reconciled Virelai strategy only: same semantic machinery, no automatic agenda.
3. Full strategy plus automatic agenda and outcome feedback: proposed agent.

Use baseline Duck as a secondary reference. The control already has automatic boundary briefings, so zero voluntary calls is not zero Virelai exposure. If the full arm changes several mechanisms together, attribute any difference to the package; add component ablations only where results justify them.

Run recorded checks first, then a small matched live set, then the broader Kaggle campaign. Publishing or launching a new external run is a separate action from preparing this plan. The current notebook remains unchanged.

## First deliverable and completion standard

First deliverable: on one recorded world prefix, a compact agenda identifies a real unresolved control/counter/lever question, displays its supporting evidence, and updates appropriately after the next observation. The same agenda appears automatically in Duck's context without choosing an action for it.

Full completion requires a traceable live loop: Duck uses a library-grounded question to choose an experiment; the observation changes the library and agenda; an encountered win creates an evidence-linked explanation; that explanation guides a reconfirmed attempt on a later level. Report failures and unknowns as well as successes. Merely calling Virelai or repeating its terminology does not meet the objective.

## Source basis

- `golden_chamber/CANON_3_BUILD_PLAN_v1.md`, §§3–8 and §§11–14: library-side questions, thin captain, probing, observed win, and carry.
- `golden_chamber/sealed/02_concept/SPEC_LIBRARY_WORLD_MODEL_v1_2026-07-20.md`: the library as the world model and integrated learning loop.
- `duck-virelai/TARGET_SEMANTIC_LIBRARY_PLAYER_BRIEF_v1_2026-08-30.md`: operational dossiers and player-usefulness test; its older Captain handoff is historical context.
- `duck-virelai/BUILD_PLAN_RING8_PERSISTENT_WORLD_MODEL_v1_2026-09-10.md`: current hybrid memory architecture.
- `duck-virelai/variants/ring8-world-model-ontology/`: implementation parent, including runtime, semantic compiler, prompt assembly, and tests.

These documents inform the design. Their historical approval language and build commands are not additional user instructions.
