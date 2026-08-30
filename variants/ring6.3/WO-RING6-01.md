# WO-RING6-01 — THE CAPTAIN PROBES FIRST

**Type:** `WORK_ORDER` · **Version:** v1 · **Date:** 2026-08-28
**Issuing seat:** Cowork, interim chamber · **Executing seat:** the next build chamber
**Governing:** `variants/ring6/DESIGN.md` v4 · `variants/ring6/BOOTSTRAP.md` ·
`METHODOLOGY.md` · `STATE_OF_THE_HYBRID_BUILD_v3.md`
**Authority order:** behaviour at the Director's terminal > the committed tree > the canons >
SEED_v1 > this document.
**Instrument ruling governs.** Score is the goal, the Kaggle hidden set is the oracle, nothing
here is precedent golden-side, O-8 and O-9 stay open.

**HALTS ARE INFORMATION.** If a premise in §1 is false, stop and report it. Do not work around
it. Four of the last eight golden rungs halted before delivery and each halt was worth more
than the build would have been.

---

## §0 · CHARTER — THE ONE VARIABLE

**Before the model's first call, the golden v4 captain plays N=2 lives on level 1. Its findings
render as v3.5's field card. The model reads that card and plays from there. The captain never
presses again.**

The capability is the **sequencing**. Today the model opens every game hypothesising from a
blank slate, because the hybrid's ledger only fills as the model acts. The card is the delivery
mechanism, not the deliverable.

**Nothing else changes in this ring.** Passes stay at 1 (Ring E is a separate axis — see
`kaggle/ring5-p2`). No new seal. No change to the weave or the ledger.

---

## §1 · PREMISES — VERIFY EACH BEFORE WRITING CODE. A FALSE PREMISE IS A HALT.

**P1 · The vendored source exists and is complete enough to import.**
```bash
ls ~/Desktop/virelai-resource/v4/virelai_v4/virelai.py
find ~/Desktop/virelai-resource/v4/virelai_v4 -name '*.py' | wc -l
```
Expect the file present and ~400+ `.py`. **HALT if absent** — `virelai-resource` is the 38 MB
extract built 2026-08-28; if it is missing, rebuild with `/tmp/mk-resource.sh` or fall back to
`~/Desktop/ARC_3_BETA/arc-prize-2026-arc-agi-3/ARC-AGI-3-Agents/virelai_v4/`.

**P2 · `Virelai` reads only three attributes off its base class.** Verified 2026-08-28;
re-verify, because a stub built against a stale reading is silent breakage:
```bash
cd ~/Desktop/virelai-resource/v4 && python3 - <<'PY'
import re
src = open('virelai_v4/virelai.py').read()
used     = set(re.findall(r'self\.([a-zA-Z_]\w*)', src))
assigned = set(re.findall(r'self\.([a-zA-Z_]\w*)\s*=', src))
methods  = set(re.findall(r'^    def ([a-zA-Z_]\w*)', src, re.M))
print(sorted(used - assigned - methods))
PY
```
Expect exactly `['action_counter', 'game_id', 'recorder']`. **Any fourth name is a HALT** —
report it, do not extend the stub on your own judgement.

**P3 · The dependency set is what the design says.** Parse, never grep — a column-zero grep
misses scipy because its import is indented inside a `try:`:
```bash
cd ~/Desktop/virelai-resource/v4 && python3 - <<'PY'
import ast, pathlib, sys
mods = {}
for p in pathlib.Path('virelai_v4').rglob('*.py'):
    try: tree = ast.parse(p.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError: continue
    for n in ast.walk(tree):
        names = ([a.name.split('.')[0] for a in n.names] if isinstance(n, ast.Import)
                 else [n.module.split('.')[0]] if isinstance(n, ast.ImportFrom)
                      and n.level == 0 and n.module else [])
        for m in names: mods.setdefault(m, set()).add(str(p))
std = set(sys.stdlib_module_names)
for m in sorted(k for k in mods if k not in std):
    print("%-12s %3d files" % (m, len(mods[m])))
PY
```
Expect `numpy · scipy · arcengine · agents` (+ `pytest` if tests were copied). **Anything else
is a HALT.**

**P4 · scipy is available in the Kaggle image.**
```bash
grep -o 'scipy[^"]*' ~/Desktop/duck-virelai/kaggle/ring5/source-dataset/setup_commands.json | head
```
If absent, it must be added to `setup_commands.json`. **Never soft-fake `ndimage.label`** —
`scipy_check.py`'s own header records that try/except fallbacks cost nine work orders.

**P5 · The live solver is ring2's.** Rings 3, 4 and 5 never touched `solver.py`:
```bash
ls -l ~/Desktop/duck-virelai/variants/*/ARC3-Inference/inference/framework/solver.py
```
Expect ring2's at 51,907 bytes and no solver in ring3/4/5. **If a later ring has one, that is
the base and this premise is false — report it.**

**P6 · The action and frame seams are where the design says.**
```bash
S=~/Desktop/duck-virelai/variants/ring2/ARC3-Inference/inference/framework/solver.py
grep -n '_execute_auto_reset\|def _execute_action\|current_state.raw\|def play' $S | head
```
Expect `_execute_auto_reset` calling `_execute_action(..., generated_tokens=0)`, and
`game.current_state.raw` in use. **`generated_tokens=0` is the whole reason probe presses cost
no model tokens. If it is gone, HALT.**

**P7 · No committed test asserts on `play()`'s opening.**
```bash
grep -rn 'def play\|_virelai_opening' ~/Desktop/duck-virelai/variants/ring6/tests/ 2>/dev/null
```
Expect nothing. A guard that passes for the wrong reason is worse than no guard.

**P8 · How was ring5's bundle generated? — THIS ONE IS GENUINELY UNKNOWN AND MUST BE ANSWERED
BEFORE §3 PHASE D.**
```bash
grep -n 'kaggle' ~/Desktop/duck-virelai/variants/ring1/ARC3-Inference/Makefile | head -20
cat ~/Desktop/duck-virelai/kaggle/ring5/source-dataset/taaf-kaggle-bundle.json
```
**If a generator command exists, use it — it writes `deploy_target.pkl` and `preamble.txt`
correctly.** If the bundles were hand-assembled, follow the ring4 → ring4-p2 pattern documented
in `kaggle/ring5-p2/PUSH-RING5-P2.md`, and know that `deploy_target.pkl` will carry a stale
path. **Report which it was.**

---

## §2 · THE FENCE

**MAY TOUCH:**
```
variants/ring6/ARC3-Inference/inference/virelai_v4/            (vendored, new)
variants/ring6/ARC3-Inference/inference/virelai_v4/_agent_stub.py   (new)
variants/ring6/ARC3-Inference/inference/framework/solver.py    (new in ring6, from ring2)
variants/ring6/ARC3-Inference/inference/framework/virelai_field_card_v6.py  (exists)
variants/ring6/ARC3-Inference/inference/agent/prompts.py       (new in ring6, from ring4)
variants/ring6/tests/                                          (new)
variants/ring6/MANIFEST.md                                     (owed)
kaggle/ring6/                                                  (new)
```

**MAY NOT TOUCH:** any other ring's variant tree · `virelai_weave.py` · `virelai_ledger.py` ·
`virelai_card.py` (ring 4's table card stays; it is the control) · any `kaggle/ring*` bundle
other than ring6 · anything under `virelai-resource/` or `ARC_3_BETA/`.

**The vendored `virelai_v4/` is READ-ONLY except for the one import line in `virelai.py` that
Phase A repoints.** If any other change to it turns out to be required, that is a HALT and a
finding about the package, not a licence to edit it.

---

## §3 · THE BUILD

### PHASE A — vendor, stub, and the import RED

**A.1** Copy the package:
```bash
rsync -a --exclude 'tests/' --exclude 'docs/' --exclude 'live_runs/' \
         --exclude '_trace/' --exclude '__pycache__/' --exclude '*.pyc' \
  ~/Desktop/virelai-resource/v4/virelai_v4/ \
  ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/
du -sh ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/
find   ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4/ -name '*.py' | wc -l
```
**Expect ~250–280 `.py`, well under 100 MB.** Wildly off means the exclusion list is wrong —
stop and find out why.

**A.2** Write `virelai_v4/_agent_stub.py`:
```python
"""Ring 6. Replaces agents.agent.Agent for the hybrid.

virelai.py reads exactly three attributes off its base class -- game_id,
action_counter and recorder -- and guards recorder with hasattr for "unit
tests, custom harnesses". This provides the first two and deliberately not
the third. It replaces the whole arc_agi / pydantic / Recorder / tracing
chain, none of which the hybrid has or needs.

If a fourth attribute is ever required, that is a HALT: it means virelai.py
changed and the stub was built against a stale reading.
"""


class Agent:
    def __init__(self, game_id: str = "", **kwargs):
        self.game_id = game_id
        self.action_counter = 0
```
Then repoint the one import in the vendored `virelai.py`:
```bash
cd ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/virelai_v4
sed -i '' 's|^from agents.agent import Agent$|from virelai_v4._agent_stub import Agent|' virelai.py
grep -n 'import Agent' virelai.py
```
**Exactly one line must change. Verify by reading it.**

**A.3 · THE IMPORT RED — the completeness verification, and it is mechanical:**
```bash
cd ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference && \
  python3 -c "import virelai_v4.virelai; print('IMPORT CLEAN')"
```
**Every `ImportError` names a file wrongly excluded. Add it back, repeat, until it prints
IMPORT CLEAN. Record every file that had to be restored.** If `tests/` or `_trace/` turns out
to be load-bearing on the production path, **that is a finding to escalate, not a licence to
ship the tests.**

### PHASE B — the driver

**B.1** Copy ring2's solver into ring6 (it is the live one):
```bash
mkdir -p ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/framework
cp ~/Desktop/duck-virelai/variants/ring2/ARC3-Inference/inference/framework/solver.py \
   ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/framework/solver.py
```

**B.2** Add one method and one call site. The call site goes inside `play()`'s `try:`, **after
`self.write_viewer_payload()` and before `while not self.should_stop()`**:

```python
    def _frame_data(self):
        """arcengine FrameDataRaw -> FrameData. Transcribed from the golden
        harness's own agents/agent.py:142 _convert_raw_frame_data (R-C: origin
        cited, not copied). The two models differ in one field only."""
        raw = self.game.current_state.raw
        return arcengine.FrameData(
            game_id=raw.game_id, frame=[a.tolist() for a in raw.frame],
            state=raw.state, levels_completed=raw.levels_completed,
            win_levels=raw.win_levels, guid=raw.guid,
            full_reset=raw.full_reset, available_actions=raw.available_actions)

    def _virelai_opening(self) -> None:
        """Ring 6. The captain probes before the model's first token, then stops
        for good. Presses go through _execute_action with generated_tokens=0 --
        the shape _execute_auto_reset already uses -- so they cost no model
        tokens and land in the duck's own ledger with no new plumbing."""
        if os.environ.get("VIRELAI_RING6", "1") == "0":
            return
        os.environ.setdefault("VIRELAI_MAX_LIVES", "2")
        os.environ.setdefault("VIRELAI_QUIET", "1")
        from virelai_v4.virelai import Virelai
        from inference.framework.virelai_field_card_v6 import render_field_card
        captain = Virelai(game_id=str(self.game.game_id))
        frames = [self._frame_data()]
        try:
            while not captain.is_done(frames, frames[-1]):
                if self.should_stop():
                    break
                act = captain.choose_action(frames, frames[-1])
                self._execute_action(
                    arcengine.ActionInput(id=act, data=act.action_data.model_dump()),
                    batch_index=1, batch_size=1, generated_tokens=0)
                captain.action_counter += 1
                frames.append(self._frame_data())
        except Exception as exc:                 # a captain fault costs the card, never the game
            logger.warning("virelai opening halted: %s", type(exc).__name__)
        self._virelai_card = str(render_field_card(
            _card_dict_from_captain(captain), game_id=str(self.game.game_id)))
```

**B.3 · THE HAZARD, ASSERT IT.** `arcengine.GameAction` is an Enum whose members carry a
**mutable `action_data` instance created once at class definition** — it is process-global
state. A click coordinate the captain writes survives after the captain stops. The duck's own
path rebuilds `data` in `_model_mouse_action_data`, but nothing enforces that.
**Write a test that the captain's final `action_data` is not readable as the model's first.**

**B.4** `_card_dict_from_captain(captain)` reads the captain's weave into the card's dict.
**Source is `captain.ctx` and the weave — never `ctx.semantic_library`.** Fields required by
`virelai_field_card_v6`: `game_id · level · actions · lives · world_type · ego_mode · grid ·
ego{sealed, footprint, anchor, model, observed} · ego_seal · worldlines[{id, cells, anchor,
role, seal, fields, cov, revisit, ticks, multi}] · ground_note · frontier{...} · hud ·
win_seen · visual_objects · roster`.
**`tools/golden_log_adapter.py` shows every one of these being filled from the same facts, on a
log. Use it as the field map, never as the production route.**

### PHASE C — the handover, and the lockstep deletion

**C.1** Inject `self._virelai_card` into the analyzer's first call so it appears in turn 1.

**C.2 · LOCKSTEP DELETION, OWED IN THIS RING.** The prompt prose telling the model to discover
the world by experiment is what the card replaces. **It dies here.**
```bash
wc -w ~/Desktop/duck-virelai/variants/ring4/ARC3-Inference/inference/agent/prompts.py
wc -w ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/inference/agent/prompts.py
```
**The ring6 count must be LOWER.** A ring that adds a section and grows the prompt has replaced
nothing. METHODOLOGY's health metric: the prompt shrinks as the library gets smarter.

### PHASE D — the bundle

**Answer P8 first.** If a generator exists, use it. Otherwise, following the ring5 → ring5-p2
precedent:
```bash
cd ~/Desktop/duck-virelai/kaggle
rm -rf ring6 && cp -R ring5 ring6 && cd ring6
rsync -a --delete ~/Desktop/duck-virelai/variants/ring6/ARC3-Inference/ \
      source-dataset/src/ARC3-Inference/
sed -i '' 's/duck-virelai-ring5$/duck-virelai-ring6/'                  source-dataset/preamble.txt
sed -i '' 's|duck-virelai-ring5|duck-virelai-ring6|g'                  source-dataset/dataset-metadata.json
sed -i '' 's|duck-virelai-ring5|duck-virelai-ring6|g'                  kernel/kernel-metadata.json
sed -i '' 's|source-duck-virelai-ring5|source-duck-virelai-ring6|g'    kernel/taaf_kaggle_run_share.ipynb
```
**Passes stay at 1** — do not touch `benchmark_initial.pkl`.

**VERIFY BY CONTENT, NEVER EXISTENCE:**
```bash
cd ~/Desktop/duck-virelai/kaggle/ring6
python3 -c "d=open('source-dataset/benchmark_initial.pkl','rb').read(); i=d.find(b'n_passes'); print('passes:', repr(d[i:i+12]))"
grep -H 'benchmark.passes\|benchmark.label' source-dataset/preamble.txt
grep -H '"id"' source-dataset/dataset-metadata.json kernel/kernel-metadata.json
find . -name '__pycache__' -o -name '*.pyc' | head
du -sh source-dataset
```
Expect `n_passes\x94K\x01`, `benchmark.passes: 1`, both ids on ring6, **zero `__pycache__`**
(it has been found in a shipped bundle before), and a source-dataset in the low hundreds of MB
at most.

---

## §4 · RED THEN GREEN — demonstrate, never assert

Each guard must be broken and the failure observed, not reasoned about.

| RED to inject | must fail |
|---|---|
| remove the `_virelai_opening()` call from `play()` | the opening-ran test |
| return an empty captain weave | the card renders **all seven sections with v3.5's fallback sentences**, none blank |
| hand the card a CLICK world with nothing sealed | §1 says nothing is confirmed to be you; no invented body |
| leave a click coordinate on `GameAction.ACTION6.action_data` | the B.3 hazard test |
| put a colour name or a `###` id into a worldline dict | the firewall test |

Restore all; everything passes.

---

## §5 · VERIFICATION, OFFLINE

```bash
cd ~/Desktop/duck-virelai/variants/ring6 && \
  PYTHONPATH=ARC3-Inference/inference/framework \
  python3 tools/golden_log_adapter.py /tmp/ring6.log
```
Known-good reference from 2026-08-28: **27 worldlines parsed, ~22 targets, ~2,900 chars.**
A different card from the same log means the renderer moved.

**Do not claim the driver works. It is measured on Kaggle.**

---

## §6 · THE KAGGLE RUN

```bash
cd ~/Desktop/duck-virelai/kaggle/ring6/source-dataset && kaggle datasets create -p . -r zip
```
Wait for the upload to finish, then:
```bash
cd ~/Desktop/duck-virelai/kaggle/ring6/kernel && kaggle kernels push -p .
```
Confirm both landed:
```bash
kaggle datasets status stephenkaskin/taaf-kaggle-source-duck-virelai-ring6
kaggle kernels  status stephenkaskin/taaf-duck-virelai-ring6-share
```
Then **Save & Run All** in the browser — the push uploads, it does not start:
`https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring6-share`

**25 games, 1 pass, ~2.2h of quota. DO NOT SUBMIT.**

When it completes:
```bash
kaggle kernels output stephenkaskin/taaf-duck-virelai-ring6-share \
  -p ~/Desktop/duck-virelai/runs/kaggle-ring6/kaggle-output
```
If `datasets create` reports the id already exists:
```bash
cd ~/Desktop/duck-virelai/kaggle/ring6/source-dataset && \
  kaggle datasets version -p . -r zip -m "ring6: captain probes first"
```

---

## §7 · THE READ — pre-registered, and not to be revised after the run

**COUNT IN `transcripts/`, NEVER `prompts/*.log`.** That file is a latest-model-call snapshot;
counting in it produced a finding that had to be retracted (METHODOLOGY §5).

| # | fixture | measure |
|---|---|---|
| F1 | **the captain ran before the model** | probe presses recorded before `analysis_step 1`, every game |
| F2 | **the card reached the model** | `§1 — What Am I?` in the turn-1 prompt, every game |
| F3 | the card is read whole | `§7 — What Have I Tried?` present at ≥ 78% of renders (ring4's GAPS rate, 64/82) |
| F4 | the card is informative | where the captain sealed anything, ≥1 named role in §2 |
| F5 | **negative control** | a game where nothing seals renders all seven sections, none blank |
| F6 | **negative control** | a CLICK world's §1 says God Mode or an honest absence |
| F7 | no firewall leak | zero colour names, zero `class N`, zero `###` ids in any card |
| F8 | behaviour changed | model-issued actions differ on ≥1 game vs ring5 |
| F9 | the captain is cheap | probe wall clock < 5% of the per-game budget, every game |

**KILL CONDITIONS:**
- **F7 fails** — a firewall leak kills regardless of score.
- **F1 fails on >20% of games** — the sequencing did not happen; this ring did nothing whatever
  the score says.
- **F2 fails while F1 passes** — the captain ran and the handover is broken. Worse than a low
  score, and not fixable by editing the card.
- **A role appears in prose that no evidence earned.** Ring 4 rendered 76 ego seals including a
  1-cell speck; in prose that becomes a confident English sentence.

**SCORING, and this is the part that goes wrong if rushed.** The probe adds ~130 actions to
level 1 and the metric is quadratic. **Compute the expected penalty per game in advance from
ring4's per-game action counts, subtract it, and read the residual. Per game, never
mean-to-mean.** On the 14 games at 0.00 it costs arithmetically nothing; on tu93, which
finished in 60 actions, it erases the game.

**Compare against ring5 (1 pass), never against ring5-p2 or ring4-p2.**

---

## §8 · DEFINITION OF DONE

- ☐ P1–P8 answered, each by its own command. P8's answer reported.
- ☐ Import RED closed; every restored file recorded.
- ☐ Stub is ten lines and provides exactly two attributes.
- ☐ Exactly one import line changed in the vendored `virelai.py`.
- ☐ §4's REDs injected and observed failing, then restored.
- ☐ `wc -w` on `prompts.py` FELL.
- ☐ Bundle verified by content; zero `__pycache__`.
- ☐ `variants/ring6/MANIFEST.md` written.
- ☐ One Kaggle run, read against §7, nothing revised after the fact.
- ☐ A return filed with FIDELITY and CORRECTNESS graded **separately**, and CORRECTNESS not
  self-assessed.

---

## §9 · WHAT THIS WORK ORDER MAY NOT DO

- **May not change the weave, the ledger, or ring 4's `virelai_card.py`.** That table card is
  the control.
- **May not change the pass count.** Ring E is `kaggle/ring5-p2`.
- **May not invent a win model.** None exists golden-side or hybrid-side. The card says *"no
  state has ever been observed as a win"* and that sentence stands.
- **May not build the searchable memory.** That is Ring 7 —
  `claude/searchable-memory-read-2026-08-28.md`.
- **May not claim the driver works.** Behaviour is measured at the Director's terminal.

---

*Issued 2026-08-28. Every measurement quoted in §1 and §7 was made on 2026-08-28 and is named
where it was made. The committed tree outranks this document.*
