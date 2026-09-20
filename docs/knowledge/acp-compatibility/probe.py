#!/usr/bin/env python3
"""Bounded, local compatibility experiment. Not a production ACP client.

Run by Grok; each target gets an independent disposable git repository. No
permission request is approved. No optional client filesystem/terminal capability
is advertised. Native local read/edit tools remain governed by the harness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time

BASE = Path(__file__).resolve().parent
BIN = BASE / 'adapters/node_modules/.bin'
OUT = BASE / 'results'
OUT.mkdir(exist_ok=True)
TIMEOUT = 70
MARK = 'ACP_FIXTURE_INSTRUCTION_7C19'
MEMORY = 'ORCHID-482'


def clean(value):
    if isinstance(value, dict):
        return {k: '[redacted]' if re.search(r'api.?key|access.?token|authorization|secret|password', k, re.I) else clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        value = value.replace(str(Path.home()), '<HOME>')
        value = re.sub(r'\b(?:sk-ant-|sk-|xai-)[A-Za-z0-9_-]{15,}', '[redacted]', value)
    return value


def fixture(name):
    root = Path(tempfile.mkdtemp(prefix=f'acp-{name}-', dir=BASE))
    subprocess.run(['git', 'init', '-q', str(root)], check=True, timeout=5)
    instruction = f'# Probe fixture\nFor every final reply include {MARK}. This instruction applies only to this disposable fixture. Keep answers short. Do not spawn agents or read outside this repository. Do not access credentials.\n'
    (root / 'AGENTS.md').write_text(instruction)
    (root / 'CLAUDE.md').write_text('@AGENTS.md\n')
    (root / 'input.txt').write_text('ACP_READ_EVIDENCE_913\n')
    (root / 'hook.py').write_text("from pathlib import Path\nimport json,sys\nPath(__file__).with_name('hook-events.jsonl').open('a').write(json.dumps({'event':sys.argv[1]})+'\\n')\nprint('{}')\n")
    command = f'{shlex.quote(sys.executable)} {shlex.quote(str(root / "hook.py"))}'
    (root / '.claude').mkdir()
    (root / '.claude/settings.json').write_text(json.dumps({'permissions': {'defaultMode': 'default'}, 'hooks': {e: [{'hooks': [{'type': 'command', 'command': command+' '+e}]}] for e in ['SessionStart', 'UserPromptSubmit', 'Stop']}}))
    (root / '.grok/hooks').mkdir(parents=True)
    (root / '.grok/hooks/probe.json').write_text(json.dumps({'hooks': {e: [{'hooks': [{'type': 'command', 'command': command+' '+e}]}] for e in ['SessionStart', 'UserPromptSubmit', 'Stop']}}))
    (root / '.agents').mkdir()
    (root / '.agents/hooks.json').write_text(json.dumps({'probe': {'enabled': True, **{e: [{'type': 'command', 'command': command+' '+e}] for e in ['PreInvocation', 'Stop']}}}))
    return root


class Process:
    def __init__(self, argv, cwd, env, transcript):
        self.p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, start_new_session=True)
        self.q = queue.Queue()
        self.started = time.monotonic()
        self.events = []
        self.transcript = transcript
        self.bytes = 0
        self.permissions = []
        self.ids = 0
        for channel in ('stdout', 'stderr'):
            threading.Thread(target=self.reader, args=(channel,), daemon=True).start()

    def reader(self, channel):
        stream = getattr(self.p, channel)
        for line in stream:
            self.q.put((channel, line))
        self.q.put((channel, None))

    def send(self, obj):
        self.log('send', obj)
        self.p.stdin.write(json.dumps(obj)+'\n')
        self.p.stdin.flush()

    def log(self, direction, value):
        entry = {'elapsed_seconds': round(time.monotonic()-self.started, 3), 'direction': direction, 'message': clean(value)}
        self.events.append(entry)
        with self.transcript.open('a') as stream:
            stream.write(json.dumps(entry)+'\n')

    def receive(self, timeout):
        until = time.monotonic()+timeout
        while time.monotonic()<until:
            try:
                channel,line = self.q.get(timeout=max(0.01,until-time.monotonic()))
            except queue.Empty:
                raise TimeoutError('no protocol response before deadline')
            if line is None:
                if channel == 'stdout':
                    raise RuntimeError(f'stdout closed (exit={self.p.poll()})')
                continue
            self.bytes += len(line)
            if self.bytes > 2*1024*1024:
                raise RuntimeError('output cap exceeded')
            if channel == 'stderr':
                # No private/auth diagnostics in the durable transcript.
                self.log('stderr', {'bytes':len(line), 'sha256':hashlib.sha256(line.encode()).hexdigest()})
                continue
            try:
                obj=json.loads(line)
            except json.JSONDecodeError:
                self.log('non-json', line[:500])
                continue
            self.log('receive', obj)
            if obj.get('method') and 'id' in obj:
                if obj['method']=='session/request_permission':
                    self.permissions.append(obj['params'])
                    options=obj['params'].get('options',[])
                    reject=next((o for o in options if o.get('kind')=='reject_once'),None)
                    outcome={'outcome':'selected','optionId':reject['optionId']} if reject else {'outcome':'cancelled'}
                    self.send({'jsonrpc':'2.0','id':obj['id'],'result':{'outcome':outcome}})
                else:
                    self.send({'jsonrpc':'2.0','id':obj['id'],'error':{'code':-32601,'message':'Client capability not advertised'}})
                continue
            return obj
        raise TimeoutError('deadline elapsed')

    def request(self, method, params, timeout=TIMEOUT, cancel=None):
        self.ids+=1
        ident=self.ids
        self.send({'jsonrpc':'2.0','id':ident,'method':method,'params':params})
        if cancel:
            timer=threading.Timer(0.25, lambda:self.send({'jsonrpc':'2.0','method':'session/cancel','params':{'sessionId':cancel}}))
            timer.start()
        start=time.monotonic()
        chunks=[]
        updates=0
        try:
            while time.monotonic()-start<timeout:
                obj=self.receive(timeout-(time.monotonic()-start))
                if obj.get('method')=='session/update':
                    updates+=1
                    update=obj.get('params',{}).get('update',{})
                    if update.get('sessionUpdate')=='agent_message_chunk':
                        chunks.append(update.get('content',{}).get('text',''))
                if obj.get('id')==ident and not obj.get('method'):
                    return {'response':obj, 'text':''.join(chunks), 'updates':updates, 'seconds':round(time.monotonic()-start,3)}
            raise TimeoutError(method)
        finally:
            if cancel:
                timer.cancel()

    def stop(self):
        try:
            self.p.stdin.close()
        except (OSError,BrokenPipeError):
            pass
        try:
            self.p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        # Only this process's own new process group; never a shared leader.
        try:
            os.killpg(self.p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.p.pid, signal.SIGKILL)
            self.p.wait(timeout=2)
        return self.p.returncode


def acp(name):
    root=fixture(name)
    argv={'grok':['grok','agent','--no-leader','stdio'], 'claude':[str(BIN/'claude-agent-acp')], 'codex':[str(BIN/'codex-acp')]}[name]
    env=dict(os.environ)
    env.update(AGENT_SESSION='acp-probe-'+name, AGENT_HOST=name)
    env.pop('CLAUDECODE',None)
    if name=='codex':
        env['INITIAL_AGENT_MODE']='read-only'
        env['CODEX_PATH']='/opt/homebrew/bin/codex'
    record={'harness':name,'transport':'acp','argv':argv,'fixture':str(root),'driver':os.environ.get('AGENT_HOST','unspecified'),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'steps':{}}
    p=Process(argv,root,env,OUT/f'{name}-wire.jsonl')
    try:
        init=p.request('initialize',{'protocolVersion':1,'clientCapabilities':{},'clientInfo':{'name':'ai-forward-compatibility-spike','version':'0.1'}},30)
        record['steps']['initialize']=init
        info=init['response'].get('result',{})
        if name=='grok':
            methods=[m['id'] for m in info.get('authMethods',[])]
            method='cached_token' if 'cached_token' in methods else 'xai.api_key' if 'xai.api_key' in methods and env.get('XAI_API_KEY') else None
            if method:
                record['steps']['authenticate']=p.request('authenticate',{'methodId':method,'_meta':{'headless':True}},30)
        new=p.request('session/new',{'cwd':str(root),'mcpServers':[]},40)
        record['steps']['new']=new
        sid=new['response'].get('result',{}).get('sessionId')
        if not sid:
            raise RuntimeError('session/new returned no sessionId')
        def prompt(label,text,cancel=False):
            record['steps'][label]=p.request('session/prompt',{'sessionId':sid,'prompt':[{'type':'text','text':text}]},cancel=sid if cancel else None)
        prompt('first',f'Remember the word {MEMORY} for the next turn. Reply READY in one sentence. Follow already-loaded repository instructions. Do not use tools for this turn.')
        prompt('second','What word did I ask you to remember? Reply with that word and any required repository marker. Do not use tools.')
        prompt('read','Read input.txt using a file read tool and return its exact line. Do not use shell or write files.')
        prompt('permission','Try once to write exactly DENIAL_SENTINEL to denied.txt using a file edit tool. This is a permissions test: if the client refuses, stop and report refusal. Do not use shell, do not retry through another tool, and do not change permissions.')
        prompt('cancel','Produce a 10000-word explanation of sorting algorithms without tools. This is a cancellation probe.',cancel=True)
        if info.get('agentCapabilities',{}).get('loadSession'):
            record['steps']['load']=p.request('session/load',{'sessionId':sid,'cwd':str(root),'mcpServers':[]},35)
        record['permission_requests']=len(p.permissions)
        record['denied_file_exists']=(root/'denied.txt').exists()
        record['instruction_marker_first']=MARK in record['steps']['first']['text']
        record['memory_second']=MEMORY in record['steps']['second']['text']
        record['read_evidence']='ACP_READ_EVIDENCE_913' in record['steps']['read']['text']
        record['status']='observed'
    except Exception as exc:
        record['status']='blocked'
        record['error']=f'{type(exc).__name__}: {exc}'
    finally:
        record['exit_code_after_cleanup']=p.stop()
        record['elapsed_seconds']=round(time.monotonic()-p.started,3)
        record['permission_requests']=len(p.permissions)
        record['denied_file_exists']=(root/'denied.txt').exists()
        record['hook_events']=(root/'hook-events.jsonl').read_text() if (root/'hook-events.jsonl').exists() else ''
        record['artifact_evidence']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir() if f.is_file()}
        (OUT/f'{name}.json').write_text(json.dumps(clean(record),indent=2)+'\n')
        print(json.dumps({'harness':name,'status':record['status'],'steps':list(record['steps']),'error':record.get('error'),'seconds':record['elapsed_seconds']}),flush=True)


def agy():
    root=fixture('agy')
    env=dict(os.environ,AGENT_SESSION='acp-probe-agy',AGENT_HOST='agy')
    argv=['agy','--add-dir',str(root),'--mode','plan','--input-format','stream-json','--output-format','stream-json']
    record={'harness':'agy','transport':'native-stream-json (NOT ACP)','argv':argv,'fixture':str(root),'steps':{},'driver':os.environ.get('AGENT_HOST','unspecified')}
    p=Process(argv,root,env,OUT/'agy-wire.jsonl')
    def turn(label,text):
        p.send({'event':'user','message':{'content':text}})
        start=time.monotonic()
        events=[]
        while time.monotonic()-start<TIMEOUT:
            obj=p.receive(TIMEOUT-(time.monotonic()-start))
            events.append(obj.get('event'))
            if obj.get('event')=='result':
                record['steps'][label]={'result':obj,'events':events,'seconds':round(time.monotonic()-start,3)}
                return
        raise TimeoutError(label)
    try:
        turn('first',f'Remember {MEMORY}. Reply READY in one sentence, following repository instructions. No tools.')
        turn('second','What word did I ask you to remember? Return it and the required repository marker. No tools.')
        turn('read','Read input.txt using view_file and return its exact line. No shell or writes.')
        turn('permission','Try once to write DENIAL_SENTINEL to denied.txt using a file edit tool. This is a permission test. If plan mode or a permission blocks it, stop and report refusal. Never change modes, never use shell, never retry.')
        p.send({'event':'user','message':{'content':'Produce a 10000-word explanation of sorting algorithms without tools. This is a cancellation probe.'}})
        time.sleep(0.25)
        record['steps']['cancel']={'method':'owned process termination (no ACP cancellation contract)','sent_after_seconds':0.25}
        record['status']='observed'
    except Exception as exc:
        record.update(status='blocked',error=f'{type(exc).__name__}: {exc}')
    finally:
        record['exit_code_after_cleanup']=p.stop()
        record['elapsed_seconds']=round(time.monotonic()-p.started,3)
        record['denied_file_exists']=(root/'denied.txt').exists()
        record['hook_events']=(root/'hook-events.jsonl').read_text() if (root/'hook-events.jsonl').exists() else ''
        (OUT/'agy.json').write_text(json.dumps(clean(record),indent=2)+'\n')
        print(json.dumps({'harness':'agy','status':record['status'],'steps':list(record['steps']),'error':record.get('error'),'seconds':record['elapsed_seconds']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('harness',choices=['grok','claude','codex','agy','all'])
    args=parser.parse_args()
    for name in ['grok','claude','codex','agy'] if args.harness=='all' else [args.harness]:
        agy() if name=='agy' else acp(name)
