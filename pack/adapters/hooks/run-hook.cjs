'use strict';

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const HOOKS = new Set([
  'reread-guard.py', 'session-start.py', 'mail-doorbell.py',
  'heartbeat.py', 'owner-review-gate.py',
]);
const HOSTS = new Set(['claude', 'copilot', 'codex', 'grok', 'agy']);
const EVENTS = new Set([
  'PreToolUse', 'UserPromptSubmit', 'SessionStart', 'SubagentStart', 'PostToolUse',
  'Stop', 'SubagentStop', 'PreInvocation', 'preToolUse', 'postToolUse',
  'sessionStart', 'subagentStart', 'agentStop', 'subagentStop', 'userPromptSubmitted',
]);

function validArgs(args) {
  if (args[0] === 'coord-core.py') {
    return args.length === 4 && args[1] === 'hook' && args[2] === '--host' && HOSTS.has(args[3]);
  }
  return HOOKS.has(args[0]) && args[1] === '--host' && HOSTS.has(args[2])
    && (args.length === 3 || (args.length === 5 && args[3] === '--event' && EVENTS.has(args[4])));
}

function findPython(run = spawnSync, now = Date.now, platform = process.platform) {
  const candidates = platform === 'win32'
    ? [['python', []], ['py', ['-3']], ['python3', []]]
    : [['python3', []], ['python', []]];
  const deadline = now() + 1000;
  for (const [exe, prefix] of candidates) {
    const remaining = deadline - now();
    if (remaining <= 0) break;
    const result = run(exe, [...prefix, '-I', '-c',
      'import json,sys;print(json.dumps([sys.executable,list(sys.version_info[:2])]))'], {
      input: '', encoding: 'utf8', timeout: Math.min(400, remaining),
      maxBuffer: 4096, windowsHide: true, shell: false, killSignal: 'SIGKILL',
    });
    if (result.error || result.signal || result.status !== 0) continue;
    try {
      const [executable, version] = JSON.parse(result.stdout);
      if (typeof executable === 'string' && path.isAbsolute(executable)
          && Array.isArray(version) && version[0] === 3 && version[1] >= 8) return executable;
    } catch (error) {
      if (!(error instanceof SyntaxError || error instanceof TypeError)) throw error;
    }
  }
  throw new Error('HOOK-PYTHON-MISSING: Python 3.8+ was not found within the discovery deadline');
}

function childStatus(result) {
  if (result.error || result.signal || !Number.isInteger(result.status)) {
    throw new Error('HOOK-CHILD-FAILED: could not start or complete the hook within two seconds');
  }
  return result.status;
}

function runChild(python, args, root, run = spawnSync) {
  return run(python, args, {
    cwd: root, stdio: 'inherit', shell: false, windowsHide: true,
    timeout: 2000, killSignal: 'SIGKILL',
  });
}

function main(args) {
  try {
    if (args.length === 1 && args[0] === '--check') {
      findPython();
      process.stdout.write('{"launcher":"ready","python":"available"}\n');
      return;
    }
    if (!validArgs(args)) throw new Error('HOOK-ARGUMENT: unsupported script, host, event or arguments');
    const root = fs.realpathSync(path.resolve(__dirname, '../../..'));
    const candidate = args[0] === 'coord-core.py'
      ? path.resolve(__dirname, '../scripts/coord-core.py') : path.join(__dirname, args[0]);
    const script = fs.realpathSync(candidate);
    const relative = path.relative(root, script);
    if (relative.startsWith(`..${path.sep}`) || relative === '..' || path.isAbsolute(relative)) {
      throw new Error('HOOK-PATH: script escapes the installed checkout');
    }
    const python = findPython();
    const result = runChild(python, [script, ...args.slice(1)], root);
    process.exitCode = childStatus(result);
  } catch (error) {
    const message = error.message.startsWith('HOOK-') ? error.message : 'HOOK-START: launcher or script unavailable';
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { validArgs, findPython, childStatus, runChild, main };
if (require.main === module) main(process.argv.slice(2));
