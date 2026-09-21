"""Public immutable-control contracts; no model credentials or network."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "pack/scripts/coord_runtime.py"


def module():
    spec = importlib.util.spec_from_file_location("coord_runtime", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@unittest.skipUnless(os.name == "posix", "The runtime uses POSIX containment and locking")
class RuntimeControls(unittest.TestCase):
    def setUp(self):
        self.api = module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name).resolve() / "controls"
        self.box = self.api.Controls(self.path)

    def test_enqueue_consume_close_preserves_append_only_order(self):
        first = self.box.enqueue("al-first", "abc", 2)
        second = self.box.enqueue("al-second", "def", 2)
        self.box.finish()
        self.assertEqual(first, self.box.next_prompt())
        self.box.dispatched(first["id"])
        self.assertEqual(second, self.box.next_prompt())
        self.box.dispatched(second["id"])
        self.assertIs(self.box.next_prompt(), False)
        self.assertEqual(["prompt", "prompt", "finish", "dispatch", "dispatch"],
                         [r["kind"] for r in self.box.records()])
        with self.assertRaises(ValueError):
            self.box.dispatched(first["id"])
        with self.assertRaises(ValueError):
            self.box.enqueue("al-third", "ghi", 3)

    def test_duplicate_and_capacity_are_not_extra_prompts(self):
        self.box.enqueue("al-first", "abc", 1)
        for audit in ("al-first", "al-other"):
            with self.subTest(audit=audit), self.assertRaises(ValueError):
                self.box.enqueue(audit, "abc", 1)
        self.assertEqual(1, len(self.box.records()))

    def request(self):
        return {"sessionId": "native-one", "requestId": 7,
                "toolCall": {"title": "SECRET native action", "rawInput": {"path": "SECRET"}},
                "options": [{"optionId": "yes", "kind": "allow_once", "name": "Allow once"},
                            {"optionId": "no", "kind": "reject_once", "name": "Reject"},
                            {"optionId": "always", "kind": "allow_always", "name": "Always"}]}

    def test_permission_binds_request_options_expiry_and_one_decision(self):
        request = self.box.permission(self.request(), expires_at=200)
        self.assertIsNone(self.box.answer(request["id"], now=100))
        for option in ("unknown", "always"):
            with self.subTest(option=option), self.assertRaises(ValueError):
                self.box.decide(request["id"], option, now=100)
        self.box.decide(request["id"], "yes", now=100)
        self.assertEqual("yes", self.box.answer(request["id"], now=100))
        with self.assertRaises(ValueError):
            self.box.decide(request["id"], "no", now=100)
        self.assertEqual([], self.box.pending(now=100))
        other = self.box.permission(self.request(), expires_at=200)
        with self.assertRaises(ValueError):
            self.box.decide(other["id"], "yes", now=201)
        self.assertEqual("expired", self.box.pending(now=201)[0]["state"])

    def test_tampered_missing_symlink_and_oversize_records_fail_closed(self):
        self.box.enqueue("al-first", "abc", 2)
        path = next(self.path.glob("*.json"))
        original = path.read_bytes()
        row = json.loads(original)
        row["compilation_id"] = "al-forged"
        path.write_text(json.dumps(row))
        with self.assertRaises(ValueError):
            self.box.records()
        path.write_bytes(original)
        self.box.enqueue("al-second", "def", 2)
        path.unlink()
        with self.assertRaises((ValueError, OSError)):
            self.box.records()
        path.symlink_to(self.path / "missing")
        with self.assertRaises((ValueError, OSError)):
            self.box.records()

    def test_oversize_native_request_is_not_published(self):
        request = self.request()
        request["toolCall"]["title"] = "x" * self.api.MAX_RECORD_BYTES
        with self.assertRaises(ValueError):
            self.box.permission(request, expires_at=200)
        self.assertEqual([], self.box.records())

    def test_concurrent_writers_have_unique_ordered_records(self):
        def enqueue(index):
            return self.api.Controls(self.path).enqueue("al-" + str(index), "abc", 8)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            result = list(pool.map(enqueue, range(8)))
        self.assertEqual(8, len({r["id"] for r in result}))
        self.assertEqual(list(range(1, 9)), [r["sequence"] for r in self.box.records()])

    def test_private_files_and_no_replace_of_preexisting_symlink_directory(self):
        self.box.enqueue("al-first", "abc", 2)
        self.assertEqual(0o700, self.path.stat().st_mode & 0o777)
        for path in self.path.iterdir():
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
        link = self.path.parent / "link"
        link.symlink_to(self.path, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.api.Controls(link).records()

    def test_fifo_record_is_rejected_without_waiting_for_a_writer(self):
        self.box.records()
        os.mkfifo(self.path / "000001.json", 0o600)
        process = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                  "--read-controls", str(self.path)], capture_output=True, timeout=2)
        self.assertNotEqual(0, process.returncode)
        self.assertIn(b"invalid_runtime_control", process.stderr)

    def test_another_process_holding_lock_cannot_suspend_deadline_forever(self):
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                    "--hold-lock", str(self.path)], stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertEqual(b"locked\n", process.stdout.readline())
            started = time.monotonic()
            with self.assertRaises(ValueError):
                self.box.records()
            self.assertLess(time.monotonic() - started, .5)
        finally:
            process.communicate(input=b"release", timeout=2)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--read-controls":
        module().Controls(Path(sys.argv[2])).records()
    elif len(sys.argv) == 3 and sys.argv[1] == "--hold-lock":
        with module().Controls(Path(sys.argv[2])).locked():
            print("locked", flush=True)
            sys.stdin.read()
    else:
        unittest.main()
