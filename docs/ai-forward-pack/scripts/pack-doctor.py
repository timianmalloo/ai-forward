#!/usr/bin/env python3
"""pack-doctor.py — AI-Forward install-health check (deployable; runs in a TARGET repo).

Reports whether THIS repo has the pack installed and healthy: the installed revision, both
tool surfaces present, the managed blocks intact, and the knowledge graph valid + fresh.
One PASS/WARN/FAIL line per check with a suggested fix; exit 1 if any FAIL.

Distinct from tools/check-consistency.py (which validates the pack SOURCE — pack/ == docs).
A target repo has no pack/, so this checks INSTALL health, not source consistency.
Design: docs/design/pack-doctor.md. Stdlib only; composes docs-graph.py for the graph half.

Usage
  pack-doctor.py [--root <repo>] [--json]
Exit: 0 all PASS/WARN · 1 any FAIL.
"""
import argparse, json, os, re, subprocess, sys

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def _result(name, status, detail, fix=""):
    return {"name": name, "status": status, "detail": detail, "fix": fix}


def check_installed(root):
    p = os.path.join(root, "docs", "ai-forward-pack", "INSTALL.md")
    if not os.path.exists(p):
        return _result("pack installed", FAIL,
                       "docs/ai-forward-pack/INSTALL.md not found",
                       "run /addpacktorepo (this repo has no pack installed)"), None
    text = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"^revision:\s*(\d+)", text, re.M)
    if not m:
        return _result("pack installed", WARN, "INSTALL.md present but revision unreadable",
                       "re-run /updatepack to restamp the revision"), None
    rev = m.group(1)
    bv = re.search(r"^bundle_version:\s*'([^']+)'", text, re.M)
    detail = f"revision {rev}" + (f" ({bv.group(1)})" if bv else "")
    return _result("pack installed", PASS, detail), rev


def check_surface(root, label, subdirs):
    base = os.path.join(root, *label.split("/")) if "/" in label else os.path.join(root, label)
    missing = [d for d in subdirs if not os.path.isdir(os.path.join(root, *d.split("/")))]
    surface = "Claude Code" if label == ".claude" else "Copilot"
    if not os.path.isdir(os.path.join(root, label)):
        return _result(f"{surface} surface", FAIL, f"{label}/ not present",
                       "run /updatepack (or pwsh tools/sync-pack.ps1 in the source repo)")
    if missing:
        return _result(f"{surface} surface", FAIL, f"missing: {', '.join(missing)}",
                       "run /updatepack to restore the full surface")
    return _result(f"{surface} surface", PASS, f"{label}/{{{','.join(s.split('/')[-1] for s in subdirs)}}} present")


def check_block(root, fname):
    p = os.path.join(root, fname)
    if not os.path.exists(p):
        return _result(f"{fname} managed block", WARN, f"{fname} not present",
                       "run /updatepack to add the managed block")
    text = open(p, encoding="utf-8", errors="replace").read()
    begins = text.count("AI-FORWARD-PACK:BEGIN")
    ends = text.count("AI-FORWARD-PACK:END")
    if begins == 1 and ends == 1:
        return _result(f"{fname} managed block", PASS, "intact (1 block)")
    if begins == 0:
        return _result(f"{fname} managed block", FAIL, "no AI-FORWARD-PACK block",
                       "run /updatepack to paste the managed block")
    return _result(f"{fname} managed block", FAIL, f"{begins} begin / {ends} end markers (expected 1/1)",
                   "remove duplicate blocks; keep one BEGIN/END pair")


def check_graph(root):
    bundle = os.path.join(root, "docs", "ai-forward-pack", "scripts", "docs-graph.py")
    if not os.path.exists(bundle):
        return _result("knowledge graph", WARN, "docs-graph.py not found",
                       "run /updatepack to restore the script bundle")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        v = subprocess.run([sys.executable, bundle, "validate"], cwd=root,
                           capture_output=True, text=True, env=env)
    except Exception as e:
        return _result("knowledge graph", WARN, f"graph tool unavailable ({e})",
                       "check Python availability")
    if v.returncode == 0:
        f = subprocess.run([sys.executable, bundle, "freshness"], cwd=root,
                           capture_output=True, text=True, env=env)
        if f.returncode != 0:
            return _result("knowledge graph", WARN, "valid but has stale/flagged/orphan nodes",
                           "review review-by dates; run docs-graph.py freshness for detail")
        return _result("knowledge graph", PASS, "schema-valid, no dangling links, fresh")
    # validate failed: could be genuine problems, or no graph yet
    try:
        info = json.loads(v.stdout)
        n = info.get("artifacts", 0)
        if n == 0:
            return _result("knowledge graph", WARN, "no graph yet (0 artifacts)",
                           "the first skill run creates docs/docs-index.js")
        return _result("knowledge graph", FAIL, f"{len(info.get('problems', []))} graph problem(s)",
                       "run docs-graph.py validate for detail; fix frontmatter")
    except Exception:
        return _result("knowledge graph", WARN, "graph validation inconclusive",
                       "run docs-graph.py validate manually")


def run(root):
    checks = [
        check_installed(root)[0],
        check_surface(root, ".claude", [".claude/knowledge", ".claude/skills", ".claude/agents"]),
        check_surface(root, ".github", [".github/instructions", ".github/prompts", ".github/agents"]),
        check_block(root, "CLAUDE.md"),
        check_block(root, "AGENTS.md"),
        check_graph(root),
    ]
    return checks


def main():
    ap = argparse.ArgumentParser(description="AI-Forward install-health doctor")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    checks = run(root)
    summary = {s: sum(1 for c in checks if c["status"] == s) for s in (PASS, WARN, FAIL)}
    if args.json:
        print(json.dumps({"checks": checks, "summary": summary}, indent=2))
    else:
        print("AI-Forward doctor — install health\n")
        for c in checks:
            print(f"  {c['status']:5} {c['name']:24} {c['detail']}")
            if c["fix"] and c["status"] != PASS:
                print(f"        -> fix: {c['fix']}")
        print(f"\n  {summary[FAIL]} FAIL · {summary[WARN]} WARN · {summary[PASS]} PASS")
    return 1 if summary[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
