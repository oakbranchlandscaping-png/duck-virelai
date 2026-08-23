# Bundle v2 push — kernel only (share variant)

v1 failed by mechanism (pickled `__auto__` env spec rejected by the frozen public build —
see TASK-DR-DECISION-MEMO.md). v2 replaces ONLY the kernel with Tufa's share template:
it rebuilds the game list at runtime from the competition dataset's own environment_files
mount (Phase A) or the live gateway (Phase B). Dataset unchanged — config parity verified
in the v1 dataset pickles (28 concurrent, 132 min/game, 540 min cap, 1 pass, 900 s
analyzer timeout).

## The one command (Mac terminal, new window OK)

    export PATH="$(python3 -m site --user-base)/bin:$PATH" && cd ~/Desktop/duck-virelai/kaggle/dryrun-r0/kernel-v2 && kaggle kernels push -p . --accelerator NvidiaRtxPro6000

Expected: "Kernel version 2 successfully pushed."

## Then (browser)

1. Meter reading (before).
2. https://www.kaggle.com/code/stephenkaskin/duck-virelai-r0-dryrun — version 2 runs on push.
3. Minute ~10 is the v1 failure point: games must START (look for game/board activity
   after the vLLM smoke test). If it instead errors with "No offline environments found
   under /kaggle/input/competitions/arc-prize-2026-arc-agi-3/environment_files", that is
   the memo's named risk — stop, send the log, the fallback ladder applies.
4. Quiet block ~2.5–3 h (soft-stop trims before the 9 h cap). No babysitting needed.
5. On finish: meter reading (after) + download `benchmark.json` from the Output tab →
   this is baseline run #1. Send both. No Submit click yet — Phase B is a separate
   decision put to you after run #1 is scored.

## Exit-check note (for the record)

The build order's check #3 expected a one-line `ls` diagnostic of the competition input
in the notebook; no such line exists in Tufa's share template (it never did). Not added —
editing the emitted notebook is outside the order. Functional equivalent already present:
if the env mount is absent, `_offline_games` fails loudly naming the exact path, which
converts the mount assumption to VERIFIED-or-named-failure either way.
