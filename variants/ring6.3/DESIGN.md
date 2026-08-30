# RING 6 DESIGN — THE CAPTAIN PROBES FIRST, THE MODEL READS WHAT IT LEARNED
**v4 · 2026-08-28 · Chamber: Cowork (interim) · Supersedes v1, v2, v3 whole.**

**DIRECTOR'S RULING, 2026-08-28:**
> "The virelai captain probe needs to run first. This is how the model is given data before
> it is forced to hypothesize. The field card output is how we ensure it uses what the
> captain learned from algorithmic probing."

**The capability is the SEQUENCING, not the prose.** The model currently opens every game
with nothing and must hypothesise from a blank slate. This ring puts algorithmic probing
before its first token. The card is how the findings are delivered, not what is being built.

**A rejected alternative, recorded so it is not re-proposed.** This chamber proposed feeding
the card from the hybrid's own ledger instead — no vendoring, ships in days. **It does not
deliver the capability:** our ledger only fills as the model plays, so at turn 1 the card
would be prose about nothing. Cheaper, and beside the point.

---

## 0 · THE ONE VARIABLE

**Before the first model call, the golden v4 captain plays N lives. Its findings render as
v3.5's field card. The model reads that and plays from there. The captain never presses
again.**

---

## 1 · FEASIBILITY — MEASURED 2026-08-28, NOT ESTIMATED

**This chamber called the vendoring "the biggest single change in the program" and "weeks".
That was wrong, and the numbers say so.**

| question | measured answer |
|---|---|
| does the bundle already ship source trees? | **yes.** `kaggle/ring5/source-dataset/src/` carries 90+ files — `diagnostics.py` 128 KB, `uv.lock` 361 KB, `viewer/data.py` 73 KB |
| how much of the `Agent` base class does `Virelai` use? | **three attributes** — `game_id`, `action_counter`, `recorder`. `recorder` is already `hasattr`-guarded in `virelai.py` for "unit tests, custom harnesses" |
| third-party dependencies, whole package, AST-parsed | **numpy** (108 files) · **scipy** (**1** file) · **arcengine** (14) · **agents** (6) · 29 stdlib modules |
| what is scipy used for? | `scipy.ndimage.label`, gated in `scipy_check.py`. Its header records that soft fallbacks cost nine work orders — **ship scipy, never reimplement it** |
| pytest / `execution` / `main` imports | **162 / 1 / 4 files, all tests and trace tooling.** None ship |
| wall clock | **3m13s for 2 lives, 129 actions** on ls20 — ~1.5s/action, **2.4% of the 7920s budget** |

**A method note, because the first answer was wrong.** A `grep '^from\|^import'` returned a
list with no scipy in it. The import is indented inside a `try:`, so a column-zero anchor
never saw it — an instrument reporting confidently over a population it could not see. The
AST parse above replaced it. **Do not accept a grep where a parse is available.**

---

## 2 · THE BUILD — FIVE PARTS

**2.1 · Vendor `virelai_v4/` into `src/ARC3-Inference/`.** Everything EXCEPT `tests/`,
`docs/`, `live_runs/`, `diagnostics/_trace/`, `__pycache__`. ~250–280 production modules.

**2.2 · The base stub, ~10 lines**, replacing the entire `arc_agi` / `pydantic` / `Recorder`
/ tracing chain:

```python
class Agent:                       # satisfies virelai.py's three reads
    def __init__(self, game_id="", **kw):
        self.game_id = game_id
        self.action_counter = 0
```

`recorder` stays absent; `virelai.py` already guards it.

**2.3 · The frame adapter.** Build an `arcengine.FrameData` from the duck's
`game.current_state`, and route the `GameAction` the captain returns through the duck's own
`_execute_action(..., generated_tokens=0)` — the shape `_execute_auto_reset` already uses at
`solver.py:687`, which is committed Tufa precedent and costs **zero model tokens**. Because
the press goes through the duck's path, the duck's ledger and viewer stay in sync for free.

**2.4 · The card.** `virelai_field_card_v6.render_field_card` — already built and graded at
the Director's terminal 2026-08-28 — reads the captain's weave and emits v3.5's seven
sections. **Its data source is the WEAVE, never the semantic library:** v4's library reported
178 "classified, 0 unknown" objects for a world holding 27 worldlines (19 → 87 → 156 → 171 →
178 inside one run). `infer_roles` is the right altitude and the roster's own header says so
(WO-ROSTER-SEVER-01).

**2.5 · The handover.** Card into the first prompt. **LOCKSTEP DELETION, owed in this ring:**
the prompt prose telling the model to discover the world by experiment is what the card
replaces, and it dies here. **Check: `wc -w` on `prompts.py` must FALL.**

---

## 3 · THE TWO OPEN UNKNOWNS, AND HOW EACH CLOSES

**U1 · `FrameData` from the duck's state — CLOSED 2026-08-28, and it is nine lines.**

`arcengine.FrameData` and `arcengine.FrameDataRaw` are the same model but for one field:
`FrameData.frame` is `list[list[list[int]]]` (validated, serialised), `FrameDataRaw._frame`
is `List[ndarray]` (runtime-only). The other eight fields are identical — `game_id`, `state`,
`levels_completed`, `win_levels`, `action_input`, `guid`, `full_reset`, `available_actions`.

**The duck already holds a `FrameDataRaw`.** `solver.py:141` reads
`game.current_state.raw.state == arcengine.GameState.GAME_OVER`, so `.raw` is that model.

**And the conversion already exists golden-side** — `agents/agent.py:142`
`_convert_raw_frame_data`, transcribed per R-C rather than copied:

```python
frame = FrameData(
    game_id=raw.game_id, frame=[a.tolist() for a in raw.frame],
    state=raw.state, levels_completed=raw.levels_completed,
    win_levels=raw.win_levels, guid=raw.guid,
    full_reset=raw.full_reset, available_actions=raw.available_actions)
```

The action side mirrors both harnesses' existing calls — golden's
`action.action_data.model_dump()` and the duck's
`ActionInput(id=..., data={})` at `solver.py:686`:

```python
act = captain.choose_action(frames, frames[-1])                 # -> GameAction
self._execute_action(arcengine.ActionInput(id=act, data=act.action_data.model_dump()),
                     batch_index=1, batch_size=1, generated_tokens=0)
```

**HAZARD, named because it is invisible: `GameAction` is an Enum whose members carry a
mutable `action_data` instance created once at class definition.** `GameAction.ACTION6
.action_data` is therefore process-global state. A click coordinate the captain writes
persists on the enum member after the captain stops. The duck's own path is safe — it builds
`data` fresh in `_model_mouse_action_data` — but nothing enforces that, and a future reader
of `action_data` would inherit the captain's last click. **Assert it: the captain's final
`action_data` must not be readable as the model's first.**

**U2 · Is the vendored set complete?** **RED, mechanical and cheap:** build a tree containing
only the vendored files and `import virelai_v4.virelai`. **Any `ImportError` names a file
wrongly excluded.** Repeat until it imports. That is the verification — not inspection.

**U3 · scipy in the Kaggle image.** Read `setup_commands.json` in the existing bundle. If
absent, it is added there. **It is never soft-faked** — FRICTION-RM-01.

---

## 4 · PRE-REGISTERED FIXTURES

| # | fixture | measure |
|---|---|---|
| F1 | **the captain ran before the model** | probe presses recorded before `analysis_step 1`, every game — counted in `transcripts/`, **never `prompts/*.log`** (METHODOLOGY §5) |
| F2 | **the card reached the model** | `§1 — What Am I?` present in the turn-1 prompt on every game |
| F3 | the card is read whole | `§7 — What Have I Tried?` present at ≥ the ring-4 GAPS rate (64/82 = 78%) |
| F4 | the card is informative | on every game where the captain sealed anything, ≥1 named role appears in §2 |
| F5 | **negative control — nothing sealed** | all seven sections render with v3.5's fallback sentences; none blank. Verified offline 2026-08-28 (55 words) |
| F6 | **negative control — CLICK world** | §1 reads God Mode or an honest absence, never a body that does not exist |
| F7 | no firewall leak | zero colour names, zero `class N`, zero `###` ids in any card |
| F8 | behaviour changed (FRICTION-004) | model-issued actions differ on ≥1 game vs ring5 |
| F9 | the captain is cheap | probe wall clock < 5% of the per-game budget on every game |

**KILL CONDITIONS:**
- **F7 fails** — a firewall leak kills regardless of score.
- **F1 fails on >20% of games** — the sequencing did not happen and this ring did nothing,
  whatever the score says.
- **F2 fails while F1 passes** — the captain ran and the handover is broken. A worse finding
  than a low score, and not fixable by editing the card.
- **A role appears in prose that no evidence earned.** Ring 4's pre-registered risk firing
  again and harder: "a large region in the top portion of the arena is the floor you walk on"
  reads as fact in a way a table row never did.

---

## 5 · THE COST, AND THE HALF THAT IS UNCOMFORTABLE

Two lives spend **~130 actions on level 1** before the model moves. Score is
`min(100, (baseline/taken)² × 100)` — **quadratic**.

- Ring 4: **median level score 0.00**, 11 of 25 games scoring. Where the score is already
  zero, 130 actions cost **arithmetically nothing**.
- Where it scores, the cost is real. tu93 finished in 60 actions; 130 in front of it erases
  that game.
- **The penalty is computable per game in advance** from ring4's counts. Compute it, subtract
  it, and the residual is the card's actual effect. **Read per game, never mean-to-mean.**
- **N is a spend cap, not an evidential trigger.** Start at 2 because it is cheap and the
  card was graded at 2. Nothing derives it.

**Filed now rather than discovered later: this is cheap because we are bad, and it gets
expensive as we get good.** A later ring near baseline pays it in full.

---

## 6 · WHAT IS NOT IN THIS RING

**Ring 7 = THE SEARCHABLE MEMORY** — `snapshot()` drops the destination node keys, no frame
recall, no query verbs (`claude/searchable-memory-read-2026-08-28.md`).

**No win model exists anywhere in the golden run.** §5 can only say *"no state has ever been
observed as a win."* That sentence is honest and it is the largest hole in the deliverable.
It has no producer to port and is its own ring.

**Carry across the level boundary does not exist** hybrid-side and is not built here.

---

## 7 · FAILURE SHAPES FILED IN ADVANCE

- **The model distrusts a card it did not earn.** Ring 1 measured +69% actions when the model
  was handed a frontier. F8 is where it shows.
- **Prose makes a wrong seal more convincing than a table did.** Ring 4 rendered 76 ego seals
  including a one-cell speck. In prose that becomes a confident English sentence.
- **The captain is slow on an unseen world.** Measured on one game. F9 is the guard and 25
  unknown worlds are not one game.
- **Two lives of nothing.** The captain dies early and the card describes an empty world. F5
  is the guard; the fallbacks must fire rather than the sections going quiet.
- **Everything works and nothing changes.** FRICTION-004. F8 is the criterion and a null is a
  real result.
