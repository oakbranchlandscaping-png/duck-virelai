"""WO-PE-03A: schema v5's per-level product content — every active gate product, exactly, strictly digested.

Author: Claude (Alpha build seat), 2026-10-15. Interface: ``INTERFACE_WO_PE_03_CLAIMS_KEYS_GRADER_v2`` §9; Sol's D15:
"a per-level product-content chapter containing each active product exactly once at the level's H1 or H2 census".

Schema v4 stores a product only as a receipt (gate, type, revision and a ``default=str`` hash). The paper's LAW,
RELATION and graded PREDICTION claims are about the product bodies, so v5 keeps each body once, beside its receipt:

* ``capture(machine)`` reads the same ``target_journal.active_product`` the receipts read, at the same census (H1
  before the journal is rebuilt; H2 and live views on the open level). It calls no gate method and reads no file.
* Each entry carries a versioned digest: full SHA-256 over ``virelai-canonical-json-v1`` (sorted keys, compact
  separators, ASCII, no NaN, **no** ``default=``) of ``{gate_id, product_type, revision, dependencies, payload}``.
* A product that cannot be represented in strict JSON is kept as an ``UNREPRESENTABLE`` entry with a typed gap and no
  partial payload. It seals; a formal evidence packet (PE-03B) must refuse a model holding one.
* ``validate_level_content(level)`` is pure: entries equal receipts one for one; gate, type and revision agree; every
  digest recomputes; each payload re-serialises to the receipt's legacy hash (an agreement check only, never the
  digest); ``product_answers`` names the same gate and type.

Prediction histories and graded outcomes stay inside the payloads; there is no second prediction ledger. Nothing here
is rendered to Duck.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from inference.framework import strict_json

ALGORITHM, ENCODING = "sha256", "virelai-canonical-json-v1"
CAPTURED, UNREPRESENTABLE = "CAPTURED", "UNREPRESENTABLE"
GAP_REASON = "PRODUCT_CONTENT_UNREPRESENTABLE"
ENTRY_KEYS = frozenset({"status", "gate_id", "product_type", "revision", "dependencies", "payload", "digest"})


class ProductContentError(ValueError):
    """A value cannot be represented as strict canonical JSON, or a stored chapter breaks the v5 contract."""


def canonical_json(value: Any) -> str:
    """WO-G4-DOSSIER-A (R10): the one shared strict canonicalizer (``strict_json``); a refusal names its JSON path."""
    try:
        return strict_json.canonical_json(value)
    except strict_json.StrictJsonError as exc:
        raise ProductContentError(f"not strict canonical JSON: {exc}") from exc


def digest_record(value: Any) -> dict[str, str]:
    raw = canonical_json(value).encode("ascii")
    return {"algorithm": ALGORITHM, "encoding": ENCODING, "value": hashlib.sha256(raw).hexdigest()}


def _identity(gate_id: str, product: Any) -> dict[str, Any]:
    return {"gate_id": str(gate_id), "product_type": str(product.product_type), "revision": int(product.revision),
            "dependencies": [str(item) for item in product.dependencies]}


def _digested(identity: Mapping[str, Any], payload: Any) -> dict[str, Any]:
    return digest_record({**identity, "payload": payload})


def entry(gate_id: str, product: Any) -> dict[str, Any]:
    """One product's stored content: exact strict-JSON payload and digest, or a typed unrepresentable gap."""
    identity = _identity(gate_id, product)
    try:
        payload = json.loads(canonical_json(product.payload))
    except ProductContentError as exc:
        return {"status": UNREPRESENTABLE, **identity, "payload": None, "digest": None,
                "gap": {"reason": GAP_REASON, "detail": str(exc)}}
    return {"status": CAPTURED, **identity, "payload": payload, "digest": _digested(identity, payload)}


def capture(machine: Any) -> dict[str, Any]:
    """Every active product of the machine's current target journal, keyed by product id.

    Revision 2: the journal indexes active products by gate, the chapter by product id. Two gates presenting one id
    refuse the census (``ProductContentError`` naming the id, both gates, both types and both revisions), so no
    model can claim every active product was captured while one was overwritten."""
    active = [(contract.target_id, product) for contract in machine.target_registry.ordered()
              for product in (machine.target_journal.active_product(contract.target_id),) if product is not None]
    seen: dict[str, tuple[str, Any]] = {}
    for gate_id, product in active:
        if product.product_id in seen:
            other_gate, other = seen[product.product_id]
            raise ProductContentError(
                f"duplicate active product id {product.product_id!r}: gate {other_gate} ({other.product_type}, "
                f"revision {other.revision}) and gate {gate_id} ({product.product_type}, revision {product.revision})")
        seen[product.product_id] = (gate_id, product)
    return {product.product_id: entry(gate_id, product) for gate_id, product in active}


def legacy_payload_sha256(payload: Any) -> str:
    """``library_census._payload_sha256``'s rule, reproduced only to check a receipt against the stored content."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProductContentError(message)


def _validate_entry(product_id: str, stored: Any, receipt: Mapping[str, Any]) -> None:
    _require(isinstance(stored, Mapping) and stored.get("status") in (CAPTURED, UNREPRESENTABLE),
             f"product_content[{product_id}] has a status")
    keys = ENTRY_KEYS | ({"gap"} if stored["status"] == UNREPRESENTABLE else set())
    _require(set(stored) == keys, f"product_content[{product_id}] has exactly the declared keys")
    _require((stored["gate_id"], stored["product_type"], stored["revision"]) == (
        receipt.get("gate_id"), receipt.get("product_type"), receipt.get("revision")),
        f"product_content[{product_id}] disagrees with its receipt's gate, type or revision")
    _require(isinstance(stored["dependencies"], list) and all(isinstance(item, str) for item in stored["dependencies"]),
             f"product_content[{product_id}].dependencies is a list of ids")
    identity = {key: stored[key] for key in ("gate_id", "product_type", "revision", "dependencies")}
    if stored["status"] == UNREPRESENTABLE:
        gap = stored["gap"]
        _require(stored["payload"] is None and stored["digest"] is None and isinstance(gap, Mapping)
                 and gap.get("reason") == GAP_REASON and isinstance(gap.get("detail"), str),
                 f"product_content[{product_id}] is UNREPRESENTABLE with a typed gap and no payload")
        return
    _require(stored["digest"] == _digested(identity, stored["payload"]),
             f"product_content[{product_id}].digest does not recompute")
    _require(legacy_payload_sha256(stored["payload"]) == receipt.get("payload_sha256"),
             f"product_content[{product_id}] payload disagrees with its receipt's payload_sha256")


def validate_level_content(level: Mapping[str, Any]) -> None:
    """The v5 product-content contract for one level (pure)."""
    content = level.get("product_content")
    receipts = (level.get("receipts") or {}).get("products") or {}
    _require(isinstance(content, Mapping), f"level {level.get('level')} has a product_content chapter")
    _require(set(content) == set(receipts),
             f"level {level.get('level')}: product_content and receipts name different products")
    for product_id, stored in content.items():
        _validate_entry(product_id, stored, receipts[product_id])
    for product_id, origin in (level.get("product_answers") or {}).items():
        stored = content.get(product_id)
        _require(isinstance(stored, Mapping) and isinstance(origin, Mapping)
                 and (origin.get("gate_id"), origin.get("product_type")) == (stored["gate_id"], stored["product_type"]),
                 f"product_answers[{product_id}] disagrees with its content's gate or type")


__all__ = ["ALGORITHM", "CAPTURED", "ENCODING", "GAP_REASON", "ProductContentError", "UNREPRESENTABLE", "capture",
           "canonical_json", "digest_record", "entry", "legacy_payload_sha256", "validate_level_content"]
