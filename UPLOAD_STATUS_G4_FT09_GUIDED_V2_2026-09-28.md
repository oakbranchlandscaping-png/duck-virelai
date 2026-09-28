# Ring 9 ft09 guided v2 upload status

**Prepared:** 2026-09-28
**Author:** Claude (Alpha build seat), signed. The Director runs the upload commands.
**Status:** packaged and verified; not yet uploaded.
**Revisions carried:** R9-R04 (G3 bounded card, A6; counter trigger label, A1 v2) and R9-R05 (G3
entity identity survives recolour in place).

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-g4-ft09-guided-v2` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-g4-ft09-guided-v2` (private); accelerator `NvidiaRtxPro6000`; internet off |
| Package | `kaggle/ring9-g4-ft09-guided-v2/` |
| Packager | `tools/package_g4_ft09_guided_v2.py` |
| Source commit | `4329185bd77eec5f3a4bb8c73d76f08bd36cb1ce` (R9-R05, on top of R9-R04 `8319853`) |
| Package manifest SHA-256 | `d4047476837f5f2c55f0d519397ded699f99373dd0b5d3780d523be2d719a476` |
| Source manifest SHA-256 | `f3ecef250a0f24801909920d5cb4b7fa8dd12f17500bc2cfe064428370247215` |
| Base | The committed `ring9-g4-ft09-guided-v1` package (`b68228a`; manifest `ed456471…d8`, which the packager checks before building). Its notebook ran on Kaggle on 2026-09-28 with a byte-identical receipt. |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM |
| World and budget | `ft09-0d8bbf25`; one pass; concurrency 1; 200 environment actions and 10,800 s of behavior time after model setup. Same as guided v1. |

## The question

With the G3 card bounded (A6), the counter label checked against the record (A1 v2), and entity
identity that survives a recolour (R9-R05): does the stated-target ladder carry ft09 past G3 to a
G4-A lever study that Duck executes by its own presses?

## Preregistered criteria

These are frozen in `checkpoint-preflight.json` and `RUN.md`. They are the v1 criteria plus
three more:

- **G2-1:** G2 closes under axiom A1, or as not-observed after full coverage.
- **G2-2:** mask purity, recomputed from the artifacts.
- **G2-3 (new):** the accepted trigger is admissible for the trigger class computed from the whole
  G2 record.
- **A6-1 (new):** no binding card exceeds 24,000 characters at any gate.
- **G3-1 (new; a prediction from the offline ladder):** G3 witnesses both control tiles as levers,
  and neither is filed `UNRESOLVED_ATTRIBUTION`.
- **P:** G3 closes with at least two levers and a G4.1 anatomy for each.
- **A-1 to A-3:** G4-A closure, audit fidelity, and explanations scoped to what was observed.
- **N-1:** no idle without a legal move.
- **R (reported):**
  - actions and wall time per gate;
  - Duck's choices;
  - bar cells remaining at the end;
  - the largest card at each gate.
- **I1–I4:** infrastructure checks.

**Offline expectation:** this is a reference point, not a graded prediction. The real G2 record,
followed by the recorded control law continued by hypothesis, reaches G4-A `SATISFIED` at
transition 131. The largest card is 15,792 characters.

## Verification before upload

- **`tools/verify_kaggle_package.py`:** 8/8 passed. That includes the bundled source being
  byte-identical to the Director's `git archive` export of `4329185` (`src_4329185.tar.gz`, both
  source paths).
- **`tools/simulate_kaggle_preflight.py`:** the notebook's real start-up cells ran in all three
  mount layouts (nested, zip, direct). Each verified the source manifest, the ft09 world
  allowlist and the execution receipt. Each also set the 10,800 s window from benchmark start.
- **Negative control:** a copy with one appended byte in `entity_observation.py` was rejected by
  both checks:
  - the verifier failed it 4/7, flagging the manifests and `src.zip`;
  - the notebook preflight stopped at "Source manifest verification failed".
- **Tests:** at `4329185` the cloud suite shows 411 passed and 1 skipped; the Mac shows 400 passed.
- **Rehearsal:** the packager was dry-run on an equivalent export before the commit existed. The
  real export matched it file for file, ignoring bytecode.

## Risks stated before the run (hypotheses, not findings)

1. **The toggle law is extrapolated.** After transition 57, ft09 may not behave as the offline
   ladder assumes.
2. **The bar may run out.** It allows about 32 effective clicks, and the offline ladder uses 15.
   Broken runs by Duck in G4-A use up the margin, and what happens when the bar empties is unknown.
3. **Label refusals cost time.** Duck may be refused for a wrong trigger label (A1 v2), which is
   intended. Each refusal costs a model turn, not an action.
4. **G3 repeats G2's clicks by design**, about 64 actions and roughly 35 minutes at v1's pace.
5. **A declared end still idles until the deadline** (the A2 open item, R9-I02).

— Claude, Alpha build seat, 2026-09-28
