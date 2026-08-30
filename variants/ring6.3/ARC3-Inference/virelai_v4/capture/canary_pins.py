"""WO_WEAVE_S1_PIN_AND_SEE · the canary pin manifest — pure data, no logic.

Kills the ``glob[0]`` ambiguity: the canary sessions are PINNED by name here, so
every dossier / grade names exactly which capture it ran on. The recordings
themselves are gitignored (``.gitignore`` ``recordings/``) — only these NAMES are
committed. ``resolve`` raises a clear, path-naming error when a pinned file is not
present locally, so a missing canary fails loud, never silently on ``glob[0]``.

Game names appear here (the pin manifest) and in fixtures ONLY — never in solver
or dossier logic, which stays statable-as-a-kind.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

# Each pin: the game key, its session hash, the exact recording path, the node
# count the pinned session round-trips PRISTINE to, and the default inspection
# window (inclusive route_position range) for the raw dossier.
CANARY_PINS: Dict[str, Dict] = {
    "vc33": {
        "hash": "5430563c",
        "session": "recordings/vc33-5430563c.virelai.1f7b305c-264c-435d-af5f-7475bc944c01.recording.jsonl",
        "nodes": 51,
        "window": (10, 16),
    },
    "ls20": {
        "hash": "9607627b",
        "session": "recordings/ls20-9607627b.virelai.889276ef-e036-416b-bb38-e5c91238396c.recording.jsonl",
        "nodes": 76,
        "window": (10, 16),
    },
}


def resolve(game: str) -> Dict:
    """Return the pin dict for ``game``. Raises ``KeyError`` for an unknown game
    and ``FileNotFoundError`` (naming the expected path) when the pinned session
    is not present locally — the loud failure that replaces ``glob[0]``."""
    if game not in CANARY_PINS:
        raise KeyError(
            f"no canary pin for game {game!r}; known pins: {sorted(CANARY_PINS)}"
        )
    pin = CANARY_PINS[game]
    if not os.path.isfile(pin["session"]):
        raise FileNotFoundError(
            f"canary session for {game!r} not found at {pin['session']!r} "
            f"(recordings are gitignored — the pinned file must exist locally)"
        )
    return pin


def session_basename(game: str) -> str:
    """The bare filename of a pinned session — the self-naming token a dossier
    header carries so an artifact always says which capture produced it."""
    return os.path.basename(CANARY_PINS[game]["session"])


def window_of(game: str) -> Tuple[int, int]:
    """The default (inclusive) route_position window for ``game``."""
    return tuple(CANARY_PINS[game]["window"])
