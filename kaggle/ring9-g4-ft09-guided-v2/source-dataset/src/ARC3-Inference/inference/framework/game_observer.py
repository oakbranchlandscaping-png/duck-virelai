"""Duck-owned extension seam for passive per-game observers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

OBSERVER_MODES = ("off", "observe", "tool", "controller", "gated")


def normalize_observer_mode(value: str | None) -> str:
    mode = str(value or "off").strip().lower()
    if mode not in OBSERVER_MODES:
        raise ValueError(
            f"Unsupported Virelai mode {value!r}; expected one of {OBSERVER_MODES}."
        )
    return mode


class GameObserver(Protocol):
    """The only interface through which Duck communicates with an observer."""

    def observe_initial(self, frame: Any) -> None: ...

    def observe_transition(
        self,
        *,
        frame: Any,
        action_id: int,
        action_name: str,
        acted_cell: tuple[int, int] | None,
        actor: str,
        result: dict[str, Any],
    ) -> None: ...

    def query(
        self, operation: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...

    def record_failure(
        self, event: str, detail: str, *, through_step: int | None = None
    ) -> None: ...

    def close(self) -> None: ...


class VirelaiObserver:
    """Narrow adapter from Duck's observer protocol to the evidence runtime."""

    def __init__(
        self,
        *,
        game_id: str,
        run_stem: str,
        artifact_root: Path | None,
    ) -> None:
        from inference.framework.virelai_runtime import VirelaiRuntime

        self._runtime = VirelaiRuntime(
            game_id=game_id,
            run_stem=run_stem,
            artifact_root=artifact_root,
        )

    def observe_initial(self, frame: Any) -> None:
        self._runtime.observe_initial(frame)

    def observe_transition(self, **kwargs: Any) -> None:
        self._runtime.observe_transition(**kwargs)

    def query(
        self, operation: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._runtime.query(operation, parameters)

    def record_failure(
        self, event: str, detail: str, *, through_step: int | None = None
    ) -> None:
        self._runtime.record_failure(event, detail, through_step=through_step)

    def close(self) -> None:
        self._runtime.flush()


def create_game_observer(
    *,
    mode: str,
    game_id: str,
    run_stem: str,
    artifact_root: Path | None,
) -> GameObserver | None:
    """Create no observer in off mode and one passive observer otherwise."""
    normalized = normalize_observer_mode(mode)
    if normalized == "off":
        return None
    return VirelaiObserver(
        game_id=game_id,
        run_stem=run_stem,
        artifact_root=artifact_root,
    )


__all__ = [
    "GameObserver",
    "OBSERVER_MODES",
    "VirelaiObserver",
    "create_game_observer",
    "normalize_observer_mode",
]
