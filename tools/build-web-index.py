#!/usr/bin/env python3
"""build-web-index.py — whole-pack navigable/searchable index generator (AI-Forward).

Scans the ENTIRE repository — the pack source (knowledge, skills, templates, scripts,
personas), the examples, the docs/ knowledge graph, and the guide surfaces — and emits
`web/pack-index.js` (`window.PACK_INDEX`), which `web/index.html` renders as a single
searchable, navigable index of everything in the repo.

This is repo dev-tooling (like check-consistency.py / sync-pack.ps1): it lives in tools/
and is NOT deployed to target repos. It is distinct from docs-graph.py, which derives the
docs/ knowledge graph (docs/docs-index.js) from V2 frontmatter; this tool indexes the
whole pack, most of which has no V2 frontmatter, and *reuses* docs-graph's output for the
graph slice. Stdlib only. Re-run after any pack change (wired into sync-pack.ps1).
"""
import datetime, glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")
TEXT_CAP = 6000          # per-item searchable-text budget (keeps the index lean)
SUMMARY_CAP = 240

CATEGORIES = [           # id, label — display order
    ("knowledge", "Knowledge docs"), ("skills", "Skills"), ("templates", "Templates"),
    ("scripts", "Scripts"), ("personas", "Personas"), ("examples", "Examples"),
    ("graph", "Knowledge graph (docs/)"), ("guides", "Guides & surfaces"),
]


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def clip(s, n):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def searchtext(*parts):
    return clip(" ".join(p for p in parts if p), TEXT_CAP).lower()


def headings(body):
    return " ".join(m.group(1) for m in re.finditer(r"^#{1,4}\s+(.+)$", body, re.M))


def frontmatter(text):
    """Return (fm_dict_subset, body). Parses name/description (incl. folded/block)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw, body = text[3:end], text[end + 4:]
    fm = {}
    lines = fm_raw.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(name|description|title|type):\s*(.*)$", ln)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ""):  # folded/block scalar — gather indented body
            buf = []
            for nxt in lines[i + 1:]:
                if nxt and not nxt[0].isspace():
                    break
                buf.append(nxt.strip())
            val = " ".join(b for b in buf if b)
        fm[key] = val.strip().strip('"')
    return fm, body


def first_title(body, fallback):
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return m.group(1).strip() if m else fallback


def first_para(body):
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        return s.strip("*_> ").strip()
    return ""


def add(items, cat, _id, title, summary, path, kind, text):
    items.append({"cat": cat, "id": _id, "title": title, "summary": clip(summary, SUMMARY_CAP),
                  "path": path, "kind": kind, "text": text})


def scan_knowledge(items):
    for p in sorted(glob.glob(os.path.join(PACK, "knowledge", "*.md"))):
        body = read(p)
        name = os.path.basename(p)[:-3]
        if name == "FOUNDATION":
            add(items, "knowledge", name, "FOUNDATION", "Provenance manifest for the vendored foundation docs (not an instruction).",
                rel(p), "manifest", searchtext("foundation provenance manifest", body))
            continue
        title = first_title(body, name)
        summ = first_para(body)
        add(items, "knowledge", name, title, summ, rel(p), "knowledge",
            searchtext(title, summ, headings(body), body))


def scan_skills(items):
    for p in sorted(glob.glob(os.path.join(PACK, "commands", "*", "SKILL.md"))):
        fm, body = frontmatter(read(p))
        name = fm.get("name") or os.path.basename(os.path.dirname(p))
        desc = fm.get("description", "")
        add(items, "skills", name, "/" + name, desc, rel(p), "skill",
            searchtext("/" + name, desc, headings(body)))


def scan_templates(items):
    for p in sorted(glob.glob(os.path.join(PACK, "templates", "*"))):
        if os.path.isdir(p):
            continue
        fn = os.path.basename(p)
        body = read(p)
        if fn.endswith(".md"):
            fm, b = frontmatter(body)
            title = fm.get("title") or first_title(b, fn)
            summ = fm.get("summary") or first_para(b)
        else:  # .html
            title = fn
            cm = re.search(r"<!--\s*(.+?)\s*-->", body, re.S)
            summ = (cm.group(1).strip().splitlines()[0] if cm else first_para(body))
        add(items, "templates", fn, title, summ, rel(p), "template",
            searchtext(fn, title, summ))


def scan_scripts(items):
    paths = glob.glob(os.path.join(PACK, "scripts", "*.py"))
    paths.extend(glob.glob(os.path.join(PACK, "scripts", "*.js")))
    for p in sorted(paths):
        body = read(p)
        fn = os.path.basename(p)
        doc = re.search(r'"""(.*?)"""', body, re.S)
        js_doc = re.search(r"^\s*/\*\*(.*?)\*/", body, re.S)
        docstr = doc.group(1).strip() if doc else ""
        if not docstr and js_doc:
            docstr = re.sub(r"^\s*\*\s?", "", js_doc.group(1), flags=re.M).strip()
        summ = docstr.splitlines()[0] if docstr else ""
        defs = " ".join(re.findall(r"^\s*def\s+(\w+)", body, re.M))
        add(items, "scripts", fn, fn, summ, rel(p), "script",
            searchtext(fn, docstr, defs))


def scan_personas(items):
    seen = set()
    for d in ("claude-code", "copilot"):
        for p in sorted(glob.glob(os.path.join(PACK, "adapters", d, "agents", "*.md"))):
            fm, body = frontmatter(read(p))
            name = fm.get("name") or os.path.basename(p).replace("_agent", "")[:-3]
            if name in seen:
                continue
            seen.add(name)
            desc = fm.get("description", "")
            add(items, "personas", name, name, desc, rel(p), "persona",
                searchtext(name, desc, body[:1500]))


def scan_examples(items):
    base = os.path.join(PACK, "examples")
    for dirpath, _dirs, files in os.walk(base):  # os.walk descends into dot-dirs (.claude)
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            body = read(p)
            r = rel(p)
            fm, b = frontmatter(body) if p.endswith(".md") else ({}, body)
            title = fm.get("title") or first_title(b, os.path.basename(p))
            summ = fm.get("summary") or fm.get("description") or first_para(b)
            add(items, "examples", r, title, summ, r, "example",
                searchtext(r, title, summ, b[:2000]))


def scan_graph(items):
    """Reuse docs-graph's output: parse window.DOCS_INDEX from docs/docs-index.js."""
    txt = read(os.path.join(ROOT, "docs", "docs-index.js"))
    m = re.search(r"window\.DOCS_INDEX\s*=\s*(\{.*\});?\s*$", txt, re.S)
    if not m:
        return
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return
    for a in data.get("artifacts", []):
        links = " ".join(f"{l.get('rel','')} {l.get('to','')}" for l in a.get("links", []))
        add(items, "graph", a.get("id", ""), a.get("title", a.get("id", "")),
            a.get("summary", ""), a.get("path", ""), a.get("type", "doc"),
            searchtext(a.get("title", ""), a.get("summary", ""),
                       " ".join(a.get("tags", [])), links))


def scan_guides(items):
    guides = [
        ("web/ai-forward-pack-explainer.html", "Interactive Explainer",
         "Self-contained page explaining the pack's reasoning, personas, skills, and the UI archetype grammar with rendered mockups."),
        ("docs/index.html", "Docs Explorer",
         "The docs/ knowledge graph browsable as hierarchy, graph, mind map, and health. Loads docs/docs-index.js."),
        ("docs/index.md", "Documentation Map of Content",
         "Curated human entry point linking the architecture, the explainer, the Docs Explorer, and the pack."),
        ("docs/architecture.md", "Architecture Overview",
         "The source -> build -> install -> consumer structure and the four diagram families; the architecture of record."),
        ("docs/audit/index.html", "Audit & Change-Log Viewer",
         "Searchable timeline of every meaningful prompt/skill/script and design decision (docs/audit)."),
        ("README.md", "Repository README", "The repo front door: layout, build/maintenance commands, conventions."),
        ("pack/README.md", "Pack README", "The pack's own README — structure and payload."),
        ("pack/OVERVIEW.md", "Pack OVERVIEW", "The pack overview — the artifacts, the standards, the system."),
        ("pack/adapters/INSTALL.md", "INSTALL & changelog", "Deployment map + the revision changelog (the refresh guide)."),
    ]
    for path, title, summ in guides:
        if os.path.exists(os.path.join(ROOT, path)):
            add(items, "guides", path, title, summ, path, "guide", searchtext(title, summ, path))


def main():
    items = []
    scan_knowledge(items)
    scan_skills(items)
    scan_templates(items)
    scan_scripts(items)
    scan_personas(items)
    scan_examples(items)
    scan_graph(items)
    scan_guides(items)

    counts = {c: sum(1 for it in items if it["cat"] == c) for c, _ in CATEGORIES}
    payload = {
        "repo": "AI-Forward",
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "tools/build-web-index.py",
        "categories": [{"id": c, "label": l, "count": counts[c]} for c, l in CATEGORIES],
        "total": len(items),
        "items": items,
    }
    out = os.path.join(ROOT, "web", "pack-index.js")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Generated by tools/build-web-index.py — do not hand-edit. Re-run after pack changes (wired into sync-pack.ps1).\n")
        f.write("window.PACK_INDEX = ")
        json.dump(payload, f, ensure_ascii=False, indent=0)
        f.write(";\n")
    print(f"web/pack-index.js: {len(items)} items "
          + ", ".join(f"{counts[c]} {c}" for c, _ in CATEGORIES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
