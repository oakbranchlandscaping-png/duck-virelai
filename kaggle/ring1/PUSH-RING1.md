# PUSH — Ring 1 kernel (duck-virelai-ring1)

Two commands from your Mac terminal (Kaggle CLI + credentials already work there).
This creates a NEW dataset and a NEW kernel — the r0 baseline kernel is untouched.

## 1 · Create the ring1 source dataset

```
cd ~/Desktop/duck-virelai/kaggle/ring1/source-dataset && kaggle datasets create -p . -r zip
```

## 2 · Push the ring1 kernel

```
cd ~/Desktop/duck-virelai/kaggle/ring1/kernel && kaggle kernels push -p .
```

Then open https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring1-share
and **Save & Run All** (this is the interactive Phase A: public 25 games, ~2.5h,
burns quota). When it completes, pull `benchmark.json` from the Output tab as before —
this chamber scores it against run #1 (1.2225 all-25 / 1.2734 ex-ft09).

DO NOT click Submit on this kernel yet — first read is public-set only, per the
Director's one-run-first ruling. If the public read is good, Submit spends nothing
(submissions are quota-free) and the daily submission slot moves to this kernel.

Notes: config is byte-parity with the frozen baseline (28 conc · 132 min/game ·
1 pass · RTX Pro 6000 · internet off). The only variable is the Virelai ledger insert
(disable switch: VIRELAI_RING1=0). Dataset slug is ring1-specific:
`stephenkaskin/taaf-kaggle-source-duck-virelai-ring1`.
