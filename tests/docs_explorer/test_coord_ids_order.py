"""ID-A: a time-ordered id is a total order within one process, for every prefix the pack mints.

Design: docs/design/typed-seam-requests.md §2.5. Written to fail first: on the un-fixed
coord_ids.new_id two ids minted in one millisecond order by their random part.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "pack" / "scripts"
PREFIXES = ("req", "mail", "al", "cl", "wt")
BURST = 1000


def load_ids():
    spec = importlib.util.spec_from_file_location("coord_ids_under_test", SCRIPTS / "coord_ids.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdOrderTests(unittest.TestCase):
    def setUp(self):
        self.ids = load_ids()

    def test_T9_a_burst_of_1000_per_prefix_is_strictly_ordered_and_unique(self):
        for prefix in PREFIXES:
            minted = [self.ids.new_id(prefix) for _ in range(BURST)]
            self.assertEqual(BURST, len(set(minted)), prefix)
            for earlier, later in zip(minted, minted[1:]):
                self.assertLess(earlier, later, "{}: {} !< {}".format(prefix, earlier, later))

    def test_T9b_a_frozen_clock_still_yields_a_strict_order(self):
        with mock.patch.object(self.ids.time, "time", return_value=1_700_000_000.0):
            minted = [self.ids.new_id("req") for _ in range(50)]
        self.assertEqual(sorted(minted), minted)
        self.assertEqual(50, len(set(minted)))
        for earlier, later in zip(minted, minted[1:]):
            self.assertLess(earlier, later)

    def test_T9c_an_explicit_stamp_is_honoured_as_given(self):
        # 48 bits of stamp = the first 9 base32 characters and part of the 10th.
        a, b = self.ids.new_id("mail", ts_ms=1_000), self.ids.new_id("mail", ts_ms=1_000)
        self.assertEqual(a[5:14], b[5:14])
        self.assertLess(self.ids.new_id("mail", ts_ms=1_000), self.ids.new_id("mail", ts_ms=2_000))

    def test_T9d_every_pack_minter_goes_through_new_id(self):
        core = (SCRIPTS / "coord-core.py").read_text(encoding="utf-8")
        mail = (SCRIPTS / "coord-mail.py").read_text(encoding="utf-8")
        audit = (SCRIPTS / "audit-log.py").read_text(encoding="utf-8")
        self.assertIn('new_id("req"', core)
        self.assertIn('new_id("mail"', mail)
        self.assertIn("from coord_ids import new_id", audit)
        for text, name in ((core, "coord-core.py"), (mail, "coord-mail.py")):
            self.assertFalse("import uuid" in text, "{} mints outside coord_ids".format(name))


if __name__ == "__main__":
    unittest.main()
