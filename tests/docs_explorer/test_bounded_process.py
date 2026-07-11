import importlib.util
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "bounded_process.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bounded_process", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BoundedProcessTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def run_python(self, source, **kwargs):
        return self.module.run_bounded([sys.executable, "-c", source], **kwargs)

    def wait_for_pid(self, pid_file, timeout_seconds=10):
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                return int(pid_file.read_text(encoding="utf-8"))
            except (FileNotFoundError, ValueError):
                time.sleep(0.05)
        self.fail("child process did not publish its PID before the readiness deadline")

    def test_success_preserves_unicode_output(self):
        result = self.run_python(
            "import sys; "
            "sys.stdout.buffer.write('café 😀'.encode('utf-8')); "
            "sys.stderr.buffer.write('avertissement'.encode('utf-8'))"
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual("café 😀", result.stdout)
        self.assertEqual("avertissement", result.stderr)
        self.assertFalse(result.timed_out)
        self.assertIsNone(result.limit_exceeded)
        self.assertTrue(result.contained)
        self.assertEqual(
            "windows-job" if os.name == "nt" else "posix-process-group-rlimit-as",
            result.containment_mode,
        )
        self.assertEqual(os.name == "nt", result.process_limit_enforced)
        self.assertEqual(os.name == "nt", result.aggregate_memory_limit_enforced)

    def test_exact_stdout_limit_succeeds(self):
        limit = 1024 * 1024

        result = self.run_python(
            "import sys; sys.stdout.buffer.write(b'x' * (1024 * 1024))",
            stdout_limit=limit,
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual(limit, len(result.stdout))
        self.assertIsNone(result.limit_exceeded)

    def test_stdout_limit_failure_discards_stdout(self):
        result = self.run_python(
            "import sys; sys.stdout.buffer.write(b'x' * 65)",
            stdout_limit=64,
        )

        self.assertEqual("stdout", result.limit_exceeded)
        self.assertEqual("", result.stdout)

    def test_stdout_limit_terminates_writer_before_deadline(self):
        result = self.run_python(
            "import sys,time; sys.stdout.buffer.write(b'x' * 65); sys.stdout.flush(); time.sleep(30)",
            timeout_seconds=5,
            stdout_limit=64,
        )

        self.assertEqual("stdout", result.limit_exceeded)
        self.assertFalse(result.timed_out)

    def test_windows_gate_write_failure_is_reported_without_raising(self):
        process = mock.Mock()
        process.stdin.write.side_effect = BrokenPipeError()

        error = self.module._release_windows_gate(process)

        self.assertEqual("Windows launch gate failed (BrokenPipeError)", error)
        process.stdin.close.assert_called()

    def test_stderr_limit_failure_discards_stdout(self):
        result = self.run_python(
            "import sys; "
            "sys.stdout.write('must-discard'); sys.stdout.flush(); "
            "sys.stderr.buffer.write(b'e' * 65)",
            stderr_limit=64,
        )

        self.assertEqual("stderr", result.limit_exceeded)
        self.assertEqual("", result.stdout)

    def test_nonzero_exit_discards_stdout_and_preserves_stderr(self):
        result = self.run_python(
            "import sys; print('must-discard'); "
            "sys.stderr.write('failure detail'); sys.exit(7)"
        )

        self.assertEqual(7, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("failure detail", result.stderr)

    def test_timeout_discards_stdout(self):
        result = self.run_python(
            "import sys,time; print('must-discard', flush=True); time.sleep(30)",
            timeout_seconds=0.1,
        )

        self.assertTrue(result.timed_out)
        self.assertEqual("", result.stdout)

    def test_stdout_and_stderr_are_drained_concurrently(self):
        result = self.run_python(
            "import sys; "
            "[(sys.stdout.buffer.write(b'o' * 4096), "
            "sys.stderr.buffer.write(b'e' * 1024), "
            "sys.stdout.flush(), sys.stderr.flush()) for _ in range(64)]",
            stdout_limit=300000,
            stderr_limit=100000,
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual(64 * 4096, len(result.stdout))
        self.assertEqual(64 * 1024, len(result.stderr))

    def test_second_wait_timeout_returns_bounded_failure(self):
        process = mock.Mock()
        process.wait.side_effect = [
            subprocess.TimeoutExpired("fixture", 2),
            subprocess.TimeoutExpired("fixture", 2),
        ]

        with mock.patch.object(self.module, "_terminate_tree"):
            returncode, error = self.module._wait_after_termination(process)

        self.assertEqual(-9, returncode)
        self.assertIn("did not terminate", error)

    def test_windows_taskkill_fallback_has_a_cleanup_deadline(self):
        process = mock.Mock(pid=123)
        with mock.patch.object(self.module.os, "name", "nt"), mock.patch.object(
            self.module.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("taskkill", 2),
        ) as run:
            error = self.module._terminate_tree(process)

        self.assertIn("2-second cleanup deadline", error)
        self.assertEqual(2, run.call_args.kwargs["timeout"])

    def test_cleanup_failure_is_classified_and_invalidates_containment(self):
        with mock.patch.object(
            self.module, "_terminate_tree", return_value="synthetic cleanup failure"
        ):
            result = self.run_python(
                "import sys; sys.stdout.buffer.write(b'x' * 65)",
                stdout_limit=64,
            )

        self.assertEqual("stdout", result.limit_exceeded)
        self.assertFalse(result.contained)
        self.assertEqual("synthetic cleanup failure", result.cleanup_error)
        self.assertIn("PROCESS_CLEANUP_FAILED", result.stderr)

    def test_timeout_and_output_limit_share_one_termination_attempt(self):
        entered = threading.Event()
        release = threading.Event()
        calls = []
        result_holder = []
        real_termination = self.module._terminate_tree

        def synthetic_termination(process, windows_job=None):
            calls.append(process.pid)
            entered.set()
            release.wait(timeout=10)
            return real_termination(process, windows_job)

        def invoke():
            result_holder.append(
                self.run_python(
                    "import sys,time; "
                    "sys.stdout.buffer.write(b'x' * 65); sys.stdout.flush(); "
                    "time.sleep(30)",
                    timeout_seconds=0.01,
                    stdout_limit=64,
                )
            )

        with mock.patch.object(
            self.module, "_terminate_tree", side_effect=synthetic_termination
        ):
            runner = threading.Thread(target=invoke)
            runner.start()
            self.assertTrue(entered.wait(timeout=10))
            time.sleep(0.05)
            release.set()
            runner.join(timeout=15)

        self.assertFalse(runner.is_alive())
        self.assertEqual(1, len(calls))
        self.assertIsNone(result_holder[0].cleanup_error)

    @unittest.skipUnless(os.name == "nt", "Windows gated-launch contract")
    def test_requested_command_starts_only_after_job_assignment(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "started.txt"
            module = self.module

            class InspectingJob:
                def __init__(self, process, memory_limit, process_limit):
                    self.handle = 1
                    self.error = None
                    self.memory_limit = memory_limit
                    self.process_limit = process_limit
                    if marker.exists():
                        raise AssertionError("requested command started before job assignment")

                def terminate(self):
                    return None

                def close(self):
                    self.handle = None

            with mock.patch.object(module, "_WindowsJob", InspectingJob):
                result = module.run_bounded(
                    [
                        sys.executable,
                        "-c",
                        f"from pathlib import Path; Path({str(marker)!r}).write_text('started')",
                    ]
                )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("started", marker.read_text(encoding="utf-8"))

    @unittest.skipUnless(os.name == "nt", "Windows process-tree contract")
    def test_timeout_terminates_spawned_child_process(self):
        with tempfile.TemporaryDirectory() as temp:
            pid_file = Path(temp) / "child.pid"
            child_source = "import time; time.sleep(30)"
            parent_source = (
                "import pathlib,subprocess,sys,time; "
                f"p=subprocess.Popen([sys.executable,'-c',{child_source!r}]); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
                "time.sleep(30)"
            )

            result = self.run_python(parent_source, timeout_seconds=15)

            self.assertTrue(result.timed_out)
            child_pid = self.wait_for_pid(pid_file)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and self._process_exists(child_pid):
                time.sleep(0.05)
            self.assertFalse(self._process_exists(child_pid))

    @unittest.skipUnless(os.name == "nt", "Windows process-tree contract")
    def test_timeout_terminates_child_after_parent_exits(self):
        with tempfile.TemporaryDirectory() as temp:
            pid_file = Path(temp) / "child.pid"
            child_source = "import time; time.sleep(30)"
            parent_source = (
                "import pathlib,subprocess,sys; "
                f"p=subprocess.Popen([sys.executable,'-c',{child_source!r}]); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid))"
            )
            result = self.run_python(parent_source, timeout_seconds=15)

            self.assertTrue(result.timed_out)
            child_pid = self.wait_for_pid(pid_file)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and self._process_exists(child_pid):
                time.sleep(0.05)
            self.assertFalse(self._process_exists(child_pid))

    @unittest.skipUnless(os.name == "nt", "Windows Job Object memory contract")
    def test_windows_job_enforces_memory_limit(self):
        result = self.run_python(
            "payload = bytearray(256 * 1024 * 1024); print(len(payload))",
            timeout_seconds=15,
            memory_limit=96 * 1024 * 1024,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertFalse(result.timed_out)
        self.assertTrue(result.contained)
        self.assertIsNone(result.containment_error)
        self.assertIsNone(result.cleanup_error)
        self.assertIn("MemoryError", result.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows Job Object process-count contract")
    def test_windows_job_enforces_process_limit(self):
        result = self.run_python(
            "import sys; sys.exit(0)",
            timeout_seconds=5,
            process_limit=1,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertFalse(result.timed_out)
        self.assertTrue(result.contained)
        self.assertIsNone(result.containment_error)
        self.assertIsNone(result.cleanup_error)
        self.assertIn("Not enough quota", result.stderr)

    @staticmethod
    def _process_exists(pid):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0


if __name__ == "__main__":
    unittest.main()
