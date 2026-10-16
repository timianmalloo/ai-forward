# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Install AI-Forward into the current project using its source deployment map.

Requires Git; run with uv (Linux, macOS, Windows) or Python 3.10+.
Owner: @ahutanu. No global configuration, commits, or trust changes.
"""
import sys

# Isolate the CLI before even argparse/json can find a project module. Only sys
# and the interpreter's built-in OS module are used until the guard is
# established; no project/source import participates. POSIX restarts with
# interpreter isolation. Windows sanitizes import/startup state in-process
# because the CRT spawn/exec command line loses quoted paths with spaces.
if __name__ == "__main__" and sys.platform == "win32":
    try:
        _entry_nt = __import__("nt")
        _entry_prefix = sys.base_prefix.rstrip("\\/").casefold() + "\\"
        sys.path[:] = [item for item in sys.path
                       if item and item.replace("/", "\\").casefold().startswith(_entry_prefix)]
        sys.dont_write_bytecode = True
        for _entry_key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE",
                           "PYTHONEXECUTABLE"):
            try:
                _entry_nt.unsetenv(_entry_key)
            except OSError:
                pass
        _entry_nt.putenv("PYTHONNOUSERSITE", "1")
        _AI_FORWARD_ENTRY_ISOLATED = True
    except (OSError, RuntimeError, AttributeError) as exc:
        print(f"AI-Forward bootstrap failed: cannot isolate entry interpreter: {exc}; "
              "run the saved wrapper with Python 3.10+ -I -B", file=sys.stderr)
        sys.exit(1)
elif __name__ == "__main__" and not (sys.flags.isolated and sys.flags.dont_write_bytecode):
    try:
        if "posix" not in sys.builtin_module_names or not sys.executable or not __file__:
            raise RuntimeError("a supported interpreter and saved wrapper file are required")
        _entry_os = __import__("posix")
        # __file__, not caller-controlled argv[0], identifies the already-running
        # wrapper. -- protects option-looking filenames; stdin, cwd, arguments
        # and status are inherited without a shell.
        _entry_args = [sys.executable, "-I", "-B", "--", __file__, *sys.argv[1:]]
        _entry_os.execv(sys.executable, _entry_args)
    except (OSError, RuntimeError, AttributeError) as exc:
        print(f"AI-Forward bootstrap failed: cannot isolate entry interpreter: {exc}; "
              "run the saved wrapper with Python 3.10+ -I -B", file=sys.stderr)
        sys.exit(1)

import argparse
import hashlib
import importlib.util
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import types
from typing import Any, cast

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        try:
            cast(Any, _stream).reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

DEFAULT_REPO = "https://github.com/timianmalloo/ai-forward.git"
RECEIPT = "docs/ai-forward-pack/bootstrap-receipt.json"


class BootstrapError(RuntimeError):
    pass


def run(command, cwd=None, timeout=180):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1")
    # Installer children and their descendants must not import target-selected
    # startup modules. Immediate Python children also use -I -B; clearing the
    # inherited startup path protects nested source-applier subprocesses.
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE",
                "PYTHONEXECUTABLE"):
        env.pop(key, None)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE"):
        env.pop(key, None)
    try:
        with subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding="utf-8", errors="replace",
                              start_new_session=os.name != "nt",
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0) as process:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, timeout=10)
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=10)
                raise BootstrapError(f"{Path(command[0]).name} interrupted or exceeded {timeout}s; process tree stopped") from exc
            if process.returncode:
                raise BootstrapError(stderr.strip() or stdout.strip() or
                                     f"{Path(command[0]).name} exited {process.returncode}")
            return stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BootstrapError(f"Cannot complete {Path(command[0]).name}: {exc}") from exc


def pack(source, target, mode, project=None, no_baselines=False, attributes=None):
    command = [sys.executable, "-I", "-B", str(source / "pack/scripts/pack-apply.py"), mode,
               "--source", str(source), "--target", str(target), "--install", "--json"]
    if project:
        command.extend(["--project", project])
    if no_baselines:
        command.append("--no-baselines")
    if mode == "apply" and attributes is not None:
        # Keep policy payloads out of argv (Windows command-line length limit).
        # This trusted launcher lives beside the disposable source, not in the project.
        launcher = source.parent / "bootstrap-apply.py"
        launcher.write_text(
            "import importlib.util,json,sys\n"
            "from pathlib import Path\n"
            "def load(name,path):\n"
            " spec=importlib.util.spec_from_file_location(name,path)\n"
            " module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n"
            " return module\n"
            "wrapper=load('bootstrap',sys.argv[1])\n"
            "deployment=load('bootstrap_pack_apply',sys.argv[2])\n"
            "wrapper.configure_attributes(deployment,json.loads(Path(sys.argv[3]).read_text(encoding='utf-8')))\n"
            "sys.exit(deployment.main(sys.argv[4:]))\n", encoding="utf-8", newline="\n")
        command = [sys.executable, "-I", "-B", str(launcher), str(Path(__file__).resolve()),
                   str(source / "pack/scripts/pack-apply.py"), str(attributes), *command[4:]]
    if mode == "plan":
        # Isolate source imports and retain run()'s clean Git environment/time limit.
        command = [sys.executable, "-I", "-B", "-c",
                   "import importlib.util,json,sys; from pathlib import Path; "
                   "spec=importlib.util.spec_from_file_location('bootstrap',sys.argv[1]); "
                   "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n"
                   "try:\n"
                   " print(json.dumps(module.deployment_plan(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])))\n"
                   "except (module.BootstrapError,OSError,ValueError) as exc:\n"
                   " print(str(exc),file=sys.stderr); sys.exit(1)\n",
                   str(Path(__file__).resolve()), str(source), str(target), project or ""]
    try:
        report = json.loads(run(command, cwd=target))
    except BootstrapError as exc:
        try:
            report = json.loads(str(exc))
        except ValueError:
            raise exc
        failures = [row for row in report["rows"] if row["status"] != "ok"]
        detail = "\n".join(f"  {row['action']} {row['path']}: {row['note']}" for row in failures)
        raise BootstrapError(f"Deployment {mode} refused; reconcile these items and retry:\n{detail}") from exc
    failures = [row for row in report["rows"] if row["status"] != "ok" or row["action"] in {"CONFLICT", "REVIEW", "ERROR", "STALE-APPLIER"}]
    if failures:
        detail = "; ".join(f"{row['action']} {row['path']}: {row['note']}" for row in failures)
        raise BootstrapError(f"Deployment {mode} refused: {detail}; reconcile and retry")
    return report


def inventory(root, paths):
    validate_paths(root, paths)
    result = {}
    for relative in sorted(paths):
        path = root / relative
        if path.exists():
            result[relative] = ("file", hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode)
    return result


def promote(stage, target, before, paths):
    if inventory(target, paths) != before:
        raise BootstrapError("Target changed during preflight; nothing installed. Stop concurrent writers and retry")
    after = inventory(stage, paths)
    changed = [relative for relative in sorted(set(before) | set(after))
               if before.get(relative) != after.get(relative)]
    recovery = Path(tempfile.mkdtemp(prefix="ai-forward-recovery-"))
    made_dirs, attempted = [], []
    recovered = True
    try:
        for relative in changed:
            destination = target / relative
            if relative in before:
                backup = recovery / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
        try:
            for relative in changed:
                destination = target / relative
                attempted.append(relative)
                if relative not in after:
                    destination.unlink()
                else:
                    missing = []
                    parent = destination.parent
                    while not parent.exists():
                        missing.append(parent)
                        parent = parent.parent
                    for directory in reversed(missing):
                        directory.mkdir()
                        made_dirs.append(directory)
                    shutil.copy2(stage / relative, destination)
            if inventory(target, paths) != after:
                raise OSError("Installed outcomes differ from the verified staging tree")
        except (BootstrapError, OSError, KeyboardInterrupt) as exc:
            try:
                for relative in reversed(attempted):
                    destination = target / relative
                    if relative in before:
                        validate_paths(target, [relative])
                        shutil.copy2(recovery / relative, destination)
                    elif destination.exists():
                        destination.unlink()
                for directory in reversed(made_dirs):
                    directory.rmdir()
            except (BootstrapError, OSError) as rollback:
                recovered = False
                raise BootstrapError(f"Promotion failed ({exc}); recovery incomplete ({rollback}). "
                                     f"Original files retained at {recovery}; restore them before retrying") from rollback
            raise BootstrapError(f"Promotion failed ({exc}); original target restored; retry after fixing the error") from exc
    finally:
        if recovered:
            shutil.rmtree(recovery)
    return changed


def target_root(candidate):
    try:
        root = run(["git", "rev-parse", "--show-toplevel"], cwd=candidate, timeout=30).strip()
        return Path(root).resolve(), True
    except BootstrapError as exc:
        if "not a git repository" not in str(exc):
            raise
        return candidate, False


def stage_target(target, stage, is_git, paths):
    if is_git:
        run(["git", "clone", "--shared", "--no-checkout", "--", str(target), str(stage)])
        index = Path(run(["git", "rev-parse", "--git-path", "index"], cwd=target).strip())
        if not index.is_absolute():
            index = target / index
        if index.exists():
            shutil.copy2(index, stage / ".git/index")
            for shared in index.parent.glob("sharedindex.*"):
                shutil.copy2(shared, stage / ".git" / shared.name)
    stage.mkdir(parents=True, exist_ok=True)
    validate_paths(target, paths)
    for relative in sorted(paths):
        current = target / relative
        if current.exists():
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, destination)


def validate_paths(target, paths):
    for relative in paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] == ".git":
            raise BootstrapError(f"Unsupported deployment path: {relative}")
        candidate = target
        for number, part in enumerate(path.parts):
            candidate = candidate / part
            try:
                info = candidate.lstat()
            except FileNotFoundError:
                continue
            if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise BootstrapError(f"Unsupported reparse point in managed path: {relative}; resolve it before installing")
            if stat.S_ISLNK(info.st_mode):
                raise BootstrapError(f"Unsupported symlink in managed path: {relative}; resolve it before installing")
            if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
                raise BootstrapError(f"Unsupported hardlink in managed path: {relative}; resolve it before installing")
            expected = stat.S_ISREG if number == len(path.parts) - 1 else stat.S_ISDIR
            if not expected(info.st_mode):
                raise BootstrapError(f"Unsupported non-regular managed path: {relative}; resolve it before installing")


def configure_attributes(deployment, lines):
    """Adapt only Git policy; every deployment path still comes from the source map."""
    def scoped_attributes(app):
        path = Path(app.target) / ".gitattributes"
        current = deployment.read(str(path)) or ""
        have = {" ".join(line.split()) for line in deployment.norm_nl(current).splitlines()}
        missing = [line for line in lines if " ".join(line.split()) not in have]
        if not missing:
            app.row("bundle", ".gitattributes", "UNCHANGED", "ok")
            return
        text = deployment.norm_nl(current)
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n# AI-Forward bootstrap: LF for source-mapped pack files only.\n" + "\n".join(missing) + "\n"
        app._write(str(path), text)
        app.row("bundle", ".gitattributes", "UPDATE", "ok", "pack-scoped LF policy")

    setattr(deployment.Applier, "_gitattributes", scoped_attributes)


def deployment_plan(source, target, project):
    """Observe the source's dry map, including writes omitted from action rows.

    Retired backups, revision metadata and stale removals come from the applier,
    not a second copy map. The source's parity-control discovery remains intact.
    """
    spec = importlib.util.spec_from_file_location("bootstrap_pack_apply", source / "pack/scripts/pack-apply.py")
    assert spec and spec.loader
    deployment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deployment)
    paths = {RECEIPT}
    original_read = deployment.read
    original_hook_read = deployment.read_hook_settings

    def check_read_path(path):
        candidate = Path(path).absolute()
        if candidate.is_relative_to(target):
            validate_paths(target, [candidate.relative_to(target).as_posix()])

    def checked_read(path):
        check_read_path(path)
        return original_read(path)

    hook_path = None

    def checked_hook_read(path):
        nonlocal hook_path
        check_read_path(path)
        hook_path = Path(path).relative_to(target).as_posix()
        return original_hook_read(path)

    original_named_merge = deployment.merge_named_hook_bundles

    def checked_named_merge(source_text, current_text=None):
        merged = original_named_merge(source_text, current_text)
        current = json.loads(current_text) if current_text is not None else {}
        proposed = json.loads(merged)
        changed = [name for name, bundle in current.items() if proposed.get(name) != bundle]
        if changed:
            # A source-owned name alone is not proof that its current settings
            # belong to the pack. Never enable or discard a project's deviations.
            raise BootstrapError(f"CONFLICT {hook_path}: named hook bundle(s) {', '.join(changed)} "
                                 "would change existing commands, disablement or metadata; "
                                 "reconcile these settings explicitly before installing")
        return merged

    setattr(deployment, "merge_named_hook_bundles", checked_named_merge)
    setattr(deployment, "read", checked_read)
    setattr(deployment, "read_hook_settings", checked_hook_read)
    original_walk = deployment.os.walk

    def project_walk(root, *args, **kwargs):
        if Path(root).absolute() != target:
            yield from original_walk(root, *args, **kwargs)
            return
        # Parity migration is the one map operation that discovers repo-local
        # controls. Respect ignored, untracked dependency trees while retaining
        # tracked controls (even under an ignored directory). Git does the ignore
        # parsing; a plain project uses disposable metadata, never git-init there.
        command = ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"]
        try:
            ignored = run(command, cwd=target).split("\0")
        except BootstrapError as exc:
            if "not a git repository" not in str(exc):
                raise
            with tempfile.TemporaryDirectory(prefix="ai-forward-ignore-") as metadata:
                run(["git", "init", "--bare", metadata])
                ignored = run(["git", "--git-dir=" + metadata, "--work-tree=" + str(target)] +
                              command[1:], cwd=target).split("\0")
        ignored = {path.rstrip("/") for path in ignored if path}
        for base, dirs, files in original_walk(root, *args, **kwargs):
            relative = Path(base).relative_to(target)
            dirs[:] = [name for name in dirs if (relative / name).as_posix() not in ignored]
            files = [name for name in files if (relative / name).as_posix() not in ignored
                     and (stat.S_ISREG((Path(base) / name).lstat().st_mode)
                          or (Path(base) / name).is_symlink())]
            yield base, dirs, files

    # Do not mutate the process-global os module used by the launcher.
    setattr(deployment, "os", types.SimpleNamespace(**dict(vars(os), walk=project_walk)))
    app = deployment.Applier(str(source), str(target), dry=True, project=project, install=True)
    observed_writes = {}
    # Discover the complete source map before deriving exact, root-anchored
    # attribute patterns. Local baseline inputs and arbitrary product trees are not outputs.
    app._gitattributes = lambda: None

    def observe(path, text=None):
        relative = Path(path).relative_to(target).as_posix()
        validate_paths(target, [relative])
        paths.add(relative)
        if text is not None:
            observed_writes[relative] = deployment.norm_nl(text).encode("utf-8")
        if relative == ".gitattributes" and Path(path).exists():
            # Git attributes are last-match-wins: keeping the old lines does not
            # keep their meaning when a source appends a repository-wide rule.
            raise BootstrapError("REVIEW .gitattributes: source requests changes to existing product Git "
                                 "policy; reconcile a pack-scoped policy explicitly before installing "
                                 "(nothing installed)")

    def observe_remove(path):
        observe(path)
        # Removal has no source text or historical comparison in this API.
        # A stale filename is not an ownership receipt for the active contents.
        relative = Path(path).relative_to(target).as_posix()
        raise BootstrapError(f"REVIEW {relative}: source requests removal without established "
                             "ownership of the current contents; reconcile/relocate local "
                             "instructions explicitly before installing (nothing installed)")

    app._write = observe
    app._remove = observe_remove
    rows = app.run()
    attribute_paths = {RECEIPT, ".gitattributes", "docs/ai-forward-pack/INSTALL.md"}
    attribute_paths.update(row["path"] for row in rows
                           if row["area"] != "meta" and row["action"] != "SKIP")
    validate_paths(target, attribute_paths)
    attributes = [json.dumps("/" + re.sub(r"([\\*?\[])", r"\\\1", relative), ensure_ascii=False) +
                  " text=auto eol=lf" for relative in sorted(attribute_paths)]
    current_attributes = deployment.read(str(target / ".gitattributes")) or ""
    have = {" ".join(line.split()) for line in deployment.norm_nl(current_attributes).splitlines()}
    if all(" ".join(line.split()) in have for line in deployment.GITATTRIBUTES_LINES):
        # An operator's already-satisfying policy needs no change. Never replace
        # an existing broad policy merely to convert it into bootstrap's scoped form.
        attributes = list(deployment.GITATTRIBUTES_LINES)
    configure_attributes(deployment, attributes)
    deployment.Applier._gitattributes(app)
    reported_paths = {row["path"] for row in rows}
    for relative, proposed in observed_writes.items():
        path = target / relative
        if relative not in reported_paths and path.exists() and path.read_bytes() != proposed:
            # Backup writes have no action row or historical ownership check.
            # A source-selected archive name cannot authorize replacing local data.
            raise BootstrapError(f"CONFLICT {relative}: unreported archive/write would replace "
                                 "existing contents without established ownership; reconcile or "
                                 "relocate the existing file before installing (nothing installed)")
    for row in rows:
        if row["area"] == "controls" and row["action"] == "REWRITE":
            # Marker discovery and a retired backup cannot prove preservation of
            # arbitrary active product logic. Require review, not an inferred port.
            row.update(action="REVIEW", status="fail",
                       note="source requests replacement of an active product control without "
                            "established source ownership; reconcile its complete safety checks "
                            "with the import invariant explicitly before installing")
    paths.update(row["path"] for row in rows if row["area"] != "meta")
    # An unchanged INSTALL still supplies the historical merge revision.
    paths.add("docs/ai-forward-pack/INSTALL.md")
    # Baselines also measure repo-local knowledge and skills, not arbitrary trees
    # or skill reference assets. Never run their generators on the real target.
    for pattern in (".claude/knowledge/*.md", ".claude/skills/*/SKILL.md"):
        paths.update(path.relative_to(target).as_posix() for path in target.glob(pattern))
    validate_paths(target, paths)
    return {"mode": "plan", "source_revision": app.source_rev, "target_revision": app.target_rev,
            "rows": rows, "paths": sorted(paths), "attributes": attributes}


def validate_managed_blocks(source, target):
    # Reuse the source applier's installed-revision history lookup and equality rules.
    spec = importlib.util.spec_from_file_location("bootstrap_pack_apply", source / "pack/scripts/pack-apply.py")
    assert spec and spec.loader
    deployment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deployment)
    app = deployment.Applier(str(source), str(target), dry=True, install=True)
    pattern = re.compile(r"<!-- AI-FORWARD-PACK:BEGIN.*?<!-- AI-FORWARD-PACK:END -->", re.S)
    for name in ("AGENTS", "CLAUDE"):
        path = target / (name + ".md")
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        regions = pattern.findall(text)
        if not regions and "AI-FORWARD-PACK:" not in text:
            continue
        if len(regions) != 1 or text.count("AI-FORWARD-PACK:BEGIN") != 1 or text.count("AI-FORWARD-PACK:END") != 1:
            raise BootstrapError(f"Malformed managed block in {name}.md; reconcile it before installing")
        valid = []
        # An older copy-style CLAUDE.md may carry the AGENTS block before conversion.
        for block in ({name, "AGENTS"} if name == "CLAUDE" else {name}):
            relative = f"adapters/managed-blocks/{block}.block.md"
            valid.append((source / "pack" / relative).read_text(encoding="utf-8"))
            previous = app._old_pack_text(relative)
            if previous:
                valid.append(previous)
        if not any(deployment.same(regions[0], expected) for expected in valid):
            raise BootstrapError(f"Local managed block deviation in {name}.md; reconcile it before installing (no force applied)")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="offline Git source clone; uses committed HEAD")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="source Git repository URL")
    parser.add_argument("--ref", help="source branch, tag, or commit (default: main; local source: HEAD)")
    parser.add_argument("--target", type=Path, help="existing project directory (default: cwd or enclosing Git root)")
    parser.add_argument("--dry-run", action="store_true", help="show deployment plan; no target writes")
    args = parser.parse_args(argv)
    target = (args.target or Path.cwd()).resolve()
    try:
        # Refuse credential-bearing transport before Git can echo it in an error
        # or before repository provenance can be persisted. Use Git's credential
        # helper or a credential-free URL; query/fragment secrets are unsafe too.
        if not args.source and "://" in args.repo:
            from urllib.parse import urlsplit
            try:
                repository = urlsplit(args.repo)
            except ValueError:
                raise BootstrapError("Invalid repository URL; use a credential-free URL") from None
            if "@" in repository.netloc or repository.query or repository.fragment:
                raise BootstrapError("Repository URL may contain credentials; use a credential-free URL "
                                     "and Git credential helper (nothing installed)")
        requested_target = target
        target, is_git = target_root(target)
        if args.target and requested_target != target:
            raise BootstrapError("Explicit --target must be the Git root; no files changed")
        with tempfile.TemporaryDirectory(prefix="ai-forward-bootstrap-") as folder:
            source = Path(folder) / "source"
            origin = str(args.source.resolve()) if args.source else args.repo
            run(["git", "clone", "--no-checkout", "--no-hardlinks", "--", origin, str(source)])
            ref = args.ref or ("HEAD" if args.source else "main")
            try:
                commit = run(["git", "rev-parse", "--verify", "--end-of-options", ref + "^{commit}"], cwd=source).strip()
            except BootstrapError:
                remote_ref = "refs/remotes/origin/" + (ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref)
                try:
                    commit = run(["git", "rev-parse", "--verify", "--end-of-options", remote_ref + "^{commit}"], cwd=source).strip()
                except BootstrapError:
                    # Pull/merge commits need not be in a normal branch clone.
                    # Fetch the exact caller ref, never silently substitute main.
                    run(["git", "check-ref-format", "--allow-onelevel", ref], cwd=source)
                    run(["git", "fetch", "--no-tags", "--", "origin", ref], cwd=source)
                    commit = run(["git", "rev-parse", "--verify", "FETCH_HEAD^{commit}"], cwd=source).strip()
            run(["git", "-c", "core.autocrlf=false", "-c",
                 "core.hooksPath=" + str(source / ".git/bootstrap-disabled-hooks"),
                 "checkout", "--detach", commit], cwd=source)
            project = run([sys.executable, "-I", "-B", "-c",
                           "import sys; sys.stdout.reconfigure(encoding='utf-8',errors='replace'); "
                           "sys.path.insert(0, sys.argv[1]); "
                           "from repo_identity import canonical_project; print(canonical_project(sys.argv[2]))",
                           str(source / "pack/scripts"), str(target)], cwd=target).strip()
            planned = pack(source, target, "plan", project)
            paths = set(planned["paths"])
            before = inventory(target, paths)
            validate_managed_blocks(source, target)
            if args.dry_run:
                counts = Counter(row["action"] for row in planned["rows"])
                print(f"AI-Forward dry-run: revision {planned['source_revision']}, source commit {commit}; no target writes.")
                print(", ".join(f"{value} {key}" for key, value in sorted(counts.items())))
                return 0
            stage = Path(folder) / "stage" / target.name
            stage_target(target, stage, is_git, paths)
            needs_changes = any(row["action"] not in {"UNCHANGED", "KEEP", "SKIP"} for row in planned["rows"])
            attribute_policy = Path(folder) / "bootstrap-attributes.json"
            attribute_policy.write_text(json.dumps(planned["attributes"], ensure_ascii=False),
                                        encoding="utf-8", newline="\n")
            applied = pack(source, stage, "apply", project, no_baselines=not needs_changes,
                           attributes=attribute_policy)
            verified = pack(source, stage, "plan", project)
            pending = [row for row in verified["rows"]
                       if row["action"] not in {"UNCHANGED", "KEEP", "SKIP"}]
            if pending:
                detail = "; ".join(f"{row['path']}: {row['action']}" for row in pending)
                raise BootstrapError(f"Deployment verification failed: {detail}")
            receipt = {"schema_version": 1, "source_repository": "local" if args.source else args.repo,
                       "requested_ref": ref, "source_commit": commit,
                       "pack_revision": applied["source_revision"]}
            path = stage / RECEIPT
            path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
            changed = promote(stage, target, before, paths)
            counts = Counter(row["action"] for row in applied["rows"])
            state = "already current" if not changed else ("installed" if planned["target_revision"] is None else "updated")
            print(f"AI-Forward {state}: revision {receipt['pack_revision']}, source commit {commit}.")
            print(", ".join(f"{value} {key}" for key, value in sorted(counts.items())))
            print("Next: Claude Code: /deliver <your goal>; Codex: $deliver <your goal>.")
            print("Copilot CLI: find deliver with /skills, then /deliver <your goal>, or ask "
                  "'Use the /deliver skill to <your goal>'. In an existing chat, use "
                  "/skills reload, then /skills info deliver.")
            print("VS Code Copilot: /deliver when listed, or select/request deliver. "
                  "Grok Build/Antigravity: select/request the deliver skill.")
            print("If your app has not discovered the installed skill, refresh/restart it before starting.")
            return 0
    except (BootstrapError, OSError, ValueError) as exc:
        print(f"AI-Forward bootstrap failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
