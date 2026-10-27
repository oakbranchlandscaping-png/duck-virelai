# Contributing

Virelai is a research archive and prototype. Contributions that make an idea easier to understand, reproduce, test,
or falsify are especially useful.

## Good first directions

- Build a small standalone example of the gate ladder outside ARC-AGI-3.
- Reduce the world-model schema while preserving provenance and open questions.
- Add adversarial fixtures for identity continuity, counter masking, or lever attribution.
- Compare dossier-guided exploration against a simpler coverage baseline.
- Improve documentation and diagrams for one subsystem.
- Port the semantic library to a smaller local model.
- Audit a claim in the release note and report contrary evidence.

## Ground rules

- Separate observations from explanations.
- Cite the fixture, receipt, transition, or report that supports a behavioral statement.
- Do not turn a timeout, parser failure, or missing record into a claim about mechanics.
- Preserve fail-closed behavior and frozen-schema readers.
- Add focused tests for behavior changes; update the exact T2 snapshot only for intentional test additions.

## Development setup

```bash
cd variants/ring9-cybernetic-gates/ARC3-Inference
uv sync --locked --extra dev
PYTHONPATH=.:tests:../tufa-arc-agi-framework/src \
  uv run --locked --extra dev python tools/test_tiers.py --check
```

Open an issue before a large refactor. The repository contains substantial history and duplicated packaged source, so
a small, reviewable change is easier to evaluate than broad cleanup.
