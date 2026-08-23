# Task D dry-run — push & submit (Director's Mac)

Built 2026-08-23 by TAAF `kaggle-duck` in dry-run mode (nothing sent to Kaggle yet).
Bundle contents: `source-dataset/` (harness+TAAF snapshot, pickled benchmark: 25 public
games x 1 pass, 132 min/game, 540 min cap) and `kernel/` (notebook + metadata:
RTX Pro 6000, GPU on, internet off, competition attached, private).

## One-time setup (Terminal on the Mac)

    pip3 install kaggle
    mkdir -p ~/.kaggle && echo "<YOUR-KAGGLE-TOKEN>" > ~/.kaggle/access_token && chmod 600 ~/.kaggle/access_token

(Use the current token from kaggle.com -> Settings -> API; regenerate it there first if
you want to retire the one shared earlier.)

## Push (2 commands)

    cd ~/Desktop/duck-virelai/kaggle/dryrun-r0
    kaggle datasets create -p source-dataset -r zip
    kaggle kernels push -p kernel --accelerator NvidiaRtxPro6000

(If the dataset already exists from a previous push, the first command becomes:
`kaggle datasets version -p source-dataset -m "update" -r zip`.)

## Phase A — Save & Run All

The push starts a run automatically. Open
https://www.kaggle.com/code/stephenkaskin/duck-virelai-r0-dryrun
and watch it. Exit = notebook completes end-to-end (offline mode: it plays the bundled
public games; expect it to take up to ~9h, likely much less to *validate*, since failure
modes surface early: wheelhouse install ~minutes, vLLM server start ~10 min, first game
actions shortly after).

**Meter instrumentation (memo #1 §3):** note the GPU quota meter reading right before
starting and right after it finishes.

## Phase B — Submit (spends the day's 1 submission)

If Phase A completed: on the notebook page, "Submit to Competition". Note the meter
before/after again (Phase B reruns have REPORTEDLY not drained user quota — this is the
measurement). Outcome = scorecard appears (any score, even 0.00-with-actions) or the
exact error. Either way, send back: run log (stdout of the run), runtime, meter readings,
scorecard status.

## Known failure modes to expect (halts, not surprises)

- GPU assertion fails -> pool changed (memo §7 watch trigger); file it.
- `Missing attached dataset path(s)` -> the driessmit1 datasets didn't auto-attach from
  kernel-metadata; attach them manually in the notebook editor sidebar (Add Input) and
  re-run.
- vLLM server timeout at 900s -> capture vllm-openai-server.log tail from the run output.
