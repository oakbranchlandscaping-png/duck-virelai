"""ADAPTER — the only file in this tree that knows the platform exists.

Drives the `arc_agi` SDK directly (`Arcade.make` → `env.reset()` → `env.step(action, data)`),
so nothing outside this tree changes and the harness repo holding frozen v4 is untouched
(D-1; the Director's choice of 2026-09-06). Writes the golden record: a `*.golden.jsonl` whose
node 0 is the reset frame and whose every later line carries the action that produced it —
the corpus everything above Rung 0 needs (G0-02 finding 1; F-0002 closed).

Transcription origin (R-C): ARC-AGI-3-Agents/agents/agent.py:75-95 `Agent.main` (the loop),
:123-127 `append_frame`, :129-146 `do_action_request` / `_convert_raw_frame_data`; agents/
swarm.py:64-79 (scorecard → make → play → close). What it proved: every v4 run since 2026-04.
Changed from origin (labeled): the initial observation is RECORDED (agent.py hands it to
`choose_action` and drops it); the action is recorded beside the frame it produced; no
`FrameData(levels_completed=0)` phantom root; no wall-clock RNG (`virelai.py:239-241` seeded
from `time.time()` — the defect that made the two golden runs diverge).

The environment seed is the SDK's own `make(seed=…)`; the policy seed is this file's. Both
are written in the header so a play can be reproduced from the record alone.

Policies (G1-04): the default is `captain.opening.Opening` — canon 03 §5's generative opening,
which stops the play when its enumeration is exhausted (OPENING_COMPLETE) because at Rung 1 the
captain has no further lawful question. CYCLE-v0 stays selectable (`policy="cycle"`) as the
labeled scaffold that produced the Rung 0/1 corpora. Neither consumes randomness; `seed` is
reserved for later policies. Nothing here reads the board except to enumerate frame-0 sites.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from virelai_golden.substrate.grid import settled
from virelai_golden.substrate.load import golden_given
from virelai_golden.substrate.scan import scan_grid

POLICIES = {"opening": "OPENING (canon 03 §5: every button twice, every frame-0 site once)",
            "sweep": "SWEEP (G3-03: the opening, then every present worldline once, until enumeration complete)",
            "cycle": "CYCLE-v0 (scaffold; kept for corpus generation only)"}
CLICK = 6
RESET = 0
NOT_FINISHED = "NOT_FINISHED"
GAME_OVER = "GAME_OVER"
WIN = "WIN"


@dataclass
class PlayLimits:
    max_lives: int = 2       # deaths before stopping; a WIN stops sooner
    max_actions: int = 400   # hard stop so an unwinnable world cannot run forever


def _state_str(state: Any) -> str:
    return str(getattr(state, "value", None) or getattr(state, "name", None) or state)


def _frame_dict(raw: Any, action: Optional[Tuple[int, Optional[Tuple[int, int]]]]) -> Dict[str, Any]:
    """One record line from a FrameDataRaw-like object. Every layer, every cell, as ints."""
    return {
        "game_id": str(getattr(raw, "game_id", "") or ""),
        "frame": [[[int(c) for c in row] for row in layer] for layer in getattr(raw, "frame", [])],
        "state": _state_str(getattr(raw, "state", "")),
        "levels_completed": int(getattr(raw, "levels_completed", 0) or 0),
        "win_levels": int(getattr(raw, "win_levels", 0) or 0),
        "available_actions": [int(a) for a in (getattr(raw, "available_actions", ()) or ())],
        "full_reset": bool(getattr(raw, "full_reset", False)),
        "action": None if action is None else [action[0], None if action[1] is None else list(action[1])],
    }


class CyclePolicy:
    """CYCLE-v0. `next(available, frame0_layers)` → (action id, (row, col) | None)."""

    def __init__(self) -> None:
        self._i = 0
        self._targets: List[Tuple[int, int]] = []
        self._t = 0

    def next(self, available: List[int], frame0_layers: Any, givens: Any = None) -> Tuple[int, Optional[Tuple[int, int]]]:
        buttons = [a for a in available if a != RESET] or [a for a in available]
        if not buttons:
            raise RuntimeError("the platform offered no action — nothing to press")
        a = buttons[self._i % len(buttons)]
        self._i += 1
        if a != CLICK:
            return a, None
        if not self._targets:
            self._targets = [r.anchor for r in scan_grid(settled(frame0_layers))]
        cell = self._targets[self._t % len(self._targets)]
        self._t += 1
        return a, cell


def _step(env: Any, game_id: str, action: Tuple[int, Optional[Tuple[int, int]]]) -> Any:
    from arcengine import GameAction

    ga = GameAction.from_id(action[0])
    data: Dict[str, Any] = {"game_id": game_id}
    if action[1] is not None:
        data["y"], data["x"] = int(action[1][0]), int(action[1][1])  # (row, col) → platform (y, x)
    ga.set_data(data)
    raw = env.step(ga, data=data, reasoning={})
    if raw is None:
        raise RuntimeError("the environment returned no frame — terminal without a state")
    return raw


def make_policy(name: str) -> Any:
    if name == "opening":
        from virelai_golden.captain.opening import Opening
        return Opening()
    if name == "sweep":
        from virelai_golden.captain.sweep_click import Sweep
        return Sweep()
    if name == "cycle":
        return CyclePolicy()
    raise ValueError(f"unknown policy {name!r}; one of {sorted(POLICIES)}")


def play_env(env: Any, game_id: str, out_path: str, *, seed: int, env_seed: int,
             limits: PlayLimits = PlayLimits(), log=print, policy: str = "opening") -> int:
    """Play one environment to the limits, writing the golden record. Returns the node count.
    `env` is anything with `reset()` and `step(action, data=, reasoning=)` (the SDK wrapper, or a
    fake in tests)."""
    rng = random.Random(seed)  # reserved; CYCLE-v0 draws nothing from it
    del rng
    pol = make_policy(policy)
    raw = env.reset()
    if raw is None:
        raise RuntimeError("reset returned no frame")
    header = {"golden": {"game_id": game_id, "seed": seed, "env_seed": env_seed, "policy": POLICIES[policy],
                         "guid": getattr(raw, "guid", None), "max_lives": limits.max_lives,
                         "max_actions": limits.max_actions}}
    frame0 = getattr(raw, "frame", [])
    deaths = 0
    nodes = 0
    guid = str(getattr(raw, "guid", None) or "")
    givens: List[Any] = []   # the record so far, as the loader would read it — handed to the policy (R-H)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(header, separators=(",", ":")) + "\n")
        line = _frame_dict(raw, None)
        fh.write(json.dumps(line, separators=(",", ":")) + "\n")
        givens.append(golden_given(line, guid))
        nodes = 1
        presses = 0
        while presses < limits.max_actions:
            state = _state_str(raw.state)
            if state == WIN:
                log(f"golden play · WIN at node {nodes - 1}")
                break
            if state == GAME_OVER:
                deaths += 1
                if deaths >= limits.max_lives:
                    log(f"golden play · life {deaths} ended at node {nodes - 1}; max_lives reached")
                    break
                action: Tuple[int, Optional[Tuple[int, int]]] = (RESET, None)
            else:
                nxt = pol.next(list(raw.available_actions), frame0, givens)
                if nxt is None:
                    log(f"golden play · {getattr(pol, 'complete_reason', 'policy exhausted')} at node {nodes - 1}")
                    break
                action = nxt
                note = getattr(pol, "note", None)
                if note is not None:
                    log(f"golden play · node {nodes - 1} · {note(action)}")
            raw = _step(env, game_id, action)
            presses += 1
            line = _frame_dict(raw, action)
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
            givens.append(golden_given(line, guid))
            nodes += 1
    return nodes


def play(game_id: str, *, seed: int = 0, env_seed: int = 0, out_dir: str = "recordings",
         limits: PlayLimits = PlayLimits(), tags: Optional[List[str]] = None, log=print,
         policy: str = "opening") -> str:
    """Open a scorecard, make the environment, play, close. Returns the record path.
    Configuration (API key, operation mode, environments dir) is the SDK's own, from the
    environment / `.env` in the working directory — exactly as the harness reads it."""
    from arc_agi import Arcade

    arc = Arcade()
    card = arc.open_scorecard(tags=["golden", policy] + list(tags or []))
    env = arc.make(game_id, seed=env_seed, scorecard_id=card)
    if env is None:
        raise RuntimeError(f"arc.make({game_id!r}) returned no environment — check the game id, "
                           f"OPERATION_MODE and ARC_API_KEY")
    full_id = getattr(getattr(env, "info", None), "game_id", None) or game_id
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{full_id}.{policy}.seed{seed}-{env_seed}.golden.jsonl")
    try:
        nodes = play_env(env, full_id, out_path, seed=seed, env_seed=env_seed, limits=limits, log=log,
                         policy=policy)
    finally:
        try:
            arc.close_scorecard(card)
        except Exception as exc:  # the record is on disk; the scorecard is the platform's
            log(f"golden play · close_scorecard failed: {exc!r}")
    log(f"golden play · {nodes} nodes → {out_path}")
    return out_path
