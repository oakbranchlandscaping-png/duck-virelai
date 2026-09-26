# G4.2 repeated activation and orbit discovery

**Status:** live-confirmed for CLICK lever E0004 on vc33; broader lever/world coverage remains open  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Predecessor:** live-confirmed G4.0/G4.1 effect anatomy  
**Next missing capability:** NAV/HYBRID re-contact piloting

## Question and exit

G4.2 asks one narrow question: **what counter-masked state sequence appears when the same confirmed
lever is activated repeatedly?** It does not yet infer capacity, permanence, reversibility,
conditions, coupling, or purpose.

For each G3-confirmed lever, the controller repeats the exact G4.1-bound intervention. Every new
counter-masked full-grid fingerprint keeps the orbit open. The lever descent ends only when:

- the next masked state equals the immediately preceding state: `NULL_AT_OBSERVED_STATE`; or
- the next masked state exactly equals any earlier state: `OBSERVED_STATE_RECURRENCE` with its
  observed recurrence index and period.

A level, game, or run boundary yields `BOUNDARY_INTERRUPTED`. It preserves the observation but does
not satisfy the orbit. External action and runtime budgets leave an active orbit unresolved; no
fixed activation count is an epistemic stopping rule.

Boundary interruption belongs to the later cross-level lifecycle. G4.2 records it without trying
to determine what should carry into the next level, and the CLICK lever-typing ladder continues
with evidence from completed level-local orbits.

## Ported material

This slice ports the useful mechanism rather than its older architecture:

- V4 `library/cycle_probe.py`: mask first, then compare complete state hashes; adjacent equality is
  null and equality with an earlier non-adjacent state is recurrence.
- V4 `cybernetic/state_tracker.py`: retain every novel configuration and its action edge.
- Golden G4-03 planning: return when presses repeat instead of reveal, with no threshold.
- Active Ring 9 `masked_world_state.py`: reversible counter mask, exact full-grid addresses, and
  HUD/world delta partition.

## Implementation

`inference/framework/g4_orbits.py` owns the evidence record. A `LeverOrbit` retains the initial
masked address, every later address, every exact non-counter cell rewrite, evidence references,
recurrence location, observed period, and boundary state. It rejects discontinuous transition
chains and refuses an explanatory answer before an evidence-defined stop.

`inference/framework/virelai_gates.py` registers `G4.2-LEVER-ORBITS` after `G4-REACTIONS`. The gate:

- takes its subjects and exact interventions from `LeverEffectAnatomySet`;
- authorizes one repeated confirmed click at a time;
- keeps probing while masked states are novel;
- requires Duck to explain the observed sequence after null or recurrence;
- validates the supplied intervention, state sequence, recurrence fields, and ordered evidence
  references exactly;
- emits `LeverOrbitSet` only after every confirmed lever has a closed, explained orbit;
- exposes the compact gate card automatically and the full record through
  `virelai('orbit', id=entity_id)`.

The active binding gate now intercepts `virelai('agenda')` and returns the gate card. This prevents
the older passive semantic agenda from taking control after a cybernetic checkpoint transition.

## Evidence boundary

The CLICK path is locally complete. Focused orbit tests cover counter-only masked nulls, novel
chains, exact recurrence, absence of count-based completion, boundary interruption, strict answer
binding, continuity rejection, and the G4.1-to-G4.2 product path. The complete offline suite passes
**348 tests**, excluding only the explicitly online arcade and native-observer suites.

This is infrastructure evidence. No served model has yet demonstrated G4.2, and no Kaggle package
has been created from these bytes.

## Deliberate remaining boundary

An embodied lever cannot safely be tested by blindly replaying the movement action that first made
contact. NAV/HYBRID requires a re-contact controller that uses the known ego law to move away when
necessary and pilot back to the same entity. Until that slice exists, G4.2 returns
`WAIT_FOR_NAV_RECONTACT_CONTROLLER` and makes no orbit claim.

The observer records entity ids first appearing during an orbit transition. Reliable entity-specific
G3 reopening still needs a dedicated dynamic-frontier slice: responder fragments must be separated
from genuinely new actionable visual objects before they enter the ranked probe roster.

## Live exit criterion

Run the fast OpenRouter lane on vc33. Pass only if Duck:

1. enters G4.2 directly after G4.1;
2. repeats the exact confirmed click for the current lever without consulting the passive agenda;
3. continues through every novel masked state;
4. stops on the first actual masked null or exact recurrence;
5. explains the supplied state sequence and observed stop without promoting it to a universal law;
6. advances to the next confirmed lever and ultimately emits `LeverOrbitSet`.

Score and win discovery remain outside this checkpoint.
