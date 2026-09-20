#!/usr/bin/env python3
"""Check the committed experiment's evidence and the non-vacuous verdict controls."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

base=Path(__file__).resolve().parent

def permission_verdict(record, presence):
    count=record.get('permission_requests')
    if not isinstance(count,int) or count<=0:
        return 'not-established'
    if record.get(presence) is False:
        return 'denial-observed'
    return 'denial-not-proven'

def driver_verdict(record):
    result=record.get('result')
    if record.get('process',{}).get('returncode')!=0:
        return 'failed-wrapper'
    if not isinstance(result,dict) or result.get('stopReason')!='end_turn' or not result.get('text'):
        return 'completion-not-proven'
    return 'completed-wrapper'

def main():
    observations=json.loads((base/'observations.json').read_text())['observations']
    assert set(observations)=={'grok','claude','codex','agy','grok-native-control','codex-control'}
    for name in ('grok','claude','codex'):
        steps=observations[name]['steps']
        assert steps['initialize']['result']['protocolVersion']==1
        assert steps['new']['result']['sessionId']
        assert 'ORCHID-482' in steps['second']['text']
        assert steps['first']['updates']>0
        assert steps['cancel']['result']['stopReason']=='cancelled'
    assert permission_verdict(observations['grok'],'denied_file_exists')=='not-established'
    assert permission_verdict(observations['claude'],'denied_file_exists')=='denial-observed'
    assert permission_verdict(observations['codex'],'denied_file_exists')=='not-established'
    assert permission_verdict(observations['codex-control'],'external_exists')=='denial-observed'
    assert observations['grok-native-control']['project_trusted'] is False
    assert observations['grok-native-control']['marker_seen'] is False
    assert 'ACP_READ_EVIDENCE_913' in observations['codex-control']['steps']['native_read']['text']
    drivers=json.loads((base/'grok-driver-evidence.json').read_text())
    assert driver_verdict(drivers['driver'])=='completed-wrapper'
    assert driver_verdict(drivers['retry-driver'])=='failed-wrapper'
    assert 'max turns reached' in drivers['retry-driver']['diagnostic']
    # Negative controls: absent callbacks/results cannot become a successful verdict.
    assert permission_verdict({'permission_requests':0,'exists':False},'exists')=='not-established'
    assert permission_verdict({'permission_requests':1,'exists':True},'exists')=='denial-not-proven'
    assert driver_verdict({'process':{'returncode':0},'result':{}})=='completion-not-proven'
    mutation=copy.deepcopy(drivers['driver'])
    mutation['process']['returncode']=1
    assert driver_verdict(mutation)=='failed-wrapper'
    for name,digest in json.loads((base/'manifest.json').read_text())['files'].items():
        assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    for file in ('observations.json','protocol-evidence.jsonl','grok-driver-evidence.json'):
        text=(base/file).read_text()
        assert not re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text),file
        assert not re.search(r'(?:sk-ant-|sk-|xai-)[A-Za-z0-9_-]{15,}',text),file
        assert 'availableModels' not in text and 'team_id' not in text,file
    spec=base.parents[1]/'specs/acp-coordination.md'
    rendered=spec.with_suffix('.html').read_text()
    assert hashlib.sha256(spec.read_bytes()).hexdigest() in rendered
    for n in range(1,11):
        assert f'ACP-{n} ' in rendered,f'ACP-{n}'
    assert '<script' not in rendered and '<link' not in rendered
    assert '<caption>Flow and recovery paths</caption>' in rendered
    qa=json.loads((base/'render-qa.json').read_text())
    assert qa['html_sha256']==hashlib.sha256(spec.with_suffix('.html').read_bytes()).hexdigest()
    assert qa['status']=='pass'
    assert {v['viewport'] for v in qa['viewports']}=={390,1440}
    for view in qa['viewports']:
        assert view['document']<=view['viewport']
        assert not view['overflow'] and not view['missingAnchors']
        assert view['headings']==1 and view['tables']>=1
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            if tag=='a':
                href=dict(attrs).get('href','')
                if href and not href.startswith(('https://','http://','#')):
                    assert (spec.parent/href).exists(),href
    Links().feed(rendered)
    print('PASS: six observations; real denial/empty-result negative controls; wrapper failure preserved; hashes; privacy allowlist; full offline HTML and local links.')

if __name__=='__main__':
    main()
