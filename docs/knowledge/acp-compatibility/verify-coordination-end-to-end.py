#!/usr/bin/env python3
"""Check sanitized finite-corpus consistency, not native truth or reusable attestation.

Raw-source validation happens privately before export. This checker binds the
sanitized claims to each other and, when a repository is supplied, to original
Git receipt objects retained in a pinned portable fixture and current file bytes.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit('Run without -O; this finite verifier uses assertions.')

GIT_FIXTURE = 'docs/knowledge/acp-compatibility/coordination-receipts.pack'
GIT_FIXTURE_BYTES = 230630
GIT_FIXTURE_SHA256 = 'eca0df6c4df2532921c6ee6a91e829ab8fed16682ff26cee869000876bb5d654'

def git_environment():
    """Do not inherit object stores, replacement refs, config injection or indexes."""
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS='1')
    return env

@contextmanager
def git_fixture(repo):
    """Import only the pinned original-object projection into a disposable bare repo."""
    path = repo / GIT_FIXTURE
    assert path.is_file() and not path.is_symlink(), 'GIT-FIXTURE-MISSING: original-object fixture required'
    assert path.stat().st_size == GIT_FIXTURE_BYTES, 'GIT-FIXTURE-SIZE: unexpected fixture size'
    with path.open('rb') as stream:
        payload = stream.read(GIT_FIXTURE_BYTES + 1)
    assert len(payload) == GIT_FIXTURE_BYTES and hashlib.sha256(payload).hexdigest() == GIT_FIXTURE_SHA256, \
        'GIT-FIXTURE-HASH: original-object fixture changed'
    with tempfile.TemporaryDirectory(prefix='coord-proof-git-') as directory:
        isolated = Path(directory)
        for args, input_bytes in ((['init', '--bare', '--quiet', '--template=', str(isolated)], None),
                                  (['-C', str(isolated), 'index-pack', '--stdin'], payload)):
            result = subprocess.run(['git', *args], input=input_bytes, capture_output=True,
                                    env=git_environment(), timeout=10)
            assert result.returncode == 0, 'GIT-FIXTURE-IMPORT: Git rejected isolated evidence'
        yield isolated

def digest(value, length=64):
    assert isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value)

def file_evidence(row):
    assert row['file'] == Path(row['file']).name and row['file'] not in ('', '.', '..')
    digest(row['sha256'])

def git_receipt(repo, source, worker, joined, receipt):
    """Require one receipt commit based exactly on source, retained in its join."""
    def git(*args):
        result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                                env=git_environment(), timeout=10)
        assert result.returncode == 0, 'Git evidence unavailable or inconsistent'
        return result.stdout
    for commit in (source, worker, joined):
        digest(commit, 40)
        assert git('cat-file', '-t', commit) == b'commit\n'
    assert git('rev-list', '--parents', '-n', '1', worker).decode().split() == [worker, source]
    assert git('diff', '--name-only', '-z', source, worker, '--') == receipt['path'].encode() + b'\0'
    git('merge-base', '--is-ancestor', worker, joined)
    for commit in (worker, joined):
        content = git('show', commit + ':' + receipt['path'])
        assert len(content) == receipt['bytes'] and hashlib.sha256(content).hexdigest() == receipt['sha256']

def profile(row):
    assert row['schema'] == 'finite-profile-proof/1'
    assert row['harness'] in ('claude', 'codex', 'grok', 'agy')
    assert row['scenario'] in ('positive', 'negative')
    assert row['terminal_state'] == ('ready_for_review' if row['scenario'] == 'positive' else 'blocked')
    assert type(row['epoch']) is int and row['epoch'] > 0
    assert type(row['cancel_to_return_seconds']) in (float, int) and 0 <= row['cancel_to_return_seconds'] <= 5
    digest(row['fingerprint'])
    digest(row['source_base'], 40)
    digest(row['receipt']['sha256'])
    assert row['receipt']['kind'] == 'file' and row['receipt']['bytes'] > 0
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]*', row['worker'])
    assert row['receipt']['path'] == 'docs/notes/note-' + row['worker'] + '.md'
    assert row['harness'] in row['native_stop_hosts']
    required = {'ownership', 'cancel', 'qualification', 'handback'}
    if row['scenario'] == 'positive':
        required.add('positive_review')
    assert set(row['evidence']) == required
    for value in row['evidence'].values():
        file_evidence(value)

def verify(data, repo=None):
    assert data['schema'] == 'finite-coordination-end-to-end/1' and data['unattended_enabled'] is False
    assert len(data['profiles']) == 8
    assert {(r['harness'], r['scenario']) for r in data['profiles']} == {
        (h, s) for h in ('claude', 'codex', 'grok', 'agy') for s in ('positive', 'negative')}
    for row in data['profiles']:
        profile(row)
    assert len({r['worker'] for r in data['profiles']}) == 8
    positive = {r['harness']: r for r in data['profiles'] if r['scenario'] == 'positive'}
    joins = data['codex_owner_joins']
    assert len(joins) == 4 and {j['harness'] for j in joins} == set(positive)
    for row in joins:
        assert row['worker'] == positive[row['harness']]['worker']
        assert row['source_base'] == positive[row['harness']]['source_base']
        assert row['receipt'] == positive[row['harness']]['receipt']
        assert row['returncode'] == 0 and row['timed_out'] is False and not row['limit_exceeded']
        assert row['contained'] is True and row['cleanup_error'] is None
        digest(row['worker_commit'], 40)
        digest(row['join_commit'], 40)
        file_evidence({'file': row['log'], 'sha256': row['log_sha256']})
    hooks = {h['eventName']: h for h in data['codex_native_hooks']}
    assert len(data['codex_native_hooks']) == 2 and set(hooks) == {'preToolUse', 'stop'}
    assert hooks['preToolUse']['matcher'] == 'apply_patch' and hooks['stop']['matcher'] is None
    assert hooks['preToolUse']['currentHash'] == 'sha256:2a61e11f3c15ee291fb8820452f81f09d4924a2aa35654ee5059cb8f33f9be33'
    assert hooks['stop']['currentHash'] == 'sha256:06a60eceeece9b9c70f5ecdabdd8372477e1d947757558eac9f3c01789866698'
    assert all(h['enabled'] is True and h['trustStatus'] == 'trusted' for h in hooks.values())
    owner = data['claude_owner']
    assert owner['actual_native_owner'] is True and owner['host'] == 'claude'
    assert owner['owner'] == 'coord-e2e-claude-owner-2' and owner['epoch'] > 11
    assert owner['native_session_id'] and owner['independent_review_accepted'] is True and owner['joined'] is True
    actions = owner['native_actions']
    assert [r['kind'] for r in actions] == ['driver', 'receipt_read', 'commit', 'join']
    assert all(isinstance(r['tool_call_id'], str) and r['tool_call_id'] and r['success'] is True for r in actions)
    ids = [r['tool_call_id'] for r in actions]
    assert len(set(ids)) >= 3 and ids[0] not in ids[1:] and ids[1] not in ids[2:]
    for action in actions:
        for key in ('input_sha256', 'output_sha256'):
            if key in action:
                digest(action[key])
    file_evidence(owner['raw_evidence'])
    file_evidence(owner['driver_report'])
    profile(owner['worker_proof'])
    assert owner['worker_proof']['scenario'] == 'positive' and owner['worker_proof']['epoch'] == owner['epoch']
    assert owner['worker_proof']['harness'] == 'agy' and owner['worker_proof']['worker'] == 'e2e-pos-claude-owner-2-agy'
    assert owner['worker_proof']['worker'] not in {r['worker'] for r in data['profiles']}
    assert owner['worker_proof']['receipt']['path'] not in {r['receipt']['path'] for r in data['profiles']}
    assert owner['source_base'] == owner['worker_proof']['source_base'] == data['source_landing']['linear_head']
    digest(owner['worker_commit'], 40)
    digest(owner['owner_join_commit'], 40)
    assert owner['join_gates_passed'] == 9 and owner['source_unchanged'] is True
    release = data['release_verification']
    assert (release['python_passed'], release['python_skipped'], release['python_subtests'], release['node_passed'], release['gates_covered']) == (1201, 12, 440, 34, 17)
    assert release['single_all_green_full_run'] is False
    file_evidence(release['full_run'])
    file_evidence(release['metadata_correction'])
    assert data['source_landing']['push'] is False and len(data['retained_failures']) == 3
    expected_failures = {
        ('worker', 'e2e-neg-codex'): ('RUN-EVIDENCE', 'coord-e2e-neg-codex-handback-observation.json'),
        ('worker', 'e2e-neg-grok'): ('ownership_not_qualified', 'coord-e2e-neg-grok-ownership.json'),
        ('owner', 'coord-e2e-claude-owner'): ('prepare_template_missing', 'report.json')}
    actual_failures = set()
    for failure in data['retained_failures']:
        identities = [(kind, failure[kind]) for kind in ('worker', 'owner') if kind in failure]
        assert len(identities) == 1 and identities[0] in expected_failures
        identity = identities[0]
        assert identity not in actual_failures and failure['joined'] is False
        actual_failures.add(identity)
        assert (failure['result'], failure['evidence']['file']) == expected_failures[identity]
        file_evidence(failure['evidence'])
    assert actual_failures == set(expected_failures)
    assert all(v == 'not recorded' for v in data['usage'].values()) and data['limitations']
    assert '/Users/' not in json.dumps(data) and '/home/' not in json.dumps(data)
    if repo:
        with git_fixture(repo) as objects:
            for row in joins:
                git_receipt(objects, row['source_base'], row['worker_commit'], row['join_commit'], row['receipt'])
            git_receipt(objects, owner['source_base'], owner['worker_commit'], owner['owner_join_commit'], owner['worker_proof']['receipt'])
        for row in [*positive.values(), owner['worker_proof']]:
            receipt = row['receipt']
            content = (repo / receipt['path']).read_bytes()
            assert len(content) == receipt['bytes'] and hashlib.sha256(content).hexdigest() == receipt['sha256']

def main():
    here = Path(__file__).resolve()
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else here.with_name('end-to-end-qualification.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    repo = path.parents[3]
    verify(data, repo)
    mutations = [
        lambda d: d.update(unattended_enabled=True),
        lambda d: d['profiles'][0].update(terminal_state='ready_for_review'),
        lambda d: d['profiles'][0].update(native_stop_hosts=[]),
        lambda d: d['profiles'][0].update(cancel_to_return_seconds=6),
        lambda d: d['profiles'].pop(),
        lambda d: d['codex_owner_joins'][0].update(cleanup_error='survivor'),
        lambda d: d['claude_owner'].update(actual_native_owner=False),
        lambda d: d['claude_owner'].update(native_actions=[]),
        lambda d: d['claude_owner'].update(independent_review_accepted=False),
        lambda d: d['claude_owner']['worker_proof'].update(epoch=9),
        lambda d: d['codex_native_hooks'][1].update(trustStatus='untrusted'),
        lambda d: d['retained_failures'][0].update(joined=True),
        lambda d: d['release_verification'].update(single_all_green_full_run=True),
        lambda d: d['claude_owner']['native_actions'][0].update(success=False),
        lambda d: [r.update(tool_call_id='same') for r in d['claude_owner']['native_actions']],
        lambda d: d['claude_owner']['native_actions'].reverse(),
        lambda d: d['claude_owner']['worker_proof'].update(worker=d['profiles'][-1]['worker']),
        lambda d: d['codex_native_hooks'][0].update(matcher='unrelated'),
        lambda d: d['retained_failures'][1].pop('evidence'),
        lambda d: d['codex_owner_joins'][0].update(worker_commit='0'*40)]
    for index, mutate in enumerate(mutations):
        changed = copy.deepcopy(data)
        mutate(changed)
        try:
            verify(changed, repo)
        except (AssertionError, KeyError, ValueError, subprocess.TimeoutExpired):
            continue
        raise AssertionError('False claim accepted: ' + str(index))
    print(f'Sanitized finite corpus consistent: eight worker profiles, five distinct Git receipts from the pinned portable original-object fixture, both Owner claim records; {len(mutations)} false claims rejected. Native evidence was checked privately before export; no reusable attestation emitted.')

if __name__ == '__main__':
    main()
