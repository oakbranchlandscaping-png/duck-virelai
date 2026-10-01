"""Evidence-driven lever-depth probing, deliberately disconnected from Duck.

This is the reusable state machine underneath a future Captain executor.  It names which
lever should be activated next and records exact affected-channel states supplied by an
adapter.  It does not choose an ARC action, route an ego, call the environment, or alter a
prompt.

Port sources: V4 ``weave/coverage_sweep.py`` and the lever-subtree campaign.  The dynamic
queue and one-lever-at-a-time discipline are retained.  Fixed press counts and the legacy
conflation of mechanism with saturation are not.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Iterable, Mapping


def _key(value: Any) -> str:
    """Return a deterministic key for an exact observed channel state."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ProbeTarget:
    handle: str
    activation_mode: str
    bbox: tuple[int, int, int, int] | None
    channels: tuple[str, ...]


@dataclass(frozen=True)
class ActivationObservation:
    """One completed activation and its exact post-activation channel states."""
    lever: str
    step: int
    channel_states: Mapping[str, Any]


@dataclass
class _ChannelRecord:
    states: list[str] = field(default_factory=list)
    null_run: int = 0
    mechanism: str = "UNKNOWN"
    condition: str = "OPEN_OR_UNMEASURED"
    period: int | None = None
    status: str = "COLLECTING"

    def observe(self, state: Any) -> None:
        encoded = _key(state)
        if self.states and encoded == self.states[-1]:
            self.null_run += 1
        else:
            self.null_run = 0
            # A later visible response disproves an earlier endpoint reading.
            if self.condition == "SATURATED_OBSERVED":
                self.condition = "OPEN_OR_UNMEASURED"
                self.status = "COLLECTING"
        self.states.append(encoded)
        self._classify()

    def _classify(self) -> None:
        # An endpoint is an observed condition, not a mechanism type.  Two consecutive
        # unchanged activations are the confirmation floor inherited from V4.
        if self.null_run >= 2:
            self.condition = "SATURATED_OBSERVED"
            self.status = "SEALED"
            return

        # Exact recurrence requires two complete periods.  Period one is deliberately not
        # called a cycle: repeated identical outputs are a uniform/no-novelty observation.
        for period in range(2, len(self.states) // 2 + 1):
            tail = self.states[-2 * period :]
            if tail[:period] == tail[period:]:
                self.mechanism = "TOGGLE" if period == 2 else "CYCLE"
                self.period = period
                self.status = "SEALED"
                return

        if len(self.states) >= 2 and self.states[-1] == self.states[-2]:
            self.mechanism = "UNIFORM_RESPONSE"

    @property
    def sealed(self) -> bool:
        return self.status == "SEALED"

    def export(self) -> dict[str, Any]:
        return {
            "observations": len(self.states),
            "novel_states": len(set(self.states)),
            "mechanism": self.mechanism,
            "period": self.period,
            "condition": self.condition,
            "status": self.status,
        }


class LeverDepthPlanner:
    """Maintain a dynamic, evidence-terminated queue of lever probes."""

    def __init__(self, *, engineering_cap: int = 64) -> None:
        if engineering_cap < 1:
            raise ValueError("engineering_cap must be positive")
        self.engineering_cap = engineering_cap
        self._targets: dict[str, ProbeTarget] = {}
        self._pending: list[str] = []
        self._records: dict[str, dict[str, _ChannelRecord]] = {}
        self._activations: dict[str, int] = {}
        self._finished: dict[str, str] = {}

    def refresh(self, segments: Iterable[Mapping[str, Any]]) -> None:
        """Append newly discovered levers without resetting earlier evidence."""
        for segment in segments:
            mechanics = segment.get("lever_mechanics") or {}
            candidates = [
                (lever, "lever", "effect_channels")
                for lever in mechanics.get("levers", [])
            ] + [
                (control, "control", "self_effect_channels")
                for control in mechanics.get("reactive_controls", [])
            ]
            for lever, handle_key, channels_key in candidates:
                handle = str(lever[handle_key])
                if handle in self._targets:
                    continue
                visible = lever.get("visible") or {}
                bbox = visible.get("bbox")
                target = ProbeTarget(
                    handle=handle,
                    activation_mode=(
                        "BODY_CONTACT_REQUIRED" if lever.get("kind") == "CONTACT_SURFACE"
                        else "POINTER_TARGET_REQUIRED"
                    ),
                    bbox=None if bbox is None else tuple(bbox),
                    channels=tuple(channel["channel"] for channel in lever.get(channels_key, [])),
                )
                self._targets[handle] = target
                self._pending.append(handle)
                self._records[handle] = {channel: _ChannelRecord() for channel in target.channels}
                self._activations[handle] = 0

    def request(self) -> dict[str, Any]:
        """Describe the next empirical operation; never fabricate an ARC action."""
        self._advance_completed()
        if not self._pending:
            return {"status": "SATURATED", "request": None}
        target = self._targets[self._pending[0]]
        return {
            "status": "PROBE_REQUIRED",
            "request": {
                "lever": target.handle,
                "activation_mode": target.activation_mode,
                "bbox": None if target.bbox is None else list(target.bbox),
                "channels_to_measure": list(target.channels),
                "arc_action": None,
            },
        }

    def record(self, observation: ActivationObservation) -> None:
        self._advance_completed()
        if not self._pending or observation.lever != self._pending[0]:
            expected = None if not self._pending else self._pending[0]
            raise ValueError(f"observation for {observation.lever}; expected {expected}")
        known = self._records[observation.lever]
        missing = set(known) - set(observation.channel_states)
        extra = set(observation.channel_states) - set(known)
        if missing or extra:
            raise ValueError(f"channel mismatch: missing={sorted(missing)} extra={sorted(extra)}")
        for channel, state in observation.channel_states.items():
            known[channel].observe(state)
        self._activations[observation.lever] += 1
        self._advance_completed()

    def _advance_completed(self) -> None:
        while self._pending:
            handle = self._pending[0]
            channels = self._records[handle]
            cap = self._activations[handle] >= self.engineering_cap
            # A lever with no observed effect channel is not silently declared understood.
            sealed = bool(channels) and all(record.sealed for record in channels.values())
            if not (sealed or cap):
                break
            self._pending.pop(0)
            self._finished[handle] = "EVIDENCE_TERMINATED" if sealed else "CAP_REACHED_UNRESOLVED"

    def export(self) -> dict[str, Any]:
        self._advance_completed()
        return {
            "schema": "virelai-lever-depth-plan-v1",
            "policy": "ONE_LEVER_UNTIL_NO_NOVEL_STATE_OR_CONFIRMED_RECURRENCE",
            "action_authority": "NONE",
            "pending": list(self._pending),
            "levers": [
                {
                    "lever": handle,
                    "activation_mode": target.activation_mode,
                    "bbox": None if target.bbox is None else list(target.bbox),
                    "activations": self._activations[handle],
                    "completion": self._finished.get(handle, "OPEN"),
                    "channels": {
                        channel: record.export()
                        for channel, record in self._records[handle].items()
                    },
                }
                for handle, target in self._targets.items()
            ],
        }


__all__ = ["ActivationObservation", "LeverDepthPlanner", "ProbeTarget"]
