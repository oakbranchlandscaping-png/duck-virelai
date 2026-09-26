# Gate theses — the goal of every gate, outline form

**Type:** `GATE_THESES` · **v3** · **2026-09-20**
**Supersedes:** `GATE_THESES_v2_2026-09-20`. v3 lands the seven required corrections and the
grounding and wording amendments from the Director-relayed review of v2, verified against the
official ARC-AGI-3 technical report and the repository lexicon where checkable. The per-object
G3/G4 lifecycle and world-type branching direction are accepted as governing, subject to an
explicit node/state contract before implementation.

---

## The two standing laws (Director-ruled)

**The object-centric law.** *Each visual object on any given world can have the same questions
asked about it — that is what builds the internal world model.* Precisely: the dossier's row —
the stable subject the questions attach to — is a **versioned entity hypothesis (a worldline)**,
never a frame-local visual object. Visual objects are recorded as the entity's **sightings**;
splits, merges, recolors, and re-minting are **lineage edges** between entity versions, and the
continuity machinery is what keeps a row from shearing. Columns are the standard questions —
self-state, ego, bookkeeping, response-when-acted-on, remote effect, conditions, contact
behavior, own schedule, never-tried. The gates are the lawful ordering of the columns; the empty
cells are the exploration policy (the next action is the cheapest press that fills a cell). The
belief state's completion claim is never "full": it is a **scoped coverage certificate** —
every currently eligible entity-question is answered, `NOT_APPLICABLE`, `UNREACHABLE`,
`DEFERRED`, or explicitly untried on budget. The machinery is the question set; the contents
are the answers.

**The world-type branching law.** CLICK, NAV, and HYBRID are three probe grammars with
different code paths, not difficulty settings. Every gate contract from G1 up carries explicit
per-archetype branches; a contract silent on an archetype is incomplete, not implicitly
general. Hybrid default: click arm to exhaustion first; collide only for what the pointer
cannot reach or what clicked null.

Grounding constraints binding every gate (`GROUNDING_BENCHMARK_FACTS_v1`, as amended): the
world is synchronous — state changes only in response to an action; the official evaluation
budget is 5× the human baseline per level (equivalence with the Kaggle milestone harness still
needs receipt evidence); animations are evidence attached to their action's transition; Undo is
designed against only where G0's metadata reports it; random play is *probabilistically*
resisted (validation threshold ~1 in 10,000 on non-tutorial levels; tutorial levels may be
randomly solvable) — exploration must be model-guided because chance is unreliable, not
because it is impossible.

---

## G3 + G4 · The lever lifecycle — one work, per entity (the frontier)

**Ruled:** G3 and G4 are one work, walked per entity, not all-or-nothing phases. Discovery →
that entity's G3 (witness, first-order typing) → G3-CLOSED → that entity's G4 (causal
expansion) → law locked under a contradiction monitor. A newly discovered lever enters at its
own G3 regardless of its siblings' depth. ("Saturation" is reserved for the G4 mechanic; G3
completion is G3-CLOSED.)

**Lifecycle states (the node/state contract in brief; the build contract elaborates it):**
`UNTOUCHED → ATTEMPTED → RESPONDED / NO_RESPONSE_YET → WITNESSED (G3) → TYPED (G3-CLOSED) →
G4-READY → EXPANDING → LOCKED`, with `AMBIGUOUS`, `FILED_TO_G5`, `BUDGET_STOPPED`, and
`REOPENED` as recorded side-states. G4-READY is entered on the entity's G3 close; **selection**
is the router's separate decision.

**Evidence and law, separated (ruled):** the historical witness —
`LeverWitness(entity, condition, intervention, remote_effect)` — is **immutable**: later
silence never retracts it, and it dies only if its own attribution is shown false. The
`LeverLaw` built over witnesses is **revisable and versioned**, carrying
`active / stale / contradicted` status. One witness proves capability, permanently; no witness
count ever makes a law unconditional.

**G3 — discovery and witness (per entity).** Sweep: roster derived from the visual-object
definition and resolved to entities, re-derived from the record each turn (never a stored
id-keyed queue), ordered smallest footprint → lowest class-integer → nearest (0,0); Duck goes
through it in order — interpreter during the sweep. Split cascade on the attributed residue:
responded / no-response-yet (never "inert"), then local / remote. The sweep ends only on
enumeration-completeness, scheduled within the level budget, the certificate recording what
the budget forbade.

**G4 — causal expansion (per G3-CLOSED entity).** Effect subjects, bearing and magnitude
(animations are the free trajectory channel), conditionality read as masked-state
discrimination, couplings, repetition law, saturation. The free half is the passive kernel
over every transition the run produces; the paid half is frozen demonstrations and rare
discriminating re-presses. Where Undo is offered, the Undo protocol opens as a child target.

**Prospectivity, absolute (ruled):** a demonstration closes only on a transition produced
**after** its prediction was frozen. Evidence already in hand may *motivate* the prediction;
it may never confirm it. No transition is both hypothesis construction and confirmation. The
scheduling exception is hereby scoped: a witnessed lever whose demonstration *action* is known
gets priority for its one new press — the press still follows the freeze.

**Scheduling (ruled):** the router SELECTS in the order — pending prospective demonstration →
sweep continuation to enumeration-completeness → deeper G4 expansion in roster order.

**Attribution boundary (ruled):** classify by **driver and causal relation, never merely by
affected subject.** Contact-triggered effects belong to reactions; a remotely driven ego — a
teleport, a forced recolor — is a legal lever effect subject (the archive's own teleporter
note). A change with no attributable intervention files toward G5 — abstention designed in.
Counter ticks are HUD delta. A scoped prediction failure never implies no remote effect
occurred.

**Exit (per level):** sweep enumeration-complete; every discovered entity's lifecycle LOCKED or
honestly stopped (`BUDGET_STOPPED`, undemonstrable, `FILED_TO_G5`); certificates state what was
never tried. The locked-law monitor reopens any entity's lifecycle on contradiction.

**Boundary with G5:** a pursuer's per-turn motion is G5's process; its state-conditioning is
shared machinery; its contact consequences are reaction facts; its being *driven* by an
intervention would make it a lever effect subject.

## G5 · Environmental processes

What changes per-turn or inside animations without an attributable intervention — turn-indexed
schedule, animation-carried process, or state-conditioned agent (state-conditioned, not
"autonomous"; wall-clock forces cannot exist). Product: a `ForceLaw` or evidence-backed
`NOT_APPLICABLE`. Owns the missing archetype (the sometimes-mover).

## G6 · Scoped inertness

Interaction coverage certificates per entity — aimed, offered, fired, never-tried — read off
the shared spine. INERT is PROVISIONAL always; repetition is a count, not an exhaustion; where
no action can be aimed, inertness is unassertable and the certificate says so.

## G7 · Counter-masked novelty frontier

The state representation **starts honest about hidden state** — the official validation graph
keys nodes on the returned frame *and hidden state*, so two identical masked grids may react
differently. The initial mapping is `(observable_address, intervention, known_phase) → set of
observed outcomes`; it is promoted to a deterministic function only when evidence establishes
the representation is Markov-sufficient for that world. Precedent for promotion: prior corpora
ran fully deterministic once boundary-event presses were excluded — expect promotion to be
earned often and cheaply, never assumed. Contradictions are reported, never averaged; a
persistent one is hidden state or a mask leak, and telling those apart is its own question.
Exploration walks reachable novelty under hazard-law constraints; frontier exhaustion is a
verdict: `SCOPED_FRONTIER_EXHAUSTED` — scoped to this representation and this budget, never a
claim about the world.

## G8 · Observed-win explanation

The win is never guessed and never represented as a target state before it is observed.
Exploration pursues physics questions and reachable novelty; a terminal transition may be
encountered — and when it is, it is preserved whole: boundary, preceding state, action, active
laws, participants, explained in the learned grammar and bound to the recorded transition. A
win during an early gate is preserved as an event and does not regrade the active gate.

## G9 · Cross-level transfer

Later levels are *expected to accumulate and integrate* earlier concepts (the benchmark's
stated design intent), so carry is load-bearing. The observed goal explanation converts to a
falsifiable forward hypothesis; every carried law is explicitly preserved, specialized,
reopened, or rejected. Nothing transfers silently.

---

## Implemented gates (locally implemented; live status stated per gate)

**G0 · Action surface — live-confirmed** (Kaggle checkpoint, three worlds, exact protocol
compliance). Exact opaque metadata, zero semantic claims, stated epistemic limit; the archetype
prior is interface axiom. G0's metadata also answers the grounding checks (Undo, offered set).

**G1 · Ego — locally implemented, live-unconfirmed.** A versioned `EgoLaw`: interface-axiom
exit on click-only worlds; behavioral localization and prospective demonstration on embodied
and hybrid branches. No target, counter, or remote-effect claim rides in on the ego.

**G2 · Counter — locally implemented, live-unconfirmed.** The conserved two-object exchange is
the **currently implemented counter archetype, not the universal definition of a counter**: a
bookkeeping process that fits no implemented archetype produces `REPRESENTATION_GAP`, never a
claim of absence. Within the archetype: prospective rate confirmation, min/max boundary lock
with an observed consequence, reversible mask, retroactive world-address quotient; rate
recurrence alone never locks the gate.
