# RING-ONTOLOGY DESIGN — THE NOTECARD, ISOLATED
**v1 · 2026-08-30 · Chief Engineer seat · per the Director's charter, this conversation.**

**Not a rung in the `variants/ring1…ring6.3` capability ladder.** Every ring in that
ladder bundles prompt growth and captain-code growth in the same build (ledger → prompt
text → weave → card → probe-first sequencing). This is the opposite move on purpose:
capability held at zero, one static prompt block added, nothing else touched. It is a
control-arm sibling to `kaggle/dryrun-r0` / `kaggle/r0-p2`, not their successor.

---

## 0 · The one variable

**Fork r0 (byte-identical to `baseline/duck-harness`, confirmed by diff). Add one system-
prompt block — the axioms, genre conventions, and search-economy notecard below. Change
nothing else: no `virelai_ledger.py`, no `virelai_weave.py`, no `virelai_card.py`, no
probing, nothing that touches the belief state or plays a life before the model's first
token.**

Read against what already exists in this repo, this answers a question the ladder was
never built to answer: does the ontology content alone move the score, with zero
algorithmic evidence behind it. r0 (already run, 1-pass and 2-pass) is the control.

## 1 · Why the ladder can't answer this, and why this campaign is cheap

- **"Ring 0" is not a rung.** `kaggle/dryrun-r0/source-dataset/.../prompts.py` diffs
  byte-identical to `baseline/duck-harness/.../prompts.py`. It's the zero-point control,
  packaged for Kaggle, already run twice.
- **Every landed ring conflates two variables.** ring1 (`virelai_ledger.py` only) →
  ring11/ring2 (`+VIRELAI_WORLD_ADDENDUM` text) → ring25/ring3 (`+virelai_weave.py`) →
  ring4/ring5 (`+virelai_card.py`) → ring6/6.2/6.3 (`+probe-first sequencing`). Prompt and
  capability grow together at every step. No existing arm isolates prompt content alone.
- **ring6.2's run data can't fill that gap either.** `runs/kaggle-ring6.2-run1/
  EVALUATION.md` (this run finished 2026-08-30, hours before this design was drafted)
  found the Captain-to-Duck handshake fully broken: `action_num` is conflated with
  `self.action_count`, which the Captain's own probing actions increment, so the
  `if action_num == 0` gate that's supposed to mean "Duck's first turn" never fires once
  the Captain has probed. 0/25 games had the rendered Captain report reach Duck's first
  prompt; the live ledger queried empty in all 9 games that checked it. EVALUATION.md's
  own verdict: "an ontology + Captain state-perturbation run, not a valid test of the
  intended Virelai information handoff." Its scores reflect a system prompt making a false
  promise ("THE CAPTAIN REPORT appears in the first user turn") plus a Captain that burned
  turns and changed starting states before Duck ever got control. Unusable as a comparison
  point for this question — dropped from this campaign for that reason, not by omission.
- **Feasibility, checked not assumed.** The notecard block below is inert text — no
  function call, no `virelai_*` import, no reference to a live tool that doesn't exist in
  this arm. r0's tree carries no `virelai_*` files to strip. This is a single-file,
  single-string diff against `prompts.py`.

## 2 · Where this lives

- **`variants/ring-ontology/`** — this file and the forked source tree:
  `baseline/duck-harness/` copied whole, with exactly one change —
  the notecard block inserted into `ARC3-Inference/inference/agent/prompts.py` per §4.
- **`kaggle/ring-ontology/`** — the push-ready bundle (source-dataset + kernel), built
  from the `variants/ring-ontology/` tree, mirroring the confirmed `variants/ring2` ↔
  `kaggle/ring2` pattern. The packaged source trees diff identical to the variant.
- The Director pushes and runs it personally, same pattern as every prior arm
  (`kaggle/PUSH.md`, `PUSH-V2.md`, `PUSH-P2.md` — Cowork builds the bundle, the Director
  runs `kaggle datasets create`/`kaggle kernels push` from their own terminal and clicks
  Save & Run All).

## 3 · The notecard

Eight ontology axioms, a ninth on the honest null, a tenth stating the closed taxonomy
is exhaustive without guaranteeing any member's existence (both added this pass — see
§5), four genre-convention lines, one search-economy line, one render-vs-machine line,
and a compressed six-item checklist. Stable per-item tags (`A1…`, `G1…`, `S1`, `M1`,
`C1…`) — a prompt-local scheme, not this project's `O-8`/`R-A` ruling registry.

```
# Ring Ontology — the notecard. Inserted once, as its own constant, positioned LAST
# before COMPACT_TOOL_SESSION_ADDENDUM (closest to generation each turn -- the same
# reason the Captain field card, when its handshake works, goes in the first user turn
# rather than the system prompt). No captain, no card, no [MAP], no [COUNTER] in this
# arm -- nothing here refers to them. GAME_OVERVIEW_ADDENDUM, STRUCTURED_RUNTIME_STATE_
# ADDENDUM, VISUAL_GAME_ADDENDUM, and PYTHON_ADDENDUM stay byte-identical to r0.

ARC_GRID_MULTIVERSE_NOTECARD_ADDENDUM = (
    "\n\nA notecard on this kind of game, worth reading once and using all run:\n"

    "\nWhat you're looking at (grounding):\n"
    "A1 - You encounter the world as successive finite grids plus the legal actions "
    "currently declared. A grid is an observation of state, not necessarily the whole "
    "state; identical visible grids do not prove identical hidden state.\n"
    "A2 - Knowledge is grounded in observed transitions, not appearance. An action "
    "connects a before-grid to an after-grid. Resemblance, position, color, or shape "
    "alone never establishes an object's function -- only watching it change does.\n"
    "A3 - Cells are the substrate. Objects, persistence, motion, counters, levers, "
    "obstacles, and goals are compact explanations of cell relationships over time. "
    "Hold each as a falsifiable model, not a literal fact the pixels handed you.\n"
    "A4 - Controlled, action-dependent change can reveal an embodied self. Repeated "
    "change independent of which action or target you chose is evidence for a counter "
    "or other autonomous process. Both stay hypotheses until the record distinguishes "
    "them.\n"
    "A5 - Causal roles are relational. A lever is established by an attributed "
    "intervention plus its repeatable effect elsewhere -- only after self-motion and "
    "counter-like change are excluded from that attribution.\n"
    "A6 - Hidden state is evidenced when the same visible situation and action produce "
    "different transitions under different histories. Preserve the divergence; don't "
    "force it into one rule.\n"
    "A7 - A win is never inferred from appearance. It's known when the environment "
    "reports a level or game transition, not before. Every still-playing state you've "
    "already visited is evidence of a non-win; unexplored transitions remain the only "
    "possible locations of the win.\n"
    "A8 - A proposed rule must predict an observable transition and name what future "
    "observation would falsify it. A rule that won one level is evidence for the next "
    "level, not a guarantee of it.\n"
    "A9 - None of A1-A8 promise that a self, a counter, or a lever exists in this "
    "particular game. Most objects, once you've tried every action against them, turn "
    "out to affect nothing and be affected by nothing -- that's a complete, expected "
    "answer, not a gap. Stop hunting for a role once you've tested everything and found "
    "none; a quiet, fully-tested object needs no further explanation.\n"
    "A10 - Every object's causal role resolves to exactly one of a closed set: an "
    "embodied self, a counter or other autonomous process, a lever, an unattributed "
    "environmental force, a dependent member driven by another's effect, or inert "
    "(affects nothing, is affected by nothing). This list is exhaustive -- there is no "
    "seventh kind of role. That some object resolves to one of these six is guaranteed; "
    "which one it resolves to, or whether any given kind appears at all in this game, is "
    "never guaranteed in advance (A9).\n"

    "\nWhat kind of game this is (genre, stated by the platform, true across all of "
    "them):\n"
    "G1 - The first level of any game teaches its core interaction with no "
    "instructions. Evidence gathered there is unusually clean -- weight it accordingly.\n"
    "G2 - These games combine multiple mechanics; none is built to be one mechanic that "
    "just scales. Finding one causal rule is a reason to keep probing, not a stopping "
    "condition.\n"
    "G3 - Each game has a real multi-level campaign. Don't generalize a whole game's "
    "difficulty, or assume you've seen its full mechanic set, from the first level "
    "alone.\n"
    "G4 - These games are calibrated to be fully solvable cold, from structured looking "
    "alone, with no outside information. If progress stalls, an unexplored interaction "
    "is the more likely cause, not a missing fact.\n"

    "\nWhy probing turns aren't wasted:\n"
    "S1 - A win being reachable from the start by some action sequence is guaranteed; "
    "the sequence itself is not. Undirected search over the full action space does not "
    "scale. Settling self, counters, and levers where the evidence actually supports "
    "them (A4-A5, A9-A10) is what narrows the space enough to search it -- turns spent "
    "on that are what make the later search short, not a cost against solving "
    "efficiently.\n"

    "\nWhat the grid actually is:\n"
    "M1 - The grid renders a smaller set of true variables and update rules; it is not "
    "the puzzle itself. Treat a rule as understood only once it correctly predicts a "
    "situation you have not yet tried -- not merely once it has explained something you "
    "already saw.\n"

    "\nBefore you act, check against these:\n"
    "C1 - Don't import meaning from other games or the real world (A2). What a shape "
    "resembles is not what it does.\n"
    "C2 - Don't write off something quiet as background, and don't assume something "
    "quiet is secretly important either (A3, A9). Untested quiet is still unknown; only "
    "quiet you've tried everything against is honestly settled.\n"
    "C3 - Don't stop at the first explanation that fits (A8, G2). A rule that explains "
    "what you've seen is a candidate, not a verdict, until it survives a new test.\n"
    "C4 - Don't chase score over understanding (S1). A rule you can state and predict "
    "from is worth more than a lucky action sequence you can't explain.\n"
    "C5 - Don't assume the first mechanism found is the whole picture (G2-G3). Keep "
    "probing after a win or a level clear.\n"
    "C6 - Don't brute-force before you comprehend (S1). Undirected search doesn't scale; "
    "narrowing the space first is what makes search short.\n"
)
```

`_build_system_prompt` for this arm:

```
"You are a coding agent solving a grid-based puzzle game."
+ GAME_OVERVIEW_ADDENDUM             (byte-identical to r0)
+ STRUCTURED_RUNTIME_STATE_ADDENDUM  (byte-identical to r0)
+ MULTIMODAL_CONTEXT_ADDENDUM        (byte-identical to r0, if image mode on)
+ VISUAL_GAME_ADDENDUM               (byte-identical to r0)
+ PYTHON_ADDENDUM                    (byte-identical to r0)
+ ARC_GRID_MULTIVERSE_NOTECARD_ADDENDUM   <- the one insertion
+ COMPACT_TOOL_SESSION_ADDENDUM      (byte-identical to r0)
```

## 4 · Verification plan

**Pre-flight (Cowork, before any push):**
- Diff the forked tree's `prompts.py` against r0's — exactly one string added, nothing
  else changed.
- `find` the forked tree for any `virelai_*` file or `virelai_card` reference outside the
  notecard string itself — must return nothing.
- Confirm dataset/kernel config (n_passes, per-game cap, concurrency, accelerator)
  matches r0-p2's, so the run is comparable without a pass-count caveat.

**Live (Director's terminal):** push per §2's pattern, ≥2 runs (this repo's own method
law), meter reading before/after, `benchmark.json` downloaded each run.

**Kill condition:** pre-flight diff or firewall check finds more than the one intended
string change — stop, re-fork from r0 rather than reason about a confounded run.

## 5 · Honest ledger

- **A10 added on explicit Director direction, reading confirmed before writing it.** The
  Director asked for "the axiomatic archetypes that must exist" as philosophical
  grounding. Two readings existed and pointed opposite directions: completeness (every
  object resolves to one of a closed six-member set, including INERT as a full member —
  canon-true, compatible with A9) versus an existence guarantee (an ego, a counter, and
  levers are each present in every game — contradicts canon's INERT framing and the
  evidence-before-belief law, and would have reversed A9). Confirmed completeness before
  drafting. A10 also names ENVIRONMENTAL FORCE and REACTIVE-DRIVEN for the first time in
  this notecard — the prior draft named only three of the six archetypes by omission,
  not by design; A10 closes that gap too.
- **Self-caught before commit, not after a run:** the first draft of this notecard (A1-A8)
  used conditional phrasing throughout ("can reveal," "is evidence for," "is established
  by... after... excluded") and never literally claimed a self, counter, or lever must
  exist in every game. But it named only three of the canon's six archetypes and never
  stated the honest-null case — read against `CANON_2_FLIPBOOK_ONTOLOGY_v1.md` §6.2-6.3
  ("INERT is the most drainable bucket in the taxonomy, by design"; "coverage-bounded
  silence... inert is never assertable from quiet alone; it is assertable from
  tried-everything quiet"), a compressed notecard naming only ego/counter/lever risked
  reading as an implicit hunting license even without an explicit existence claim. A9 and
  the revised C2 close this before the first build, not after a run shows the bias.
- **Content vs. format still confounded within this one arm**, by the Director's own
  framing this pass ("formatted the way we know will optimize his use of it") — this
  campaign tests content-and-format together, not separately. Recorded as a possible
  follow-on (a format-only fourth arm) only if this arm shows a real effect worth
  isolating further.
- **Built and pre-flight verified, 2026-08-30:** the forked
  `variants/ring-ontology/` source tree differs from r0 only in `prompts.py`; the
  notecard is composed immediately before the compact tool-session rules without a
  `tool_agent.py` change. The packaged source trees are byte-identical to the variant,
  the JSON/notebook artifacts parse, and the Captain/Virelai firewall is empty. The
  r0-p2 benchmark pickle retains its template label internally, so the kernel explicitly
  resets `bm.label` to `duck-virelai-ring-ontology` immediately after loading it; this is
  provenance-only and leaves the benchmark configuration unchanged.

---

*Type: ring DESIGN, `ring-ontology` · v1 · 2026-08-30 · Chief Engineer seat. Source and
push bundle built and pre-flight verified; not yet pushed.*
