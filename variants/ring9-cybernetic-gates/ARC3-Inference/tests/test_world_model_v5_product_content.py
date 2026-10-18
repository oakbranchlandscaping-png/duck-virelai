"""WO-PE-03A fail-first tests: schema v5 stores every active product's exact content per level, strictly digested.

Author: Claude (Alpha build seat), 2026-10-15. Interface: ``INTERFACE_WO_PE_03_CLAIMS_KEYS_GRADER_v2`` §9; Sol's review
of the PE-03 design (D15) and its §11 acceptance list.

Two kinds of test, kept apart in the fail-first record:

* **new behaviour** (``test_v5_*``): fails on ``0779858``, where there is no schema v5, no ``product_content`` chapter
  and no ``product_content`` module;
* **compatibility guards** (``test_guard_*``): pass on ``0779858`` and must still pass: v1-v4 artifacts read unchanged,
  and the content never reaches Duck's digest or pages.

The real runs are the production session (real ``ToolAgent``, controller executor, provenance capture) from the PE-02
suite, and the real G4-B / G4-C gate machine on the offline ft09 world.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_world_model_v4_provenance import (  # noqa: F401  (module fixtures are re-registered here)
    _TwoLevelGame, _model_of, _session, controller_session,
)

FIXTURES = Path(__file__).parent / "fixtures"
V5 = "virelai-world-model-v5"
WRITER = "virelai-world-model-v8"  # the writer since WO-G4-DOSSIER-B (B2 revision 2)
ENCODING = "virelai-canonical-json-v1"


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _expected_digest(product) -> str:
    """The digest the interface specifies: full SHA-256 over gate, type, revision, dependencies and payload."""
    return hashlib.sha256(_canonical({
        "gate_id": product.target_id, "product_type": product.product_type, "revision": int(product.revision),
        "dependencies": list(product.dependencies), "payload": json.loads(_canonical(product.payload))})).hexdigest()


def _active(machine) -> dict:
    return {product.product_id: product for product in (
        machine.target_journal.active_product(contract.target_id) for contract in machine.target_registry.ordered())
        if product is not None}


def _assert_captured(level: dict, products: dict) -> None:
    content = level["product_content"]
    assert set(content) == set(level["receipts"]["products"]) == set(products)
    for product_id, product in products.items():
        entry = content[product_id]
        assert entry["status"] == "CAPTURED"
        assert (entry["gate_id"], entry["product_type"], entry["revision"], entry["dependencies"]) == (
            product.target_id, product.product_type, int(product.revision), list(product.dependencies))
        assert _canonical(entry["payload"]) == _canonical(product.payload)  # exact, byte for byte
        assert entry["digest"] == {"algorithm": "sha256", "encoding": ENCODING, "value": _expected_digest(product)}


def _compiled(machine, *, persist_reason="RUN_END"):
    """The H2 compilation of a gate machine (no journal: the chapter is the honest UNAVAILABLE default)."""
    from inference.framework.library_census import ExecutionRecord, compile_world_model
    from inference.framework.world_model_v2 import seal

    board = tuple(tuple(int(cell) for cell in row) for row in machine.ego._initial_grid)
    executed = tuple(str((row.get("action") or {}).get("action") or "") for row in machine.transition_index)
    return seal(compile_world_model(
        machine, ExecutionRecord(board, int(machine.lives.level), tuple(a.action for a in machine.ego.affordances),
                                 executed), game_id="g", run_stem="g_p0", persist_reason=persist_reason,
        frozen_levels=list(getattr(machine, "level_censuses", ()) or ()), reconcile_journal=False))


# ---- 1 · every active product, exactly, at H2 -------------------------------------------------------------------

def test_v5_every_active_product_of_a_real_run_is_captured_exactly_at_h2(controller_session):
    from inference.framework.world_model_v2 import SCHEMA, validate

    model = controller_session.model
    assert SCHEMA == WRITER and model["schema"] == WRITER
    validate(model)
    (level,) = model["levels"]
    _assert_captured(level, _active(controller_session.agent._gate_machine))
    assert len(level["product_content"]) == 5


# ---- 2 · two levels through the real H1 / H2 path --------------------------------------------------------------

@pytest.fixture(scope="module")
def two_level_writes(tmp_path_factory):
    """The production two-level session, keeping every canonical payload written (H1 interim, then H2 final) and
    the products active at the boundary, read from the machine just before the target journal is rebuilt."""
    from inference.agent.tool_agent import _ChatCompletionResult
    from inference.framework import world_model_v2
    from inference.framework.virelai_gates import CyberneticGateMachine

    patch = pytest.MonkeyPatch()
    writes, boundary = [], []
    original_write = world_model_v2.write_canonical
    patch.setattr(world_model_v2, "write_canonical",
                  lambda payload, directory: writes.append(copy.deepcopy(payload)) or original_write(payload, directory))
    original_advance = CyberneticGateMachine._advance_level

    def advance(self, *args, **kwargs):
        boundary.append({pid: copy.deepcopy(p) for pid, p in _active(self).items()})
        return original_advance(self, *args, **kwargs)

    patch.setattr(CyberneticGateMachine, "_advance_level", advance)
    session, agent, folder = _session(tmp_path_factory.mktemp("v5_two_levels"))
    session.game = _TwoLevelGame()
    agent._controller.g3_choice_handoff = False

    def duck(messages, **kwargs):
        session.solver.max_actions_per_game = session.action_count
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    agent._chat_completion = duck
    session.play()
    patch.undo()
    return SimpleNamespace(writes=writes, boundary=boundary, final=_model_of(folder), agent=agent)


def test_v5_a_two_level_run_keeps_level_one_from_its_boundary_and_captures_level_two_fresh(two_level_writes):
    interim, final = two_level_writes.writes
    assert (interim["manifest"]["persist_reason"], final["manifest"]["persist_reason"]) == ("LEVEL_ADVANCE",
                                                                                            "BUDGET_STOP")
    assert final["schema"] == WRITER and [level["level"] for level in final["levels"]] == [1, 2]
    (at_boundary,) = two_level_writes.boundary
    level_1 = final["levels"][0]
    _assert_captured(level_1, at_boundary)  # level 1's products as they stood before the journal was rebuilt
    assert _canonical(interim["levels"][0]["product_content"]) == _canonical(level_1["product_content"])
    _assert_captured(final["levels"][1], _active(two_level_writes.agent._gate_machine))


# ---- 3 · strict digests -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", [object(), {1, 2}, float("nan"), math.inf, {"when": Path("x")}],
                         ids=["object", "set", "nan", "inf", "path"])
def test_v5_a_digest_refuses_every_non_json_value(value):
    from inference.framework import product_content

    with pytest.raises(product_content.ProductContentError):
        product_content.digest_record(value)
    assert product_content.digest_record(("a", 1)) == product_content.digest_record(["a", 1])


def test_v5_an_unrepresentable_product_is_a_typed_gap_and_still_seals():
    from inference.framework import product_content
    from inference.framework.cybernetic_targeting import MemoryProduct

    good = MemoryProduct("G0-A", "ActionSurface", "G0-ACTION-METADATA", 1, {"answer_id": "G0-A", "x": [1]})
    bad = MemoryProduct("P-BAD", "LeverOrbitSet", "G4.2-LEVER-ORBITS", 2, {"orbits": {3, 4}}, ("G4-REACTIONS",))
    machine = SimpleNamespace(
        target_registry=SimpleNamespace(ordered=lambda: [SimpleNamespace(target_id=p.target_id) for p in (good, bad)]),
        target_journal=SimpleNamespace(active_product=lambda gate: {good.target_id: good, bad.target_id: bad}[gate]))
    content = product_content.capture(machine)
    assert content["G0-A"]["status"] == "CAPTURED"
    entry = content["P-BAD"]
    assert (entry["status"], entry["payload"], entry["digest"], entry["gap"]["reason"]) == (
        "UNREPRESENTABLE", None, None, "PRODUCT_CONTENT_UNREPRESENTABLE")
    assert (entry["gate_id"], entry["product_type"], entry["revision"], entry["dependencies"]) == (
        "G4.2-LEVER-ORBITS", "LeverOrbitSet", 2, ["G4-REACTIONS"])


# ---- 4 · disagreement anywhere fails validation ----------------------------------------------------------------

def _tamper(model, mutation):
    level = model["levels"][0]
    content, receipts = level["product_content"], level["receipts"]["products"]
    pid = sorted(content)[0]
    entry = content[pid]
    if mutation == "payload":
        entry["payload"] = {**entry["payload"], "tampered": True}
    elif mutation == "revision":
        entry["revision"] += 1
    elif mutation == "dependencies":
        entry["dependencies"] = list(entry["dependencies"]) + ["G9-NOWHERE"]
    elif mutation == "digest":
        entry["digest"] = {**entry["digest"], "value": "0" * 64}
    elif mutation == "digest_encoding":
        entry["digest"] = {**entry["digest"], "encoding": "json-default-str"}
    elif mutation == "receipt_type":
        receipts[pid] = {**receipts[pid], "product_type": "Another"}
    elif mutation == "receipt_gate":
        receipts[pid] = {**receipts[pid], "gate_id": "G9-NOWHERE"}
    elif mutation == "receipt_revision":
        receipts[pid] = {**receipts[pid], "revision": receipts[pid]["revision"] + 1}
    elif mutation == "legacy_receipt_hash":
        receipts[pid] = {**receipts[pid], "payload_sha256": "0" * 64}
    elif mutation == "missing_entry":
        del content[pid]
    elif mutation == "extra_entry":
        content["P-EXTRA"] = copy.deepcopy(entry)
    elif mutation == "product_answers_type":
        level["product_answers"][pid] = {**level["product_answers"][pid], "product_type": "Another"}
    elif mutation == "unrepresentable_with_payload":
        content[pid] = {**entry, "status": "UNREPRESENTABLE",
                        "gap": {"reason": "PRODUCT_CONTENT_UNREPRESENTABLE", "detail": "x"}}
    return model


@pytest.mark.parametrize("mutation", [
    "payload", "revision", "dependencies", "digest", "digest_encoding", "receipt_type", "receipt_gate",
    "receipt_revision", "legacy_receipt_hash", "missing_entry", "extra_entry", "product_answers_type",
    "unrepresentable_with_payload"])
def test_v5_any_disagreement_between_content_receipt_and_origins_fails_validation(controller_session, mutation):
    from inference.framework.world_model_v2 import WorldModelV2Error, content_sha256, validate

    model = _tamper(copy.deepcopy(controller_session.model), mutation)
    model["content_sha256"] = content_sha256(model)  # a forger who recomputes the model hash
    with pytest.raises((WorldModelV2Error, ValueError)):
        validate(model)


# ---- 5-6 · graded predictions, the law test and record-derived relations, byte for byte -------------------------

def test_v5_graded_g4b_predictions_and_the_g4c_law_test_survive_byte_for_byte():
    from test_g4b_relations import _take
    from test_g4c_law import LAW, RELATIONS, _described, _law
    from test_g4b_relations import start_g4b

    machine, world = start_g4b()
    _described(machine, world)
    _law(machine, "E0055")
    _take(machine, world)
    relations, law = (machine.target_journal.active_product(gate) for gate in (RELATIONS, LAW))
    model = _compiled(machine)
    content = model["levels"][-1]["product_content"]
    assert {p["status"] for p in content[relations.product_id]["payload"]["predictions"]} >= {"SUPPORTED"}
    assert content[law.product_id]["payload"]["law_test"]["status"] == "SUPPORTED"
    for product in (relations, law):
        assert _canonical(content[product.product_id]["payload"]) == _canonical(product.payload)


def test_v5_record_derived_relations_survive_with_their_record_and_origin():
    from test_world_model_v4_provenance import _record_certified

    machine, product, _effective, _accepted = _record_certified()
    level = _compiled(machine)["levels"][-1]
    entry = level["product_content"][product.product_id]
    assert _canonical(entry["payload"]) == _canonical(product.payload)
    assert entry["payload"]["from_record"]["answer_id"] == entry["payload"]["answer"]["answer_id"]
    origin = level["product_answers"][product.product_id]
    assert (origin["origin"], origin["basis"]) == ("ANSWER_CERTIFIED", "RELATIONS_CERTIFIED_FROM_RECORD")


# ---- 9 · determinism -------------------------------------------------------------------------------------------

def test_v5_two_compilations_are_byte_identical():
    from inference.framework.world_model_v2 import canonical_bytes
    from test_g4b_relations import start_g4b
    from test_g4c_law import _described

    machine, world = start_g4b()
    _described(machine, world)
    first, second = canonical_bytes(_compiled(machine)), canonical_bytes(_compiled(machine))
    assert first == second and json.loads(first)["schema"] == WRITER


# ---- 7-8 · compatibility guards (pass on 0779858 and after) ------------------------------------------------------

def test_guard_frozen_v4_artifact_still_reads():
    from inference.framework.world_model_v2 import WorldModelV2Error, read_world_model

    v4 = json.loads((FIXTURES / "world_model_v4_frozen.json").read_text())  # sealed by 0779858's v4 code
    assert read_world_model(v4)["schema"] == "virelai-world-model-v4"
    tampered = copy.deepcopy(v4)
    tampered["provenance"]["completeness"] = "INCOMPLETE"
    with pytest.raises((WorldModelV2Error, ValueError)):
        read_world_model(tampered)


def test_guard_product_content_never_reaches_ducks_digest_or_pages():
    """The live model carries the content (v5 everywhere); no page, digest line or card renders a payload digest."""
    from g3_no_choice_trace import RECORDS
    from inference.framework.library_view import library_page, live_model, render_library_digest
    from inference.framework.record_replay import load_record, replay

    machine = replay(load_record(RECORDS["carry_v7"]), measure=False).machine
    model = live_model(machine)
    shown = render_library_digest(model) + "".join(
        json.dumps(library_page(model, kind), sort_keys=True)
        for kind in ("levels", "objects", "gaps", "scene", "events", "laws", "dossiers"))
    digests = [entry["digest"]["value"] for level in model.get("levels", ())
               for entry in (level.get("product_content") or {}).values() if entry.get("digest")]
    assert not [value for value in digests if value in shown]
    assert "product_content" not in shown


# ---- revision 2 (Sol, PE-03A review): non-string keys and duplicate product ids fail closed ----------------------

@pytest.mark.parametrize("value", [
    {1: "a"}, {None: "a"}, {True: "a"}, {"outer": {1: "a"}}, {"outer": {None: "a"}}, {"outer": [{"deep": {2.5: "x"}}]},
], ids=["int_top", "none_top", "bool_top", "int_nested", "none_nested", "float_in_list"])
def test_v5_r2_a_non_string_mapping_key_is_refused_never_collapsed(value):
    """``json.dumps`` silently turns ``1`` and ``None`` keys into ``"1"`` and ``"null"``: two different payloads would
    share one stored form. Strict JSON refuses them, at the top level and nested."""
    from types import SimpleNamespace as NS

    from inference.framework import product_content

    with pytest.raises(product_content.ProductContentError, match="key"):
        product_content.digest_record(value)
    with pytest.raises(product_content.ProductContentError):
        product_content.canonical_json(value)
    entry = product_content.entry("G4.2-LEVER-ORBITS", NS(product_id="P", product_type="LeverOrbitSet", revision=1,
                                                          dependencies=(), payload=value))
    assert (entry["status"], entry["payload"], entry["gap"]["reason"]) == ("UNREPRESENTABLE", None,
                                                                          "PRODUCT_CONTENT_UNREPRESENTABLE")


def test_v5_r2_strict_json_still_admits_its_primitives_and_normalises_tuples():
    from inference.framework import product_content

    value = {"s": "x", "i": 1, "f": 1.5, "b": True, "n": None, "l": [1, ("a", 2)], "m": {"k": []}}
    assert product_content.canonical_json(value) == json.dumps(
        {**value, "l": [1, ["a", 2]]}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def test_v5_r2_two_active_contracts_sharing_a_product_id_refuse_the_census():
    """The target journal indexes active products by gate; receipts and content index them by product id. Two gates
    presenting one id must fail closed, naming the id, both gates, both types and both revisions."""
    from inference.framework import product_content
    from inference.framework.cybernetic_targeting import MemoryProduct

    first = MemoryProduct("P-SAME", "LeverEffectAnatomySet", "G4-REACTIONS", 3, {"a": 1})
    second = MemoryProduct("P-SAME", "LeverOrbitSet", "G4.2-LEVER-ORBITS", 7, {"b": 2})
    by_gate = {first.target_id: first, second.target_id: second}
    machine = SimpleNamespace(
        target_registry=SimpleNamespace(ordered=lambda: [SimpleNamespace(target_id=gate) for gate in by_gate]),
        target_journal=SimpleNamespace(active_product=lambda gate: by_gate[gate]))
    with pytest.raises(product_content.ProductContentError) as caught:
        product_content.capture(machine)
    message = str(caught.value)
    for part in ("P-SAME", "G4-REACTIONS", "G4.2-LEVER-ORBITS", "LeverEffectAnatomySet", "LeverOrbitSet",
                 "revision 3", "revision 7"):
        assert part in message, part


def test_v5_r2_a_duplicated_product_id_fails_the_whole_census_not_one_entry():
    """Through ``compile_level``: the census raises, so no model can claim every active product was captured."""
    from inference.framework import product_content
    from inference.framework.cybernetic_targeting import MemoryProduct
    from test_g4b_relations import start_g4b

    machine, _world = start_g4b()
    original = machine.target_journal.active_product
    shared = original("G0-ACTION-METADATA")

    def active(gate):
        if gate == "G1-EGO":  # a second gate presents the G0 product's id
            return MemoryProduct(shared.product_id, "EgoLaw", "G1-EGO", 99, {"law_id": "x"})
        return original(gate)

    machine.target_journal.active_product = active
    with pytest.raises(product_content.ProductContentError, match=shared.product_id):
        _compiled(machine)
