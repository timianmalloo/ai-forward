from pathlib import Path
import json
import os
import sys
sys.path.insert(0, '/Users/mallalieut/projects/ai-forward-feat-acp-compatibility-spec/pack/scripts')
from bounded_process import run_bounded

base = Path('/tmp/acp-compatibility-20260920')
prompt = '''You are the Grok probe driver requested by the operator, in your assigned isolated worktree. This is a deterministic mechanics node: no additional planning, skill invocation, agent spawning, repository edits, permission changes, or global configuration changes. The parent has prepared and authorized one bounded local compatibility experiment. Execute exactly this command once using your command tool:
python3 /tmp/acp-compatibility-20260920/probe.py all
The script runs Grok native ACP, pinned Claude and Codex ACP adapters, and Agy native stream-json in disposable fixtures. It denies all ACP permission requests, uses read-only Codex and plan-mode Agy, creates no production changes, kills only owned child groups, and writes sanitized results under /tmp/acp-compatibility-20260920/results. Wait for that command to finish (within its bounded per-turn deadlines), then report its four summary lines verbatim. If any permission blocks running the command, report the actual blocker and stop. Do not retry with broader permissions. Do not read credentials or private files.'''
label = 'driver'
if len(sys.argv)>1 and sys.argv[1]=='retry':
    label='retry-driver'
    prompt='''Run exactly once: python3 /tmp/acp-compatibility-20260920/retry.py . This is the parent-authorized, bounded follow-up experiment: Grok native control on the SAME untrusted fixture, and Codex native read plus a benign outside-workspace file-write request whose ACP permission response is reject. No global trust/permission changes, no agent spawning, no additional probes. Wait for completion then report the two summary lines. Do not bypass a refusal.'''
env = dict(os.environ, AGENT_SESSION='acp-probe-grok', AGENT_HOST='grok')
result = run_bounded(['grok', '--cwd', '/Users/mallalieut/projects/ai-forward-feat-acp-probe-driver', '--no-subagents', '--max-turns', '3', '--output-format', 'json', '-p', prompt], cwd='/Users/mallalieut/projects/ai-forward-feat-acp-probe-driver', env=env, timeout_seconds=900, memory_limit=4*1024**3, stdout_limit=1024**2, stderr_limit=128*1024)
(base/f'{label}-stdout.json').write_text(result.stdout)
(base/f'{label}-stderr.txt').write_text(result.stderr)
(base/f'{label}-result.json').write_text(json.dumps({k:v for k,v in vars(result).items() if k not in ('stdout','stderr')},indent=2))
print((base/f'{label}-result.json').read_text())
print(result.stdout[-12000:])
