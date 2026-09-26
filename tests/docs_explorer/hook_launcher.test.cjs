'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const path = require('node:path');
const { findPython, childStatus, validArgs, runChild } = require('../../pack/adapters/hooks/run-hook.cjs');

test('missing interpreters fail explicitly without consuming stdin', () => {
  let calls = 0;
  assert.throws(() => findPython((_exe, _args, options) => {
    calls += 1;
    assert.equal(options.input, '');
    assert.equal(options.shell, false);
    assert.equal(options.maxBuffer, 4096);
    assert.equal(options.killSignal, 'SIGKILL');
    assert.ok(options.timeout > 0 && options.timeout <= 400);
    return { error: new Error('ENOENT'), status: null };
  }, () => 0, 'win32'), /HOOK-PYTHON-MISSING/);
  assert.equal(calls, 3);
});

test('discovery respects the aggregate deadline', () => {
  let now = 0;
  let calls = 0;
  assert.throws(() => findPython(() => {
    calls += 1;
    now = 1001;
    return { error: new Error('ETIMEDOUT'), status: null };
  }, () => now, 'win32'), /HOOK-PYTHON-MISSING/);
  assert.equal(calls, 1);
});

test('unusable Python is skipped and the actual executable is returned', () => {
  let calls = 0;
  const expected = path.resolve('python');
  const found = findPython(() => {
    calls += 1;
    return calls === 1
      ? { status: 0, stdout: 'Store alias, not Python' }
      : { status: 0, stdout: JSON.stringify([expected, [3, 12]]) };
  }, () => 0, 'win32');
  assert.equal(found, expected);
  assert.equal(calls, 2);
});

test('normal exit codes including refusal are preserved', () => {
  assert.equal(childStatus({ status: 0 }), 0);
  assert.equal(childStatus({ status: 2 }), 2);
  assert.equal(childStatus({ status: 17 }), 17);
});

test('spawn failure timeout and signal never become success', () => {
  for (const result of [{ status: null }, { status: 0, error: new Error('ETIMEDOUT') },
    { status: null, signal: 'SIGTERM' }]) {
    assert.throws(() => childStatus(result), /HOOK-CHILD-FAILED/);
  }
});

test('coordination authority is limited to the native hook', () => {
  assert.equal(validArgs(['coord-core.py', 'hook', '--host', 'codex']), true);
  assert.equal(validArgs(['coord-core.py', 'install', '--host', 'codex']), false);
  assert.equal(validArgs(['coord-core.py', 'hook', '--host', 'claude', '--force']), false);
  assert.equal(validArgs(['../heartbeat.py', '--host', 'claude']), false);
});

test('hook timeout cannot be ignored and the hook is never retried', () => {
  let calls = 0;
  const result = runChild('python', ['hook.py'], process.cwd(), (_exe, _args, options) => {
    calls += 1;
    assert.equal(options.killSignal, 'SIGKILL');
    assert.equal(options.timeout, 2000);
    assert.equal(options.shell, false);
    assert.equal(options.stdio, 'inherit');
    return { status: null, signal: 'SIGKILL' };
  });
  assert.equal(calls, 1);
  assert.throws(() => childStatus(result), /HOOK-CHILD-FAILED/);
});

test('real SIGTERM-ignoring child is terminated', { skip: process.platform === 'win32' }, () => {
  const result = runChild(process.execPath,
    ['-e', "process.on('SIGTERM',()=>{});setInterval(()=>{},1000)"], process.cwd());
  assert.equal(result.signal, 'SIGKILL');
  assert.throws(() => childStatus(result), /HOOK-CHILD-FAILED/);
});
