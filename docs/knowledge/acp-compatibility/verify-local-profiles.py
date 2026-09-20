#!/usr/bin/env python3
"""Verify this finite qualification corpus; this is not a production admission gate."""
import argparse
import copy
import json
import re
from pathlib import Path


def verify(data):
    assert data['schema'] == 'local-profile-evidence/1'
    assert data['unattended_enabled'] is False, 'unqualified rollout cannot be enabled'
    rows = {r['session']: r for r in data['observations']}
    assert len(rows) == len(data['observations']) == 7
    for row in rows.values():
        assert row['unattended_ready'] is False, 'negative qualification promoted to ready'
        assert row['profile_unchanged'] is True
        assert re.fullmatch(r'[a-f0-9]{64}', row['raw_sha256'])
        assert row['result']['cleanup_error'] is None
        assert row['result']['duration_seconds'] < 184
        assert row['result']['stdout_bytes'] + row['result']['stderr_bytes'] <= 4194304
    for harness, method in [('grok', '_x.ai/mcp/servers_updated'),
                            ('claude', '_auth/status_update'), ('codex', '_auth/status_update')]:
        row = rows['profile-' + harness + '-baseline']
        assert row['result']['code'] == 'protocol_error'
        assert row['result']['turns_completed'] == 0
        assert not row['diagnostic_only_ignored_notifications']
        assert any(s.get('method') == method for s in row['wire_shapes'])
    for harness in ['claude', 'codex']:
        row = rows['profile-' + harness + '-control']
        assert row['diagnostic_only_ignored_notifications'] == ['_auth/status_update'], 'control exception erased'
        assert row['result']['code'] == 'complete'
        assert row['result']['turns_completed'] == 3
        assert row['result']['permission_requests'] == 0
        assert row['instruction_quote_seen'] and row['nonce_returned']
        assert row['workspace_receipt']['exists'] and row['outside_canary']['exists']
    grok = rows['profile-grok-control']
    assert grok['diagnostic_only_ignored_notifications'] == ['_x.ai/mcp/servers_updated', '_auth/status_update']
    assert grok['result']['code'] == 'protocol_error'
    assert any(s.get('method') == '_x.ai/models/update' for s in grok['wire_shapes'])
    agy = rows['profile-agy-baseline']
    assert agy['result']['code'] == 'complete' and agy['result']['turns_completed'] == 3
    assert len(agy['native_denied_actions']) == 2
    assert not agy['workspace_receipt']['exists'] and not agy['outside_canary']['exists']
    assert agy['instruction_quote_seen'] and agy['nonce_returned']
    assert agy['pack_start_marker'] and agy['heartbeats']
    assert rows['profile-claude-control']['pack_start_marker']
    assert rows['profile-claude-control']['heartbeats']
    assert rows['profile-codex-control']['pack_start_marker'] is None
    assert not rows['profile-codex-control']['heartbeats']
    serialized = json.dumps(data)
    assert not re.search(r'/Users/|/home/|sk-ant-|xai-[A-Za-z0-9]{15,}', serialized)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path,
                        default=Path(__file__).with_name('local-profile-observations.json'))
    args = parser.parse_args()
    data = json.loads(args.path.read_text(encoding='utf-8'))
    verify(data)
    mutations = []
    ready = copy.deepcopy(data)
    ready['observations'][0]['unattended_ready'] = True
    mutations.append(ready)
    disguised = copy.deepcopy(data)
    next(r for r in disguised['observations'] if r['session'] == 'profile-claude-control')['diagnostic_only_ignored_notifications'] = []
    mutations.append(disguised)
    for mutation in mutations:
        try:
            verify(mutation)
        except AssertionError:
            continue
        raise AssertionError('false-readiness mutation survived')
    print('PASS: seven measured attempts; baseline/control separation; native denial retained; two false-readiness mutations rejected.')


if __name__ == '__main__':
    main()
