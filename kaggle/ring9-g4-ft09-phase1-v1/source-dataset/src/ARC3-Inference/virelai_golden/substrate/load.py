"""SUBSTRATE · load — a recording on disk → Record. Offline, deterministic, no game.

Two formats, one Record:
  `*.recording.jsonl`  the harness's — action-blind, first frame absent (F-0002, closed);
  `*.golden.jsonl`     G0-06's — line 1 a header, then one line per node from the reset frame
                       on, each carrying the action that produced it (`adapter.play`).

Transcription origin (R-C): virelai_v4/capture/ledger_build.py:155-199 `load_capture` @
oracle-v4 (read whole, 320 lines). What it proved: the jsonl's `data` carries every field the
live recorder reads; framed lines are wrapped and appended in order; lines without a frame are
skipped. Its docstring is the origin of the action-blindness finding (WO-A2-03 Part 2): the
placeholder `{"id": 0, "data": {}, "reasoning": None}` on every line.

Changed from origin (labeled):
  - skipped lines are COUNTED and reported, not dropped silently (typed silence, 01 §6);
  - the record is whole-game with segment flags (R-H) — v4 restarted its log at a level-up;
  - the action channel is a positive claim on the Record, `BLIND(n)` when every line carries
    the placeholder, never an edge of `(0, None)` that a reader could mistake for RESET.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from virelai_golden.substrate.record import Given, Record, build, freeze_layers

HARNESS_ORIGIN = ("HARNESS_LINE_0: the recorder's first line, not the game's initial frame "
                  "(F-0002); the reset frame is absent")
GOLDEN_ORIGIN = "RESET_FRAME: node 0 is the initial observation, written by golden.adapter"
PLACEHOLDER_ID = 0
GOLDEN_SUFFIX = ".golden.jsonl"


def _given(data: Dict[str, Any]) -> Given:
    return Given(
        layers=freeze_layers(data["frame"]),
        state=str(data.get("state", "")),
        levels_completed=int(data.get("levels_completed", 0) or 0),
        win_levels=int(data.get("win_levels", 0) or 0),
        available_actions=tuple(int(a) for a in (data.get("available_actions") or ())),
        full_reset=bool(data.get("full_reset", False)),
        guid=str(data.get("guid") or ""),
        game_id=str(data.get("game_id") or ""),
    )


def _action_channel(action_inputs: List[Any]) -> str:
    """BLIND(n) when all n lines carry the harness placeholder; otherwise LIVE(n) — a recording
    that carried real actions would be a new fact and gets a new label, not the old one."""
    blind = sum(1 for a in action_inputs
                if isinstance(a, dict) and a.get("id") == PLACEHOLDER_ID and not a.get("data"))
    n = len(action_inputs)
    return f"BLIND({n})" if blind == n else f"LIVE({n - blind} of {n})"


def read_lines(path: str) -> Tuple[List[Dict[str, Any]], int]:
    """`(framed data dicts in file order, skipped line count)`."""
    framed: List[Dict[str, Any]] = []
    skipped = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line).get("data")
            if not isinstance(data, dict) or not data.get("frame"):
                skipped += 1
                continue
            framed.append(data)
    return framed, skipped


def golden_given(line: Dict[str, Any], guid: str) -> Given:
    act = line.get("action")
    action = None if act is None else (int(act[0]), None if act[1] is None else (int(act[1][0]), int(act[1][1])))
    return Given(
        layers=freeze_layers(line["frame"]), state=str(line["state"]),
        levels_completed=int(line["levels_completed"]), win_levels=int(line["win_levels"]),
        available_actions=tuple(int(a) for a in line["available_actions"]),
        full_reset=bool(line.get("full_reset", False)), guid=guid, game_id=str(line["game_id"]),
        action=action,
    )


def load_golden(path: str) -> Tuple[Record, int]:
    """A `*.golden.jsonl`: header line, then nodes. Node 0 is the reset frame (action None)."""
    with open(path, encoding="utf-8") as fh:
        raw = [json.loads(line) for line in fh if line.strip()]
    if not raw or "golden" not in raw[0]:
        raise ValueError(f"{path}: not a golden record (no header line)")
    header = raw[0]["golden"]
    givens = [golden_given(line, str(header.get("guid") or "")) for line in raw[1:]]
    n = len(givens)
    seen = sum(1 for g in givens[1:] if g.action is not None)
    record = build(givens, origin=f"{GOLDEN_ORIGIN} · seed {header.get('seed')} · env seed "
                                  f"{header.get('env_seed')} · policy {header.get('policy')}",
                   action_channel=f"LIVE({seen} of {n - 1} presses)" if n > 1 else "LIVE(0)",
                   source=path)
    return record, 0


def load_recording(path: str) -> Tuple[Record, int]:
    """`(Record, skipped lines)` from either format. Raises on an empty recording."""
    if path.endswith(GOLDEN_SUFFIX):
        return load_golden(path)
    framed, skipped = read_lines(path)
    record = build(
        [_given(d) for d in framed],
        origin=HARNESS_ORIGIN,
        action_channel=_action_channel([d.get("action_input") for d in framed]),
        source=path,
    )
    return record, skipped
