"""Point a Ring 9 Kaggle package at the wheelhouse and model it should use (self-hosted or not).

Author: Claude (Alpha build seat), 2026-10-01. Director rulings 2026-10-01: depend on no one;
prepare to run the most capable model Kaggle allows.

The model and the vLLM wheelhouse reach the notebook in two places, and both must agree:
  - the kernel's ``dataset_sources`` (what Kaggle mounts);
  - the solver's setup command in ``setup_commands.json`` (where it looks, what it serves, and how:
    owner and slug of each dataset, the served model name, the context length, the install stamp,
    and vLLM's tool-call and reasoning parsers).

``retarget`` rewrites both from one ``Dependencies`` record. Every edit must match exactly once, so
a setup command of a different shape is refused rather than half-edited. A packager calls it and
records the record in the checkpoint and receipt; a model swap is then one reviewed record, not a
scattered edit.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Dependencies:
    wheelhouse: str  # OWNER/SLUG of the wheelhouse dataset
    model: str  # OWNER/SLUG of the model dataset
    served_model_name: str
    max_model_len: int = 65536
    stamp: str = "vllm==0.19.0 torch==2.10.0 flashinfer==0.6.6\n"
    tool_call_parser: str = "qwen3_coder"
    reasoning_parser: str = "qwen3"
    chat_template_kwargs: str = '{"preserve_thinking": true}'

    def record(self) -> dict[str, Any]:
        return asdict(self)


# What every Ring 9 package so far used (driessmit1's datasets, unreadable since 2026-10-01).
THIRD_PARTY_V3 = Dependencies(
    wheelhouse="driessmit1/arc3-vllm-h100-wheelhouse-v3",
    model="driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot",
    served_model_name="vrfai/Qwen3.6-27B-FP8",
)
# The same wheelhouse rebuilt byte for byte and the same model, under the Director's account.
SELF_HOSTED_V3 = Dependencies(
    wheelhouse="stephenkaskin/virelai-vllm-wheelhouse-v3",
    model="stephenkaskin/virelai-qwen3-6-27b-fp8",
    served_model_name="vrfai/Qwen3.6-27B-FP8",
)


def _sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    found = re.findall(pattern, text, flags=re.M)
    if len(found) != 1:
        raise ValueError(f"setup command: expected exactly one {label}, found {len(found)}")
    return re.sub(pattern, lambda _match: replacement, text, count=1, flags=re.M)


def retarget_setup(command: str, deps: Dependencies) -> str:
    wheel_owner, wheel_slug = deps.wheelhouse.split("/")
    model_owner, model_slug = deps.model.split("/")
    edits = {
        "wheelhouse owner": (r"^WHEELHOUSE_OWNER = '[^']*'$", f"WHEELHOUSE_OWNER = {wheel_owner!r}"),
        "wheelhouse slug": (r"^WHEELHOUSE_SLUG = '[^']*'$", f"WHEELHOUSE_SLUG = {wheel_slug!r}"),
        "model owner": (r"^MODEL_OWNER = '[^']*'$", f"MODEL_OWNER = {model_owner!r}"),
        "model slug": (r"^MODEL_SLUG = '[^']*'$", f"MODEL_SLUG = {model_slug!r}"),
        "served model name": (r"^SERVED_MODEL_NAME = '[^']*'$", f"SERVED_MODEL_NAME = {deps.served_model_name!r}"),
        "max model length": (r"^VLLM_MAX_MODEL_LEN = \d+$", f"VLLM_MAX_MODEL_LEN = {int(deps.max_model_len)}"),
        "analyzer context": (r"^ANALYZER_CONTEXT_WINDOW = \d+$", f"ANALYZER_CONTEXT_WINDOW = {int(deps.max_model_len)}"),
        "install stamp": (r"^STAMP_TEXT = '[^']*'$", f"STAMP_TEXT = {deps.stamp!r}"),
        "tool-call parser": (r"('--tool-call-parser',\n\s*)'[^']*'", None),
        "reasoning parser": (r"('--reasoning-parser',\n\s*)'[^']*'", None),
        "chat template kwargs": (r"('--default-chat-template-kwargs',\n\s*)'[^']*'", None),
    }
    values = {"tool-call parser": deps.tool_call_parser, "reasoning parser": deps.reasoning_parser,
              "chat template kwargs": deps.chat_template_kwargs}
    for label, (pattern, replacement) in edits.items():
        if replacement is None:
            match = re.findall(pattern, command, flags=re.M)
            if len(match) != 1:
                raise ValueError(f"setup command: expected exactly one {label}, found {len(match)}")
            command = re.sub(pattern, lambda m, v=values[label]: m.group(1) + repr(v), command, count=1, flags=re.M)
        else:
            command = _sub_once(command, pattern, replacement, label)
    return command


def retarget(setup_commands: list[str], kernel_metadata: dict[str, Any], old: Dependencies,
             new: Dependencies) -> tuple[list[str], dict[str, Any]]:
    """Both places at once. The kernel must currently mount exactly ``old``'s two datasets."""
    if len(setup_commands) != 1:
        raise ValueError("expected exactly one setup command")
    sources = list(kernel_metadata["dataset_sources"])
    for ref in (old.wheelhouse, old.model):
        if sources.count(ref) != 1:
            raise ValueError(f"kernel does not mount {ref} exactly once")
    sources = [new.wheelhouse if ref == old.wheelhouse else new.model if ref == old.model else ref for ref in sources]
    return [retarget_setup(setup_commands[0], new)], {**kernel_metadata, "dataset_sources": sources}


def describe(deps: Dependencies) -> str:
    return json.dumps(deps.record(), sort_keys=True)


__all__ = ["Dependencies", "SELF_HOSTED_V3", "THIRD_PARTY_V3", "describe", "retarget", "retarget_setup"]
