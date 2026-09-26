# Build slice: G1 archetype exit and G2 evidence kernel

Date: 2026-09-19  
Source family: `variants/ring9-cybernetic-gates`

Status update, 2026-09-20: the full G2 gate, evaluator, package, and queued version-2 checkpoint now
exist. The universal ontology prompt was added to active source after that package froze. See
`CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`.

## Why this slice exists

The cancelled vc33 G1 run produced a useful trace. The action surface established a click-only
world immediately, but the controller still required a coordinate-class sweep. Duck recognized
the changing top strip and a larger target-dependent effect, yet could not hand control to the
counter target. That was a controller error rather than evidence that Duck failed to reason.

## G1 correction

For a click-only action surface, G1 now requires Duck to explain that ACTION6 is its pointer hand
and that coordinates select the locus of direct intervention. This creates an `EgoLaw` whose
status is `INTERFACE_AXIOM`, cites `G0-ACTION-METADATA`, and closes G1 without an environment
probe. Exact target effects remain unknown and are assigned to later gates.

Navigation and hybrid worlds still require behavioral ego localization and prospective
demonstration. The shortcut is archetype-specific, not a general relaxation of G1 evidence.

## G2 evidence kernel

The first G2 component ports three useful ideas from existing Virelai work:

- the V4 counter march: a repeated directional visible process is evidence worth tracking;
- the Ring 8 clock compiler: varied interventions, fixed geometry, recurrence, and prospective
  falsification keep the claim observational;
- the Ring 2 ledger: raw frames remain authoritative and masking creates a derived state view.

The new kernel compiles `SCHEDULED_BOOKKEEPING_CANDIDATE` records only when the same integer
rewrite occurs on every supplied transition, at least two intervention keys differ, geometry is
fixed, and no acted coordinate lies in the candidate support. It deliberately does not call the
candidate a timer, score, life counter, objective, or noise.

A candidate can create a prospective prediction for the next rewrite. Only a later transition
with the predicted rewrite and amount supports construction of a versioned `MaskLaw`. The mask
contains the observed support from the witnesses and demonstration. Applying it returns a derived
grid with sentinels; it never mutates the raw grid.

## What this proves

This slice proves that Ring 9 can:

1. close click-only G1 at the moment its actual question is answered;
2. detect a recurrent remote rewrite without assigning semantic purpose;
3. reject a same-site effect, a directly targeted effect, a flat step, a reversal, or a geometry
   change as counter evidence;
4. freeze a prospective rate prediction before the confirming transition;
5. construct a reversible mask only after that confirmation.

## G2 controller integration

The same target router now opens `G2-COUNTER` immediately after G1. G2 owns a bounded, deterministic
sequence of varied interventions. It stops as soon as the evidence kernel finds a recurrent remote
rewrite and requires Duck to provide:

- the visible quantity being tracked;
- the frame-to-frame mechanism;
- why recurrence away from varied acted sites supports a bookkeeping interpretation;
- exact witness evidence references;
- a competing model and falsifier;
- conditions and limitations.

Submitting prose does not close the gate. The controller freezes the candidate's observed rewrite
and rate, admits one unused intervention, and compares the later lossless transition. Support emits
a `CounterModel+MaskLaw` product; contradiction discards the answer and returns G2 to its probe
hunt without a mask. Gate answers now preserve the candidate and prospective prediction in the
run artifacts.

The counter representation now treats a bar as a coupled two-object process. Pixel arithmetic
records an exact `source integer -> replacement integer` exchange: source mass decreases by the
same amount that replacement mass increases. Using the total site ledger, the verifier follows the
connected pair of integer classes along the observed rewrite axis and requires the inferred
footprint to remain stable across witnesses. A horizontal or vertical bar can therefore be masked
in full before every cell has individually changed. When the total site ledger is unavailable, the
system falls back loudly to observed rewrite support rather than guessing the unseen extent.

The next hardening requirement is lifetime monitoring: after G2 closes, later transitions must
reopen it if the full bar holds unexpectedly, reverses, becomes directly targeted, changes its
exchange arithmetic, or becomes causally entangled with the world.

## Counter boundary lock

Rate recurrence no longer closes G2. A supported prospective rate demonstration creates a
provisional mask and moves the controller to `BOUNDARY_CONFIRMATION_REQUIRED`. G2 locks the
`CounterModel` only after observing the source integer at its footprint minimum and the
replacement integer at its footprint maximum together with one of these consequences:

- the environment reports game-over at the extremal frame; or
- an extremal bar resets from low source/high replacement to higher source/lower replacement,
  establishing a respawn cycle.

The locked product records the boundary evidence reference and whether the observed consequence
was `GAME_OVER_AT_SOURCE_MIN_REPLACEMENT_MAX` or
`RESPAWN_AFTER_SOURCE_MIN_REPLACEMENT_MAX`. Reaching the extrema without either consequence keeps
G2 open.

## HUD delta, world delta, and state identity

The locked mask now feeds a retroactive state archive ported from the Golden solver's quotient
model and V4's canonical delta partition. Every raw grid remains stored. For each transition the
archive derives disjoint `hud_cells` and `world_cells`, with the enforced invariant
`raw_cells = hud_cells union world_cells`. State addresses replace the full counter footprint with
an out-of-domain sentinel before hashing.

Consequently, two frames that differ only in the counter receive different raw addresses but the
same world address. Any change outside the mask survives in world delta and produces a distinct
world address. When G2 locks, all lossless G2 transitions with total site coverage are replayed
into this archive, so masking applies retroactively rather than beginning only at the lock step.

A locked-counter monitor is also available for subsequent gates. It accepts the established
source-to-replacement tick while reporting simultaneous outside-mask changes as world delta. It
requests G2 reopening when the counter is directly targeted, unexpectedly holds, changes rate,
or exhibits a different within-mask rewrite that may indicate causal entanglement. A verified
full-bar respawn remains valid.

## Exit criteria

- G1 click-only interface exit is covered by the full Ring 9 test suite.
- G2 evidence-kernel tests cover positive recurrence, negative controls, prospective timing,
  exact-rate contradiction, and raw-grid preservation.
- G2 routing tests cover the full candidate/explanation/demonstration/product path and a
  contradiction returning to active probing without a mask.
- No Kaggle package is built from this intermediate slice.
