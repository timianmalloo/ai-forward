"""P0 — the doctrine home: `pack/knowledge/agent-coordination.md` is always loaded, under a
3,000-token ceiling, carries every proposal §3.3 invariant as a CO line with its citation, and
keeps the seeded CO-S0 / CO-L sections byte-for-byte.

Spec: docs/specs/agent-coordination-doctrine.md (US-1..US-12). Design:
docs/design/agent-coordination-doctrine.md (the aggregate invariant *completeness under the
ceiling*; every expectation derived from a source — the proposal, origin/main, est_tokens — never
a hand-kept list). Written red-first: US-1, US-4..US-11 failed against the seeded doc; US-2 and
US-3 are green on the seed by construction, so each carries a companion test that shows its
detector firing on a mutated copy.
"""
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC_REL = "pack/knowledge/agent-coordination.md"
WT_REL = "pack/knowledge/session-worktree-discipline.md"
DOC = REPO / DOC_REL
WT = REPO / WT_REL
PROPOSAL = REPO / "docs" / "proposals" / "owner-coordinator-subagent-coordination.md"
INDEX = REPO / "docs" / "docs-index.js"
SCRIPT = REPO / "pack" / "scripts" / "context-budget.py"
CEILING_TOKENS = 3000
SEEDED_SECTIONS = ("CO-S0", "CO-L")
PROTOCOL_OBJECTS = ("session card", "delegation contract", "seam request", "decision request",
                    "ruling", "leader designation", "join state", "mail", "board")
VOCABULARY = ("Owner seat", "human operator", "conductor")
# The proposal's §6 trigger cells are prose; a phrase per row is the pragmatic floor.
# simplify: ceiling = the §6 row count, which is derived and compared first, so a new row fails
# before this tuple can hide it; upgrade trigger = a second table that needs the same check.
STRUCK_TRIGGER_PHRASES = ("time-to-ack", "second machine", "leader-loss", "false-kick",
                          "never automatic", "WT4 exception", "cannot be built on files",
                          "none", "third party", "deprecated")


def _load_context_budget():
    spec = importlib.util.spec_from_file_location("context_budget_doctrine", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_show(rel_path):
    """The committed base text of a tracked file. An unreadable ref is an ERROR, never a pass."""
    errors = []
    for ref in ("origin/main", "main"):
        proc = subprocess.run(["git", "show", f"{ref}:{rel_path}"], cwd=str(REPO),
                              capture_output=True, text=True, encoding="utf-8")
        if proc.returncode == 0:
            return proc.stdout.replace("\r\n", "\n")
        errors.append(f"{ref}: exit {proc.returncode} {proc.stderr.strip()}")
    raise RuntimeError("base text unreadable for " + rel_path + " - " + "; ".join(errors))


def _read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def section(text, heading_id):
    """The H2 section whose heading starts with `heading_id`, heading to next H2; None if absent."""
    match = re.search(r"^## " + re.escape(heading_id) + r"\b.*$", text, re.M)
    if not match:
        return None
    rest = text[match.start():]
    nxt = re.search(r"^## ", rest[1:], re.M)
    return rest if not nxt else rest[: nxt.start() + 1]


def co_lines(text):
    return [line for line in text.split("\n")
            if re.match(r"^\s*(?:[-*]\s+)?\*\*CO\d+\*\*", line)]


def proposal_invariants():
    """(lead phrase, citation token) per numbered bullet of the proposal's §3.3 — derived."""
    text = _read(PROPOSAL)
    start = re.search(r"^### 3\.3\b.*$", text, re.M)
    if not start:
        raise AssertionError("proposal §3.3 heading not found")
    region = text[start.end():]
    end = re.search(r"^## ", region, re.M)
    region = region[: end.start()] if end else region
    bullets = re.split(r"^\d+\.\s+", region, flags=re.M)[1:]
    out = []
    for bullet in bullets:
        lead = re.search(r"\*\*(.+?)\*\*", bullet, re.S)
        cites = re.findall(r"\(([^()]*)\)", bullet)
        if not lead or not cites:
            raise AssertionError("§3.3 bullet without a bold lead or a citation: " + bullet[:80])
        token = re.split(r"[;\s,]+", cites[-1].strip())[0]
        out.append((" ".join(lead.group(1).split()), token))
    return out


def proposal_struck_rows():
    """The §6 table rows (struck, why, trigger) — derived from the proposal."""
    text = _read(PROPOSAL)
    start = re.search(r"^## 6\. .*$", text, re.M)
    if not start:
        raise AssertionError("proposal §6 heading not found")
    region = text[start.end():]
    end = re.search(r"^## ", region, re.M)
    region = region[: end.start()] if end else region
    rows = []
    for line in region.split("\n"):
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Struck"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3:
            rows.append(tuple(cells))
    return rows


def struck_keyword(struck_cell):
    words = struck_cell.split()
    while words and words[0].lower() in ("a", "an", "the"):
        words = words[1:]
    return words[0].strip("*")


class FrontmatterTests(unittest.TestCase):
    """US-1 — always loaded, and no inert `skills:` key misdescribing the scope."""

    def setUp(self):
        self.cb = _load_context_budget()
        self.meta, _ = self.cb.read_frontmatter(str(DOC))

    def test_the_doc_is_load_always(self):
        self.assertEqual(self.meta.get("load"), "always", self.meta)

    def test_the_doc_declares_no_skills_key(self):
        self.assertNotIn("skills", self.meta, "skills: is inert on an always-on doc (scan() filters on load only)")


class CeilingTests(unittest.TestCase):
    """US-2 — under 3,000 estimated tokens by the SAME counter the gate uses."""

    def setUp(self):
        self.cb = _load_context_budget()

    def test_the_doc_is_under_the_ceiling(self):
        tokens = self.cb.est_tokens(os.path.getsize(DOC))
        self.assertLessEqual(tokens, CEILING_TOKENS,
                             f"measured {tokens} est. tokens ({os.path.getsize(DOC)} bytes) > {CEILING_TOKENS}")

    def test_the_counter_flags_a_doc_one_token_over(self):
        # The detector's oracle: a file sized just past the ceiling reads as over it.
        over = int((CEILING_TOKENS + 1) * self.cb.CHARS_PER_TOKEN) + 1
        under = int((CEILING_TOKENS - 1) * self.cb.CHARS_PER_TOKEN)
        self.assertGreater(self.cb.est_tokens(over), CEILING_TOKENS)
        self.assertLessEqual(self.cb.est_tokens(under), CEILING_TOKENS)


class SeededSectionTests(unittest.TestCase):
    """US-3 — CO-S0 and CO-L are byte-for-byte the base commit's text; absence is a failure."""

    def setUp(self):
        self.base = _git_show(DOC_REL)
        self.tree = _read(DOC)

    def test_seeded_sections_are_unchanged_from_base(self):
        for sid in SEEDED_SECTIONS:
            base_sec = section(self.base, sid)
            tree_sec = section(self.tree, sid)
            self.assertIsNotNone(base_sec, f"{sid} missing from base")
            self.assertIsNotNone(tree_sec, f"{sid} missing from the tree")
            self.assertEqual(base_sec, tree_sec, f"{sid} drifted from origin/main")

    def test_a_one_byte_change_to_a_seeded_section_is_detected(self):
        original = section(self.tree, "CO-S0")
        self.assertIsNotNone(original)
        mutated_doc = self.tree.replace(original, original.replace("compile", "compi1e", 1), 1)
        self.assertNotEqual(section(mutated_doc, "CO-S0"), original)

    def test_a_missing_seeded_section_is_none_not_empty(self):
        self.assertIsNone(section("# nothing\n\n## CO-X\ntext\n", "CO-S0"))


class InvariantTests(unittest.TestCase):
    """US-4 — every §3.3 invariant is a CO line naming its measurement or spike."""

    def setUp(self):
        self.invariants = proposal_invariants()
        self.doc = _read(DOC)
        self.lines = [" ".join(line.split()) for line in co_lines(self.doc)]

    def test_the_proposal_yields_invariants(self):
        # PACK-P: an empty corpus must fail, never pass vacuously.
        self.assertGreaterEqual(len(self.invariants), 12, self.invariants)

    def test_every_invariant_phrase_is_a_co_line(self):
        for phrase, _ in self.invariants:
            self.assertTrue(any(phrase in line for line in self.lines),
                            f"no CO line carries the invariant: {phrase!r}")

    def test_every_invariant_co_line_names_its_measurement_or_spike(self):
        for phrase, token in self.invariants:
            carriers = [line for line in self.lines if phrase in line]
            self.assertTrue(carriers, phrase)
            for line in carriers:
                cites = re.findall(r"\(([^()]*)\)", line)
                self.assertTrue(cites, f"CO line has no parenthesised citation: {line[:80]}")
                self.assertTrue(any(token in c for c in cites),
                                f"CO line for {phrase[:40]!r} does not cite {token!r}: {cites}")

    def test_every_co_line_has_a_unique_id(self):
        ids = [re.match(r"^\s*(?:[-*]\s+)?\*\*(CO\d+)\*\*", line).group(1) for line in co_lines(self.doc)]
        self.assertEqual(len(ids), len(set(ids)), ids)


class ContentTests(unittest.TestCase):
    """US-5..US-10 — protocol objects, the kick ladder, the vocabulary, the stages, the struck
    list, the scenarios and the citations."""

    def setUp(self):
        self.doc = _read(DOC)
        self.lower = self.doc.lower()

    def test_every_protocol_object_is_named(self):
        for name in PROTOCOL_OBJECTS:
            self.assertIn(name, self.lower, name)

    def test_the_kick_ladder_and_its_cap(self):
        self.assertRegex(self.doc, r"0\s+notify")
        self.assertRegex(self.doc, r"1\s+kick")
        self.assertRegex(self.doc, r"2\s+\**escalate")
        self.assertRegex(self.doc, r"3\s+\**human")
        self.assertIn("two kicks per work item", self.lower)

    def test_the_vocabulary(self):
        for term in VOCABULARY:
            self.assertIn(term, self.doc, term)

    def test_the_three_shared_stages_are_defined(self):
        for sid in ("CO-S0", "CO-S1", "CO-S2"):
            self.assertIsNotNone(section(self.doc, sid), f"## {sid} missing")

    def test_the_struck_list_matches_the_proposal_with_a_trigger_per_row(self):
        rows = proposal_struck_rows()
        self.assertGreaterEqual(len(rows), 10, rows)
        heading = re.search(r"^## .*[Ss]truck.*$", self.doc, re.M)
        self.assertIsNotNone(heading, "no struck-list section")
        struck = section(self.doc, heading.group(0)[3:].split(" ")[0])
        doc_rows = [line for line in struck.split("\n")
                    if line.startswith("|") and not line.startswith("|---") and not line.startswith("| Struck")]
        self.assertEqual(len(doc_rows), len(rows), "one doc row per struck item")
        for (item, _, _), doc_row in zip(rows, doc_rows):
            self.assertIn(struck_keyword(item).lower(), doc_row.lower(), item)
            self.assertTrue(any(p.lower() in doc_row.lower() for p in STRUCK_TRIGGER_PHRASES),
                            f"struck row without a reopen trigger: {doc_row}")

    def test_each_scenario_points_at_its_playbook_in_one_line(self):
        for scenario, ref in (("S1", "5.2"), ("S2", "5.1"), ("S3", "5.3")):
            pattern = r"^.*\*\*" + scenario + r"\b.*§" + re.escape(ref) + r".*$"
            self.assertIsNotNone(re.search(pattern, self.doc, re.M),
                                 f"{scenario} must point at proposal §{ref} on one line")

    def test_stage_detail_is_cited_by_kb_id_never_inlined(self):
        index = _read(INDEX)
        ids = set(re.findall(r"kb-multi-agent-coordination[\w-]*", self.doc))
        self.assertIn("kb-multi-agent-coordination", ids)
        for kb_id in ids:
            self.assertIn(kb_id, index, f"cited id not in docs-index.js: {kb_id}")
        for copied in ("| Part | Mechanism |", "| Harness | Coordinator spawns |", "| Object | Verb"):
            self.assertNotIn(copied, self.doc, "a proposal table was inlined: " + copied)


class WorktreePointerTests(unittest.TestCase):
    """US-11 — one paragraph after WT12 points at CTX-Q and CO-L without restating them."""

    def _after_wt12(self, text):
        start = re.search(r"^\*\*WT12", text, re.M)
        end = re.search(r"^## 4\.", text, re.M)
        self.assertTrue(start and end, "WT12 or §4 heading missing")
        region = text[start.start(): end.start()]
        paras = [p.strip() for p in re.split(r"\n\s*\n", region) if p.strip() and p.strip() != "---"]
        return paras[1:]  # drop the WT12 paragraph itself

    def test_exactly_one_new_paragraph_after_wt12(self):
        base_paras = self._after_wt12(_git_show(WT_REL))
        tree_paras = self._after_wt12(_read(WT))
        new = [p for p in tree_paras if p not in base_paras]
        self.assertEqual(len(new), 1, new)
        para = new[0]
        self.assertIn("CTX-Q", para)
        self.assertIn("CO-L", para)
        for restated in ("update-ref", "epoch", "compare-and-swap"):
            self.assertNotIn(restated, para, "the pointer must not restate CO-L")


if __name__ == "__main__":
    unittest.main()
