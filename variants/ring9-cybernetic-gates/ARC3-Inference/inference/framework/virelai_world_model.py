"""Canonical, deterministic Virelai world-model schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
import hashlib
import json
from typing import Any, Iterable


WORLD_MODEL_SCHEMA = "virelai-world-model-v1"
CLAIM_STATUSES = frozenset(
    {"OBSERVED", "INFERRED", "CANDIDATE", "CONTRADICTED", "SUPERSEDED", "UNKNOWN"}
)
MECHANIC_STATUSES = frozenset(
    {"OBSERVED", "CANDIDATE", "CONTRADICTED", "SUPERSEDED", "UNKNOWN"}
)


@dataclass(frozen=True, order=True)
class EvidenceRef:
    transition_id: int
    level: int
    step: int
    observation: str
    from_node: int | None = None
    to_node: int | None = None
    action_id: int | None = None


@dataclass(frozen=True)
class Claim:
    claim_id: str
    predicate: str
    status: str
    scope: str
    witness_count: int = 0
    contradiction_count: int = 0
    evidence: tuple[EvidenceRef, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObjectType:
    type_id: str
    integer_classes: tuple[int, ...]
    shape_signature: str
    size_range: tuple[int, int]
    composition: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    levels_observed: tuple[int, ...] = ()
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObjectInstance:
    object_id: str
    type_id: str
    level: int
    worldline_ids: tuple[str, ...]
    born_step: int
    last_seen_step: int
    present: bool
    bbox: tuple[int, int, int, int] | None
    integer_classes: tuple[int, ...]
    cells: int
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateVariable:
    variable_id: str
    owner_id: str
    values_observed: tuple[str, ...]
    current_value: str | None
    ordered: bool = False
    cyclic: bool = False
    endpoints: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class MechanicRule:
    rule_id: str
    trigger_action: str
    trigger_object_type: str | None
    affected_ids: tuple[str, ...]
    transformation: str
    preconditions: tuple[str, ...] = ()
    direction: str | None = None
    magnitude: str | None = None
    period: int | None = None
    endpoint_behavior: str | None = None
    inverse_rule_id: str | None = None
    levels_observed: tuple[int, ...] = ()
    claim_id: str = ""
    # Physics-grammar extension.  These fields describe the rule without
    # changing the immutable observations from which it was compiled.
    subject_ids: tuple[str, ...] = ()
    condition: str | None = None
    phase: str | None = None
    affected_region: tuple[int, int, int, int] | None = None
    witness_transition_ids: tuple[int, ...] = ()
    counterexample_transition_ids: tuple[int, ...] = ()
    scope: str = ""
    status: str = "CANDIDATE"
    supersedes_rule_id: str | None = None
    component_rule_ids: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    class_rewrites: tuple[tuple[int, int, int], ...] = ()
    signed_class_delta: tuple[tuple[int, int], ...] = ()
    decomposition: tuple[str, ...] = ()
    subject_bbox: tuple[int, int, int, int] | None = None
    subject_integer_classes: tuple[int, ...] = ()
    subject_cell_count: int | None = None
    subject_kind: str = "UNRESOLVED_SOURCE"


@dataclass(frozen=True)
class WinRecord:
    win_id: str
    completed_level: int
    transition_id: int
    winning_action: str
    acted_object_id: str | None
    participating_ids: tuple[str, ...]
    preconditions_observed: tuple[str, ...]
    separator_predicates: tuple[str, ...]
    earlier_same_action_failures: int
    causal_status: str
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class LevelDiff:
    from_level: int
    to_level: int
    still_present: tuple[str, ...] = ()
    changed_or_extended: tuple[str, ...] = ()
    new_or_unexplained: tuple[str, ...] = ()
    contradicted_claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorldModel:
    schema: str
    game_id: str
    model_version: int
    observed_through_step: int
    levels_observed: tuple[int, ...]
    current_level: int
    world_mode: str
    object_types: tuple[ObjectType, ...] = ()
    objects: tuple[ObjectInstance, ...] = ()
    state_variables: tuple[StateVariable, ...] = ()
    mechanics: tuple[MechanicRule, ...] = ()
    wins: tuple[WinRecord, ...] = ()
    level_diffs: tuple[LevelDiff, ...] = ()
    claims: tuple[Claim, ...] = ()
    unknowns: tuple[str, ...] = ()
    source_schema: str = ""


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        rows = [_canonical(item) for item in value]
        if isinstance(value, (set, frozenset)):
            rows.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return rows
    return value


def canonical_bytes(model: WorldModel) -> bytes:
    validate_world_model(model)
    return (
        json.dumps(
            _canonical(model),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")


def world_model_from_dict(payload: dict[str, Any]) -> WorldModel:
    """Load the canonical persisted form without weakening schema validation."""
    def evidence(row: dict[str, Any]) -> EvidenceRef:
        return EvidenceRef(**row)

    def claim(row: dict[str, Any]) -> Claim:
        return Claim(
            **{
                **row,
                "evidence": tuple(evidence(item) for item in row.get("evidence", ())),
                "limitations": tuple(row.get("limitations", ())),
            }
        )

    conversions = {
        "object_types": (ObjectType, ("integer_classes", "size_range", "composition", "roles", "levels_observed", "claim_ids")),
        "objects": (ObjectInstance, ("worldline_ids", "integer_classes", "claim_ids", "bbox")),
        "state_variables": (StateVariable, ("values_observed", "endpoints", "claim_ids")),
        "wins": (WinRecord, ("participating_ids", "preconditions_observed", "separator_predicates", "claim_ids")),
        "level_diffs": (LevelDiff, ("still_present", "changed_or_extended", "new_or_unexplained", "contradicted_claim_ids")),
    }

    def convert_rows(key: str) -> tuple[Any, ...]:
        cls, tuple_fields = conversions[key]
        rows = []
        for source in payload.get(key, ()):
            row = dict(source)
            for field in tuple_fields:
                if row.get(field) is not None:
                    row[field] = tuple(row[field])
            rows.append(cls(**row))
        return tuple(rows)

    mechanics = []
    mechanic_tuple_fields = (
        "affected_ids", "preconditions", "levels_observed", "subject_ids",
        "witness_transition_ids", "counterexample_transition_ids",
        "component_rule_ids", "parameters", "class_rewrites",
        "signed_class_delta", "decomposition", "subject_integer_classes",
    )
    for source in payload.get("mechanics", ()):
        row = dict(source)
        for field in mechanic_tuple_fields:
            row[field] = tuple(tuple(item) if isinstance(item, list) else item for item in row.get(field, ()))
        for field in ("affected_region", "subject_bbox"):
            if row.get(field) is not None:
                row[field] = tuple(row[field])
        mechanics.append(MechanicRule(**row))
    model = WorldModel(
        schema=str(payload.get("schema") or ""),
        game_id=str(payload.get("game_id") or ""),
        model_version=int(payload.get("model_version") or 0),
        observed_through_step=int(payload.get("observed_through_step") or 0),
        levels_observed=tuple(payload.get("levels_observed", ())),
        current_level=int(payload.get("current_level") or 0),
        world_mode=str(payload.get("world_mode") or "UNKNOWN"),
        object_types=convert_rows("object_types"),
        objects=convert_rows("objects"),
        state_variables=convert_rows("state_variables"),
        mechanics=tuple(mechanics),
        wins=convert_rows("wins"),
        level_diffs=convert_rows("level_diffs"),
        claims=tuple(claim(item) for item in payload.get("claims", ())),
        unknowns=tuple(payload.get("unknowns", ())),
        source_schema=str(payload.get("source_schema") or ""),
    )
    validate_world_model(model)
    return model


def model_sha256(model: WorldModel) -> str:
    return hashlib.sha256(canonical_bytes(model)).hexdigest()


def with_level_lessons(
    model: WorldModel, lessons: Iterable[dict[str, Any]]
) -> WorldModel:
    """Add observed win boundaries without converting separators into causes."""
    claims = list(model.claims)
    wins: list[WinRecord] = list(model.wins)
    for lesson in sorted(lessons, key=lambda row: int(row.get("completed_level") or 0)):
        level = int(lesson.get("completed_level") or 0)
        transition_id = int(lesson.get("compiled_at_transition") or 0)
        if level < 1 or transition_id < 1:
            continue
        boundary = lesson.get("boundary") or {}
        action = str(boundary.get("winning_action") or "UNKNOWN_ACTION")
        evidence = (
            EvidenceRef(
                transition_id=transition_id,
                level=level,
                step=transition_id,
                observation=f"Level {level} completed on {action}",
                action_id=_action_id_from_name(action),
            ),
        )
        predicate = f"Level {level} ended after {action} at transition {transition_id}"
        claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
        claims.append(
            Claim(
                claim_id=claim_id,
                predicate=predicate,
                status="OBSERVED",
                scope=f"L{level}",
                witness_count=1,
                evidence=evidence,
                limitations=("The boundary is observed; its causal condition is not proven.",),
            )
        )
        contrast = next(iter(lesson.get("contrasts") or ()), {})
        hypotheses = lesson.get("hypotheses") or ()
        separators = tuple(
            str(item.get("claim"))
            for item in hypotheses
            if item.get("claim") and item.get("status") in {"SUPPORTED", "UNTESTED"}
        )
        wins.append(
            WinRecord(
                win_id=f"W-L{level}-T{transition_id}",
                completed_level=level,
                transition_id=transition_id,
                winning_action=action,
                acted_object_id=None,
                participating_ids=(),
                preconditions_observed=tuple(
                    str(item.get("fact"))
                    for item in lesson.get("established") or ()
                    if item.get("fact")
                ),
                separator_predicates=separators,
                earlier_same_action_failures=int(contrast.get("attempts") or 0),
                causal_status="UNKNOWN",
                claim_ids=(claim_id,),
            )
        )
    return replace(
        model,
        wins=tuple(sorted(wins, key=lambda item: (item.completed_level, item.transition_id))),
        claims=tuple(sorted(claims, key=lambda item: item.claim_id)),
        level_diffs=compile_level_diffs(model),
    )


def with_clock_patterns(
    model: WorldModel, patterns: Iterable[dict[str, Any]]
) -> WorldModel:
    """Admit strict visible clock patterns as state variables and rules.

    This adapter preserves the detector's limited claim: a visible class count
    changed in one direction across an action-diverse consecutive suffix.  It
    does not call the process a timer, counter, objective, or hidden state.
    """
    claims = list(model.claims)
    variables = list(model.state_variables)
    mechanics = list(model.mechanics)
    for pattern in patterns:
        level = max(1, int(pattern.get("level") or model.current_level))
        tracked = tuple(pattern.get("tracked_classes") or ())
        steps = tuple(sorted({int(step) for step in pattern.get("witness_steps") or () if int(step) > 0}))
        if not tracked or not steps:
            continue
        classes = tuple(sorted(int(row.get("class_id")) for row in tracked))
        process_seed = f"L{level}|clock|{classes}|{steps}"
        process_id = "P-" + hashlib.sha256(process_seed.encode("utf-8")).hexdigest()[:12]
        predicate = (
            f"Visible class process {classes} changed on every transition in an "
            f"action-diverse suffix of {len(steps)} presses"
        )
        claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
        rate = pattern.get("rate") or {}
        evidence = tuple(
            EvidenceRef(
                transition_id=step,
                level=level,
                step=step,
                observation=(
                    f"action-independent visible process; rate range "
                    f"{rate.get('min')}..{rate.get('max')} cells/action"
                ),
            )
            for step in steps
        )
        claims.append(Claim(
            claim_id=claim_id,
            predicate=predicate,
            status="OBSERVED",
            scope=f"L{level}",
            witness_count=len(evidence),
            evidence=evidence,
            limitations=(str(pattern.get("caveat") or ""),),
        ))
        current = tuple(str(row.get("current_standing")) for row in tracked)
        variables.append(StateVariable(
            variable_id="V-" + hashlib.sha256(f"{process_id}|standing".encode("utf-8")).hexdigest()[:12],
            owner_id=process_id,
            values_observed=tuple(str(value) for value in rate.get("recent") or ()),
            current_value=",".join(current),
            ordered=True,
            endpoints=("0",) if all(str(row.get("direction")) == "decreasing" for row in tracked) else (),
            claim_ids=(claim_id,),
        ))
        mechanics.append(MechanicRule(
            rule_id="M-" + hashlib.sha256(process_seed.encode("utf-8")).hexdigest()[:12],
            trigger_action="ANY_OBSERVED_DUCK_ACTION",
            trigger_object_type=None,
            affected_ids=(process_id,),
            transformation=str(pattern.get("process_kind") or "VISIBLE_PROCESS"),
            direction=",".join(str(row.get("direction")) for row in tracked),
            magnitude=(
                str(rate.get("median")) if rate.get("median") is not None else None
            ),
            endpoint_behavior=(
                "TERMINAL_EXTENT_OBSERVED" if pattern.get("terminal_extent_observed")
                else "TERMINAL_EXTENT_UNOBSERVED"
            ),
            levels_observed=(level,),
            claim_id=claim_id,
            subject_ids=(process_id,),
            condition="CONSECUTIVE_ACTION_DIVERSE_SUFFIX",
            witness_transition_ids=steps,
            scope=f"L{level}",
            status="OBSERVED",
        ))
    return replace(
        model,
        claims=tuple(sorted(claims, key=lambda item: item.claim_id)),
        state_variables=tuple(sorted(variables, key=lambda item: item.variable_id)),
        mechanics=tuple(sorted(mechanics, key=lambda item: item.rule_id)),
    )


def compile_level_diffs(model: WorldModel) -> tuple[LevelDiff, ...]:
    """Compare structural types across consecutive levels; never reuse instances."""
    by_level: dict[int, set[str]] = {level: set() for level in model.levels_observed}
    for item in model.object_types:
        for level in item.levels_observed:
            by_level.setdefault(level, set()).add(item.type_id)
    rows = []
    for left, right in zip(model.levels_observed, model.levels_observed[1:]):
        prior, current = by_level.get(left, set()), by_level.get(right, set())
        rows.append(
            LevelDiff(
                from_level=left,
                to_level=right,
                still_present=tuple(sorted(prior & current)),
                new_or_unexplained=tuple(sorted(current - prior)),
            )
        )
    return tuple(rows)


def query_world_model(
    model: WorldModel, operation: str, identifier: str | None = None, limit: int = 12
) -> dict[str, Any]:
    """Bounded, deterministic read-only views over the canonical model."""
    limit = max(1, min(int(limit), 50))
    if operation == "world":
        return _bounded_view({
            "game_id": model.game_id,
            "current_level": model.current_level,
            "world_mode": model.world_mode,
            "objects": model.objects,
            "mechanics": model.mechanics,
            "wins": model.wins,
            "unknowns": model.unknowns,
        }, limit)
    if operation == "diff":
        return _bounded_view({"level_diffs": model.level_diffs}, limit)
    collections = {
        "object": model.objects,
        "mechanic": model.mechanics,
        "evidence": model.claims,
    }
    if operation not in collections:
        return {"ok": False, "error": "unknown operation"}
    rows = collections[operation]
    if identifier:
        keys = {"object": "object_id", "mechanic": "rule_id", "evidence": "claim_id"}
        row = next((item for item in rows if getattr(item, keys[operation]) == identifier), None)
        return {"ok": row is not None, "data": _canonical(row) if row else None}
    return _bounded_view({operation + "s": rows}, limit)


def transition_briefing(model: WorldModel, entered_level: int) -> str:
    """Automatic briefing sourced exclusively from the canonical model."""
    diff = next((row for row in model.level_diffs if row.to_level == entered_level), None)
    win = next((row for row in reversed(model.wins) if row.completed_level == entered_level - 1), None)
    lines = [
        "VIRELAI WORLD-MODEL UPDATE",
        f"Entered level {entered_level}.",
    ]
    if win:
        lines.append(
            f"Observed prior win: {win.winning_action}; earlier identical-action failures: "
            f"{win.earlier_same_action_failures}. Cause remains {win.causal_status}."
        )
    else:
        lines.append("No prior win record is available.")
    if diff:
        lines.extend((
            f"Structural types seen again: {', '.join(diff.still_present) or 'none'}.",
            f"New or unexplained types: {', '.join(diff.new_or_unexplained) or 'none'}.",
        ))
    lines.append("Prior mechanics remain evidence about the old level; reconfirm their behavior here.")
    return "\n".join(lines)


def _bounded_view(payload: dict[str, Any], limit: int) -> dict[str, Any]:
    rendered: dict[str, Any] = {}
    truncated = False
    for key, value in payload.items():
        if isinstance(value, tuple):
            truncated = truncated or len(value) > limit
            rendered[key] = _canonical(value[:limit])
        else:
            rendered[key] = _canonical(value)
    return {"ok": True, "data": rendered, "truncated": truncated}


def _action_id_from_name(action: str) -> int | None:
    if action.startswith("ACTION"):
        digits = "".join(ch for ch in action[6:] if ch.isdigit())
        return int(digits) if digits else None
    return None


def validate_world_model(model: WorldModel) -> None:
    if model.schema != WORLD_MODEL_SCHEMA:
        raise ValueError(f"unsupported world-model schema: {model.schema}")
    if not model.game_id:
        raise ValueError("world model requires game_id")
    if model.model_version < 1:
        raise ValueError("model_version must be positive")
    if model.current_level < 1:
        raise ValueError("current_level must be positive")
    if tuple(sorted(set(model.levels_observed))) != model.levels_observed:
        raise ValueError("levels_observed must be sorted and unique")
    _require_unique("claim", (item.claim_id for item in model.claims))
    _require_unique("object type", (item.type_id for item in model.object_types))
    _require_unique("object", (item.object_id for item in model.objects))
    _require_unique("state variable", (item.variable_id for item in model.state_variables))
    _require_unique("mechanic", (item.rule_id for item in model.mechanics))
    _require_unique("win", (item.win_id for item in model.wins))
    known_claims = {item.claim_id for item in model.claims}
    for claim in model.claims:
        if claim.status not in CLAIM_STATUSES:
            raise ValueError(f"invalid claim status: {claim.status}")
        if claim.witness_count < 0 or claim.contradiction_count < 0:
            raise ValueError(f"negative evidence count: {claim.claim_id}")
        if claim.status == "OBSERVED" and (
            claim.witness_count < 1 or not claim.evidence
        ):
            raise ValueError(
                f"observed claim lacks a witness and evidence: {claim.claim_id}"
            )
    for rule in model.mechanics:
        if rule.status not in MECHANIC_STATUSES:
            raise ValueError(f"invalid mechanic status: {rule.status}")
        if rule.period is not None and rule.period < 2:
            raise ValueError(f"mechanic period must be >= 2: {rule.rule_id}")
        if any(item < 1 for item in rule.witness_transition_ids):
            raise ValueError(f"invalid mechanic witness transition: {rule.rule_id}")
        if any(item < 1 for item in rule.counterexample_transition_ids):
            raise ValueError(f"invalid mechanic counterexample transition: {rule.rule_id}")
        if rule.status == "OBSERVED" and not rule.witness_transition_ids:
            raise ValueError(f"observed mechanic lacks transition witnesses: {rule.rule_id}")
    for mechanic in model.mechanics:
        if mechanic.status not in MECHANIC_STATUSES:
            raise ValueError(f"invalid mechanic status: {mechanic.status}")
        if mechanic.period is not None and mechanic.period < 2:
            raise ValueError(f"mechanic period must be >= 2: {mechanic.rule_id}")
        if mechanic.status == "OBSERVED" and not mechanic.witness_transition_ids:
            raise ValueError(
                f"observed mechanic lacks transition witnesses: {mechanic.rule_id}"
            )
    for owner, claim_ids in _claim_references(model):
        missing = sorted(set(claim_ids) - known_claims)
        if missing:
            raise ValueError(f"{owner} references unknown claims: {missing}")


def _require_unique(kind: str, identifiers: Iterable[str]) -> None:
    rows = list(identifiers)
    if any(not item for item in rows):
        raise ValueError(f"{kind} identifiers must be non-empty")
    if len(rows) != len(set(rows)):
        raise ValueError(f"duplicate {kind} identifier")


def _claim_references(model: WorldModel) -> Iterable[tuple[str, tuple[str, ...]]]:
    for item in model.object_types:
        yield item.type_id, item.claim_ids
    for item in model.objects:
        yield item.object_id, item.claim_ids
    for item in model.state_variables:
        yield item.variable_id, item.claim_ids
    for item in model.mechanics:
        yield item.rule_id, (item.claim_id,) if item.claim_id else ()
    for item in model.wins:
        yield item.win_id, item.claim_ids


def empty_world_model(
    *,
    game_id: str,
    observed_through_step: int,
    levels_observed: Iterable[int],
    current_level: int,
    source_schema: str,
) -> WorldModel:
    levels = tuple(sorted(set(int(level) for level in levels_observed)))
    return WorldModel(
        schema=WORLD_MODEL_SCHEMA,
        game_id=game_id,
        model_version=1,
        observed_through_step=max(0, int(observed_through_step)),
        levels_observed=levels,
        current_level=max(1, int(current_level)),
        world_mode="UNKNOWN",
        source_schema=source_schema,
        unknowns=("World-specific semantic adapters have not yet admitted claims.",),
    )


def from_semantic_library_metadata(payload: dict[str, Any]) -> WorldModel:
    """Admit only source identity and evidence-boundary facts in schema rung 1."""
    levels = tuple(
        sorted(set(int(level) for level in payload.get("levels_observed") or ()))
    )
    if not levels:
        levels = (1,)
    return empty_world_model(
        game_id=str(payload.get("game_id") or ""),
        observed_through_step=int(payload.get("observed_transitions") or 0),
        levels_observed=levels,
        current_level=max(levels),
        source_schema=str(payload.get("schema") or ""),
    )


def from_semantic_library(payload: dict[str, Any]) -> WorldModel:
    """Compile admitted facts from the semantic library into one world model.

    Object continuity is structural. Source role verdicts remain candidates. An
    action/effect rule becomes OBSERVED only when its exact transition witnesses
    are present; the rule deliberately describes correlation, not unproved
    causation.
    """
    shell = from_semantic_library_metadata(payload)
    objects: list[ObjectInstance] = []
    claims: list[Claim] = []
    type_rows: dict[str, dict[str, Any]] = {}
    for segment in sorted(
        payload.get("segments") or (),
        key=lambda item: (int(item.get("level") or 1), str(item.get("segment") or "")),
    ):
        level = max(1, int(segment.get("level") or 1))
        for entity in sorted(
            segment.get("entities") or (), key=lambda item: str(item.get("handle") or "")
        ):
            handle = str(entity.get("handle") or "")
            current = entity.get("current") or {}
            bbox_value = current.get("bbox")
            bbox = (
                tuple(int(value) for value in bbox_value)
                if isinstance(bbox_value, list) and len(bbox_value) == 4
                else None
            )
            integer_class = int(current.get("integer_class") or 0)
            cells = max(0, int(current.get("cells") or 0))
            signature = _object_signature(integer_class, cells, bbox)
            type_id = "T-" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]
            entity_claims = _candidate_role_claims(entity, level)
            claims.extend(entity_claims)
            objects.append(
                ObjectInstance(
                    object_id=handle,
                    type_id=type_id,
                    level=level,
                    worldline_ids=(str(entity.get("worldline_id")),),
                    born_step=max(0, int(entity.get("born_node") or 0)),
                    last_seen_step=max(0, int(entity.get("last_seen_node") or 0)),
                    present=int(entity.get("last_seen_node") or 0) == int(payload.get("observed_nodes") or 1) - 1,
                    bbox=bbox,
                    integer_classes=(integer_class,),
                    cells=cells,
                    claim_ids=tuple(item.claim_id for item in entity_claims),
                )
            )
            aggregate = type_rows.setdefault(
                type_id,
                {
                    "integer_classes": set(),
                    "shape_signature": signature,
                    "sizes": [],
                    "levels": set(),
                },
            )
            aggregate["integer_classes"].add(integer_class)
            aggregate["sizes"].append(cells)
            aggregate["levels"].add(level)
    object_types = tuple(
        ObjectType(
            type_id=type_id,
            integer_classes=tuple(sorted(row["integer_classes"])),
            shape_signature=row["shape_signature"],
            size_range=(min(row["sizes"]), max(row["sizes"])),
            levels_observed=tuple(sorted(row["levels"])),
        )
        for type_id, row in sorted(type_rows.items())
    )
    state_variables, mechanics, mechanic_claims = _observed_mechanics(payload)
    claims.extend(mechanic_claims)
    observed_modes = {
        str((segment.get("control") or {}).get("kind"))
        for segment in payload.get("segments") or ()
        if str((segment.get("control") or {}).get("kind") or "UNKNOWN") != "UNKNOWN"
    }
    world_mode = next(iter(observed_modes)) if len(observed_modes) == 1 else "MIXED" if observed_modes else "UNKNOWN"
    return WorldModel(
        **{
            **asdict(shell),
            "object_types": object_types,
            "objects": tuple(sorted(objects, key=lambda item: item.object_id)),
            "state_variables": state_variables,
            "mechanics": mechanics,
            "world_mode": world_mode,
            "claims": tuple(sorted(claims, key=lambda item: item.claim_id)),
            "unknowns": (
                "Semantic roles, causal direction, wins, and cross-level identity "
                "have not yet passed their admission gates.",
            ),
        }
    )


def _observed_mechanics(
    payload: dict[str, Any],
) -> tuple[tuple[StateVariable, ...], tuple[MechanicRule, ...], tuple[Claim, ...]]:
    """Admit witnessed action/effect channels without promoting lever labels."""
    variables: list[StateVariable] = []
    mechanics: list[MechanicRule] = []
    claims: list[Claim] = []
    for segment in sorted(
        payload.get("segments") or (),
        key=lambda item: (int(item.get("level") or 1), str(item.get("segment") or "")),
    ):
        level = max(1, int(segment.get("level") or 1))
        lever_model = segment.get("lever_mechanics") or {}
        rows = list(lever_model.get("levers") or ())
        # Self-reactive controls are observationally useful even when no remote
        # partner exists.  Normalize their shape; do not promote them to LEVER.
        rows.extend(
            {
                "lever": row.get("control"),
                "effect_channels": row.get("self_effect_channels") or (),
                "evidence": row.get("evidence") or (),
                "source_kind": row.get("kind") or "SELF_REACTIVE_CONTROL",
            }
            for row in lever_model.get("reactive_controls") or ()
        )
        for source in sorted(rows, key=lambda item: str(item.get("lever") or "")):
            source_id = str(source.get("lever") or "UNNAMED-SOURCE")
            source_kind = str(source.get("source_kind") or source.get("kind") or "VISUAL_OBJECT")
            source_visible = source.get("visible") or {}
            source_bbox_value = source_visible.get("bbox")
            source_bbox = (
                tuple(int(value) for value in source_bbox_value)
                if isinstance(source_bbox_value, (list, tuple)) and len(source_bbox_value) == 4
                else None
            )
            source_classes = tuple(sorted(int(value) for value in source_visible.get("integer_classes") or ()))
            source_cells = source_visible.get("cells")
            evidence_rows = source.get("evidence") or ()
            source_rule_ids: list[str] = []
            source_affected: set[str] = set()
            for channel in sorted(
                source.get("effect_channels") or (),
                key=lambda item: str(item.get("channel") or ""),
            ):
                transitions = channel.get("transitions") or ()
                if int(channel.get("observations") or 0) < 1 or not transitions:
                    continue
                channel_id = str(channel.get("channel") or "CHANNEL")
                evidence = tuple(
                    EvidenceRef(
                        transition_id=int(row.get("right_node") or 0),
                        level=level,
                        step=int(row.get("right_node") or 0),
                        observation=_transition_observation(channel, row),
                        from_node=int(row.get("left_node") or 0),
                        to_node=int(row.get("right_node") or 0),
                        action_id=_action_for_transition(evidence_rows, row),
                    )
                    for row in transitions
                )
                actions = sorted(
                    {item.action_id for item in evidence if item.action_id is not None}
                )
                trigger = (
                    f"ACTION{actions[0]}" if len(actions) == 1 else "OBSERVED_ACTION_SET"
                )
                affected = tuple(sorted(str(x) for x in channel.get("target_worldlines") or ()))
                predicate = (
                    f"During {trigger}, {source_id}/{channel_id} showed "
                    f"{str(channel.get('direction') or 'VISIBLE_CHANGE')} in "
                    f"{', '.join(affected) or 'an observed region'}"
                )
                claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
                claims.append(
                    Claim(
                        claim_id=claim_id,
                        predicate=predicate,
                        status="OBSERVED",
                        scope=f"L{level}",
                        witness_count=len(evidence),
                        evidence=evidence,
                        limitations=(
                            "The action/effect pairing is observed; source identity and causation remain unproven.",
                            str(channel.get("interpretation_limit") or "").strip(),
                        ),
                    )
                )
                rule_seed = f"L{level}|{source_id}|{channel_id}|{predicate}"
                rule_id = "M-" + hashlib.sha256(rule_seed.encode("utf-8")).hexdigest()[:12]
                deltas = tuple(int(x) for x in channel.get("cell_count_deltas") or ())
                typing = dict(channel.get("typing") or {})
                period = typing.get("period")
                bboxes = tuple(
                    tuple(int(value) for value in box)
                    for box in channel.get("affected_regions") or ()
                    if isinstance(box, (list, tuple)) and len(box) == 4
                )
                if not bboxes:
                    box = channel.get("affected_bbox")
                    if isinstance(box, (list, tuple)) and len(box) == 4:
                        bboxes = (tuple(int(value) for value in box),)
                mechanics.append(
                    MechanicRule(
                        rule_id=rule_id,
                        trigger_action=trigger,
                        trigger_object_type=None,
                        affected_ids=affected,
                        transformation=str(
                            typing.get("mechanism") or _channel_transformation(channel)
                        ),
                        preconditions=(str(typing.get("condition")),)
                        if typing.get("condition") else (),
                        direction=str(channel.get("direction") or "VISIBLE_CHANGE"),
                        magnitude=_constant_magnitude(deltas),
                        period=int(period) if period is not None else None,
                        levels_observed=(level,),
                        claim_id=claim_id,
                        subject_ids=(source_id,),
                        condition=str(typing.get("condition"))
                        if typing.get("condition") else None,
                        affected_region=bboxes[0] if len(set(bboxes)) == 1 else None,
                        witness_transition_ids=tuple(
                            sorted({item.transition_id for item in evidence})
                        ),
                        scope=f"L{level}",
                        status="OBSERVED",
                        parameters=tuple(
                            "observed_state_transition=" + json.dumps(row, sort_keys=True, separators=(",", ":"))
                            for row in typing.get("state_transitions") or ()
                        ),
                        subject_bbox=source_bbox,
                        subject_integer_classes=source_classes,
                        subject_cell_count=int(source_cells) if source_cells is not None else None,
                        subject_kind=source_kind,
                    )
                )
                source_rule_ids.append(rule_id)
                source_affected.update(affected)
                values = _channel_values(transitions)
                if values:
                    variable_id = "V-" + hashlib.sha256(
                        f"{rule_id}|values".encode("utf-8")
                    ).hexdigest()[:12]
                    variables.append(
                        StateVariable(
                            variable_id=variable_id,
                            owner_id=affected[0] if affected else rule_id,
                            values_observed=values,
                            current_value=values[-1],
                            ordered=bool(deltas) and (all(x > 0 for x in deltas) or all(x < 0 for x in deltas)),
                            claim_ids=(claim_id,),
                        )
                    )
            joint = source.get("joint_transformation") or {}
            joint_steps = tuple(
                sorted({int(step) for step in joint.get("witness_steps") or () if int(step) > 0})
            )
            if joint_steps and source_rule_ids:
                kind = str(joint.get("kind") or "COORDINATED_VISIBLE_TRANSFORMATION")
                predicate = (
                    f"During presses attributed to {source_id}, {len(source_affected)} visible "
                    f"channels participated in one {kind}"
                )
                claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
                action_by_right = {
                    int(row.get("right_node") or 0): int(row.get("action_id"))
                    for row in evidence_rows
                    if row.get("right_node") is not None and row.get("action_id") is not None
                }
                joint_evidence = tuple(
                    EvidenceRef(
                        transition_id=step,
                        level=level,
                        step=step,
                        observation=(
                            f"{kind}; joint pixel arithmetic preserved press {step} as one event"
                        ),
                        action_id=action_by_right.get(step),
                    )
                    for step in joint_steps
                )
                claims.append(Claim(
                    claim_id=claim_id,
                    predicate=predicate,
                    status="OBSERVED",
                    scope=f"L{level}",
                    witness_count=len(joint_evidence),
                    evidence=joint_evidence,
                    limitations=(str(joint.get("limitations") or ""),),
                ))
                counts = joint.get("changed_cells_per_press") or {}
                rule_id = "M-" + hashlib.sha256(
                    f"L{level}|{source_id}|joint|{kind}".encode("utf-8")
                ).hexdigest()[:12]
                mechanics.append(MechanicRule(
                    rule_id=rule_id,
                    trigger_action=(
                        f"ACTION{joint_evidence[0].action_id}"
                        if joint_evidence[0].action_id is not None else "ATTRIBUTED_CONTROL_ACTION"
                    ),
                    trigger_object_type=None,
                    affected_ids=tuple(sorted(source_affected)),
                    transformation=kind,
                    magnitude=str(counts.get("median")) if counts.get("median") is not None else None,
                    period=int(joint["period"]) if joint.get("period") is not None else None,
                    levels_observed=(level,),
                    claim_id=claim_id,
                    subject_ids=(source_id,),
                    condition="SAME_ATTRIBUTED_CONTROL",
                    witness_transition_ids=joint_steps,
                    scope=f"L{level}",
                    status="OBSERVED",
                    component_rule_ids=tuple(sorted(source_rule_ids)),
                    parameters=(
                        f"support_union_cells={int(joint.get('support_union_cells') or 0)}",
                        f"component_count={int(joint.get('component_count') or 0)}",
                        f"class_multiset_conserved_each_press={bool(joint.get('class_multiset_conserved_each_press'))}",
                        f"rewrite_table_repeats_exactly={bool(joint.get('rewrite_table_repeats_exactly'))}",
                        f"rewrite_is_functional_substitution={bool(joint.get('rewrite_is_functional_substitution'))}",
                    ),
                    class_rewrites=tuple(
                        (
                            int(row.get("before_class")),
                            int(row.get("after_class")),
                            int(row.get("cells") or 0),
                        )
                        for row in joint.get("common_class_rewrites") or ()
                    ),
                    signed_class_delta=tuple(
                        (int(row[0]), int(row[1]))
                        for row in joint.get("common_signed_class_delta") or ()
                    ),
                    decomposition=tuple(
                        _render_decomposition_row(row)
                        for row in joint.get("decomposition") or ()
                    ),
                    subject_bbox=source_bbox,
                    subject_integer_classes=source_classes,
                    subject_cell_count=int(source_cells) if source_cells is not None else None,
                    subject_kind=source_kind,
                ))

        # A repeated opposed-direction bundle is a relation between controls,
        # not another visual object.  Preserve it as its own witnessed rule.
        for bundle in lever_model.get("shared_controls") or ():
            subjects = tuple(
                str(value) for value in (bundle.get("lever_a"), bundle.get("lever_b"))
                if value
            )
            targets = tuple(
                sorted(str(row.get("target")) for row in bundle.get("affected_targets") or ()
                       if row.get("target"))
            )
            if len(subjects) != 2 or not targets:
                continue
            witness_steps = tuple(sorted({
                int(step)
                for row in bundle.get("affected_targets") or ()
                for key in ("lever_a_witness_steps", "lever_b_witness_steps")
                for step in row.get(key) or ()
            }))
            evidence = tuple(EvidenceRef(
                transition_id=step, level=level, step=step,
                observation="One member of the paired controls changed a shared visible target",
            ) for step in witness_steps)
            witness_count = len(witness_steps)
            predicate = (
                f"{subjects[0]} and {subjects[1]} repeatedly changed "
                f"{', '.join(targets)} in opposite directions"
            )
            claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
            claims.append(Claim(
                claim_id=claim_id,
                predicate=predicate,
                status="OBSERVED" if evidence else "CANDIDATE",
                scope=f"L{level}",
                witness_count=witness_count,
                evidence=evidence,
                limitations=(str(bundle.get("interpretation_limit") or ""),),
            ))
            rule_id = "M-" + hashlib.sha256(
                f"L{level}|{predicate}".encode("utf-8")
            ).hexdigest()[:12]
            mechanics.append(MechanicRule(
                rule_id=rule_id,
                trigger_action="OBSERVED_CONTROL_PAIR",
                trigger_object_type=None,
                affected_ids=targets,
                transformation="OPPOSED_DIRECTION_CONTROL_BUNDLE",
                levels_observed=(level,),
                claim_id=claim_id,
                subject_ids=subjects,
                witness_transition_ids=witness_steps,
                scope=f"L{level}",
                status="OBSERVED" if evidence else "CANDIDATE",
                subject_kind="CONTROL_RELATION",
            ))
    return (
        tuple(sorted(variables, key=lambda item: item.variable_id)),
        tuple(sorted(mechanics, key=lambda item: item.rule_id)),
        tuple(sorted(claims, key=lambda item: item.claim_id)),
    )


def _action_for_transition(rows: Iterable[dict[str, Any]], transition: dict[str, Any]) -> int | None:
    left = int(transition.get("left_node") or 0)
    right = int(transition.get("right_node") or 0)
    actions = sorted(
        {
            int(row["action_id"])
            for row in rows
            if int(row.get("left_node") or 0) == left
            and int(row.get("right_node") or 0) == right
            and row.get("action_id") is not None
        }
    )
    return actions[0] if len(actions) == 1 else None


def _transition_observation(channel: dict[str, Any], row: dict[str, Any]) -> str:
    return (
        f"class/count/anchor changed from {row.get('before')} to {row.get('after')} "
        f"within bbox {channel.get('affected_bbox')}"
    )


def _channel_transformation(channel: dict[str, Any]) -> str:
    return (
        f"{str(channel.get('direction') or 'VISIBLE_CHANGE')}; "
        f"bbox={channel.get('affected_bbox')}; "
        f"class_before={channel.get('integer_class_before')}"
    )


def _constant_magnitude(deltas: tuple[int, ...]) -> str | None:
    return str(deltas[0]) if deltas and len(set(deltas)) == 1 else None


def _channel_values(transitions: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    values: list[str] = []
    for row in transitions:
        before = row.get("before")
        after = row.get("after")
        for value in (before, after):
            if not isinstance(value, list) or len(value) < 2 or value[1] is None:
                continue
            rendered = str(int(value[1]))
            if not values or values[-1] != rendered:
                values.append(rendered)
    return tuple(values)


def _render_decomposition_row(row: dict[str, Any]) -> str:
    """Store one derived sub-transformation deterministically without a mutable dict."""
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def _candidate_role_claims(entity: dict[str, Any], level: int) -> tuple[Claim, ...]:
    """Preserve detector output as candidates until an external role gate passes."""
    handle = str(entity.get("handle") or "")
    results = []
    for role in sorted(entity.get("roles") or (), key=lambda item: str(item.get("role") or "")):
        role_name = str(role.get("role") or "UNKNOWN")
        predicate = f"{handle} has semantic role {role_name}"
        claim_id = "C-" + hashlib.sha256(predicate.encode("utf-8")).hexdigest()[:12]
        evidence = tuple(
            sorted(
                (
                    EvidenceRef(
                        transition_id=int(item.get("right_node") or 0),
                        level=level,
                        step=int(item.get("right_node") or 0),
                        observation=f"source detector witness for role {role_name}",
                        from_node=int(item.get("left_node") or 0),
                        to_node=int(item.get("right_node") or 0),
                        action_id=(
                            int(item["action_id"])
                            if item.get("action_id") is not None
                            else None
                        ),
                    )
                    for item in role.get("witnesses") or ()
                ),
                key=lambda item: (
                    item.transition_id,
                    item.from_node or 0,
                    item.action_id or 0,
                ),
            )
        )
        results.append(
            Claim(
                claim_id=claim_id,
                predicate=predicate,
                status="CANDIDATE",
                scope=f"L{level}",
                witness_count=max(int(role.get("witness_count") or 0), len(evidence)),
                evidence=evidence,
                limitations=tuple(
                    item
                    for item in (
                        "Source role detector has not passed an external fixture gate.",
                        str(role.get("limitations") or "").strip(),
                    )
                    if item
                ),
            )
        )
    return tuple(results)


def _object_signature(
    integer_class: int,
    cells: int,
    bbox: tuple[int, int, int, int] | None,
) -> str:
    if bbox is None:
        dimensions = "unknown"
    else:
        dimensions = f"{bbox[2] - bbox[0] + 1}x{bbox[3] - bbox[1] + 1}"
    return f"class={integer_class};cells={cells};bbox={dimensions}"
