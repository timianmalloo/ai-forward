"""Test-environment normalisation for the docs_explorer suite.

Fixes an order-dependent flake (~17 failures) in the git-using harness-conformance tests, seen only
on Windows under the Copilot CLI harness. The chain:

  1. The harness injects git config through the environment: GIT_CONFIG_COUNT=N with
     GIT_CONFIG_KEY_i / GIT_CONFIG_VALUE_i pairs. One value is the empty string
     (core.fsmonitor="", to disable fsmonitor).
  2. On Windows, setting an environment variable to "" DELETES it. `unittest.mock.patch.dict(
     os.environ, ...)` restores on exit by clearing and re-setting every saved var, so re-setting
     the empty GIT_CONFIG_VALUE_i deletes it - while GIT_CONFIG_COUNT still counts it.
  3. Every subsequent `git` subprocess then aborts with
     `error: missing config value GIT_CONFIG_VALUE_i` (exit 128). The first test that patches
     os.environ (test_ctx_controls) therefore breaks every later test that shells to git
     (test_harness_conformance's git init, etc.).

CI (Linux) does not hit this - an empty env var is preserved there - which is why the merge gates
stay green while a full local run flakes. The fix removes the trigger once, at session start: drop
the harness's GIT_CONFIG_* injection so the test session has a consistent git configuration that no
patch.dict round-trip can corrupt. The tests create their own throwaway repos and set their own
identity, so the injected safe.* settings are not needed; it is restored at session end.
"""
import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _stable_git_config_env():
    removed = {}
    count = os.environ.get("GIT_CONFIG_COUNT")
    if count is not None and count.isdigit():
        names = ["GIT_CONFIG_COUNT"]
        for i in range(int(count)):
            names.append(f"GIT_CONFIG_KEY_{i}")
            names.append(f"GIT_CONFIG_VALUE_{i}")
        for name in names:
            if name in os.environ:
                removed[name] = os.environ.pop(name)
    try:
        yield
    finally:
        os.environ.update(removed)
