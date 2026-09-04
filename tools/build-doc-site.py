#!/usr/bin/env python3
"""build-doc-site.py — render the close-up bundle reading view (AI-Forward, repo dev-tooling).

The Docs Explorer (`docs/index.html`) is the **map**: every artifact in the graph, browsable as
hierarchy, graph, mind map and health. This is the **close-up**: the documentation bundle itself
— the MoC, the architecture overview with its four diagram families, and the generated API
reference — rendered with navigation in one self-contained page that opens over `file://`.

It is emitted as `docs/_site/bundle.html`, NOT as `_site/index.html`. That was the first attempt
and it was wrong: `_site/index.html` is a deliberately designed hub with an accessibility contract
its own test enforces — every raw-markdown destination announced as such *before* navigation, plus
forced-colors support. Overwriting it silently traded a tested contract for a feature nobody asked
to lose. The hub stays the entry point and links here; this file is the reading surface.

Content is embedded as JSON, so the page needs no server and no fetch. Mermaid is loaded from a
CDN by the template: online it renders the diagrams, offline it degrades to the readable source
block — the same trade the Docs Explorer already makes.

Usage
  build-doc-site.py            # write docs/_site/bundle.html
  build-doc-site.py --check    # fail (exit 1) when the committed page is stale
Stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "pack", "templates", "doc-viewer.template.html")
OUT = os.path.join(ROOT, "docs", "_site", "bundle.html")
PROJECT = "AI-Forward"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def strip_frontmatter(text):
    """Drop the YAML record from the rendered view; it is metadata, not documentation."""
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, flags=re.S)


def title_of(text, fallback):
    m = re.search(r"(?m)^title:\s*\"?([^\"\n]+)\"?\s*$", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?m)^#\s+(.+)$", strip_frontmatter(text))
    return m.group(1).strip() if m else fallback


def pages():
    """The bundle, in reading order: entry point, architecture, then the API reference."""
    out = []
    for rel, pid in (("docs/index.md", "index"), ("docs/architecture.md", "architecture")):
        path = os.path.join(ROOT, rel)
        if os.path.isfile(path):
            raw = read(path)
            out.append({"id": pid, "title": title_of(raw, pid),
                        "markdown": strip_frontmatter(raw)})
    api_dir = os.path.join(ROOT, "docs", "api")
    if os.path.isdir(api_dir):
        names = sorted(os.listdir(api_dir))
        # index.md first so the API section opens on its own table of contents.
        names.sort(key=lambda n: (n != "index.md", n))
        for name in names:
            if not name.endswith(".md"):
                continue
            raw = read(os.path.join(api_dir, name))
            out.append({"id": "api-" + name[:-3], "title": title_of(raw, name),
                        "markdown": strip_frontmatter(raw)})
    return out


def head_sha():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def build():
    tpl = read(TEMPLATE)
    docs = pages()

    meta_path = os.path.join(ROOT, "docs", "_meta.json")
    generated, sha = "", head_sha()
    if os.path.isfile(meta_path):
        meta = json.loads(read(meta_path))
        generated = meta.get("generated", "")
        sha = meta.get("documentedCommit", sha)

    docs_js = "window.DOCS = " + json.dumps(docs, ensure_ascii=False, indent=1) + ";"
    meta_js = "window.DOC_META = " + json.dumps(
        {"project": PROJECT, "generated": generated, "documented_sha": sha},
        ensure_ascii=False) + ";"

    out = re.sub(r"window\.DOCS\s*=\s*\[.*?\];", lambda _: docs_js, tpl, count=1, flags=re.S)
    if out == tpl:
        raise SystemExit("build-doc-site: could not find the window.DOCS array in the template")
    out2 = re.sub(r"window\.DOC_META\s*=\s*\{.*?\};", lambda _: meta_js, out, count=1, flags=re.S)
    if out2 == out:
        raise SystemExit("build-doc-site: could not find window.DOC_META in the template")
    return out2.replace("__PROJECT__", PROJECT), len(docs)


def main():
    ap = argparse.ArgumentParser(description="Render docs/_site/bundle.html from the bundle.")
    ap.add_argument("--check", action="store_true",
                    help="fail when the committed page differs from a fresh render")
    args = ap.parse_args()

    text, n = build()
    if args.check:
        if not os.path.isfile(OUT):
            print("DRIFT: docs/_site/bundle.html is missing - re-run tools/build-doc-site.py")
            return 1
        with open(OUT, encoding="utf-8", newline="") as fh:
            current = fh.read().replace("\r\n", "\n")
        if current != text:
            print("DRIFT: docs/_site/bundle.html is stale - re-run tools/build-doc-site.py")
            return 1
        print(f"docs/_site current: {n} pages embedded")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"docs/_site/bundle.html: {n} pages embedded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
