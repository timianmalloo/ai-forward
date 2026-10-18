#!/usr/bin/env python3
"""CI-speed C3: every collected test reports a result, so a parallel run cannot silently drop one.

pytest-xdist distributes tests across workers; a worker that dies or a collection that differs
between workers can lose tests while the summary line still reads green. This compares the number
of tests pytest collects with the number of test cases in the run's JUnit report, and fails when
they differ.

Usage: check-test-counts.py --junit <report.xml> [pytest collection args, default: tests]
"""
import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def collected(args):
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
                         capture_output=True, text=True, encoding="utf-8")
    match = re.search(r"(\d+) tests? collected", out.stdout)
    if out.returncode != 0 or not match:
        raise SystemExit("could not collect: exit {}\n{}".format(out.returncode, out.stdout[-2000:]))
    return int(match.group(1))


def reported(junit):
    cases = {(case.get("classname"), case.get("name")) for case in ET.parse(junit).getroot().iter("testcase")}
    return len(cases)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit", required=True)
    args, rest = ap.parse_known_args(argv)
    want, got = collected(rest or ["tests"]), reported(args.junit)
    print("collected {}, reported {}".format(want, got))
    if want != got:
        print("FAIL: {} collected test(s) have no result in {}".format(want - got, args.junit))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
