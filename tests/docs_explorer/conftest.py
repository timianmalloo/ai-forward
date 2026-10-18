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

The same holds for the harness's SESSION identity (FR-099, 2026-10-17). A developer's
`.claude/settings.local.json` sets AGENT_SESSION; the installed session-start hook keys its
run-start marker by it, so two `test_delivery_session_start` subtests found `tim-interactive`
where they expected their fixture session - locally only, never on CI, which has no session.
Tests that need a session set their own explicitly.
"""
import os

import pytest

# CI-speed P1a (owner ruling, 2026-10-18). These tests assert real wall-clock deadlines, process
# kills and concurrent-writer ordering. Under `-n 4` on a 4-vCPU Windows runner the contention
# made each one fail in turn (runs 39074268339..39148797169), not the code. They run in a serial
# stage after the parallel one (`-m wallclock`), keeping their real deadlines. This is the only list.
WALLCLOCK = (
    "test_coord_transport.py",
    "test_bounded_process.py",
    "test_benchmark_harness.py",
    "test_docs_graph.py::DocsGraphTests::test_atomic_append_serializes_concurrent_writers_without_losing_lines",
)


def pytest_configure(config):
    config.addinivalue_line("markers", "wallclock: asserts real time; runs in the serial stage, never under xdist")


def pytest_collection_modifyitems(config, items):
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if any(nodeid.startswith("tests/docs_explorer/" + entry) for entry in WALLCLOCK):
            item.add_marker(pytest.mark.wallclock)


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
    for name in ("AGENT_SESSION", "AGENT_HOST", "AGENT_NAME"):
        if name in os.environ:
            removed[name] = os.environ.pop(name)
    try:
        yield
    finally:
        os.environ.update(removed)
