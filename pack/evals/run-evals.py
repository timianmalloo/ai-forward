#!/usr/bin/env python3
"""run-evals.py — golden-task assertion runner for the AI-Forward Pack (pack maintenance).

A skill is prompt-code; this is its regression suite. Each case is a JSON file:
  { "id": "...", "skill": "design", "prompt": "<the golden task to give the agent>",
    "setup": [{"path": "...", "content": "..."}],          // optional workspace seed
    "assertions": [ ... ] }                                 // objective post-conditions

Assertion types (all run against --workspace):
  {"type":"file-exists","path":"docs/design/x.md"}
  {"type":"file-absent","path":"src/tmp.cs"}
  {"type":"grep","path":"...","pattern":"<regex>"}          // must match
  {"type":"not-grep","path":"...","pattern":"<regex>"}      // must not match
  {"type":"frontmatter-valid","path":"..."}                 // via scripts/docs-graph.py parser
  {"type":"index-has","id":"design-x"}                      // docs/docs-index.js contains entry
  {"type":"cmd-exit","cmd":["python3","docs/ai-forward-pack/scripts/docs-graph.py","validate"],"exit":0}

Flow per case: (1) `--setup` seeds the workspace; (2) YOU run the skill against it (paste
case["prompt"] into Claude Code / Copilot); (3) `--check` evaluates assertions. Or run all
three in one pass with `--exec "<command>"`, which seeds, invokes a headless agent CLI, then
checks. The command receives `AIF_EVAL_WORKSPACE`, `AIF_EVAL_PROMPT`, and `AIF_EVAL_CASE`.
Prompt and workspace interpolation are rejected; commands must read the environment variables
to avoid shell injection and quoting defects.
With `--exec --cases`, each case runs in its own
`<workspace>/<id>` subdirectory. CI runs --check (or --exec) over workspaces. Exit 0 = all pass.
"""

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import PurePosixPath, PureWindowsPath

SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bounded_process import run_bounded  # noqa: E402

MAX_ASSERTION_FILE_BYTES = 1024 * 1024
CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_case_id(case_id):
    if not isinstance(case_id, str) or not CASE_ID_PATTERN.fullmatch(case_id):
        raise ValueError("case id must be a lowercase kebab-case slug")
    return case_id


def workspace_path(workspace, relative_path):
    windows_path = PureWindowsPath(relative_path)
    posix_path = PurePosixPath(relative_path)
    path_parts = [part for part in re.split(r"[\\/]+", relative_path) if part]
    if (
        not relative_path
        or os.path.isabs(relative_path)
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or posix_path.is_absolute()
        or ".." in path_parts
    ):
        raise ValueError("path must be a non-empty workspace-relative path")
    workspace_root = os.path.realpath(workspace)
    candidate = os.path.realpath(os.path.join(workspace_root, relative_path))
    try:
        contained = os.path.commonpath([candidate, workspace_root]) == workspace_root
    except ValueError:
        contained = False
    if not contained:
        raise ValueError("path escapes the eval workspace")
    return candidate


def read_text_bounded(path, maximum=MAX_ASSERTION_FILE_BYTES):
    with open(path, "rb") as source:
        data = source.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError(f"file exceeds {maximum} byte assertion limit")
    return data.decode("utf-8")


def process_failures(result, label, expected_exit=None):
    failures = []
    if result.timed_out:
        failures.append(f"{label}: exceeded deadline")
    if result.limit_exceeded:
        failures.append(f"{label}: exceeded {result.limit_exceeded} limit")
    if not result.contained:
        detail = (
            result.cleanup_error or result.containment_error or "unknown cleanup error"
        )
        failures.append(f"{label}: process containment failed ({detail})")
    if expected_exit is not None and result.returncode != expected_exit:
        failures.append(f"{label}: got {result.returncode}, want {expected_exit}")
    if failures and result.stderr:
        failures.append(f"{label}: stderr: {result.stderr[:2048]}")
    return failures


def load_graph_module(workspace):
    candidates = [
        os.path.join(
            workspace,
            "docs",
            "ai-forward-pack",
            "scripts",
            "docs-graph.py",
        ),
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "docs-graph.py",
        ),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            spec = importlib.util.spec_from_file_location("dg", candidate)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return None


def command_for_host(command):
    resolved = list(command)
    if os.name == "nt" and resolved and resolved[0] == "python3":
        resolved[0] = sys.executable
    return resolved


def shell_command(command):
    if os.name == "nt":
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", command]
    return ["/bin/sh", "-c", command]


def check(case, ws):
    fails = []
    dg = load_graph_module(ws)
    for a in case.get("assertions", []):
        t = a["type"]
        try:
            p = workspace_path(ws, a["path"]) if a.get("path") else None
            if t == "file-exists" and not os.path.exists(p):
                fails.append(f"file-exists: {a['path']}")
            elif t == "file-absent" and os.path.exists(p):
                fails.append(f"file-absent: {a['path']}")
            elif t == "grep":
                if not os.path.exists(p) or not re.search(
                    a["pattern"], read_text_bounded(p), re.S
                ):
                    fails.append(f"grep '{a['pattern']}' in {a['path']}")
            elif t == "not-grep":
                if os.path.exists(p) and re.search(
                    a["pattern"], read_text_bounded(p), re.S
                ):
                    fails.append(f"not-grep '{a['pattern']}' in {a['path']}")
            elif t == "frontmatter-valid":
                if not dg:
                    fails.append("frontmatter-valid: docs-graph.py not found")
                    continue
                fm, err = dg.parse_frontmatter(read_text_bounded(p))
                if err:
                    fails.append(f"frontmatter-valid {a['path']}: {err}")
            elif t == "index-has":
                ip = workspace_path(ws, os.path.join("docs", "docs-index.js"))
                m = (
                    re.search(
                        r"window\.DOCS_INDEX\s*=\s*(\{.*\});?\s*$",
                        read_text_bounded(ip),
                        re.S,
                    )
                    if os.path.exists(ip)
                    else None
                )
                ids = [
                    e.get("id")
                    for e in (json.loads(m.group(1))["artifacts"] if m else [])
                ]
                if a["id"] not in ids:
                    fails.append(f"index-has: {a['id']}")
            elif t == "cmd-exit":
                r = run_bounded(command_for_host(a["cmd"]), cwd=ws, timeout_seconds=30)
                fails.extend(
                    process_failures(r, f"cmd-exit {a['cmd']}", a.get("exit", 0))
                )
        except Exception as e:
            fails.append(f"{t}: error {e}")
    return fails


def seed(case, ws):
    for s in case.get("setup", []):
        p = workspace_path(ws, s["path"])
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as seeded:
            seeded.write(s["content"])


def run_exec(case, ws, template, timeout_seconds):
    case_id = validate_case_id(case.get("id"))
    ws = os.path.abspath(ws)
    os.makedirs(ws, exist_ok=True)
    seed(case, ws)
    if "{prompt}" in template:
        raise ValueError(
            "--exec templates must read AIF_EVAL_PROMPT instead of interpolating {prompt}"
        )
    if "{workspace}" in template:
        raise ValueError(
            "--exec templates must read AIF_EVAL_WORKSPACE instead of interpolating {workspace}"
        )
    env = dict(
        os.environ,
        AIF_EVAL_WORKSPACE=ws,
        AIF_EVAL_PROMPT=case["prompt"],
        AIF_EVAL_CASE=case_id,
    )
    print(f"exec: {case_id} -> {ws}")
    r = run_bounded(
        shell_command(template),
        cwd=ws,
        env=env,
        timeout_seconds=timeout_seconds,
        stdout_limit=1024 * 1024,
        stderr_limit=256 * 1024,
        memory_limit=2 * 1024 * 1024 * 1024,
        process_limit=64,
    )
    fails = check(case, ws)
    fails[0:0] = process_failures(r, "exec command", 0)
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--cases",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases"),
    )
    ap.add_argument("--case", default=None, help="single case file")
    ap.add_argument("--workspace", required=True)
    ap.add_argument(
        "--setup", action="store_true", help="seed workspace from case setup, then exit"
    )
    ap.add_argument("--check", action="store_true", help="evaluate assertions")
    ap.add_argument(
        "--exec",
        default=None,
        metavar="CMD",
        help="seed, run CMD (a headless agent reading the AIF_EVAL_* environment), then check",
    )
    ap.add_argument(
        "--exec-timeout",
        type=int,
        default=1800,
        help="hard deadline in seconds for each --exec command (default: 1800)",
    )
    args = ap.parse_args()
    files = (
        [args.case]
        if args.case
        else sorted(
            os.path.join(args.cases, filename)
            for filename in os.listdir(args.cases)
            if filename.endswith(".json")
        )
    )
    total_fail = 0
    for cf in files:
        with open(cf, encoding="utf-8") as case_file:
            case = json.load(case_file)
        case_id = validate_case_id(case.get("id"))
        if args.exec:
            ws = (
                args.workspace
                if args.case
                else workspace_path(args.workspace, case_id)
            )
            fails = run_exec(case, ws, args.exec, args.exec_timeout)
            print(
                f"{'PASS' if not fails else 'FAIL'}  {case_id}"
                + ("" if not fails else "\n  - " + "\n  - ".join(fails))
            )
            total_fail += len(fails)
            continue
        if args.setup:
            seed(case, args.workspace)
            print(f"setup: {case_id} -> {args.workspace}")
            print(f"PROMPT for the agent:\n{case['prompt']}\n")
        if args.check:
            fails = check(case, args.workspace)
            print(
                f"{'PASS' if not fails else 'FAIL'}  {case_id}"
                + ("" if not fails else "\n  - " + "\n  - ".join(fails))
            )
            total_fail += len(fails)
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
