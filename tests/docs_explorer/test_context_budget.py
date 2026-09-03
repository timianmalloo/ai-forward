"""P1/P2/P3/P5 — the always-on context budget is declared, measured, and ratcheted.

An instruction set attached to every request IS the static prefix of every model call. In
the session that motivated this, 37 of 39 knowledge docs shipped with `applyTo: "**"`,
making a 184K-token corpus the prefix of all 484 calls — 63% of every input token spent
re-reading the same text, and a ceiling that failed 27 of 39 delegated runs outright.

The failure mode is not that the docs are wrong. It is that nothing reported what they
cost, so each new one looked free. These tests pin the properties that keep it from
re-growing: every doc DECLARES its scope, growth is RATCHETED, and every agent declares
the lens it actually needs instead of inheriting the world.
"""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "context-budget.py")
KNOWLEDGE = os.path.join(ROOT, "pack", "knowledge")
CONFIG = os.path.join(ROOT, "pack", "context-budget.json")
CC_AGENTS = os.path.join(ROOT, "pack", "adapters", "claude-code", "agents")
COP_AGENTS = os.path.join(ROOT, "pack", "adapters", "copilot", "agents")

spec = importlib.util.spec_from_file_location("context_budget", SCRIPT)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

def set_scope(kdir, name, scope):
    """Rewrite a doc's load scope, or strip its frontmatter entirely when scope is None."""
    path = os.path.join(kdir, name)
    with open(path, encoding="utf-8") as fh:
        body = fh.read().split("---\n", 2)[-1]
    header = "---\nload: " + scope + "\n---\n" if scope else ""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header + body)


class DeclarationTests(unittest.TestCase):
    """P1 — every knowledge doc declares when it loads."""

    def setUp(self):
        self.docs = cb.scan(KNOWLEDGE)

    def test_every_doc_declares_a_known_load_scope(self):
        undeclared = [d["name"] for d in self.docs if d["load"] not in cb.TIERS]
        self.assertEqual(undeclared, [],
                         "an undeclared doc is an unbudgeted doc — add `load:` frontmatter")

    def test_glob_scoped_docs_carry_a_pattern(self):
        # `load: glob` with no applyTo would deploy with an empty scope, which is either
        # "never attached" or "always attached" depending on the reader. Neither is intended.
        for doc in self.docs:
            if doc["load"] == "glob":
                self.assertTrue(doc["applyTo"], f"{doc['name']}: load: glob with no applyTo")

    def test_skill_scoped_docs_name_the_skills_that_load_them(self):
        skills_dir = os.path.join(ROOT, "pack", "commands")
        real = {d for d in os.listdir(skills_dir)
                if os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))}
        for doc in self.docs:
            if doc["load"] == "skill":
                self.assertTrue(doc["skills"], f"{doc['name']}: load: skill names no skills")
                unknown = [s for s in doc["skills"] if s not in real]
                self.assertEqual(unknown, [], f"{doc['name']} names skills that do not exist")

    def test_the_manifest_is_always_on_without_frontmatter(self):
        # FOUNDATION.md is the vendored provenance manifest: hashed by foundation-check.py
        # and kept byte-identical, so it carries no frontmatter and is always-on by rule.
        manifest = [d for d in self.docs if d["name"] == "FOUNDATION"]
        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]["load"], "always")


class BudgetRatchetTests(unittest.TestCase):
    """P2 — the gate fails on unacknowledged GROWTH, not on an absolute number.

    The first cut of this gate was a fixed 45,000-token ceiling. It was the wrong shape:
    two ordinary paragraphs (IO13 and GO19) took the set to 97% of budget, so the next
    routine edit would have red-lighted the build — training exactly the reflex ("just
    raise the ceiling") that PACK-R exists to break. A ceiling stays silent through the
    whole accumulation and then fires on something innocent. A ratchet fires on the
    accumulation itself, and the fix is one acknowledged line in a diff.
    """

    def _sandbox(self, mutate=None, extra=()):
        """A throwaway copy of the shipped tree, optionally mutated. Returns the gate's exit."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        kdir = os.path.join(tmp, "knowledge")
        shutil.copytree(KNOWLEDGE, kdir)
        cfg = os.path.join(tmp, "context-budget.json")
        shutil.copy(CONFIG, cfg)
        if mutate:
            mutate(kdir, cfg)
        return cb.main(["--knowledge-dir", kdir, "--config", cfg, "gate", *extra])

    def test_passes_on_the_shipped_tree(self):
        self.assertEqual(self._sandbox(), 0)

    def test_fails_when_the_set_grows_without_the_baseline_moving(self):
        """The control, observed failing on the shape it exists to catch."""
        self.assertEqual(
            self._sandbox(lambda k, c: set_scope(k, "layered-optimized-architecture.md",
                                                 "always")), 1,
            "a doc promoted back to always-on must fail until the baseline records it")

    def test_an_ordinary_edit_does_not_trip_the_gate(self):
        """The regression the ceiling design caused. Editing prose is not a budget event."""
        def grow(kdir, _cfg):
            with open(os.path.join(kdir, "rigor-protocol.md"), "a", encoding="utf-8") as fh:
                fh.write("\n" + ("x" * 1900) + "\n")   # ~400 estimated tokens
        self.assertEqual(self._sandbox(grow), 0,
                         "a routine edit inside tolerance must not fail the build")

    def test_fails_when_a_doc_loses_its_declaration(self):
        self.assertEqual(
            self._sandbox(lambda k, c: set_scope(k, "rigor-protocol.md", None)), 1)

    def test_acknowledging_the_growth_clears_it(self):
        """Growth is allowed; SILENT growth is not. Recording it must actually resolve."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        kdir = os.path.join(tmp, "knowledge")
        shutil.copytree(KNOWLEDGE, kdir)
        cfg = os.path.join(tmp, "context-budget.json")
        shutil.copy(CONFIG, cfg)
        set_scope(kdir, "ui-archetype-catalog.md", "always")
        args = ["--knowledge-dir", kdir, "--config", cfg, "gate"]
        self.assertEqual(cb.main(args), 1, "growth should fail before it is recorded")
        self.assertEqual(cb.main(args + ["--update-baseline"]), 0)
        self.assertEqual(cb.main(args), 0, "recording the growth should clear the gate")

    def test_the_backstop_bites_even_when_the_growth_is_acknowledged(self):
        """A ratchet alone would let the set grow forever, one acknowledged step at a time.

        The backstop is where the always-on set stops fitting the smallest model tier the
        roster delegates to, so passing it is a decision about which models can still be
        used — not something --update-baseline should be able to wave through.
        """
        def blow_past(kdir, cfgpath):
            for name in ("layered-optimized-architecture.md", "ui-archetype-catalog.md",
                         "agent-body-of-knowledge.md", "persona-audit.md"):
                set_scope(kdir, name, "always")
            with open(cfgpath, encoding="utf-8") as fh:
                raw = fh.read()
            with open(cfgpath, "w", encoding="utf-8") as fh:
                fh.write(raw.replace('"always_on_tokens": 43708',
                                     '"always_on_tokens": 999999'))
        self.assertEqual(self._sandbox(blow_past), 1)

    def test_the_backstop_is_traceable_to_its_stated_derivation(self):
        # A number nobody can derive is a number nobody can argue with, which is how the
        # first ceiling ended up arbitrary. This keeps the two in step.
        with open(CONFIG, encoding="utf-8") as fh:
            cfg = json.load(fh)
        d = cfg["ceiling_derivation"]
        derived = (d["smallest_supported_window"] - d["tool_definition_tokens"]
                   - d["required_working_headroom"])
        self.assertLessEqual(cfg["ceiling_tokens"], derived + 100,
                             "ceiling_tokens has drifted from its stated derivation")
        self.assertLess(cfg["always_on_tokens"], cfg["ceiling_tokens"])

    def test_the_recorded_baseline_matches_the_shipped_tree(self):
        with open(CONFIG, encoding="utf-8") as fh:
            baseline = json.load(fh)["always_on_tokens"]
        total = sum(d["tokens"] for d in cb.always_on(cb.scan(KNOWLEDGE)))
        tolerance = baseline * 0.02
        self.assertLessEqual(abs(total - baseline), tolerance,
                             "the committed baseline no longer reflects the shipped set")


class CorpusResolutionTests(unittest.TestCase):
    """PACK-P — a check must never report a verdict over a corpus it did not establish.

    Found live: run from its deployed location, the script walked up and matched
    `docs/knowledge/` (the research evidence dirs) as a knowledge directory, scanned zero
    docs, and printed a clean gate. A green result over nothing is worse than no gate.
    """

    def test_an_empty_directory_fails_loudly(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertEqual(cb.main(["--knowledge-dir", tmp, "gate"]), 1,
                         "an empty corpus must fail, never report clean")

    def test_a_directory_without_the_manifest_is_not_a_knowledge_dir(self):
        # The discriminator that stops docs/knowledge/ from matching.
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "some-topic"))
        self.assertFalse(cb._is_knowledge_dir(tmp))
        self.assertTrue(cb._is_knowledge_dir(KNOWLEDGE))

    def test_the_deployed_copy_resolves_the_same_corpus_as_the_source(self):
        """The bug was invisible from the source tree and only appeared once installed."""
        deployed = os.path.join(ROOT, "docs", "ai-forward-pack", "scripts", "context-budget.py")
        if not os.path.isfile(deployed):
            self.skipTest("pack not synced to docs/ai-forward-pack/")
        dspec = importlib.util.spec_from_file_location("context_budget_deployed", deployed)
        dcb = importlib.util.module_from_spec(dspec)
        dspec.loader.exec_module(dcb)
        self.assertEqual(len(dcb.scan(dcb.knowledge_dir())), len(cb.scan(cb.knowledge_dir())))


class AgentLensTests(unittest.TestCase):
    """P3 — a sub-agent inherits its lens, not the world."""

    def _agents(self):
        rows = []
        for adir in (CC_AGENTS, COP_AGENTS):
            for name in sorted(os.listdir(adir)):
                if name.endswith(".md"):
                    meta, _ = cb.read_frontmatter(os.path.join(adir, name))
                    rows.append((meta.get("name") or name[:-3], meta))
        return rows

    def test_every_agent_declares_a_knowledge_lens(self):
        missing = [n for n, m in self._agents() if not m.get("knowledge")]
        self.assertEqual(missing, [], "an agent with no lens inherits the whole set")

    def test_every_referenced_doc_exists(self):
        known = {d["name"] for d in cb.scan(KNOWLEDGE)}
        for name, meta in self._agents():
            for doc in meta.get("knowledge") or []:
                self.assertIn(doc, known, f"{name} references a knowledge doc that is gone")

    def test_no_lens_is_wider_than_the_main_threads_always_on_set(self):
        # A sub-agent prefix at or above the main thread's defeats the purpose of delegating.
        base = sum(d["tokens"] for d in cb.always_on(cb.scan(KNOWLEDGE)))
        sizes = {d["name"]: d["tokens"] for d in cb.scan(KNOWLEDGE)}
        for name, meta in self._agents():
            total = sum(sizes.get(d, 0) for d in meta.get("knowledge") or [])
            self.assertLess(total, base, f"{name}'s lens is not narrower than the global set")

    def test_every_agent_carries_the_non_negotiable_core(self):
        # No-guessing and task discipline cannot be looked up on demand: not knowing they
        # apply is the failure they exist to prevent.
        for name, meta in self._agents():
            docs = meta.get("knowledge") or []
            self.assertIn("no-guessing-protocol", docs, f"{name} may guess")
            self.assertIn("communication-and-task-discipline", docs, f"{name} may sprawl")


class PreflightTests(unittest.TestCase):
    """P5 — a wave that cannot fit is refused before it is dispatched, not during."""

    def test_a_wave_that_cannot_fit_is_refused(self):
        # The profiled failure: a flash-class window against a main-thread-sized prefix.
        self.assertEqual(cb.main(["preflight", "--window", "200000",
                                  "--tools", "24070", "--overhead", "141000"]), 1)

    def test_a_narrow_lens_fits_a_small_window(self):
        self.assertEqual(cb.main(["preflight", "--window", "128000",
                                  "--agent", "the-simplifier"]), 0)

    def test_an_unknown_agent_is_an_error_not_a_pass(self):
        # Failing open here would restore the exact silence the gate exists to remove.
        self.assertEqual(cb.main(["preflight", "--window", "200000",
                                  "--agent", "no-such-agent"]), 1)


if __name__ == "__main__":
    unittest.main()
