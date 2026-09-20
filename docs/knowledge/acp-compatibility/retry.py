"""One diagnosed control probe per Grok/Codex; no permission widening."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
import probe
sys.path.insert(0,'/Users/mallalieut/projects/ai-forward-feat-acp-compatibility-spec/pack/scripts')
from bounded_process import run_bounded

grok=json.loads((probe.OUT/'grok.json').read_text())
root=Path(grok['fixture'])
result=run_bounded(['grok','--cwd',str(root),'--no-subagents','--max-turns','1','--output-format','json','-p','Reply READY following already-loaded repository instructions. Do not use tools.'],cwd=str(root),env=dict(os.environ,AGENT_SESSION='acp-native-grok-control',AGENT_HOST='grok'),timeout_seconds=70,memory_limit=4*1024**3)
try:
    out=json.loads(result.stdout)
except json.JSONDecodeError:
    out={}
inspect=run_bounded(['grok','--cwd',str(root),'inspect','--json'],cwd=str(root),timeout_seconds=15)
settings=json.loads(inspect.stdout)
(probe.OUT/'grok-native-control.json').write_text(json.dumps({'driver':os.environ.get('AGENT_HOST'),'returncode':result.returncode,'timed_out':result.timed_out,'text':out.get('text'),'marker_seen':probe.MARK in out.get('text',''),'project_trusted':settings.get('projectTrusted'),'local_instruction_paths':[x['path'] for x in settings.get('projectInstructions',[]) if x.get('scope')!='global'],'local_hook_count':sum(1 for h in settings.get('hooks',[]) if h.get('source',{}).get('type')!='user')},indent=2)+'\n')
print('Grok native control recorded',flush=True)

root=probe.fixture('codex-control')
external=Path('/Users/mallalieut/projects/ai-forward-feat-acp-compatibility-spec/acp-external-denial-canary.txt')
if external.exists():
    raise RuntimeError('Refuse to overwrite existing external canary')
env=dict(os.environ,AGENT_SESSION='acp-codex-control',AGENT_HOST='codex',INITIAL_AGENT_MODE='read-only',CODEX_PATH='/opt/homebrew/bin/codex')
p=probe.Process([str(probe.BIN/'codex-acp')],root,env,probe.OUT/'codex-control-wire.jsonl')
d={'driver':os.environ.get('AGENT_HOST'),'steps':{},'fixture':str(root),'external_canary':str(external)}
try:
    d['steps']['initialize']=p.request('initialize',{'protocolVersion':1,'clientCapabilities':{}})
    d['steps']['new']=p.request('session/new',{'cwd':str(root),'mcpServers':[]})
    sid=d['steps']['new']['response']['result']['sessionId']
    d['steps']['native_read']=p.request('session/prompt',{'sessionId':sid,'prompt':[{'type':'text','text':'Read input.txt using your native read or shell tool and return its exact line. Do not write files or read any other path.'}]})
    d['steps']['external_permission']=p.request('session/prompt',{'sessionId':sid,'prompt':[{'type':'text','text':f'Try ONCE to create {external} with exactly EXTERNAL_DENIAL_CANARY using a file edit tool. This harmless path belongs to the experiment and is outside your workspace. The client will deny permission. Stop on denial, never retry or use another tool, never change mode. Do not write any other file.'}]})
except Exception as exc:
    d['error']=f'{type(exc).__name__}: {exc}'
finally:
    d['exit_code']=p.stop()
    d['external_exists']=external.exists()
    d['permission_requests']=len(p.permissions)
    d['elapsed_seconds']=round(probe.time.monotonic()-p.started,3)
    (probe.OUT/'codex-control.json').write_text(json.dumps(probe.clean(d),indent=2)+'\n')
print('Codex control recorded',flush=True)
