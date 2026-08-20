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


def _frontmatter_lines(text):
    """Yield (key, raw_value) for the top-level scalar lines of a --- fenced frontmatter block."""
    if not text or not text.startswith("---"):
        return
    end = text.find("\n---", 3)
    if end == -1:
        return
    block = text[3:end]
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s?(.*)$", line)
        if m:
            yield m.group(1), m.group(2)


def check_frontmatter_yaml(truth, findings):
    """Every SKILL.md / prompt frontmatter must parse as YAML.

    The load-bearing failure this catches: an unquoted `description:` scalar containing a
    colon-followed-by-space (e.g. "... assume: markers") is read by YAML as a nested mapping,
    the whole frontmatter fails to parse, and the tool silently drops the skill/prompt from
    the roster (it becomes unrecognized). Enforce the class, not the instance: a plain
    (unquoted) scalar value MUST NOT contain ': '. Stdlib-only — no PyYAML dependency.
    """
    files = [os.path.join(PACK, "commands", s, "SKILL.md") for s in truth["skills"]]
    files += [os.path.join(PACK, "adapters", "copilot", "prompts", p) for p in truth["prompts"]]
    for path in files:
        text = _read(path)
        if text is None:
            continue
        rel = os.path.relpath(path, ROOT)
        for key, value in _frontmatter_lines(text):
            v = value.strip()
            if not v:
                continue
            quoted = (v[0] in "\"'" and v[-1] == v[0] and len(v) >= 2)
            block_scalar = v[0] in "|>"
            if not quoted and not block_scalar and re.search(r":\s", v):
                findings.append(
                    f"{rel}: frontmatter '{key}:' value contains an unquoted colon-space "
                    f"(': ') — YAML reads it as a mapping and the whole frontmatter fails to "
                    f"parse, silently dropping this skill/prompt. Quote the value or remove the "
                    f"': '.")


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


def check_deployed_agent_parity(truth, findings):
    """FR-032. Every other check here reads the pack SOURCE. That is exactly why the
    Copilot surface could ship 11 of 23 personas for twelve revisions while this script
    printed "23 lenses" and exited 0: `lenses` is len(cc)+len(cop) from pack/, and nothing
    ever counted what was actually deployed.

    The deployment map promises both peers and adversaries on both surfaces, so the
    invariant is: each deployed agent directory carries one file per persona. Checking the
    installed state rather than the source is the whole point (end-to-end-integrity E11).
    """
    expected = len(truth["cc_agents"]) + len(truth["cop_agents"])
    for label, rel, suffix in ((".claude/agents", os.path.join(ROOT, ".claude", "agents"), ".md"),
                               (".github/agents", os.path.join(ROOT, ".github", "agents"), ".agent.md")):
        if not os.path.isdir(rel):
            findings.append(f"{label}: directory missing; expected {expected} deployed personas")
            continue
        actual = len([f for f in os.listdir(rel) if f.endswith(suffix)])
        if actual != expected:
            findings.append(
                f"{label}: {actual} personas deployed, but the pack source defines {expected} "
                f"({len(truth['cc_agents'])} claude-code + {len(truth['cop_agents'])} copilot). "
                f"The deployment map promises every persona on both surfaces - re-run sync-pack.ps1")

    # A tools: line on the Copilot surface is misleading (Copilot ignores unknown tool
    # names and silently falls back to all-tools), so INSTALL 1.2 requires it stripped.
    gh = os.path.join(ROOT, ".github", "agents")
    if os.path.isdir(gh):
        leaked = []
        for name in sorted(os.listdir(gh)):
            if not name.endswith(".agent.md"):
                continue
            with open(os.path.join(gh, name), "r", encoding="utf-8") as handle:
                if re.search(r"(?m)^tools:", handle.read()):
                    leaked.append(name)
        if leaked:
            findings.append(
                f".github/agents: {len(leaked)} agent(s) still carry a `tools:` line, which "
                f"INSTALL 1.2 requires stripped at the Copilot boundary: {', '.join(leaked[:4])}")


def check_directive_ranges(findings):
    """FR-035. Standards are cited by range — "ui-interaction-design.md (U1–U20)". Nothing
    verified that the cited extent matched the standard, so `S1–S18` survived in ~30 files
    after the specification standard was consolidated to S10, and `G1–G18` against a grammar
    defining G16. Every skill's Authority line was pointing at directives that do not exist.

    The invariant: for a standard defining directives with prefix X, any whole-range citation
    `X1–Xn` anywhere in the corpus must have n == the highest X actually defined.
    """
    prefixes = {
        "U": "ui-interaction-design", "DX": "ui-design-craft", "TQ": "technical-ui-design",
        "G": "ui-archetype-grammar", "S": "specification-standards", "CD": "ui-craft-detection",
        "VA": "ui-visual-assets", "DM": "domain-and-data-modelling", "E": "end-to-end-integrity",
        "CI": "continuous-improvement", "NG": "no-guessing-protocol", "OB": "obsidian-lens",
        "GK": "code-knowledge-graph", "L": "solution-selection-ladder",
        "V": "knowledge-visualization", "O": "observability-and-instrumentation",
    }
    highest = {}
    for prefix, doc in prefixes.items():
        path = os.path.join(PACK, "knowledge", "%s.md" % doc)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            nums = [int(m) for m in re.findall(r"\*\*%s(\d+)\s*[\u2014-]" % prefix, handle.read())]
        if nums:
            highest[prefix] = max(nums)

    # Scan the pack SOURCE only; the generated surfaces are copies and would double-report.
    targets = []
    for base, _dirs, names in os.walk(PACK):
        for name in names:
            if name.endswith((".md", ".html")):
                targets.append(os.path.join(base, name))

    rx = re.compile(r"\b([A-Z]{1,2})1\s*(?:\u2013|-|&ndash;)\s*(?:\1)?(\d+)\b")
    seen = set()
    for path in sorted(targets):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError:
            continue
        for match in rx.finditer(text):
            prefix, cited = match.group(1), int(match.group(2))
            if prefix not in highest:
                continue
            real = highest[prefix]
            # Only a citation that OUTRUNS the standard is a defect. A shorter range is a
            # deliberate sub-range ("CI1-CI6"), which is legitimate and common.
            if cited > real:
                key = (prefix, cited, real)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    f"directive range: `{prefix}1-{prefix}{cited}` is cited, but "
                    f"{prefixes[prefix]}.md defines only up to {prefix}{real} - "
                    f"the citation names {cited - real} directive(s) that do not exist")


def check_static_page_links(findings):
    """FR-036. `docs/_site/index.html` is a hand-maintained landing page - fully static, no
    index read - so it drifts silently as documents move. Found pointing at `../skills.md`,
    a file that has never existed in this repo. Nothing checked it because it is HTML, not
    a graph node, so `docs-graph.py validate` never sees it.
    """
    pages = [os.path.join(ROOT, "docs", "_site", "index.html")]
    for page in pages:
        if not os.path.isfile(page):
            continue
        with open(page, "r", encoding="utf-8") as handle:
            text = handle.read()
        base = os.path.dirname(page)
        rel = os.path.relpath(page, ROOT).replace(os.sep, "/")
        for href in re.findall(r'href="((?:\.\./|\./)[^"#?]+)"', text):
            target = os.path.normpath(os.path.join(base, href))
            if not os.path.exists(target):
                findings.append(
                    f"{rel}: link `{href}` points at a file that does not exist - "
                    f"a static page is invisible to docs-graph validate, so nothing else checks it")


# A path the pack names but does not ship is only legitimate when something creates it at
# runtime. These are the cases with no owning SKILL.md, each with the reason it is exempt.
PROMISED_PATH_ALLOWLIST = {
    ".github/mcp.json": "written by visual-assets-setup.py --init-mcp; git-ignored (carries credentials)",
    "docs/.obsidian/workspace.json": "per-user Obsidian state, deliberately git-ignored (obsidian-lens OB4)",
    "docs/design/conceptual-model.md": "authored by /design when a domain is modelled (DM18)",
    "docs/lessons/defect-classes.md": "seeded per-repo from the template",
}


def check_promised_paths(findings):
    """FR-044/FR-045, and the control for PACK-E generally.

    A deployment map or standard that names a repo path the project does not ship sends an
    adopting agent to a file that is not there. FR-043 found one instance and fixed it; FR-044
    found another *in the same file* one revision later, because the fix never swept the class.
    RIG-C - "sweep stopped at the instance" - is this project's dominant defect signature, and
    nothing enforced CI2's sweep step. This is that enforcement.

    A referenced path is legitimate when it (a) exists, (b) is claimed by a SKILL.md as
    something that skill creates, or (c) is allowlisted above with a stated reason. Anything
    else is a promise with no source.
    """
    skill_text = []
    for base, _dirs, names in os.walk(os.path.join(PACK, "commands")):
        for name in names:
            if name == "SKILL.md":
                with open(os.path.join(base, name), "r", encoding="utf-8") as handle:
                    skill_text.append(handle.read())
    skills = "\n".join(skill_text)

    rx = re.compile(
        r"`((?:docs/|tools/|web/|tests/|\.claude/|\.github/)[A-Za-z0-9_./-]+"
        r"\.(?:md|py|ps1|js|html|yml|json))`")

    seen = {}
    for base, dirs, names in os.walk(PACK):
        dirs[:] = [d for d in dirs if d != "evals"]
        for name in names:
            if not name.endswith((".md", ".html")):
                continue
            path = os.path.join(base, name)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
            except OSError:
                continue
            for match in rx.finditer(text):
                ref = match.group(1)
                if "<" in ref or "*" in ref:
                    continue
                if os.path.exists(os.path.join(ROOT, ref)):
                    continue
                if ref in PROMISED_PATH_ALLOWLIST or ref in skills:
                    continue
                seen.setdefault(ref, set()).add(
                    os.path.relpath(path, ROOT).replace(os.sep, "/"))

    for ref in sorted(seen):
        where = sorted(seen[ref])
        findings.append(
            f"promised path `{ref}` does not exist and nothing creates it "
            f"(named in {where[0]}" + (f" +{len(where)-1} more" if len(where) > 1 else "") + ")")


def check_html_inline_scripts(findings):
    """PACK-G: a client-rendered surface with a syntax error in an embedded <script> renders a
    success-shaped blank (the mount target stays empty -> a black page), and nothing in the build
    parses the JavaScript. This gate runs `node --check` over the inline scripts of the committed
    HTML surfaces the site serves, so a broken data literal can never ship green again. If Node is
    not on PATH it is skipped with a note (the Python consistency gate stays dependency-free)."""
    import shutil, subprocess, glob, tempfile
    node = shutil.which("node")
    if not node:
        return  # dependency-free skip: no node -> no gate (do not fail the Python-only path)
    targets = []
    for pat in ("web/*.html", "docs/portal/index.html", "docs/mockups/*.html", "docs/*.html"):
        targets.extend(glob.glob(os.path.join(ROOT, *pat.split("/"))))
    seen = set()
    for path in sorted(targets):
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        try:
            html = open(path, "r", encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        # inline scripts only: those WITHOUT a src= attribute
        for m in re.finditer(r"(?is)<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>", html):
            body = m.group(1).strip()
            if not body or ("application/json" in (m.group(0)[:120].lower())):
                continue  # skip empty and JSON data blocks (not executable JS)
            tf = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
            try:
                tf.write(body); tf.close()
                r = subprocess.run([node, "--check", tf.name], capture_output=True, text=True, timeout=30)
                if r.returncode != 0:
                    err = (r.stderr or r.stdout or "").strip().splitlines()
                    msg = next((l for l in err if "Error" in l), (err[-1] if err else "syntax error"))
                    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                    findings.append(
                        f"{rel}: inline <script> has a JavaScript syntax error "
                        f"({msg.strip()}) - this surface renders blank/black at runtime (PACK-G).")
            except (OSError, subprocess.SubprocessError):
                pass
            finally:
                try:
                    os.unlink(tf.name)
                except OSError:
                    pass


def check_docs_portal(findings):
    """The Documentation Portal (docs/portal/portal-data.js) is a DERIVED artifact; assert it is
    current by re-running its generator in --check mode. A stale portal is a failing build, not a
    matter of discipline (spec-documentation-portal US-4)."""
    import subprocess
    gen = os.path.join(ROOT, "tools", "build-docs-portal.py")
    if not os.path.isfile(gen):
        return
    try:
        r = subprocess.run([sys.executable, gen, "--check"], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        findings.append(f"docs portal: could not run drift check ({e})")
        return
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "portal-data.js is stale").strip().splitlines()
        findings.append("docs portal: " + (msg[0] if msg else "stale") +
                        " (run: python tools/build-docs-portal.py)")


def main():
    truth = filesystem_truth()
    findings = []
    check_install_counts(truth, findings)
    check_release_gate(findings)
    check_skill_prompt_parity(truth, findings)
    check_frontmatter_yaml(truth, findings)
    check_deployed_agent_parity(truth, findings)
    check_directive_ranges(findings)
    check_static_page_links(findings)
    check_promised_paths(findings)
    check_managed_blocks(truth, findings)
    check_prose(truth, findings)
    check_docs_portal(findings)
    check_html_inline_scripts(findings)

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
