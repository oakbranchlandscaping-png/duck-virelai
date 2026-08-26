# PUSH — the two 2-pass power runs (variance reduction, Director-sanctioned)

Both arms identical to their originals except ONE number: each game played TWICE per
run (n_passes=2). Expected wall ~4.5-5h each; each burns its quota. Push both, then
run them one after the other (Kaggle allows one GPU session at a time).

## Arm A — baseline at 2 passes
```
cd ~/Desktop/duck-virelai/kaggle/r0-p2/source-dataset && kaggle datasets create -p . -r zip
```
```
cd ~/Desktop/duck-virelai/kaggle/r0-p2/kernel && kaggle kernels push -p .
```
Then Save & Run All on: https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-r0-p2-share

## Arm B — ring11 at 2 passes
```
cd ~/Desktop/duck-virelai/kaggle/ring11-p2/source-dataset && kaggle datasets create -p . -r zip
```
```
cd ~/Desktop/duck-virelai/kaggle/ring11-p2/kernel && kaggle kernels push -p .
```
Then Save & Run All on: https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring11-p2-share

No Submit on either. When each completes:
```
kaggle kernels output stephenkaskin/taaf-duck-virelai-r0-p2-share -p ~/Desktop/duck-virelai/runs/kaggle-r0p2/kaggle-output
kaggle kernels output stephenkaskin/taaf-duck-virelai-ring11-p2-share -p ~/Desktop/duck-virelai/runs/kaggle-ring11p2/kaggle-output
```
Notes: 50 lanes per arm (25 games x 2) doubles draws; the diagnostics stack pairs
across passes natively. The baseline 2-pass run also closes WO-1 exit B's second-run
obligation (two independent plays per game at the frozen config). Best-of-passes
scoring means each arm's SUMMARY mean will read higher than 1-pass runs -- compare
only through the paired battery, never raw means across pass counts.
