"""Export only allowlisted fields; raw provider/account/extension payloads stay local."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

src=Path(sys.argv[1])
dest=Path(sys.argv[2])
dest.mkdir(parents=True,exist_ok=True)

def response(value):
    raw=value.get('response',{})
    result=raw.get('result',{})
    out={k:value[k] for k in ('text','seconds','updates') if k in value}
    out['result']={k:result[k] for k in ('protocolVersion','sessionId','stopReason') if k in result}
    if 'agentCapabilities' in result:
        caps=result['agentCapabilities']
        out['result']['agentCapabilities']={k:caps[k] for k in ('loadSession','promptCapabilities','sessionCapabilities','mcpCapabilities') if k in caps}
    if 'modes' in result:
        out['result']['modes']={'currentModeId':result['modes'].get('currentModeId'),'availableModes':[{k:m[k] for k in ('id','name','description') if k in m} for m in result['modes'].get('availableModes',[])]}
    if 'error' in raw:
        out['error']={k:raw['error'][k] for k in ('code','message') if k in raw['error']}
    return out

records={}
for name in ('grok','claude','codex','agy','grok-native-control','codex-control'):
    d=json.loads((src/'results'/f'{name}.json').read_text())
    record={k:d[k] for k in ('harness','transport','driver','started_utc','status','error','permission_requests','denied_file_exists','instruction_marker_first','memory_second','read_evidence','exit_code_after_cleanup','elapsed_seconds','hook_events','external_exists','exit_code','returncode','timed_out','text','marker_seen','project_trusted','local_instruction_paths','local_hook_count') if k in d}
    record['steps']={}
    for key,value in d.get('steps',{}).items():
        if 'response' in value:
            record['steps'][key]=response(value)
        elif 'result' in value:
            result=value['result'].get('result',{})
            record['steps'][key]={'seconds':value.get('seconds'),'events':value.get('events'),'result':{k:result[k] for k in ('conversation_id','status','response','duration_seconds','num_turns') if k in result}}
        else:
            record['steps'][key]=value
    if 'artifact_evidence' in d:
        record['artifact_evidence']={k:v for k,v in d['artifact_evidence'].items() if k in ('input.txt','denied.txt')}
    records[name]=record
(dest/'observations.json').write_text(json.dumps({'schema':'acp-spike-observations/1','platform':'macOS arm64','scope':'2026-09-20 local bounded experiment; not production qualification','observations':records},indent=2)+'\n')

traces=[]
for name in ('grok','claude','codex','codex-control'):
    rows=[json.loads(x) for x in (src/'results'/f'{name}-wire.jsonl').read_text().splitlines()]
    for row in rows:
        msg=row['message']
        if not isinstance(msg,dict):
            continue
        method=msg.get('method')
        event=None
        if method=='session/request_permission':
            params=msg['params']
            tc=params.get('toolCall',{})
            event={'method':method,'id':msg['id'],'sessionId':params.get('sessionId'),'toolCall':{k:tc[k] for k in ('toolCallId','title','kind','name','locations') if k in tc},'options':params.get('options')}
        elif row['direction']=='send' and 'outcome' in msg.get('result',{}):
            event={'id':msg['id'],'result':msg['result']}
        elif method=='session/cancel':
            event={'method':method,'params':msg['params']}
        elif method=='session/update':
            u=msg.get('params',{}).get('update',{})
            if u.get('sessionUpdate') in ('tool_call','tool_call_update'):
                event={'method':method,'update':{k:u[k] for k in ('sessionUpdate','toolCallId','title','name','kind','status') if k in u}}
                ro=u.get('rawOutput')
                if isinstance(ro,dict) and ro.get('formatted_output')=='ACP_READ_EVIDENCE_913\n':
                    event['update']['rawOutput']=ro
        if event:
            traces.append({'harness':name,'elapsed_seconds':row['elapsed_seconds'],'direction':row['direction'],'message':event})
(dest/'protocol-evidence.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in traces))

drivers={}
for name in ('driver','retry-driver'):
    raw=(src/f'{name}-stdout.json').read_text()
    d=json.loads(raw) if raw.strip() else {}
    drivers[name]={'process':json.loads((src/f'{name}-result.json').read_text()),'result':{k:d[k] for k in ('text','stopReason','sessionId','num_turns','total_cost_usd','usage') if k in d}}
    if not raw.strip():
        drivers[name]['diagnostic']=(src/f'{name}-stderr.txt').read_text().strip()
        drivers[name]['interpretation']='Driver reached its max-turn cap; target control result files completed and were inspected independently. No successful final driver response is claimed.'
(dest/'grok-driver-evidence.json').write_text(json.dumps(drivers,indent=2)+'\n')
for f in ('probe.py','retry.py','run-driver.py','capture-evidence.py'):
    shutil.copy2(src/f,dest/f)
shutil.copy2(src/'adapters/package.json',dest/'package.json')
# npm on this machine wrote prefix-relative keys against the invoking checkout.
# Preserve the observed lock and derive a portable reproduction lock without
# changing any dependency version, resolved URL or integrity value.
lock=json.loads((src/'adapters/package-lock.json').read_text())
shutil.copy2(src/'adapters/package-lock.json',dest/'observed-package-lock.json')
deps=json.loads((dest/'package.json').read_text())['dependencies']
packages={'':{'dependencies':deps}}
for key,value in lock['packages'].items():
    marker='/adapters/node_modules/'
    if marker in key:
        packages['node_modules/'+key.split(marker,1)[1]]=value
    elif key.startswith('node_modules/') and not value.get('dev'):
        packages[key]=value
portable={'name':'acp-compatibility-spike','lockfileVersion':3,'requires':True,'packages':packages}
(dest/'package-lock.json').write_text(json.dumps(portable,indent=2)+'\n')
manifest={'schema':'acp-spike-manifest/1','date':'2026-09-20','versions':{'grok':'1.0.34 (3736acbc8658)','installed_claude_cli':'2.1.278 (inventoried, not adapter runtime)','claude_acp':'0.79.0','claude_agent_sdk':'0.3.274','codex_acp':'1.12.0','codex_cli':'0.155.1 via CODEX_PATH','agy':'1.2.7','node':'22.22.2'},'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file() and p.name!='manifest.json'},'limits':{'prompt_seconds':70,'initialize_seconds':30,'new_seconds':40,'load_seconds':35,'consumed_output_bytes':2097152,'driver_seconds':900},'limitations':['Queue bytes and unterminated input line are not bounded before read: experiment only','Process-group cleanup on macOS; no descendant or other-platform proof','Protocol progress/completion is distinct from pack ownership/handback proof']}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Exported six observations, minimal protocol traces and driver provenance without provider/account inventories.')
