"""FR-099: a test that needs what this machine lacks is SKIPPED with the reason, never failed.

Two capabilities are environmental, not code: creating a file symlink (Windows grants it only
with Developer Mode or SeCreateSymbolicLinkPrivilege, WinError 1314 otherwise) and a POSIX `sh`
on PATH (Git Bash provides one on Windows). A red gate made of known environmental failures hides
a real new one, so conftest installs these guards for the whole suite. Only those two causes turn
into a skip; every other error is raised unchanged.

Each skip is also the error its caller expects (OSError / FileNotFoundError), so code under test
that handles the failure itself still sees it.
"""
import os
import shutil
import subprocess
import unittest

NO_SYMLINK_PRIVILEGE = 1314
POSIX_SHELLS = ("sh", "bash")


class NoSymlinkPrivilege(OSError, unittest.SkipTest):
    """Skip: this process may not create symlinks here (WinError 1314)."""


class NoPosixShell(FileNotFoundError, unittest.SkipTest):
    """Skip: the test launches a POSIX shell and none is on PATH."""


def guard_symlink(symlink):
    def guarded(*args, **kwargs):
        try:
            return symlink(*args, **kwargs)
        except OSError as exc:
            if getattr(exc, "winerror", None) == NO_SYMLINK_PRIVILEGE:
                raise NoSymlinkPrivilege(exc.errno, "no symlink privilege (WinError 1314): enable "
                                         "Developer Mode to run this test") from exc
            raise
    guarded.__wrapped__ = symlink
    return guarded


def _program(args):
    if isinstance(args, (str, bytes, os.PathLike)):
        return None   # a command string runs through a shell the test chose; not ours to judge
    first = next(iter(args), None)
    return os.path.basename(os.fsdecode(first)) if first is not None else None


def guard_popen(popen, which=shutil.which):
    class GuardedPopen(popen):
        def __init__(self, args, *rest, **kwargs):
            try:
                super().__init__(args, *rest, **kwargs)
            except FileNotFoundError as exc:
                program = _program(args)
                if program in POSIX_SHELLS and which(program) is None:
                    raise NoPosixShell(exc.errno, "no POSIX {!r} on PATH: install Git Bash or run "
                                       "on a POSIX host to run this test".format(program)) from exc
                raise
    GuardedPopen.__name__ = popen.__name__
    return GuardedPopen


def install():
    """Install both guards; return a function that removes them."""
    original_symlink, original_popen = os.symlink, subprocess.Popen
    os.symlink = guard_symlink(original_symlink)
    subprocess.Popen = guard_popen(original_popen)

    def restore():
        os.symlink, subprocess.Popen = original_symlink, original_popen
    return restore
