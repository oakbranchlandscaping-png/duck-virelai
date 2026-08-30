"""Pure Ring 6.3 handoff inspection helpers.

This module deliberately depends only on the standard library.  The transport
tests can therefore grade the exact report/payload contract without importing
ARC, TAAF, Pillow, NumPy, or the model client.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class TextFingerprint:
    sha256: str
    characters: int
    utf8_bytes: int


@dataclass(frozen=True)
class ReportLocation:
    message_index: int
    role: str
    text_block_index: int
    occurrence_index: int


def fingerprint_text(text: str) -> TextFingerprint:
    """Fingerprint exact text without whitespace or Unicode normalization."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    raw = text.encode("utf-8")
    return TextFingerprint(
        sha256=hashlib.sha256(raw).hexdigest(),
        characters=len(text),
        utf8_bytes=len(raw),
    )


def _message_text_blocks(message: dict[str, Any]) -> Iterable[tuple[int, str]]:
    content = message.get("content", "")
    if isinstance(content, str):
        yield 0, content
        return
    if not isinstance(content, list):
        return
    for block_index, block in enumerate(content):
        if not isinstance(block, dict):
            continue
        if str(block.get("type", "")).strip().lower() != "text":
            continue
        text = block.get("text", "")
        if isinstance(text, str):
            yield block_index, text


def report_locations(
    messages: list[dict[str, Any]] | None,
    report: str,
    *,
    roles: set[str] | None = None,
) -> list[ReportLocation]:
    """Locate exact, contiguous report copies in OpenAI-style messages."""
    if not isinstance(report, str) or not report:
        return []
    allowed = {str(role).strip().lower() for role in roles} if roles else None
    locations: list[ReportLocation] = []
    for message_index, message in enumerate(messages or []):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip().lower()
        if allowed is not None and role not in allowed:
            continue
        for block_index, text in _message_text_blocks(message):
            start = 0
            occurrence_index = 0
            while True:
                found = text.find(report, start)
                if found < 0:
                    break
                locations.append(
                    ReportLocation(
                        message_index=message_index,
                        role=role,
                        text_block_index=block_index,
                        occurrence_index=occurrence_index,
                    )
                )
                occurrence_index += 1
                start = found + len(report)
    return locations


def payload_report_locations(
    provider_payload: dict[str, Any] | None,
    report: str,
    *,
    roles: set[str] | None = None,
) -> list[ReportLocation]:
    messages = (
        provider_payload.get("messages")
        if isinstance(provider_payload, dict)
        else None
    )
    return report_locations(messages if isinstance(messages, list) else [], report, roles=roles)


def locations_as_dicts(locations: Iterable[ReportLocation]) -> list[dict[str, Any]]:
    return [asdict(location) for location in locations]


def history_contains_report(
    history_messages: list[dict[str, Any]] | None,
    report: str,
) -> bool:
    """True only when an exact report already exists in retained user history."""
    return bool(report_locations(history_messages, report, roles={"user"}))
