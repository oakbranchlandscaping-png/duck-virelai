# THE RING 7 REVELATION — AND WHAT IT CHANGED
**Type:** REVELATION_RING7 · **Version:** v1 · **Date:** 2026-08-30
**Author:** Cowork (hybrid seat), ratified by the Director
**Audience:** build collaborators with repo access
**Anchors:** ring7 variant `f56bc27`, bundle `a20a4ff`; ring6.3 reference `f36c149`/`aee22f7`

## 1 · The revelation, in four numbers

The Ring 6.3 evaluation ended with one unanswered comparison: how does the
first successful handoff run stand against the ORIGINAL frozen baseline —
not against its own controls? Pulling the r0 dryrun summary answered it, and
the answer decomposed the whole campaign:

| arm | what it is | total score |
|---|---|---|
| **r0** | pristine Tufa Duck, untouched | **~30.5** (mean 1.22) |
| ring6.0 | ring 1–5 lineage host, NO probe | 6.33 |
| ring6.2 | probe runs, report NOT delivered | 4.55 |
| ring6.3 | probe runs, report DELIVERED | 13.97 |

Read bottom-up: the delivered card earned +9.4 over its no-delivery control —
the only component in the campaign that ever paid rent. The probe itself cost
only ~1.8 (6.33 → 4.55). **And the accumulated ring 1–5 layer — the deleted
discovery prose, the injected ledger/[MAP]/weave machinery, the reworked
strategy text — had already given back ~24 of baseline's 30.5 points before
the Captain ever arrived.** Every ring 6.x arm, including the celebrated 6.3,
was feeding our best instrument into a host our own earlier rings had
degraded to a fifth of stock.

The mechanism is concrete: ring 4's lockstep deletion removed Duck's native
exploration instructions on the bet that the card would replace them. Where
the starved probe delivered a thin card, Duck had neither its original
guidance nor a substitute. The card fought from 4.55 to 13.97 *inside that
hole* — impressive, and still 16 points below stock.

The permanent laws predicted this. "Every native invention that diverged from
proven prior art has failed expensively" — the ring 1–5 layer was exactly
such an invention, replacing Tufa's proven prompt with our own machinery, and
it was never charged for its cost because every ring was only ever measured
against its sibling rings, not against r0.

## 2 · The ruling

Director, 2026-08-30, in substance: **rings 1 through 5 are chalked up as a
learning experience. Return to the r0 Duck and feed in the Captain's probe,
now that the handshake protocol is proven.** Probe + card only; the ontology
is held out as a separate future arm (one variable).

## 3 · What Ring 7 is

The minimal hybrid. Seeded byte-for-byte from the executed r0 tree
(`kaggle/dryrun-r0/source-dataset/src/ARC3-Inference`, the tree that scored
30.5), plus exactly the machinery Ring 6.3 proved:

- the vendored `virelai_v4` Captain (unchanged) and its probe/report modules;
- the solver probe block (`_virelai_opening`, snapshots, action bridge),
  the full 6.3 audit chain (fingerprint, atomic persist, provider-payload
  observer, `RING6_*` markers, three artifact families), including the D1/D2
  amendments (observer silent with no report; honest fallback card);
- the tool_agent handshake (explicit-argument card insertion, yield-resume
  containment, request-id observer plumbing).

Deliberately absent: the ontology; the ring 1 ledger and [MAP] digest; ring 2
counter seal; ring 2.5 weave; `virelai`/`virelai_card()` runtime views; every
prompt edit. `prompts.py` and `python_tool_sandbox.py` are byte-identical to
r0 and a test pins that purity. Battery 37/37 (the ring 6.3 suite, with the
ontology test replaced by the purity contract). Kaggle run in flight under
label `duck-virelai-ring7` (kernel slug remains the reused ring6-share
address — the runtime label is the authority, per standing rule).

## 4 · What this changed about the build goal

**The bar moved.** The campaign's success criterion is no longer "beat the
previous ring" — a ladder that let 24 points of self-inflicted damage hide
for five rings. The bar is r0's 30.5, permanently. Every future arm is
charged against the best Duck we have, not the most recent one.

**Subtraction became a first-class move.** The biggest single score movement
in the program's history came from *removing* our own accumulated layer.
Additions must now prove they pay rent against the pristine host; deletions
of proven upstream competence carry the burden of proof, not the other way
around. This is the PORT-default law finally applied to ourselves: Tufa's
prompt was proven prior art, and we were the ones inventing natively.

**The lineage question is settled by experiment, not argument.** Ring 7's
result sorts into three decisive readings:
- **> 30.5:** the thesis is proven against the true bar — grounded evidence
  improves the best available player. The 6.4–6.7 ladder rebases onto ring 7.
- **14 – 30.5:** the card helps but does not yet cover its cost on the good
  host; the ladder's known remedies (probe throughput, win analysis, use
  contract, memory) apply, on the ring 7 base.
- **≤ 14:** host degradation was not the main story — the card's *content* is
  the bottleneck, and card/Captain quality jumps the queue.

**The 6.4–6.7 ladder survives, re-based.** Nothing in the Director's ladder
is invalidated — throughput, learn-to-win, the use contract, and persistent
memory all operate on the Captain/handshake side, which ring 7 carries
whole. What changed is the host they land on and the number they answer to.
Ring 6.3 remains the frozen handshake reference; the ring 6.x lineage becomes
archive and control data.

**What rings 1–5 still bought.** The tuition was not wasted: the handshake
protocol and its proof discipline; the Captain itself and the action bridge;
the field-card renderer and its language; the methodology scars (transcripts
over prompt logs, parse over grep, content over existence, markers as
completed facts); and the evaluation machinery that made this very
decomposition possible. Those all ride into ring 7. What died was the belief
that wrapping the model in our machinery is free.

## 5 · Standing cautions

All four arm totals are single stochastic passes — the decomposition's
*direction* is unambiguous (5×–7× gaps), but individual deltas carry noise.
ft09 remains the variance monster in every arm. And the ontology, now
cleanly excluded, is an untested variable on the ring 7 base — a cheap
future A/B once ring 7's own number is in.

*The committed repo outranks this document. Ring 7's run artifacts, when
pulled, outrank both.*
