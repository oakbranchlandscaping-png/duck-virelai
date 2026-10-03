"""Count executed query/experiment records, never prompt echoes or proposed code."""
import argparse
from collections import Counter
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def evaluate(root):
    games=[]
    for path in sorted(root.rglob('queries.jsonl')):
        queries=rows(path); events=rows(path.with_name('experiments.jsonl'))
        automatic=[q for q in queries if q.get('parameters',{}).get('automatic') is True]
        explicit=[q for q in queries if q not in automatic and q.get('operation') != 'briefing']
        intents=[e for e in events if e.get('event')=='INTENT' and e.get('accepted')]
        outcomes=[e for e in events if e.get('event')=='OUTCOME']
        transitions=[e for e in rows(path.with_name('events.jsonl')) if e.get('event')=='TRANSITION']
        games.append({'game':path.parent.name,'actions':len(transitions),
            'automatic_agendas':len(automatic),'explicit_operations':dict(Counter(q.get('operation') for q in explicit)),
            'query_errors':[{'operation':q.get('operation'),'error':q['error']} for q in queries if q.get('error')],
            'query_compute_seconds':sum(q.get('compute_latency_ms',0) for q in queries)/1000,
            'intents':len(intents),'outcomes':dict(Counter(e.get('outcome') for e in outcomes)),
            'question_ids':sorted({e.get('question_id','') for e in outcomes}),
            'non_duck_transitions':sum(e.get('actor')!='DUCK' for e in transitions),
            'level_boundaries':sum(bool(e.get('level_completed')) for e in transitions)})
    return {'schema':'virelai-cybernetic-pilot-evaluation-v1','games':games,
        'limitation':'Counts establish interface uptake, not experiment quality, causal learning or score improvement. Manually review evidence and actual actions.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=evaluate(a.root)
    if not report['games']:raise SystemExit('No executed query logs found')
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
