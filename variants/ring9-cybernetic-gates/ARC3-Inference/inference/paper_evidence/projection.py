"""The pure projection of a sealed v11 model into ``paper_evidence.json`` (WO-PE-03B).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.3-§2.4.

A packet needs:
- a v11 model that the canonical reader validates;
- no UNREPRESENTABLE product.
Anything else is refused with a typed reason (``PRODUCT_CONTENT_UNAVAILABLE`` for v4, ``SCHEMA_NOT_V11`` for other
schemas).

An open or incomplete provenance chapter is not a refusal (the Director's directive, step 7). It is measured output:
the stamp carries integrity, completeness and the chapter's own reasons, and ``stamp.provenance_sealed`` is false. Every
table the grader writes reports that column, so a world with an unsealed journal is counted, never dropped.
Two projections of one model are byte-identical.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from inference.framework import strict_json, world_description, world_model_v2
from inference.paper_evidence import sources_answers, sources_products, sources_record
from inference.paper_evidence.context import level_context

SCHEMA = "virelai-paper-evidence-v1"
V11 = "virelai-world-model-v11"
NO_CONTENT = frozenset({"virelai-world-model-v2", "virelai-world-model-v3", "virelai-world-model-v4"})


class ProjectionRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def check_formal(model: Mapping[str, Any]) -> None:
    """Refuse anything that is not a validated v11 model with every product represented."""
    schema = model.get("schema")
    if schema in NO_CONTENT:
        raise ProjectionRefused("PRODUCT_CONTENT_UNAVAILABLE", f"{schema} holds no product content")
    if schema != V11:
        raise ProjectionRefused("SCHEMA_NOT_V11", repr(schema))
    try:
        world_model_v2.read_world_model(model)
    except world_model_v2.WorldModelV2Error as exc:
        raise ProjectionRefused("MODEL_INVALID", str(exc)) from exc
    for level in model["levels"]:
        for product_id, entry in (level.get("product_content") or {}).items():
            if entry.get("status") != "CAPTURED":
                raise ProjectionRefused("PRODUCT_UNREPRESENTABLE", f"level {level['level']} {product_id}")


def _stamp(model: Mapping[str, Any]) -> dict[str, Any]:
    chapter = model.get("provenance") or {}
    return {"model_schema": model["schema"], "content_sha256": model["content_sha256"], "game_id": model["game_id"],
            "run_stem": model.get("run_stem"), "integrity": chapter.get("integrity"),
            "provenance_sealed": chapter.get("integrity") == "SEALED" and chapter.get("completeness") == "COMPLETE",
            "completeness": chapter.get("completeness"), "completeness_reasons": list(chapter.get("reasons") or ()),
            "journal_check": (model.get("manifest") or {}).get("journal_check"),
            "entry_frames": {str(level["level"]): level["entry"]["board_sha256"] for level in model["levels"]}}


def _level_claims(model: Mapping[str, Any], level: Mapping[str, Any], described: Mapping[str, Any]) -> list[dict]:
    ctx = level_context(model, level)
    found: list[dict[str, Any]] = []
    for source in (sources_record.role_claims(ctx), sources_record.scoped_null_claims(ctx),
                   sources_record.pattern_claims(ctx, described), sources_record.gap_claims(ctx),
                   sources_record.chapter_claims(ctx), sources_record.win_claims(ctx),
                   sources_products.product_claims(ctx), sources_answers.answer_claims(ctx)):
        found.extend(source)
    return found


def _counts(claims: list[dict[str, Any]]) -> dict[str, Any]:
    by = Counter((item["family"], item["kind"], item["executor"], item["admission"]) for item in claims)
    return {"claims": len(claims), "propositions": sum(item["kind"] == "PROPOSITION" for item in claims),
            "audits": sum(item["kind"] == "AUDIT" for item in claims),
            "by_family_kind_executor_admission": [[*key, count] for key, count in sorted(by.items())]}


def project(model: Mapping[str, Any]) -> dict[str, Any]:
    """The paper-evidence packet of one sealed model; refuses (raises) anything that cannot be formal."""
    check_formal(model)
    described = {item["level"]: item for item in world_description.describe_world(model)["levels"]}
    claims = [claim for level in model["levels"] for claim in _level_claims(model, level, described.get(level["level"], {}))]
    seen: set[str] = set()
    for item in claims:
        if item["assertion_id"] in seen:
            raise ProjectionRefused("DUPLICATE_ASSERTION", item["assertion_id"])
        seen.add(item["assertion_id"])
    claims.sort(key=lambda item: (item["level"], item["family"], item["kind"], item["claim_key"], item["assertion_id"]))
    return {"schema": SCHEMA, "stamp": _stamp(model), "counts": _counts(claims), "claims": claims}


def evidence_bytes(packet: Mapping[str, Any]) -> bytes:
    """The one serialization of ``paper_evidence.json``: strict canonical JSON plus a final newline."""
    return (strict_json.canonical_json(packet) + "\n").encode("ascii")


__all__ = ["ProjectionRefused", "SCHEMA", "check_formal", "evidence_bytes", "project"]
