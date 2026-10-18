#!/usr/bin/env python3
"""CI-speed C6 / P9: per-job wall-clock for this run against the trailing median of green `main` runs.

Writes a Markdown table to $GITHUB_STEP_SUMMARY (or stdout) and fails when a job took more than
`--growth` times its trailing median. With fewer than `--min-history` green main runs for a job,
that job is reported as "not enough history" and never fails: a missing baseline degrades to
"not recorded", never to a guessed one. Reads the Actions API through `gh` (GH_TOKEN in CI).

Usage: ci-duration-budget.py --repo <owner/name> --run <run_id> --workflow <file.yml> --jobs a,b,c --since YYYY-MM-DD
`--since` bounds the history to runs of the current suite shape; older runs are not comparable.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit("gh api {} failed: {}".format(path, out.stderr.strip()[:500]))
    return json.loads(out.stdout)


def seconds(job):
    if job.get("conclusion") != "success" or not job.get("started_at") or not job.get("completed_at"):
        return None
    parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (parse(job["completed_at"]) - parse(job["started_at"])).total_seconds()


def run_jobs(repo, run_id):
    return {j["name"]: j for j in gh("repos/{}/actions/runs/{}/jobs?per_page=50".format(repo, run_id))["jobs"]}


def history(repo, workflow, exclude, limit, since):
    runs = gh("repos/{}/actions/workflows/{}/runs?branch=main&event=push&status=success&per_page={}&created=%3E%3D{}"
              .format(repo, workflow, limit, since))["workflow_runs"]
    return [r["id"] for r in runs if str(r["id"]) != str(exclude)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--growth", type=float, default=1.5)
    ap.add_argument("--min-history", type=int, default=5)
    ap.add_argument("--history", type=int, default=10)
    ap.add_argument("--since", required=True,
                    help="YYYY-MM-DD: only runs of the current suite shape are comparable")
    args = ap.parse_args(argv)
    names = [n for n in args.jobs.split(",") if n]
    current = run_jobs(args.repo, args.run)
    past = {name: [] for name in names}
    for run_id in history(args.repo, args.workflow, args.run, args.history, args.since):
        jobs = run_jobs(args.repo, run_id)
        for name in names:
            value = seconds(jobs.get(name, {}))
            if value is not None:
                past[name].append(value)
    rows, over = [], []
    for name in names:
        now = seconds(current.get(name, {}))
        points = past[name]
        if now is None:
            rows.append((name, "not recorded (job not successful)", "", "", "-"))
            continue
        if len(points) < args.min_history:
            rows.append((name, "{:.0f} s".format(now), "not enough history ({} of {})".format(len(points), args.min_history), "", "-"))
            continue
        median = statistics.median(points)
        ratio = now / median
        verdict = "over budget" if ratio > args.growth else "ok"
        if ratio > args.growth:
            over.append(name)
        rows.append((name, "{:.0f} s".format(now), "{:.0f} s (n={})".format(median, len(points)), "{:.2f}x".format(ratio), verdict))
    lines = ["### CI duration budget (fails above {:.2f}x the trailing median of green `main` runs since {})".format(args.growth, args.since), "",
             "| Job | This run | Trailing median | Ratio | Verdict |", "|---|---|---|---|---|"]
    lines += ["| {} | {} | {} | {} | {} |".format(*row) for row in rows]
    report = "\n".join(lines) + "\n"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(report)
    print(report)
    if over:
        print("FAIL: over budget: {}".format(", ".join(over)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
