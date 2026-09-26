import json
from tools.evaluate_cybernetic_pilot import evaluate


def test_evaluation_counts_execution_records_not_prompt_mentions(tmp_path):
    game=tmp_path/'fixture';game.mkdir()
    records=[{'operation':'agenda','parameters':{'automatic':True}},
             {'operation':'world','parameters':{}}, {'operation':'intent','parameters':{},'error':'invalid'}]
    (game/'queries.jsonl').write_text('\n'.join(json.dumps(x) for x in records))
    (game/'prompt.txt').write_text("virelai('world') "*100)
    (game/'experiments.jsonl').write_text(json.dumps({'event':'INTENT','accepted':True})+'\n'+json.dumps({'event':'OUTCOME','outcome':'CONTRADICTED','question_id':'L1:CONTROL'}))
    result=evaluate(tmp_path)['games'][0]
    assert result['automatic_agendas']==1
    assert result['explicit_operations']=={'world':1,'intent':1}
    assert result['intents']==1 and result['outcomes']=={'CONTRADICTED':1}
    assert len(result['query_errors'])==1
