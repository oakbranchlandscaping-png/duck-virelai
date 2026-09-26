from dataclasses import replace
from inference.framework.virelai_agenda import compile_agenda, render_agenda
from inference.framework.virelai_world_model import empty_world_model, Claim, EvidenceRef, WinRecord

def model():
    return empty_world_model(game_id="fixture", observed_through_step=3, levels_observed=[1], current_level=1, source_schema="fixture")

def test_empty_evidence_starts_control_without_goal():
    a = compile_agenda(model())
    assert a == compile_agenda(model())
    assert a["focus"] == "CONTROL" and not a["first_win_observed"]
    assert "EXPLAIN_AND_CARRY" not in [q["stage"] for q in a["questions"]]

def test_candidate_is_not_confirmation_and_contradiction_reopens():
    c = Claim("c", "object has semantic role EGO", "CANDIDATE", "L1", 1, evidence=(EvidenceRef(1,1,1,"moved"),))
    m = replace(model(), claims=(c,))
    assert compile_agenda(m)["questions"][0]["disposition"] == "OPEN"
    assert compile_agenda(m)["focus"] == "COUNTER"
    m = replace(m, claims=(replace(c,status="INFERRED"),))
    assert compile_agenda(m)["focus"] == "COUNTER"
    m = replace(m, claims=(replace(c,status="CONTRADICTED"),))
    assert compile_agenda(m)["focus"] == "CONTROL"

def test_new_level_does_not_inherit_role_confirmation():
    c = Claim("c", "object has semantic role EGO", "INFERRED", "L1", 1, evidence=(EvidenceRef(1,1,1,"moved"),))
    assert compile_agenda(replace(model(),current_level=2,claims=(c,)))["focus"] == "CONTROL"

def test_win_opens_explanation_without_claiming_cause():
    w = WinRecord("w",1,3,"ACTION6",None,(),(),(),0,"UNKNOWN")
    a = compile_agenda(replace(model(),wins=(w,), current_level=2))
    assert a["focus"] == "EXPLAIN_AND_CARRY"
    assert "does not prove its cause" in render_agenda(a)

def test_optional_physics_tool_preserves_native_duck_strategy():
    from inference.agent.tool_agent import _build_system_prompt
    p = _build_system_prompt(tool_output_tokens=1024,virelai_enabled=True)
    assert "You are a coding agent solving a grid-based puzzle game" in p
    assert "Do not invent a goal" not in p
    assert "virelai('physics')" in p


def test_runtime_agenda_uses_real_journal_without_actions(tmp_path):
    from test_virelai_runtime import _frame
    from inference.framework.virelai_runtime import VirelaiRuntime
    rt = VirelaiRuntime(game_id="fixture",artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    before = len(rt.transitions)
    result = rt.query("agenda")
    assert result["data"]["focus"] == "CONTROL"
    assert "VIRELAI EXPLORATION AGENDA" in result["data"]["text"]
    assert len(rt.transitions) == before
    q = rt.query("question", {"id":result["data"]["questions"][0]["id"]})
    assert q["data"]["stage"] == "CONTROL"


def test_optional_context_does_not_automatically_query_agenda():
    from inference.agent.tool_agent import ToolAgent
    agent = object.__new__(ToolAgent)
    agent._summarized_knowledge = {}
    calls = []
    def query(op, params):
        calls.append(op)
        return {"data": {"text": render_agenda(compile_agenda(model()))}}
    agent._virelai_query_callback = query
    prompt = agent._build_user_prompt(0,valid_actions=["MOUSE"])
    assert calls == []
    assert "VIRELAI EXPLORATION AGENDA" not in prompt
    assert "BEFORE EXECUTING NEW ACTIONS YOU MUST ALWAYS GIVE" in prompt
    def broken(op, params):
        raise RuntimeError("fixture")
    agent._virelai_query_callback = broken
    assert "Agenda unavailable" not in agent._build_user_prompt(0,valid_actions=["MOUSE"])


def test_mechanic_questions_close_from_evidence_and_reopen():
    from inference.framework.virelai_world_model import MechanicRule
    from inference.framework.virelai_agenda import agenda_changes
    claim = Claim("effect", "observed change", "OBSERVED", "L1", 2,
                  evidence=(EvidenceRef(1,1,1,"delta"), EvidenceRef(2,1,2,"delta")))
    rule = MechanicRule("m", "ACTION6", None, ("o",), "increase", magnitude="2", levels_observed=(1,), claim_id="effect")
    m = replace(model(),claims=(claim,),mechanics=(rule,))
    a = compile_agenda(m)
    questions = {q["id"]:q for q in a["questions"]}
    assert questions["L1:m:magnitude"]["disposition"] == "CLOSED_BY_DATA"
    assert questions["L1:m:conditions"]["disposition"] == "OPEN"
    b = compile_agenda(replace(m,claims=(replace(claim,status="CONTRADICTED",contradiction_count=1),)))
    assert any(x.startswith("Reopened:") for x in agenda_changes(a,b))
    assert "Magnitude: 2" in render_agenda(a)

def test_win_brief_contains_observed_boundary_not_just_task():
    w = WinRecord("w",1,3,"ACTION6",None,(),(),("candidate relation",),4,"UNKNOWN")
    text = render_agenda(compile_agenda(replace(model(),wins=(w,),current_level=2)))
    assert "4 recorded earlier same-action failures" in text
    assert "Cause: UNKNOWN" in text
    assert "candidate relation" in text
    assert "virelai('lesson', level=1)" in text


def test_full_ontology_survives_strategy_replacement():
    from inference.agent.tool_agent import _build_system_prompt
    from inference.agent.virelai_ontology import ARC_GRID_MULTIVERSE_ONTOLOGY
    assert ARC_GRID_MULTIVERSE_ONTOLOGY in _build_system_prompt(tool_output_tokens=1024, virelai_enabled=True)


def test_old_win_does_not_starve_new_level_control():
    w = WinRecord("w",1,3,"ACTION6",None,(),(),(),0,"UNKNOWN")
    a = compile_agenda(replace(model(),wins=(w,),current_level=2,observed_through_step=10))
    assert a["focus"] == "CONTROL"
    assert any(q["stage"] == "EXPLAIN_AND_CARRY" for q in a["questions"])


def test_automatic_refresh_is_bounded_and_explicit_query_is_current(tmp_path):
    from test_virelai_runtime import _frame
    from inference.framework.virelai_runtime import VirelaiRuntime
    rt = VirelaiRuntime(game_id="fixture",artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    for step in range(1, 19):
        rt.observe_transition(frame=_frame(step % 3), action_id=1, action_name="ACTION1", acted_cell=None, actor="DUCK", result={"level":1})
        a = rt.query("agenda", {"automatic":True})["data"]
        assert a["journal_through_step"] == step
        assert 0 <= a["pending_transitions"] < 8
        if a["pending_transitions"]:
            assert "newer transitions await model refresh" in a["text"]
    a = rt.query("agenda")["data"]
    assert a["pending_transitions"] == 0 and a["observed_through_step"] == 18
    rt.observe_transition(frame=_frame(0), action_id=0, action_name="RESET", acted_cell=None, actor="DUCK", result={"level":1})
    assert rt.query("agenda", {"automatic":True})["data"]["pending_transitions"] == 0


def test_cached_correspondences_equal_uncached_and_cannot_be_mutated():
    import numpy as np
    from virelai_golden.substrate.scan import scan_grid
    from virelai_golden.weave.edge import weave_edge, _cached_weave_edge
    rng = np.random.default_rng(817)
    for _ in range(20):
        a,b = [scan_grid(rng.integers(0,4,(6,6))) for _ in range(2)]
        expected = list(_cached_weave_edge.__wrapped__(a,b))
        actual = weave_edge(a,b)
        assert actual == expected
        actual.clear()
        assert weave_edge(a,b) == expected


def test_witnessed_action_channel_advances_control_without_ego_claim():
    from inference.framework.virelai_world_model import MechanicRule
    claim = Claim("effect", "observed action-bound change", "OBSERVED", "L1", 2,
                  evidence=(EvidenceRef(1,1,1,"moved",action_id=1),))
    rule = MechanicRule("move", "UP", None, ("o",), "object translated north",
                        levels_observed=(1,), claim_id="effect")
    agenda = compile_agenda(replace(model(), claims=(claim,), mechanics=(rule,)))
    control = next(q for q in agenda['questions'] if q['stage'] == 'CONTROL')
    assert control['disposition'] == 'CLOSED_BY_DATA'
    assert control['answer'].startswith('Witnessed offered-action channel')
    assert agenda['focus'] == 'COUNTER'


def test_agenda_bounds_depth_frontier_without_discarding_library():
    from inference.framework.virelai_world_model import MechanicRule
    claims = []
    mechanics = []
    for index in range(100):
        cid = f"c{index}"
        claims.append(Claim(cid, "observed change", "OBSERVED", "L1", 1,
                            evidence=(EvidenceRef(index+1,1,index+1,"delta"),)))
        mechanics.append(MechanicRule(f"m{index}", "MOUSE", None, (f"o{index}",),
                                      "remote rewrite", levels_observed=(1,), claim_id=cid))
    agenda = compile_agenda(replace(model(), claims=tuple(claims), mechanics=tuple(mechanics)))
    assert agenda['questions_total_unbounded'] > len(agenda['questions'])
    assert agenda['questions_frontier_truncated'] is True
    assert len([q for q in agenda['questions'] if q['stage'] == 'DEPTH']) <= 24
def test_role_subtree_requires_current_object_and_retains_uncertainty():
    from inference.framework.virelai_world_model import ObjectInstance
    c = Claim("c", "object has semantic role LEVER", "CANDIDATE", "L1", 1, evidence=(EvidenceRef(3,1,3,"press"),))
    obj = ObjectInstance("o","t",1,("w",),0,3,True,(1,2,1,2),(4,),1,("c",))
    a = compile_agenda(replace(model(),claims=(c,),objects=(obj,)))
    q = next(q for q in a["questions"] if q["subject"] == "o")
    assert q["disposition"] == "OPEN" and "every affected object" in q["question"]
    a = compile_agenda(replace(model(),claims=(c,),objects=(replace(obj,last_seen_step=2),)))
    assert not any(q["subject"] == "o" for q in a["questions"])


def test_disappeared_object_is_not_reported_as_present():
    from inference.framework.virelai_world_model import from_semantic_library
    payload = {"game_id":"fixture","observed_nodes":4,"observed_transitions":3,"levels_observed":[1],
               "segments":[{"level":1,"entities":[{"handle":"gone","born_node":0,"last_seen_node":2,
                            "current":{"integer_class":4,"cells":1,"bbox":[1,1,1,1]}}]}]}
    assert not from_semantic_library(payload).objects[0].present
