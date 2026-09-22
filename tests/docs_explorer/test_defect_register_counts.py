"""FR-076 (class REC-A). The register's **Status counts:** line is checked against its entries.

The line was hand-maintained over a file appended to on every defect. By revision 59 it said
controlled 12 / partially-controlled 9 / uncontrolled 22 while the entries held 14 / 8 / 2, and
a later hand correction was itself stale. Nothing executed the claim, so nothing failed.

The register has two regions with different meanings, so the line states both:
  * project classes - the `### <ID> — <shape>` sections, each with a `- **Status:**` line;
  * inherited table - the seeded rows, whose last cell is "Status here".
A status is its leading token; a qualifier after it ("`controlled` for the POSIX pilot") does
not change the count. An entry whose status has no leading token fails by name.

Seen failing on the pre-fix file: the line was struck through and matched neither region.
"""
import re
import unittest
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "docs" / "lessons" / "defect-classes.md"
STATUSES = ("controlled", "partially-controlled", "uncontrolled")
_LEAD = re.compile(r"`?(partially[- ]controlled|uncontrolled|controlled)\b", re.I)
_STATED = re.compile(
    r"^\*\*Status counts:\*\* project classes: controlled `(\d+)` · partially-controlled `(\d+)`"
    r" · uncontrolled `(\d+)`; inherited table: controlled `(\d+)` · partially-controlled `(\d+)`"
    r" · uncontrolled `(\d+)`", re.M)


def _status(text):
    m = _LEAD.match(text.strip())
    return m.group(1).lower().replace(" ", "-") if m else None


def tally(text):
    """Return ({region: {status: n}}, [unparseable entry ids])."""
    after = text.split("\n## Project classes", 1)[1]
    sections, table = after.split("\n## Inherited classes", 1)
    counts = {"project": dict.fromkeys(STATUSES, 0), "inherited": dict.fromkeys(STATUSES, 0)}
    bad = []
    for block in re.split(r"^### ", sections, flags=re.M)[1:]:
        cid = block.split()[0]
        m = re.search(r"^- \*\*Status:\*\*(.*)$", block, re.M)
        status = _status(m.group(1)) if m else None
        if status:
            counts["project"][status] += 1
        else:
            bad.append(cid)
    for line in table.splitlines():
        if not line.startswith("| **"):
            continue
        cells = line.strip().strip("|").split("|")
        status = _status(cells[-1])
        if status:
            counts["inherited"][status] += 1
        else:
            bad.append(cells[0].strip())
    return counts, bad


def stated(text):
    m = _STATED.search(text)
    if not m:
        return None
    n = [int(g) for g in m.groups()]
    return {"project": dict(zip(STATUSES, n[:3])), "inherited": dict(zip(STATUSES, n[3:]))}


class ParserTests(unittest.TestCase):
    FIXTURE = (
        "**Status counts:** project classes: controlled `1` · partially-controlled `1` · "
        "uncontrolled `0`; inherited table: controlled `0` · partially-controlled `0` · "
        "uncontrolled `2`\n\n## Entry schema\n### <ID> — example\n- **Status:** `controlled`\n"
        "\n## Project classes\n### A-A — one\n- **Status:** `controlled` for one host\n"
        "### A-B — two\n- **Status:** partially controlled. Detail.\n"
        "\n## Inherited classes\n| ID | Status here |\n|---|---|\n"
        "| **X-A** | `uncontrolled` |\n| **X-B** | `uncontrolled` - note |\n")

    def test_fixture_tally_and_stated_line_agree(self):
        counts, bad = tally(self.FIXTURE)
        self.assertEqual(bad, [])
        self.assertEqual(counts, stated(self.FIXTURE))

    def test_schema_example_is_not_counted(self):
        counts, _ = tally(self.FIXTURE)
        self.assertEqual(sum(counts["project"].values()), 2)

    def test_a_stale_line_is_detected(self):
        stale = self.FIXTURE.replace("controlled `1` · partially", "controlled `9` · partially", 1)
        self.assertNotEqual(tally(stale)[0], stated(stale))

    def test_an_entry_without_a_status_is_named(self):
        broken = self.FIXTURE.replace("- **Status:** partially controlled. Detail.\n", "")
        self.assertEqual(tally(broken)[1], ["A-B"])


class RegisterCountsTests(unittest.TestCase):
    def setUp(self):
        self.text = REGISTER.read_text(encoding="utf-8")

    def test_corpus_is_not_empty(self):
        counts, _ = tally(self.text)
        self.assertGreater(sum(counts["project"].values()), 0)
        self.assertGreater(sum(counts["inherited"].values()), 0)

    def test_every_entry_has_a_leading_status(self):
        self.assertEqual(tally(self.text)[1], [],
                         "these entries have no leading controlled/partially-controlled/"
                         "uncontrolled status, so they cannot be counted")

    def test_stated_counts_equal_the_tally(self):
        counts, _ = tally(self.text)
        line = stated(self.text)
        self.assertIsNotNone(line, "no **Status counts:** line in the two-region form; expected: "
                             + _format(counts))
        self.assertEqual(line, counts, "the stated line is stale; replace it with: " + _format(counts))


def _format(counts):
    p, i = counts["project"], counts["inherited"]
    return ("**Status counts:** project classes: controlled `{0}` · partially-controlled `{1}` · "
            "uncontrolled `{2}`; inherited table: controlled `{3}` · partially-controlled `{4}` · "
            "uncontrolled `{5}`").format(p["controlled"], p["partially-controlled"],
                                         p["uncontrolled"], i["controlled"],
                                         i["partially-controlled"], i["uncontrolled"])


if __name__ == "__main__":
    unittest.main()
