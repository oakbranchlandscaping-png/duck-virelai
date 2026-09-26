# Virelai × Duck campaign recap through Ring 6.2

**Audience:** a new team member with access to this workspace  
**Status date:** 2026-08-30  
**Current work:** Ring 6.3, a handshake-only repair  
**Authority:** this is the current campaign-level account. Older manifests remain valuable
organic build records, but any pre-run claim that conflicts with the completed Ring 6.1 or
Ring 6.2 artifacts is superseded here.

## 1. The project in one page

We are building an ARC-AGI-3 solver by placing Tufa Labs' Duck LLM harness inside a larger
cognitive architecture called Virelai.

Duck already supplies the LLM, the iterative tool-use loop, the runtime view of the game,
and the Kaggle execution interface. Our hypothesis is that the same model will reason better
if we give it two additional forms of structure:

1. **Above the model: an ARC Grid Multiverse Ontology.** This states what can be known about
   every ARC world: grids are observations of state; actions create transitions; identical
   visible grids may conceal different hidden states; roles must be earned from behavior;
   and wins are observed through platform transitions rather than guessed from appearance.
2. **Below the model: a world-specific empirical system.** Virelai segments cells into
   forms, tracks forms through time, records the effects of controlled actions, builds
   persistent objects, separates ego and counter noise, and identifies causal roles such as
   levers. The resulting state-transition account is the world's **physics grammar**.

The model sits between the universal and the particular:

```text
ARC Grid Multiverse Ontology
              ↓
            Duck LLM
              ↑
Captain probe → perception → weave → world-specific report
```

The immediate proof of concept is intentionally narrow:

> Let the deterministic V4 Captain spend a bounded opening phase learning level 1, render
> what it learned as a compact field card, give that exact card to Duck before Duck's first
> token, and then let Duck play from the resulting live state.

We have now proven that the Captain can execute reliably inside Kaggle. We have **not** yet
proven the information transfer. Ring 6.3 exists to close that exact gap.

## 2. The ARC stance we are testing

The external ARC-AGI-3 and Duck-harness sweep led us to treat these games as interactive
state machines exposed through successive grids. In the current harness, Duck sees a 64×64
colored grid, a set of currently legal actions, and platform-reported level/game state.
Depending on the world, actions can include directional movement, SPACE, MOUSE, ACTION7,
and RESET.

The ontology currently shipped in `inference/agent/prompts.py` is deliberately general. Its
main commitments are:

- A grid is an observation of state, not proof that all state is visible.
- Knowledge comes from observed before/action/after transitions.
- Objects and roles are explanatory models over cell relationships, not facts supplied by
  a color, shape, or location.
- An ego is evidenced by controlled action-dependent change.
- A counter is evidenced by repeated change that is not explained by the chosen target or
  action.
- A lever is established by an intervention and a repeatable remote effect after ego and
  counter change have been excluded.
- Divergent transitions from apparently identical visible situations are evidence of hidden
  state.
- A win is first known only when the environment reports a level or game transition.
- A rule must predict an observable result and state what future evidence would falsify it.
- A rule that won one level is evidence for the next, not a universal guarantee.

The practical search rule derived from this is:

> Before the first observed win, seek novel reachable transitions rather than trying to
> imagine a winning picture. Every visited still-playing state is already a known non-win.
> Once a win is observed, preserve its transition as a tested example and then explain and
> falsify the proposed rule.

This separates the two future phases:

- **Phase 1:** reliably encounter a level-1 win and hand the learned world to Duck.
- **Phase 2:** analyze why that transition won, carry the rule into the next level, and let
  the Captain return when the prediction fails. Phase 2 is not built yet.

## 3. What “the Captain” means

The Captain is not another LLM. It is a deterministic, stateful cybernetic targeting
system. The useful mental model is a Turing-like machine whose tape is the accumulated
transition record and whose next move is selected by an ordered probing policy.

Its intended opening logic is:

1. **Delphi gambit:** determine what kind of world this is from the action roster.
2. **Find the ego:** in navigation worlds, identify which persistent form is under direct
   control and learn the action-to-bearing map.
3. **Find and mask the counter:** systematically act on or collide with visual objects;
   repeated autonomous change is separated from world change so it stops minting false
   states and false causal attributions.
4. **Broad sweep:** in CLICK worlds, click identified visual forms; in NAV worlds, route the
   ego into contact with them. This is how the system discovers which unknowns matter.
5. **Object depth:** once a semantic role emerges, probe it asymmetrically. A possible lever
   deserves repeated, focused tests: its affected region, directionality, period, toggle or
   cycle law, saturation, and one-shot behavior.
6. **Continue through a win:** a level transition is an observation worth preserving, not a
   reason to discard the record immediately.

The actual V4 policy is more algorithmic than an ideal “most valuable unknown” chooser. It
uses ordered dispatch, sweep lists, gates, and fallback paths. It does not globally score
every unknown by expected information value. Our present strategic reading is therefore:

- broad coverage first;
- ego and counter early because masking them removes noise;
- then depth around causal candidates, especially levers.

Current capability is asymmetric by world type:

- **CLICK:** V4 can sweep visual targets, often find counter-like regions and levers, and
  produce a rich description.
- **NAV:** V4 can usually find the ego and label objects, but the “collide with everything”
  sweep is incomplete. Routing, arrival, obstruction, and reliable contact remain the main
  Captain-side weakness.

We deliberately accepted that incomplete Captain because the existing weave already looked
rich enough to test the larger hypothesis: does a structured report improve Duck? That is
the test the Ring 6.x ladder is trying to reach.

## 4. Where the ideas and code live

This workspace is an organic growth record. Some documents describe ideas later replaced.
Read by provenance and date; do not assume every attractive design in an old folder remains
current.

### Workspace-level sources

| Path | Role |
|---|---|
| `virelai_v4/` | Current golden Captain implementation and the most mature perception, weave, targeting, and library code. Start with `docs/core/` and `docs/golden_run/`. |
| `Universal_Solver_v3_5/` | Earlier universal solver. Important for the expandable field-card presentation, ontology work, falsification structure, and the idea of feeding a compiled world account to an LLM. |
| `duck-virelai/` | The live experimental and Kaggle repository. This is where Tufa/Duck, Virelai integration variants, bundles, and downloaded runs are kept. |
| `virelai-resource/`, `golden_chamber/`, `ring6/` | Supporting and archival build material. Useful for provenance, but not the current shipped authority. |

### Inside `duck-virelai/`

| Path | Role |
|---|---|
| `baseline/duck-harness/` | Frozen Tufa/Duck baseline. Treat as read-only. |
| `variants/` | Source trees for experimental rings. Each ring's manifest records its intended one-variable change and build history. |
| `kaggle/` | Assembled Kaggle source-dataset and kernel bundles. These are deployment artifacts, not the best place to author changes. |
| `runs/` | Downloaded Kaggle outputs and post-run evaluations. For claims about what actually happened, these outrank pre-run manifests. |
| `RULING.md` | Project charter and disclosure boundary. |

Naming trap: there is no separate `variants/ring6.1/`. The Ring 6.1 source is under
`variants/ring6/`, its bundle is under `kaggle/ring6/`, and its authoritative runtime label
is `duck-virelai-ring6.1`. Ring 6.2 has explicit `variants/ring6.2/` and `kaggle/ring6.2/`
directories.

The current source of record is:

```text
duck-virelai/variants/ring6.2/ARC3-Inference/
```

The exact assembled bundle that ran is:

```text
duck-virelai/kaggle/ring6.2/
```

The completed run and its authoritative evaluation are:

```text
duck-virelai/runs/kaggle-ring6.2-run1/kaggle-output/
duck-virelai/runs/kaggle-ring6.2-run1/EVALUATION.md
```

## 5. The earlier ring ladder

The pre-Captain rings built a lighter Virelai layer directly around Duck. Their main value
now is architectural ancestry and reusable machinery:

| Ring | Main contribution |
|---|---|
| Ring 1 | Per-game walked-edge ledger, compact map digest, and removal of actions proven no-op at the current state. |
| Ring 1.1 (`ring11`) | First ontology implant, reset-aware world map, and queryable runtime state. |
| Ring 2 | Counter detection and counter-masked world identity; separates HUD/autonomous churn from meaningful state change. |
| Ring 2.5 (`ring25`) | World type, light weave, persistent worldlines, and an evidence-based ego seal. |
| Ring 3 | Explicit frontier, known-route replay, drains, and first lever attribution. |
| Ring 4 | Sandbox `virelai_card()` with expandable sections and evidence/falsifier language; prompt prose shrank as machinery took over. |
| Ring 5 | Stronger ego evidence to distinguish directly controlled bodies from objects they push. |
| Ring 6.x | Replace the light opening with the complete golden V4 Captain, render its output in V3.5-style cards, and hand control to Duck. |

The intended Ring 6 opening contract is:

- Captain acts before Duck's first model call.
- Bounds are two lives, 320 actions, or 480 seconds.
- Captain actions are real game actions but cost zero generated model tokens.
- The Captain may continue after a level win.
- Each life or outgoing level is snapshotted before V4 clears level-scoped state.
- The combined report is delivered exactly once in Duck's first user prompt.
- Duck then plays alone; the Captain does not return in Phase 1.

The report format borrows V3.5's expandable field-card style while using V4's golden weave
as content. It aims to name situation, observed objects, action effects, exploration
coverage, causal relationships, gaps, and any platform-observed winning transition without
exposing internal ids or turning uncertain visual guesses into facts.

## 6. Integration frictions already encountered

Most Ring 6.x work has been systems integration rather than strategic tuning. Important
failures and lessons include:

1. **Partial-tree packaging plus deletion.** A build step used `rsync --delete` to overlay a
   diff-only variant onto a complete bundle. It deleted untouched Duck files such as
   `action_names.py`. Future overlays must preserve the complete inherited tree.
2. **V4 import location.** The vendored package initially sat at a path that did not match
   its canonical `virelai_v4...` imports or Kaggle's `sys.path`. It now lives as a sibling
   of `inference/` and is explicitly included by packaging metadata.
3. **Fault containment was incomplete.** A Captain import/construction error happened before
   the guarded probe loop and crashed the whole game. Optional setup now sits inside the
   same containment boundary; a Captain failure must cost only the report, never Duck's run.
4. **Action-data protocol mismatch.** V4 forwarded arcengine's internal action model dump.
   Simple actions carried an internal `game_id`, while TAAF requires `{}`. Ring 6.2 created
   an explicit bridge: `{}` for simple actions and public integer `x`/`y` only for MOUSE.
5. **RESET and life boundaries.** CLICK probes that reached GAME_OVER exposed failures when
   the Captain attempted RESET. The explicit action bridge fixed this class too.
6. **Bundle hygiene.** `__pycache__` and `.pyc` repeatedly rode into source variants and
   assembled bundles. Every build must check both locations.
7. **Label drift.** Folder names, dataset ids, kernel ids, benchmark labels, and output
   directory names have not always agreed. The benchmark's runtime label is the final
   authority for a run.
8. **Kaggle execution semantics.** Dataset/kernel pushes upload versions but do not execute
   the notebook. The browser's Save & Run All starts the job. These development runs are
   preserved and graded but not submitted.
9. **Marker semantics.** A marker can prove that code reached a line, not that downstream
   content actually entered a model request. Ring 6.2 made this distinction unavoidable.
10. **Artifact sufficiency.** If exact one-shot content is not persisted, it cannot be
    audited after a two-hour run. Future rings must save the report itself, not only its
    character count.

## 7. The Ring 6.0–6.2 evidence ladder

### Ring 6.0: contemporary no-Captain control

Saved under `runs/kaggle-ring6.0-run1/`. Its downloaded benchmark is internally labelled
`duck-virelai-ring5`, and it contains no Captain markers. It is useful as the nearest
contemporary control, not as a pristine frozen-Tufa baseline.

- Levels completed: 6
- Games clearing at least one level: 6
- Aggregate score: 6.331551
- Total actions: 2,570
- Generated tokens: 1,403,454

### Ring 6.1: probe wiring reached Kaggle, action bridge failed

Ring 6.1 established the outer execution order and fault containment, but 24 of 25 Captain
phases ended in `ValueError`:

- 18 games faulted before a Captain action.
- 7 games sustained some probing.
- 5 CLICK runs reached GAME_OVER and then faulted at the life boundary.
- 602 Captain actions and 2,460 Duck actions were recorded.
- Captain produced two level advances; Duck produced seven.
- Total: 9 levels across 8 games; aggregate score 9.568701.

The first post-run evaluation said the technical handoff passed because all 25 games emitted
`PROBE_START → PROBE_END → CARD_INJECTED → DUCK_FIRST_ACTION`. The later Ring 6.2 audit
revealed that this was too strong.

Retrospective prompt audit:

- `CARD_INJECTED` marker: 25/25.
- Exact `=== CAPTAIN PROBE REPORT` in the first Duck prompt: 18/25.
- Those 18 were exactly the games with zero Captain actions—the thin fault/initial-frame
  reports.
- The 7 games with substantial Captain activity did **not** deliver their richer reports.

Ring 6.1 therefore proved sequencing and containment, but not the meaningful V4-to-Duck
handoff.

### Ring 6.2: Captain execution repaired, handoff defect exposed

Ring 6.2 changed only the Captain-to-TAAF action bridge and improved fault diagnostics.
This worked:

- Captain faults: 0/25.
- Captain actions: 906; minimum 6, median 32, maximum 89.
- Report render lengths: 1,823–8,295 characters; median 3,704.
- Stop reasons: 24 `TIME_CAP`, 1 `TWO_LIVES_USED`.
- Captain game-over transitions: 3.
- Captain level advances: 1 (`vc33`, action 34,
  `MOUSE(row=34, col=62)`).
- Duck actions: 2,029.
- Total: 8 levels across 8 games; aggregate score 4.554020.
- No complete-game win.

But the primary experiment did not occur:

- `CARD_INJECTED` marker: 25/25.
- Exact Captain report in first Duck prompt: 0/25.
- Exact Captain report persisted elsewhere in downloaded text artifacts: 0/25.
- Duck queried `virelai_card()` on its first turn in 9 games; all 9 received an empty
  library.

Duck inherited only the post-probe frame and raw Captain action history. It did not receive
the fixed structured V4 report. The separate Duck ledger begins empty and learns from Duck's
later actions; it is not a fallback transport for the Captain's V4 context.

Ring 6.2 therefore proves **Captain execution**, not **Duck use of Captain knowledge**. Its
score cannot estimate the value of the report because the report was absent, Captain actions
altered the starting state, and LLM play is stochastic.

## 8. The exact current defect

The failure is a disagreement between two clocks:

- `analysis_step` counts Duck model turns.
- `action_num` / `self.action_count` counts real game actions, including Captain actions.

The solver correctly passes `_virelai_card` when `analysis_step == 1`, but it also passes
`self.action_count` into the analyzer. The prompt builder appends the card only inside
`if action_num == 0`.

That means:

```text
Captain takes actions
        ↓
self.action_count becomes nonzero
        ↓
solver passes the card on Duck turn 1
        ↓
prompt builder sees action_num != 0
        ↓
card argument is silently ignored
```

The marker is emitted earlier, merely because `_virelai_card` exists. It does not inspect
the completed prompt. That is why `CARD_INJECTED` claimed success in all 25 Ring 6.2 games
while the transcript proved zero deliveries.

Relevant code:

- `variants/ring6.2/ARC3-Inference/inference/framework/solver.py`: first-turn marker and
  `analyzer.analyze(... self.action_count ..., virelai_card=...)`.
- `variants/ring6.2/ARC3-Inference/inference/agent/tool_agent.py`: `_build_user_prompt()`
  appends the card only under `action_num == 0`.
- The same tool agent initializes its live `_virelai_state` independently and only updates
  it after a later Duck action payload, explaining the empty first-turn live card.

This defect existed in Ring 6.1 too. The zero-action Captain faults accidentally satisfied
the `action_num == 0` gate; substantial probes did not.

## 9. Ring 6.3: the next build

Ring 6.3 should be a **handshake-only repair**. Do not tune Captain strategy, budgets,
ontology, report wording, model configuration, or live-ledger semantics in the same ring.
We need one clean causal question:

> Does the already-rendered Captain report reach the first Duck model request exactly once,
> even when the Captain has already taken real actions?

### Required changes

1. Gate report insertion on the first Duck analysis turn, not on total game-action count.
2. Persist every exact rendered report as its own per-game text artifact.
3. Record a stable report digest and character count.
4. Emit the successful attachment marker only after the completed first user prompt is
   known to contain the exact report.
5. Keep separate markers for “report rendered” and “report attached” so generation and
   transport cannot be conflated again.
6. Add a regression test whose Captain action count is nonzero before Duck turn 1.
7. Keep the report one-shot: retries of Duck turn 1 may resend it idempotently, but later
   completed Duck turns must not receive it again.

Seeding Duck's live ledger from Captain V4 is a different architectural choice and should
not be bundled into 6.3. The fixed report is the intended Phase-1 transport. Once that works,
we can separately decide whether a shared live record is useful.

### Local acceptance before Kaggle

- A synthetic first Duck turn with `action_num > 0` contains the full report.
- A later Duck turn does not contain it.
- The saved report bytes, prompt substring, digest, and marker metadata agree.
- Captain actions remain zero-token actions.
- Captain failure still degrades to an honest fallback report without blocking Duck.
- Existing Ring 6.2 action-bridge tests remain green.
- Variant and assembled bundle are byte-checked for the touched files.
- No `__pycache__` or `.pyc` exists in either tree.

### Kaggle acceptance

Ring 6.3 passes the handshake only if all 25 games show:

```text
PROBE_START
→ PROBE_END
→ REPORT_RENDERED
→ first Duck request containing the exact saved report
→ REPORT_ATTACHED with matching digest
→ DUCK_FIRST_ACTION
```

Additional checks:

- 25 saved reports exist and are readable.
- 25/25 first Duck user prompts contain the matching report exactly once.
- No later completed Duck turn repeats the fixed report.
- Nonzero Captain action count does not affect delivery.
- The transcript allows us to grade whether Duck cites specific report evidence, follows a
  named gap, reproduces an observed winning transition, or ignores/contradicts the card.

Score remains secondary for this canary. The success condition is an inspectable causal
handoff.

## 10. What happens after the handshake is proven

Once Ring 6.3 lands, we can finally review the architecture rather than its plumbing:

1. **Duck response audit.** Read the exact report and Duck's first reasoning/action for each
   game. Grade report use as direct, partial, ignored, or contradicted.
2. **Field-card review.** Decide whether the V3.5 expandable format exposes the right facts,
   the right gaps, and enough mechanism detail without overwhelming the model.
3. **Captain execution tuning.** Ring 6.2's 24 time-cap stops and incomplete NAV collision
   sweep become the main mechanical targets. This is where broad sweep versus object depth,
   counter/ego masking, arrival, and lever-focused probing are tuned.
4. **Ontology experiments.** The ontology is a cheap prompt switch, but it should be tested
   in controlled arms only after the handoff is known to work. Useful comparisons include a
   no-Captain Duck arm with and without the ontology and a working-Captain arm with the
   ontology held fixed.
5. **Win analysis.** Add explicit retention and explanation of an observed winning
   transition, predict what should win the next level, state falsifiers, and eventually let
   the Captain return when Duck's transferred rule fails.

Do not use Ring 6.2 to choose among these semantic improvements. It never delivered the
Captain report, so it contains no evidence about how Duck responds to V4's compiled world
model.

## 11. How to audit a completed Kaggle run

### Build rhythm after Ring 6.3

Narrow integration fixes no longer go directly from local tests to a full
25-game run. After local contract tests pass, run a 2–3 game Kaggle smoke set
that exercises the changed mechanism. Use the full suite only after the smoke
run proves the repair in the real Kaggle runtime. This keeps transport and
protocol debugging cheap while reserving full runs for reliability, model-use,
and outcome measurement.

Use the downloaded artifacts by role:

- `transcripts/*.txt`: authoritative record of the system prompt, exact per-turn user
  prompts, model reasoning, tool calls, tool results, and action decisions.
- `artifacts/*_events.jsonl`: authoritative actor/action stream and machine-readable probe,
  transition, card, and first-action markers.
- `benchmark.json`: outcome, level count, score, action history, and token accounting.
- `summary.txt`: convenient aggregate summary; verify exact claims against
  `benchmark.json` when precision matters.
- notebook/kernel log: tracebacks, analyzer timeouts, packaging failures, and server events.
- `prompts/*.log`: only the latest model-call snapshot. It is not sufficient by itself to
  prove a one-shot first-turn delivery.

For every run, grade three layers separately:

1. **Captain quality:** what it actually explored and learned.
2. **Handoff fidelity:** whether the exact intended report reached the exact model request.
3. **Duck use:** whether the model understood and acted on report evidence.

Only after those three are separated should score be interpreted.

## 12. Current bottom line

The campaign has crossed one major boundary: the golden V4 Captain now runs inside the
Tufa/Duck Kaggle harness without crashing, including NAV actions, CLICK actions, RESET, life
boundaries, snapshots, and continued play after a level transition.

The remaining immediate problem is smaller but absolute: the compiled knowledge is not
reaching Duck. Ring 6.3 must make the information boundary real and auditable. Until an
exact saved Captain report appears inside Duck's first recorded request, claims about card
quality, Duck use, or the full Virelai hypothesis remain untested.

That is the current campaign state.
