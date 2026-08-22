#!/usr/bin/env python3
"""coord-core.py - agent coordination, Phase 1 walking skeleton.

Holds the record of intent and answers "may this session touch this artifact?" from it.
Append-only JSONL, one file per session; every piece of state is a fold over it. No daemon,
no database, no dependency beyond the standard library (ADR-0007).

Four controls here were observed failing on the un-fixed shape before they were trusted:
  LOG-A     an append onto a file not ending in a newline fuses two records and loses BOTH
  R4        a check that scanned nothing must not report "free"
  CTRL-PORT os.open without O_BINARY translates newlines on Windows -- which also MASKED
            the LOG-A control, because a stray CR still terminates a line
  F8        a claim over the coordination record itself would lock the substrate

Design: docs/design/coord-core-phase1.md
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TTL_DEFAULT = 300
COORD_DIRNAME = ".agents"


class CoordError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# --- paths & identity -------------------------------------------------------

def repo_root(cwd):
    """The PRIMARY checkout of this repository, from any worktree.

    The record is per REPOSITORY, not per checkout. `--git-common-dir` is the primitive
    that says so: from a linked worktree it returns the primary .git (absolute), and from
    the primary checkout it returns a relative ".git". Its parent is the primary checkout
    in both cases.

    Found by running the Phase-1 demo: with the root defaulting to cwd/.agents, every
    worktree got its own private record and two sessions could never see each other -
    which is the exact criterion this phase exists to satisfy.

    Read from the filesystem, NOT by shelling out to `git rev-parse --git-common-dir`.
    The first implementation did shell out and cost ~35 ms of the check's budget - measured
    at 82 ms p95, which met NFR-P1 but blew straight through ADR-0007's own 60 ms
    compaction trigger. On the hot path of every edit, a subprocess is not free.

    The layout this reads is git's own:
      primary checkout -> .git is a DIRECTORY; the repo root is its parent
      linked worktree  -> .git is a FILE holding "gitdir: <primary>/.git/worktrees/<name>"
    """
    here = Path(cwd).resolve()
    for candidate in [here, *here.parents]:
        dot_git = candidate / ".git"
        if dot_git.is_dir():
            return candidate
        if dot_git.is_file():
            try:
                text = dot_git.read_text(encoding="utf-8").strip()
            except OSError:
                break
            if text.startswith("gitdir:"):
                gitdir = Path(text.split(":", 1)[1].strip())
                if not gitdir.is_absolute():
                    gitdir = candidate / gitdir
                parts = gitdir.resolve().parts
                if "worktrees" in parts:
                    common = Path(*parts[: parts.index("worktrees")])
                    return common.parent
            break
    return here     # not a git repo: degrade to the directory, and say nothing false


def resolve_root(cwd, raw):
    """Resolve COORD_ROOT, refusing anything outside the repository.

    COORD_ROOT is attacker-controllable input that selects which file becomes trusted
    state (STRIDE B1, elevation of privilege). Found at the design gate, not in the draft.
    """
    base = repo_root(cwd)
    root = Path(raw).resolve() if raw else (base / COORD_DIRNAME).resolve()
    try:
        root.relative_to(base)
    except ValueError:
        return None, {"code": "COORD-NOT-CHECKED-ROOT",
                      "reason": "COORD_ROOT resolves outside the repository: {}".format(root)}
    return root, None


def _norm(p):
    return str(p).replace("\\", "/").replace("**", "*")


def _literal_segments(pattern):
    """The leading path segments of a pattern that contain no wildcard."""
    segs = []
    for seg in _norm(pattern).split("/"):
        if any(ch in seg for ch in "*?["):
            break
        segs.append(seg)
    return segs


def overlaps(a, b):
    """Do two path patterns intersect? Prefer a false positive: a false refusal costs a
    message, a false grant costs a merge.

    Compared by SEGMENT, not by string prefix, so src/Foo/** and src/FooBar/** are
    correctly disjoint.

    simplify: fnmatch both ways plus a segment-prefix test.
      ceiling: a wildcard in the middle of a pattern, and character classes.
      upgrade trigger: the first refusal a human calls wrong, or Phase 3's artifact-class
      registry introducing nested patterns.
    """
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return True
    if fnmatch.fnmatch(nb, na) or fnmatch.fnmatch(na, nb):
        return True
    sa, sb = _literal_segments(na), _literal_segments(nb)
    n = min(len(sa), len(sb))
    return sa[:n] == sb[:n]


# --- the record -------------------------------------------------------------

def make_event(kind, session, agent, wi, path, at, ttl=TTL_DEFAULT, seq=None):
    first = next((seg for seg in _norm(path).split("/") if seg not in (".", "")), "")
    if first == COORD_DIRNAME:
        raise CoordError("COORD-CLAIM-SELF",
                         "a claim over the coordination record itself is refused")
    event = {"kind": kind, "session": session, "agent": agent, "wi": wi,
             "path": _norm(path), "at": float(at)}
    if kind == "claim":
        event["ttl"] = float(ttl)
    if seq is not None:
        event["seq"] = int(seq)
    return event


def _next_seq(logfile):
    if not logfile.exists():
        return 1
    n = 0
    with open(logfile, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n + 1


def append_event(root, event):
    """Append one event as exactly one write() - atomic under O_APPEND (spike S3)."""
    logdir = Path(root) / "log"
    logdir.mkdir(parents=True, exist_ok=True)
    logfile = logdir / "{}.jsonl".format(event["session"])
    if "seq" not in event:
        event["seq"] = _next_seq(logfile)
    payload = json.dumps(event, sort_keys=True) + "\n"

    # LOG-A: emit a LEADING newline when the file does not already end in one, so a fused
    # record is impossible to express rather than merely detectable (control ladder rung 1).
    # The file may have been left unterminated by a merge resolution or a hand edit -- the
    # writer owns this seam because no single actor otherwise does.
    if logfile.exists() and logfile.stat().st_size:
        with open(logfile, "rb") as fh:
            fh.seek(-1, os.SEEK_END)
            last = fh.read(1)
        if last not in (b"\n", b"\r"):
            payload = "\n" + payload

    # CTRL-PORT: O_BINARY (Windows only; 0 elsewhere) stops newline translation, so the
    # committed bytes are LF on every platform as .gitattributes requires. It also stops a
    # stray CR from masking the LOG-A control above -- which is how that masking was found.
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0)
    fd = os.open(str(logfile), flags, 0o644)
    try:
        os.write(fd, payload.encode("utf-8"))   # exactly one write() -- atomic (spike S3)
    finally:
        os.close(fd)
    return event


def read_events(root):
    """Return (events, errors, files_scanned).

    Errors are collected, never raised - but a single error makes the whole check
    not_checked. Fail safe, never open (NFR-R2).
    """
    logdir = Path(root) / "log"
    events, errors, files = [], [], 0
    if not logdir.is_dir():
        return events, errors, files
    for logfile in sorted(logdir.glob("*.jsonl")):
        files += 1
        with open(logfile, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    errors.append("{}:{}: {}".format(logfile.name, lineno, exc.msg))
    events.sort(key=lambda e: (e.get("at", 0.0), e.get("session", ""), e.get("seq", 0)))
    return events, errors, files


def fold(events, now):
    """Pure fold: events -> live leases. Replaying is idempotent (NFR-R1).

    derive-don't-store (DM7): `expires` is computed here (at + ttl) and never persisted.
    Two stored definitions of one quantity is the defect signature.
    """
    leases, seen = {}, set()
    for event in events:
        ident = (event.get("session"), event.get("seq"))
        if ident in seen:            # F9: a retried tool call must not take a second lease
            continue
        seen.add(ident)
        key = (event.get("path"), event.get("session"))
        if event.get("kind") == "claim":
            leases[key] = {"path": event["path"], "session": event["session"],
                           "agent": event.get("agent", event["session"]),
                           "wi": event.get("wi", ""),
                           "expires": event["at"] + event.get("ttl", TTL_DEFAULT)}
        elif event.get("kind") == "release":
            leases.pop(key, None)
    return {k: v for k, v in leases.items() if v["expires"] > now}


# --- the decision -----------------------------------------------------------

def check(root, path, me, now):
    if not me:
        return {"decision": "not_checked", "path": path, "files_scanned": 0,
                "events_scanned": 0, "code": "COORD-NOT-CHECKED-IDENTITY",
                "reason": "AGENT_SESSION is unset, so this session has no identity to check"}

    events, errors, files = read_events(root)

    if errors:
        return {"decision": "not_checked", "path": path, "files_scanned": files,
                "events_scanned": len(events), "code": "COORD-NOT-CHECKED-RECORD",
                "reason": "the record could not be read: " + "; ".join(errors[:3])}

    # R4: a control that scanned nothing has not reported clean. An empty corpus and a
    # clean corpus must never render the same. Written because this architecture's own
    # allocator spike printed "COLLISION-FREE" over zero identifiers.
    if files == 0:
        return {"decision": "not_checked", "path": path, "files_scanned": 0,
                "events_scanned": 0, "code": "COORD-NOT-CHECKED-RECORD",
                "reason": "0 files scanned - there is no record here, so nothing was checked"}

    for lease in fold(events, now).values():
        if lease["session"] != me and overlaps(lease["path"], path):
            return {"decision": "deny", "path": path, "files_scanned": files,
                    "events_scanned": len(events), "code": "COORD-REFUSED",
                    "holder": lease["agent"], "session": lease["session"],
                    "wi": lease["wi"], "expires_in": int(lease["expires"] - now),
                    "reason": "an unexpired lease overlaps your pattern"}

    return {"decision": "allow", "path": path, "files_scanned": files,
            "events_scanned": len(events), "code": None, "reason": ""}


def _safe(value, limit=200):
    """Strip control characters and cap length before interpolating into the refusal.

    STRIDE B4, elevation: the refusal is rendered into ANOTHER MODEL'S context. The
    template is fixed and nothing is interpolated into prose, but an interpolated VALUE
    carrying a newline could still add a line that reads as an instruction. This is the
    Phase-4 trust boundary arriving three phases early, so it is closed here.
    """
    text = "".join(ch for ch in str(value) if ch.isprintable())
    return text[:limit]


def render(decision):
    """Four labelled lines, fixed order: what happened - who - why - what to do.

    No colour is load-bearing: every state is distinguishable from the text and the exit
    code alone. Accessibility and machine-readability are the same requirement here.
    "refused" is never softened to "denied" or "unavailable" - the reader is a model that
    must not read the outcome as a transient failure worth retrying.
    """
    decision = {k: (_safe(v) if isinstance(v, str) else v) for k, v in decision.items()}
    verdict = decision["decision"]
    if verdict == "allow":
        return ""
    if verdict == "deny":
        return ("REFUSED  {path}\n"
                "  held by   {holder} - {wi} - expires in {expires_in}s\n"
                "  because   {reason}\n"
                "  remedy    wait, claim a disjoint subset, or record a block on {wi}"
                ).format(**decision)
    return ("NOT CHECKED  {path}\n"
            "  held by   unknown - this check did not run\n"
            "  because   {reason}\n"
            "  remedy    fix the condition above, then re-run; this is not a pass"
            ).format(**decision)


EXIT = {"allow": 0, "deny": 3, "not_checked": 4}


# --- the decisions store (Phase 2) ------------------------------------------
#
# TWO STORES, TWO GRAINS, ONE READER EACH.
#   log/       one row is one INTENT event  (claim/release/session)  -> FOLDED
#   decisions/ one row is one ENFORCEMENT decision (allow/deny/ask)  -> NEVER folded
#
# Phase 1 appended refusals into the folded log. That is now wrong, and the reason is
# Phase 1's own measurement: the check was 63 ms p95 at 10,000 events, already at
# ADR-0007's 60 ms compaction trigger. Phase 2 records a decision PER EDIT - orders of
# magnitude more traffic than one per claim - so folding those would blow the hot path
# within a day. Keeping them out means the fold stays proportional to CLAIMS, not EDITS,
# and the metric that decides whether this phase worked costs nothing to collect.

def append_decision(root, session, agent, path, decision):
    """Record one enforcement decision. Never folded; read by `tail` and `metrics`.

    G14: the verdict is computed BEFORE this is attempted and cannot be changed by it.
    A refusal that cannot be recorded is still a refusal.
    """
    logdir = Path(root) / "decisions"
    # The stored kind is the UBIQUITOUS LANGUAGE word, not the internal one: "refused",
    # never "denied". The store is read by humans in `tail`, and the vocabulary is the
    # same one the refusal itself uses.
    kind = {"allow": "allowed", "deny": "refused",
            "not_checked": "not_checked"}.get(decision.get("decision"), "unknown")
    record = {"kind": kind,
              "session": session or "anon", "agent": agent or "anon",
              "wi": decision.get("wi", ""), "path": _norm(path),
              "at": time.time(), "code": decision.get("code")}
    try:
        logdir.mkdir(parents=True, exist_ok=True)
        logfile = logdir / "{}.jsonl".format(record["session"])
        payload = json.dumps(record, sort_keys=True) + "\n"
        if logfile.exists() and logfile.stat().st_size:
            with open(logfile, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                if fh.read(1) not in (b"\n", b"\r"):    # LOG-A, same seam
                    payload = "\n" + payload
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0)
        fd = os.open(str(logfile), flags, 0o644)
        try:
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
    except Exception:
        pass    # never let a bookkeeping failure change a verdict


def read_decisions(root):
    logdir = Path(root) / "decisions"
    out = []
    if not logdir.is_dir():
        return out
    for logfile in sorted(logdir.glob("*.jsonl")):
        with open(logfile, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue    # a damaged decision is lost telemetry, not lost state
    out.sort(key=lambda d: d.get("at", 0.0))
    return out


# --- git plumbing -----------------------------------------------------------

def _git(repo, *args):
    """Run git and READ THE RESULT BACK. An exit code is not a result (CTRL-E)."""
    try:
        proc = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                              text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "{}: {}".format(exc.__class__.__name__, exc)
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "git {} failed".format(args[0])).strip()
    return proc.stdout, None


def unique_commits(repo):
    """Commits reachable from HEAD and from NO other ref. Returns (count, reason_code).

    `--all` is FORBIDDEN in this expression. Spike S9 reproduced the recorded bug:
    `git rev-list HEAD --not --all` returns 0 for a branch holding exactly one commit
    that exists nowhere else, because --all implicitly includes HEAD -- so the expression
    reduces to `HEAD --not HEAD` and reports SAFE for the one case the guard exists to
    catch. `--exclude=<branch> --all` fails identically, because it does not exclude HEAD.
    """
    out, err = _git(repo, "rev-parse", "--is-inside-work-tree")
    if err:
        return None, "COORD-NOT-CHECKED-GIT"

    out, err = _git(repo, "symbolic-ref", "-q", "--short", "HEAD")
    if err or not (out or "").strip():
        # Detached: every PR gate runs here, and "does my work exist anywhere else?" has
        # no meaning. Decline. A control that cannot see is not licensed to accuse.
        return None, "COORD-DETACHED"
    current = out.strip()

    out, err = _git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    if err:
        return None, "COORD-NOT-CHECKED-GIT"
    peers = [r for r in out.split() if r != "refs/heads/" + current]
    if not peers:
        # Nothing to compare against: a fresh repo genuinely has one copy of everything.
        # Reported distinctly so it does not train people to switch the guard off.
        return None, "COORD-NO-PEER-REFS"

    out, err = _git(repo, "rev-list", "HEAD", "--not", *peers)
    if err:
        return None, "COORD-NOT-CHECKED-GIT"
    return len([line for line in out.split() if line]), None


def staged_paths(repo):
    """Staged paths, NUL-separated. Returns (paths, error).

    S8: `--cached` works before the first commit; appending HEAD is FATAL there, so HEAD
    is never passed. The -z form is required - a path containing a space is otherwise
    split, and one containing a quote is otherwise escaped.
    """
    out, err = _git(repo, "diff", "--cached", "--name-only", "-z")
    if err:
        return None, err
    return [p for p in out.split("\0") if p], None


# --- CLI --------------------------------------------------------------------

def _identity():
    session = os.environ.get("AGENT_SESSION")
    return session, os.environ.get("AGENT_NAME") or session


def _build_parser():
    parser = argparse.ArgumentParser(prog="coord", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    claim = sub.add_parser("claim", help="declare intent over an artifact set")
    claim.add_argument("--wi", required=True)
    claim.add_argument("--path", required=True)
    claim.add_argument("--ttl", type=float, default=TTL_DEFAULT)

    chk = sub.add_parser("check", help="may this session touch this path?")
    chk.add_argument("path")
    chk.add_argument("--json", action="store_true")

    rel = sub.add_parser("release", help="drop a lease")
    rel.add_argument("--path", required=True)
    rel.add_argument("--wi", default="WI-0")

    tail = sub.add_parser("tail", help="the merged chronological stream")
    tail.add_argument("-n", type=int, default=20)

    # --- Phase 2: enforcement ---
    sub.add_parser("hook", help="PreToolUse adapter: stdin JSON in, decision JSON out")
    sub.add_parser("precommit", help="the universal floor: refuse unclaimed staged paths")
    guard = sub.add_parser("guard", help="refuse to move HEAD over work held in one place")
    guard.add_argument("--fix", action="store_true", help="push, the cheapest second copy")
    ses = sub.add_parser("session", help="one session per working tree")
    ses.add_argument("action", choices=["start", "end"])
    met = sub.add_parser("metrics", help="the four measures this layer exists to move")
    met.add_argument("--json", action="store_true")
    sub.add_parser("install", help="write the pre-commit hook; print the settings entry")
    return parser


MAX_PATH = 4096
HOOK_MARKER = "# coord-core pre-commit floor"
HOOK_BODY = """#!/bin/sh
{marker}
# The universal floor: every harness has a commit boundary, and no settings key removes it.
exec "{python}" "{script}" precommit
"""


def _reject_path(path):
    """Reasons a path may not be checked at all. Returns a reason, or None if it is fine.

    STRIDE B4/B5, tampering: the path is never opened, never globbed against the
    filesystem, and never passed to a shell - but a path that escapes the repository has
    no meaning in a repo-scoped lease, and answering "free" for it would be a false grant.
    """
    if len(path) > MAX_PATH:
        return "the path exceeds the length bound"
    normalised = _norm(path)
    if "\0" in path or not path.strip():
        return "the path contains a NUL or is empty"
    segments = [s for s in normalised.split("/") if s not in ("", ".")]
    depth = 0
    for segment in segments:
        depth += -1 if segment == ".." else 1
        if depth < 0:
            return "the path escapes the repository"
    return None


def hook_response(decision, reason):
    """The PreToolUse envelope. ALWAYS printed, and the caller ALWAYS exits 0 - the
    harness reads the decision in the JSON, not the exit code. Conflating them would make
    a crashed hook indistinguishable from a refusal.
    """
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason}})


def cmd_hook(root, session, agent, now, stdin_text):
    """G1: this must never raise. A hook that crashes on a bad payload blocks every edit."""
    try:
        event = json.loads(stdin_text or "")
        if not isinstance(event, dict):
            raise ValueError("payload is not an object")
        tool_input = event.get("tool_input")
        path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    except Exception as exc:
        return hook_response("ask", "NOT CHECKED  -\n  held by   unknown - this check did"
                             " not run\n  because   unreadable hook payload ({})\n"
                             "  remedy    fix the condition above; this is not a pass"
                             .format(exc.__class__.__name__))
    if not path:
        # G2: Bash, Read, and anything else without a file_path. The `if` pre-filter
        # should stop most of these from ever spawning a process.
        return hook_response("allow", "coordination: no file_path in this call")
    bad = _reject_path(str(path))                       # B4 tampering
    if bad:
        return hook_response("ask", "NOT CHECKED  -\n  held by   unknown - this check did"
                             " not run\n  because   {}\n"
                             "  remedy    fix the condition above; this is not a pass"
                             .format(bad))

    # B4 spoofing: identity is the ENVIRONMENT's, never the payload's session_id.
    decision = check(root, str(path), session, now)
    if decision["decision"] != "allow":
        append_decision(root, session, agent, path, decision)
    else:
        append_decision(root, session, agent, path, decision)
    mapped = {"allow": "allow", "deny": "deny", "not_checked": "ask"}[decision["decision"]]
    reason = render(decision) or "coordination: lease held or artifact free"
    return hook_response(mapped, reason)


def cmd_precommit(root, repo, session, agent, now):
    paths, err = staged_paths(repo)
    if err is not None:
        print("COORD-NOT-CHECKED-GIT: {}".format(_safe(err, 300)))
        return 4
    if not paths:
        print("0 staged paths - nothing to check")
        return 0

    # US-8: a repository that has not adopted the layer runs in ADVISORY mode and SAYS SO,
    # rather than implying enforcement it cannot deliver. Blocking every commit in every
    # unconfigured repo is how a floor gets deleted instead of adopted.
    _, _, files = read_events(root)
    if files == 0:
        print("advisory: no coordination record in this repository, so nothing was checked."
              "\n  {} staged path(s) allowed. Run `coord claim` to make this enforcing."
              .format(len(paths)))
        return 0

    refused = []
    for path in paths:
        decision = check(root, path, session, now)
        append_decision(root, session, agent, path, decision)
        if decision["decision"] == "deny":
            refused.append(decision)
        elif decision["decision"] == "not_checked":
            print(render(decision))
            return 4
    if refused:
        for decision in refused:
            print(render(decision))
        print("\n{} of {} staged path(s) are held by another session".format(
            len(refused), len(paths)))
        return 3
    print("{} staged path(s) checked - all free or mine".format(len(paths)))
    return 0


def cmd_guard(repo, fix):
    count, reason = unique_commits(repo)
    if reason == "COORD-DETACHED":
        print("COORD-DETACHED  HEAD is detached, so 'does this exist anywhere else' has no"
              " meaning here. NOT CHECKED - this is not a pass.")
        return 4
    if reason == "COORD-NOT-CHECKED-GIT":
        print("COORD-NOT-CHECKED-GIT  git could not answer; nothing was checked.")
        return 4
    if reason == "COORD-NO-PEER-REFS":
        print("COORD-NO-PEER-REFS  there are no other refs in this repository, so nothing"
              " here exists in a second place.\n  remedy    push, or accept that this is a"
              " fresh repository")
        return 3
    if count:
        out, _ = _git(repo, "rev-list", "--oneline", "-n", "20", "HEAD", "--not",
                      *[r for r in (_git(repo, "for-each-ref", "--format=%(refname)",
                                         "refs/heads", "refs/remotes")[0] or "").split()
                        if r != "refs/heads/" + (_git(repo, "symbolic-ref", "-q",
                                                      "--short", "HEAD")[0] or "").strip()])
        print("COORD-UNIQUE-WORK  {} commit(s) exist here and nowhere else:".format(count))
        for line in (out or "").splitlines():
            print("  {}".format(_safe(line, 120)))
        print("  remedy    push - it is the cheapest way to make the work exist twice")
        if fix:
            _, err = _git(repo, "push")
            if err:
                print("  push failed: {}".format(_safe(err, 200)))
                return 3
            recount, _ = unique_commits(repo)
            if recount:
                print("  push reported success but {} commit(s) are still unique"
                      .format(recount))
                return 3
            print("  pushed - now safe")
            return 0
        return 3
    print("safe to move HEAD - nothing here exists in only one place")
    return 0


def _worktree_key(cwd):
    return str(Path(cwd).resolve()).replace("\\", "/")


def cmd_session(root, action, session, agent, cwd, now):
    # simplify: occupancy is the newest session-start with no matching session-end,
    #   inside a staleness window.
    #   ceiling: a session killed without `session end` holds the tree until it elapses.
    #   upgrade trigger: the first time a human is blocked by a dead session.
    STALE_SECONDS = 8 * 3600
    key = _worktree_key(cwd)
    events, errors, _ = read_events(root)
    if errors:
        print("COORD-NOT-CHECKED-RECORD: {}".format(_safe("; ".join(errors[:2]), 200)))
        return 4
    live = {}
    for event in events:
        if event.get("worktree") != key:
            continue
        if event.get("kind") == "session-start":
            live[event.get("session")] = event.get("at", 0.0)
        elif event.get("kind") == "session-end":
            live.pop(event.get("session"), None)
    live = {s: t for s, t in live.items() if now - t < STALE_SECONDS and s != session}

    if action == "start":
        if live:
            holder = sorted(live, key=live.get)[-1]
            print("COORD-WORKTREE-OCCUPIED  {}\n  held by   {}\n  because   one session per"
                  " working tree - two sessions in one tree is how work gets lost\n"
                  "  remedy    use a separate worktree, or run `coord session end` there"
                  .format(_safe(key, 300), _safe(holder)))
            return 3
        append_event(root, {"kind": "session-start", "session": session, "agent": agent,
                            "wi": "WI-0", "path": "-", "at": now, "worktree": key})
        print("session {} registered in {}".format(session, key))
        return 0

    append_event(root, {"kind": "session-end", "session": session, "agent": agent,
                        "wi": "WI-0", "path": "-", "at": now, "worktree": key})
    print("session {} released {}".format(session, key))
    return 0


def cmd_metrics(root, repo, as_json):
    decisions = read_decisions(root)
    allowed = sum(1 for d in decisions if d.get("kind") == "allowed")
    refused = sum(1 for d in decisions if d.get("kind") == "refused")
    unchecked = sum(1 for d in decisions if d.get("kind") == "not_checked")
    total = allowed + refused
    # G15 / R4: a rate over an empty corpus is not a measurement. Report the absence.
    pct = round(100.0 * allowed / total, 1) if total else None
    unique, unique_reason = unique_commits(repo)
    payload = {"decisions": len(decisions), "allowed": allowed, "refused": refused,
               "not_checked": unchecked, "edits_under_lease_pct": pct,
               "unique_commits": unique, "unique_commits_reason": unique_reason,
               "reason": "" if total else "no decisions recorded - nothing to rate"}
    if as_json:
        print(json.dumps(payload))
        return 0
    print("decisions        {}".format(payload["decisions"]))
    print("  allowed        {}".format(allowed))
    print("  refused        {}".format(refused))
    print("  not checked    {}".format(unchecked))
    print("edits under a held lease   {}".format(
        "{}%".format(pct) if pct is not None else "no decisions recorded - nothing to rate"))
    print("commits existing in one place   {}".format(
        unique if unique is not None else unique_reason))
    return 0


def cmd_install(repo, root):
    hooks, err = _git(repo, "rev-parse", "--git-path", "hooks")
    if err:
        print("COORD-NOT-CHECKED-GIT  {}".format(_safe(err, 200)))
        return 4
    hooks_dir = Path(hooks.strip())
    if not hooks_dir.is_absolute():
        hooks_dir = Path(repo) / hooks_dir
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / "pre-commit"
    body = HOOK_BODY.format(marker=HOOK_MARKER, python=sys.executable,
                            script=str(Path(__file__).resolve()).replace("\\", "/"))
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if HOOK_MARKER not in existing:
            # G11 / B6: never overwrite somebody else's hook.
            print("COORD-HOOK-EXISTS  {} already exists and is not ours - not overwritten."
                  "\n  remedy    merge the two by hand, or move the existing hook aside"
                  .format(target))
            return 2
        if existing == body:
            print("pre-commit hook already installed (unchanged)")
            _print_settings_entry(repo)
            return 0
    target.write_text(body, encoding="utf-8", newline="\n")
    try:
        os.chmod(target, 0o755)
    except OSError:
        pass
    gitignore = Path(root) / ".gitignore"
    try:
        Path(root).mkdir(parents=True, exist_ok=True)
        current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        if "decisions/" not in current:
            gitignore.write_text(current + "decisions/\n", encoding="utf-8", newline="\n")
    except OSError:
        pass
    print("Wrote {}  (shared by every worktree of this repo)".format(target))
    _print_settings_entry(repo)
    return 0


def _print_settings_entry(repo):
    """Print the hook entry for a human to paste.

    Built with json.dumps, NOT by hand. The hand-formatted version shipped literal `{{`
    braces (from .format escaping on lines that never called .format) and an unescaped
    Windows path - output that reads correctly and is invalid the moment it is pasted.
    A serializer cannot make either mistake.
    """
    entry = {"hooks": {"PreToolUse": [{
        "matcher": "Write|Edit",
        "hooks": [{"type": "command",
                   "command": sys.executable,
                   "args": [str(Path(__file__).resolve()), "hook"],
                   "timeout": 5}]}]}}
    print("")
    print("Add this to .claude/settings.json yourself - this tool does not edit it:")
    for line in json.dumps(entry, indent=2).splitlines():
        print("  " + line)
    print("")
    print("Enforcement can be switched off by disableAllHooks, allowManagedHooksOnly, or")
    print("strictPluginOnlyCustomization. The pre-commit floor cannot.")


def main(argv=None):
    args = _build_parser().parse_args(argv)

    root, err = resolve_root(os.getcwd(), os.environ.get("COORD_ROOT"))
    if err:
        payload = {"decision": "not_checked", "path": "-"}
        payload.update(err)
        print(render(payload), file=sys.stderr)
        return 4

    session, agent = _identity()
    now = time.time()

    repo = repo_root(os.getcwd())

    if args.cmd == "hook":
        # ALWAYS exit 0: the harness reads the decision in the JSON, not the exit code.
        print(cmd_hook(root, session, agent, now, sys.stdin.read()))
        return 0

    if args.cmd == "guard":
        return cmd_guard(repo, args.fix)

    if args.cmd == "install":
        return cmd_install(repo, root)

    if args.cmd == "metrics":
        return cmd_metrics(root, repo, args.json)

    if args.cmd == "check":
        decision = check(root, args.path, session, now)
        append_decision(root, session, agent, args.path, decision)
        print(json.dumps(decision) if args.json else render(decision))
        return EXIT[decision["decision"]]

    if args.cmd == "precommit":
        if not session:
            print("COORD-NOT-CHECKED-IDENTITY  AGENT_SESSION is unset; nothing was checked")
            return 4
        return cmd_precommit(root, repo, session, agent, now)

    if not session:
        print(render({"decision": "not_checked", "path": "-",
                      "code": "COORD-NOT-CHECKED-IDENTITY",
                      "reason": "AGENT_SESSION is unset"}), file=sys.stderr)
        return 4

    if args.cmd == "claim":
        decision = check(root, args.path, session, now)
        if decision["decision"] == "deny":
            append_decision(root, session, agent, args.path, decision)
            print(render(decision))
            return 3
        try:
            append_event(root, make_event("claim", session, agent, args.wi,
                                          args.path, now, args.ttl))
        except CoordError as exc:
            print("{}: {}".format(exc.code, exc), file=sys.stderr)
            return 2
        print("granted  {}  {}".format(args.path, args.wi))
        return 0

    if args.cmd == "release":
        try:
            append_event(root, make_event("release", session, agent, args.wi,
                                          args.path, now))
        except CoordError as exc:
            print("{}: {}".format(exc.code, exc), file=sys.stderr)
            return 2
        print("released {}".format(args.path))
        return 0

    if args.cmd == "session":
        return cmd_session(root, args.action, session, agent, os.getcwd(), now)

    if args.cmd == "tail":
        # tail is the HUMAN stream, so it reads BOTH stores. `check` is the machine
        # verdict, so it reads only log/. Two grains, two stores, one reader each.
        events, errors, files = read_events(root)
        events = sorted(events + read_decisions(root), key=lambda e: e.get("at", 0.0))
        if files == 0 and not events:
            print("0 files scanned - there is no record here", file=sys.stderr)
            return 4
        for event in events[-args.n:]:
            stamp = time.strftime("%H:%M:%S", time.localtime(event.get("at", 0)))
            print("{}  {:<10} {:<9} {}  {}".format(
                stamp, event.get("agent", "?"), event.get("kind", "?"),
                event.get("path", ""), event.get("wi", "")))
        for line in errors:
            print("  ! unreadable: {}".format(line), file=sys.stderr)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
