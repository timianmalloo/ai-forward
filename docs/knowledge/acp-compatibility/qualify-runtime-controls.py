#!/usr/bin/env python3
"""Opt-in native lifecycle smoke test; never a reusable profile qualification.

Run from a fresh clone with an installed adapter/CLI and its normal credentials.
No package download, trust change, existing-session contact or automatic approval.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pack/scripts"))
from coord_transport import run_session
from coord_runtime import Controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("claude", "codex", "grok", "agy"), required=True)
    parser.add_argument("--executable", required=True, help="Installed adapter/CLI executable; never a shell command")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ask", action="store_true", help="Claude only: pause for explicit once-only approval of a disposable file write")
    args = parser.parse_args()
    if args.ask and args.harness != "claude":
        parser.error("The concrete manual permission canary is qualified only for Claude ACP")
    executable = shutil.which(args.executable)
    if not executable:
        parser.error("Install the selected native adapter/CLI first")
    output = args.output.resolve()
    if output.exists():
        parser.error("Use a new output path; evidence is never overwritten")
    controls = Controls(output.with_suffix(".controls")) if args.ask else None
    observations = []
    pending = {}
    with tempfile.TemporaryDirectory(prefix="coord-native-runtime-") as directory:
        workspace = Path(directory).resolve()
        target = workspace / "runtime-canary.txt"
        if args.ask:
            (workspace / ".claude").mkdir()
            (workspace / ".claude/settings.json").write_text(json.dumps({"permissions": {"defaultMode": "default"}}))
        argv = [executable]
        if args.harness == "grok":
            argv += ["agent", "--no-leader", "stdio"]
        if args.harness == "agy":
            argv += ["--add-dir", str(workspace), "--input-format", "stream-json", "--output-format", "stream-json"]
        env = dict(os.environ, AGENT_SESSION="native-runtime-" + args.harness, AGENT_HOST=args.harness)
        env.pop("CLAUDECODE", None)
        if args.harness == "codex":
            env["CODEX_PATH"] = shutil.which("codex") or "codex"
        messages = ["This is a bounded transport canary. Reply SECOND. Do not use tools, edit files or spawn agents.", False]
        def next_prompt(remaining):
            return messages.pop(0)
        def permission(request, remaining):
            key = request["requestSequence"]
            if key not in pending:
                row = controls.permission(request, expires_at=time.time() + remaining)
                pending[key] = row
                print(json.dumps({"state": "permission_pending", "id": row["id"],
                                  "detail_path": str(controls.directory / (row["id"] + ".json")),
                                  "allowed_canary_path": str(target)}), flush=True)
            return controls.answer(pending[key]["id"])
        prompt = "This is a bounded transport canary. Reply FIRST. Do not use tools, edit files or spawn agents."
        if args.ask:
            prompt = ("This is a finite interactive permission canary. Use exactly one native file edit to write "
                      "RUNTIME_CANARY to " + str(target) + ". Wait for explicit permission. If denied, stop. "
                      "Do not use shell, read other files, change permissions or spawn agents.")
        result = run_session("agy" if args.harness == "agy" else "acp", argv, str(workspace), env,
                             [prompt], 180, 4 * 1024 * 1024, observations.append, lambda: False,
                             next_prompt=next_prompt, permission_handler=permission if args.ask else None,
                             max_turns=2)
        evidence = {"schema": "native-runtime-canary/1", "harness": args.harness,
                    "scope": "native lifecycle; not ownership/trust qualification", "transport": result,
                    "dynamic_prompt_delivered": result["turns_completed"] == 2,
                    "events": observations, "canary_file_written": target.exists(),
                    "usage": "not recorded", "existing_session_contacted": False}
        if args.ask and target.exists():
            evidence["canary_content_matches"] = target.read_text().strip() == "RUNTIME_CANARY"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x") as stream:
            json.dump(evidence, stream, indent=2)
        print(json.dumps({"state": result["outcome"], "code": result["code"], "evidence": str(output)}), flush=True)
        return 0 if result["outcome"] == "complete" and result["turns_completed"] == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
