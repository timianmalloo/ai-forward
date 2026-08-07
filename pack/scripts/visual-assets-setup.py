#!/usr/bin/env python3
"""visual-assets-setup.py - wire up a generation backend for UI visual assets (AI-Forward).

`ui-visual-assets.md` (VA1-VA18) governs *whether and how* imagery, personas and motion
may be generated for a UI. This script is the *mechanism*: it reports which generation
backends a repo can actually reach, scaffolds the asset directory and manifest, and keeps
the credential and hygiene rules that VA9/VA11 depend on. Stdlib only; lives in the script
bundle (deployed to docs/ai-forward-pack/scripts/).

It deliberately does NOT generate anything and NEVER writes a credential. Generation runs
through the `/visualize` skill against whichever backend is configured; secrets live in the
environment or the agent host's own MCP configuration, never in the repository.

Modes
  --check      what is configured, what is missing, and exactly how to fix it
  --init       scaffold docs/assets/, the DESIGN.md assets manifest, and .gitignore hygiene
  --backends   print the backend capability matrix and exit
  --dry-run    with --init: print what would change, write nothing
  --json       machine-readable output for --check

Exit codes: 0 fine, 1 nothing usable is configured (with --check), 2 a hygiene problem was
found that needs a human (a credential appears to be committed).

Usage:
  visual-assets-setup.py --check [--json]
  visual-assets-setup.py --init [--dry-run]
  visual-assets-setup.py --backends
"""
import argparse
import json
import os
import re
import sys

# --- The backend registry ------------------------------------------------------
# A backend is described by what it CAN DO, not by which vendor it is - so the
# capability contract stays substitutable (VA1). `env` lists the environment
# variables that indicate it is configured; `any_of` means one of them suffices.
BACKENDS = {
    "higgsfield": {
        "label": "Higgsfield",
        "kind": "mcp",
        "env": ["HIGGSFIELD_API_KEY", "HIGGSFIELD_SECRET"],
        "any_of": False,          # both are required
        "capabilities": ["text-to-image", "image-to-image", "image-to-video",
                         "talking-head", "character-reference", "style-presets",
                         "motion-presets"],
        "notes": (
            "Exposed as an MCP server, so the agent host holds the credentials rather than "
            "the repo. Style presets skew fashion/lifestyle; the product-appropriate subset "
            "is small (VA3). Results are retained ~7 days, which is why VA4 requires "
            "download-and-commit rather than linking."),
        "howto": (
            "Configure the Higgsfield MCP server in your agent host (Claude Code: .mcp.json "
            "or the user config; Copilot CLI: the MCP settings), supplying HIGGSFIELD_API_KEY "
            "and HIGGSFIELD_SECRET from platform.higgsfield.ai. Do not put them in the repo."),
    },
    "google": {
        "label": "Google (Gemini image / Veo video)",
        "kind": "sdk",
        "env": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "any_of": True,           # either works; GOOGLE_API_KEY takes precedence
        "vertex_env": ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"],
        "capabilities": ["text-to-image", "image-to-image", "text-to-video",
                         "image-to-video", "reference-to-video"],
        "models": {
            "image-fast": "gemini-3.1-flash-lite-image",
            "image": "gemini-3.1-flash-image",
            "image-pro": "gemini-3-pro-image",
            "video-async": "veo-3.1-generate-preview",
            "video-sync": "gemini-omni-flash-preview",
        },
        "notes": (
            "A CONSUMER Google AI Pro/Ultra subscription does NOT grant API access - the "
            "consumer app and the developer API are separate billing relationships, and "
            "image and video generation are NOT on the API free tier at all. You need an AI "
            "Studio key tied to a Cloud project with active billing (VA19). There is no "
            "official Google MCP server for generation; call the SDK directly. All generated "
            "images carry an invisible SynthID watermark. Imagen (imagen-4.0-generate-001) "
            "is deprecated - do not build new work on it."),
        "howto": (
            "Create an API key at aistudio.google.com/apikey (it binds to a Cloud project "
            "with billing enabled) and export it as GOOGLE_API_KEY. Install the SDK: "
            "`pip install google-genai` or `npm i @google/genai`. For Vertex AI instead, set "
            "GOOGLE_CLOUD_PROJECT and use application-default credentials."),
    },
}

# Files/globs that must never be committed once generation starts.
GITIGNORE_ENTRIES = [
    ("# --- AI-Forward: visual-asset hygiene (ui-visual-assets.md) ---", None),
    ("docs/assets/**/_scratch/", "candidate boards and rejected generations - never committed"),
    ("*.env", "credentials live in the environment, never in the repo (VA9)"),
    (".env", "credentials live in the environment, never in the repo (VA9)"),
]

# Shapes that look like a committed generation credential.
SECRET_PATTERNS = [
    (re.compile(r"HIGGSFIELD_(?:API_KEY|SECRET)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"), "Higgsfield credential"),
    (re.compile(r"(?:GEMINI|GOOGLE(?:_GENAI)?)_API_KEY\s*[:=]\s*['\"]?AIza[A-Za-z0-9_\-]{20,}"), "Google API key"),
    (re.compile(r"\bAIza[A-Za-z0-9_\-]{35}\b"), "Google API key (bare)"),
]

ASSET_README = """# Generated visual assets

Governed by `ui-visual-assets.md` (VA1-VA18). Produced by the `/visualize` skill.

**The rules that make this directory safe to trust:**

- **Committed, not linked (VA4).** Every asset here was generated once, downloaded,
  optimized and committed. No provider CDN URL appears in any surface: provider results
  expire, and an asset that re-rolls per run is non-determinism inside a deterministic
  artifact.
- **Never the interface itself (VA5).** These are photographs, textures, portraits and
  motion the UI *shows*. No generated screenshots, panels, charts or icon sets - image
  models render illegible text and invented controls.
- **Every asset has a manifest entry (VA12)** in `DESIGN.md` under `assets:`, carrying the
  verbatim prompt, backend, model, preset, date, cost, **alt text** and disclosure. Without
  the prompt nobody can regenerate a consistent sibling; without the cost nobody can see
  the spend.
- **Alt text was written at generation time (VA13)**, not deferred. Decorative images use
  `alt=""`. A prompt is not alt text: one describes what was asked for, the other describes
  what a non-sighted user needs.
- **No real person's likeness or customer data was ever uploaded (VA9).** Personas here are
  fictional by construction and are fixtures, not production data.

`_scratch/` is git-ignored: it holds candidate boards and rejected generations.
"""


def repo_paths(root):
    return {
        "assets": os.path.join(root, "docs", "assets"),
        "scratch": os.path.join(root, "docs", "assets", "_scratch"),
        "readme": os.path.join(root, "docs", "assets", "README.md"),
        "gitignore": os.path.join(root, ".gitignore"),
    }


def find_design_md(root):
    """VA12's manifest lives in the design language. Resolve it the way the craft
    detector does (repo root, then docs/) so both tools agree on one file (CD4)."""
    for candidate in ("DESIGN.md", os.path.join("docs", "DESIGN.md")):
        path = os.path.join(root, candidate)
        if os.path.isfile(path):
            return path
    return None


def backend_status(name, spec):
    present = [v for v in spec["env"] if os.environ.get(v)]
    if spec.get("any_of"):
        configured = bool(present)
        missing = [] if configured else spec["env"]
    else:
        configured = len(present) == len(spec["env"])
        missing = [v for v in spec["env"] if not os.environ.get(v)]
    vertex = [v for v in spec.get("vertex_env", []) if os.environ.get(v)]
    return {
        "backend": name,
        "label": spec["label"],
        "kind": spec["kind"],
        "configured": configured,
        "present_env": present,
        "missing_env": missing,
        "vertex_env_present": vertex,
        "capabilities": spec["capabilities"],
    }


def scan_for_committed_secrets(root):
    """A generation credential in the tree is a hygiene failure, not a style issue.
    Deliberately shallow and cheap: a first-pass tripwire, not a scanner (see the
    Responsible-AI policy - real enforcement belongs in CI secret scanning)."""
    hits = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "graphify-out"}
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() not in (
                    ".md", ".json", ".yml", ".yaml", ".env", ".txt", ".ps1", ".sh", ".py", ".js", ".ts", ""):
                continue
            path = os.path.join(directory, filename)
            try:
                if os.path.getsize(path) > 512 * 1024:
                    continue
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    text = handle.read()
            except OSError:
                continue
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(text):
                    hits.append((os.path.relpath(path, root), label))
                    break
    return hits


def cmd_backends():
    print("Generation backends known to the pack\n")
    for name, spec in BACKENDS.items():
        print("  %s  (%s, %s)" % (name, spec["label"], spec["kind"]))
        print("    capabilities : %s" % ", ".join(spec["capabilities"]))
        print("    configured by: %s" % (" or ".join(spec["env"]) if spec.get("any_of")
                                         else " and ".join(spec["env"])))
        print("    note         : %s" % spec["notes"])
        print()
    print("A backend is described by capability, not vendor, so a different one substitutes")
    print("without rewriting the standard (ui-visual-assets.md VA1).")
    return 0


def cmd_check(root, as_json):
    paths = repo_paths(root)
    design = find_design_md(root)
    statuses = [backend_status(n, s) for n, s in BACKENDS.items()]
    usable = [s for s in statuses if s["configured"]]
    secrets = scan_for_committed_secrets(root)

    manifest = False
    if design:
        try:
            with open(design, "r", encoding="utf-8") as handle:
                manifest = re.search(r"^assets:", handle.read(), re.M) is not None
        except OSError:
            manifest = False

    report = {
        "root": os.path.abspath(root),
        "backends": statuses,
        "usable_backends": [s["backend"] for s in usable],
        "assets_dir": os.path.isdir(paths["assets"]),
        "design_md": os.path.relpath(design, root) if design else None,
        "assets_manifest_present": manifest,
        "committed_secret_suspects": [{"path": p, "kind": k} for p, k in secrets],
    }
    if as_json:
        print(json.dumps(report, indent=2))
        return 2 if secrets else (0 if usable else 1)

    print("visual-assets-setup - %s\n" % report["root"])
    print("Backends")
    for status in statuses:
        spec = BACKENDS[status["backend"]]
        if status["configured"]:
            print("  OK  %-38s configured (credentials in this environment)" % status["label"])
        elif spec["kind"] == "mcp":
            # An MCP backend's credentials live in the AGENT HOST, not this process.
            # Absence from os.environ is therefore not evidence of unavailability - saying
            # otherwise would be a success-shaped failure in reverse (NG6).
            print("  ??  %-38s not in this environment" % status["label"])
            print("       This backend is reached over MCP, so the agent host may hold the")
            print("       credentials even though they are not visible here. Confirm by asking")
            print("       the agent to call the backend's own status/debug tool; do not conclude")
            print("       from this check alone.")
            print("       To configure: %s" % spec["howto"])
        else:
            joiner = " or " if spec.get("any_of") else " and "
            print("  --  %-38s not configured" % status["label"])
            print("       set %s" % joiner.join(status["missing_env"]))
            print("       %s" % spec["howto"])
        if status["vertex_env_present"]:
            print("       (Vertex AI env also present: %s)" % ", ".join(status["vertex_env_present"]))

    print("\nRepository")
    print("  %s docs/assets/            %s" % ("OK " if report["assets_dir"] else "-- ",
                                               "present" if report["assets_dir"] else "missing - run --init"))
    print("  %s design language          %s" % ("OK " if design else "-- ",
                                                report["design_md"] or "none found (root or docs/) - the manifest has nowhere to live"))
    print("  %s assets: manifest         %s" % ("OK " if manifest else "-- ",
                                                "present" if manifest else "missing - run --init"))

    if secrets:
        print("\nHYGIENE PROBLEM - a generation credential appears to be committed (VA9):")
        for path, kind in secrets:
            print("  %s  (%s)" % (path, kind))
        print("  Rotate the credential, remove it from history, and move it to the environment.")

    mcp_unknown = [s for s in statuses
                   if not s["configured"] and BACKENDS[s["backend"]]["kind"] == "mcp"]
    if not usable and not mcp_unknown:
        print("\nNo backend is configured, so /visualize cannot generate anything yet.")
        print("That is a setup gap, not a design failure: the guardrails in ui-visual-assets.md")
        print("still govern any asset you add by hand.")
    elif not usable:
        print("\nNo backend is confirmed from this environment, but %d MCP backend(s) may still"
              % len(mcp_unknown))
        print("be reachable through the agent host. Confirm before concluding either way.")

    # Exit 1 only when nothing is usable AND nothing is merely unknown - an unknown is a
    # question, not a failure.
    return 2 if secrets else (0 if (usable or mcp_unknown) else 1)


def ensure_gitignore(root, dry_run):
    path = repo_paths(root)["gitignore"]
    existing = ""
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = handle.read()
    additions = [entry for entry, _ in GITIGNORE_ENTRIES if entry not in existing]
    if not additions:
        return "gitignore already covers visual-asset hygiene"
    if dry_run:
        return "would append %d line(s) to .gitignore" % len(additions)
    with open(path, "a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n")
        for entry, why in GITIGNORE_ENTRIES:
            if entry in existing:
                continue
            handle.write(entry + ("\n" if why is None else "    # %s\n" % why))
    return "appended %d line(s) to .gitignore" % len(additions)


def ensure_manifest(root, dry_run):
    design = find_design_md(root)
    if not design:
        return ("no design language found at DESIGN.md or docs/DESIGN.md - create one from "
                "templates/design-language.template.md first (U3a); the manifest lives in it")
    with open(design, "r", encoding="utf-8") as handle:
        text = handle.read()
    if re.search(r"^assets:", text, re.M):
        return "assets manifest already present in %s" % os.path.relpath(design, root)
    if dry_run:
        return "would add an assets: manifest section to %s" % os.path.relpath(design, root)
    block = (
        "\n## Generated visual assets (VA12)\n\n"
        "One entry per committed asset. Without the verbatim prompt nobody can regenerate a\n"
        "consistent sibling; without the cost nobody can see the spend; without alt text it\n"
        "fails WCAG. Written at generation time, never backfilled.\n\n"
        "```yaml\n"
        "assets: []\n"
        "  # - id: hero-workspace\n"
        "  #   file: docs/assets/<surface>/hero-workspace.webp\n"
        "  #   purpose: \"<which part of the direction brief this renders>\"\n"
        "  #   backend: higgsfield | google\n"
        "  #   model: \"<model id>\"\n"
        "  #   preset: \"<style or motion preset, if any>\"\n"
        "  #   prompt: \"<the exact prompt, verbatim>\"\n"
        "  #   generated: <ISO date>\n"
        "  #   cost: \"<credits or currency>\"\n"
        "  #   alt: \"<what a non-sighted user needs, not the prompt>\"\n"
        "  #   disclosure: ai-generated\n"
        "  #   licence-checked: true\n"
        "```\n")
    with open(design, "a", encoding="utf-8") as handle:
        handle.write(block)
    return "added an assets: manifest section to %s" % os.path.relpath(design, root)


def cmd_init(root, dry_run):
    paths = repo_paths(root)
    actions = []

    for key, label in (("assets", "docs/assets/"), ("scratch", "docs/assets/_scratch/")):
        if os.path.isdir(paths[key]):
            actions.append("%s already exists" % label)
        elif dry_run:
            actions.append("would create %s" % label)
        else:
            os.makedirs(paths[key], exist_ok=True)
            actions.append("created %s" % label)

    if os.path.isfile(paths["readme"]):
        actions.append("docs/assets/README.md already exists")
    elif dry_run:
        actions.append("would write docs/assets/README.md")
    else:
        with open(paths["readme"], "w", encoding="utf-8") as handle:
            handle.write(ASSET_README)
        actions.append("wrote docs/assets/README.md")

    actions.append(ensure_gitignore(root, dry_run))
    actions.append(ensure_manifest(root, dry_run))

    print("visual-assets-setup --init%s\n" % (" (dry run)" if dry_run else ""))
    for action in actions:
        print("  %s" % action)

    print("\nCredentials are NOT written by this script and never belong in the repo (VA9).")
    print("Run --check to see which backends your environment can reach, and --backends for")
    print("the capability matrix. Generation itself runs through /visualize.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Wire up and verify a generation backend for UI visual assets.")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--check", action="store_true", help="report what is configured")
    parser.add_argument("--init", action="store_true", help="scaffold assets dir, manifest and hygiene")
    parser.add_argument("--backends", action="store_true", help="print the capability matrix")
    parser.add_argument("--dry-run", action="store_true", help="with --init, write nothing")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable --check")
    args = parser.parse_args(argv)

    if args.backends:
        return cmd_backends()
    if args.init:
        return cmd_init(args.root, args.dry_run)
    return cmd_check(args.root, args.as_json)


if __name__ == "__main__":
    sys.exit(main())
