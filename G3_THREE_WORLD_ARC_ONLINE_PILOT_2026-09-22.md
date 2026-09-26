# G3 three-world ARC online pilot

**Purpose:** fast behavioral validation before any 25-game Kaggle sweep.  
**Evidence state:** prepared; no execution claim yet.

## World set

| Order | Game | Expected arm | Rule |
|---|---|---|---|
| 1 | `ls20-9607627b` | NAVIGATION | User-established classification; verify metadata in the trace. |
| 2 | `vc33-5430563c` | CLICK_GOD_MODE | User-established classification; verify metadata in the trace. |
| 3 | `ft09-0d8bbf25` | Metadata-selected | Chosen as the remaining configured world; do not assume its arm before G0. |

## Per-world exit criteria

The run is useful only if the trace lets us grade the G3 contract for that world:

- metadata selects the correct arm;
- the scheduler follows visual rank;
- the counter mask remains present and monitored;
- entity ids and dossiers persist;
- every positive witness receives a separate confirmation;
- null, ambiguous, and boundary results stay distinct;
- the sweep stops when G3 is complete;
- no win is guessed.

Use `configs/g3-three-world-openai.json` with `OPENAI_API_KEY` supplied through the runtime
environment; the key is never stored in the repository. Run the three worlds sequentially with the same model, prompt, step budget, and concurrency. Save
the raw trace and final gate snapshot separately for each world. Run
`evaluate_g3_checkpoint` per world; do not average away a world-specific failure.

## Interpretation

These ARC online runs establish behavioral readiness and reveal prompt/controller friction quickly.
They do not validate the Kaggle package mount, manifest, deployment reserve, or served Kaggle
runtime. A clean three-world result authorizes a small Kaggle smoke run; it does not yet justify a
25-game sweep.
