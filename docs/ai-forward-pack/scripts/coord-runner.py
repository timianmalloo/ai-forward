#!/usr/bin/env python3
"""Prepare and run an opt-in, qualified multi-harness coordination contract.

Run `prepare --contract FILE`, qualify the resulting checkout-specific fingerprints,
then `run --run ID --qualification FILE`. `status --run ID` never replays work.
The existing coordinator remains responsible for decisions and semantic review.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time

from bounded_process import run_bounded

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
CAPABILITIES = {"worktree_isolation", "instructions", "hooks", "permissions"}
RANK = {"unsupported": 0, "observed-only": 1, "enforced": 2}
MAX_DOCUMENT = 2 * 1024 * 1024


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_module("runner_core", "coord-core.py")
compiler = load_module("runner_compiler", "prompt-compile.py")
gate = load_module("runner_compile_gate", "verify-compiled-prompt.py")


class Refused(Exception):
    def __init__(self, code, remedy):
        self.code, self.remedy = code, remedy
        super().__init__(code)


def require(condition, code, remedy):
    if not condition:
        raise Refused(code, remedy)


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read_json(path):
    with open(path, "rb") as handle:
        data = handle.read(MAX_DOCUMENT + 1)
    require(len(data) <= MAX_DOCUMENT, "RUN-INPUT", "Use a JSON document below 2 MiB.")
    value = json.loads(data)
    require(isinstance(value, dict), "RUN-INPUT", "Use a JSON object.")
    return value


def private_write(path, value):
    with open(os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
              "w", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded(value).decode("utf-8") + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=10)
    require(result.returncode == 0, "RUN-GIT", "Resolve the repository/index condition and retry with a new run id.")
    return result.stdout.strip()


def identity(value):
    require(isinstance(value, str) and len(value) <= 80 and not core.session_id_error(value),
            "RUN-IDENTITY", "Use a unique portable session/run id of at most 80 characters.")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def relative_path(value):
    return (text(value) and not Path(value).is_absolute() and "\\" not in value
            and not any(part in ("..", ".git") for part in Path(value).parts)
            and str(Path(value)) != ".")


def child_env(worker):
    env = dict(os.environ, AGENT_SESSION=worker["session"], AGENT_HOST=worker["harness"],
               AGENT_WI=worker["session"], PWD=worker["worktree"])
    # The external Claude adapter is its own session, not a nested native CLI turn.
    env.pop("CLAUDECODE", None)
    env.pop("AGENT_NAME", None)
    return env


def file_hash(path):
    if not path.exists():
        return "missing"
    require(path.is_file(), "RUN-BINDING", "Bind regular executable/configuration files, not directories.")
    sha = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            total += len(chunk)
            require(total <= 512 * 1024 * 1024, "RUN-BINDING", "Bind files below 512 MiB.")
            sha.update(chunk)
    return sha.hexdigest()


class Runner:
    def __init__(self, cwd):
        self.cwd = Path(git(cwd, "rev-parse", "--show-toplevel")).resolve()
        self.repo = Path(core.repo_root(self.cwd)).resolve()
        self.root, error = core.resolve_root(self.cwd, os.environ.get("COORD_ROOT"))
        require(not error, "RUN-ROOT", "Use the repository's coordination root.")
        common = Path(git(self.cwd, "rev-parse", "--git-common-dir"))
        self.common = (self.cwd / common).resolve()
        self.lock = threading.Lock()

    def directory(self, run_id):
        identity(run_id)
        parent = self.common / "coord-runs"
        require(not parent.is_symlink(), "RUN-STORE", "Use an ordinary common-git run directory.")
        result = parent / run_id
        require(not result.is_symlink(), "RUN-STORE", "Inspect the existing run directory; do not follow a symlink.")
        return result

    def event(self, manifest, state, worker=None, **fields):
        row = {"kind": "runner", "session": manifest["owner"], "agent": manifest["owner"],
               "wi": manifest["run_id"], "path": "-", "at": time.time(),
               "run_id": manifest["run_id"], "state": state, "worker": worker,
               "usage": "not recorded", "cost": "not recorded", **fields}
        with self.lock:
            core.append_event(self.root, row)
            print(json.dumps(row, sort_keys=True), flush=True)

    def compiled_prompts(self, ids, session):
        path = self.cwd / "docs/audit/audit-log.jsonl"
        entries = {}
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    entries[row.get("id")] = row
        prompts = []
        for entry_id in ids:
            entry = entries.get(entry_id, {})
            doc = entry.get("compiled")
            require(entry.get("kind") == "compilation" and entry.get("dispatchable") is True
                    and isinstance(doc, dict) and not compiler.check_schema(doc)
                    and doc.get("dispatchable") is True and doc.get("mode") != "not-compiled"
                    and not doc.get("decision_requests"), "RUN-COMPILE",
                    "Finish a verified, dispatchable compilation with no unanswered decision requests.")
            raw = entries.get(doc.get("raw_id"), {})
            require(raw.get("kind") == "prompt" and not gate.verify_document(doc, raw.get("prompt", "")),
                    "RUN-COMPILE", "Repair the compilation against its original audit prompt.")
            # A compilation's rendered `prompt` may include native launcher instructions
            # (Codex's template does). Dispatch only deterministically rendered verified
            # sections, never a separately mutable rendition or a nested launch command.
            prompt = ("python3 docs/ai-forward-pack/scripts/audit-log.py start --session "
                      + session + " --skill coordination-worker\n"
                      + "\n\n".join(compiler.render_sections(doc).values())
                      + "\nWork only in your assigned cwd. Follow the plan's owned paths and return evidence to the Owner.\n")
            require(text(prompt) and len(prompt.encode("utf-8")) <= 256 * 1024, "RUN-COMPILE",
                    "Use a nonempty compiled prompt below 256 KiB.")
            prompts.append(prompt)
        return prompts

    def validate(self, contract):
        require(contract.get("schema") == "coord-run/1", "RUN-CONTRACT", "Use schema coord-run/1.")
        identity(contract.get("run_id"))
        identity(contract.get("owner"))
        require(os.environ.get("AGENT_SESSION") == contract["owner"], "RUN-OWNER",
                "Invoke from the declared Owner session (AGENT_SESSION).")
        workers = contract.get("workers")
        require(isinstance(workers, list) and 1 <= len(workers) <= 8
                and integer(contract.get("parallelism"), 1, 4), "RUN-CONTRACT",
                "Declare 1–8 workers and parallelism 1–4.")
        seen, branches = {contract["owner"]}, set()
        events, errors, _ = core.read_events(self.root)
        require(not errors, "RUN-STORE", "Repair unreadable coordination state before preparing new workers.")
        used_sessions = {e.get("session", "").casefold() for e in events if isinstance(e.get("session"), str)}
        prepared = []
        for original in workers:
            require(isinstance(original, dict), "RUN-CONTRACT", "Each worker must be an object.")
            worker = dict(original)
            identity(worker.get("session"))
            require(worker["session"].casefold() not in used_sessions, "RUN-IDENTITY",
                    "Each new worker attempt needs a new session identity, including after a prior run stopped.")
            require(worker["session"].casefold() not in {s.casefold() for s in seen}, "RUN-IDENTITY",
                    "Use distinct worker identities, different from the Owner.")
            seen.add(worker["session"])
            branch = worker.get("branch")
            require(text(branch) and not branch.startswith("-") and branch.casefold() not in branches,
                    "RUN-BRANCH", "Use distinct new work-named git branches.")
            git(self.cwd, "check-ref-format", "--branch", branch)
            branches.add(branch.casefold())
            require(not git(self.cwd, "for-each-ref", "--format=%(refname)", "refs/heads/" + branch),
                    "RUN-BRANCH", "Select a new branch; existing worker branches are never reused.")
            require(worker.get("harness") in ("claude", "codex", "grok", "agy") and
                    worker.get("transport") == ("agy" if worker.get("harness") == "agy" else "acp"),
                    "RUN-TRANSPORT", "Select ACP for Claude/Codex/Grok or the explicit Agy native transport.")
            argv = worker.get("argv")
            require(isinstance(argv, list) and 1 <= len(argv) <= 32
                    and all(text(v) and "\x00" not in v and ("{worktree}" not in v or v == "{worktree}") for v in argv)
                    and argv.count("{worktree}") <= 1 and len(encoded(argv)) <= 65536,
                    "RUN-ARGV", "Supply an installed executable and an explicit argument array, without a shell.")
            if worker["transport"] == "agy":
                require(all(flag in argv for flag in ("--add-dir", "--input-format", "--output-format"))
                        and argv[argv.index("--add-dir") + 1:][:1] == ["{worktree}"]
                        and all(argv[argv.index(flag) + 1:][:1] == ["stream-json"]
                                for flag in ("--input-format", "--output-format")), "RUN-ARGV",
                        "Agy requires --add-dir {worktree} --input-format stream-json --output-format stream-json.")
            require(integer(worker.get("deadline_seconds"), 1, 3600)
                    and integer(worker.get("output_limit"), 1024, 16 * 1024 * 1024)
                    and text(worker.get("fallback")), "RUN-BOUNDS", "Declare finite time/byte bounds and a fallback.")
            caps = worker.get("required_capabilities")
            require(isinstance(caps, dict) and CAPABILITIES <= caps.keys()
                    and all(text(k) and v in ("observed-only", "enforced") for k, v in caps.items()),
                    "RUN-CAPABILITY", "Explicitly require worktree_isolation, instructions, hooks and permissions.")
            bindings = worker.get("binding_files")
            require(isinstance(bindings, list) and bindings and all(text(p) for p in bindings),
                    "RUN-BINDING", "List all effective instruction, hook, trust, permission and adapter configuration files.")
            evidence = worker.get("evidence")
            require(isinstance(evidence, list) and 1 <= len(evidence) <= 32,
                    "RUN-EVIDENCE", "Declare 1–32 file and/or commit evidence items.")
            for item in evidence:
                require(isinstance(item, dict) and (item.get("kind") == "commit" or
                        (item.get("kind") == "file" and relative_path(item.get("path"))
                         and integer(item.get("max_bytes"), 1, 16 * 1024 * 1024))),
                        "RUN-EVIDENCE", "Use commit or bounded file evidence within the worker checkout.")
            ids = worker.get("prompts")
            require(isinstance(ids, list) and 1 <= len(ids) <= 8 and all(text(i) for i in ids),
                    "RUN-COMPILE", "Supply 1–8 completed compilation audit IDs.")
            worker["prompt_texts"] = self.compiled_prompts(ids, worker["session"])
            prepared.append(worker)
        # Headroom accommodates actual checkout/executable paths and immutable metadata.
        require(len(encoded(prepared)) <= 512 * 1024, "RUN-INPUT",
                "Keep the aggregate admitted worker/brief data below 512 KiB; split a larger plan into explicit runs.")
        return prepared

    def prepare(self, contract):
        workers = self.validate(contract)
        require(not git(self.cwd, "ls-files", "-u"), "RUN-INDEX", "Resolve the invoking checkout's unmerged index first.")
        manifest = {"schema": "coord-prepared/1", "run_id": contract["run_id"], "owner": contract["owner"],
                    "parallelism": contract["parallelism"], "base": git(self.cwd, "rev-parse", "HEAD"),
                    "contract_sha256": digest(contract), "workers": workers, "created_at": time.time()}
        directory = self.directory(manifest["run_id"])
        directory.parent.mkdir(mode=0o700, exist_ok=True)
        require(not directory.exists(), "RUN-EXISTS", "Inspect status and retained worktrees; use a new run id for a new attempt.")
        directory.mkdir(mode=0o700)
        private_write(directory / "contract.json", contract)
        self.event(manifest, "preparing", contract_sha256=digest(contract))
        try:
            reservations = self.common / "coord-run-sessions"
            require(not reservations.is_symlink(), "RUN-STORE", "Inspect the session reservation directory.")
            reservations.mkdir(mode=0o700, exist_ok=True)
            for worker in workers:
                try:
                    private_write(reservations / worker["session"].casefold(), {"run_id": manifest["run_id"]})
                except FileExistsError:
                    raise Refused("RUN-IDENTITY", "A prepared attempt already reserved this worker identity; use a new identity.")
            for worker in workers:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = core.cmd_worktree(self.root, self.repo, "new", self.cwd, time.time(),
                        session=worker["session"], agent=worker["session"], branch=worker["branch"], base=manifest["base"])
                require(result == 0, "RUN-WORKTREE", "Inspect the actual git worktree inventory; retain partial work and use a new run id.")
                inventory, error = core.worktree_inventory(self.repo)
                rows = [r for r in inventory or [] if r.get("branch") == worker["branch"]]
                require(not error and len(rows) == 1, "RUN-WORKTREE", "Resolve the worker's unique branch/worktree mapping.")
                worker["worktree"] = str(Path(rows[0]["path"]).resolve())
                require(Path(worker["worktree"]) != self.repo and rows[0].get("head") == manifest["base"],
                        "RUN-WORKTREE", "A worker must have a separate checkout at the invoking base commit.")
                worker["argv"] = [arg.replace("{worktree}", worker["worktree"]) for arg in worker["argv"]]
                private_write(directory / (worker["session"] + ".brief.json"), {"prompts": worker["prompt_texts"], "fallback": worker["fallback"]})
                self.event(manifest, "worker_prepared", worker=worker["session"], branch=worker["branch"],
                           worktree=worker["worktree"], manual_brief=str(directory / (worker["session"] + ".brief.json")))
                worker["argv"][0] = self.resolve_executable(worker)
            private_write(directory / "manifest.json", manifest)
            self.event(manifest, "prepared", manifest_sha256=digest(manifest), base=manifest["base"])
        except Exception:
            self.event(manifest, "prepare_failed", code="RUN-PREPARE", remedy="Inspect retained trees and contract; no automatic retry.")
            raise
        return self.public_manifest(manifest)

    def public_manifest(self, manifest):
        return {"run_id": manifest["run_id"], "state": "prepared", "base": manifest["base"],
                "workers": [{"session": w["session"], "worktree": w["worktree"], "branch": w["branch"],
                             "manual_brief": str(self.directory(manifest["run_id"]) / (w["session"] + ".brief.json"))}
                            for w in manifest["workers"]]}

    def load(self, run_id, allow_partial=False):
        if allow_partial and not (self.directory(run_id) / "manifest.json").exists():
            contract = read_json(self.directory(run_id) / "contract.json")
            require(contract.get("run_id") == run_id and text(contract.get("owner")),
                    "RUN-STORE", "Inspect the retained partial preparation contract.")
            return {"schema": "coord-partial/1", "run_id": run_id, "owner": contract["owner"],
                    "workers": contract.get("workers", []), "contract_sha256": digest(contract)}
        manifest = read_json(self.directory(run_id) / "manifest.json")
        require(manifest.get("schema") == "coord-prepared/1" and manifest.get("run_id") == run_id,
                "RUN-STORE", "Inspect the immutable prepared manifest; do not reconstruct an attempt by guessing.")
        rows, errors, _ = core.read_events(self.root)
        admissions = [r for r in rows if r.get("kind") == "runner" and r.get("run_id") == run_id
                      and r.get("state") == "prepared" and r.get("session") == manifest["owner"]]
        require(not errors and len(admissions) == 1 and admissions[0].get("manifest_sha256") == digest(manifest),
                "RUN-STORE", "Prepared manifest must match its recorded admission hash.")
        return manifest

    def resolve_executable(self, worker):
        """Resolve using the child's cwd, including relative executable/PATH entries."""
        cwd = Path(worker["worktree"])
        name = worker["argv"][0]
        env = child_env(worker)
        if os.sep in name:
            candidate = Path(name)
            path = candidate if candidate.is_absolute() else cwd / candidate
            executable = str(path) if path.is_file() and os.access(path, os.X_OK) else None
        else:
            search_path = os.pathsep.join(str(Path(p) if Path(p).is_absolute() else cwd / p)
                                          for p in env.get("PATH", os.defpath).split(os.pathsep))
            executable = shutil.which(name, path=search_path)
        require(executable is not None, "RUN-EXECUTABLE", "Install the selected adapter or continue with the compiled manual brief; no model launched.")
        return str(Path(executable).resolve())

    def fingerprint(self, manifest, worker):
        env = child_env(worker)
        self.worker_identity(manifest, worker)
        executable = self.resolve_executable(worker)
        files = {}
        for value in worker["binding_files"]:
            path = Path(value)
            if not path.is_absolute():
                path = Path(worker["worktree"]) / path
            files[str(path.resolve())] = file_hash(path)
        return digest({"manifest_sha256": digest(manifest), "worker": worker,
                       "executable": str(Path(executable).resolve()), "executable_sha256": file_hash(Path(executable)),
                       "binding_files": files, "environment_sha256": digest(env)})

    def fingerprints(self, manifest):
        return {"run_id": manifest["run_id"], "qualification": "not performed",
                "fingerprints": {w["session"]: self.fingerprint(manifest, w) for w in manifest["workers"]}}

    def leader(self, owner, timeout=2, renew_run=None):
        require(timeout > 0, "RUN-LEADER", "Lease or attempt deadline expired; retain the worker evidence.")
        command = ([sys.executable, str(HERE / "coord-runner.py"), "_renew", "--run", renew_run]
                   if renew_run else [sys.executable, str(HERE / "coord-core.py"), "leader", "who", "--json"])
        result = run_bounded(command,
                             cwd=self.cwd, env=dict(os.environ, AGENT_SESSION=owner),
                             timeout_seconds=timeout, stdout_limit=8192, stderr_limit=2048)
        require(result.returncode == 0 and not result.timed_out and not result.limit_exceeded
                and not result.cleanup_error and result.contained, "RUN-LEADER",
                "Establish a live designation for this Owner or inspect the bounded leader command failure.")
        if renew_run:
            return None
        row = json.loads(result.stdout)
        require(row.get("state") == "live" and row.get("leader") == owner,
                "RUN-LEADER", "Use the live designated Owner; the runner never pins or steals leadership.")
        return row

    def renew_admitted(self, manifest):
        """Bounded helper: expected epoch is checked in the SAME CAS attempt as renewal."""
        admission = read_json(self.directory(manifest["run_id"]) / "started.json")
        owner = manifest["owner"]
        require(os.environ.get("AGENT_SESSION") == owner, "RUN-LEADER", "Only the admitted Owner may renew.")
        row, oid, error = core.leader_read(self.repo)
        now = time.time()
        require(not error and row and row.get("leader") == owner
                and row.get("epoch") == admission.get("epoch") and core.leader_state(row, now) == "live",
                "RUN-LEADER", "The admitted designation changed or expired; do not renew its successor.")
        updated, error = core.leader_decide("renew", row, now, owner, owner, row["ttl"],
                                          host=row.get("host"), tree=row.get("tree"))
        require(not error, "RUN-LEADER", "Renewal was refused by the existing designation protocol.")
        new_oid, error = core.leader_write(self.repo, updated, oid)
        require(not error, "RUN-LEADER", "The designation changed during renewal; stop this attempt.")
        core.append_event(self.root, {"kind": "leader", "type": "leader", "action": "renew",
            "session": owner, "agent": owner, "wi": manifest["run_id"], "path": "-", "at": now,
            "leader": owner, "epoch": row["epoch"], "outcome": "ok", "ref_old": oid, "ref_new": new_oid,
            "expires_at": updated["expires_at"]})
        return {"state": "renewed", "epoch": row["epoch"], "expires_at": updated["expires_at"]}

    def worker_identity(self, manifest, worker, initial=False):
        cwd = Path(worker["worktree"])
        common = Path(git(cwd, "rev-parse", "--git-common-dir"))
        inventory, error = core.worktree_inventory(self.repo)
        matches = [r for r in inventory or [] if Path(r["path"]).resolve() == cwd]
        require((cwd / common).resolve() == self.common and not error and len(matches) == 1
                and matches[0].get("branch") == worker["branch"], "RUN-WORKTREE",
                "Use the registered worktree of this repository; a substituted clone is not the assigned checkout.")
        require(cwd.resolve() != self.repo and Path(git(cwd, "rev-parse", "--show-toplevel")).resolve() == cwd
                and git(cwd, "symbolic-ref", "--short", "HEAD") == worker["branch"],
                "RUN-WORKTREE", "Restore the assigned checkout and branch before reviewing evidence.")
        if initial:
            require(git(cwd, "rev-parse", "HEAD") == manifest["base"], "RUN-WORKTREE",
                    "Prepared worker HEAD changed; inspect work and prepare an explicit new attempt.")

    def verify(self, manifest, worker):
        self.worker_identity(manifest, worker)
        receipts = []
        cwd = Path(worker["worktree"])
        for expected in worker["evidence"]:
            if expected["kind"] == "commit":
                head = git(cwd, "rev-parse", "HEAD")
                require(head != manifest["base"], "RUN-EVIDENCE", "Return a new descendant commit.")
                git(cwd, "merge-base", "--is-ancestor", manifest["base"], head)
                receipts.append({"kind": "commit", "commit": head})
            else:
                # Each component is opened relative to an already-open directory, so a
                # renamed parent cannot substitute an outside artifact after a path check.
                parts = Path(expected["path"]).parts
                directory_fd = os.open(str(cwd), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    for part in parts[:-1]:
                        next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                        os.close(directory_fd)
                        directory_fd = next_fd
                    fd = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory_fd)
                finally:
                    os.close(directory_fd)
                with os.fdopen(fd, "rb") as handle:
                    info = os.fstat(handle.fileno())
                    require(stat.S_ISREG(info.st_mode), "RUN-EVIDENCE", "Return a regular file.")
                    data = handle.read(expected["max_bytes"] + 1)
                    after = os.fstat(handle.fileno())
                    require(0 < len(data) <= expected["max_bytes"] and info.st_mtime_ns == after.st_mtime_ns
                            and info.st_size == after.st_size, "RUN-EVIDENCE", "Return a stable nonempty artifact within its byte bound.")
                receipts.append({"kind": "file", "path": expected["path"], "bytes": len(data),
                                 "sha256": hashlib.sha256(data).hexdigest()})
        return receipts

    def status(self, manifest):
        rows, errors, _ = core.read_events(self.root)
        require(not errors, "RUN-STORE", "Repair unreadable coordination events before deriving status.")
        events = [r for r in rows if r.get("kind") == "runner" and r.get("run_id") == manifest["run_id"]
                  and r.get("session") == manifest["owner"]]
        if manifest["schema"] == "coord-partial/1":
            retained = {e["worker"]: e for e in events if e.get("state") == "worker_prepared"}
            return {"run_id": manifest["run_id"], "state": "prepare_failed" if any(
                    e.get("state") == "prepare_failed" for e in events) else "preparation_interrupted",
                    "workers": [{"session": w["session"], "branch": w["branch"],
                                 "worktree": retained.get(w["session"], {}).get("worktree"),
                                 "manual_brief": retained.get(w["session"], {}).get("manual_brief")}
                                for w in manifest["workers"]],
                    "remedy": "Retain the reported trees and contract; prepare a new explicit attempt, never resume partially by guessing."}
        terminal = next((e for e in reversed(events) if e.get("state") == "finished"), None)
        if terminal:
            started = read_json(self.directory(manifest["run_id"]) / "started.json")
            require(started.get("owner") == manifest["owner"] and any(e.get("state") == "started"
                    and e.get("epoch") == started.get("epoch")
                    and e.get("qualification_sha256") == started.get("qualification_sha256") for e in events)
                    and terminal.get("result", {}).get("epoch") == started.get("epoch"),
                    "RUN-STORE", "Completion requires matching Owner admission and terminal evidence.")
            return terminal["result"]
        return {"run_id": manifest["run_id"], "state": "interrupted_or_running" if
                (self.directory(manifest["run_id"]) / "started.json").exists() else "prepared",
                "workers": self.public_manifest(manifest)["workers"], "events": len(events),
                "remedy": "Inspect retained evidence; never replay an interrupted run automatically."}

    def run(self, manifest, qualification):
        require(os.name == "posix", "RUN-PLATFORM", "Use manual briefs until interactive containment is qualified on this platform.")
        owner = manifest["owner"]
        require(os.environ.get("AGENT_SESSION") == owner, "RUN-OWNER", "Invoke from the admitted Owner session.")
        require(qualification.get("schema") == "coord-qualification/1" and isinstance(qualification.get("workers"), dict),
                "RUN-QUALIFICATION", "Supply measured checkout-specific qualification, or use the retained manual briefs.")
        for worker in manifest["workers"]:
            q = qualification["workers"].get(worker["session"], {})
            require(isinstance(q, dict) and all(text(q.get(k)) for k in
                    ("version", "evidence", "effective_policy", "trust")) and q.get("fingerprint") == self.fingerprint(manifest, worker),
                    "RUN-QUALIFICATION", "Reobserve effective policy, trust and required hooks for this fingerprint; mode labels are not evidence.")
            caps = q.get("capabilities", {})
            require(isinstance(caps, dict) and all(RANK.get(caps.get(k), 0) >= RANK[v]
                    for k, v in worker["required_capabilities"].items()), "RUN-QUALIFICATION",
                    "Qualify every declared capability at the required strength or use the manual brief.")
            self.worker_identity(manifest, worker, initial=True)
        admission = self.leader(owner)
        directory = self.directory(manifest["run_id"])
        require(not (directory / "started.json").exists(), "RUN-STARTED", "Read status; use a new run id and worker identities for a new attempt.")
        private_write(directory / "started.json", {"owner": owner, "epoch": admission["epoch"],
                      "at": time.time(), "qualification_sha256": digest(qualification)})
        self.event(manifest, "started", epoch=admission["epoch"], qualification_sha256=digest(qualification),
                   qualification_source="Owner attestation; not runner enforcement")
        stop = threading.Event()
        lease = {"expires_at": admission["expires_at"], "reason": None}
        old_handlers = {}

        def cancel_signal(signum, _frame):
            lease["reason"] = "RUN-CANCELLED"
            stop.set()

        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.signal(signum, cancel_signal)

        def cancelled():
            if time.time() >= lease["expires_at"]:
                lease["reason"] = "RUN-LEADER"
                stop.set()
            return stop.is_set()

        def fence(remaining):
            if cancelled():
                return False
            try:
                row = self.leader(owner, timeout=min(2, remaining, lease["expires_at"] - time.time()))
                require(row["epoch"] == admission["epoch"], "RUN-LEADER", "The leader epoch changed; no further dispatch is admitted.")
                lease["expires_at"] = row["expires_at"]
                return not cancelled()
            except (Refused, OSError, ValueError):
                lease["reason"] = "RUN-LEADER"
                stop.set()
                return False

        def execute(worker):
            from coord_transport import run_session
            if cancelled():
                result = {"session": worker["session"], "state": "cancelled", "code": lease["reason"]}
            else:
                try:
                    # A queued worker may wait behind another turn. Bind the *current*
                    # executable/configuration/checkout again at its actual launch seam.
                    self.worker_identity(manifest, worker, initial=True)
                    require(self.fingerprint(manifest, worker) == qualification["workers"][worker["session"]]["fingerprint"],
                            "RUN-QUALIFICATION", "The queued worker changed before launch; requalify a new explicit attempt.")
                    self.event(manifest, "worker_started", worker=worker["session"], harness=worker["harness"])
                    transport = run_session(worker["transport"], worker["argv"], worker["worktree"], child_env(worker),
                        worker["prompt_texts"], worker["deadline_seconds"], worker["output_limit"],
                        lambda event: self.event(manifest, "progress", worker=worker["session"], observation=event),
                        cancelled, fence)
                    transport_state = {"blocked": "blocked", "cancelled": "cancelled"}.get(transport["outcome"], "failed")
                    result = {"session": worker["session"], "state": transport_state, "transport": transport,
                              "manual_brief": str(directory / (worker["session"] + ".brief.json"))}
                    if transport["outcome"] == "complete" and not cancelled():
                        try:
                            result["receipts"] = self.verify(manifest, worker)
                            result["state"] = "ready_for_review"
                        except (Refused, OSError, subprocess.SubprocessError):
                            result.update(state="evidence_incomplete", code="RUN-EVIDENCE")
                except Refused as exc:
                    result = {"session": worker["session"], "state": "blocked", "code": exc.code,
                              "manual_brief": str(directory / (worker["session"] + ".brief.json"))}
                except Exception as exc:
                    result = {"session": worker["session"], "state": "failed", "code": "RUN-WORKER",
                              "error_type": type(exc).__name__}
            self.event(manifest, "worker_finished", worker=worker["session"], result=result)
            return result

        results = []
        try:
            with ThreadPoolExecutor(max_workers=manifest["parallelism"]) as pool:
                pending = {pool.submit(execute, worker) for worker in manifest["workers"]}
                next_check = time.monotonic()
                while pending:
                    done, pending = wait(pending, timeout=0.1, return_when=FIRST_COMPLETED)
                    results.extend(f.result() for f in done)
                    if not stop.is_set() and time.monotonic() >= next_check:
                        if fence(2):
                            if lease["expires_at"] - time.time() <= float(admission["ttl"]) * 2 / 3:
                                try:
                                    self.leader(owner, timeout=min(2, lease["expires_at"] - time.time()), renew_run=manifest["run_id"])
                                    fence(2)
                                except (Refused, OSError, ValueError):
                                    lease["reason"] = "RUN-LEADER"
                                    stop.set()
                        next_check = time.monotonic() + 0.5
        finally:
            stop.set()
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
        ready = not lease["reason"] and all(r["state"] == "ready_for_review" for r in results)
        result = {"run_id": manifest["run_id"], "state": "ready_for_review" if ready else "incomplete",
                  "workers": sorted(results, key=lambda r: r["session"]), "epoch": admission["epoch"],
                  "semantic_acceptance": "Owner review required", "code": lease["reason"]}
        self.event(manifest, "finished", result=result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare").add_argument("--contract", required=True)
    for command in ("run", "status", "fingerprint", "_renew"):
        item = sub.add_parser(command)
        item.add_argument("--run", required=True)
        if command == "run":
            item.add_argument("--qualification", required=True)
    args = parser.parse_args(argv)
    try:
        runner = Runner(Path.cwd())
        if args.command == "prepare":
            result = runner.prepare(read_json(args.contract))
        else:
            manifest = runner.load(args.run, allow_partial=args.command == "status")
            if args.command == "fingerprint":
                result = runner.fingerprints(manifest)
            elif args.command == "status":
                result = runner.status(manifest)
            elif args.command == "_renew":
                result = runner.renew_admitted(manifest)
            else:
                result = runner.run(manifest, read_json(args.qualification))
        print(json.dumps(result, sort_keys=True))
        return 3 if args.command == "run" and result["state"] != "ready_for_review" else 0
    except Refused as exc:
        print(json.dumps({"state": "blocked", "code": exc.code, "remedy": exc.remedy}))
        return 2
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "blocked", "code": "RUN-INPUT", "error_type": type(exc).__name__,
                          "remedy": "Inspect the contract, retained run state and local dependencies; do not replay an attempt."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
