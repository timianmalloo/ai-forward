#!/usr/bin/env python3
"""build-docs-portal.py - generate the unified Documentation Portal data (AI-Forward).

Emits `docs/portal/portal-data.js` (`window.PORTAL_DATA`), rendered by the committed shell
`docs/portal/index.html` as the single front door to the whole repo: a capabilities overview,
getting-started, every skill, the Foundations (reasoning constitution + engineering guidance +
coding style), the UI & Design capabilities and examples, the Architecture (of-record + ADRs +
specs + designs), the Systems, an embedded knowledge-Graph view, and a reference/link-out map.

DESIGN PRINCIPLE (spec-documentation-portal): the portal is a LENS, not a copy. It LISTS and LINKS
the structured artifacts with DERIVED summaries; the artifacts themselves stay structured where they
live. So the portal is a pure, deterministic function of committed sources and CANNOT drift:
  * skill list + count      <- pack/commands/*/                         (complete by construction)
  * skill descriptions      <- each skill's Copilot prompt frontmatter
  * counts                  <- pack/adapters/INSTALL.md `counts:`
  * Foundations             <- pack/knowledge/*.md (title + summary), grouped by the editorial map
  * Architecture            <- docs/architecture*.md + docs/adr + docs/specs + docs/design (frontmatter)
  * UI examples             <- docs/mockups/*.md (frontmatter)
  * Graph                   <- docs/docs-index.js (window.DOCS_INDEX) nodes + typed edges
  * editorial framing       <- tools/docs-portal-editorial.json
There is NO timestamp in the output, so regeneration over identical sources is BYTE-IDENTICAL; that
is what lets check-consistency.py drift-gate it. Repo dev-tooling (like build-web-index.py); re-run
by sync-pack.ps1 on every pack change. Stdlib only.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")
OUT_DIR = os.path.join(ROOT, "docs", "portal")
EDITORIAL = os.path.join(ROOT, "tools", "docs-portal-editorial.json")
SUMMARY_CAP = 260


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


def clip(s, n=SUMMARY_CAP):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


def strip_frontmatter(txt):
    m = re.match(r"^---\n.*?\n---\n(.*)$", txt, re.S)
    return m.group(1) if m else txt


def frontmatter_field(txt, field):
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    if not m:
        return ""
    fm = m.group(1)
    if field == "summary":
        sm = re.search(r"(?ms)^summary:\s*>-?\s*\n((?:[ \t]+.*\n?)+)", fm)
        if sm:
            return clip(re.sub(r"\s+", " ", sm.group(1)))
        sm = re.search(r"(?m)^summary:\s*(.+)$", fm)
        return clip(sm.group(1)) if sm else ""
    m2 = re.search(r"(?m)^%s:\s*(.+)$" % re.escape(field), fm)
    if m2:
        return m2.group(1).strip().strip('"').strip("'")
    return ""


def first_heading(txt):
    m = re.search(r"(?m)^#\s+(.+?)\s*$", strip_frontmatter(txt))
    return m.group(1).strip() if m else ""


def first_paragraph(txt):
    body = strip_frontmatter(txt)
    for para in re.split(r"\n\s*\n", body):
        p = para.strip()
        if not p or p.startswith("#") or p.startswith(">") or p.startswith("*Version") or p.startswith("|"):
            continue
        if p.startswith("*") and p.endswith("*"):
            continue
        return clip(re.sub(r"[*`]", "", re.sub(r"\s+", " ", p)))
    return ""


# ---------------------------------------------------------------- skills
def skill_names():
    base = os.path.join(PACK, "commands")
    return sorted(n for n in os.listdir(base)
                  if os.path.isfile(os.path.join(base, n, "SKILL.md"))) if os.path.isdir(base) else []


def skill_description(name):
    txt = read(os.path.join(PACK, "adapters", "copilot", "prompts", name + ".prompt.md"))
    m = re.search(r"(?m)^description:\s*(.+?)\s*$", txt)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return first_paragraph(read(os.path.join(PACK, "commands", name, "SKILL.md"))) or "(no description)"


# ---------------------------------------------------------------- counts
def counts():
    install = read(os.path.join(PACK, "adapters", "INSTALL.md"))
    out = {}
    m = re.search(r"(?m)^counts:\s*\{([^}]*)\}", install)
    if m:
        for k, v in re.findall(r"(\w+)\s*:\s*(\d+)", m.group(1)):
            out[k] = int(v)
    return {
        "skills": len(skill_names()),
        "personas": out.get("lenses", 0),
        "knowledge": out.get("knowledge_docs", 0),
        "templates": out.get("templates", 0),
        "scripts": out.get("scripts", 0),
    }


# ---------------------------------------------------------------- foundations (knowledge docs)
def foundations(ed):
    ui_set = set(ed.get("uiStandards", []))
    groups_map = ed.get("knowledgeGroups", {})
    base = os.path.join(PACK, "knowledge")
    by_group = {}
    if os.path.isdir(base):
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".md"):
                continue
            name = fn[:-3]
            if name in ui_set or name == "FOUNDATION":
                continue
            txt = read(os.path.join(base, fn))
            title = first_heading(txt) or name.replace("-", " ").title()
            by_group.setdefault(groups_map.get(name, "Other"), []).append(
                {"name": name, "title": title, "summary": first_paragraph(txt),
                 "path": "../../pack/knowledge/%s.md" % name})
    order = ed.get("foundationGroupOrder", [])
    ordered = [g for g in order if g in by_group] + sorted(g for g in by_group if g not in order)
    return [{"group": g, "items": by_group[g]} for g in ordered]


# ---------------------------------------------------------------- architecture (of-record + adr + spec + design)
def _doc_items(paths, prefix):
    items = []
    for p in paths:
        txt = read(p)
        title = frontmatter_field(txt, "title") or first_heading(txt) or os.path.basename(p)
        summary = frontmatter_field(txt, "summary") or first_paragraph(txt)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        items.append({"title": title, "summary": summary, "path": prefix + rel})
    return sorted(items, key=lambda x: x["path"])


def _glob(dsub, pat):
    base = os.path.join(ROOT, *dsub.split("/"))
    out = []
    if os.path.isdir(base):
        for dp, _, fns in os.walk(base):
            for fn in fns:
                if re.match(pat, fn):
                    out.append(os.path.join(dp, fn))
    return out


def architecture():
    arch = [os.path.join(ROOT, "docs", f) for f in ("architecture.md", "architecture-dreaming.md")
            if os.path.isfile(os.path.join(ROOT, "docs", f))]
    groups = [
        {"group": "Architecture of record", "items": _doc_items(arch, "../../")},
        {"group": "Decisions (ADRs)", "items": _doc_items(_glob("docs/adr", r".*\.md$"), "../../")},
        {"group": "Specifications", "items": _doc_items(_glob("docs/specs", r".*\.md$"), "../../")},
        {"group": "Component designs", "items": _doc_items(_glob("docs/design", r".*\.md$"), "../../")},
    ]
    return [g for g in groups if g["items"]]


# ---------------------------------------------------------------- ui examples (mockups)
def ui_examples():
    base = os.path.join(ROOT, "docs", "mockups")
    items = []
    if os.path.isdir(base):
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".md"):
                continue
            txt = read(os.path.join(base, fn))
            title = frontmatter_field(txt, "title") or fn[:-3]
            summary = frontmatter_field(txt, "summary") or first_paragraph(txt)
            html = fn[:-3] + ".html"
            path = "../mockups/%s" % (html if os.path.isfile(os.path.join(base, html)) else fn)
            items.append({"title": title, "summary": summary, "path": path})
    return items


# ---------------------------------------------------------------- graph slice (from docs-index.js)
def personas():
    """The persona roster, DERIVED from the agent definitions rather than hand-listed.

    Veto strength is read out of each agent's own `description`, so the portal cannot claim a
    veto the shipped agent does not hold, and a new persona appears here the moment it exists.
    The same property the skills section relies on: complete by construction (V12 — an honest
    projection over a silent omission).
    """
    rows = []
    for sub, kind in (("claude-code", "Claude Code"), ("copilot", "Copilot")):
        adir = os.path.join(PACK, "adapters", sub, "agents")
        if not os.path.isdir(adir):
            continue
        for fn in sorted(os.listdir(adir)):
            if not fn.endswith(".md"):
                continue
            txt = read(os.path.join(adir, fn))
            name = frontmatter_field(txt, "name") or fn[:-3]
            desc = frontmatter_field(txt, "description") or ""
            low = desc.lower()
            veto = "hard" if "hard veto" in low else ("soft" if "soft veto" in low else "advisory")
            lens = frontmatter_field(txt, "knowledge") or ""
            lens = [d.strip() for d in lens.strip("[]").split(",") if d.strip()]
            rows.append({"name": name, "surface": kind, "veto": veto,
                         "desc": clip(desc), "lens": lens})
    rows.sort(key=lambda r: ({"hard": 0, "soft": 1, "advisory": 2}[r["veto"]], r["name"]))
    return rows


def graph_slice():
    raw = read(os.path.join(ROOT, "docs", "docs-index.js"))
    m = re.search(r"window\.DOCS_INDEX\s*=\s*(\{.*\});?\s*$", raw, re.S)
    if not m:
        return {"nodes": [], "edges": [], "types": []}
    try:
        idx = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"nodes": [], "edges": [], "types": []}
    arts = idx.get("artifacts", [])
    ids = {a.get("id") for a in arts if a.get("id")}
    nodes, edges = [], []
    for a in arts:
        aid = a.get("id")
        if not aid:
            continue
        nodes.append({"id": aid, "type": a.get("type", "doc"),
                      "title": a.get("title", aid), "summary": clip(a.get("summary", ""), 160)})
        for lk in a.get("links", []) or []:
            to = lk.get("to")
            if to in ids:
                edges.append({"from": aid, "to": to, "rel": lk.get("rel", "relates-to")})
    nodes.sort(key=lambda n: n["id"])
    edges.sort(key=lambda e: (e["from"], e["to"], e["rel"]))
    return {"nodes": nodes, "edges": edges, "types": sorted({n["type"] for n in nodes})}


# ---------------------------------------------------------------- assemble
def build():
    if not os.path.isfile(EDITORIAL):
        print("error: editorial source not found:", EDITORIAL, file=sys.stderr)
        return None, []
    ed = json.loads(read(EDITORIAL))
    names = skill_names()
    meta_by_name = ed.get("skillMeta", {})
    missing_meta = [n for n in names if n not in meta_by_name]

    by_group = {}
    for name in names:
        m = meta_by_name.get(name, {})
        by_group.setdefault(m.get("group", "Utilities & lenses"), []).append({
            "cmd": "/" + name, "desc": skill_description(name),
            "when": m.get("when", "-"), "produces": m.get("produces", "-"), "handoff": m.get("handoff", "-")})
    order = ed.get("groupOrder", [])
    og = [g for g in order if g in by_group] + sorted(g for g in by_group if g not in order)
    skills = [{"group": g, "items": by_group[g]} for g in og]

    # Section order is the reading order: what it is, what it does, the skills that do it,
    # then HOW those skills are run — the persona panel and the per-turn loop — before the
    # reference layers. Numbers are derived so inserting a section cannot leave a stale label.
    titles = [
        ("start", "Getting Started"),
        ("caps", "Capabilities"),
        ("skills", "The %d Skills" % len(names)),
        ("agents", "Multi-Agent Collaboration"),
        ("loop", "The Prompt Loop"),
        ("foundations", "Foundations"),
        ("ui", "UI & Design"),
        ("architecture", "Architecture"),
        ("systems", "Systems"),
        ("graph", "Graph"),
        ("ref", "Reference"),
    ]
    sections = [{"id": sid, "n": str(i), "title": t}
                for i, (sid, t) in enumerate(titles, start=1)]

    ui = dict(ed.get("ui", {}))
    ui["examplesIntro"] = ed.get("uiExamplesIntro", "")
    ui["examples"] = ui_examples()

    data = {
        "meta": {"counts": counts(), "whatIs": ed.get("whatIs", ""),
                 "skillCount": len(names), "precisionNote": ed.get("precisionNote", "")},
        "sections": sections,
        "gettingStarted": ed.get("gettingStarted", []),
        "capabilities": ed.get("capabilities", []),
        "skills": skills,
        "foundations": {"intro": ed.get("foundationsIntro", ""), "groups": foundations(ed)},
        "ui": ui,
        "architecture": {"intro": ed.get("architectureIntro", ""), "groups": architecture()},
        "collaboration": dict(ed.get("collaboration", {}), personas=personas()),
        "promptLoop": ed.get("promptLoop", {}),
        "systems": ed.get("systems", []),
        "graph": graph_slice(),
        "surfaces": ed.get("surfaces", []),
    }
    return data, missing_meta


def main():
    check = "--check" in sys.argv
    data, missing = build()
    if data is None:
        return 2
    payload = "window.PORTAL_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    out_path = os.path.join(OUT_DIR, "portal-data.js")

    if check:
        if read(out_path) != payload:
            print("DRIFT: docs/portal/portal-data.js is stale - re-run tools/build-docs-portal.py", file=sys.stderr)
            return 1
        if missing:
            print("WARNING: skills without editorial metadata: " + ", ".join(missing), file=sys.stderr)
        print("portal-data.js is current (%d skills, %d graph nodes)." % (
            data["meta"]["skillCount"], len(data["graph"]["nodes"])))
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
    c = data["meta"]["counts"]
    fcount = sum(len(g["items"]) for g in data["foundations"]["groups"])
    acount = sum(len(g["items"]) for g in data["architecture"]["groups"])
    print("docs/portal/portal-data.js: %d skills, %d foundations, %d architecture docs, %d graph nodes/%d edges" % (
        c["skills"], fcount, acount, len(data["graph"]["nodes"]), len(data["graph"]["edges"])))
    if missing:
        print("  note: skills without editorial metadata: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
