#!/usr/bin/env python3
"""The repository's gates: ONE list, run by tools/verify-bundle.ps1 and by every CI job (FR-091).

CI used to copy each gate into the workflow by hand, and the copies drifted: the ubuntu job ran
two of the four context-budget ratchets, checked three fewer drift paths, and ordered the steps
differently from the script. Now a gate exists only here. Adding one changes the local proof and
every CI job at once, with no workflow edit.

Each gate names where CI runs it (`ci_os`). Locally a gate runs on any machine that can run it;
the few that change local state (installing the pre-commit hook) run only in CI. Every gate runs
even after a failure, so one run reports everything that is wrong.

  run  [--ci] [--skip-tests] [--shard I/N]   run the gates; exit 1 if any failed
  list [--ci] [--os linux|windows|macos]     the gates for that context, one per line

--ci: the context is a CI job; a SKIP is a FAIL there (CI must run everything it lists).
--shard I/N: run test shard I of N (FR-094); the non-test gates run only in shard 1.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
ALL = frozenset({"linux", "windows", "macos"})
DRIFT_PATHS = [".claude", ".github/instructions", ".github/knowledge", ".github/prompts", ".github/agents",
               ".grok", ".agents", ".codex", "docs", "web", "CLAUDE.md", "AGENTS.md"]
NODE_TESTS = ["tests/docs_explorer/docs_explorer_core.test.js", "tests/docs_explorer/knowledge_surfaces.test.js",
              "tests/docs_explorer/mockup_harness_audit.test.js"]
BROWSER_TEST = "tests/docs_explorer/browser_benchmark.test.js"


class Skip(Exception):
    """The gate cannot run on this machine; the reason is printed, and --ci counts it a failure."""


def this_os():
    return {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")


def run(*argv, env=None, ok=(0,)):
    """Run one command in the repo; return True when its exit status is in `ok`."""
    return subprocess.run(list(argv), cwd=REPO, env=env).returncode in ok


def script(relative, *args):
    return run(PY, os.path.join(REPO, relative), *args)


def unchanged(*paths):
    subprocess.run(["git", "--no-pager", "diff", "--stat", "--", *paths], cwd=REPO)
    return run("git", "diff", "--exit-code", "--quiet", "--", *paths)


# ---- the gates that need more than one command ------------------------------------------

def drift(_ctx):
    # FR-057: sync AND compare. Regeneration without a comparison silently repairs and passes.
    pwsh = shutil.which("pwsh")
    if not pwsh:
        raise Skip("pwsh is not installed (sync-pack.ps1 needs it)")
    if not run(pwsh, "-NoProfile", "-File", os.path.join(REPO, "tools", "sync-pack.ps1")):
        return False
    if unchanged(*DRIFT_PATHS):
        return True
    print("pack/ and the generated surfaces have drifted: the files above were just regenerated -"
          " review and commit them.")
    return False


def tests(ctx):
    env = dict(os.environ)
    if ctx.shard:
        env["AIF_TEST_SHARD"] = "{}/{}".format(*ctx.shard)
    if subprocess.run([PY, "-c", "import xdist"], cwd=REPO, capture_output=True).returncode != 0:
        if ctx.ci or ctx.shard:
            print("pytest-xdist is not installed; CI runs the suite in parallel and counts it")
            return False
        return run(PY, "-m", "pytest", "tests", "-q", env=env)
    with tempfile.TemporaryDirectory(prefix="aif-gates-") as folder:
        parallel, serial = os.path.join(folder, "parallel.xml"), os.path.join(folder, "wallclock.xml")
        green = run(PY, "-m", "pytest", "tests", "-q", "-n", "4", "-m", "not wallclock",
                    "--junitxml=" + parallel, env=env)
        # The wallclock tests assert real time; contention under xdist failed them (P1a). A shard
        # holding none of them exits 5 (no tests collected), which is not a failure.
        green = run(PY, "-m", "pytest", "tests", "-q", "-m", "wallclock", "--junitxml=" + serial,
                    env=env, ok=(0, 5)) and green
        # CI-speed C3: every collected test reported a result.
        return run(PY, os.path.join(REPO, "tools", "check-test-counts.py"), "--junit", parallel,
                   "--junit", serial, env=env) and green


def node_contracts(ctx):
    node = shutil.which("node")
    if not node:
        raise Skip("node is not installed")
    files = list(NODE_TESTS)
    if os.path.isdir(os.path.join(REPO, "node_modules", "playwright")):
        files.append(BROWSER_TEST)
    elif ctx.ci:
        print("node_modules/playwright is absent: run `npm ci` first")
        return False
    else:
        print("(browser_benchmark.test.js skipped: node_modules/playwright absent - run `npm ci`; CI runs it)")
    return run(node, "--test", *files)


def explainer(_ctx):
    node = shutil.which("node")
    if not node:
        raise Skip("node is not installed")
    return run(node, os.path.join("tools", "verify-explainer-render.js"))


def eval_cases(_ctx):
    files = sorted(glob.glob(os.path.join(REPO, "pack", "evals", "cases", "*.json")))
    bad = 0
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                case = json.load(handle)
            for assertion in case.get("assertions", []):
                if "pattern" in assertion:
                    re.compile(assertion["pattern"])
        except Exception as exc:  # noqa: BLE001 - every malformed case is reported, none stops the scan
            print("  - {}: {}".format(os.path.basename(path), exc))
            bad += 1
    print("{} eval cases checked".format(len(files)))
    return bool(files) and not bad


def context_budget(_ctx):
    # FR-072/FR-073: a ratchet, not a ceiling. All four halves run and EITHER fails the gate.
    budget = os.path.join("pack", "scripts", "context-budget.py")
    results = [script(budget, *args) for args in (["gate"], ["agents"], ["prefix", "--gate"], ["skills", "--gate"])]
    return all(results)


def coordination(_ctx):
    # CTX-H: this repo is itself a pack install, so its own coordination layer being ON is the only
    # end-to-end proof the install path works. WARN is expected on a fresh clone; FAIL fails.
    out = subprocess.run([PY, os.path.join(REPO, "docs", "ai-forward-pack", "scripts", "pack-doctor.py"),
                          "--root", REPO, "--json"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    try:
        checks = [c for c in json.loads(out.stdout)["checks"] if c["name"] == "coordination"]
    except (ValueError, KeyError, TypeError):
        print("pack-doctor produced no readable report: " + out.stderr.strip()[:300])
        return False
    if not checks:
        print("pack-doctor has no coordination check")
        return False
    print("  {} - {}".format(checks[0]["status"], checks[0]["detail"]))
    if checks[0]["status"] == "FAIL":
        print("  fix: " + checks[0].get("fix", ""))
    return checks[0]["status"] != "FAIL"


def help_under_cp1252(_ctx):
    # XP-14: --help must not raise UnicodeEncodeError on a legacy code page. With no UTF-8 override,
    # a Windows pipe uses the ANSI code page (cp1252 on the runners), the shape a cp1252 console has.
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    failed = []
    for path in sorted(glob.glob(os.path.join(REPO, "pack", "scripts", "*.py"))
                       + glob.glob(os.path.join(REPO, "pack", "adapters", "hooks", "*.py"))):
        code = subprocess.run([PY, path, "--help"], cwd=REPO, env=env, capture_output=True).returncode
        if code != 0:
            failed.append("{} (exit {})".format(os.path.basename(path), code))
    for line in failed:
        print("  FAIL --help: " + line)
    return not failed


def registry_regenerates(_ctx):
    # PLAT-B: the registry carries the interpreter token, never this machine's path.
    return (script(os.path.join("docs", "ai-forward-pack", "scripts", "coord-core.py"), "classify", "init", "--force")
            and unchanged(".agents/artifacts.yml"))


def docs_index_regenerates(_ctx):
    # XP-07: docs-index.js is merged by byte identity; a CRLF write would make every derive a diff.
    return script(os.path.join("docs", "ai-forward-pack", "scripts", "docs-graph.py"), "derive") \
        and unchanged("docs/docs-index.js")


def precommit_under_sh(_ctx):
    # The pre-commit floor `coord install` writes is `#!/bin/sh`; Git for Windows runs it through
    # its bundled sh. Advisory path (no AGENT_SESSION) and enforcing path, both exit 0 when clean.
    sh = shutil.which("sh")
    if not sh:
        raise Skip("no POSIX sh on PATH")
    hook = os.path.join(REPO, ".git", "hooks", "pre-commit")
    if not script(os.path.join("docs", "ai-forward-pack", "scripts", "coord-core.py"), "install"):
        return False
    if not os.path.isfile(hook):
        print("coord install wrote no .git/hooks/pre-commit")
        return False
    advisory = {k: v for k, v in os.environ.items() if k != "AGENT_SESSION"}
    return (run(sh, hook, env=advisory) and run(sh, hook, env=dict(os.environ, AGENT_SESSION="ci-windows"))
            and coordination(_ctx))


def command(relative, *args):
    return lambda _ctx: script(relative, *args)


# (id, name, action, ci_os, local, kind). Order is the run order; tests run last so a red test never
# hides a later proof. `local=False` gates change local state and run only in CI.
GATES = [
    ("1", "counts, skill/prompt parity, proof coverage", command("tools/check-consistency.py"), ALL, True, "check"),
    ("1b", "no machine-specific paths in tracked files", command("pack/scripts/verify-no-machine-paths.py", "--root", REPO), ALL, True, "check"),
    ("1c", "subprocess text decodes state utf-8", command("pack/scripts/verify-subprocess-utf8.py", "--root", REPO), ALL, True, "check"),
    ("1d", "text writes and consoles are portable", command("pack/scripts/verify-portable-text-io.py", "--root", REPO), ALL, True, "check"),
    ("1e", "skill contracts: seat, CO-S0 before dispatch, CO-S2 on hard stops", command("pack/scripts/verify-skill-contracts.py", "--root", REPO), ALL, True, "check"),
    ("1f", "documented commands run in any shell", command("pack/scripts/verify-documented-commands.py", "--root", REPO), ALL, True, "check"),
    ("1g", "ruling citations resolve to one heading each", command("pack/scripts/verify-ruling-citations.py", "--root", REPO), ALL, True, "check"),
    ("1h", "inline markers carry their required fields", command("pack/scripts/marker-lint.py", "--root", REPO, "--gate"), ALL, True, "check"),
    ("2", "source<->install drift (pack/ is the only source of truth)", drift, ALL, True, "check"),
    ("4", "docs explorer core contracts", node_contracts, {"linux"}, True, "node"),
    ("4b", "explainer render + accessibility proof", explainer, {"linux"}, True, "node"),
    ("5", "knowledge-graph validation", command("docs/ai-forward-pack/scripts/docs-graph.py", "--root", os.path.join(REPO, "docs"), "validate"), ALL, True, "check"),
    ("6", "vendored-foundation drift", command("pack/scripts/foundation-check.py"), ALL, True, "check"),
    ("6b", "audit log is fully readable", command("pack/scripts/audit-log.py", "verify"), ALL, True, "check"),
    ("7", "eval cases well-formed", eval_cases, ALL, True, "check"),
    ("8", "always-on context budget", context_budget, ALL, True, "check"),
    ("8b", "coordination layer installed (pack-doctor)", coordination, {"linux", "macos"}, True, "check"),
    ("9a", "every script answers --help under cp1252", help_under_cp1252, {"windows"}, True, "check"),
    ("9b", "registry regenerates byte-identically", registry_regenerates, {"windows", "macos"}, True, "check"),
    ("9c", "docs-index.js regenerates byte-identically", docs_index_regenerates, {"windows"}, True, "check"),
    ("9d", "pre-commit hook runs under sh", precommit_under_sh, {"windows"}, False, "check"),
    ("3", "python test suite", tests, ALL, True, "tests"),
]


class Context:
    def __init__(self, ci, skip_tests, shard, os_name):
        self.ci, self.skip_tests, self.shard, self.os = ci, skip_tests, shard, os_name


def selected(ctx):
    """The gates this context runs, and the ones it skips with a reason."""
    chosen = []
    for gate_id, name, action, ci_os, local, kind in GATES:
        if ctx.ci and ctx.os not in ci_os:
            continue
        if not ctx.ci and not local:
            chosen.append((gate_id, name, None, "changes local state; CI runs it"))
            continue
        if kind == "tests" and ctx.skip_tests:
            chosen.append((gate_id, name, None, "--skip-tests was passed (CI still runs it)"))
            continue
        if kind == "node" and ctx.skip_tests:
            chosen.append((gate_id, name, None, "--skip-tests was passed (CI still runs it)"))
            continue
        if ctx.shard and ctx.shard[0] != 1 and kind != "tests":
            continue  # FR-094: shard 1 carries the non-test gates; the others only their tests
        chosen.append((gate_id, name, action, None))
    return chosen


def parse_shard(text):
    match = re.fullmatch(r"(\d+)/(\d+)", text or "")
    if not match or not 1 <= int(match.group(1)) <= int(match.group(2)):
        raise argparse.ArgumentTypeError("--shard must be I/N with 1 <= I <= N")
    return int(match.group(1)), int(match.group(2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "list"):
        p = sub.add_parser(name)
        p.add_argument("--ci", action="store_true", help="a CI job: run its OS's gates; a skip fails")
        p.add_argument("--os", choices=sorted(ALL), default=this_os(), help="the OS whose CI gates to select")
        p.add_argument("--skip-tests", action="store_true", help="inner loop: skip the test suites (printed)")
        p.add_argument("--shard", type=parse_shard, help="test shard I/N (FR-094)")
    args = ap.parse_args(argv)
    ctx = Context(args.ci, args.skip_tests, args.shard, args.os)
    gates = selected(ctx)
    if args.cmd == "list":
        for gate_id, name, _action, reason in gates:
            print("{:<4} {}{}".format(gate_id, name, "  (skipped: {})".format(reason) if reason else ""))
        print("{} gates".format(len(gates)))
        return 0

    grouped = bool(os.environ.get("GITHUB_ACTIONS"))
    print("python: {} ({})".format(PY, sys.version.split()[0]))
    results = []
    for gate_id, name, action, reason in gates:
        title = "{}. {}".format(gate_id, name)
        print(("::group::" if grouped else "\n=== ") + title + ("" if grouped else " ==="), flush=True)
        started = time.monotonic()
        status = "SKIP"
        try:
            if action is None:
                raise Skip(reason)
            status = "PASS" if action(ctx) else "FAIL"
        except Skip as why:
            print("SKIPPED: {}".format(why))
            status = "FAIL" if ctx.ci else "SKIP"
        except Exception as exc:  # noqa: BLE001 - a crashing gate is a failed gate, and the rest still run
            print("ERROR: {}: {}".format(exc.__class__.__name__, exc))
            status = "FAIL"
        seconds = time.monotonic() - started
        sys.stdout.flush()
        if grouped:
            print("::endgroup::")
        if status == "FAIL":
            print(("::error::" if grouped else "") + "FAILED: " + title, flush=True)
        results.append((status, title, seconds))

    print("\n=== summary ===")
    for status, title, seconds in results:
        print("  {:<5} {:>7.1f}s  {}".format(status, seconds, title))
    failed = [r for r in results if r[0] == "FAIL"]
    skipped = [r for r in results if r[0] == "SKIP"]
    if not results:
        print("NOT CHECKED - no gate applies to this context")
        return 1
    if failed:
        print("BUNDLE INCONSISTENT - {} of {} gate(s) failed.".format(len(failed), len(results)))
        return 1
    if skipped:
        print("BUNDLE CONSISTENT for the gates that ran - {} gate(s) were SKIPPED; CI runs them.".format(len(skipped)))
        return 0
    print("BUNDLE CONSISTENT - all {} gates passed.".format(len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
