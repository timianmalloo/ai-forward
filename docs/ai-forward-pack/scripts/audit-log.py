#!/usr/bin/env python3
"""audit-log.py — the AI-Forward Pack audit & change log bundle (audit-and-change-log.md).

Durable, committed, history-as-knowledge for a repo: an append-only record of every
meaningful prompt / skill / script / decision, so any future Copilot or Claude Code
session reads the project's own history instead of starting blind. The canonical logs
are append-only JSONL (clean git diffs, like docs/health-history.jsonl); the viewer
reads a derived window.AUDIT_DATA JS (loadable over file://, like docs/docs-index.js).
Python 3.8+, stdlib only — no dependencies.

Two logs, one bundle:
  docs/audit/audit-log.jsonl    every action (shortname, datetime, session, prompt, summary, …)
  docs/audit/change-log.jsonl   the meaningful design changes / decisions (+ git before/after)
  docs/audit/audit-data.js      derived window.AUDIT_DATA = {audit:[…], changes:[…]} (the viewer's data)
  docs/audit/index.html         the interactive viewer (self-bootstrapped from the template)

Subcommands
  append      Add an audit entry.            (Audit Mandate — every skill's last action)
  change      Add a change-log entry.        (Change Mandate — collectknowledge/define-architecture/design/migrate)
  list        Show the last N entries (audit|change). For the CLI skill.
  search      Filter by --session / --since / --until / --keyword. For the CLI skill.
  get         Print one entry by --id (use --field prompt to extract the prompt to re-run).
  render      Regenerate audit-data.js from the JSONL and ensure the viewer exists (repair).
  git-context Print the current git {sha, short, branch, pushed} as JSON (a helper).
  suggest     Discern unlogged meaningful changes (recent commits + new ADRs/notes not in the change log).
  import      Ingest a session-export JSON array of turns into the audit log (build on session history).

Conventions
  --root defaults to docs/. The audit dir is <root>/audit. The viewer template is resolved
  relative to this script (pack/templates or docs/ai-forward-pack/templates). git is optional —
  every git call degrades gracefully when git or a repo is absent. This tool never invents a
  prompt or a summary; required fields must be supplied (flags, --*-file, or --from-json -).
"""
import argparse, datetime, html, json, os, re, subprocess, sys

ISO = "%Y-%m-%dT%H:%M:%SZ"
AUDIT_KINDS = ["skill", "command", "script", "prompt", "commit", "manual", "session-import"]
CHANGE_KINDS = ["architecture", "design", "knowledge", "migration", "decision", "spec", "other"]


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime(ISO)


def audit_dir(root):
    return os.path.join(root, "audit")


def log_path(root, which):
    return os.path.join(audit_dir(root), "audit-log.jsonl" if which == "audit" else "change-log.jsonl")


# ---------- JSONL read / append ----------
def read_log(root, which):
    p = log_path(root, which)
    if not os.path.exists(p):
        return []
    out = []
    for ln in open(p, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            pass  # a malformed line is skipped, never fatal — the log keeps working
    return out


def append_log(root, which, entry):
    os.makedirs(audit_dir(root), exist_ok=True)
    with open(log_path(root, which), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def next_id(entries, prefix):
    n = 0
    for e in entries:
        m = re.match(prefix + r"-(\d+)$", str(e.get("id", "")))
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}-{n + 1:04d}"


# ---------- git helpers (always graceful) ----------
def git(args, root):
    try:
        cwd = os.path.dirname(os.path.abspath(root)) or "."
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def git_context(root):
    sha = git(["rev-parse", "HEAD"], root)
    if not sha:
        return {"sha": None, "short": None, "branch": None, "pushed": None}
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    # pushed == no commits ahead of the upstream (None when there is no upstream)
    ahead = git(["rev-list", "--count", "@{upstream}..HEAD"], root)
    pushed = (ahead == "0") if ahead is not None else None
    return {"sha": sha, "short": sha[:9], "branch": branch, "pushed": pushed}


def commits_between(before, after, root):
    if not before or not after:
        return []
    out = git(["log", "--pretty=%h %s", f"{before}..{after}"], root)
    return [ln for ln in (out or "").split("\n") if ln.strip()]


# ---------- viewer (self-bootstrap from the template) ----------
def find_template():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "..", "templates", "audit-explorer.template.html"),
                 os.path.join(here, "..", "..", "templates", "audit-explorer.template.html")):
        if os.path.exists(cand):
            return os.path.abspath(cand)
    return None


def project_name(root):
    return os.path.basename(os.path.abspath(os.path.join(root, "..")))


def render(root, project=None):
    """Regenerate audit-data.js and the managed viewer from canonical sources."""
    os.makedirs(audit_dir(root), exist_ok=True)
    data = {"project": project or project_name(root), "generated": now_iso(),
            "audit": read_log(root, "audit"), "changes": read_log(root, "change")}
    # </ is escaped so a prompt containing </script> can never break the <script> host.
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    body = ("// Derived from docs/audit/*.jsonl by scripts/audit-log.py — DO NOT hand-edit"
            " (the JSONL logs are the source of truth; see audit-and-change-log.md).\n"
            "window.AUDIT_DATA = " + payload + ";\n")
    open(os.path.join(audit_dir(root), "audit-data.js"), "w", encoding="utf-8").write(body)
    idx = os.path.join(audit_dir(root), "index.html")
    tpl = find_template()
    if tpl:
        viewer = open(tpl, encoding="utf-8").read().replace(
            "__PROJECT__", html.escape(data["project"], quote=True)
        )
        open(idx, "w", encoding="utf-8").write(viewer)
    return data


# ---------- field collection (flags / files / stdin JSON) ----------
def _read_field(value, value_file):
    if value_file:
        if value_file == "-":
            return sys.stdin.read().rstrip("\n")
        return open(value_file, encoding="utf-8").read().rstrip("\n")
    return value


def _from_json(arg):
    if not arg:
        return {}
    text = sys.stdin.read() if arg == "-" else open(arg, encoding="utf-8").read()
    obj = json.loads(text)
    return obj if isinstance(obj, dict) else {}


# ---------- subcommands ----------
def cmd_append(args):
    base = _from_json(getattr(args, "from_json", None))
    prompt = _read_field(args.prompt, args.prompt_file) or base.get("prompt")
    summary = _read_field(args.summary, args.summary_file) or base.get("summary")
    shortname = args.shortname or base.get("shortname")
    session = args.session or base.get("session")
    missing = [k for k, v in [("shortname", shortname), ("session", session),
                              ("prompt", prompt), ("summary", summary)] if not v]
    if missing:
        sys.stderr.write(f"audit-log append: missing required field(s): {', '.join(missing)}\n")
        return 2
    entries = read_log(args.root, "audit")
    entry = {
        "id": next_id(entries, "al"),
        "shortname": shortname,
        "datetime": args.datetime or base.get("datetime") or now_iso(),
        "session": session,
        "prompt": prompt,
        "summary": summary,
        "kind": args.kind or base.get("kind") or "manual",
        "skill": args.skill or base.get("skill"),
        "tool": args.tool or base.get("tool"),
        "actor": args.actor or base.get("actor"),
        "artifacts": (args.artifact or []) or base.get("artifacts") or [],
        "tags": (args.tag or []) or base.get("tags") or [],
        "outcome": args.outcome or base.get("outcome") or "success",
    }
    if args.change or base.get("change"):
        entry["change"] = args.change or base.get("change")
    if args.git:
        entry["git"] = git_context(args.root)
    append_log(args.root, "audit", entry)
    render(args.root, args.project)
    print(entry["id"])
    return 0


def cmd_change(args):
    base = _from_json(getattr(args, "from_json", None))
    title = args.title or base.get("title")
    summary = _read_field(args.summary, args.summary_file) or base.get("summary")
    missing = [k for k, v in [("title", title), ("summary", summary)] if not v]
    if missing:
        sys.stderr.write(f"audit-log change: missing required field(s): {', '.join(missing)}\n")
        return 2
    after = git_context(args.root)
    before = args.git_before or base.get("git_before")
    entries = read_log(args.root, "change")
    entry = {
        "id": next_id(entries, "cl"),
        "datetime": args.datetime or now_iso(),
        "session": args.session or base.get("session"),
        "kind": args.kind or base.get("kind") or "decision",
        "skill": args.skill or base.get("skill"),
        "title": title,
        "prompt": _read_field(args.prompt, args.prompt_file) or base.get("prompt"),
        "summary": summary,
        "rationale": args.rationale or base.get("rationale"),
        "artifacts": (args.artifact or []) or base.get("artifacts") or [],
        "tags": (args.tag or []) or base.get("tags") or [],
        "git": {"before": before, "after": after.get("sha"), "branch": after.get("branch"),
                "pushed": after.get("pushed"), "commits": commits_between(before, after.get("sha"), args.root)},
    }
    if args.supersedes or base.get("supersedes"):
        entry["supersedes"] = args.supersedes or base.get("supersedes")
    if args.audit_ref or base.get("audit_ref"):
        entry["audit_ref"] = args.audit_ref or base.get("audit_ref")
    append_log(args.root, "change", entry)
    render(args.root, args.project)
    print(entry["id"])
    return 0


def _fmt_row(e, which):
    when = (e.get("datetime") or "")[:16].replace("T", " ")
    if which == "audit":
        label = e.get("shortname") or e.get("skill") or e.get("kind") or "—"
    else:
        label = e.get("title") or e.get("kind") or "—"
    summ = (e.get("summary") or "").replace("\n", " ")
    if len(summ) > 80:
        summ = summ[:77] + "…"
    sess = (e.get("session") or "")[:8]
    return f"{e.get('id','?'):<8} {when:<16} {sess:<8} {label[:24]:<24} {summ}"


def cmd_list(args):
    entries = read_log(args.root, args.kind)
    if args.json:
        print(json.dumps(entries[-args.n:], ensure_ascii=False, indent=2))
        return 0
    sel = entries[-args.n:]
    if not sel:
        print(f"(no {args.kind} entries yet)")
        return 0
    print(f"{'id':<8} {'datetime':<16} {'session':<8} {'label':<24} summary")
    for e in sel:
        print(_fmt_row(e, args.kind))
    return 0


def _matches(e, kw):
    if not kw:
        return True
    hay = " ".join(str(e.get(k, "")) for k in
                   ("id", "shortname", "title", "prompt", "summary", "skill", "kind", "actor"))
    hay += " " + " ".join(e.get("tags") or []) + " " + " ".join(e.get("artifacts") or [])
    return kw.lower() in hay.lower()


def cmd_search(args):
    entries = read_log(args.root, args.kind)
    res = []
    for e in entries:
        if args.session and args.session not in str(e.get("session", "")):
            continue
        dt = str(e.get("datetime", ""))
        if args.since and dt < args.since:
            continue
        if args.until and dt > args.until:
            continue
        if not _matches(e, args.keyword):
            continue
        res.append(e)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if not res:
        print("(no matches)")
        return 0
    print(f"{'id':<8} {'datetime':<16} {'session':<8} {'label':<24} summary")
    for e in res:
        print(_fmt_row(e, args.kind))
    print(f"\n{len(res)} match(es)")
    return 0


def cmd_get(args):
    for which in ("audit", "change"):
        for e in read_log(args.root, which):
            if str(e.get("id")) == args.id:
                if args.field:
                    print(e.get(args.field, ""))
                else:
                    print(json.dumps(e, ensure_ascii=False, indent=2))
                return 0
    sys.stderr.write(f"audit-log get: id not found: {args.id}\n")
    return 1


def cmd_render(args):
    data = render(args.root, args.project)
    print(f"rendered {len(data['audit'])} audit + {len(data['changes'])} change entries "
          f"-> {os.path.join(audit_dir(args.root), 'audit-data.js')}")
    return 0


def cmd_git_context(args):
    print(json.dumps(git_context(args.root), indent=2))
    return 0


def cmd_suggest(args):
    """Advisory: surface meaningful changes that may not be in the change log yet."""
    changes = read_log(args.root, "change")
    last_after = None
    for e in changes:
        a = (e.get("git") or {}).get("after")
        if a:
            last_after = a
    head = git(["rev-parse", "HEAD"], args.root)
    findings = []
    if last_after and head:
        for ln in commits_between(last_after, head, args.root):
            findings.append(("commit", ln))
    elif head:
        for ln in (git(["log", "-n", str(args.n), "--pretty=%h %s"], args.root) or "").split("\n"):
            if ln.strip():
                findings.append(("commit", ln))
    # New decision artifacts (ADRs / decision notes) not referenced by any change entry.
    referenced = " ".join(json.dumps(e) for e in changes)
    for sub in ("adr", "notes"):
        d = os.path.join(args.root, sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".md") and f[:-3] not in referenced and f not in referenced:
                    findings.append(("artifact", f"docs/{sub}/{f}"))
    if not findings:
        print("no unlogged meaningful changes detected")
        return 0
    print("Possible meaningful changes not yet in the change log "
          "(promote with `audit-log.py change`):")
    for kind, what in findings:
        print(f"  [{kind}] {what}")
    return 0


def cmd_import(args):
    """Ingest a session-export JSON array of turns into the audit log (build on session history)."""
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    rows = json.loads(text)
    if isinstance(rows, dict):
        rows = rows.get("turns") or rows.get("entries") or [rows]
    entries = read_log(args.root, "audit")
    existing = {e.get("id") for e in entries}
    added = 0
    for r in rows:
        prompt = r.get("prompt") or r.get("user_message") or ""
        summary = r.get("summary") or r.get("assistant_response") or ""
        if not (prompt or summary):
            continue
        if len(summary) > 280:
            summary = summary[:277] + "…"
        eid = next_id(entries, "al")
        entry = {
            "id": eid,
            "shortname": r.get("shortname") or (r.get("session", "") or "session")[:8] + f"-t{r.get('turn_index', added)}",
            "datetime": r.get("datetime") or r.get("timestamp") or now_iso(),
            "session": r.get("session") or r.get("session_id") or args.session,
            "prompt": prompt,
            "summary": summary or "(imported turn)",
            "kind": "session-import",
            "skill": r.get("skill"),
            "tool": r.get("tool") or args.tool,
            "actor": r.get("actor"),
            "artifacts": r.get("artifacts") or [],
            "tags": r.get("tags") or ["imported"],
            "outcome": r.get("outcome") or "success",
        }
        if eid in existing:
            continue
        entries.append(entry)
        append_log(args.root, "audit", entry)
        existing.add(eid)
        added += 1
    render(args.root, args.project)
    print(f"imported {added} session turn(s) into the audit log")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="audit-log.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="docs", help="docs root (default: docs); audit dir is <root>/audit")
    ap.add_argument("--project", default=None, help="project name for the viewer (default: repo dir name)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_a = sub.add_parser("append", help="add an audit entry")
    ap_a.add_argument("--shortname"); ap_a.add_argument("--session"); ap_a.add_argument("--prompt")
    ap_a.add_argument("--prompt-file", dest="prompt_file"); ap_a.add_argument("--summary")
    ap_a.add_argument("--summary-file", dest="summary_file"); ap_a.add_argument("--datetime")
    ap_a.add_argument("--kind", choices=AUDIT_KINDS); ap_a.add_argument("--skill")
    ap_a.add_argument("--tool"); ap_a.add_argument("--actor")
    ap_a.add_argument("--artifact", action="append"); ap_a.add_argument("--tag", action="append")
    ap_a.add_argument("--outcome", choices=["success", "partial", "failed", "blocked"])
    ap_a.add_argument("--change", help="link to a change-log id (cl-NNNN)")
    ap_a.add_argument("--git", action="store_true", help="capture current git context")
    ap_a.add_argument("--from-json", dest="from_json", help="read fields from a JSON object (path or - for stdin)")

    ap_c = sub.add_parser("change", help="add a change-log entry")
    ap_c.add_argument("--title"); ap_c.add_argument("--summary"); ap_c.add_argument("--summary-file", dest="summary_file")
    ap_c.add_argument("--session"); ap_c.add_argument("--kind", choices=CHANGE_KINDS); ap_c.add_argument("--skill")
    ap_c.add_argument("--prompt"); ap_c.add_argument("--prompt-file", dest="prompt_file"); ap_c.add_argument("--rationale")
    ap_c.add_argument("--artifact", action="append"); ap_c.add_argument("--tag", action="append")
    ap_c.add_argument("--supersedes"); ap_c.add_argument("--audit-ref", dest="audit_ref")
    ap_c.add_argument("--git-before", dest="git_before", help="HEAD sha captured before the work began")
    ap_c.add_argument("--datetime")
    ap_c.add_argument("--from-json", dest="from_json", help="read fields from a JSON object (path or - for stdin)")

    ap_l = sub.add_parser("list", help="show the last N entries")
    ap_l.add_argument("--n", type=int, default=10); ap_l.add_argument("--kind", choices=["audit", "change"], default="audit")
    ap_l.add_argument("--json", action="store_true")

    ap_s = sub.add_parser("search", help="filter by session/datetime/keyword")
    ap_s.add_argument("--kind", choices=["audit", "change"], default="audit")
    ap_s.add_argument("--session"); ap_s.add_argument("--since"); ap_s.add_argument("--until")
    ap_s.add_argument("--keyword"); ap_s.add_argument("--json", action="store_true")

    ap_g = sub.add_parser("get", help="print one entry by id")
    ap_g.add_argument("--id", required=True); ap_g.add_argument("--field", help="print just this field (e.g. prompt)")

    sub.add_parser("render", help="regenerate audit-data.js and ensure the viewer exists")
    sub.add_parser("git-context", help="print current git context as JSON")

    ap_sug = sub.add_parser("suggest", help="surface meaningful changes not yet in the change log")
    ap_sug.add_argument("--n", type=int, default=15)

    ap_imp = sub.add_parser("import", help="ingest a session-export JSON array into the audit log")
    ap_imp.add_argument("--file", default="-", help="JSON file (or - for stdin)")
    ap_imp.add_argument("--session"); ap_imp.add_argument("--tool")

    args = ap.parse_args()
    dispatch = {
        "append": cmd_append, "change": cmd_change, "list": cmd_list, "search": cmd_search,
        "get": cmd_get, "render": cmd_render, "git-context": cmd_git_context,
        "suggest": cmd_suggest, "import": cmd_import,
    }
    sys.exit(dispatch[args.cmd](args))


if __name__ == "__main__":
    main()
