# Gate theses — the goal of every gate, outline form

**Type:** `GATE_THESES` · **v2** · **2026-09-20**
**Supersedes:** `GATE_THESES_v1_2026-09-20`. v2 lands four Director rulings from the gate
discussions of 2026-09-20: the object-centric definition, the world-type branching law, the
unified G3/G4 per-object lifecycle with its scheduling policy, and grounding corrections from
`GROUNDING_BENCHMARK_FACTS_v1`.

---

## The two standing laws (Director-ruled, gate-independent)

**The object-centric law.** *Each visual object on any given world can have the same questions
asked about it — that is what builds the internal world model.* The model is the dossier table:
rows are the visual objects the weave individuates (kept stable by the continuity machinery
across re-minting, split, and merge); columns are the standard questions — self-state, ego,
bookkeeping, response-when-acted-on, remote effect, conditions, contact behavior, own schedule,
never-tried. The gates are the lawful ordering of the columns; the empty cells are the
exploration policy (the next action is the cheapest press that fills a cell); the belief state
is full when every present object's askable cells are answered or certified. The machinery is
the question set; the contents are the answers — the questions transfer to every world, no
answer ever does.

**The world-type branching law.** CLICK, NAV, and HYBRID are three probe grammars with
different code paths, not difficulty settings. Every gate contract from G1 up carries explicit
per-archetype branches; a contract silent on an archetype is incomplete, not implicitly
general. (Recorded failure behind it: a dispatch table that carried only CLICK keys.) Hybrid
default: click arm to exhaustion first; collide only for what the pointer cannot reach or what
clicked null.

Grounding constraints that bind every gate (`GROUNDING_BENCHMARK_FACTS_v1`): the world is
synchronous — nothing changes except in response to an action; budgets are ~5× the human
baseline per level and terminate the level; animations are evidence attached to their action's
transition; Undo is designed against only where G0's metadata reports it.

---

## G3 + G4 · The lever lifecycle — one work, object-centric (the frontier)

**Ruled:** G3 and G4 are the same work, walked per object, not all-or-nothing phases. The sweep
discovers activity → that object's G3 runs (witness, basic typing) to saturation → that
object's G4 opens (causal expansion) → its law locks under a contradiction monitor. A lever
discovered later enters at its own G3 regardless of its siblings' depth. At any moment a level
holds objects at different depths.

**G3 — discovery and witness (per object).** Which interventions produce effects outside the
acted locus. Sweep: roster derived from the visual-object definition, re-derived from the
record each turn (never a stored id-keyed queue), ordered smallest footprint → lowest
class-integer → nearest (0,0); Duck goes through it in order — interpreter during the sweep.
Split cascade on the attributed residue: responded / no-response-yet (never "inert"), then
local / remote; local-only files as contact-response evidence, remote-bearing proceeds. LEVER
is ∃ — one witness, permanent. The sweep ends only on enumeration-completeness, scheduled
within the level's action budget, with the certificate recording what the budget forbade.

**G4 — causal expansion (per saturated object).** Under what conditions each cause produces its
effect, and what depends on what: effect subjects, bearing and magnitude (animations are the
free trajectory channel), conditionality read as masked-state discrimination (same press, same
world address → same effect, or a condition is found, or the law dies — the synchronous world
makes this exact), couplings, repetition law, saturation. Two halves: the free half — a passive
kernel reading every transition the run produces anyway; the paid half — single-action frozen
demonstrations and rare discriminating re-presses. Where Undo is offered, the Undo protocol is
the cleanest same-address discriminator and opens as a child target.

**Scheduling (ruled, with the ratified exception):** pending one-press demonstrations first;
then sweep continuation to enumeration-completeness; then G4 expansions in roster order. A
witnessed lever whose confirming action is already in hand closes immediately.

**Refusals:** counter ticks are HUD delta; effects on the ego or at the contact point belong to
the contact-response family; a change with no attributable intervention files toward G5 —
abstention designed in (the sometimes-mover has no archetype). A scoped prediction failure
never implies no remote effect occurred.

**Exit (per level):** sweep enumeration-complete; every discovered object's lifecycle locked or
honestly stopped (budget, undemonstrable, filed-to-G5); certificates state what was never
tried. The locked-law monitor reopens any object's lifecycle on contradiction.

**Boundary with G5:** an intent-driven pursuer's per-turn motion is G5's process; its
conditioning on world state is shared condition machinery; its collision with the ego is a G4
contact fact.

## G5 · Environmental processes

What changes per-turn or inside animations without an attributable intervention — and its law:
turn-indexed schedule, animation-carried process, or state-conditioned agent (the force
observable is state-conditioned, not "autonomous"; wall-clock forces cannot exist). Product: a
`ForceLaw` or evidence-backed `NOT_APPLICABLE`. Owns the missing archetype (the sometimes-
mover); expect a genuine ruling here, not a port list.

## G6 · Scoped inertness

Interaction coverage certificates per object — aimed, offered, fired, never-tried — read off
the shared spine. INERT is PROVISIONAL always; repetition is a count, not an exhaustion; where
no action can be aimed, inertness is unassertable and the certificate says so. Under per-level
budgets, "never tried, budget spent elsewhere" is the common honest line and correct play.

## G7 · Counter-masked novelty frontier

The masked state machine — (state, key) → state, visited and frontier addresses, per-state
UNTRIED keys, reachability edges labeled by exact interventions — is the designers' own
validation instrument turned inward. Exploration walks reachable novelty under hazard-law
constraints; random-proofing guarantees stumbling cannot win. Contradictions are reported,
never averaged. Saturation is a verdict: `EXHAUSTED_NO_WIN`.

## G8 · Observed-win explanation

The win is a terminal frame the platform announces — never guessed, never sought. Preserve the
boundary: preceding state, action, active laws, participants; explain it in the learned
grammar, bound to the recorded transition. A win during an early gate is preserved as an event
and does not regrade the active gate.

## G9 · Cross-level transfer

Composition is the benchmark's own difficulty model — later levels require earlier concepts, so
carry is load-bearing. The observed goal explanation converts to a falsifiable forward
hypothesis; every carried law is explicitly preserved, specialized, reopened, or rejected.
Nothing transfers silently.

---

## Sealed gates (reference theses — the live build already implements these)

**G0 · Action surface.** Exact opaque interface metadata, zero semantic claims, stated
epistemic limit; the archetype prior is interface axiom. G0's metadata also answers the
grounding checks (Undo presence, offered set) for free.

**G1 · Ego.** A versioned `EgoLaw`: interface-axiom exit on click-only worlds; behavioral
localization and prospective demonstration on embodied and hybrid worlds. No target, counter,
or remote-effect claim rides in on the ego.

**G2 · Counter.** The conserved two-object exchange, prospective rate confirmation, min/max
boundary lock with an observed consequence, reversible mask, retroactive world-address
quotient. Rate recurrence alone never locks the gate.
