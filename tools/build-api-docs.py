#!/usr/bin/env python3
"""build-api-docs.py — generate the API reference from the source (AI-Forward, repo dev-tooling).

The pack's public surface is the **deployed script bundle**: `pack/scripts/*.py`, which lands in
every consuming repo as `docs/ai-forward-pack/scripts/`. A consuming repo calls those CLIs and
imports those functions; everything in `tools/` is repo-local build tooling and is deliberately
NOT part of the surface (it is never deployed).

Why generated rather than written: an API reference maintained by hand is a second source of
truth for a contract that already has one, and it rots silently — the bundle's own `_meta.json`
still claimed 17 skills and 24 knowledge docs months after both numbers had moved. Everything
here is extracted with `ast` from the code itself:

  * the module docstring                       -> the module summary
  * argparse `add_parser` / `add_argument`     -> the CLI contract (subcommands, flags, help)
  * public `def` signatures + docstrings       -> the function reference

**Nothing is invented.** A public function with no docstring is emitted as a recorded coverage
gap, never as fabricated prose (documentation-bundle template: "a public member with no doc
comment is a recorded coverage gap"). The coverage percentage is computed, not asserted.

Usage
  build-api-docs.py                # write docs/api/*.md + return coverage
  build-api-docs.py --check        # fail (exit 1) if the committed output is stale
Stdlib only.
"""
import argparse
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pack", "scripts")
OUT = os.path.join(ROOT, "docs", "api")

# Deployed to every consuming repo, so this is the contract other repos call.
SURFACE_NOTE = ("Deployed to consuming repos as `docs/ai-forward-pack/scripts/`. "
                "Everything under `tools/` is repo-local build tooling and is not part of "
                "this surface.")


def first_line(text):
    for line in (text or "").strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def signature(fn):
    """Render a def's parameter list, defaults collapsed to `=…` to stay stable across edits."""
    a = fn.args
    parts = []
    pos = list(a.posonlyargs) + list(a.args)
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for arg, default in zip(pos, defaults):
        parts.append(arg.arg + ("=…" if default is not None else ""))
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    for arg, default in zip(a.kwonlyargs, a.kw_defaults):
        parts.append(arg.arg + ("=…" if default is not None else ""))
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    return "%s(%s)" % (fn.name, ", ".join(parts))


def _str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def cli_contract(tree):
    """Subcommands and flags, read out of the argparse calls themselves.

    Reading the parser rather than `--help` output means the reference cannot drift from the
    code, and it works without executing the script (which would need its dependencies present).
    """
    subs, flags = [], []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr == "add_parser" and node.args:
            name = _str(node.args[0])
            if name:
                help_kw = next((_str(k.value) for k in node.keywords if k.arg == "help"), "")
                subs.append((name, help_kw or ""))
        elif attr == "add_argument" and node.args:
            names = [n for n in (_str(a) for a in node.args) if n]
            opts = [n for n in names if n.startswith("-")]
            if not opts:
                continue
            help_kw = next((_str(k.value) for k in node.keywords if k.arg == "help"), "")
            flags.append((", ".join(f"`{o}`" for o in opts), help_kw or ""))
    # Deterministic output: same tree in, same bytes out, so --check is meaningful.
    seen = set()
    subs = [s for s in subs if not (s[0] in seen or seen.add(s[0]))]
    seen = set()
    flags = [f for f in flags if not (f[0] in seen or seen.add(f[0]))]
    return sorted(subs), sorted(flags)


def public_functions(tree):
    """Module-level defs that are part of the surface: not _private, not a CLI shim."""
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_") or node.name in ("main",):
            continue
        out.append((node.name, signature(node), ast.get_docstring(node) or ""))
    return out


def public_classes(tree):
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            out.append((node.name, ast.get_docstring(node) or ""))
    return out


def render(name, tree, source_rel):
    subs, flags = cli_contract(tree)
    fns = public_functions(tree)
    classes = public_classes(tree)
    moddoc = ast.get_docstring(tree) or ""
    documented = sum(1 for _, _, d in fns if d.strip())
    gaps = [n for n, _, d in fns if not d.strip()]

    slug = name[:-3]
    L = []
    L.append("---")
    L.append(f"id: api-{slug}")
    L.append(f'title: "API — {slug}.py"')
    L.append("type: api")
    L.append("status: accepted")
    L.append('owner: "@timianmalloo"')
    L.append("tags: [api, scripts, generated]")
    L.append("links:")
    L.append("  - { to: api-index, rel: refines }")
    L.append('review-by: "2027-03-03"')
    L.append("summary: >-")
    summary = first_line(moddoc) or f"{slug}.py — no module docstring (recorded gap)."
    L.append("  " + summary.replace("\n", " ")[:300])
    L.append("---")
    L.append("")
    L.append(f"# `{slug}.py`")
    L.append("")
    L.append(f"*Generated from `{source_rel}` by `tools/build-api-docs.py`. Do not edit by hand — "
             "edit the source docstrings and regenerate.*")
    L.append("")
    if moddoc:
        L.append("## Summary")
        L.append("")
        L.append("```text")
        L.extend(moddoc.strip().splitlines())
        L.append("```")
        L.append("")
    else:
        L.append("## Summary")
        L.append("")
        L.append("**Coverage gap** — this module has no docstring. Not fabricated here.")
        L.append("")

    if subs:
        L.append("## CLI — subcommands")
        L.append("")
        L.append("| Subcommand | Help |")
        L.append("|---|---|")
        for sname, shelp in subs:
            L.append(f"| `{sname}` | {shelp or '_(no help text — coverage gap)_'} |")
        L.append("")
    if flags:
        L.append("## CLI — options")
        L.append("")
        L.append("| Option | Help |")
        L.append("|---|---|")
        for fname, fhelp in flags:
            L.append(f"| {fname} | {fhelp or '_(no help text — coverage gap)_'} |")
        L.append("")

    if classes:
        L.append("## Types")
        L.append("")
        for cname, cdoc in classes:
            L.append(f"### `{cname}`")
            L.append("")
            L.append(first_line(cdoc) or "_(no docstring — coverage gap)_")
            L.append("")

    if fns:
        L.append("## Functions")
        L.append("")
        for fname, sig, doc in fns:
            L.append(f"### `{sig}`")
            L.append("")
            if doc.strip():
                L.append(doc.strip())
            else:
                L.append("**Coverage gap** — no docstring in the source.")
            L.append("")

    L.append("## Coverage")
    L.append("")
    pct = int(round(100.0 * documented / len(fns))) if fns else 100
    L.append(f"- Public functions: **{len(fns)}** · documented: **{documented}** (**{pct}%**)")
    if gaps:
        L.append(f"- Undocumented (recorded, not invented): {', '.join('`%s`' % g for g in gaps)}")
    L.append("")
    return "\n".join(L) + "\n", len(fns), documented


def index_page(rows, totals):
    fns, documented = totals
    pct = int(round(100.0 * documented / fns)) if fns else 100
    L = ["---", "id: api-index", 'title: "API reference — the deployed script bundle"',
         "type: api", "status: accepted", 'owner: "@timianmalloo"',
         "tags: [api, scripts, generated, index]", "links:",
         "  - { to: architecture, rel: documents }", 'review-by: "2027-03-03"',
         "summary: >-",
         "  Generated API reference for the pack's public surface — the deployed script bundle."
         f" {fns} public functions across {len(rows)} modules, {pct}% carrying a docstring.",
         "---", "",
         "# API reference — the deployed script bundle", "",
         f"*Generated by `tools/build-api-docs.py` from `pack/scripts/`. {SURFACE_NOTE}*", "",
         "Prose is extracted from the code's own docstrings and argparse help. A public member",
         "with no docstring is listed as a **coverage gap** rather than described from guesswork.",
         "", "## Modules", "",
         "| Module | Public fns | Documented | CLI | Summary |", "|---|---:|---:|---:|---|"]
    for r in rows:
        L.append("| [`%s`](%s.md) | %d | %d | %s | %s |"
                 % (r["slug"] + ".py", r["slug"], r["fns"], r["documented"],
                    r["subs"] or "—", r["summary"][:110].replace("|", "\\|")))
    L.append("")
    L.append(f"**Total** — {fns} public functions across {len(rows)} modules, "
             f"**{documented} documented ({pct}%)**.")
    L.append("")
    return "\n".join(L) + "\n"


def build():
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".py"))
    pages, rows, tot_fns, tot_doc = {}, [], 0, 0
    for name in files:
        path = os.path.join(SRC, name)
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=name)
        rel = "pack/scripts/" + name
        text, fns, documented = render(name, tree, rel)
        pages[name[:-3] + ".md"] = text
        subs, _ = cli_contract(tree)
        rows.append({"slug": name[:-3], "fns": fns, "documented": documented,
                     "subs": len(subs), "summary": first_line(ast.get_docstring(tree) or "")})
        tot_fns += fns
        tot_doc += documented
    pages["index.md"] = index_page(rows, (tot_fns, tot_doc))
    return pages, tot_fns, tot_doc


def main():
    ap = argparse.ArgumentParser(description="Generate the API reference from pack/scripts/.")
    ap.add_argument("--check", action="store_true",
                    help="fail when the committed output differs from a fresh generation")
    args = ap.parse_args()

    pages, fns, documented = build()
    pct = int(round(100.0 * documented / fns)) if fns else 100

    if args.check:
        stale = []
        for fname, text in sorted(pages.items()):
            path = os.path.join(OUT, fname)
            if not os.path.isfile(path):
                stale.append(fname + " (missing)")
                continue
            with open(path, encoding="utf-8", newline="") as fh:
                if fh.read().replace("\r\n", "\n") != text:
                    stale.append(fname)
        extra = [f for f in (os.listdir(OUT) if os.path.isdir(OUT) else []) if f not in pages]
        if stale or extra:
            print("DRIFT: docs/api is stale - re-run tools/build-api-docs.py")
            for f in stale:
                print("  stale:  " + f)
            for f in extra:
                print("  orphan: " + f)
            return 1
        print(f"docs/api current: {len(pages) - 1} modules, {fns} public fns, {pct}% documented")
        return 0

    os.makedirs(OUT, exist_ok=True)
    for fname, text in sorted(pages.items()):
        with open(os.path.join(OUT, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    for fname in list(os.listdir(OUT)):
        if fname not in pages:
            os.remove(os.path.join(OUT, fname))
    print(f"docs/api: {len(pages) - 1} modules, {fns} public fns, {documented} documented ({pct}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
