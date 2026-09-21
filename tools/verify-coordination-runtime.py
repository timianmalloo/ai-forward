#!/usr/bin/env python3
"""Credential-free, fresh-clone proof for coordination runtime boundaries."""
from pathlib import Path
import os
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def main():
    root = Path(__file__).resolve().parents[1]
    if os.name != "posix":
        print("UNQUALIFIED: these runtime containment checks require POSIX")
        return 2
    commands = [[sys.executable, "docs/knowledge/acp-compatibility/verify-coordination-end-to-end.py"]]
    commands += [[sys.executable, "-m", "unittest", "discover", "-s", "tests/docs_explorer", "-p", name]
                 for name in ("test_coord_proof_fresh_clone.py", "test_coord_runtime.py", "test_coord_native.py",
                              "test_coord_transport.py", "test_coord_runner.py", "test_bounded_process.py",
                              "test_coord_liveness.py")]
    for command in commands:
        print("VERIFY " + " ".join(command[1:]), flush=True)
        result = subprocess.run(command, cwd=root, timeout=300)
        if result.returncode:
            return result.returncode
    print("PASS: historical Git evidence and offline runtime boundary checks; native credentials/profile qualification is separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
