"""P1/P2/P3/P5 — the always-on context budget is declared, measured, and gated.

An instruction set attached to every request IS the static prefix of every model call. In
the session that motivated this, 37 of 39 knowledge docs shipped with `applyTo: "**"`,
making a 184K-token corpus the prefix of all 484 calls — 63% of every input token spent
re-reading the same text, and a ceiling that failed 27 of 39 delegated runs outright.

The failure mode is not that the docs are wrong. It is that nothing reported what they
cost, so each new one looked free. These tests pin the three properties that keep it from
re-growing: every doc DECLARES its scope, the always-on total is GATED, and every agent
declares the lens it actually needs instead of inheriting the world.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "pack", "scripts", "context-budget.py")
KNOWLEDGE = os.path.join(ROOT, "pack", "knowledge")
CC_AGENTS = os.path.join(ROOT, "pack", "adapters", "claude-code", "agents")
COP_AGENTS = os.path.join(ROOT, "pack", "adapters", "copilot", "agents")

spec = importlib.util.spec_from_file_location("context_budget", SCRIPT)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

# The ceiling verify-bundle.ps1 and pack-consistency.yml enforce. Kept here so a change to
# one without the other fails a test rather than drifting silently.
CEILING = 45000


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


class BudgetGateTests(unittest.TestCase):
    """P2 — the always-on total fails closed."""

    def test_always_on_set_is_under_the_ceiling(self):
        total = sum(d["tokens"] for d in cb.always_on(cb.scan(KNOWLEDGE)))
        self.assertLessEqual(total, CEILING,
                             "always-on knowledge is over the declared ceiling; scope a doc "
                             "out of Tier A or raise the ceiling deliberately")

    def test_gate_fails_when_a_doc_loses_its_declaration(self):
        """The control, observed failing on the shape it exists to catch.

        This is the regression that matters: a doc added or edited without a `load:` line
        silently rejoins the always-on set in some readers and vanishes in others.
        """
        tmp = tempfile.mkdtemp()
        try:
            copy = os.path.join(tmp, "knowledge")
            shutil.copytree(KNOWLEDGE, copy)
            victim = os.path.join(copy, "rigor-protocol.md")
            with open(victim, encoding="utf-8") as fh:
                body = fh.read().split("---\n", 2)[-1]
            with open(victim, "w", encoding="utf-8") as fh:
                fh.write(body)
            args = cb.main(["--knowledge-dir", copy, "gate", "--ceiling", str(CEILING)])
            self.assertEqual(args, 1, "gate passed a doc with no declared load scope")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_gate_fails_when_the_always_on_set_grows_past_the_ceiling(self):
        tmp = tempfile.mkdtemp()
        try:
            copy = os.path.join(tmp, "knowledge")
            shutil.copytree(KNOWLEDGE, copy)
            # Promote the largest reference doc back to always-on — the exact regression
            # that produced the 184K prefix, one doc at a time.
            victim = os.path.join(copy, "layered-optimized-architecture.md")
            with open(victim, encoding="utf-8") as fh:
                body = fh.read().split("---\n", 2)[-1]
            with open(victim, "w", encoding="utf-8") as fh:
                fh.write("---\nload: always\n---\n" + body)
            self.assertEqual(cb.main(["--knowledge-dir", copy, "gate",
                                      "--ceiling", str(CEILING)]), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_gate_passes_on_the_shipped_tree(self):
        self.assertEqual(cb.main(["gate", "--ceiling", str(CEILING)]), 0)


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
