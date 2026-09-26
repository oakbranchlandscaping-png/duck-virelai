# prior-art/ — the mining shelf for the gate ladder

**Created 2026-09-20 · additive-only · read before chartering any gate's build slice.**

## What this folder is

One subfolder per gate. Each holds that gate's **prior-art packet**: the located, first-hand-read
prior art for the gate's question — golden, V4, V3.5, the Ring 8 experiments, and the project
knowledge base's mining returns and rulings — with, for every source, *where it is*, *what it
proved*, and *what its own record says not to carry*. Packets are produced one gate per session,
after the gate's goal has been discussed and ruled with the Director. `GATE_THESES` (highest
version in this folder) is the ruled goal statement each packet is mined against.

## How the build team uses it

1. **At gate charter time, the packet is the WO-00 head start, not its replacement.** Read the
   packet first; then re-verify every citation at the current anchor before binding to it —
   file:line citations are perishable (`RULING_COLLISION_ATTRIBUTION_v2`: "a ruling that carries
   one carries an expiry date"). A named file absent at HEAD is a finding to surface, never
   content to assume.
2. **PORT default, INVENT justified.** If the packet names proven machinery for a clause of your
   work order, the burden of proof is on building fresh. Port the smallest coherent unit, with
   its provenance and limitations in the module docstring, per the golden tree's R-C discipline.
3. **Port structure, re-derive epistemology.** The two-column judgement from the ego campaign:
   carry what the code *knows* (shapes, persistence, consumers); re-derive what it *believes*
   (population rules, confidences, thresholds, priors). Almost always: structure yes,
   epistemology no. No threshold constant rides in on a port.
4. **The NOT-carried lists are binding until re-ruled.** When a packet records that a source's
   own history retired something (an early-stop, a permanent filter, a class-keyed oracle), do
   not re-import it because it looks convenient. Those entries are paid-for lessons.
5. **Evidence classes hold here too.** Everything in a packet is a *builder report* about the
   archive until you re-read the source first-hand; treat packet claims as pointers, not ground
   truth. The committed repo outranks every packet.

## Layout

```
prior-art/
  README.md                          this file
  GATE_THESES_v1_2026-09-20.md       the ruled goal of every gate, outline form
  G3-levers/                         one folder per gate; each gains its packet
  G4-reactions/                      (PRIOR_ART_<gate>_vN_YYYY-MM-DD.md and any
  G5-forces/                          extracts) when its mining pass runs
  G6-inertness/
  G7-novelty/
  G8-observed-win/
  G9-transfer/
  G0-action-surface/                 sealed gates: packets record what the live
  G1-ego/                            build already ported, for regrade and paper use
  G2-counter/
```

Documents in this folder follow the lab's versioning discipline: `TYPE_NAME_vN_YYYY-MM-DD`,
highest version current, nothing edited, nothing deleted.
