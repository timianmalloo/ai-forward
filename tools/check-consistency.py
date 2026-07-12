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
import json, math, os, re, sys

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
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as source:
        return source.read()


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
                  lambda p, f: os.path.isfile(p) and f.endswith((".py", ".js")))
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


def _accepted_reference_deviation(path, revision):
    text = _read(path)
    if text is None:
        return False
    required_fields_present = all(
        re.search(pattern, text, re.M)
        for pattern in (
            r"^status:\s*accepted\s*$",
            rf"^revision:\s*['\"]?{revision}['\"]?\s*$",
            r"^decision:\s*accept-reference-performance-risk\s*$",
        )
    )
    approver = re.search(
        r"^approved-by:\s*['\"]?@([^'\"\s]+)['\"]?\s*$",
        text,
        re.M,
    )
    if not required_fields_present or not approver:
        return False
    handle = approver.group(1).casefold()
    return (
        not handle.startswith("copilot")
        and handle not in {"github-actions", "dependabot", "renovate"}
        and not handle.endswith("[bot]")
    )


def _finite_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _percentile(values, quantile):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _valid_reference_benchmark(proof):
    if not isinstance(proof, dict):
        return False
    environment = proof.get("environment", {})
    azure = environment.get("azureReferenceMetadata", {})
    corpus = proof.get("corpus", {})
    thresholds = proof.get("thresholds", {})
    summary = proof.get("summary", {})
    p75 = summary.get("p75WallMilliseconds")
    peak = summary.get("maxPeakWorkingSetBytes")
    p75_limit = thresholds.get("p75WallMilliseconds")
    peak_limit = thresholds.get("peakWorkingSetBytes")
    return (
        proof.get("schemaVersion") == "docs-context-benchmark/v1"
        and proof.get("passed") is True
        and proof.get("localThresholdsPassed") is True
        and proof.get("referenceBudgetProved") is True
        and environment.get("referenceEnvironmentMatched") is True
        and environment.get("architecture") == "X64"
        and environment.get("logicalProcessors") == 4
        and environment.get("python") == "Python 3.11.9"
        and "Windows Server 2022" in environment.get("windowsCaption", "")
        and azure.get("vmSize") == "Standard_D4s_v5"
        and azure.get("offer") == "WindowsServer"
        and azure.get("osType") == "Windows"
        and corpus.get("artifacts") == 2000
        and corpus.get("relationships") == 20000
        and corpus.get("admittedSourceBytes") == 64 * 1024 * 1024
        and corpus.get("seed") == 20260710
        and corpus.get("sha256")
        == "f055e195583abdd97d673032a5e78ad89155f1adff1a8c4d324bddf8ca0a43b1"
        and p75_limit == 2000.0
        and peak_limit == 256 * 1024 * 1024
        and _finite_number(p75)
        and _finite_number(peak)
        and 0 <= p75 <= p75_limit
        and 0 <= peak <= peak_limit
    )


def _valid_browser_reference_benchmark(proof):
    if not isinstance(proof, dict):
        return False
    environment = proof.get("environment", {})
    azure = environment.get("azureReferenceMetadata", {})
    corpus = proof.get("corpus", {})
    runs = proof.get("runs", {})
    thresholds = proof.get("thresholds", {})
    summary = proof.get("summary", {})
    samples = proof.get("samples", {})
    summary_metric_names = (
        "usable2dShellP75Milliseconds",
        "selectionSearchP75Milliseconds",
        "initial2dLayoutP75Milliseconds",
        "initialSpatialP75Milliseconds",
        "minimumOrbitFramesPerSecond",
    )
    if not all(
        _finite_number(thresholds.get(name)) and _finite_number(summary.get(name))
        for name in summary_metric_names
    ):
        return False
    cold = samples.get("cold")
    warm = samples.get("warm")
    raw_metric_names = (
        "usable2dShellMilliseconds",
        "selectionSearchMilliseconds",
        "initial2dLayoutMilliseconds",
        "initialSpatialMilliseconds",
        "minimumOrbitFramesPerSecond",
    )
    if (
        not isinstance(cold, list)
        or not isinstance(warm, list)
        or len(cold) != 5
        or len(warm) != 5
        or not all(
            isinstance(sample, dict)
            and all(
                _finite_number(sample.get(name)) and sample.get(name) >= 0
                for name in raw_metric_names
            )
            and _finite_number(sample.get("heapDeltaBytes"))
            for sample in cold + warm
        )
        or any(sample.get("cacheMode") != "cold" for sample in cold)
        or any(sample.get("cacheMode") != "warm" for sample in warm)
    ):
        return False
    all_samples = cold + warm
    recomputed = {
        "usable2dShellP75Milliseconds": _percentile(
            [sample["usable2dShellMilliseconds"] for sample in cold],
            0.75,
        ),
        "selectionSearchP75Milliseconds": _percentile(
            [sample["selectionSearchMilliseconds"] for sample in all_samples],
            0.75,
        ),
        "initial2dLayoutP75Milliseconds": _percentile(
            [sample["initial2dLayoutMilliseconds"] for sample in all_samples],
            0.75,
        ),
        "initialSpatialP75Milliseconds": _percentile(
            [sample["initialSpatialMilliseconds"] for sample in all_samples],
            0.75,
        ),
        "minimumOrbitFramesPerSecond": min(
            sample["minimumOrbitFramesPerSecond"] for sample in all_samples
        ),
    }
    if not all(
        math.isclose(summary[name], recomputed[name], rel_tol=1e-9, abs_tol=1e-6)
        for name in summary_metric_names
    ):
        return False
    distributions = summary.get("distributions")
    distribution_values = {
        "usable2dShellMilliseconds": [
            sample["usable2dShellMilliseconds"] for sample in cold
        ],
        "selectionSearchMilliseconds": [
            sample["selectionSearchMilliseconds"] for sample in all_samples
        ],
        "initial2dLayoutMilliseconds": [
            sample["initial2dLayoutMilliseconds"] for sample in all_samples
        ],
        "initialSpatialMilliseconds": [
            sample["initialSpatialMilliseconds"] for sample in all_samples
        ],
        "heapDeltaBytes": [sample["heapDeltaBytes"] for sample in all_samples],
    }
    if not isinstance(distributions, dict):
        return False
    for name, values in distribution_values.items():
        actual = distributions.get(name)
        expected = {
            "p50": _percentile(values, 0.5),
            "p75": _percentile(values, 0.75),
            "max": max(values),
        }
        if not isinstance(actual, dict) or not all(
            _finite_number(actual.get(key))
            and math.isclose(
                actual[key],
                expected[key],
                rel_tol=1e-9,
                abs_tol=1e-6,
            )
            for key in expected
        ):
            return False
    return (
        proof.get("schemaVersion") == "docs-explorer-browser-benchmark/v1"
        and proof.get("passed") is True
        and proof.get("localThresholdsPassed") is True
        and proof.get("referenceBudgetProved") is True
        and environment.get("referenceEnvironmentMatched") is True
        and environment.get("architecture") == "X64"
        and environment.get("logicalProcessors") == 4
        and environment.get("playwright") == "1.61.1"
        and environment.get("browserName") == "chromium"
        and isinstance(environment.get("chromiumBuild"), str)
        and bool(environment.get("chromiumBuild"))
        and environment.get("headless") is True
        and environment.get("gpuMode") == "swiftshader"
        and environment.get("launchFlags")
        == [
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-extensions",
            "--disable-renderer-backgrounding",
            "--use-angle=swiftshader",
        ]
        and environment.get("viewport") == {"width": 1366, "height": 768}
        and environment.get("deviceScaleFactor") == 1
        and environment.get("cpuSlowdown") == 4
        and environment.get("orbitFrameWindowMilliseconds") == 1000
        and "Windows Server 2022" in environment.get("windowsCaption", "")
        and azure.get("vmSize") == "Standard_D4s_v5"
        and azure.get("offer") == "WindowsServer"
        and azure.get("osType") == "Windows"
        and corpus.get("artifacts") == 500
        and corpus.get("relationships") == 1000
        and corpus.get("surfaces") == 100
        and corpus.get("seed") == 20260710
        and corpus.get("sha256")
        == "f4b34a29d2f836957f7fe24d0424444ac515881b6618cdfdd759a302ccb3cdef"
        and runs.get("cold") == 5
        and runs.get("warm") == 5
        and thresholds.get("usable2dShellP75Milliseconds") == 2000.0
        and thresholds.get("selectionSearchP75Milliseconds") == 100.0
        and thresholds.get("initial2dLayoutP75Milliseconds") == 500.0
        and thresholds.get("initialSpatialP75Milliseconds") == 500.0
        and thresholds.get("minimumOrbitFramesPerSecond") == 30.0
        and 0 <= summary.get("usable2dShellP75Milliseconds")
        <= thresholds.get("usable2dShellP75Milliseconds")
        and 0 <= summary.get("selectionSearchP75Milliseconds")
        <= thresholds.get("selectionSearchP75Milliseconds")
        and 0 <= summary.get("initial2dLayoutP75Milliseconds")
        <= thresholds.get("initial2dLayoutP75Milliseconds")
        and 0 <= summary.get("initialSpatialP75Milliseconds")
        <= thresholds.get("initialSpatialP75Milliseconds")
        and summary.get("minimumOrbitFramesPerSecond")
        >= thresholds.get("minimumOrbitFramesPerSecond")
    )


def check_release_gate(findings):
    install = _read(os.path.join(PACK, "adapters", "INSTALL.md"))
    if install is None:
        return
    revision_match = re.search(r"^revision:\s*(\d+)\s*$", install, re.M)
    released_match = re.search(r"^released:\s*['\"]?([^'\"\r\n]*)['\"]?\s*$", install, re.M)
    if not revision_match or not released_match or not released_match.group(1).strip():
        return
    revision = int(revision_match.group(1))
    if revision < 17:
        return

    proof_dir = os.path.join(ROOT, "docs", "proof")
    cli_proof_path = os.path.join(proof_dir, "docs-context-benchmark.reference.json")
    browser_proof_path = os.path.join(
        proof_dir,
        "docs-explorer-browser-benchmark.reference.json",
    )
    cli_proof_valid = False
    browser_proof_valid = False
    try:
        proof = json.loads(_read(cli_proof_path) or "")
        cli_proof_valid = _valid_reference_benchmark(proof)
    except (OSError, ValueError, TypeError):
        cli_proof_valid = False
    try:
        proof = json.loads(_read(browser_proof_path) or "")
        browser_proof_valid = _valid_browser_reference_benchmark(proof)
    except (OSError, ValueError, TypeError):
        browser_proof_valid = False

    deviation_path = os.path.join(
        ROOT,
        "docs",
        "notes",
        "docs-explorer-reference-performance-deviation.md",
    )
    if (
        not (cli_proof_valid and browser_proof_valid)
        and not _accepted_reference_deviation(deviation_path, revision)
    ):
        findings.append(
            f"INSTALL revision {revision} is marked released without pinned CLI and browser "
            "benchmark proof or an accepted human-approved performance deviation"
        )


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
    check_release_gate(findings)
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
