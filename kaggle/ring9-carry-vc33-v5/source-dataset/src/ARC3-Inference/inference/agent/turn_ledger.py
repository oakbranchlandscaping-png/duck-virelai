"""The turn ledger: what each Duck turn cost and what it was shown (memory law M10).

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 §7, stage M-0).

One JSON row per analyzer turn, written beside the other run artifacts as
``{stem}_turn_ledger.jsonl``:

- who acted (``executor``: ``DUCK`` today; the controller executor adds ``CONTROLLER`` rows);
- the gate before and after the turn;
- the characters of every section of the model-visible user message (the card) and their sum;
- per model request: prompt tokens and generated tokens as the server reported them;
- wall seconds; recall queries Duck issued (by operation); whether an action executed.

The ledger only observes. It never alters a prompt, a request or a decision.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "virelai-turn-ledger-v1"


def _int(usage: Mapping[str, Any] | None, *keys: str) -> int | None:
    if not isinstance(usage, Mapping):
        return None
    for key in keys:
        try:
            return max(0, int(usage[key]))
        except (KeyError, TypeError, ValueError):
            continue
    return None


class TurnLedger:
    def __init__(
        self,
        path: Path,
        *,
        analysis_step: int | None,
        action_num: int,
        executor: str,
        gate_before: str | None,
        sections: Mapping[str, str],
    ) -> None:
        self.path = path
        self._started = time.monotonic()
        self._row: dict[str, Any] = {
            "schema": SCHEMA,
            "analysis_step": analysis_step,
            "action_num": int(action_num),
            "executor": executor,
            "gate_before": gate_before,
            "section_chars": {name: len(text or "") for name, text in sections.items()},
            "requests": [],
            "recall_queries": [],
        }
        self._row["card_chars"] = sum(self._row["section_chars"].values())

    def request(self, usage: Mapping[str, Any] | None) -> None:
        self._row["requests"].append({
            "prompt_tokens": _int(usage, "prompt_tokens", "input_tokens"),
            "generated_tokens": _int(usage, "completion_tokens", "output_tokens", "generated_tokens"),
        })

    def query(self, operation: str) -> None:
        self._row["recall_queries"].append(str(operation))

    def finish(self, *, gate_after: str | None, step_executed: bool, outcome: str) -> dict[str, Any]:
        requests = self._row["requests"]
        row = {
            **self._row,
            "gate_after": gate_after,
            "step_executed": bool(step_executed),
            "outcome": outcome,
            "wall_seconds": round(time.monotonic() - self._started, 3),
            "request_count": len(requests),
            "prompt_tokens_max": max(
                (item["prompt_tokens"] for item in requests if item["prompt_tokens"] is not None),
                default=None,
            ),
            "generated_tokens": sum(item["generated_tokens"] or 0 for item in requests),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        return row
