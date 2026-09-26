import json
from dataclasses import replace
from test_virelai_runtime import _frame
from inference.framework.virelai_runtime import VirelaiRuntime
from inference.framework.virelai_experiments import evaluate


def test_intent_records_and_evaluates_without_promoting_claims(tmp_path):
    rt = VirelaiRuntime(game_id='fixture', artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    a = rt.query('agenda')['data']
    q = a['questions'][0]['id']
    result = rt.query('intent', {'question_id':q,'action':{'action':'MOUSE','row':1,'col':1},
                                 'scope_cell':[1,1],'prediction':'CHANGED'})
    assert result['data']['accepted'] and len(rt.transitions) == 0
    intent = rt._experiment_intent
    rt.observe_transition(frame=_frame(2), action_id=6, action_name='MOUSE(row=1, col=1)',
                          acted_cell=(1,1), actor='DUCK',result={})
    outcome = rt.query('experiments')['data'][-1]
    assert outcome['outcome'] == 'SUPPORTED' and not outcome['question_closed']
    assert rt._experiment_intent is None
    assert 'Last experiment E1' in rt.query('agenda')['data']['text']
    assert evaluate(replace(intent,prediction='UNCHANGED'),rt.transitions[-1])['outcome'] == 'CONTRADICTED'
    assert evaluate(replace(intent,acted_cell=(0,0)),rt.transitions[-1])['outcome'] == 'NOT_ATTEMPTED'
    assert evaluate(intent,replace(rt.transitions[-1],level_completed=True))['outcome'] == 'NOT_EVALUATED'
    assert evaluate(replace(intent,scope_cell=(99,99)),rt.transitions[-1])['outcome'] == 'NOT_EVALUATED'
    rows=[json.loads(x) for x in (tmp_path/'fixture/experiments.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['INTENT','OUTCOME']


def test_invalid_intent_does_not_replace_valid_intent(tmp_path):
    rt=VirelaiRuntime(game_id='fixture',artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    q=rt.query('agenda')['data']['questions'][0]['id']
    rt.query('intent',{'question_id':q,'action':{'action':'UP'}})
    held=rt._experiment_intent
    rt.query('intent',{'question_id':'invented','action':{'action':'MOUSE','row':1,'col':1}})
    assert rt._experiment_intent == held and not rt.transitions


def test_sandbox_intent_and_action_follow_real_bridge(tmp_path):
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    rt=VirelaiRuntime(game_id='bridge',artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    state={"current_frame":None,"history":[],"valid_actions":["MOUSE"],"last_action_result":{}}
    def act(actions):
        assert len(actions) == 1
        rt.observe_transition(frame=_frame(2),action_id=6,action_name='MOUSE(row=1, col=1)',
                              acted_cell=(1,1),actor='DUCK',result={})
        return {"state":state,"action_result":{"executed":True}}
    result=run_sandboxed_python(timeout_seconds=10, initial_state=state, action_handler=act,
        virelai_handler=rt.query,code="""
a = virelai('agenda')['data']
virelai('intent', question_id=a['questions'][0]['id'], action={'action':'MOUSE','row':1,'col':1}, prediction='CHANGED', scope_cell=[1,1])
action([{'action':'MOUSE','row':1,'col':1}])
print(virelai('experiments')['data'][-1]['outcome'])
""")
    assert 'SUPPORTED' in result['stdout'], result
    assert len(rt.transitions)==1


def test_bare_virelai_call_is_visible_and_invalid_action_is_displayed(tmp_path):
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    rt = VirelaiRuntime(game_id='bridge', artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    state = {"current_frame":None,"history":[],"valid_actions":["UP"],"last_action_result":{}}
    visible = run_sandboxed_python(timeout_seconds=10, initial_state=state,
        action_handler=lambda actions: {}, virelai_handler=rt.query,
        code="virelai('overview')")
    assert 'virelai-query-v2' in visible['stdout']
    invalid = run_sandboxed_python(timeout_seconds=10, initial_state=state,
        action_handler=lambda actions: {}, virelai_handler=rt.query,
        code="a=virelai('agenda'); virelai('intent', question_id=a['data']['questions'][0]['id'], action={'action':'MOUSE','row':1,'col':1})")
    assert 'not currently offered' in invalid['stdout']


def test_scoped_feedback_separates_unchanged_target_from_remote_effect(tmp_path):
    rt = VirelaiRuntime(game_id='fixture', artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    q = rt.query('agenda')['data']['questions'][0]['id']
    rt.query('intent', {'question_id':q, 'action':{'action':'MOUSE','row':0,'col':0},
                        'scope_cell':[0,0], 'prediction':'CHANGED'})
    rt.observe_transition(frame=_frame(2), action_id=6, action_name='MOUSE(row=0, col=0)',
                          acted_cell=(0,0), actor='DUCK', result={})
    out = rt.query('experiments')['data'][-1]
    assert out['outcome'] == 'CONTRADICTED'
    assert out['tested_scope'] == 'cell (0, 0)'
    assert out['other_cell_delta_count'] == 1
    assert 'Other cells changed: 1' in out['observed_summary']


def test_no_change_does_not_claim_inert_or_unreachable(tmp_path):
    rt=VirelaiRuntime(game_id='fixture',artifact_root=tmp_path)
    rt.observe_initial(_frame(0))
    q=rt.query('agenda')['data']['questions'][0]['id']
    rt.query('intent',{'question_id':q,'action':{'action':'MOUSE','row':1,'col':1},'prediction':'CHANGED'})
    rt.observe_transition(frame=_frame(0),action_id=6,action_name='MOUSE(row=1, col=1)',acted_cell=(1,1),actor='DUCK',result={})
    out=rt.query('experiments')['data'][-1]
    assert out['outcome']=='CONTRADICTED' and out['observed']=='UNCHANGED'
    assert out['question_closed'] is False
    assert 'reachability' in out['limitation']
