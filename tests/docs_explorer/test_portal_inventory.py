"""The Documentation Portal is the published front door, so its inventories must be derived
or checked — never hand-maintained on trust.

The portal is what timianmalloo.github.io/ai-forward/ serves. Three of its sections claim to
enumerate something real: the skills, the knowledge foundations, and the persona roster. Each
of those claims is falsifiable against the filesystem, and an enumeration that silently omits
a member is worse than one that admits it is partial (V12 — an honest projection over a silent
omission).

Nothing asserted this before. The skills list happens to be derived from SKILL.md, but its
editorial companion (`skillMeta`) was hand-kept, the knowledge routing was hand-kept, and a
section added to the builder with no matching renderer in index.html would have shipped a
blank pane with no error at all.
"""
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EDITORIAL = os.path.join(ROOT, "tools", "docs-portal-editorial.json")
PORTAL_HTML = os.path.join(ROOT, "docs", "portal", "index.html")
PORTAL_DATA = os.path.join(ROOT, "docs", "portal", "portal-data.js")
COMMANDS = os.path.join(ROOT, "pack", "commands")
KNOWLEDGE = os.path.join(ROOT, "pack", "knowledge")
AGENT_DIRS = [os.path.join(ROOT, "pack", "adapters", "claude-code", "agents"),
              os.path.join(ROOT, "pack", "adapters", "copilot", "agents")]


def editorial():
    with open(EDITORIAL, encoding="utf-8") as fh:
        return json.load(fh)


def portal_data():
    """The generated payload, read as JSON out of its `window.X = {...};` wrapper."""
    with open(PORTAL_DATA, encoding="utf-8") as fh:
        text = fh.read()
    start, end = text.index("{"), text.rindex("}")
    return json.loads(text[start:end + 1])


def skills_on_disk():
    return {d for d in os.listdir(COMMANDS)
            if os.path.isfile(os.path.join(COMMANDS, d, "SKILL.md"))}


def knowledge_on_disk():
    return {f[:-3] for f in os.listdir(KNOWLEDGE)
            if f.endswith(".md") and f != "FOUNDATION.md"}


def agents_on_disk():
    rows = {}
    for adir in AGENT_DIRS:
        for fn in sorted(os.listdir(adir)):
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(adir, fn), encoding="utf-8") as fh:
                head = fh.read(4000)
            name = re.search(r"(?m)^name:\s*(\S+)", head)
            desc = re.search(r"(?m)^description:\s*(.+)$", head)
            rows[name.group(1) if name else fn[:-3]] = (desc.group(1) if desc else "").lower()
    return rows


class SkillInventoryTests(unittest.TestCase):
    def test_every_skill_has_portal_editorial(self):
        missing = sorted(skills_on_disk() - set(editorial()["skillMeta"]))
        self.assertEqual(missing, [],
                         "a skill ships with no portal entry — it exists but is undiscoverable")

    def test_no_editorial_entry_outlives_its_skill(self):
        stale = sorted(set(editorial()["skillMeta"]) - skills_on_disk())
        self.assertEqual(stale, [], "the portal advertises a skill that no longer exists")

    def test_the_published_payload_lists_every_skill(self):
        listed = {i["cmd"].lstrip("/") for g in portal_data()["skills"] for i in g["items"]}
        self.assertEqual(listed, skills_on_disk())

    def test_the_headline_count_matches_the_filesystem(self):
        data = portal_data()
        self.assertEqual(data["meta"]["skillCount"], len(skills_on_disk()))
        title = next(s["title"] for s in data["sections"] if s["id"] == "skills")
        self.assertIn(str(len(skills_on_disk())), title)


class KnowledgeInventoryTests(unittest.TestCase):
    """Every knowledge doc surfaces exactly once — in Foundations or in UI & Design."""

    def test_every_doc_is_routed_to_exactly_one_section(self):
        ed = editorial()
        docs = knowledge_on_disk()
        ui = set(ed["uiStandards"])
        grouped = set(ed["knowledgeGroups"])
        self.assertEqual(sorted(docs - grouped - ui), [],
                         "a knowledge doc reaches neither the Foundations nor the UI section")
        self.assertEqual(sorted(docs & grouped & ui), [],
                         "a knowledge doc is routed to two sections and would be listed twice")

    def test_no_routing_entry_outlives_its_doc(self):
        ed = editorial()
        docs = knowledge_on_disk()
        self.assertEqual(sorted(set(ed["knowledgeGroups"]) - docs), [])
        self.assertEqual(sorted(set(ed["uiStandards"]) - docs), [])

    def test_ui_docs_are_excluded_from_foundations_by_design(self):
        # foundations() skips uiStandards, so a knowledgeGroups entry for one of them is
        # unreachable configuration. Kept as a test so it is not "fixed" back in.
        ed = editorial()
        for name in ed["uiStandards"]:
            self.assertNotIn(name, ed["knowledgeGroups"],
                             f"{name} is routed to UI & Design; its group entry can never be read")

    def test_every_group_used_is_ordered(self):
        ed = editorial()
        used = set(ed["knowledgeGroups"].values())
        order = set(ed["foundationGroupOrder"])
        self.assertEqual(sorted(used - order), [],
                         "a group appears with no declared position and sorts to the end")


class PersonaRosterTests(unittest.TestCase):
    """The roster is derived from the agent definitions, so it cannot over-claim."""

    def test_every_agent_reaches_the_portal(self):
        listed = {p["name"] for p in portal_data()["collaboration"]["personas"]}
        self.assertEqual(listed, set(agents_on_disk()))

    def test_veto_strength_matches_the_agents_own_description(self):
        disk = agents_on_disk()
        for p in portal_data()["collaboration"]["personas"]:
            desc = disk[p["name"]]
            expected = ("hard" if "hard veto" in desc
                        else "soft" if "soft veto" in desc else "advisory")
            self.assertEqual(p["veto"], expected,
                             f"the portal claims a {p['veto']} veto for {p['name']}")

    def test_the_published_roster_is_symmetric_across_harnesses(self):
        """FR-032, recurring at the presentation layer.

        Every persona deploys to BOTH `.claude/agents/` and `.github/agents/` — an invariant
        already gated by check_deployed_agent_parity. The portal's first cut nonetheless
        labelled each row with its *source folder*, publishing the 12/11 authoring split as
        though Copilot had 11 lenses and Claude Code 12. The deploy bug was fixed twelve
        revisions before; the claim about it came back on a new surface.
        """
        for p in portal_data()["collaboration"]["personas"]:
            self.assertEqual(
                sorted(p["surfaces"]), ["Claude Code", "Copilot"],
                f"{p['name']} is published as single-surface, but every persona is deployed "
                f"to both — the source folder is an authoring detail, not availability")

    def test_availability_is_read_from_the_installed_tree_not_the_source(self):
        """The whole point of E11: 'promised on both surfaces' and 'installed on both' are
        different claims, and only the second one is checkable here."""
        def installed(rel, suffix):
            # Read the frontmatter `name:`, never the filename: the Copilot definitions are
            # copied into .claude/agents/ verbatim and keep their `_agent` suffix, so a
            # filename-derived roster silently disagrees with the persona's own identity.
            out = set()
            base = os.path.join(ROOT, *rel)
            for fn in os.listdir(base):
                if not fn.endswith(suffix):
                    continue
                with open(os.path.join(base, fn), encoding="utf-8") as fh:
                    head = fh.read(2000)
                m = re.search(r"(?m)^name:\s*(\S+)", head)
                out.add(m.group(1) if m else fn[: -len(suffix)])
            return out

        deployed = {
            "Claude Code": installed((".claude", "agents"), ".md"),
            "Copilot": installed((".github", "agents"), ".agent.md"),
        }
        for p in portal_data()["collaboration"]["personas"]:
            for surface in p["surfaces"]:
                self.assertIn(p["name"], deployed[surface],
                              f"the portal says {p['name']} runs on {surface}, but no such "
                              f"file is installed there")

    def test_every_persona_publishes_its_knowledge_lens(self):
        # The lens is what makes delegation affordable; a persona showing none on the public
        # page would misrepresent how the panel is actually run.
        for p in portal_data()["collaboration"]["personas"]:
            self.assertTrue(p["lens"], f"{p['name']} publishes no knowledge lens")


class SectionWiringTests(unittest.TestCase):
    def test_every_section_has_a_renderer(self):
        """A section in the data with no renderer in the page ships a blank pane, silently."""
        with open(PORTAL_HTML, encoding="utf-8") as fh:
            html = fh.read()
        dispatch = re.search(r"pane\.innerHTML=\(\{(.*?)\}\[state\.section\]", html, re.S)
        self.assertIsNotNone(dispatch, "the portal's section dispatch map could not be found")
        wired = set(re.findall(r"(\w+):sec\w+", dispatch.group(1)))
        declared = {s["id"] for s in portal_data()["sections"]}
        self.assertEqual(sorted(declared - wired), [],
                         "a section is declared in portal-data.js with no renderer wired")
        for name in re.findall(r"\w+:(sec\w+)", dispatch.group(1)):
            self.assertIn("function " + name + "(", html,
                          f"{name} is wired into the dispatch but never defined")

    def test_section_numbers_are_contiguous_from_one(self):
        nums = [int(s["n"]) for s in portal_data()["sections"]]
        self.assertEqual(nums, list(range(1, len(nums) + 1)),
                         "section numbering has a gap — inserting one left a stale label")

    def test_the_two_requested_sections_are_present(self):
        data = portal_data()
        ids = {s["id"] for s in data["sections"]}
        self.assertIn("agents", ids)
        self.assertIn("loop", ids)
        self.assertTrue(data["collaboration"]["mechanics"])
        self.assertTrue(data["promptLoop"]["steps"])


if __name__ == "__main__":
    unittest.main()
