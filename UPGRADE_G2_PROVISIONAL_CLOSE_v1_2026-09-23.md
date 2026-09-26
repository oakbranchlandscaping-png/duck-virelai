# Future upgrade: G2 provisional close — the boundary becomes a watched obligation

**Type:** `UPGRADE_G2_PROVISIONAL_CLOSE` · **v1** · **2026-09-23**
**Status:** Director-ruled design, **NOT scheduled** — a touch upgrade for when the build reaches
it. It touches the decision substrate and the belief-write path, so when it lands it is
**canary-bound** (canary-before-closure applies) and gets its own work order.
**Origin:** Director ruling in discussion, 2026-09-23, motivated by direct run evidence: the
three-world served run ended vc33 stalled in `RATE_SUPPORTED_AWAITING_MIN_MAX_BOUNDARY`, and on
an embodied world the extremum sits a full life (~42 actions on the measured ls20 period) behind
a blocking wait, under a scoring law that squares action waste.

## The ruling, in one paragraph

Requiring the counter's min/max consequence *before* G2 closes is too expensive: it burns a life
per world as a prerequisite. G2 therefore closes once the agent's counter evidence is
structurally sufficient — recurrence across at least two varied interventions plus one supported
frozen rate prediction, exactly the criteria that already create the provisional mask — and the
min/max boundary **solidifies** the model later, when it is observed. The key fact making this
safe and free: the counter ticks on every action, so the extremum arrives on its own during
G3's ordinary work. The boundary observation was never expensive; only waiting for it was. The
obligation converts from a blocking probe requirement into a **standing passive obligation on
the locked-counter monitor**, which already watches every G3 transition.

## Behavior change, precisely

Current (as live-confirmed on ls20): `DEMONSTRATION_REQUIRED` → supported comparison →
`BOUNDARY_CONFIRMATION_REQUIRED` (blocking; counter-only presses or waiting) → extremum plus
game-over/respawn observed → `CounterModel` status `LOCKED_BY_EXTREMUM_BOUNDARY` → CLOSED.

Upgraded:

1. Supported prospective rate comparison → G2 **closes** with `CounterModel` status
   **`PROVISIONAL_RATE_CONFIRMED`**; the provisional mask (which this step already builds)
   activates; the masked state archive begins; the router advances to G3 immediately.
2. A **boundary obligation record** is journaled open: footprint, source/replacement integers,
   expected extremum, expected consequence alternatives (game-over at source-min/replacement-max,
   or respawn), unresolved.
3. The locked-counter monitor — unchanged in its verdicts — gains one promotion hook: on a later
   transition where the extremum and a consequence are observed, it marks the obligation
   fulfilled and promotes the model to **`LOCKED_BY_EXTREMUM_BOUNDARY`** (the Director's
   "solidified"), recording the consequence type for G4's conditional-reaction laws.
4. On a contradicting observation (bar holds at extremum with no consequence, reversal,
   direct targeting, changed arithmetic), the monitor **reopens G2** — the path that already
   exists — and every consumer of the mask is notified through the provisionality tag below.

No dedicated boundary probes exist anywhere in the upgraded flow. `COUNTER_EXTREMA_BOUNDARY_NOT_
OBSERVED_WITHIN_BUDGET` ceases to be a G2 stop reason; an unfulfilled obligation at level end is
recorded on the certificate as exactly that — unfulfilled, not failed.

## The two guards that travel with it (binding)

**Structural confidence, never a number.** "Confident in the counter" is cashed only as the
existing structural criteria (varied-intervention recurrence + one supported frozen prediction).
No threshold constant, no confidence score, no press-count minimum enters with this upgrade.

**Contagious provisionality until solidified.** While the model is `PROVISIONAL_RATE_CONFIRMED`:
every world address minted under the provisional mask, every G3 attribution whose residue
subtracted it, and every law citing either carries the provisional tag. If solidification ever
forces a mask revision (the one-sided-mask failure class), the retroactive re-address machinery
replays the record under the corrected mask and re-quotients — downstream claims inherit the
revision loudly, never silently. Solidification clears the tags in place.

## Why this is doctrine-consistent, not an erosion

The house pattern is provisional-with-monitor everywhere else: INERT is provisional always; G7
starts as outcome-sets and promotes on demonstrated Markov-sufficiency; identity abstains into
candidate links. The August hardening ("rate recurrence never locks") was right that rate-only
closure is not final truth; it overcorrected by making final truth a prerequisite for
*advancing*. This upgrade keeps both halves honest: nothing is called locked that is not, and
nothing waits that does not need to.

## Acceptance criteria when scheduled

- Supported rate comparison closes G2 provisional and the router opens G3 in the same trace;
  zero boundary-dedicated probes issued anywhere in the run.
- The obligation record is journaled open at close and fulfilled by the monitor on a natural
  later extremum, promoting the model, with the consequence type recorded.
- A contradicting extremum reopens G2 and the provisional tags propagate to every dependent
  address, attribution, and law (one planted-defect test: a mask revision re-addresses the
  archive and no stale address survives untagged).
- The G3 checkpoint certificate accepts `PROVISIONAL_RATE_CONFIRMED` as a valid mask basis and
  reports the obligation's state; an unfulfilled obligation is never a certificate failure.
- Canary: full-capture-graded live run on an embodied world, comparing actions-to-G3-entry
  against the current flow (expected saving on the measured ls20 period: roughly a full life).

## Files this will touch (verify at the WO's own anchor)

`counter_verification.py` (model status split), `virelai_gates.py` (G2 close path, router
advance, monitor promotion hook, stop-reason retirement), `masked_world_state.py` (provisional
tagging and re-quotient), `lever_attribution.py` (tag pass-through), `g3_checkpoint.py` and the
G2 evaluator (accept provisional basis; report obligation state), plus the theses at their next
version.

*Filed as the record of the ruling so it never becomes chamber memory. Not a work order; not
scheduled; supersedes nothing until its WO lands.*
