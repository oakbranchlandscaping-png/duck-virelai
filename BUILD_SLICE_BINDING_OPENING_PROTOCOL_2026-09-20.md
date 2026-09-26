# Build slice: binding opening protocol and ranked object frontier

**Date:** 2026-09-20  
**Active source:** `variants/ring9-cybernetic-gates/`  
**Status:** Click arm and Duck-piloted collision arm built and locally verified; live unconfirmed

## Governing protocol

The Captain protocol is now explicit in Duck's universal system prompt and controller state:

1. read the exact legal action metadata;
2. assign `CLICK_GOD_MODE`, `NAVIGATION`, or `HYBRID` from the action families;
3. in click worlds, accept the coordinate hand as the ego and click every visual object;
4. in navigation and hybrid worlds, complete the Delphi ego opening, then collide the embodied
   ego with every visual object;
5. use the same sweep to expose both counters and levers, while interpreting and masking the
   counter first because it contaminates causal attribution and state identity.

The prompt says that Duck must follow the controller's object order and must not reorder, skip, or
terminate the enumeration because it found one lever or observed several quiet objects.

## Port basis

This slice ports the strategy documented in `MINING_INDEX_PROBE_STRATEGY_v1_2026-09-20.md`:

- Golden `captain/opening.py`: action-roster branch and consecutive Delphi pairs;
- Golden `captain/sweep_click.py`: target an actual NW-most member cell and enumerate to
  completion;
- Golden `captain/nav_sweep.py`: collide-with-everything is the embodied twin of click-everything;
- V4/Golden ranking rulings: ranking orders experiments and never assigns a role.

The strict frame-zero visual order is:

```text
smallest cell footprint
-> lowest observed integer
-> nearest member anchor to (0,0)
-> row, column, stable member id
```

This is a total deterministic order. It is not evidence that a small, low-integer, or top-left
object is a lever, counter, ego, or goal.

## Implemented controller behavior

`AdaptiveCoordinateCoverage` now exposes one exhaustive `ranked_candidates()` roster shared by
the opening protocol. Its class representatives also follow the same ranking.

For `CLICK_GOD_MODE`, G2 now clicks every connected frame-zero component once in this order. The
previous policy sampled at most twelve class representatives and then added row-major cells. That
policy was neither exhaustive over objects nor suitable for handoff to G3, and has been removed.

G2 exposes the branch, ranking law, roster size, observed count, and current target in its gate
view. When the counter closes, the `CounterModel + MaskLaw` product also stores the complete ranked
frontier with each object marked `OBSERVED` or `UNTRIED`. G3 can therefore resume the same sweep
instead of reconstructing or restarting it.

Counter demonstration and boundary-confirmation repetitions now have a separate probe serial.
They no longer advance the ranked object frontier. This fixes the vc33 trace failure in which 45
repetitions at one coordinate would otherwise look like 45 distinct investigated objects.

## Navigation and hybrid arm

The controller now binds the next ranked object while Duck chooses one legal opaque embodied
action at a time from its demonstrated G1 motion model. Duck prospectively labels each action
`APPROACH` or `CONTACT_ATTEMPT`. Approach steps do not consume the object. A target advances only
after a direct target-footprint delta, an observed terminal boundary, a declared zero-delta contact,
or a 24-step bounded pilot failure. Every disposition and its evidence strength is retained in the
shared frontier.

G2 is rebuilt from the post-G1 frame. Its embodied roster excludes the demonstrated ego footprint
and structural background fields, so Duck is not assigned itself or the floor as a collision
target. The handoff records whether the footprint came from an exact demonstrated after-state or
from Duck's declared G1 scope fallback.

This implements the user-directed Duck-piloted arm. It does not yet reproduce Golden's
deterministic route planner or controller-derived contact line. A zero-delta refused-contact result
is therefore explicitly model-declared evidence, and pilot exhaustion is not an unreachability
proof. See `BUILD_SLICE_DUCK_PILOTED_COLLISION_SWEEP_2026-09-20.md`.

## Verification

- Complete Ring 9 suite: **276 passed**, with 14 dependency warnings.
- Targeted counter, ranking, bridge, and G1 suite: **31 passed**.
- Targeted Ruff checks passed.
- Tests prove exhaustive strict click ordering, prompt delivery, branch visibility, frontier
  persistence, and that confirmation detours do not consume object coverage.
- Navigation tests prove target binding, Duck-selected legal piloting, direct response recording,
  lower-strength declared refusal, and ego/background exclusion.

These are implementation checks. No Kaggle run has yet demonstrated that the served Duck follows
the new prompt or that the ranked click sweep improves discovery.

## Collision-arm exit criteria

The local collision-arm slice is complete because production-shaped contracts now show:

- G1 closes with an evidence-backed embodied ego and usable opaque movement laws;
- G2 selects the first untried object from the same strict roster;
- every movement is either a route step or a deliberate contact attempt toward that object;
- target response is attributed from before/action/after footprint evidence;
- Duck-declared zero-delta contact is recorded at its lower evidence strength;
- responding, refusing, reaching a boundary, or exhausting a target updates only that target;
- counter observations may interrupt the sweep without corrupting or reordering its frontier.

Live confirmation still requires a completed packaged run in an embodied world.
