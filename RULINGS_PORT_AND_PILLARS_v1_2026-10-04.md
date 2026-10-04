# Rulings: the port plan and the two pillars (v1, 2026-10-04)

**Type:** `RULINGS_PORT_AND_PILLARS` · **v1** · **2026-10-04**
**Status:** **RULED by the Director, 2026-10-04 07:03.** These bind every seat working in this repo: the Ring 9 build seat (Claude), the NAV seat (Sol), and anyone who picks up the work.
**Recorded by:** Claude (Alpha build seat), signed.
**Rules on:**
- `PORT_PLAN_PUBLIC_NOTEBOOKS_v2_2026-10-04` §8 and §9.7 (R-1 to R-8);
- `PILLARS_PORT_AND_LEARN_TO_WIN_v1_2026-10-04`.

**Versioning:** highest version wins. A change is a new version with a dated reason, never an edit in place.

| # | Question | Ruling (Director's words, then what it means in practice) |
|---|---|---|
| **R-5** | Go | **"yes."** The two read-only steps start now: (1) tokens and images per Duck turn, from the v6 record; (2) shared state under concurrent games. No GPU, no code change. |
| **R-2** | Games the gates cannot finish inside their time slice | **"B, use what data we have and keep playing."** When the ladder rests, Duck plays on freely for the rest of the slice. It carries what the gates already certified, and the gates keep recording. Each game is receipted GATED or FREE_PLAY. Paper and prereg claims cite gated evidence only. |
| **R-1** | Who presses the buttons during guided gates | **"as recommended."** One action at a time, each admitted by the gate, inside guided gates. Batched action scripts (Franzen's style, under the waste guards) only in free play. |
| **R-8** | Wasted repeat actions | **"block and label why it is being blocked to avoid confusion."** A known no-op is refused, and the refusal is labelled as coming **from the harness, not the game**, with its reason and evidence. For example: "Blocked by the harness: this action changed nothing on this board at t41 and t44." Scott Le Grand's report that unlabelled refusals made the model mistake the harness for the game is the risk this label answers. Whether the label is enough is graded at the first canary that exercises the guard. |
| **R-3** | Branch | **"Click branch, we are planning to merge soon."** Ports land on `r9-r20-level-entry`. The merge with `main` (the NAV line) comes soon. Ports touching the shared files (`tool_agent.py`, `solver.py`) are announced in the documentation index before landing. |
| **R-4** | `su15` in the prereg held-out set | **"keep it, we are fine."** `su15` stays. The exposure is recorded, as the lab's honesty rule requires: on 2026-10-04 the build seat read a one-line mechanic description of `su15` in Franzen's `WRITEUP.md` §5. The next prereg version carries this as a declared exposure, and any `su15` result in the paper cites it. |
| **R-6** | How the learn-to-win checker is built | **"build as you suggest."** The referee is built from Tycho `wmlib_template.py` (outcome verifier `:1071-1375`, transition verifier `:434-892`) and JustAdev742's claim check (`dsl.py:245-289, 905-968`), with our G2 counter mask as Tycho's UNKNOWN mask. It runs in code, with zero model calls. |
| **R-7** | Acting on a learned goal | **"name it as a dedicated project."** A named project, `ACT_ON_GOAL`, opened after learn-to-win passes its level-3 live test (LW-4). It starts with golden's Push machine (ours), then JustAdev742's code-fitted rules and simulator, Tycho's planners, and the one-action predict-act-compare check. |

**Not ruled today; governed by existing law.** Whether the first scored submission waits for learn-to-win: `DIRECTIVE_COMPETITION_ENDGAME_v2` D-4 already places the first submission (~12 October) before the learn-to-win canary. The submission does not wait.

— Claude, Alpha build seat, 2026-10-04. Ruled by the Director, 2026-10-04.
