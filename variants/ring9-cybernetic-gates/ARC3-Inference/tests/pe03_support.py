"""WO-PE-03B/C/D test support: the three frozen canary models and their cached projections.

Author: Claude (Alpha build seat), 2026-10-25. Nothing here is production code.
"""
from __future__ import annotations

import copy
import functools
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures" / "pe03_canary"
MANIFEST = json.loads((FIXTURES / "MANIFEST.json").read_text())
WORLDS = tuple(sorted(MANIFEST["models"]))
VC33, KA59, G50T = "vc33-5430563c", "ka59-38d34dbb", "g50t-5849a774"


@functools.lru_cache(maxsize=None)
def _raw(world: str) -> bytes:
    data = gzip.decompress((FIXTURES / MANIFEST["models"][world]["file"]).read_bytes())
    assert hashlib.sha256(data).hexdigest() == MANIFEST["models"][world]["source_sha256"], world
    return data


def model(world: str) -> dict[str, Any]:
    """A fresh copy of the frozen sealed model (tests may mutate it)."""
    return json.loads(_raw(world))


@functools.lru_cache(maxsize=None)
def _packet(world: str) -> str:
    from inference.paper_evidence import projection

    return projection.evidence_bytes(projection.project(model(world))).decode("ascii")


def packet(world: str) -> dict[str, Any]:
    return json.loads(_packet(world))


def claims(world: str, **match: Any) -> list[dict[str, Any]]:
    return [item for item in packet(world)["claims"] if all(item.get(k) == v for k, v in match.items())]


def deep(value: Any) -> Any:
    return copy.deepcopy(value)




GOLDEN_VC33 = FIXTURES / "vc33-5430563c.sweep.golden.jsonl.gz"


def entry(anchor, bbox, cells, klass):
    return {"frame": "ENTRY", "class": klass, "anchor": list(anchor), "bbox": list(bbox), "cell_count": cells}


def obj(handle, anchor, bbox, cells, klass):
    return {"type": "OBJECT", "handle": handle, "geometry": entry(anchor, bbox, cells, klass)}


LEVER_A = obj("c9@24,60", (24, 60), (24, 60, 27, 63), 16, 9)
LEVER_B = obj("c9@32,60", (32, 60), (32, 60, 35, 63), 16, 9)
COUNTER_BAR = obj("c7@0,0", (0, 0), (0, 0, 0, 63), 64, 7)
NOWHERE = obj("c2@10,10", (10, 10), (10, 10, 11, 11), 4, 2)
SMALL = obj("c11@44,50", (44, 50), (44, 50, 49, 51), 12, 11)
AGENT = {"type": "AGENT", "handle": "agent", "geometry": None}
LEVEL1 = {"type": "LEVEL", "handle": "level-1", "geometry": None}


def item(subject, family, predicate, value, required=True, alternatives=None, level=1):
    return {"level": level, "required": required, "kind": "PROPOSITION", "family": family, "subject": deep(subject),
            "predicate": predicate, "object": deep(value), "scope": {}, "accepted_alternatives": alternatives or [],
            "basis": "synthetic test item: code testing only", "ambiguity": None}


def synthetic_key(items=None, levels=(1,)):
    """A SYNTHETIC_TEST key for vc33 written by the build seat for code tests only: refused for formal grading."""
    frames = {str(l["level"]): l["entry"]["board_sha256"] for l in model(VC33)["levels"]}
    return {"schema": "virelai-paper-key-v1", "game_id": VC33, "levels": list(levels),
            "construction": {"author": "Claude (build seat, synthetic)", "method": "SYNTHETIC_TEST",
                             "frozen_on": "2026-10-25", "commit": None, "blind_to_reports": False,
                             "entry_frames": {str(l): frames.get(str(l), "0" * 64) for l in levels}},
            "sources": [], "items": items if items is not None else default_items()}


def default_items():
    return [
        item(LEVER_A, "ROLE", "ROLE_IS", "LEVER"),
        item(LEVER_B, "ROLE", "ROLE_IS", "LEVER"),
        item(COUNTER_BAR, "ROLE", "ROLE_IS", "COUNTER"),
        item(COUNTER_BAR, "LAW", "COUNTER_REWRITE", "7->4"),
        item(COUNTER_BAR, "LAW", "COUNTER_TRIGGER", "EFFECTIVE_TRANSITIONS_ONLY",
             alternatives=[{"predicate": "COUNTER_TRIGGER", "object": "EVERY_TRANSITION"}]),
        item(AGENT, "LAW", "CONTROL_MODE", "POINTER"),
        item(LEVER_A, "LAW", "LEVER_CLASS", "CYCLE"),
        item(LEVER_B, "LAW", "EFFECT_LOCALITY", "LOCAL"),
        item(LEVEL1, "CONDITION", "WIN_CONDITION", "synthetic: the level clears when a stated arrangement holds"),
        item(NOWHERE, "ROLE", "ROLE_IS", "LEVER"),
        item(SMALL, "ROLE", "ROLE_IS", "LEVER", required=False),
    ]


__all__ = ["AGENT", "COUNTER_BAR", "G50T", "GOLDEN_VC33", "KA59", "LEVEL1", "LEVER_A", "LEVER_B", "NOWHERE", "SMALL",
           "VC33", "WORLDS", "claims", "deep", "default_items", "entry", "item", "model", "obj", "packet", "synthetic_key"]
