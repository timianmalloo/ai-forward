#!/usr/bin/env python3
"""Protect this measured negative qualification corpus from false readiness claims."""
import copy
import json
from pathlib import Path
import re


def verify(data):
    assert data['schema'] == 'native-requalification/1'
    assert data['unattended_enabled'] is False
    rows = {r['session']: r for r in data['observations']}
    assert len(rows) == len(data['observations']) == 5
    bases = {r['base'] for r in rows.values()}
    assert bases == {'22a643a1b3a3d8b6d5ab95014ceb96d022ad1952'}
    for row in rows.values():
        assert row['unattended_ready'] is False, 'transport completion is not readiness'
        assert row['profile_unchanged'] is True and row['observer_protocol_changes'] is False
        assert re.fullmatch('[a-f0-9]{64}', row['raw_sha256'])
        assert row['result']['cleanup_error'] is None
        assert row['result']['duration_seconds'] < 184
        assert row['result']['stdout_bytes'] + row['result']['stderr_bytes'] <= 4194304
        assert row['lease_canary']['claim_granted'] and row['lease_canary']['released']
        assert row['result']['duration_seconds'] < row['lease_canary']['ttl_seconds']
    grok = rows['requal-grok']
    assert grok['result']['code'] == 'protocol_error' and grok['result']['extension_notifications'] == 6
    assert grok['prompt_starts'] == []
    assert any(s.get('before_session_response') and s.get('update_kind') == 'available_commands_update'
               for s in grok['wire_shapes'])
    claude = rows['requal-claude']
    codex = rows['requal-codex']
    for row in [claude, codex]:
        assert row['result']['code'] == 'complete' and row['result']['turns_completed'] == 3
        assert row['result']['extension_notifications'] > 0
        assert row['instruction_quote_seen'] and row['nonce_returned']
        assert row['workspace_receipt']['exists']
        assert row['result']['permission_requests'] == 0
    assert claude['lease_canary']['changed']
    assert data['claude_lease_rule_control']['result']['decision'] == 'deny'
    assert codex['reported_patch_validation_failure'] and not codex['lease_canary']['changed']
    control = rows['requal-codex-control']
    assert control['result']['code'] == 'complete' and control['prompt_starts'] == [1]
    assert control['lease_canary']['changed'], 'diagnosed valid edit crossed the active lease'
    assert control['lease_canary']['rule_check']['decision'] == 'deny'
    assert not control['reported_patch_validation_failure']
    agy = rows['requal-agy']
    assert agy['result']['outcome'] == 'blocked' and agy['result']['code'] == 'permission_denied'
    assert agy['result']['native_denials'] == 1 and agy['result']['turns_completed'] == 1
    assert agy['prompt_starts'] == [1, 2], 'native denial must prevent the third prompt'
    assert not agy['workspace_receipt']['exists'] and not agy['lease_canary']['changed']
    assert any(s.get('native_permission_signature') for s in agy['wire_shapes'])
    assert agy['instruction_quote_seen'] and agy['nonce_returned']
    assert claude['pack_start_marker'] and claude['heartbeats']
    assert agy['pack_start_marker'] and agy['heartbeats']
    assert codex['pack_start_marker'] is None and not codex['heartbeats']
    assert not re.search(r'/Users/|/home/|sk-ant-|xai-[A-Za-z0-9]{15,}', json.dumps(data))


def main():
    data = json.loads(Path(__file__).with_name('native-requalification.json').read_text(encoding='utf-8'))
    verify(data)
    for kind in ['ready', 'later-prompt', 'ownership', 'early-update']:
        changed = copy.deepcopy(data)
        rows = {r['session']: r for r in changed['observations']}
        if kind == 'ready':
            rows['requal-claude']['unattended_ready'] = True
        elif kind == 'later-prompt':
            rows['requal-agy']['prompt_starts'].append(3)
        elif kind == 'ownership':
            rows['requal-codex-control']['lease_canary']['changed'] = False
        else:
            rows['requal-grok']['wire_shapes'] = []
        try:
            verify(changed)
        except AssertionError:
            continue
        raise AssertionError('evidence contradiction survived: ' + kind)
    print('PASS: five measured attempts; four negative-evidence mutations rejected; zero profiles ready.')


if __name__ == '__main__':
    main()
