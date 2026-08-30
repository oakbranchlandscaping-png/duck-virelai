# Variant: ring6.3 — exact Captain-to-Duck handoff proof

**Created:** 2026-08-30 · **Executed base:**
`kaggle/ring6.2/source-dataset/src/ARC3-Inference/` · **Runtime label:**
`duck-virelai-ring6.3`

## Ring 6.3 change

Ring 6.2 proved that the Captain could execute, but its report never reached
Duck: `solver.py` offered the report on `analysis_step == 1`, while
`tool_agent.py` appended it only under global `action_num == 0`. Every Captain
had already acted.

Ring 6.3 removes that conflicting action gate and proves the exact report at
the final provider-payload boundary. It fingerprints and saves the report,
inspects a detached copy of every provider-built payload before the post,
saves the first verified payload, and correlates it with a parsed endpoint
response. The observer is fail-open and cannot mutate the live request.

Natural ToolAgent history is preserved. A yielded analysis step does not
freshly append a duplicate when its retained user history already contains the
exact report. Request failures can re-offer it when restored history lacks it.

New durable outputs are `captain_reports/`, `handoff_requests/`, and
`handoff_audit/`. The false-positive `CARD_INJECTED` marker is retired.

The source was seeded from the full tree that executed Ring 6.2, not the
partial `variants/ring6.2` overlay. Empty Finder-style duplicate directories,
`__pycache__`, and `.pyc` were excluded. Historical Ring 6.2 was not modified.

Local verification at construction: **34 dependency-free tests pass**, the
mocked post captures the exact provider payload after `build_chat_payload`,
callback mutation cannot affect the posted object, and callback failure cannot
block the request. Full ARC/TAAF runtime validation remains the Kaggle canary.

## Frozen from Ring 6.2

- V4 Captain code and targeting policy;
- two lives / 320 actions / 480 seconds;
- simple-action `{}` and public MOUSE coordinate bridge;
- life/level snapshots and complete-game stop;
- seven-section report content and ARC ontology;
- Duck model, settings, tools, ledger, and ordinary prompt wording.

---

# Historical manifest inherited from ring6.2

**Created:** 2026-08-29 · **From:** `variants/ring2`'s `solver.py` (driver base) + `variants/ring4`'s
`agent/prompts.py` (lockstep-deletion base) · **Design:** `DESIGN.md`, `BOOTSTRAP.md`
**Ruling basis:** `WO-RING6-01.md` §0 — *"Before the model's first call, the golden v4 captain
plays N=2 lives on level 1. Its findings render as v3.5's field card. The model reads that
card and plays from there. The captain never presses again."*

## Current local candidate — Ring 6.2 — 2026-08-30

Ring 6.1 proved the handoff but exposed a protocol mismatch before the Captain's
strategy could be judged. The Captain passed
`GameAction.action_data.model_dump()` directly into TAAF. In the exact
arcengine 0.9.3 package used by the run, that dump contains an internal
`game_id` field even for simple actions. TAAF's public contract requires simple
actions to carry no data and raises `ValueError` otherwise.

This explains the 18 worlds that faulted before a first Captain action and the
five sustained CLICK runs that reached `GAME_OVER` and faulted when V4 returned
its simple RESET. The remaining CLICK fault after two recorded actions is not
assigned a cause without a detailed exception message.

Ring 6.2 replaces the verbatim model dump with one explicit bridge:

- directional, SPACE, ACTION7, and RESET actions carry `{}`;
- MOUSE carries only integer `x` and `y`;
- no internal `game_id` field crosses into TAAF.

Captain faults now retain the exception type, a bounded message, and a full
log traceback. The machine-readable `PROBE_END` marker includes the bounded
message. This makes any surviving Captain failure attributable on the next
canary instead of collapsing to the word `ValueError`.

Local verification: all **20 dependency-free contract tests pass**; all **203**
Python files in the variant and test tree parse; and the bridge was exercised
against the exact cached arcengine runtime, where simple actions produced `{}`
and a mouse action produced `{"x": 17, "y": 23}` and both passed arcengine
validation. Ring 6.1 remains untouched. The assembled canary is
`kaggle/ring6.2/` with runtime label `duck-virelai-ring6.2`.

This is deliberately an integration repair and diagnostic canary. It does not
yet retune V4's targeting policy; the next run first needs to reveal the
Captain's real NAV and CLICK behavior once its actions can actually reach the
world.

## Current local candidate — Ring 6.1 — 2026-08-29

This section supersedes the deployment status recorded later in this organic build log;
the older failed-run entries remain below as evidence.

The V4 package now lives at `ARC3-Inference/virelai_v4/`, beside `inference/`, and both
`pyproject.toml` files explicitly discover `virelai_v4` and `virelai_v4.*`. This matches
V4's canonical `from virelai_v4...` imports and the Kaggle notebook's repository-root
`sys.path`. There is no nested `inference/virelai_v4` in the candidate bundle.

The opening driver is now a bounded, fault-contained handoff rather than a single final
context dump. It spends at most two lives, 320 actions, or 480 seconds; continues after an
observed level advance; stops on complete-game WIN, environment termination, an outer
harness stop, or a cap; and snapshots the outgoing level/life before V4 clears its scoped
state. Level descent is recorded separately and never mislabeled as a win. Captain actions,
level transitions, snapshots, card injection, and Duck's first action emit machine-readable
`RING6_*` transcript/viewer markers.

The handoff is an expandable sequence of V3.5 seven-section field cards. It preserves each
life/level observation separately, names platform-observed winning transitions, and adds
V4 mechanism evidence to levers as spatial affected regions plus the measured response law
(toggle, cycle, directional, saturated, one-shot, or unknown). Internal worldline ids remain
join keys only and do not render. The system prompt now contains the ARC Grid Multiverse
Ontology and distinguishes universal axioms, Captain evidence, and Duck's live ledger.

Local verification on this candidate: **19 dependency-free contract tests pass**; AST parsing
passes for all **199** Python files in the variant and **228** in the assembled bundle;
top-level `virelai_v4` resolution points at the sibling package; variant/bundle V4 trees and
all handoff files are byte-identical; `inference/agent/action_names.py` is present; and the
offline golden-log adapter still reports **27 worldlines, 22 targets, 3299 characters / 622
total words**. Final hygiene checks report zero `__pycache__` directories and zero `.pyc`
files in both the variant and assembled Ring 6 bundle. Full runtime import and engine behavior remain a Kaggle smoke-test obligation
because this Mac Python lacks `arcengine`, NumPy, and SciPy.

The assembled local candidate is `kaggle/ring6/`, but its authoritative runtime label is
`duck-virelai-ring6.1`: the kernel assigns that label immediately after unpickling the
inherited benchmark, and the bundle marker and printed preamble agree. Use a `ring6.1`
dataset-version message and a `kaggle-ring6.1-run1` output directory when it is launched.
The already-running Kaggle Ring 6.0 job was
not pushed, restarted, cancelled, or submitted while this candidate was built. Its output is
therefore a read of the previous dataset version, not validation of this candidate. Push only
after that run is preserved and reviewed.

## The one variable

A deterministic probe phase, ahead of the model's first token: the golden `virelai_v4`
captain plays N=2 lives against the live engine, its weave renders as v3.5's seven-section
field card, the card reaches the model's turn-1 prompt once, and the prompt's own
discovery-strategy prose — now redundant with the card — is deleted, not duplicated.

## Diff surface

| file | change |
|---|---|
| `virelai_v4/` (vendored) | Phase A — the golden captain, ported whole, PORT-default |
| `virelai_v4/_agent_stub.py` | Phase A — import-satisfying stub, no live game contact |
| `framework/solver.py` | Phase B — `_frame_data`, `_virelai_opening` (the driver: N=2 lives, `_execute_action` at `generated_tokens=0`, `VIRELAI_RING6=0` control-arm kill switch); Phase C.1 — `self._virelai_card` threaded into the `analyzer.analyze()` call at `analysis_step == 1` only |
| `framework/virelai_field_card_v6.py` | unchanged — pre-existing, pure-stdlib, `render_field_card` |
| `agent/prompts.py` | Phase C.2 — copied from ring4 (2633 words), the "How to play" numbered discovery-strategy block deleted and replaced with a single line pointing at the card; **2490 words, a fall of 143** |
| `agent/tool_agent.py` | **fence exception** (see below) — `_build_user_prompt` and `analyze()` gain an additive `virelai_card: str \| None = None` parameter; when set, the card renders into the turn-1 prompt only |
| `tests/test_ring6_action_data_hazard.py` | Phase B.3 — the `GameAction.action_data` singleton-leak tripwire |
| `tests/test_ring6_card_guards.py` | §4 — the five RED-then-GREEN guards, permanent GREEN form |

## The fence exception — `agent/tool_agent.py`

WO §2's MAY-touch list names `agent/prompts.py` explicitly but does not name `tool_agent.py`.
Tracing Phase C.1's injection requirement (the card must appear inside the model's own turn-1
prompt text, not merely be available to solver.py) through `tool_agent.py`'s `analyze()` →
`_build_user_prompt()` call chain, and through `runtime_state.py`'s `Frame`/`HistoryEntry`
schema, ruled out every channel that stays inside the named fence:
`previous_step_summary`/`virelai_digest` populates only *after* a model action and is never
present on turn 1; the raw JSON runtime-state schema is fixed to `current_frame`/`history`
with no free field. The only real channel is `_build_user_prompt`/`analyze()` themselves.

This was surfaced to the Director as a scope question rather than silently resolved either
way (invent a workaround inside the fence, or touch the file outside it) — per the project's
altitude discipline, a WO's silence on a build-site is a halt, not a license. Decision:
**extend the fence to `tool_agent.py`**, minimal and additive only — one new optional
keyword-argument threaded through two existing signatures, no removed or restructured
logic, no other file in `agent/` touched.

## Laws honored

**One frame in, one action out.** The captain's presses inside `_virelai_opening` are
synchronous, one `_execute_action` per loop iteration against the live frame — no queued
plan, no multi-frame script. **The frame is truth.** The card renders only from the
captain's own recorded weave (`_card_dict_from_captain`, sourced from
`captain.ctx.frame_record_log` via the ledger's own reader, never a live side-collection).
**Evidence before belief.** An empty or faulted captain weave still renders all seven
sections — v3.5's fallback sentences, never a blank body and never an invented "you have a
body" or "sealed" claim the evidence doesn't support (`test_click_world_nothing_sealed_...`,
`test_unknown_ego_mode_...`). **Universality / no game-specific knowledge.** The firewall
guard (`test_firewall_no_hash_id_or_colour_leaks_into_rendered_prose`) asserts no `###`
worldline id, no colour/color/class field, ever reaches rendered prose.

## Verification at creation

`py_compile` ×3 (`solver.py`, `tool_agent.py`, `prompts.py`) — all clean. Test battery run
as one batch under a dependency-free `importlib`-based runner (no pytest on this session's
Python; pytest-shaped for Kaggle's runtime, which is the authoritative run): **8 tests, all
PASS** — 3 from the B.3 hazard tripwire, 5 from the §4 card guards.

**A fixture defect the battery caught:** the hazard test's confinement check originally
asserted exactly one whole-file occurrence of `.action_data.model_dump()`; it found two,
because `_virelai_opening`'s own docstring quotes that literal pattern in explanatory prose
alongside the one live read in code. Not a hazard — a wrong assertion. Corrected to require
every occurrence in the file, code and docstring alike, to fall inside `_virelai_opening`'s
own AST-extracted body; a leak to any other function is what actually signals new risk
surface.

**§4 RED-then-GREEN, all five rows demonstrated live this session** (mutate a scratch copy,
observe the specific named failure, restore, confirm GREEN against the real module) before
this file's permanent form was committed: opening-call removal fails `test_opening_ran`;
a whitespace-only section-renderer return survives the module's own `fn(d) or
_FALLBACK[key]` truthy-OR net but fails the guard's `.strip()` check; the GOD_MODE branch
appending the EMBODIED body sentence fails the CLICK-world guard; a raw worldline `id` print
fails the firewall guard; the B.3 hazard has its own dedicated file per above.

**End-to-end NOT_MEASURED until the Kaggle validation run (§6, Director-run).**

## Phase D and §5 — Director-run, verified 2026-08-29

`device_bash` never recovered in time; Phase D's `rm -rf`/`cp -R`/`rsync --delete`/`sed -i`
sequence exceeds what the file-by-file stage/commit workaround can do, so the Director ran
the WO's literal Phase D commands directly on the Mac. **P8 resolved by proceeding with the
WO's own fallback path** ("if a generator exists, use it; otherwise, following the ring5 →
ring5-p2 precedent") rather than the Makefile's `kaggle-duck` target, which was traced this
session to live Kaggle-deployment tooling (`inference-taaf-run --deployment-target kaggle`)
and judged unsafe to hand over as a bare command. Known, accepted consequence: `git_status.txt`,
`setup_commands.json`, `teardown_commands.json`, `deploy_target.pkl` in
`kaggle/ring6/source-dataset/` are carried over from ring5 verbatim — none are in the WO's
sed-rename list, so `git_status.txt` still reads ring5 at commit `bc6f1b0`. Accepted as
stale/informational rather than regenerated, since regenerating them correctly requires the
live tool this ruling declined to invoke. Flagging in case a later chamber reads
`git_status.txt` as ring6's actual anchor commit — it is not.

**Verify-by-content, all pass:** `n_passes\x94K\x01` intact in `benchmark_initial.pkl`
(passes untouched at 1); `preamble.txt` reads `benchmark.label: duck-virelai-ring6` /
`benchmark.passes: 1`; both `dataset-metadata.json` and `kernel-metadata.json` ids read
`ring6`; zero `__pycache__`/`.pyc` hits; `source-dataset` is 3.5M (well inside "low hundreds
of MB").

**§5 offline card verification**, run against `/tmp/ring6.log`: **27 worldlines parsed, 22
targets** — exact match to the 2026-08-28 known-good reference on both deterministic counts.
Rendered card length was 3299 chars / 622 words against a stated reference of "~2,900
chars" — about 14% over the WO's approximate figure. `virelai_field_card_v6.py` is unchanged
by this ring (see Diff surface above), so nothing in ring6's own edits should move the
renderer's output for a fixed input; the WO's figure is explicitly a rounded approximation
(the "~"), and the two exact, falsifiable counts (worldlines, targets) match precisely. Not
re-flagged as a renderer-moved signal on that basis, but recorded here rather than silently
reconciled — if a future chamber can locate the exact byte/char count the 2026-08-28
reference was measured from, worth a direct diff.

## Phase D defect found on the first live run — the WO's own `rsync --delete`, corrected

The first §6 attempt failed before the model ever took a turn: `papermill` raised
`ModuleNotFoundError: No module named 'inference.agent.action_names'` unpickling
`benchmark_initial.pkl`, which imports `solver.py`, which imports that module —
pre-existing code, untouched by any ring6 edit.

**Root cause, diagnosed against the repo, not assumed:** WO §3 Phase D's own literal command
is `rsync -a --delete variants/ring6/ARC3-Inference/ source-dataset/src/ARC3-Inference/`.
`--delete` makes the destination match the source exactly — anything in the destination not
present in the source is removed. But `variants/ring6/ARC3-Inference/` is, by this project's
own ring/variant convention, a **diff-only tree** (only `agent/prompts.py`,
`agent/tool_agent.py`, `framework/solver.py`, and the new `virelai_v4/` vendor drop — nothing
else). Run against that partial source, `--delete` doesn't overlay ring6's changes onto
ring5's bundle — it prunes the bundle down to only what ring6 happens to touch. Confirmed by
directory diff: ring5's shipped `inference/` tree carries `agent/action_names.py`,
`agent/__init__.py`, `agent/python_tool_sandbox.py`, `agent/runtime_state.py`,
`agent/vision_context.py`, all of `framework/{__init__,kaggle,run,virelai_card,
virelai_ledger,virelai_weave}.py`, all of `inference/tools/` (8 files) and
`inference/utils/` (6 files), `inference/__init__.py`, plus the top-level `Makefile`,
`pyproject.toml`, `README.md`, `uv.lock`, `configs/`, `scripts/`, `viewer/` — **every one of
these was missing from the first ring6 bundle.** The four verify-by-content checks in WO §3
never looked inside `inference/agent/`, `inference/tools/`, or `inference/utils/`, so this
passed local verification cleanly and only surfaced on the actual Kaggle run — exactly the
gap "verify by content, never existence" is meant to close, and didn't, because the check
list itself didn't reach far enough.

**The fix: drop `--delete`.** `cp -R ring5 ring6` already gives ring6 a complete, correct
copy of everything ring5 shipped; the rsync's only job is to lay ring6's actual changes on
top, never to prune — ring6 doesn't retire or remove any file from ring5's tree, so a plain
overlay is the correct operation, not a defended one. Rebuilt from `ring5` with the corrected
`rsync -a` (no `--delete`) and re-verified: `action_names.py` present (checked explicitly
this time, `os.path.exists` → `True`), passes still 1, both metadata ids read ring6, bundle
4.4M. One `__pycache__` (`framework/__pycache__/virelai_field_card_v6.cpython-314.pyc`) rode
along from the source variant tree itself — the same recurring shipped-bundle defect ring4's
MANIFEST already named ("owed a check on every prior ring") — stripped from both
`variants/ring6/ARC3-Inference/inference/framework/` and the built bundle; re-checked to
zero hits.

**This is a WO-text defect, not a ring6-specific one — it will recur on every future ring
that follows §3 Phase D verbatim**, since the diff-only variant-tree convention is structural
to this project and `--delete` is incompatible with it categorically, not just this once.
Flagging for CE to consider amending WO Phase D's template command (drop `--delete`
permanently, or add "action_names.py present" and a full old-vs-new file-count diff to the
verify-by-content list) rather than treating this as a one-off ring6 fix.

## Second live-run failure and fix — `virelai_v4` import path + an unguarded probe-setup path

The corrected bundle reached the model this time — no `papermill`/import-time crash — but
every one of the 25 games still ended `state=crashed`, `score=0.00`, `actions=0`, `tokens=0`,
each with `error: ModuleNotFoundError: No module named 'virelai_v4'`. Zero actions on every
game meant the crash happened before a single frame was even read, inside `_virelai_opening`,
before the model ever got involved — explaining both symptoms the Director reported ("score
of zero" and "the time was far too fast").

**Root cause 1, diagnosed against the actual shipped tree, not assumed:** every import of the
vendored captain in `solver.py` (six sites: `_virelai_opening` plus five module-level
helpers) used a bare top-level `virelai_v4.X`. The tree physically ships at
`ARC3-Inference/inference/virelai_v4/` — nested one directory inside `inference/` — but the
Kaggle notebook's own `sys.path` setup (cell 8, `_source_path_entries`) only ever adds the
`ARC3-Inference` repo root to the path, never `inference/` as a separate root. A bare
`virelai_v4` therefore never resolves; `inference.agent.action_names` and everything else
under `inference/` resolves fine because it's a genuine subpackage of the one thing actually
on the path.

**Fix, chosen over the alternative:** two ways to close this — physically move the ~150-file
`virelai_v4/` tree up one level (matches the WO fence's literal wording, but is a bulk
directory move the file-by-file stage/commit workaround cannot do without `device_bash`,
which stayed down throughout), or repoint the six import sites to
`inference.virelai_v4.X` (same physical location, corrected import path, a same-file edit).
Took the second: smaller diff, no bulk move, equally correct since the fence names vendoring
`virelai_v4/`, not a specific nesting depth.

**Root cause 2, found while diagnosing root cause 1:** `_virelai_opening`'s own
`from virelai_v4.virelai import Virelai` and `captain = Virelai(...)` were top-level
statements in the function, executed *before* its only `try/except` — so this exact import
failure (and any future setup failure at that point) propagated out of the function entirely
and crashed the whole game, contradicting the function's own documented guarantee ("a
captain fault costs only the card; it never costs the game"). That guarantee only ever
covered exceptions inside the probing loop's `try:`, not setup ahead of it — a gap that was
real from Phase B onward and simply hadn't been exercised by a real failure until this run.

**Fix:** moved the captain import and construction inside the existing `try`, with `captain`
pre-initialized to `None`. The card-building code below was already defensive —
`_card_dict_from_captain(captain)` is wrapped in its own `try/except` that falls back to an
empty dict on any exception, `NameError` from an unset `captain` included — so this closes
the gap without restructuring anything downstream; a captain-construction failure now
produces the honest, all-fallback-sentence v3.5 card instead of crashing the game, which is
what the docstring already claimed happened.

**Test-before-fix, per project discipline:** wrote `tests/test_ring6_probe_safety.py` —
`test_no_bare_top_level_virelai_v4_import_remains` (AST-scans every import site in
`solver.py` for a bare `virelai_v4` prefix) and `test_probe_setup_is_exception_guarded`
(AST-confirms the captain import and `Virelai(...)` construction are lexically inside
`_virelai_opening`'s first `try` block, not top-level statements of the function). Both
confirmed RED against the broken file (reproducing the exact defects) before either fix was
applied, GREEN after. Full battery re-run as one batch after both fixes: **11 tests, all
PASS** — the original 8 plus these 3.

**Not yet re-verified:** Phase D must be re-run once more against this corrected `solver.py`
before the next Kaggle attempt — the currently-pushed dataset version still carries the
pre-fix file. Neither defect was reachable by any local check before this: `py_compile` only
validates syntax, never actually imports the module graph, and no local test in this sandbox
ever executed `_virelai_opening` for real (no `arcengine` here) — both only surfaced because
an actual Kaggle run exercised the real import graph. Worth naming plainly rather than
letting "8/8 tests pass" or "py_compile clean" read as stronger guarantees than they are.

## Not done

§6 (the live Kaggle run: dataset create, kernel push, Save & Run All, output pull) held for
the Director — this project's sandbox and device bridge cannot reach Kaggle's API, and it is
Director-only under the terminal protocol regardless. Phase D's directory-structure and
content checks passed twice now (`--delete` fix, then this run), but **must run a third
time** to pick up the corrected `solver.py` above before the next Kaggle attempt — the
dataset version currently live on Kaggle still carries the pre-fix file that just crashed all
25 games. §7/§8 (the pre-registered read, Definition of Done close-out) not started — both
wait on a completed §6 run against the corrected bundle.
