# PUSH — Ring 1.1 kernel (duck-virelai-ring11): the Virelai ontology implant

Two commands from a fresh Mac terminal window. New dataset + new kernel; r0 and ring1
are untouched.

## 1 · Create the ring11 source dataset

```
cd ~/Desktop/duck-virelai/kaggle/ring11/source-dataset && kaggle datasets create -p . -r zip
```

## 2 · Push the ring11 kernel

```
cd ~/Desktop/duck-virelai/kaggle/ring11/kernel && kaggle kernels push -p .
```

Then open https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring11-share
and **Save & Run All** (public 25 games, ~2.5h of quota). Do NOT Submit yet — the
public A/B decides promotion. When it completes:

```
kaggle kernels output stephenkaskin/taaf-duck-virelai-ring11-share -p ~/Desktop/duck-virelai/runs/kaggle-ring11-2026-08-25/kaggle-output
```

What this build is: axioms + output contract + five-beat Virelai strategy in the system
prompt; Tufa's object-matching, frame-diff, and goal-search coaching DELETED; world model
narrowed to interpretive content; full walked-state map queryable in the sandbox as
`virelai`; loud batch accounting; RESET as known-destination teleport with root marking.
One variable vs the frozen baseline. Scoring bar: paired significance on terminal +
hold the score-at-budget win; over-pressing should fall.
