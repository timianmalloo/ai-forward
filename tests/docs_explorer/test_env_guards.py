"""FR-099: the environment guards skip only for the two named causes, and raise everything else."""
import errno
import subprocess
import sys
import unittest

import env_guards


def raising(exc):
    def fn(*args, **kwargs):
        raise exc
    return fn


def win_error(code):
    exc = OSError(errno.EPERM, "A required privilege is not held by the client")
    exc.winerror = code
    return exc


class SymlinkGuardTests(unittest.TestCase):
    def test_missing_privilege_is_a_skip_that_is_still_an_oserror(self):
        guarded = env_guards.guard_symlink(raising(win_error(1314)))
        with self.assertRaises(unittest.SkipTest) as caught:
            guarded("target", "link")
        self.assertIsInstance(caught.exception, OSError)
        self.assertIn("Developer Mode", str(caught.exception))

    def test_any_other_symlink_error_is_raised_unchanged(self):
        for exc in (win_error(5), FileExistsError(errno.EEXIST, "exists")):
            with self.subTest(exc=exc):
                with self.assertRaises(OSError) as caught:
                    env_guards.guard_symlink(raising(exc))("target", "link")
                self.assertNotIsInstance(caught.exception, unittest.SkipTest)


class PosixShellGuardTests(unittest.TestCase):
    class Missing(subprocess.Popen):
        def __init__(self, args, *rest, **kwargs):
            raise FileNotFoundError(errno.ENOENT, "not found", args[0] if isinstance(args, list) else args)

    def test_a_missing_sh_is_a_skip(self):
        popen = env_guards.guard_popen(self.Missing, which=lambda name: None)
        with self.assertRaises(unittest.SkipTest) as caught:
            popen(["sh", "-c", "true"])
        self.assertIsInstance(caught.exception, FileNotFoundError)

    def test_a_missing_program_that_is_not_a_shell_still_fails(self):
        popen = env_guards.guard_popen(self.Missing, which=lambda name: None)
        for args in (["no-such-tool"], "sh -c true"):
            with self.subTest(args=args):
                with self.assertRaises(FileNotFoundError) as caught:
                    popen(args)
                self.assertNotIsInstance(caught.exception, unittest.SkipTest)

    def test_sh_present_but_failing_to_start_still_fails(self):
        popen = env_guards.guard_popen(self.Missing, which=lambda name: "/bin/sh")
        with self.assertRaises(FileNotFoundError) as caught:
            popen(["sh", "-c", "true"])
        self.assertNotIsInstance(caught.exception, unittest.SkipTest)

    def test_the_suite_runs_with_both_guards_installed(self):
        self.assertTrue(hasattr(__import__("os").symlink, "__wrapped__"))
        self.assertTrue(subprocess.Popen.__qualname__.endswith("GuardedPopen"))
        self.assertEqual(0, subprocess.run([sys.executable, "-c", "pass"]).returncode)


if __name__ == "__main__":
    unittest.main()
