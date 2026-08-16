#!/usr/bin/env python3
"""build-pages-bundle.py - assemble the publishable GitHub Pages bundle (AI-Forward).

Implements the approved "Option A + publish boundary" (docs/notes/hosting-and-dream-manifest.md):
serve from a root where the portal's relative links resolve, so docs/portal/index.html becomes the
shareable front door - BUT enforce a publish boundary that keeps operational/working data LOCAL.

PUBLISH (public - the repo is already public, this just makes it browsable):
  * docs/          (the portal, Docs Explorer, knowledge graph index, architecture, adr, specs,
                    designs, mockups, DESIGN.md, ui-guide) - EXCEPT the local-only subtrees below
  * pack/          (needed: the portal's Foundations/Skills sections link into pack/knowledge & pack/commands)
  * web/           (the interactive explainer + whole-pack index)
  * learnings/fleet-classes.{md,jsonl}   (PROMOTED, abstracted, scrubbed fleet learnings - public by design)
  * README.md, CLAUDE.md, AGENTS.md      (already-public project docs)
  * a generated root index.html -> redirect to docs/portal/index.html, and .nojekyll

KEEP LOCAL (excluded - raw working/operational data, matching "raw dreams + audit kept local"):
  * docs/dreams/           raw dream review surfaces + per-dream evidence (pre-publication working material)
  * docs/audit/            the repo's activity/decision history
  * learnings/manifests/   Dream Manifests (contain repo identifiers + rollout status - operational)
  * learnings/plans/       per-repo reconciliation plans (operational)
  * learnings/promoted.jsonl, learnings/repo-local.jsonl   working ledgers

Deterministic + testable: run it locally (`python tools/build-pages-bundle.py --out _site`) and inspect
the boundary before it ever ships. The Pages workflow runs the same script. Stdlib only; repo dev-tooling.
"""
import argparse, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# top-level dirs/files to publish (allowlist - nothing sensitive slips in by default)
PUBLISH_DIRS = ["docs", "pack", "web"]
PUBLISH_FILES = ["README.md", "CLAUDE.md", "AGENTS.md"]
# fine-grained local-only subtrees inside an otherwise-published dir (the publish boundary)
LOCAL_ONLY = [
    os.path.join("docs", "dreams"),
    os.path.join("docs", "audit"),
    os.path.join("learnings", "manifests"),
    os.path.join("learnings", "plans"),
]
# individual files that ARE publishable out of an otherwise-local dir
PUBLISH_LEARNINGS = ["fleet-classes.md", "fleet-classes.jsonl"]
# never copy these anywhere
NEVER = {".git", "node_modules", "_site", "dist", "__pycache__", ".pytest_cache", "spikes"}

REDIRECT = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=docs/portal/index.html">
<title>AI-Forward - Documentation</title>
<link rel="canonical" href="docs/portal/index.html">
</head><body>
<p>Redirecting to the <a href="docs/portal/index.html">AI-Forward Documentation Portal</a>&hellip;</p>
</body></html>
"""


def is_local_only(rel):
    rel = rel.replace("\\", "/")
    for lo in LOCAL_ONLY:
        lo = lo.replace("\\", "/")
        if rel == lo or rel.startswith(lo + "/"):
            return True
    return False


def copy_tree(src_dir, out_dir, stats):
    """Copy a directory, skipping NEVER dirs and LOCAL_ONLY subtrees."""
    for dp, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in NEVER]
        rel_dir = os.path.relpath(dp, ROOT)
        if is_local_only(rel_dir):
            stats["excluded_dirs"].append(rel_dir.replace("\\", "/"))
            dirs[:] = []  # prune
            continue
        for fn in files:
            src = os.path.join(dp, fn)
            rel = os.path.relpath(src, ROOT)
            if is_local_only(rel):
                continue
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            stats["files"] += 1


def main():
    ap = argparse.ArgumentParser(description="Assemble the publishable GitHub Pages bundle (publish boundary enforced).")
    ap.add_argument("--out", default="_site", help="output directory (default _site)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    out = os.path.join(ROOT, args.out) if not os.path.isabs(args.out) else args.out
    if os.path.abspath(out) in (ROOT, os.path.dirname(ROOT)):
        print("refusing to write bundle over the repo root", file=sys.stderr)
        return 2
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    stats = {"files": 0, "excluded_dirs": []}
    for d in PUBLISH_DIRS:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            copy_tree(p, out, stats)
    for f in PUBLISH_FILES:
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(out, f))
            stats["files"] += 1
    # publishable fleet learnings only (the rest of learnings/ stays local)
    for f in PUBLISH_LEARNINGS:
        p = os.path.join(ROOT, "learnings", f)
        if os.path.isfile(p):
            os.makedirs(os.path.join(out, "learnings"), exist_ok=True)
            shutil.copy2(p, os.path.join(out, "learnings", f))
            stats["files"] += 1

    # root redirect -> the portal, and .nojekyll (paths with dots/underscores)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(REDIRECT)
    open(os.path.join(out, ".nojekyll"), "w").close()
    stats["files"] += 2

    if not args.quiet:
        print("pages bundle -> %s" % args.out)
        print("  published: %d files (docs* / pack / web / fleet-classes / README+CLAUDE+AGENTS + root redirect)" % stats["files"])
        print("  local-only (excluded): docs/dreams, docs/audit, learnings/{manifests,plans,working ledgers}")
        # boundary assertions (fail loudly if a sensitive tree leaked)
        leaked = []
        for lo in LOCAL_ONLY:
            if os.path.exists(os.path.join(out, lo)):
                leaked.append(lo)
        for f in ("promoted.jsonl", "repo-local.jsonl"):
            if os.path.exists(os.path.join(out, "learnings", f)):
                leaked.append("learnings/" + f)
        if leaked:
            print("  ! BOUNDARY VIOLATION - these should be local-only: " + ", ".join(leaked), file=sys.stderr)
            return 1
        print("  boundary OK: no raw dreams / audit / manifests / plans / working ledgers in the bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
