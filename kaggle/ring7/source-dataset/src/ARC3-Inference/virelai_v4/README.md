# Virelai V4

A cognitive architecture for the ARC-AGI-3 abstract reasoning benchmark.

---

## What V4 Is

Virelai V4 is a cognitive architecture for the ARC-AGI-3 competition. It encodes reasoning in software through a cybernetic loop: perceive, model, act, observe, update. V4 is not a model, not a wrapper, not a prompt-engineering pattern — it is a structured agent grounded in three foundational axioms.

## V4 Foundation Triad

1. **Captain Sovereignty** — The captain is the only gameplay actor.
2. **Library-Only Action Grounding** — The captain acts only from the Semantic Library.
3. **Expanding Bayesian Taxonomy** — The Library grows through evidence: categories open sub-libraries, variants, causal questions, and win-discovery structures.

The captain remains small. The Library grows in detail and nuance.

V4 is governed by this Triad as both aspiration and build constraint. Current production partially implements the Triad; the Blueprint Absorption campaign closes the remaining gaps. See `docs/governing/CONSTITUTION.md` for full foundational governance and `docs/governing/V4_LONG_HORIZON_BUILD_PLAN.md` for the build sequence.

---

## The Thesis

Intelligence is the efficient reduction of uncertainty about an unknown world through structured interaction. Not pattern completion. Pattern completion requires vast training data and produces brittle generalization. Structured interaction requires a reasoning architecture and produces genuine adaptability.

ARC-AGI-3 was designed to make this distinction measurable. The benchmark presents puzzles drawn from a distribution explicitly out-of-sample from any training data. Solutions require an agent that can model an unknown world, test hypotheses about its rules, and act on grounded belief rather than statistical pattern.

V4 is a proof of concept for that kind of agent. The semantic library is a belief state. The probe strategy is the scientific method operationalized as a decision function. The captain is the agent reading its belief and choosing how to act. The cybernetic loop — perception, library update, captain decision, action, observation — handles the mechanics of keeping belief grounded.

If V4 works, the proof is not just a competition result. It is a demonstration that cognitive architecture matters — that the container shapes the intelligence, that transparency and structure are not constraints on capability but preconditions for it.

---

## Project Status

V4 is in active development under the Blueprint Absorption campaign. Eleven sub-phases sequence the work from current state through campaign closure. As of this README's filing date:

- **Sub-Phases 1–3 closed** on charter (foundation work, captain keystone, Bayesian belief architecture Layer One)
- **Sub-Phase 4 opening** — Captain Sovereignty (operationalizes Axiom 1)
- **Sub-Phases 5–11 sequenced** — level-advance substrate, causal map tier, win-discovery, vocabulary migration, persistence rebuild, variant catalogs, campaign closure

The empirical floor: V4 wins vc33 Life 1 Level 1 under Bayesian Belief Architecture Layer One. This anchor binds every subsequent sub-phase.

For the current state in detail, see `docs/state/CURRENT_MISSION.md`. For the full sub-phase sequence, see `docs/governing/V4_LONG_HORIZON_BUILD_PLAN.md`.

---

## Package Structure

```
virelai_v4/
├── virelai.py                Top-level agent: choose_action(), cybernetic loop
├── captain.py                The captain — Form B walk, behavior tree Selector
├── context.py                VirelaiContext — per-frame shared state
├── library/                  Semantic Library — four hierarchical layers, BBA Layer One
├── cybernetic/               Per-frame update machinery
├── perception/               Frame parsing and delta computation
├── memory/                   Exploration record and cross-frame state
├── strategy/                 Legacy action selection (Strangler Fig; retiring SP8)
├── targeting/                Target identification and tracking
├── falsification/            Probe primitives and causal verification
├── contracts/                Contract specifications
├── tests/                    Test corpus (~1,305 passing)
└── docs/                     All V4 documentation
    ├── governing/            CONSTITUTION, V4_PROJECT_INSTRUCTIONS, V4_LONG_HORIZON_BUILD_PLAN, V4_GLOSSARY
    ├── architecture/         V4_ARCHITECTURE, Library Blueprint, FORM_B_FAILURE_MODE_REGISTER
    ├── state/                CURRENT_MISSION, OPEN_FLAGS_REGISTER
    ├── campaigns/            Per-campaign record (locked on closure)
    ├── historical/           State snapshots and campaign artifacts; not authoritative
    └── deprecated/           Documents superseded by current canonical versions
```

The V4 agent entry point from the framework is `agents/virelai_agent.py` (one level up, in the framework's `agents/` directory).

---

## Where to Read Next

Depending on what brings you here:

- **New reader orienting:** `docs/governing/CONSTITUTION.md` — the foundational layer
- **Picking up build work:** `docs/governing/V4_PROJECT_INSTRUCTIONS.md` — operating discipline
- **Architecture detail:** `docs/architecture/V4_ARCHITECTURE.md` — structural description
- **Current campaign state:** `docs/state/CURRENT_MISSION.md` — where the build is right now
- **Build sequence:** `docs/governing/V4_LONG_HORIZON_BUILD_PLAN.md` — sub-phase sequence through campaign closure
- **Glossary:** `docs/governing/V4_GLOSSARY.md` — terminology
- **Competition platform truths:** `docs/architecture/V4_COMPETITION_REFERENCE.md` — ARC-AGI-3 specifics

The Library Blueprint (Sections 1–3 with amendments) sits in `docs/` and specifies V4's belief state in detail.

---

## Operating Discipline

V4 is built by a small team operating under a chamber architecture:

- **Campaign Director** — sole human authority; ratifies all decisions; runs all live game runs
- **Strategy Chamber** — architecture, campaign design, work order authorship
- **Apex Build Chamber** — strategic authority for architectural questions exceeding strategy altitude
- **Cowork** — build executor; runs tests; executes work orders against formal specification
- **Specialist chambers** — convened for bounded missions (V3.5 Chamber, Kaggle Submission Chamber, task forces)

Work proceeds at the speed of quality. No external deadlines govern pace or scope. The work takes as long as the work takes.

For governance and operating discipline detail, see `docs/governing/V4_PROJECT_INSTRUCTIONS.md`.

---

## Running V4

From the `ARC-AGI-3-Agents/` root (see the framework README for full setup):

```bash
# Two-game canary — NAV and CLICK
VIRELAI_QUIET=1 bash -c '
for game in ls20 vc33; do
  echo "======== $game ========"
  uv run main.py --agent=virelai --game=$game 2>&1
  echo ""
  sleep 2
done
'

# Tests (does not require online API)
cd virelai_v4
python -m pytest tests/ -q
```

Tests are a prerequisite for live runs — never run a live game with failing tests.

---

## License and Contact

[License placeholder — to be filled by Director per ARC Prize Milestone 1 requirements before public submission. Current visibility: Private.]

Project lead: Stephen Kaskin (Campaign Director, Virelai Research Labs)

---

*Filed under WO-DOC-V4-FOUNDATION-TRIAD Phase 4. Governed by the V4 Foundation Triad. See `docs/governing/CONSTITUTION.md` for foundational authority.*
