"""WO-CC-S1 · CAPTURE — the lossless given record.

Node-grained, append-only, interpretation-free record of what the platform
hands the solver at each ``choose_action`` entry. It records the given and
derives nothing: no Region, Slot, object, role, delta, or weave.

Fences (WO-CC-S1 §3 — each a build-failure if broken):
  - Interpretation-free: imports only stdlib + ``state_tracker._norm_key``.
    Nothing from ``library/``, ``targeting/``, ``captain``, ``perception/``.
  - Lossless: records ALL layers of ``frame.frame`` (not ``frame[-1]``);
    ``reconstruct`` returns ``frame.frame`` byte-equal.
  - Append-only: no record is mutated after append; ``node_index`` is
    monotonic from 0.
  - Additive read-sidecar: reads ``latest_frame`` / ``frames`` / ``ctx``;
    writes only its own log. Never touches a belief write.

The inbound edge reuses the committed WO-R4 composite ``EdgeKey`` via the
imported ``state_tracker._norm_key`` — never reimplemented.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any, List, Optional, Tuple

from virelai_v4.cybernetic.state_tracker import _norm_key

# A deep-frozen 3D grid stack: layers -> rows -> cells. Mirrors the shape of
# arcengine FrameData.frame (list[list[list[int]]]) as immutable tuples.
Layers = Tuple[Tuple[Tuple[int, ...], ...], ...]
# The composite inbound edge: (action_id, target) or None at the root node.
Edge = Optional[Tuple[int, Any]]


def _freeze_layers(frame_layers: Any) -> Layers:
    """Deep-freeze a 3D grid stack to nested tuples of ints. Lossless."""
    return tuple(
        tuple(tuple(int(cell) for cell in row) for row in layer)
        for layer in (frame_layers or [])
    )


def _thaw_layers(layers: Layers) -> List[List[List[int]]]:
    """Rebuild ``frame.frame`` as nested lists — the round-trip inverse."""
    return [[[int(cell) for cell in row] for row in layer] for layer in layers]


def _hash_layers(layers: Layers) -> str:
    """SHA-256 over the FULL layered payload (all layers), computed in-module.

    Distinct from ``virelai._hash_grid``, which hashes only the derived
    last-layer grid; this must cover the whole given.
    """
    digest = hashlib.sha256()
    digest.update(repr(layers).encode("utf-8"))
    return digest.hexdigest()


def _state_str(state: Any) -> str:
    """Store the frame state as a plain string, so the record carries no
    ``arcengine`` enum dependency to reconstruct."""
    if state is None:
        return ""
    return str(getattr(state, "value", None) or getattr(state, "name", None) or state)


@dataclass(frozen=True)
class CaptureRecord:
    """One frozen record per ``choose_action`` node — the given, verbatim."""

    node_index: int
    game_id: str
    guid: Optional[str]
    state: str
    available_actions: Tuple[int, ...]
    full_reset: bool
    levels_completed: int
    win_levels: int
    layers: Layers
    frames_len: int
    layered_hash: str
    edge: Edge
    # (site, class) — carried from the original (site, class, action, node)
    # record lineage; additive, never derived.
    site: Optional[str] = None
    cls: Optional[int] = None
    # WO-R1-02c — THE ACTED-ON CELL: the grid cell (row, col) the solver actually
    # acted on to produce this node, or None for a non-coordinate action
    # (directionals, RESET) and for the root node.
    #
    # This completes the record. ``edge`` keys IDENTITY — (action_id, region) —
    # deliberately (WO-R4 D1), and feeds StateTracker's committed keyspace; it is
    # right for what it is for and is untouched here. But the record was silent
    # about WHERE the solver acted: the emitter computes the cell, sends it to the
    # world, and the capture layer dropped it. The capture layer is the lossless
    # given — what we did — and the cell is what we did. A record that omits it is
    # an incomplete record of the action.
    #
    # Recorded, never derived: it is the coordinate the solver emitted, carried
    # verbatim on the same per-frame channel as ``edge``'s action_id. Anything
    # needing to know which object an action touched reads it from here — no
    # parallel channel, no Store-A round-trip.
    acted_cell: Optional[Tuple[int, int]] = None

    @staticmethod
    def from_frame(
        frame: Any,
        *,
        site: Optional[str] = None,
        cls: Optional[int] = None,
        action: Any = None,
        node_index: int = 0,
        frames_len: int = 1,
        acted_cell: Optional[Tuple[int, int]] = None,
    ) -> "CaptureRecord":
        """Build a record off a FrameData-like object (anything exposing
        ``.frame``). All non-frame fields read via ``getattr`` with defaults,
        so a partial/synthetic frame captures losslessly what it carries.

        ``action`` is the action that produced this node (the inbound edge):
        a bare int -> ``(id, None)``, a ``(id, target)`` tuple passed through,
        both via the real ``_norm_key``. ``None`` -> ``edge=None`` (root node).

        ``acted_cell`` is the ``(row, col)`` the solver acted on to produce this
        node — ``None`` for non-coordinate actions and the root. Recorded
        verbatim from the emitter; never derived.
        """
        layers = _freeze_layers(getattr(frame, "frame", []))
        edge: Edge = _norm_key(action) if action is not None else None
        return CaptureRecord(
            acted_cell=acted_cell,
            node_index=node_index,
            game_id=getattr(frame, "game_id", "") or "",
            guid=getattr(frame, "guid", None),
            state=_state_str(getattr(frame, "state", None)),
            available_actions=tuple(
                int(a) for a in (getattr(frame, "available_actions", ()) or ())
            ),
            full_reset=bool(getattr(frame, "full_reset", False)),
            levels_completed=int(getattr(frame, "levels_completed", 0) or 0),
            win_levels=int(getattr(frame, "win_levels", 0) or 0),
            layers=layers,
            frames_len=int(frames_len),
            layered_hash=_hash_layers(layers),
            edge=edge,
            site=site,
            cls=cls,
        )

    def reconstruct_frame(self) -> List[List[List[int]]]:
        """Return ``frame.frame`` byte-equal, all layers, as nested lists."""
        return _thaw_layers(self.layers)


class FrameRecordLog:
    """Append-only container of ``CaptureRecord``, held on ``ctx``.

    ``append`` accepts either a prebuilt ``CaptureRecord`` (WO §1 shape) or a
    FrameData-like frame plus its capture kwargs; in both cases the log owns
    ``node_index`` assignment, guaranteeing monotonicity and that no prior
    record is mutated.
    """

    def __init__(self) -> None:
        self._records: List[CaptureRecord] = []

    def append(
        self,
        item: Any,
        *,
        site: Optional[str] = None,
        cls: Optional[int] = None,
        action: Any = None,
        frames_len: int = 1,
        acted_cell: Optional[Tuple[int, int]] = None,
    ) -> None:
        idx = len(self._records)
        if isinstance(item, CaptureRecord):
            record = replace(item, node_index=idx)
        else:
            record = CaptureRecord.from_frame(
                item,
                site=site,
                cls=cls,
                action=action,
                node_index=idx,
                frames_len=frames_len,
                acted_cell=acted_cell,
            )
        self._records.append(record)

    @property
    def records(self) -> Tuple[CaptureRecord, ...]:
        """Immutable snapshot view of the appended records, in order."""
        return tuple(self._records)

    def reconstruct(self, node_index: int) -> List[List[List[int]]]:
        """Rebuild ``frame.frame`` (all layers) for the record at ``node_index``."""
        for record in self._records:
            if record.node_index == node_index:
                return record.reconstruct_frame()
        raise KeyError(f"no CaptureRecord at node_index {node_index}")

    def __len__(self) -> int:
        return len(self._records)


# The pre-flight red contract (tests/capture/) names the container CaptureStore;
# WO-CC-S1 §1 names it FrameRecordLog. Same object, one alias — no divergence.
CaptureStore = FrameRecordLog
