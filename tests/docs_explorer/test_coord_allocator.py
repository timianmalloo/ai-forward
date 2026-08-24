"""Tests for coord-core.py Phase 3 — the collision-proof allocator and register merges.

Design: docs/design/coord-federation-phase3.md (test plan Q1..Q5, Q17).

Q3 leads, and is written to fail first. It is the one that matters most, because unique ids
alone would NOT have caught the recorded instance. KG-B occurrence one: two branches minted
`al-0203` independently, the conflict was resolved by deduping on the id, the resolver
reported "203 ours + 203 theirs -> 203 unique", and one entry ceased to exist. It was caught
only because a union of 203 and 203 producing 203 is arithmetically impossible, and somebody
checked that number.

So the id scheme stops the COLLISION; only a conservation assertion stops the RESOLUTION
from destroying an entry. Both are needed, and this file proves the second.

The fingerprint deliberately EXCLUDES the id: in the recorded instance the two entries had
the same id and different content, and the register's own write-up names them by
`shortname` rather than by id precisely because ids get renumbered by rebases.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"

CONFLICT_START = "<" * 7


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def entry(eid, shortname, **extra):
    row = {"id": eid, "shortname": shortname, "datetime": "2026-08-23T10:00:00Z"}
    row.update(extra)
    return row


class AllocatorCase(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def jsonl(self, name, rows):
        p = self.dir / name
        p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                     encoding="utf-8", newline="\n")
        return p


# ------------------------------------------------------- Q3: conservation

class RegisterMergeTests(AllocatorCase):
    def test_Q3_merge_losing_an_entry_fails_closed(self):
        """Q3 / H2. The recorded KG-B resolution, reconstructed exactly.

        Two branches each minted `al-0203` for DIFFERENT work. Deduping on the id keeps one
        and destroys the other, while reporting a plausible count. The conservation
        assertion is what refuses that.
        """
        ours = [entry("al-0202", "earlier-work"), entry("al-0203", "ui-design-ask-ai-sharing")]
        theirs = [entry("al-0202", "earlier-work"), entry("al-0203", "reread-ask-ai-output-shape")]

        # The resolution that actually happened: dedupe by id, keep one.
        by_id = {}
        for row in ours + theirs:
            by_id[row["id"]] = row
        naive = list(by_id.values())
        self.assertEqual(len(naive), 2, "precondition: the naive resolution looks plausible")

        lost = self.m.conservation_lost(ours, theirs, naive)

        self.assertTrue(lost, "a resolution that destroyed an entry was reported conserved")
        self.assertEqual(len(lost), 1)
        self.assertIn("ask-ai", json.dumps(lost), "the lost entry was not identified")

    def test_Q3b_correct_union_conserves(self):
        ours = [entry("al-0202", "a"), entry("al-0203", "b")]
        theirs = [entry("al-0202", "a"), entry("al-0203", "c")]
        merged, lost = self.m.merge_register(ours, theirs)
        self.assertEqual(lost, [], "a correct union reported a loss")
        self.assertEqual(len(merged), 3, "the union of 2 and 2 sharing 1 entry is 3")
        self.assertEqual(len({json.dumps(r, sort_keys=True) for r in merged}), 3)

    def test_Q3c_conservation_ignores_the_id_because_ids_get_renumbered(self):
        """The register's own write-up names the lost entries by shortname, not by id,
        because a rebase renumbered their ids three times. A fingerprint keyed on the id
        would therefore report a loss for every legitimate renumber."""
        ours = [entry("al-0203", "same-work")]
        theirs = [entry("al-0999", "same-work")]     # same entry, renumbered
        merged, lost = self.m.merge_register(ours, theirs)
        self.assertEqual(lost, [])
        self.assertEqual(len(merged), 1, "a renumbered duplicate was kept twice")

    def test_Q3d_register_driver_writes_the_union_and_exits_zero(self):
        ours = self.jsonl("ours.jsonl", [entry("al-1", "a"), entry("al-2", "b")])
        base = self.jsonl("base.jsonl", [entry("al-1", "a")])
        theirs = self.jsonl("theirs.jsonl", [entry("al-1", "a"), entry("al-2", "c")])
        rc = self.m.cmd_merge_register(str(ours), str(base), str(theirs), "audit-log.jsonl")
        self.assertEqual(rc, 0)
        rows = [json.loads(l) for l in ours.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(rows), 3, "the register driver did not union both sides")

    def test_Q3f_an_incoming_duplicate_id_is_renumbered_not_left_ambiguous(self):
        """KG-B's own prescribed resolution: *the id is a sequence, not an identity.* The
        merged side is authoritative for every id it already holds, and the incoming entry
        is renumbered to a free id rather than deduped away.

        Conservation alone leaves two entries sharing one id -- nothing is lost, but the id
        is permanently ambiguous. The base (%O) is what distinguishes an already-published
        id from one this merge is introducing, so NFR-C2 still holds: nothing already in
        the base is ever rewritten.
        """
        base = [entry("al-0202", "earlier")]
        ours = base + [entry("al-0203", "reread-ask-ai-output-shape")]
        theirs = base + [entry("al-0203", "ui-design-ask-ai-sharing")]

        merged, lost = self.m.merge_register(ours, theirs, base=base)

        self.assertEqual(lost, [], "an entry was destroyed")
        self.assertEqual(len(merged), 3)
        by_name = {r["shortname"]: r["id"] for r in merged}
        self.assertEqual(by_name["al-0202" and "earlier"], "al-0202",
                         "an id already in the base was rewritten")
        self.assertEqual(by_name["reread-ask-ai-output-shape"], "al-0203",
                         "the side that already held the id lost it")
        self.assertNotEqual(by_name["ui-design-ask-ai-sharing"], "al-0203",
                            "the incoming duplicate was left sharing the id")
        self.assertEqual(len({r["id"] for r in merged}), 3, "ids are not unique after merge")

    def test_Q3g_renumbering_only_applies_to_ids_the_merge_introduces(self):
        """Without a base the driver cannot tell which side published first, so it must
        conserve and NOT guess which id to rewrite."""
        ours = [entry("al-0203", "a")]
        theirs = [entry("al-0203", "b")]
        merged, lost = self.m.merge_register(ours, theirs)
        self.assertEqual(lost, [])
        self.assertEqual(len(merged), 2, "an entry was destroyed")
        self.assertEqual([r["id"] for r in merged], ["al-0203", "al-0203"],
                         "an id was rewritten with no base to justify it")

    def test_Q3e_unparseable_side_conflicts_rather_than_guessing(self):
        """A register the driver cannot read must not be 'merged' -- guessing here is how
        an entry disappears. Conflict markers, exit 0 (the S12b rule)."""
        ours = self.jsonl("ours.jsonl", [entry("al-1", "a")])
        base = self.jsonl("base.jsonl", [])
        theirs = self.dir / "theirs.jsonl"
        theirs.write_text("{not json\n", encoding="utf-8", newline="\n")
        rc = self.m.cmd_merge_register(str(ours), str(base), str(theirs), "audit-log.jsonl")
        self.assertEqual(rc, 0, "a non-zero exit leaves a clean-looking unmerged file")
        self.assertIn(CONFLICT_START, ours.read_text(encoding="utf-8"))


# --------------------------------------------------------- Q1: the allocator

class AllocatorTests(AllocatorCase):
    def test_Q1_burst_asserts_ids_were_actually_issued_then_uniqueness(self):
        """Q1 / H1 / R4. The corpus assertion comes FIRST.

        The architecture's own allocator spike printed "COLLISION-FREE" over zero ids
        because it only compared set size to list size. That is PACK-P, and this test is
        written so it cannot repeat: the count is asserted before uniqueness is judged.

        The condition is the one that defeated the 22-branch scanner: separate processes,
        the same millisecond, no shared state, no network.
        """
        worker = self.dir / "burst.py"
        worker.write_text(
            "import importlib.util, sys, time\n"
            "spec = importlib.util.spec_from_file_location('c', r'{}')\n"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "target = int(sys.argv[1])\n"
            "while int(time.time() * 1000) < target:\n"
            "    pass\n"
            "for _ in range(250):\n"
            "    print(m.new_id('al', target))\n".format(SCRIPT),
            encoding="utf-8", newline="\n")
        import time as _t
        at = int(_t.time() * 1000) + 500
        procs = [subprocess.Popen([sys.executable, str(worker), str(at)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                 for _ in range(6)]
        out = [p.communicate() for p in procs]
        for _o, err in out:
            self.assertEqual(err.decode().strip(), "", "a burst worker failed")
        ids = [x for o, _e in out for x in o.decode().split()]

        self.assertEqual(len(ids), 1500,
                         "the corpus was not the size this check assumes -- verdict withheld")
        self.assertEqual(len(set(ids)), len(ids), "ids collided without coordination")

    def test_ids_are_time_ordered_and_prefixed(self):
        early = self.m.new_id("al", 1_000_000_000_000)
        later = self.m.new_id("al", 1_000_000_000_001)
        self.assertTrue(early.startswith("al-"))
        self.assertLess(early, later, "ids are not lexicographically time-ordered")
        self.assertEqual(len(early), len(later))

    def test_Q2_existing_ids_are_never_rewritten(self):
        """Q2 / NFR-C2. Expand-migrate-contract: nothing is renumbered, so nothing is
        guessed. There is no backfill at all, and that is the point."""
        rows = [entry("al-0001", "old"), entry("al-0002", "older")]
        before = [r["id"] for r in rows]
        rows.append(entry(self.m.new_id("al"), "new"))
        self.assertEqual([r["id"] for r in rows][:2], before)
        self.assertTrue(rows[-1]["id"].startswith("al-"))
        self.assertNotEqual(len(rows[-1]["id"]), len("al-0001"),
                            "the new id took the old sequential shape")


# ----------------------------------------------------- Q4/Q5: prefix recall

class PrefixResolutionTests(AllocatorCase):
    def test_Q4_prefix_resolution_is_unique_or_refuses(self):
        """Q4 / H9. The git short-hash idiom. It never picks the first match."""
        rows = [entry("al-01ABCDEF", "a"), entry("al-01ABCXYZ", "b"), entry("al-0001", "old")]
        status, result, corpus = self.m.resolve_prefix(rows, "al-01ABCD")
        self.assertEqual(status, "unique")
        self.assertEqual(result["shortname"], "a")

        status, result, corpus = self.m.resolve_prefix(rows, "al-01ABC")
        self.assertEqual(status, "ambiguous")
        self.assertEqual(len(result), 2, "an ambiguous prefix must list every candidate")

    def test_Q5_prefix_nomatch_reports_corpus_size(self):
        """Q5 / H10 / R4. 'Not found' over an empty corpus is not a result."""
        status, result, corpus = self.m.resolve_prefix([], "al-01")
        self.assertEqual(status, "nomatch")
        self.assertEqual(corpus, 0)

        status, result, corpus = self.m.resolve_prefix([entry("al-0001", "x")], "al-99")
        self.assertEqual(status, "nomatch")
        self.assertEqual(corpus, 1)

    def test_exact_id_still_resolves(self):
        rows = [entry("al-0064", "legacy")]
        status, result, _ = self.m.resolve_prefix(rows, "al-0064")
        self.assertEqual(status, "unique")
        self.assertEqual(result["shortname"], "legacy")


# ------------------------------------------------------------------ the CLI

class AllocatorCliTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        (self.repo / ".agents").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)

    def run_cli(self, *args):
        env = dict(os.environ)
        env.pop("COORD_ROOT", None)
        env["AGENT_SESSION"] = "s1"; env["AGENT_NAME"] = "s1"
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(self.repo),
                              env=env, capture_output=True, text=True)

    def test_allocate_prints_one_id_and_exits_zero(self):
        r = self.run_cli("allocate", "--scheme", "al")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        got = r.stdout.strip()
        self.assertTrue(got.startswith("al-"))
        self.assertNotEqual(got, self.run_cli("allocate", "--scheme", "al").stdout.strip())

    def test_resolve_exit_codes_are_the_contract(self):
        register = self.repo / "reg.jsonl"
        register.write_text(
            json.dumps(entry("al-01ABCDEF", "a")) + "\n" +
            json.dumps(entry("al-01ABCXYZ", "b")) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(self.run_cli("resolve", "--register", str(register),
                                      "al-01ABCD").returncode, 0)
        ambiguous = self.run_cli("resolve", "--register", str(register), "al-01ABC")
        self.assertEqual(ambiguous.returncode, 3)
        self.assertIn("al-01ABCDEF", ambiguous.stdout)
        self.assertIn("al-01ABCXYZ", ambiguous.stdout)
        nomatch = self.run_cli("resolve", "--register", str(register), "al-zz")
        self.assertEqual(nomatch.returncode, 4)
        self.assertIn("2", nomatch.stdout, "nomatch must report the corpus size")


if __name__ == "__main__":
    unittest.main()
