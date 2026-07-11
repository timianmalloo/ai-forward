#!/usr/bin/env python3
"""Spawn one child and block without writing to stdout or stderr."""

import argparse
import json
import os
import subprocess
import sys
import threading


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--pid-file")
    args = parser.parse_args()
    if args.child:
        threading.Event().wait()
        return
    child = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--child"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with open(args.pid_file, "w", encoding="utf-8") as pid_file:
        json.dump({"parent": os.getpid(), "child": child.pid}, pid_file)
        pid_file.flush()
        os.fsync(pid_file.fileno())
    threading.Event().wait()


if __name__ == "__main__":
    main()
