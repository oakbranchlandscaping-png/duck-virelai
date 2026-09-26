# G1 closure local pilot

**Purpose:** Validate the repaired G1 answer and demonstration path on `ls20` through OpenRouter
before freezing another Kaggle package.

## Preconditions

- Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.
- `OPENROUTER_API_KEY` is loaded from that directory's ignored `.env` file.
- `ARC_API_KEY` is loaded from the same file or the process environment.
- Exact model: `Qwen/Qwen3.6-27B`. Do not substitute another model and compare the behavior as if
  it were the same test.

OpenRouter authentication and one minimal request to this exact model succeeded on 2026-09-22.
ARC authentication also succeeded through a read-only game-catalog request, which exposed all
three target worlds without creating a game session or executing an action. Both external
prerequisites are ready.

Use the hidden-input helper for the OpenRouter key. Never paste secrets into a tracked file,
terminal command, transcript, or report.

When the ARC key is available, store it from the active `ARC3-Inference` directory with:

```bash
./scripts/configure_arc_key.sh
```

The prompt hides input, preserves the existing OpenRouter entry, and leaves `.env` owner-only.

## Bounded configuration

`configs/g1-closure-live-pilot.json` fixes:

- one world: `ls20-9607627b`;
- one pass and one worker;
- 16 environment actions;
- 20 minutes for the world and 22 minutes for the experiment;
- 65,536-token context and 1,024-token tool display budget;
- gated Virelai mode, current-grid image context, and request logging.

## Launch

From the active `ARC3-Inference` directory:

```bash
CONFIG_PATH=configs/g1-closure-live-pilot.json \
RUN_NAME=ring9-g1-closure-local-ls20-v1 \
VIRELAI_MODE=gated \
make run
```

## Grade only this milestone

The pilot passes when the trace directly shows:

1. G0 accepts the exact opaque action surface.
2. G1 executes the eight paired probes in order.
3. Duck explains the complete composite ego and the observed opaque action laws.
4. The controller accepts a prospective `PATTERN_TRANSLATION` claim.
5. A later action supports the claim and produces a complete demonstrated after-footprint.
6. A versioned observed `EgoLaw` closes G1.
7. G2 opens and binds its first ranked collision target or first G2 probe.

Record rejection count and correction latency. A rejection is useful only if its reason is visible
and Duck promptly fixes the named field. Do not grade counter identification, level completion, or
win discovery in this pilot.

## Stop and inspect

Stop the build ladder and inspect before packaging if:

- Duck still cannot see a rejection reason;
- the template encourages a partial one-color ego footprint;
- the demonstration absorbs the separate bottom-bar rewrite into the ego;
- G2 receives a stale or partial footprint;
- the run silently changes model, world, action budget, or concurrency.
