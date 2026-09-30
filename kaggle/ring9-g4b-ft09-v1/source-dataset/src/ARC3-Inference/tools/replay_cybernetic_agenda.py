import json,time,hashlib,argparse
from pathlib import Path
from tools.replay_continuity_archives import _frames,_read_jsonl
from inference.framework.virelai_runtime import VirelaiRuntime,verify_frame_archive
parser=argparse.ArgumentParser(description="Replay archived observations; never load environment implementations or run an LLM.")
parser.add_argument("--source",type=Path,required=True)
parser.add_argument("--output",type=Path,required=True)
parser.add_argument("--max-transitions",type=int,default=150)
args=parser.parse_args()
base=args.source;out=args.output;out.mkdir(parents=True,exist_ok=True)
samples=set()
rows=[]
for source in sorted(base.iterdir()):
 if not (source/'frames.jsonl').exists() or source.name[:4] not in {'ar25','bp35','lp85','ls20','r11l'}:continue
 frames=_frames(source)[:args.max_transitions+1]; events=[e for e in _read_jsonl(source/'events.jsonl') if e.get('event')=='TRANSITION']
 events=events[:len(frames)-1]
 rt=VirelaiRuntime(game_id=frames[0].game_id);rt.observe_initial(frames[0])
 times=[];sizes=[];checks=[]
 for i,frame in enumerate(frames):
  if i:
   e=events[i-1]
   rt.observe_transition(frame=frame,action_id=int(e.get('action_id') or 0),action_name=e.get('action_name',''),acted_cell=tuple(e['acted_cell']) if e.get('acted_cell') is not None else None,actor=e.get('actor','DUCK'),result={'level':e.get('level_after',1),'level_completed':e.get('level_completed',False),'game_over':e.get('game_over',False),'run_complete':e.get('run_complete',False)})
  start=time.perf_counter();r=rt.query('agenda', {'automatic':True});times.append(time.perf_counter()-start)
  a=r.get('data') or {};samples.add(a.get('text',''));sizes.append(len(a.get('text','').encode()))
  if r.get('error'): print('QUERY ERROR',source.name,i,r['error'],flush=True)
  checks.append(not r.get('error') and a.get('journal_through_step')==i and 0 <= i-a.get('observed_through_step',-100) < 8 and len(rt.transitions)==i)
 row={'game':source.name,'transitions':len(events),'prefix_queries':len(times),'query_seconds':sum(times),'max_query_seconds':max(times),'max_context_utf8_bytes':max(sizes),'prefix_checks_passed':all(checks),'source_integrity':verify_frame_archive(source)['passed'],'source_frames_sha256':hashlib.sha256((source/'frames.bin').read_bytes()).hexdigest()}
 rows.append(row);print(json.dumps(row),flush=True)
 (out/'replay.json').write_text(json.dumps({'results':rows,'complete':False},indent=2))
(out/'replay.json').write_text(json.dumps({'results':rows,'complete':True,'passed':all(r['prefix_checks_passed'] and r['source_integrity'] for r in rows)},indent=2))

(out/'agenda-samples.json').write_text(json.dumps(sorted(samples),indent=2))
