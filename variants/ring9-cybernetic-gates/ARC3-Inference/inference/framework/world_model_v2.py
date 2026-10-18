"""The canonical world model, schema v6: one validated, canonically hashed file per observed game.

Author: Claude (Alpha build seat), 2026-10-10. WO-L2a (INTERFACE_WO_L2A_WORLD_MODEL_V2 v2; Sol's reviews
REVIEW_WO_L2_00_CENSUS_ARCHITECTURE and REVIEW_WO_L2A_INTERFACE, 2026-10-10). Schema v3, 2026-10-13: WO-DESC-A
(INTERFACE_WO_DESC_A_v2) adds each level's descriptive event ledger and scene (``descriptive_events``) and
enriches the receipts it is checked against. A v2 artifact is still read, by the v2 rules (``validate_v2``).
Schema v4, 2026-10-14: WO-PE-02 (INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2) adds the ``provenance`` chapter, the
validated audit journal absorbed once with every level holding only its event-id index (``provenance_chapter``),
and two census fields reconciliation needs (``record.reset_transition_ids``, ``product_answers``). A v3 artifact
is still read, by the frozen v3 rules (``validate_v3``). The v3 ``journal_check`` fields keep their meaning: H2's
record check, not the provenance journal. Schema v5, 2026-10-15: WO-PE-03A (INTERFACE_WO_PE_03_CLAIMS_KEYS_GRADER_v2
§9) adds each level's ``product_content``, every active product's exact body with a strict versioned digest
(``product_content``). A v4 artifact is still read, by the frozen v4 rules (``validate_v4``). Schema v6, 2026-10-16:
WO-G4-DOSSIER-A (INTERFACE_WO_G4_DOSSIER_A_v2) adds each level's ``lever_dossiers``, one chapter-statused mechanics
dossier per certified lever (``lever_dossiers``, validated by ``lever_dossier_schema``), and refuses a payload that is
not strict canonical JSON before its hash (R10). A v5 artifact is still read, by the frozen v5 rules (``validate_v5``).
Accepted limitation (R12): a hard process kill writes no H2, so per-lever work since the last written model is lost.

Two tiers, kept apart by the validator:

- **observation**: level/life-scoped object tracks read off the recorded boards. They carry sightings,
  departures and possible correspondences, never a role.
- **certified**: roles that a gate product or gate-written witness certifies, each citing its gate and
  evidence. Nothing else may occupy a role: not a detector candidate, not a Duck note, not a terrain
  label, and never INERT (no coverage certificate exists yet).

Everything open is a typed gap. The level-entry board is the ``INITIAL_FRAME`` (or ``LEVEL_ENTRY`` after a
level change), never a transition. This module validates, serializes, reads and writes; it computes
nothing about a world (``library_census`` does) and is the only writer of ``world_model.json``.

**What validation does and does not prove.** Each level carries a receipt index (recorded transition
evidence, active gate products, G3 witnesses). Every certified role must resolve its product, witness and
evidence references against that index, with the right gate and entity, and every receipt must sit on a
recorded transition of the level. An invented or mismatched reference therefore fails. Validation does
not prove the index itself came from the gate machine: that rests on the compiler, which reads gate state
only, and on a later cross-check against the run's gate artifacts.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "virelai-world-model-v7"  # WO-G4-DOSSIER-B (B1): every lever dossier holds its record-derived observations
V6_SCHEMA = "virelai-world-model-v6"
V5_SCHEMA = "virelai-world-model-v5"
V4_SCHEMA = "virelai-world-model-v4"
V3_SCHEMA = "virelai-world-model-v3"
V2_SCHEMA = "virelai-world-model-v2"
V1_SCHEMA = "virelai-world-model-v1"
CANONICAL_NAME = "world_model.json"

MANIFEST_STATUSES = frozenset({"ACTIVE", "OBSERVED_NEVER_ACTED"})
PERSIST_REASONS = frozenset({"LEVEL_ADVANCE", "RUN_END", "BUDGET_STOP", "CONTROLLED_STOP", "CRASH", "CANCELLED",
                             "LIVE_VIEW"})
LIVE_VIEW = "LIVE_VIEW"  # the in-memory library Duck reads (library_view); validated, never written to disk
ENTRY_SOURCES = frozenset({"INITIAL_FRAME", "LEVEL_ENTRY"})
GAP_REASONS = frozenset({
    "NOT_REACHED", "BUDGET", "FOUNDATION_UNRESOLVED", "CLASS_CHANGED", "NOT_BUILT",
    "IDENTITY_UNRESOLVED", "RECORD_MISMATCH", "INCONCLUSIVE",
})
CERTIFIED_ROLES = frozenset({"EGO", "COUNTER", "LEVER"})  # this slice; FORCE/DRIVEN/INERT are gaps
ROLE_SOURCES = {"EGO": "G1-EGO", "COUNTER": "G2-COUNTER", "LEVER": "G3-LEVERS"}
INVENTORY_STATUSES = frozenset({"PENDING", "ACCEPTED"})
JOIN_STATUSES = frozenset({"EXACT_ONE_TO_ONE", "UNRESOLVED", "NOT_APPLICABLE"})
BAND1 = frozenset({"UNSETTLED"})  # settled-frame Band 1 is a later slice


class WorldModelV2Error(ValueError):
    """A v2 model violates its contract."""


@dataclass(frozen=True)
class WriteResult:
    ok: bool
    path: str
    sha256: str | None
    error: str | None = None


def _fail(message: str) -> None:
    raise WorldModelV2Error(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def content_sha256(payload: Mapping[str, Any]) -> str:
    """The hash of the model's content, excluding its own hash field."""
    return hashlib.sha256(_canonical({k: v for k, v in payload.items() if k != "content_sha256"})).hexdigest()


def seal(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and stamp ``content_sha256``; the result is what ``canonical_bytes`` serializes.

    Schema v4: the provenance chapter is attached (the honest default for the persist reason when none was supplied)
    and every level receives its event-id index. Schema v5 adds nothing here: ``product_content`` comes from the
    census and is validated. Schema v6 (WO-G4-DOSSIER-A revision 2): the dossiers' provenance-dependent facts are
    reconciled with that chapter (``lever_dossier_provenance``: final at H2, pending otherwise)."""
    from inference.framework.lever_dossier_provenance import reconcile
    from inference.framework.provenance_chapter import attach

    sealed = reconcile(attach({k: v for k, v in dict(payload).items() if k != "content_sha256"}))
    sealed["schema"] = SCHEMA
    _strict(sealed)  # R10: no hash over a payload json.dumps would silently rewrite
    sealed["content_sha256"] = content_sha256(sealed)
    validate(sealed)
    return sealed


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    validate(payload)
    return _canonical(payload)


def validate(payload: Mapping[str, Any]) -> None:
    """The v7 contract: the v6 rules, and every lever dossier's record-derived observations (WO-G4-DOSSIER-B, B1)."""
    _validate_payload(payload, SCHEMA)


def validate_v6(payload: Mapping[str, Any]) -> None:
    """The accepted v6 contract, frozen: how a v6 artifact written before schema v7 is still read."""
    _validate_payload(payload, V6_SCHEMA)


def validate_v5(payload: Mapping[str, Any]) -> None:
    """The accepted v5 contract, frozen: how a v5 artifact written before schema v6 is still read."""
    _validate_payload(payload, V5_SCHEMA)


def validate_v4(payload: Mapping[str, Any]) -> None:
    """The accepted v4 contract, frozen: how a v4 artifact written before schema v5 is still read."""
    _validate_payload(payload, V4_SCHEMA)


def validate_v3(payload: Mapping[str, Any]) -> None:
    """The accepted v3 contract, frozen: how a v3 artifact written before schema v4 is still read."""
    _validate_payload(payload, V3_SCHEMA)


def validate_v2(payload: Mapping[str, Any]) -> None:
    """The accepted v2 contract, unchanged: how a v2 artifact written before schema v3 is still read."""
    _validate_payload(payload, V2_SCHEMA)


def _validate_payload(payload: Mapping[str, Any], schema: str) -> None:
    _require(payload.get("schema") == schema, f"schema must be {schema}")
    if schema in {V6_SCHEMA, SCHEMA}:
        _strict(payload)
    manifest = payload.get("manifest") or {}
    _require(manifest.get("status") in MANIFEST_STATUSES, "manifest.status is not a known status")
    _require(manifest.get("persist_reason") in PERSIST_REASONS, "manifest.persist_reason is not a known reason")
    levels = payload.get("levels")
    _require(isinstance(levels, list) and bool(levels), "a model holds at least the level-entry level")
    numbers = [level.get("level") for level in levels]
    _require(len(numbers) == len(set(numbers)), "each level appears once")
    open_levels = [level for level in levels if level.get("state") == "OPEN"]
    _require(len(open_levels) <= 1, "at most one level is open")
    for level in levels:
        _validate_level(level)
        if schema in {V3_SCHEMA, V4_SCHEMA, V5_SCHEMA, V6_SCHEMA, SCHEMA}:
            _validate_v3_level(level)
    if schema in {V5_SCHEMA, V6_SCHEMA, SCHEMA}:
        _validate_product_content(levels)
    if schema in {V4_SCHEMA, V5_SCHEMA, V6_SCHEMA, SCHEMA}:
        from inference.framework.provenance_chapter import ProvenanceChapterError, validate_chapter

        try:
            validate_chapter(payload)
        except ProvenanceChapterError as exc:
            _fail(f"provenance: {exc}")
    if schema in {V6_SCHEMA, SCHEMA}:  # after the provenance chapter: the dossiers' provenance facts are checked against it
        _validate_lever_dossiers(levels, manifest, payload.get("provenance"), v7=schema == SCHEMA)
    if "content_sha256" in payload:
        _require(payload["content_sha256"] == content_sha256(payload), "content_sha256 does not match the content")


def _validate_product_content(levels: list) -> None:
    from inference.framework.product_content import ProductContentError, validate_level_content

    for level in levels:
        try:
            validate_level_content(level)
        except ProductContentError as exc:
            _fail(f"product content: {exc}")


def _strict(payload: Mapping[str, Any]) -> None:
    from inference.framework.lever_dossier_schema import DossierError, check_strict

    try:
        check_strict(payload)
    except DossierError as exc:
        _fail(str(exc))


def _validate_lever_dossiers(levels: list, manifest: Mapping[str, Any], provenance: Any, *, v7: bool) -> None:
    from inference.framework.lever_dossier_schema import DossierError, validate_level

    for level in levels:
        try:
            validate_level(level, manifest, provenance, v7=v7)
        except DossierError as exc:
            _fail(f"lever dossiers: {exc}")


def _validate_level(level: Mapping[str, Any]) -> None:
    _require(level.get("state") in {"OPEN", "FROZEN"}, "level.state is OPEN or FROZEN")
    entry = level.get("entry") or {}
    _require(entry.get("source") in ENTRY_SOURCES, "the entry board's source is INITIAL_FRAME or LEVEL_ENTRY")
    _require("transition_id" not in entry, "the entry board is not a transition; it has no transition_id")
    if entry["source"] == "LEVEL_ENTRY":
        _require(isinstance(entry.get("after_transition"), int) and entry["after_transition"] > 0,
                 "a LEVEL_ENTRY board cites the transition that ended the previous level")
    recorded = set((level.get("record") or {}).get("transition_ids") or ())
    _require(0 not in recorded, "transition 0 is not a receipt")
    tracks = (level.get("observation") or {}).get("tracks") or []
    track_ids = [track.get("track_id") for track in tracks]
    _require(len(track_ids) == len(set(track_ids)), "track ids are unique")
    for track in tracks:
        _validate_track(track, recorded)
    known_tracks = set(track_ids)
    receipts = _validate_receipts(level.get("receipts"), recorded)
    certified = level.get("certified") or {}
    for role in certified.get("roles") or ():
        _validate_role(role, known_tracks, receipts)
    for null in certified.get("scoped_nulls") or ():
        _require(null.get("inertness_claim_permitted") is False, "a scoped null never claims inertness")
        _require(bool(null.get("evidence_ref")), "a scoped null cites its evidence")
    for gap in level.get("gaps") or ():
        _require(gap.get("reason") in GAP_REASONS, f"unknown gap reason {gap.get('reason')!r}")
        _require(bool(gap.get("archetype_question")), "a gap names its open question")
    accounting = level.get("accounting") or {}
    _require(accounting.get("status") in {"ACCOUNTED", "NOT_ACCOUNTED"}, "accounting.status is required")
    mismatch = any(gap.get("reason") == "RECORD_MISMATCH" for gap in level.get("gaps") or ())
    _require(not (mismatch and accounting["status"] == "ACCOUNTED"), "a record mismatch is never ACCOUNTED")
    _validate_journal_check(level, accounting)
    _require(accounting["status"] == "NOT_ACCOUNTED" or not accounting.get("missing"),
             "an ACCOUNTED level lists nothing missing")


CHECK_KEYS = ("missing", "extra", "duplicated", "renamed")


def _validate_v3_level(level: Mapping[str, Any]) -> None:
    """The v3 additions: enriched receipts, binding ends, and the description, checked against all of them."""
    from inference.framework import descriptive_events

    receipts = level["receipts"]
    for ref, product in receipts["products"].items():
        mask = product.get("mask")
        if mask is not None:
            _require(product["gate_id"] == "G2-COUNTER", f"product receipt {ref}: only a G2 mask law carries a mask")
            cells = descriptive_events.run_cells(mask.get("cell_runs") or ())
            rewrite = mask.get("rewrite") or {}
            _require(len(cells) == mask.get("cell_count") and isinstance(rewrite.get("from"), int)
                     and isinstance(rewrite.get("to"), int), f"product receipt {ref} carries a malformed mask")
    for ref, witness in receipts["witnesses"].items():
        _require(isinstance(witness.get("residue"), Mapping) and bool(witness.get("witness_sha256")),
                 f"witness receipt {ref} carries its residue and hash")
    roles = (level.get("certified") or {}).get("roles") or []
    recorded = set((level.get("record") or {}).get("transition_ids") or ())
    for role in roles:
        ends = role.get("binding_ends_at")
        _require(ends is None or ends in recorded, f"a {role.get('role')} binding ends at a recorded transition")
    entry = level.get("entry") or {}
    _require(((level.get("description") or {}).get("basis") or {}).get("entry_node")
             == (entry.get("after_transition") if entry.get("source") == "LEVEL_ENTRY" else 0),
             "the description starts at the level's entry board")
    descriptive_events.validate_description(
        level.get("description"), recorded=recorded, receipts=receipts, roles=roles, gaps=level.get("gaps") or [],
        tracks=[track["track_id"] for track in (level.get("observation") or {}).get("tracks") or ()])
    if (level.get("description") or {}).get("first_mismatch"):
        _require(level["accounting"]["status"] == "NOT_ACCOUNTED", "a description cut short is never ACCOUNTED")


def _validate_journal_check(level: Mapping[str, Any], accounting: Mapping[str, Any]) -> None:
    """PENDING until H2 reconciles the level against the execution history; only CHECKED may be ACCOUNTED."""
    check = (level.get("record") or {}).get("journal_check") or {}
    status = check.get("status")
    _require(status in {"PENDING", "CHECKED"}, "journal_check.status is PENDING or CHECKED")
    if status == "PENDING":
        _require(accounting["status"] == "NOT_ACCOUNTED" and "JOURNAL_CHECK_PENDING" in (accounting.get("missing") or ()),
                 "a level whose journal check is pending is NOT_ACCOUNTED, with JOURNAL_CHECK_PENDING missing")
        return
    named = {key: sorted(check.get(key) or ()) for key in CHECK_KEYS}
    _require(check.get("ok") is (not any(named.values())), "journal_check.ok agrees with its ids")
    if not check["ok"]:
        _require(accounting["status"] == "NOT_ACCOUNTED", "a checked level with a mismatch is NOT_ACCOUNTED")
        _require(any(gap.get("reason") == "RECORD_MISMATCH" and gap.get("source") == "record_check"
                     and {key: sorted(gap.get(key) or ()) for key in CHECK_KEYS} == named
                     for gap in level.get("gaps") or ()),
                 "a checked mismatch carries a RECORD_MISMATCH gap naming the same ids")


def _validate_track(track: Mapping[str, Any], recorded: set[int]) -> None:
    segments = track.get("segments") or []
    _require(bool(segments), "a track has at least one sighting segment")
    for segment in segments:
        _require(int(segment.get("count") or 0) >= 1, "a segment holds at least one sighting")
        for sighting in (segment.get("first") or {}, segment.get("last") or {}):
            source = sighting.get("source")
            if source in ENTRY_SOURCES:
                _require("transition_id" not in sighting, "an entry sighting is not a transition")
            else:
                _require(source == "TRANSITION", "a sighting comes from the entry board or a transition")
                _require(sighting.get("transition_id") in recorded, "a sighting cites a recorded transition")
    _require((track.get("band1") or {}).get("status") in BAND1, "Band 1 stays UNSETTLED in this slice")
    _require("roles" not in track, "an observation track carries no role")
    join = track.get("g3_join") or {}
    _require(join.get("status") in JOIN_STATUSES, "g3_join.status is required")
    _require((join.get("status") == "EXACT_ONE_TO_ONE") == bool(join.get("entity_id")),
             "only an exact one-to-one join names a G3 entity")


def _validate_receipts(receipts: Any, recorded: set[int]) -> Mapping[str, Any]:
    _require(isinstance(receipts, Mapping) and {"evidence", "products", "witnesses"} <= set(receipts),
             "a level carries its receipt index (evidence, products, witnesses)")
    for ref, receipt in receipts["evidence"].items():
        _require(receipt.get("transition_id") in recorded, f"evidence receipt {ref} is not a recorded transition")
    for ref, receipt in receipts["products"].items():
        _require(bool(receipt.get("gate_id")) and len(str(receipt.get("payload_sha256") or "")) == 64,
                 f"product receipt {ref} names its gate and payload hash")
    for ref, receipt in receipts["witnesses"].items():
        evidence = receipts["evidence"].get(receipt.get("evidence_ref"))
        _require(evidence is not None, f"witness receipt {ref} cites no recorded evidence")
        _require(evidence["transition_id"] == receipt.get("transition_id"), f"witness receipt {ref} disagrees with its evidence")
    return receipts


def _validate_role(role: Mapping[str, Any], known_tracks: set[str], receipts: Mapping[str, Any]) -> None:
    name = role.get("role")
    _require(name in CERTIFIED_ROLES, f"{name!r} cannot be certified in this slice")
    gate = ROLE_SOURCES[name]
    _require(role.get("gate_id") == gate, f"{name} is certified only by {gate}")
    if name in {"EGO", "COUNTER"}:
        product = receipts["products"].get(role.get("product_id"))
        _require(product is not None, f"{name}'s product_id resolves to no product receipt")
        _require(product["gate_id"] == gate, f"{name}'s product receipt belongs to {product['gate_id']}, not {gate}")
    known = set(receipts["evidence"]) | set(receipts["products"]) | set(receipts["witnesses"])
    for ref in role.get("evidence_refs") or ():
        _require(ref in known, f"{name} cites {ref!r}, which no receipt resolves")
    identity = role.get("identity") or {}
    _require(identity.get("status") in JOIN_STATUSES, "a role states its object identity status")
    track = identity.get("track_id")
    if identity["status"] == "EXACT_ONE_TO_ONE":
        _require(track in known_tracks, "a joined role names a known track")
        _require(bool(identity.get("basis")), "a joined role states its join basis")
    else:
        _require(track is None, "an unresolved role names no track")
    if name == "LEVER":
        _require(bool(role.get("witness_refs")), "a LEVER cites its G3 witness")
        for ref in role["witness_refs"]:
            witness = receipts["witnesses"].get(ref)
            _require(witness is not None, f"LEVER witness {ref!r} resolves to no witness receipt")
            _require(witness.get("entity_id") == role.get("entity_id"),
                     f"LEVER witness {ref!r} belongs to {witness.get('entity_id')}, not {role.get('entity_id')}")
        _require(role.get("inventory_status") in INVENTORY_STATUSES, "a LEVER states its inventory status")
    if name == "EGO" and role.get("binding_source") == "DUCK_DECLARED_SCOPE_FALLBACK":
        _require(identity["status"] != "EXACT_ONE_TO_ONE", "a Duck-declared footprint is a hint, never an identity")


def read_world_model(payload: Mapping[str, Any]) -> Any:
    """Version-aware reader: v1 through its own validator, v2-v6 by their frozen rules, v7 by this module's;
    anything else is refused."""
    schema = payload.get("schema")
    if schema == V1_SCHEMA:
        from inference.framework.virelai_world_model import validate_world_model, world_model_from_dict

        model = world_model_from_dict(dict(payload))
        validate_world_model(model)
        return model
    if schema == V2_SCHEMA:
        validate_v2(payload)
        return dict(payload)
    if schema == V3_SCHEMA:
        validate_v3(payload)
        return dict(payload)
    if schema == V4_SCHEMA:
        validate_v4(payload)
        return dict(payload)
    if schema == V5_SCHEMA:
        validate_v5(payload)
        return dict(payload)
    if schema == V6_SCHEMA:
        validate_v6(payload)
        return dict(payload)
    if schema == SCHEMA:
        validate(payload)
        return dict(payload)
    raise WorldModelV2Error(f"unknown world model schema {schema!r}")


def write_canonical(payload: Mapping[str, Any], directory: str | Path) -> WriteResult:
    """The one writer of ``world_model.json``: validate, serialize, write a sibling, replace atomically.

    Never raises: a failure is returned (and left for the caller to record), and no partial file remains.
    """
    target = Path(directory) / CANONICAL_NAME
    temporary: Path | None = None
    try:
        sealed = seal(payload) if "content_sha256" not in payload else dict(payload)
        _require((sealed.get("manifest") or {}).get("persist_reason") != LIVE_VIEW,
                 "a live view is never written as the canonical model")
        data = canonical_bytes(sealed)
        target.parent.mkdir(parents=True, exist_ok=True)
        # A unique sibling in the same directory: never a fixed name another write could share or clobber.
        handle, name = tempfile.mkstemp(prefix=f".{CANONICAL_NAME}.", suffix=".tmp", dir=target.parent)
        temporary = Path(name)
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return WriteResult(True, str(target), sealed["content_sha256"])
    except Exception as exc:  # noqa: BLE001 - a failed write is reported, never raised into the solver
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        return WriteResult(False, str(target), None, f"{type(exc).__name__}: {exc}")


__all__ = [
    "CANONICAL_NAME", "GAP_REASONS", "LIVE_VIEW", "SCHEMA", "V2_SCHEMA", "V3_SCHEMA", "V4_SCHEMA", "V5_SCHEMA",
    "V6_SCHEMA",
    "WorldModelV2Error", "WriteResult", "canonical_bytes", "content_sha256", "read_world_model", "seal", "validate",
    "validate_v2", "validate_v3", "validate_v4", "validate_v5", "validate_v6", "write_canonical",
]
