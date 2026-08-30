# RING 6 — BOOTSTRAP FOR THE NEXT CHAMBER

**Paste this as the opening message of the new session.**
**Written 2026-08-28 by the outgoing interim chamber. Authority order unchanged:
behaviour at the Director's terminal > the committed tree > the canons > SEED_v1 > anything
in this document.** Where this and the repo disagree, the repo wins.

---

## 0 · WHAT YOU ARE DOING

You are building **Ring 6 of the Duck-Virelai hybrid** — the separate ARC Prize 2026
Milestone #2 entry (deadline 2026-09-30) that clones Tufa's MIT Duck harness and inserts
deterministic Virelai code around the LLM. **The instrument ruling governs: score is the goal,
the Kaggle hidden set is the oracle, nothing hybrid-side is precedent golden-side, O-8 and O-9
stay open, and the hybrid may adopt instrument conventions without ruling them.**

**RING 6'S ONE VARIABLE, in the Director's words:**

> "The virelai captain probe needs to run first. This is how the model is given data before it
> is forced to hypothesize. The field card output is how we ensure it uses what the captain
> learned from algorithmic probing."

**The capability is the SEQUENCING, not the prose.** Today the model opens every game with
nothing and must hypothesise from a blank slate. Ring 6 puts algorithmic probing before its
first token. The card is the delivery mechanism, not the deliverable.

**Read `variants/ring6/DESIGN.md` (v4) before touching anything.** It carries the fixtures,
the kill conditions and the cost analysis. This document carries what the design does not:
the measurements behind it, and the traps.

---

## 1 · WHAT IS ALREADY BUILT AND GRADED

| file | state |
|---|---|
| `variants/ring6/DESIGN.md` | **v4, current.** Supersedes v1–v3 whole |
| `variants/ring6/ARC3-Inference/inference/framework/virelai_field_card_v6.py` | **built, run at the Director's terminal 2026-08-28, approved.** A port of v3.5's `observer/field_card_renderer.py` — seven sections, its headers, its vocabulary, its word ceiling, its fallbacks |
| `variants/ring6/tools/golden_log_adapter.py` | **built and working.** Fills the card's dict from a golden run's log. **VERIFICATION PATH ONLY — never the production route** |
| `variants/ring6/ARC3-Inference/inference/virelai_v4/` | **the vendored golden solver** (may or may not be copied yet — check) |

**Project docs written this cycle, all relevant:**
`claude/golden-run-field-card-harvest-2026-08-28.md` ·
`claude/searchable-memory-read-2026-08-28.md` ·
`claude/v35-presentation-over-v4-library-2026-08-28.md`

---

## 2 · MEASURED FACTS — every one of these was measured, not estimated

**The golden captain, run on ls20 with `VIRELAI_MAX_LIVES=2`:**

| | |
|---|---|
| wall clock | **3m13s**, 129 actions — ~1.5s/action, **2.4% of the 7920s per-game budget** |
| v4's own field card | **~27,000 chars**; its OBJECTS table ran **178 rows** |
| that object count, across one run | **19 → 87 → 156 → 171 → 174 → 175 → 178**; `unknown` fell to 0 and stayed |
| what the world actually holds | **27 worldlines**, folded from **152 visual objects** (X/Y = 5.63) |
| the ported card | **~2,900 chars, ~520 words** |

**THE CONSEQUENCE, AND IT IS THE RING'S CENTRAL DESIGN FACT: the card's source is the WEAVE,
never the semantic library.** v4's library mints a new region every time anything changes and
then declares all of them classified with confidence up to 0.95, over rows reading `no deltas
yet` and `tried=[1:_,2:_,3:_,4:_]`. `weave.role_read.infer_roles` — LIST 3 — is the right
altitude, and `WO-ROSTER-SEVER-01` already ruled that golden-side. **The library counts
appearances; the weave counts things.**

**Dependencies of `virelai_v4`, AST-parsed over every file:**

```
numpy      108 files      scipy       1 file  (scipy.ndimage.label, gated in scipy_check.py)
arcengine   14 files      agents      6 files (1 on the production path)
pytest     162 files      — tests only, do not ship
29 stdlib modules
```

**`scipy_check.py`'s header records that soft try/except fallbacks around scipy cost nine work
orders to diagnose. SHIP SCIPY. NEVER REIMPLEMENT `ndimage.label`.**

**The `Agent` base-class coupling is three attributes.** `Virelai` reads exactly `game_id`,
`action_counter`, `recorder` off its base — and `recorder` is already `hasattr`-guarded in
`virelai.py` for "unit tests, custom harnesses". A ~10-line stub replaces the whole
`arc_agi` / `pydantic` / `Recorder` / tracing chain.

**The frame adapter is nine lines and already exists golden-side.** `FrameData` and
`FrameDataRaw` are the same pydantic model but for one field (`frame` as nested lists vs
`_frame` as ndarrays). The duck already holds a `FrameDataRaw` — `solver.py:141` reads
`game.current_state.raw.state == arcengine.GameState.GAME_OVER`. Transcribe
`agents/agent.py:142 _convert_raw_frame_data`.

**Interface facts, verified in the tree:**

| fact | where |
|---|---|
| the live solver is **ring2's** `solver.py` (51,907 b) — rings 3/4/5 never touched it | `variants/ring2/.../solver.py` |
| `_execute_action(..., generated_tokens=0)` outside the analyzer is committed Tufa precedent | `solver.py:687`, `_execute_auto_reset` |
| `_execute_action` already feeds the ledger — **probe presses need no new recording plumbing** | `solver.py:757` |
| `_engine_action_names` filters `RESET` — **the model can never reset** | `solver.py:110-119` |
| the insertion point is inside `play()`'s `try:`, before `while not self.should_stop()` | `solver.py:264-278` |
| the bundle already ships whole source trees | `kaggle/ring5/source-dataset/src/` — 90+ files, `diagnostics.py` 128 KB, `uv.lock` 361 KB |

**The metric, verified against 25 scored games (mean abs error 0.024):**
`level_score = min(100, (baseline_actions / actions_taken)² × 100)`, index-weighted
`i / (N(N+1)/2)` over all N levels. **The cap is 100, not 115.**

**Ring 4's numbers, which every Ring 6 read must be paired against:**
3,436 actions over 25 games · all-25 **0.8340** · **median level score 0.00** · 11 of 25
scoring · 82 card renders across 23 games · `=== GAPS` present in only **64 of 82** renders ·
`card[:` in 20 of 25 games · median render **3,478 chars** · **76 distinct ego seals across 12
games**, including a 1-cell speck and a 135-cell region.

---

## 3 · INSTITUTIONAL KNOWLEDGE — the traps, and what each already cost

**1 · COUNT EVENTS IN `transcripts/`, NEVER `prompts/*.log`.** `prompts/*.log` is a LATEST
MODEL CALL SNAPSHOT — 9 renders against 119 actions on one measured run. A whole finding was
published off it, attributed to a code line, and had to be retracted (commit `9b73652`).
METHODOLOGY §5 carries the scar.

**2 · DO NOT GREP WHERE YOU CAN PARSE.** A `grep '^from\|^import'` over `virelai_v4` returned
a dependency list **with no scipy in it**, because the import sits indented inside a `try:`
and a column-zero anchor cannot see it. An AST parse fixed it. An instrument that reports
confidently over a population it cannot see is the failure mode this project pays for most.

**3 · NEVER GREP A BARE VOCABULARY WORD FOR A COUNT.** The system prompt echoes the contract
vocabulary every turn. Three false readings were produced this way in one day — ring3's
"contract compliance" (constant counts across all 25 games gave it away), ring4's "3,482 card
calls" (the real render count was 82), and `falsif` × 3,757 which is prompt echo and must
never be cited. **Anchor every count on the line that carries the fact.**

**4 · QUIET IS NOT SUCCESS.** Every "it didn't complain" must first prove "it ran."

**5 · VERIFY BUNDLES BY CONTENT, NEVER EXISTENCE.** `preamble.txt` is static build-time text;
a ring4-p2 rename via regex left `benchmark.passes: 1` while the pickle said 2. Check the
pickle bytes (`n_passes\x94K\x02`) and `pickletools.dis`.

**6 · `__pycache__` HAS BEEN FOUND INSIDE SHIPPED BUNDLES** — ring3, and present in ring4,
ring5 and ring11 variant trees. Exclude it explicitly and check the bundle after assembly.

**7 · THE GIT LOCK.** A read-only `git status` from the bridge creates `.git/index.lock`,
which `device_bash` cannot unlink (deletes are blocked by default). Before every git write:
`mv .git/index.lock _to_delete/gitlocks/`. METHODOLOGY §7.

**8 · THE MOUNT KILLED THE SHELL.** The 13 GB `ARC_3_BETA` folder filled the local VM's
~9.8 GB volume and `device_bash` died with "Failed to create bridge sockets". **There is no UI
to disconnect a folder** — open issue anthropics/claude-code#40043, no workaround. The route
is a fresh session connecting only the folders you need. **Copy anything you need out of
ARC_3_BETA before dropping it.**

**9 · FRICTION-004.** *"Does this change what the solver does on at least one game? If not,
don't ship it."* And: name the consumer before building the producer.

**10 · THE CHAMBER NEVER CLAIMS IT WORKS.** You may read and write code; you may not claim it
runs. Say what would be measured and how it could fail. Behaviour is measured at the
Director's terminal.

---

## 4 · CORRECTIONS ALREADY PAID FOR — do not re-derive these

**Four claims the outgoing chamber made and had to withdraw. Each cost a cycle.**

1. **"Point v3.5's renderer at v4's `SemanticLibrary` — they import the same class."** True
   about the import, **false about where the data is**. The library is the 178-object layer.
   The run falsified it. Source is the weave.
2. **"Vendoring is the biggest single change in the program; weeks."** Wrong. The bundle
   already ships trees; the base coupling is three attributes; scipy is one file.
3. **"Feed the card from the hybrid's own ledger instead — no vendoring, ships in days."**
   Wrong, and beside the point: **our ledger only fills as the model plays, so at turn 1 the
   card would be prose about nothing.** It does not deliver the capability.
4. **"Here is a port of v3.5's field card."** It was not a port — it was five invented
   sections with a citation attached. **A port means porting.** Read the whole source file
   before claiming to have carried it across. R-C.

---

## 5 · BUILD INSTRUCTIONS

**Order matters. Each step has a verification that is a measurement, not an inspection.**

### STEP 0 — vendor the solver

**Connect `duck-virelai` and `virelai-resource` only. Do NOT connect `ARC_3_BETA`** — it is
13 GB, it fills the local VM, and it is what killed `device_bash` with "Failed to create
bridge sockets". `~/Desktop/virelai-resource` is the 38 MB readable extract built
2026-08-28; its own README records what was excluded, and the headline exclusion is **every
recording, so nothing in it can be replayed.** There is no UI to disconnect a folder
(anthropics/claude-code#40043) — the route is a fresh session with the right folders.

```bash
rsync -a --exclude 'tests/' --exclude 'docs/' --exclude 'live_runs/' \
         --exclude '_trace/' --exclude '__pycache__/' --exclude '*.pyc' \
  ~/Desktop/virelai-resource/v4/virelai_v4/ \
  ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/
du -sh  ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/
find    ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/ -name '*.py' | wc -l
```

**VERIFY: expect ~250–280 `.py` files and well under 100 MB. If either is wildly off the
exclusion list is wrong — stop and find out why rather than proceeding.**

The `agents` base class is NOT copied — Step 1 replaces it with a ten-line stub. The original
is at `~/Desktop/virelai-resource/v4/agents/agent.py` if you need to read it.

### STEP 1 — the base stub

`variants/ring6/ARC3-Inference/inference/virelai_v4/_agent_stub.py`, and repoint
`virelai.py`'s `from agents.agent import Agent`:

```python
class Agent:                       # satisfies virelai.py's three reads; nothing more
    def __init__(self, game_id: str = "", **kw):
        self.game_id = game_id
        self.action_counter = 0
```

`recorder` stays absent — `virelai.py` already guards it.

### STEP 2 — U2, the completeness RED

**Mechanical, not inspection.** In a tree containing only the vendored files:

```bash
cd ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference && \
  python3 -c "import virelai_v4.virelai"
```

**Every `ImportError` names a file wrongly excluded. Fix, repeat, until it imports clean.
That is the verification.** Record what had to be added back — if `tests/` or `_trace/`
turns out to be load-bearing, that is a finding about the package, not a licence to ship it.

### STEP 3 — U3, scipy in the Kaggle image

Read `kaggle/ring5/source-dataset/setup_commands.json`. If scipy is not installed there, add
it. **Never soft-fake `ndimage.label`.**

### STEP 4 — the driver

One method on the duck solver, one call site in `play()` after `write_viewer_payload()` and
before `while not self.should_stop()`:

```python
def _virelai_opening(self) -> None:
    captain = Virelai(game_id=...)
    frames = [self._frame_data()]                      # from game.current_state.raw
    while not captain.is_done(frames, frames[-1]):
        act = captain.choose_action(frames, frames[-1])
        self._execute_action(arcengine.ActionInput(id=act,
                                                   data=act.action_data.model_dump()),
                             batch_index=1, batch_size=1, generated_tokens=0)
        captain.action_counter += 1
        frames.append(self._frame_data())
    self._virelai_card = render_field_card(_from_captain(captain), game_id=...)
```

Set `VIRELAI_MAX_LIVES=2` and `VIRELAI_QUIET=1` in the environment before constructing it.

**HAZARD, named because it is invisible: `arcengine.GameAction` is an Enum whose members carry
a MUTABLE `action_data` instance created once at class definition.** `GameAction.ACTION6
.action_data` is process-global. A click coordinate the captain writes survives after the
captain stops. The duck's own path is safe — it rebuilds `data` in `_model_mouse_action_data`
— but nothing enforces that. **Assert the captain's last `action_data` is not readable as the
model's first.**

### STEP 5 — the handover, with lockstep deletion

Inject the card into the first prompt. **In the same ring, delete the prompt prose telling the
model to discover the world by experiment — that is what the card replaces.**
**Check: `wc -w` on `prompts.py` must FALL.** A ring that adds a section and grows the prompt
has replaced nothing.

### STEP 6 — bundle, and check it by content

Assemble as rings 3–5 were. Then: no `__pycache__` anywhere in the bundle; the pickle's
`n_passes` read as bytes; `pickletools.dis` clean; `preamble.txt` inspected rather than
regex-renamed.

### STEP 7 — one run, then read it

**Pre-registered fixtures and kill conditions are in `DESIGN.md` §4. Do not invent new ones
after the run.** F1 (the captain ran before the model) and F2 (the card reached the model) are
counted in `transcripts/`, never `prompts/*.log`.

**Read the score per game, never mean-to-mean.** The probe's action cost is computable in
advance from ring4's per-game counts — compute it, subtract it, and the residual is the card's
actual effect. On the fourteen games at 0.00 it costs arithmetically nothing; on tu93, which
finished in 60 actions, ~130 in front of it erases the game.

---

## 6 · WHAT IS NOT THIS RING

**Ring 7 = THE SEARCHABLE MEMORY.** `snapshot()` emits `"outcomes": len(rec.dests)` and drops
the destination node keys, so the model can count outcomes and never follow one; every grid
ever seen is stored in `self.grids` and none of it reaches the model; there are no query
verbs. Plus a defect found by reading and **NOT_MEASURED live**: `_rebuild_map`'s cache
signature includes `len(self.edges)`, so it rebuilds every press and re-appends one note per
reset — the digest re-announces the whole reset history every turn.
See `claude/searchable-memory-read-2026-08-28.md`.

**No win model exists anywhere in the golden run.** The card can only say *"no state has ever
been observed as a win."* That is honest and it is the largest hole in the deliverable. It has
no producer to port and is its own ring.

**Carry across the level boundary does not exist hybrid-side.**

**Ring 5's read is still owed** — pre-registered as 76 distinct ego seals → <3/game, ZERO on
CLICK, ZERO ≥40-cell, ZERO 1-cell; kill condition 76→0 with refusals everywhere, which is
blindness rather than a fix.

---

*Written at the close of the interim chamber, 2026-08-28. Nothing in this document is
measured; everything in §2 was. The repo outranks it.*
