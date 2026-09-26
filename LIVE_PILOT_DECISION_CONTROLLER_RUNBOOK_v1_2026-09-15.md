# Decision Controller — Three-World Live Pilot

## Purpose

This is a quality gate, not a score run. It runs one pass each of `vc33`,
`ft09`, and `ls20`, sequentially, with at most 40 actions and 20 minutes per
world. It uses the unmodified Duck model plus the explicit Virelai controller
contract.

## Required external access

- `ARC_API_KEY` for the ARC online environments.
- `OPENROUTER_API_KEY` for `Qwen/Qwen3.6-27B`, or an equivalent configured
  endpoint serving the exact Duck model.

Do not silently substitute another model. This pilot tests Duck's behavior with
the controller, not generic model compliance.

## Launch

From `variants/ring8-decision-controller/ARC3-Inference`:

```bash
CONFIG_PATH=configs/controller-live-pilot.json \
RUN_NAME=ring8-decision-controller-live-pilot-v1 \
VIRELAI_MODE=controller \
make run
```

## Automatic engineering evaluation

```bash
python tools/evaluate_controller_pilot.py RUN_DIRECTORY \
  --output RUN_DIRECTORY/controller_evaluation.json
```

The evaluator reads executed decision, transition, comparison, and revision
artifacts. It does not count system-prompt or user-prompt text as adoption.

## Human gate

For each world, review whether the focus was useful, whether Duck's declared
scope matched its stated experiment, whether the verdict matched observable
reality, and whether a later decision actually retrieved or used an earlier
revision. Do not proceed to Kaggle if the engineering trace passes but these
semantic judgments fail.
