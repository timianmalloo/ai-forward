#!/usr/bin/env python3
"""docs-graph.py — the AI-Forward Pack docs script bundle (knowledge-visualization.md V18).

Deterministic mechanics for the knowledge graph, so skills invoke ONE tool instead of
generating ad-hoc scripts at prompt time. Python 3.8+, stdlib only (a built-in parser
covers the V2 frontmatter subset; no PyYAML needed).

Subcommands
  inventory   Scan the graph: artifacts, missing/invalid frontmatter, bad links,
              unregistered rels, orphans, stale (V13), flagged (V16), index drift. JSON out.
  derive      Full derivation sweep: frontmatter -> docs/docs-index.js (V2/V10).
  validate    inventory + nonzero exit on findings (CI-able).
  freshness   The freshness gate's time-based half: stale + flagged + orphans; exit code.
  flag        V16 propagation: --changed <id> --reason "..." flags inbound neighbors.
  clear-flag  Clear a review-suggested flag (--id <artifact> --by <changed-id>) and
              optionally --bump-review <days>.
  stub        Scaffold a new artifact file with schema-correct frontmatter.
  snapshot    Append a graph-health record to docs/health-history.jsonl (governance trend).
  rollup      Aggregate per-artifact markdown tables under a heading (e.g. the designs'
              STRIDE / privacy tables) into one register, each row prefixed with its
              source artifact — paste-ready for the threat-model / privacy-review docs.

Conventions
  --root defaults to docs/. Excluded from the graph: docs/ai-forward-pack/**, docs/_site/**,
  docs/index.html, docs/docs-index.js, non-.md files. Frontmatter is the record; this tool
  never invents metadata — files without frontmatter are reported, not silently indexed.
"""
import argparse, json, os, re, sys, datetime

REL_REGISTRY = ["implements","refines","depends-on","supersedes","tested-by","documents","uses-term","relates-to"]
TYPES = ["knowledge","glossary","spec","architecture","adr","design","investigation","proof-pack","decision-note","threat-model","privacy-review","api","source","doc","index"]
REQUIRED = ["id","title","type","status","summary"]
EXCLUDE_DIRS = {"ai-forward-pack","_site","node_modules",".git"}
TODAY = datetime.date.today().isoformat()

# ---------- minimal YAML-subset parser (the V2 frontmatter schema only) ----------
def parse_scalar(v):
    v = v.strip()
    if v == "" or v == "~": return ""
    if v.startswith('"') and v.endswith('"') and len(v) >= 2: return v[1:-1]
    if v.startswith("'") and v.endswith("'") and len(v) >= 2: return v[1:-1]
    if v == "[]": return []
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [parse_scalar(x) for x in split_flow(inner)] if inner else []
    if v.startswith("{") and v.endswith("}"): return parse_flow_map(v)
    return v

def split_flow(s):
    out, depth, cur, q = [], 0, "", None
    for c in s:
        if q:
            cur += c
            if c == q: q = None
            continue
        if c in "\"'": q = c; cur += c; continue
        if c in "[{": depth += 1
        if c in "]}": depth -= 1
        if c == "," and depth == 0: out.append(cur); cur = ""; continue
        cur += c
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out]

def parse_flow_map(v):
    inner = v.strip()[1:-1]
    d = {}
    for part in split_flow(inner):
        if ":" not in part: continue
        k, val = part.split(":", 1)
        d[k.strip()] = parse_scalar(val)
    return d

def parse_frontmatter(text):
    """Returns (dict, error). Supports: scalars, '>-' folded blocks, '- item' lists,
    '- { k: v }' lists, flow lists/maps. That is the whole V2 schema."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m: return None, "no frontmatter"
    lines, fm, i = m.group(1).split("\n"), {}, 0
    try:
        while i < len(lines):
            ln = lines[i]
            if not ln.strip() or ln.lstrip().startswith("#"): i += 1; continue
            km = re.match(r"^([A-Za-z][\w-]*):(.*)$", ln)
            if not km: return None, f"unparseable line {i+1}: {ln.strip()[:60]}"
            key, rest = km.group(1), km.group(2).strip()
            if rest in (">-", ">", "|", "|-"):                       # folded/literal block
                i += 1; buf = []
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    buf.append(lines[i].strip()); i += 1
                fm[key] = " ".join(b for b in buf if b)
                continue
            if rest == "":                                            # block list (or empty)
                items = []; i += 1
                while i < len(lines) and re.match(r"^\s+-\s", lines[i]):
                    items.append(parse_scalar(re.sub(r"^\s+-\s", "", lines[i]))); i += 1
                fm[key] = items
                continue
            fm[key] = parse_scalar(rest); i += 1
        return fm, None
    except Exception as e:
        return None, f"frontmatter parse error: {e}"

# ---------- scanning ----------
def scan(root):
    arts, problems = [], []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in sorted(dns) if d not in EXCLUDE_DIRS]
        for f in sorted(fns):
            if not f.endswith(".md"): continue
            path = os.path.join(dp, f)
            rel = path.replace("\\", "/")
            try: text = open(path, encoding="utf-8").read()
            except OSError as e: problems.append({"file": rel, "problem": f"unreadable: {e}"}); continue
            fm, err = parse_frontmatter(text)
            if err: problems.append({"file": rel, "problem": err}); continue
            missing = [k for k in REQUIRED if not fm.get(k)]
            if missing: problems.append({"file": rel, "problem": f"missing required keys: {','.join(missing)}"})
            if fm.get("type") and fm["type"] not in TYPES:
                problems.append({"file": rel, "problem": f"unknown type: {fm['type']}"})
            links = fm.get("links") or []
            links = [l for l in links if isinstance(l, dict)]
            fm["links"] = [{"to": l.get("to",""), "rel": l.get("rel","")} for l in links]
            fm["_path"] = rel
            fm["_diagrams"] = [{"kind": sniff_kind(code), "title": (title or "").strip(), "mermaid": code.strip()}
                               for title, code in re.findall(r"(?:^|\n)(?:#+\s*(.*)\n+)?```mermaid\n(.*?)```", text, re.S)]
            arts.append(fm)
    return arts, problems

def sniff_kind(code):
    head = code.strip().split(None, 1)[0].lower() if code.strip() else ""
    return {"sequencediagram":"sequence","classdiagram":"class","statediagram":"state",
            "statediagram-v2":"state","flowchart":"flowchart","graph":"flowchart",
            "erdiagram":"er","timeline":"timeline"}.get(head, "c4" if head.startswith("c4") else head or "diagram")

def analyze(arts, problems):
    by_id, dup = {}, []
    for a in arts:
        if a.get("id") in by_id: dup.append(a["id"])
        by_id[a.get("id")] = a
    inbound = {}
    for a in arts:
        for l in a["links"]:
            if l["rel"] not in REL_REGISTRY:
                problems.append({"file": a["_path"], "problem": f"unregistered rel: {l['rel']} (V14)"})
            if l["to"] and l["to"] not in by_id:
                problems.append({"file": a["_path"], "problem": f"dangling link target: {l['to']}"})
            inbound.setdefault(l["to"], []).append({"from": a["id"], "rel": l["rel"]})
    for d in dup: problems.append({"file": by_id[d]["_path"], "problem": f"duplicate id: {d}"})
    frozen = {"superseded", "resolved"}
    stale   = [a["id"] for a in arts if a.get("review-by") and str(a["review-by"]) < TODAY and a.get("status") not in frozen]
    flagged = [a["id"] for a in arts if a.get("review-suggested")]
    orphans = [a["id"] for a in arts if not a["links"] and a.get("id") not in inbound]
    return by_id, inbound, stale, flagged, orphans

# ---------- subcommands ----------
def cmd_inventory(args, exit_on_findings=False):
    arts, problems = scan(args.root)
    by_id, inbound, stale, flagged, orphans = analyze(arts, problems)
    drift = index_drift(args, arts)
    report = {"root": args.root, "today": TODAY, "artifacts": len(arts),
              "problems": problems, "stale": stale, "flagged": flagged,
              "orphans": orphans, "index_drift": drift,
              "by_type": count_by(arts, "type")}
    print(json.dumps(report, indent=2))
    findings = bool(problems or stale or flagged or orphans or drift)
    return 1 if (exit_on_findings and findings) else 0

def count_by(arts, key):
    d = {}
    for a in arts: d[a.get(key, "?")] = d.get(a.get(key, "?"), 0) + 1
    return d

def index_drift(args, arts):
    """Compare derived-from-frontmatter against the existing docs-index.js (ids + shallow fields)."""
    p = args.out if hasattr(args, "out") and args.out else os.path.join(args.root, "docs-index.js")
    if not os.path.exists(p): return ["docs-index.js missing"]
    try:
        m = re.search(r"window\.DOCS_INDEX\s*=\s*(\{.*\});?\s*$", open(p, encoding="utf-8").read(), re.S)
        idx = json.loads(m.group(1)) if m else None
    except Exception:
        return ["docs-index.js unparseable as JSON (regenerate with `derive`)"]
    if not idx: return ["docs-index.js unparseable"]
    have = {e.get("id"): e for e in idx.get("artifacts", [])}
    want = {a.get("id"): a for a in arts}
    drift = [f"in index, file gone: {i}" for i in have if i not in want]
    drift += [f"file not in index: {i}" for i in want if i not in have]
    for i in set(have) & set(want):
        for k_idx, k_fm in [("status","status"), ("owner","owner"), ("reviewBy","review-by"), ("summary","summary")]:
            if str(have[i].get(k_idx) or "") != str(want[i].get(k_fm) or ""):
                drift.append(f"{i}: index.{k_idx} != frontmatter.{k_fm}")
    return drift

def cmd_derive(args):
    arts, problems = scan(args.root)
    analyze(arts, problems)   # populate problems (reported to stderr, not blocking)
    entries = []
    for a in sorted(arts, key=lambda x: (x.get("type",""), x.get("id",""))):
        entries.append({"id": a.get("id"), "path": a["_path"], "title": a.get("title"),
                        "type": a.get("type"), "status": a.get("status"),
                        "owner": a.get("owner",""), "phase": str(a.get("phase","")),
                        "reviewBy": str(a.get("review-by","")),
                        "reviewSuggested": a.get("review-suggested") or [],
                        "summary": a.get("summary",""), "tags": a.get("tags") or [],
                        "links": a["links"], "diagrams": a["_diagrams"]})
    out = {"project": args.project or os.path.basename(os.path.abspath(os.path.join(args.root, ".."))),
           "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "generator": args.generator, "artifacts": entries}
    body = ("// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit"
            " (frontmatter wins; see knowledge-visualization.md V2/V18).\n"
            "window.DOCS_INDEX = " + json.dumps(out, indent=2, ensure_ascii=False) + ";\n")
    dst = args.out or os.path.join(args.root, "docs-index.js")
    open(dst, "w", encoding="utf-8").write(body)
    for p in problems: print(f"finding: {p['file']}: {p['problem']}", file=sys.stderr)
    print(f"derived {len(entries)} entries -> {dst}" + (f" ({len(problems)} findings on stderr)" if problems else ""))
    return 0

def cmd_freshness(args):
    arts, problems = scan(args.root)
    _, _, stale, flagged, orphans = analyze(arts, problems)
    for i in stale:   print(f"STALE   (V13): {i}")
    for i in flagged: print(f"FLAGGED (V16): {i}")
    for i in orphans: print(f"ORPHAN  (V10): {i}")
    bad = [p for p in problems if "unreadable" in p["problem"] or "no frontmatter" in p["problem"] or "parse" in p["problem"]]
    for p in bad: print(f"INVALID      : {p['file']}: {p['problem']}")
    n = len(stale) + len(flagged) + len(orphans) + len(bad)
    print(f"freshness: {n} finding(s)")
    return 1 if (n and args.gate == "fail") else 0

# ---- V16 flag mechanics: targeted textual frontmatter edits (preserve the file) ----
def edit_frontmatter_flags(path, mutate):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^(---\r?\n)(.*?)(\r?\n---\r?\n)(.*)$", text, re.S)
    if not m: raise SystemExit(f"{path}: no frontmatter to edit")
    head = m.group(2)
    fm, err = parse_frontmatter(text)
    if err: raise SystemExit(f"{path}: {err}")
    flags = [f for f in (fm.get("review-suggested") or []) if isinstance(f, dict)]
    flags, bump = mutate(flags, fm)
    block = "review-suggested: []" if not flags else \
        "review-suggested:\n" + "\n".join(
            '  - { by: %s, on: %s, reason: "%s" }' % (f.get("by",""), f.get("on",""), str(f.get("reason","")).replace('"', "'"))
            for f in flags)
    if re.search(r"^review-suggested:.*$(?:\n\s+-\s.*$)*", head, re.M):
        head = re.sub(r"^review-suggested:.*$(?:\n\s+-\s.*$)*", block, head, count=1, flags=re.M)
    else:
        head = head.rstrip("\n") + "\n" + block
    if bump:
        new_date = (datetime.date.today() + datetime.timedelta(days=bump)).isoformat()
        if re.search(r"^review-by:.*$", head, re.M):
            head = re.sub(r"^review-by:.*$", f"review-by: {new_date}", head, count=1, flags=re.M)
        else:
            head += f"\nreview-by: {new_date}"
    open(path, "w", encoding="utf-8").write(m.group(1) + head + m.group(3) + m.group(4))

def cmd_flag(args):
    arts, problems = scan(args.root)
    by_id, inbound, *_ = analyze(arts, problems)
    if args.changed not in by_id: raise SystemExit(f"unknown artifact id: {args.changed}")
    nbrs = inbound.get(args.changed, [])
    if not nbrs: print(f"no inbound neighbors of {args.changed}; nothing to flag"); return 0
    for n in nbrs:
        a = by_id[n["from"]]
        def add(flags, _fm, _by=args.changed, _r=args.reason):
            if any(f.get("by") == _by for f in flags): return flags, 0
            flags.append({"by": _by, "on": TODAY, "reason": _r}); return flags, 0
        edit_frontmatter_flags(a["_path"], add)
        print(f"flagged {a['id']} ({n['rel']} -> {args.changed})")
    return cmd_derive(args)

def cmd_clear_flag(args):
    arts, problems = scan(args.root)
    by_id, *_ = analyze(arts, problems)
    if args.id not in by_id: raise SystemExit(f"unknown artifact id: {args.id}")
    def rm(flags, _fm):
        kept = [f for f in flags if f.get("by") != args.by]
        if len(kept) == len(flags): print(f"warning: no flag by {args.by} on {args.id}", file=sys.stderr)
        return kept, (args.bump_review or 0)
    edit_frontmatter_flags(by_id[args.id]["_path"], rm)
    print(f"cleared flag by {args.by} on {args.id}" + (f"; review-by +{args.bump_review}d" if args.bump_review else ""))
    return cmd_derive(args)

def cmd_rollup(args):
    """Extract the markdown table under --heading from every matching artifact and merge."""
    arts, problems = scan(args.root)
    if args.type: arts=[a for a in arts if a.get("type")==args.type]
    header, out = None, []
    for a in sorted(arts, key=lambda x: x.get("id","")):
        text = open(a["_path"], encoding="utf-8").read()
        m = re.search(r"^#{2,3}\s+" + re.escape(args.heading) + r"\s*$([\s\S]*?)(?=^#{1,3}\s|\Z)", text, re.M)
        if not m: continue
        rows = [ln for ln in m.group(1).split("\n") if ln.strip().startswith("|")]
        if len(rows) < 3: continue            # header + separator + at least one data row
        if header is None: header = rows[0], rows[1]
        for r in rows[2:]:
            if r.strip().strip("|").strip(): out.append("| [" + a.get("id","?") + "](" +
                os.path.relpath(a["_path"], args.root).replace(os.sep,"/") + ") " + r.strip())
    if header is None:
        print(f"no '{args.heading}' tables found", file=sys.stderr); return 1
    print("| source " + header[0].strip())
    print("|---" + header[1].strip())
    for r in out: print(r)
    print(f"\n<!-- rolled up from {len(set(r.split(']')[0] for r in out))} artifact(s) by docs-graph.py rollup on {TODAY} -->")
    return 0

def cmd_snapshot(args):
    arts, problems = scan(args.root)
    _, _, stale, flagged, orphans = analyze(arts, problems)
    rec = {"on": TODAY, "artifacts": len(arts), "by_type": count_by(arts, "type"),
           "orphans": len(orphans), "stale": len(stale), "flagged": len(flagged),
           "notes": count_by(arts, "type").get("decision-note", 0), "problems": len(problems)}
    dst = os.path.join(args.root, "health-history.jsonl")
    with open(dst, "a", encoding="utf-8") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec)); print(f"appended -> {dst}")
    return 0

def cmd_stub(args):
    links = "\n".join("  - { to: %s, rel: %s }" % tuple(l.split(":", 1)) for l in (args.link or [])) or "  []"
    links_block = "links:\n" + links if links.strip() != "[]" else "links: []"
    fm = f"""---
id: {args.id}
title: "{args.title}"
type: {args.type}
status: draft
owner: "{args.owner}"
phase: "{args.phase or ''}"
tags: [{', '.join(args.tag or [])}]
{links_block}
review-by: {args.review_by or ''}
review-suggested: []
summary: >-
  {args.summary or 'TODO — real 1-3 sentence summary (V2).'}
---

# {args.title}
"""
    os.makedirs(os.path.dirname(args.file), exist_ok=True)
    if os.path.exists(args.file) and not args.force: raise SystemExit(f"{args.file} exists (use --force)")
    open(args.file, "w", encoding="utf-8").write(fm)
    print(f"stubbed {args.file}")
    return 0

def main():
    ap = argparse.ArgumentParser(prog="docs-graph.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="docs", help="docs root (default: docs)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory")
    d = sub.add_parser("derive"); v = sub.add_parser("validate"); fr = sub.add_parser("freshness")
    for x in (d,):
        pass
    for x in (ap,):
        pass
    d.add_argument("--out", default=None); d.add_argument("--project", default=None)
    d.add_argument("--generator", default="docs-graph.py derive")
    fr.add_argument("--gate", choices=["warn","fail"], default="warn")
    fl = sub.add_parser("flag"); fl.add_argument("--changed", required=True); fl.add_argument("--reason", required=True)
    fl.add_argument("--out", default=None); fl.add_argument("--project", default=None); fl.add_argument("--generator", default="docs-graph.py flag")
    cf = sub.add_parser("clear-flag"); cf.add_argument("--id", required=True); cf.add_argument("--by", required=True)
    cf.add_argument("--bump-review", type=int, default=0)
    cf.add_argument("--out", default=None); cf.add_argument("--project", default=None); cf.add_argument("--generator", default="docs-graph.py clear-flag")
    st = sub.add_parser("stub")
    st.add_argument("--file", required=True); st.add_argument("--id", required=True); st.add_argument("--title", required=True)
    st.add_argument("--type", required=True, choices=TYPES); st.add_argument("--owner", default="@owner")
    st.add_argument("--phase", default=""); st.add_argument("--tag", action="append"); st.add_argument("--link", action="append",
        help="to:rel (repeatable), e.g. --link spec-checkout:implements")
    st.add_argument("--review-by", default=""); st.add_argument("--summary", default=""); st.add_argument("--force", action="store_true")
    sub.add_parser("snapshot")
    ru = sub.add_parser("rollup"); ru.add_argument("--heading", required=True)
    ru.add_argument("--type", default=None, help="restrict to one artifact type (e.g. design)")
    args = ap.parse_args()
    if args.cmd == "inventory":  sys.exit(cmd_inventory(args))
    if args.cmd == "validate":   sys.exit(cmd_inventory(args, exit_on_findings=True))
    if args.cmd == "derive":     sys.exit(cmd_derive(args))
    if args.cmd == "freshness":  sys.exit(cmd_freshness(args))
    if args.cmd == "flag":       sys.exit(cmd_flag(args))
    if args.cmd == "clear-flag": sys.exit(cmd_clear_flag(args))
    if args.cmd == "stub":       sys.exit(cmd_stub(args))
    if args.cmd == "snapshot":   sys.exit(cmd_snapshot(args))
    if args.cmd == "rollup":     sys.exit(cmd_rollup(args))

if __name__ == "__main__":
    main()
