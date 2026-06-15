#!/usr/bin/env python3
"""check-consistency.py — pack inventory / count drift detector (AI-Forward, source-only).

The pack's headline counts (skills, lenses, knowledge docs, templates, scripts) and the
skill list are hand-duplicated across INSTALL.md, the managed blocks, README/OVERVIEW, the
web explainer, and copilot-instructions. This makes those numbers a single derivable fact
again: it reads the filesystem as the source of truth and fails on any documented count or
skill/prompt-parity that disagrees. Stdlib only; lives in tools/ (NOT deployed to targets).

Checks (all FAIL the run):
  1. Filesystem counts == INSTALL.md frontmatter `counts:` (the authoritative numbers).
  2. Every skill (pack/commands/<n>/SKILL.md) has a Copilot prompt and vice versa.
  3. Managed blocks state "Skills (N)" / "Workflows (N)" with N == the real skill count.
  4. Prose totals across the doc surface ("12 skills", "23 lenses", "15 templates",
     "18 docs (+FOUNDATION ...)") match the filesystem. Qualified sub-counts
     ("ten workflow skills", "five delivery workflows") are deliberately not matched.

Exit 0 clean, 1 on any finding.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")

NUMWORDS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
}
# longest-first so "twenty-three" wins over "twenty"
_NUMALT = "|".join(sorted(NUMWORDS, key=len, reverse=True))
_NUM = r"(\d+|" + _NUMALT + r")"


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.exists(path) else None


def _val(tok):
    return int(tok) if tok.isdigit() else NUMWORDS[tok.lower()]


def _ls(path, pred):
    return sorted(f for f in os.listdir(path) if pred(os.path.join(path, f), f)) \
        if os.path.isdir(path) else []


def filesystem_truth():
    cmd = os.path.join(PACK, "commands")
    skills = sorted(d for d in os.listdir(cmd)
                    if os.path.isfile(os.path.join(cmd, d, "SKILL.md")))
    knowledge = _ls(os.path.join(PACK, "knowledge"),
                    lambda p, f: os.path.isfile(p) and f.endswith(".md"))
    knowledge_docs = [f for f in knowledge if f != "FOUNDATION.md"]
    templates = _ls(os.path.join(PACK, "templates"), lambda p, f: os.path.isfile(p))
    scripts = _ls(os.path.join(PACK, "scripts"),
                  lambda p, f: os.path.isfile(p) and f.endswith(".py"))
    cc = _ls(os.path.join(PACK, "adapters", "claude-code", "agents"),
             lambda p, f: f.endswith(".md"))
    cop = _ls(os.path.join(PACK, "adapters", "copilot", "agents"),
              lambda p, f: f.endswith("_agent.md"))
    prompts = _ls(os.path.join(PACK, "adapters", "copilot", "prompts"),
                  lambda p, f: f.endswith(".prompt.md"))
    return {
        "skills": skills, "knowledge_docs": knowledge_docs, "templates": templates,
        "scripts": scripts, "cc_agents": cc, "cop_agents": cop, "prompts": prompts,
        "counts": {
            "lenses": len(cc) + len(cop), "skills": len(skills),
            "knowledge_docs": len(knowledge_docs), "templates": len(templates),
            "scripts": len(scripts),
        },
    }


def check_install_counts(truth, findings):
    text = _read(os.path.join(PACK, "adapters", "INSTALL.md"))
    if text is None:
        findings.append("INSTALL.md not found")
        return
    m = re.search(r"\ncounts:\s*\{([^}]*)\}", text)
    if not m:
        findings.append("INSTALL.md frontmatter has no `counts:` map")
        return
    documented = {k.strip(): int(v) for k, v in re.findall(r"(\w+)\s*:\s*(\d+)", m.group(1))}
    for key, want in truth["counts"].items():
        got = documented.get(key)
        if got is None:
            findings.append(f"INSTALL counts: missing `{key}` (filesystem has {want})")
        elif got != want:
            findings.append(f"INSTALL counts.{key} = {got}, filesystem has {want}")


def check_skill_prompt_parity(truth, findings):
    skills = set(truth["skills"])
    prompts = {p[:-len(".prompt.md")] for p in truth["prompts"]}
    for s in sorted(skills - prompts):
        findings.append(f"skill '{s}' has no Copilot prompt (adapters/copilot/prompts/{s}.prompt.md)")
    for p in sorted(prompts - skills):
        findings.append(f"Copilot prompt '{p}.prompt.md' has no skill (commands/{p}/SKILL.md)")


def check_managed_blocks(truth, findings):
    n = truth["counts"]["skills"]
    for name in ("CLAUDE.block.md", "AGENTS.block.md"):
        text = _read(os.path.join(PACK, "adapters", "managed-blocks", name))
        if text is None:
            findings.append(f"managed block {name} not found")
            continue
        hits = re.findall(r"(Skills|Workflows)\s*\((\d+)\)", text)
        if not hits:
            findings.append(f"{name}: no 'Skills (N)' / 'Workflows (N)' marker found")
        for label, num in hits:
            if int(num) != n:
                findings.append(f"{name}: '{label} ({num})' but filesystem has {n} skills")
        # Every skill must be named in the block's skill/workflow list (as `/name` or `name`).
        for s in truth["skills"]:
            if not re.search(r"(?:/|`)" + re.escape(s) + r"\b", text):
                findings.append(f"{name}: skill '{s}' is missing from the skill/workflow list")


# (regex, noun-group-index, expected-count-key) tuples for prose totals.
def _prose_rules(truth):
    nb = r"(?<![\w-])"  # not preceded by word-char or hyphen
    return [
        (re.compile(nb + _NUM + r"\s+(skills|workflows)\b", re.I), "skills"),
        (re.compile(nb + _NUM + r"[\s-]+(lenses|lens|personas|persona)\b", re.I), "lenses"),
        (re.compile(nb + _NUM + r"\s+(?:artifact\s+)?templates\b", re.I), "templates"),
        (re.compile(r"(\d+)\s+docs\s*\(\+FOUNDATION", re.I), "knowledge_docs"),
    ]


DOC_SURFACE = [
    "README.md", "CLAUDE.md", "AGENTS.md",
    os.path.join("pack", "README.md"), os.path.join("pack", "OVERVIEW.md"),
    os.path.join("pack", "adapters", "INSTALL.md"),
    os.path.join("web", "ai-forward-pack-explainer.html"),
    os.path.join(".github", "copilot-instructions.md"),
]


def check_prose(truth, findings):
    rules = _prose_rules(truth)
    for rel in DOC_SURFACE:
        text = _read(os.path.join(ROOT, rel))
        if text is None:
            continue
        for rx, key in rules:
            want = truth["counts"][key]
            for m in rx.finditer(text):
                got = _val(m.group(1))
                if got != want:
                    line = text[:m.start()].count("\n") + 1
                    findings.append(
                        f"{rel}:{line}: '{m.group(0).strip()}' implies {key}={got}, "
                        f"filesystem has {want}")


def main():
    truth = filesystem_truth()
    findings = []
    check_install_counts(truth, findings)
    check_skill_prompt_parity(truth, findings)
    check_managed_blocks(truth, findings)
    check_prose(truth, findings)

    c = truth["counts"]
    print(f"filesystem: {c['skills']} skills, {c['lenses']} lenses "
          f"({len(truth['cc_agents'])} claude-code + {len(truth['cop_agents'])} copilot), "
          f"{c['knowledge_docs']} knowledge docs, {c['templates']} templates, "
          f"{c['scripts']} scripts; {len(truth['prompts'])} copilot prompts")
    if findings:
        print(f"\n{len(findings)} consistency finding(s):")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("clean - all documented counts and skill/prompt parity match the filesystem")
    return 0


if __name__ == "__main__":
    sys.exit(main())
