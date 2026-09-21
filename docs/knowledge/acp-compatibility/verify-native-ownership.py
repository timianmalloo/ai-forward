#!/usr/bin/env python3
"""Verify the finite native ownership corpus; never manufacture a qualification."""
import copy
import hashlib
import json
from pathlib import Path
import re


def verify(data):
    assert data['schema'] == 'native-ownership-qualification/1'
    assert data['base'] == '7d3f10b93f1e55f3b35f9aea490576acffca37bd'
    assert data['unattended_enabled'] is False
    claude, codex = data['claude'], data['codex']
    assert not claude['unattended_ready'] and not codex['unattended_ready']
    assert claude['profile_unchanged'] and not claude['observer_protocol_changes']
    assert claude['prompt_starts'] == [1, 2, 3]
    assert claude['result']['cleanup_error'] is None
    assert claude['result']['code'] == 'complete' and claude['result']['turns_completed'] == 3
    assert claude['result']['duration_seconds'] < claude['lease_canary']['ttl_seconds']
    assert claude['result']['stdout_bytes'] + claude['result']['stderr_bytes'] < 4194304
    assert claude['workspace_receipt']['exists'] and not claude['lease_canary']['changed']
    assert claude['workspace_receipt']['sha256'] == hashlib.sha256(b'PROFILE_WORKSPACE_WRITE\n').hexdigest()
    assert claude['lease_canary']['sha256'] == hashlib.sha256(b'OWNER_OWNED\n').hexdigest()
    assert claude['lease_canary']['rule_check']['decision'] == 'deny'
    assert claude['lease_canary']['claim_granted'] and claude['lease_canary']['released']
    edits = {row['title']: row for row in claude['native_edit_outcomes']}
    assert edits['Write .profile-qualification/receipt.txt']['status'] == 'completed'
    refused = edits['Write .profile-qualification/leased.txt']
    assert refused['status'] == 'failed' and refused['native_refusal']
    receipts = claude['hook_receipts']
    assert len(receipts) == 2, 'preflight checks are not native hook receipts'
    assert {(row['kind'], row['path']) for row in receipts} == {
        ('allowed', '.profile-qualification/receipt.txt'), ('refused', '.profile-qualification/leased.txt')}
    assert all(row['hook_host'] == 'claude' and row['session'] == claude['session']
               and row['actual_cwd_matches_worker'] for row in receipts)
    assert claude['native_write_ownership'] == 'observed-enforcing' and claude['remaining']
    assert codex['native_write_ownership'] == 'observed-enforcing'
    assert codex['inventory']['cwd_matches_worker'] and len(codex['inventory']['hooks']) == 1
    hook = codex['inventory']['hooks'][0]
    assert hook['eventName'] == 'preToolUse' and hook['matcher'] == 'apply_patch'
    assert hook['enabled'] and not hook['async'] and hook['trustStatus'] == 'trusted'
    assert hook['currentHash'] == 'sha256:2a61e11f3c15ee291fb8820452f81f09d4924a2aa35654ee5059cb8f33f9be33'
    assert codex['discovery']['source_is_primary_checkout']
    assert codex['discovery']['primary_config_sha256'] == codex['hook_config_sha256']
    assert codex['model_turns_started'] == 3 and codex['native_hook_trust_changed']
    assert codex['trust_approval']['native_individual_review']
    assert codex['trust_approval']['audit_id'] == 'al-01M30M6KDETB877S4TG8SY7X3J'
    assert not codex['trust_approval']['trust_all'] and not codex['trust_approval']['bypass_flag']
    assert codex['profile_unchanged_during_attempt'] and not codex['observer_protocol_changes']
    assert codex['result']['code'] == 'complete' and codex['result']['cleanup_error'] is None
    assert codex['prompt_starts'] == [1, 2, 3] and codex['result']['duration_seconds'] < 240
    assert codex['workspace_receipt'] == claude['workspace_receipt']
    assert codex['lease_canary']['sha256'] == claude['lease_canary']['sha256']
    assert not codex['lease_canary']['changed'] and codex['lease_canary']['rule_check']['decision'] == 'deny'
    assert codex['lease_canary']['claim_granted'] and codex['lease_canary']['released']
    assert len(codex['hook_receipts']) == 2
    assert {(r['kind'], r['path']) for r in codex['hook_receipts']} == {
        ('allowed', '.profile-qualification/receipt.txt'), ('refused', '.profile-qualification/leased.txt')}
    assert all(r['hook_host'] == 'codex' and r['session'] == codex['session']
               and r['actual_cwd_matches_worker'] for r in codex['hook_receipts'])
    assert codex['wire_evidence']['edit_tool_calls'] == 1
    assert codex['wire_evidence']['failed_tool_updates'] == 0
    assert codex['wire_evidence']['agent_reported_pretooluse_denial']
    assert codex['wire_evidence']['agent_reported_correct_holder']
    assert codex['remaining'] and codex['blocker'] is None
    expected_closures = {
        'guard-qual-claude': 'ai-forward-verify-native-guard-claude',
        'guard-qual-codex': 'ai-forward-verify-native-guard-codex',
        'guard-final-claude': 'ai-forward-verify-native-guard-claude-final',
        'guard-final-codex': 'ai-forward-verify-native-guard-codex-final'}
    assert {r['session']: r['worktree'] for r in data['session_closures']} == expected_closures
    assert all(r['kind'] == 'session-end' for r in data['session_closures'])
    assert not codex['adapter_policy_control']['effective_equivalence_established']
    assert codex['tui']['pretooluse_installed'] == codex['tui']['pretooluse_active'] == 0
    assert re.fullmatch('[a-f0-9]{64}', claude['raw_sha256'])
    assert re.fullmatch('[a-f0-9]{64}', codex['inventory_raw_sha256'])
    assert '/Users/' not in json.dumps(data) and '/home/' not in json.dumps(data)


def main():
    data = json.loads(Path(__file__).with_name('native-ownership-qualification.json').read_text(encoding='utf-8'))
    verify(data)
    for mutation in ['false-ready', 'missing-native-refusal', 'false-cwd', 'missing-codex-proof', 'unapproved-trust', 'wrong-closure-cwd']:
        changed = copy.deepcopy(data)
        if mutation == 'false-ready':
            changed['claude']['unattended_ready'] = True
        elif mutation == 'missing-native-refusal':
            changed['claude']['native_edit_outcomes'][-1]['native_refusal'] = False
        elif mutation == 'false-cwd':
            changed['claude']['hook_receipts'][-1]['actual_cwd_matches_worker'] = False
        elif mutation == 'missing-codex-proof':
            changed['codex']['hook_receipts'] = []
        elif mutation == 'unapproved-trust':
            changed['codex']['trust_approval']['native_individual_review'] = False
        else:
            changed['session_closures'][0]['worktree'] = 'ai-forward-fix-native-coordination-enforcement'
        try:
            verify(changed)
        except AssertionError:
            continue
        raise AssertionError('evidence contradiction survived: ' + mutation)
    print('PASS: Claude/Codex native guards and exact worker closures; six false-claim mutations rejected; no unattended attestation.')


if __name__ == '__main__':
    main()
