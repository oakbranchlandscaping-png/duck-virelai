"""The one strict canonical JSON of the semantic library (WO-G4-DOSSIER-A, Sol's ruling R10).

Author: Claude (Alpha build seat), 2026-10-16. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` §7.

``json.dumps`` silently turns a ``1``, ``2.5``, ``True`` or ``None`` mapping key into a string, so two different values
could share one serialization and one hash. Here every mapping key must be a string at every depth, every number
finite, and every value a JSON primitive, a list (a tuple is a list) or a mapping. A refusal names its JSON path.

For every value that passes, the bytes are exactly ``json.dumps(sort_keys=True, separators=(",", ":"),
ensure_ascii=True, allow_nan=False)``: valid payloads keep their serialization and their hashes. Shared by
``answer_shapes``, ``product_content``, the lever-dossier compiler and validator, and the schema-v6 model seal.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

ALGORITHM, ENCODING = "sha256", "virelai-canonical-json-v1"


class StrictJsonError(ValueError):
    """A value that strict canonical JSON refuses, with the JSON path where it was found."""

    def __init__(self, detail: str, path: str) -> None:
        super().__init__(f"{detail} at {path}")
        self.detail, self.path = detail, path


def check(value: Any, path: str = "$") -> None:
    """Refuse non-string keys, non-finite numbers and non-JSON values, recursively."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise StrictJsonError(f"non-string mapping key {key!r}", path)
            check(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            check(item, f"{path}[{index}]")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise StrictJsonError(f"non-finite number {value!r}", path)
    elif not (value is None or isinstance(value, (str, int, bool))):
        raise StrictJsonError(f"{type(value).__name__} is not a JSON value", path)


def canonical_json(value: Any) -> str:
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def sha16(value: Any) -> str:
    return sha256(value)[:16]


def digest_record(value: Any) -> dict[str, str]:
    return {"algorithm": ALGORITHM, "encoding": ENCODING, "value": sha256(value)}


__all__ = ["ALGORITHM", "ENCODING", "StrictJsonError", "canonical_json", "check", "digest_record", "sha16", "sha256"]
