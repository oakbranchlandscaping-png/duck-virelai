# Ring 9 carry, vc33 v1: upload status

**Prepared:** 2026-10-01
**Author:** Claude (Alpha build seat), signed. The Director runs the upload commands.
**Status:** packaged and verified; not yet uploaded.

**Revisions carried:** R9-R06 to R9-R18. New since `ring9-g4-exit-v1`:
- R9-R15: replay fidelity, and actor provenance;
- R9-R16: the life record;
- R9-R17: the level freeze;
- R9-R18: G9-A carry.

**Rulings applied (Director, 2026-10-01):**
- carry hypotheses only;
- the win is recorded only;
- `tools/live_level_carry_gate.py` is left out of the shipped source;
- vc33 is packaged alone (the recommended option; you asked only for the export).

## Identifiers

| Item | Value |
|---|---|
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v1` (to be created, private) |
| Notebook | `stephenkaskin/taaf-virelai-ring9-carry-vc33-v1` (private). Accelerator `NvidiaRtxPro6000`; internet off. |
| Package | `kaggle/ring9-carry-vc33-v1/`, delivered as `ring9-carry-vc33-v1.tar.gz`. SHA-256 `c776e5e68decc15670ce326ed59aa8ff36aca0575a939f119175a0457eefc627`. |
| Packager | `tools/package_ring9_carry_vc33.py` |
| Source commit | `fbbc7f4a9f1decc669d2aa599dc37903a4431e90` (R9-R18) |
| Source export | `src_fbbc7f4.tar.gz`, SHA-256 `c95d742e…72d19b324`. It is identical to the cloud tree that was tested. |
| Package manifest SHA-256 | `f60e60d02cc689a010defd76bb52eff8e4652cc17ed3fb5594829e50c81045d1` |
| Source manifest SHA-256 | `eedbf8827953bad3146f4c527e0893b0b675b8eea0735ab86e20706eb16a2b05` |
| Base | The committed `ring9-g4-exit-v1` package (`10b1310`, manifest `80fac5e2…2b38`). The packager checks this base before it builds. |
| Model | `vrfai/Qwen3.6-27B-FP8` via local vLLM. Context 65,536 tokens; tool output 1,024 tokens. |
| World and budget | `vc33-5430563c`; one pass; 200 environment actions and 10,800 s of behaviour time |

## The question

When vc33's level 1 ends, does the machine do these three things?
1. Freeze what it established about level 1.
2. Restart its ladder on level 2's board.
3. Test what it carried on level 2, without carrying any verdict.

In the exit run, level 1 was won at transition 26 by the G4-A study of E0005, and the run stopped there.

## Preregistered criteria

These are frozen in `checkpoint-preflight.json` and `RUN.md`, and graded from artifacts.

- **M5-1 and M5-2, on each level:**
  - every card within the slot budget;
  - G0 to G4.1 with zero model calls;
  - Duck's first turn is the orientation, accepted within 2 turns.
- **G2 and G3:**
  - level 1 as in the exit run;
  - level 2 certifies its own counter and mask again, and witnesses its own levers.
- **A:** as before.
- **X-1 (level freeze):**
  - LevelModel(1) is frozen at the transition that ends level 1, from the gate machine's own record, with the win record;
  - the run does not stop; the ladder restarts at G0 on level 2;
  - every later row is tagged level 2.
- **X-2 (carry):**
  - every candidate is frozen at level-2 entry, before any level-2 click;
  - each is graded only by a level-2 click made after level 2's mask exists, and never on a terminal transition;
  - grades re-derive from the frames.
  - Reported: candidates, RECONFIRMED, FALSIFIED, UNCONFIRMED and not found.
- **X-3 (no verdict carried):** no level-2 product exists before level 2's own gate certifies it. G3 certifies level-2 levers on level-2 evidence.
- **L-1 (life record):**
  - each death is a RESET row that opens the next life;
  - a G4-B or G4-C prediction taken on a death or a level change is INDETERMINATE.
- **B and C:** as in the exit run, if reached.
- **E:**
  - the run ends by a planned stop or by its action or time budget;
  - it never crashes;
  - no model request comes after a planned stop.
- **N-1:** no gate idles without a legal move.
- **I0 (new):** the shipped source holds no `tools/live_level_carry_gate.py`, and no world name in the solver's executable code other than the harness's public game roster.
- **I1 to I4:** as before.
- **R (reported, not graded):**
  - actions and Duck time per level;
  - level-2 levers versus level 1;
  - the carry line Duck saw;
  - whether level 2 was won, and by whom;
  - the level-1 win record, verbatim.

  **A level won by the G4-A study is the study's, not the model's.**

**Offline reference (not a graded prediction):** on the live level-1 record, level 1 freezes at transition 26:
- E0004 is explained (ABSORBING) and E0005 is interrupted;
- the same click failed 7 times before the win.

Level 2's spawn board then gives **4 carry candidates** of level 1's lever type, all UNCONFIRMED at entry. Level 2 has never been played.

## Verification before upload

**The packager's own checks passed:**
- every stage marker from R9-R06 to R9-R18;
- the secret guard;
- request preflight (T10): 33,158 tokens worst case, unchanged.

**World-content guard (I0)** passed on the package.

**Negative controls on a copy:**
- a world id added as a string in `carry.py` was refused, naming `carry.py:153`;
- the excluded tool, put back, was refused.

**`tools/verify_kaggle_package.py`:** 8/8 passed. The bundled source equals the `fbbc7f4` export, except the deliberately excluded tool (the verifier compares bundle files to the export).

**The notebook's real start-up cells ran in the nested, zip and direct mount layouts:**
- each verified the source manifest (217 files), the world allowlist `['vc33-5430563c']`, and the receipt;
- each printed `controller executor on`;
- each reported 200 actions and 10,800 s;
- the run deadline is `timedelta(seconds=10800)`.

The simulator used the scratch copy with a stand-in game, as for the exit package, because the benchmark pickle still holds only ft09. Kaggle builds vc33 from its environment files, as the exit run did.

**Tamper test:** I appended one line to `carry.py` in a copy. The verifier passed only 4/8, and the notebook stopped at "Source manifest verification failed".

**Tests at `fbbc7f4`:** cloud 509 passed, 1 skipped; Mac 510 passed.

## Risks stated before the run (hypotheses, not findings)

1. **Duck may change level 1's path.**
   - The controller is deterministic until Duck acts on its own turn, and Duck answers G4-A at different moments.
   - Level 1 should still end the same way, the G4-A study of E0005, unless Duck presses something itself.
2. **Level 2 is unknown.**
   - The carried type, a solid square of one integer reacting elsewhere, may be FALSIFIED. That would be a real finding about transfer, not a defect.
   - Some candidates may never be clicked by G3, and stay UNCONFIRMED.
3. **The budget.**
   - Level 1 took 26 actions.
   - Level 2 re-runs G0 to G2 (ft09's G2 alone took 57) and then sweeps in G3.
   - 200 actions may end the run inside level 2's G3 or G4. That is a legitimate budget stop, not a failure.
4. **One extra Duck turn at level entry:** the level change is a boundary wake.
5. **Level 2 may be won by accident too.** It would then freeze, and the ladder would start on level 3. The score can rise with no win-seeking, and the review must not credit that to the model.
6. **F4 is still open.** The preflight bounds one request, not one turn.

— Claude, Alpha build seat, 2026-10-01
