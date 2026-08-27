# PUSH — Ring 4 kernel (duck-virelai-ring4): the field card

Two commands from a fresh Mac terminal. New dataset + new kernel; r0, ring1, ring11,
ring2, ring25 and ring3 are untouched.

## 1 · Create the ring4 source dataset

```
cd ~/Desktop/duck-virelai/kaggle/ring4/source-dataset && kaggle datasets create -p . -r zip
```

## 2 · Push the ring4 kernel

```
cd ~/Desktop/duck-virelai/kaggle/ring4/kernel && kaggle kernels push -p .
```

Then open https://www.kaggle.com/code/stephenkaskin/taaf-duck-virelai-ring4-share
and **Save & Run All** (public 25 games, ~2.5 h of quota). Do **not** Submit — the daily
hidden click stays on r0. When it completes:

```
kaggle kernels output stephenkaskin/taaf-duck-virelai-ring4-share -p ~/Desktop/duck-virelai/runs/kaggle-ring4/kaggle-output
```

## What this build is

`virelai_card()` — a dossier the model can call in python, rendered inside the sandbox
from the snapshot already shipped there, so an unread card costs nothing. Sections:
SITUATION, OBJECTS (every sealed read with the observation that earned it **and what
would falsify it**), UNKNOWNS, ACTIONS AT THIS STATE, EXPLORATION, CAUSAL MAP, and GAPS —
which always renders and names what the record does *not* show. Three prompt bullets
deleted in lockstep; the prompt **shrinks** 807 → 668 words on the world addendum.

One variable vs ring3.

## How the run will be read (METHODOLOGY §5, and count in `transcripts/`, never `prompts/`)

1. **Prove-it-ran first.** `virelai_card` appears in transcripts — pre-registered **≥15
   of 25 games** (F1). If it is never called, the ring did nothing and that is the finding.
2. **Fixtures** (baselines from ring3): `"not subscriptable"` **1,666** → must fall (F2);
   `"is an int, not a"` **29** → must fall (F3); prompt words already verified fallen (F4);
   world model names a role after a card call it had not named before (F5); the
   negative-control shape — a game with zero seals renders SITUATION + EXPLORATION + GAPS
   only (F6).
3. Then summary shapes, then the seven-arm table through the diagnostics stack.
4. **Acceptance criterion, v4's own (FRICTION-004):** *does this change what the solver
   does on at least one game?* If not, don't ship it.

## The one thing to watch

A false ego seal is now rendered **with its evidence**, which could make it more
persuasive rather than less. That inversion is pre-registered in DESIGN.md §6 and is the
first thing to check in the transcripts of sp80, ka59 and tr87.
