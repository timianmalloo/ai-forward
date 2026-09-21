"""Tests for progress liveness, the running track and the kick ladder (track P3).

Spec: docs/specs/liveness-and-track.md (US-1..US-9). Design: docs/design/liveness-and-track.md
(sections 2, 7, 8, 11). Written red-first: every test here failed before the code existed
(AttributeError on the module functions; argparse exit 2 on the CLI; FileNotFoundError on the hook).

Each test's docstring names the input that makes it fail (D0).
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "pack" / "scripts" / "coord-core.py"
HOOK = REPO / "pack" / "adapters" / "hooks" / "heartbeat.py"
DOCTOR = REPO / "pack" / "scripts" / "pack-doctor.py"
NO_MACHINE_PATHS = REPO / "pack" / "scripts" / "verify-no-machine-paths.py"
HOOK_JSONS = {
    "claude": REPO / "pack" / "adapters" / "hooks" / "claude-code.settings.hooks.json",
    "grok": REPO / "pack" / "adapters" / "hooks" / "grok.ai-forward-hooks.json",
    "agy": REPO / "pack" / "adapters" / "hooks" / "agy.ai-forward-hooks.json",
    "copilot": REPO / "pack" / "adapters" / "hooks" / "copilot.ai-forward-hooks.json",
}
NOW = 1_700_000_000.0


def load_module():
    spec = importlib.util.spec_from_file_location("coord_core_liveness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LivenessCase(unittest.TestCase):
    """A real repository per test: the ledger, the ref and the worktrees are never mocked."""

    def setUp(self):
        self.m = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "r"
        self.repo.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        (self.repo / "README.md").write_text("x\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "init")
        self.root = self.repo / ".agents"
        (self.root / "log").mkdir(parents=True)

    def git(self, *args, check=True, cwd=None):
        return subprocess.run(["git", *args], cwd=str(cwd or self.repo), check=check,
                              capture_output=True, text=True, encoding="utf-8")

    def env(self, session, extra=None):
        env = dict(os.environ)
        for key in ("COORD_ROOT", "AGENT_SESSION", "AGENT_NAME", "AGENT_WI"):
            env.pop(key, None)
        env["COORD_ROOT"] = str(self.root)
        if session:
            env["AGENT_SESSION"] = session
            env["AGENT_NAME"] = session
        env.update(extra or {})
        return env

    def run_cli(self, *args, session="coord", cwd=None, extra_env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(cwd or self.repo),
                              env=self.env(session, extra_env), capture_output=True, text=True,
                              encoding="utf-8")

    def run_hook(self, payload, session="s1", host="claude", event=None, raw=None):
        args = [sys.executable, str(HOOK), "--host", host]
        if event:
            args += ["--event", event]
        stdin = raw if raw is not None else json.dumps(payload)
        return subprocess.run(args, cwd=str(self.repo), env=self.env(session), input=stdin,
                              capture_output=True, text=True, encoding="utf-8")

    def row(self, session, kind, at, **extra):
        event = {"kind": kind, "session": session, "agent": session, "wi": extra.pop("wi", "WI-0"),
                 "path": "-", "at": float(at)}
        event.update(extra)
        return self.m.append_event(self.root, event)

    def start(self, session, at=NOW - 1000, worktree="wt-a", wi="WI-0"):
        return self.row(session, "session-start", at, worktree=worktree, tree="worktree", wi=wi)

    def beat(self, session, at, calls, files=0, **extra):
        return self.row(session, "heartbeat", at, calls=calls, files=files,
                        tokens=extra.pop("tokens", "not recorded"), worktree="wt-a", **extra)

    def twin(self, session, kind, to, at, ref=None, mail_id="mail-x"):
        return self.m.append_record(self.root / "log" / "{}.jsonl".format(session), {
            "type": "mail", "mail_id": mail_id, "kind": kind, "from": session, "to": to,
            "ref": ref, "at": float(at), "session": session})

    def ledger(self, session):
        path = self.root / "log" / "{}.jsonl".format(session)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def inbox(self, session):
        path = self.root / "mail" / "{}.jsonl".format(session)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def fold(self, now=NOW, mtimes=None):
        events, errors, _files = self.m.read_events(self.root)
        self.assertEqual(errors, [])
        return {(r["session"], r["wi"]): r for r in self.m.track_fold(events, now, mtimes)}


# --- the fold (US-2, US-4, US-5) --------------------------------------------------------------

class TrackFoldTests(LivenessCase):

    def test_zero_delta_ping_is_stalled_never_live(self):
        """Fails if a fresh (10 s old) beat with calls=0 files=0 renders live."""
        self.start("s1")
        self.beat("s1", NOW - 10, calls=0, files=0)
        row = self.fold()[("s1", "WI-0")]
        self.assertEqual(row["state"], "stalled")
        self.assertEqual(row["source"], "heartbeat")

    def test_progress_beat_is_live(self):
        """Fails if a 10 s old beat with calls=3 renders anything but live."""
        self.start("s1")
        self.beat("s1", NOW - 10, calls=3, files=1)
        row = self.fold()[("s1", "WI-0")]
        self.assertEqual(row["state"], "live")
        self.assertEqual(row["last_progress_at"], NOW - 10)
        self.assertEqual(row["missed_beats"], 0)

    def test_three_missed_beats_boundary(self):
        """Fails if 299 s renders stalled or 301 s renders live (STALL_AFTER = 3 x 100 s)."""
        self.start("s1")
        self.beat("s1", NOW - 299, calls=1)
        self.assertEqual(self.fold()[("s1", "WI-0")]["state"], "live")
        self.start("s2")
        self.beat("s2", NOW - 301, calls=1)
        row = self.fold()[("s2", "WI-0")]
        self.assertEqual(row["state"], "stalled")
        self.assertEqual(row["missed_beats"], 3)

    def test_stale_progress_after_zero_delta_still_stalled(self):
        """Fails if an old progress beat followed by a fresh zero-delta beat renders live."""
        self.start("s1")
        self.beat("s1", NOW - 400, calls=5)
        self.beat("s1", NOW - 5, calls=0)
        row = self.fold()[("s1", "WI-0")]
        self.assertEqual(row["state"], "stalled")
        self.assertEqual(row["last_progress_at"], NOW - 400)

    def test_blocked_from_mail_twin_and_unblocked_clears_it(self):
        """Fails if a blocked twin newer than any unblocked does not render blocked with blocked_on."""
        self.start("s1")
        self.beat("s1", NOW - 5, calls=2)
        self.twin("s1", "blocked", "coord", NOW - 50, mail_id="m1")
        row = self.fold()[("s1", "WI-0")]
        self.assertEqual(row["state"], "blocked")
        self.assertEqual(row["blocked_on"], "coord")
        self.twin("s1", "unblocked", "coord", NOW - 40, mail_id="m2")
        self.assertEqual(self.fold()[("s1", "WI-0")]["state"], "live")

    def test_done_from_session_end_regardless_of_age(self):
        """Fails if an ended session renders stalled after 300 s."""
        self.start("s1")
        self.beat("s1", NOW - 900, calls=1)
        self.row("s1", "session-end", NOW - 800, worktree="wt-a")
        self.assertEqual(self.fold()[("s1", "WI-0")]["state"], "done")

    def test_done_from_done_twin(self):
        """Fails if a `done` mail twin does not render done."""
        self.start("s1")
        self.twin("s1", "done", "coord", NOW - 10, mail_id="m9")
        self.assertEqual(self.fold()[("s1", "WI-0")]["state"], "done")

    def test_worktree_mtime_fallback(self):
        """Fails if a session with no beat but a 30 s old file change renders stalled, or 300 s renders live."""
        self.start("s1", worktree="wt-a")
        self.start("s2", worktree="wt-b")
        rows = self.fold(mtimes={"wt-a": NOW - 30, "wt-b": NOW - 300})
        self.assertEqual((rows[("s1", "WI-0")]["state"], rows[("s1", "WI-0")]["source"]), ("live", "worktree-mtime"))
        self.assertEqual((rows[("s2", "WI-0")]["state"], rows[("s2", "WI-0")]["source"]), ("stalled", "worktree-mtime"))

    def test_unresolved_worktree_is_stalled_with_source_none(self):
        """Fails if unproven liveness renders live."""
        self.start("s1", worktree="nowhere")
        row = self.fold(mtimes={})[("s1", "WI-0")]
        self.assertEqual((row["state"], row["source"]), ("stalled", "none"))

    def test_legacy_absolute_worktree_matches_label(self):
        """Fails if a pre-F-3 row with an absolute worktree path cannot find its mtime by label."""
        self.start("s1", worktree=str(Path(self.tmp.name) / "trees" / "wt-a"))
        row = self.fold(mtimes={"wt-a": NOW - 1})[("s1", "WI-0")]
        self.assertEqual(row["state"], "live")

    def test_deadline_not_recorded(self):
        """Fails if the fold invents a deadline (no store carries one yet)."""
        self.start("s1")
        self.assertIsNone(self.fold()[("s1", "WI-0")]["deadline_at"])


# --- coord track (US-3 + the rendered surface) -----------------------------------------------

class TrackCliTests(LivenessCase):

    def test_empty_corpus_is_not_checked(self):
        """Fails if an empty ledger renders 'all quiet' with exit 0."""
        done = self.run_cli("track")
        self.assertEqual(done.returncode, 4, done.stdout + done.stderr)
        self.assertIn("COORD-TRACK-NOT-CHECKED", done.stdout + done.stderr)

    def test_track_renders_rows_through_the_real_entry_point(self):
        """Fails if the CLI does not render one row per (session, wi) with the state words."""
        self.start("s1", at=time.time() - 600)
        self.beat("s1", time.time() - 5, calls=4, files=2)
        self.start("s2", at=time.time() - 600)
        self.beat("s2", time.time() - 5, calls=0)
        done = self.run_cli("track")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertRegex(done.stdout, r"live\s+s1")
        self.assertRegex(done.stdout, r"stalled\s+s2")
        as_json = json.loads(self.run_cli("track", "--json").stdout)
        states = {r["session"]: r["state"] for r in as_json["tracks"]}
        self.assertEqual(states, {"s1": "live", "s2": "stalled"})
        self.assertEqual(as_json["tracks"][0]["deadline"], "not recorded")


# --- heartbeat_tick and the verb (US-1, US-8) -----------------------------------------------

class HeartbeatTickTests(LivenessCase):

    def tick(self, session="s1", now=NOW, **kw):
        return self.m.heartbeat_tick(self.root, self.repo, session, session, now, **kw)

    def test_first_tick_opens_the_window_and_writes_nothing(self):
        """Fails if the first tick writes a ledger row (US-1 first clause)."""
        self.assertIsNone(self.tick(files=["docs/x.md"]))
        self.assertEqual([r for r in self.ledger("s1") if r["kind"] == "heartbeat"], [])

    def test_sampled_row_carries_the_deltas(self):
        """Fails if two ticks 100 s apart do not yield exactly one row with calls=2 files=1, or if
        two ticks 5 s apart yield a row."""
        self.tick(files=["docs/x.md"])
        self.assertIsNone(self.tick(now=NOW + 5))
        row = self.tick(now=NOW + 100, files=["docs/x.md"])
        self.assertIsNotNone(row)
        self.assertEqual((row["kind"], row["calls"], row["files"], row["tokens"]),
                         ("heartbeat", 3, 1, "not recorded"))
        self.assertEqual(len([r for r in self.ledger("s1") if r["kind"] == "heartbeat"]), 1)

    def test_flush_writes_a_zero_delta_row(self):
        """Fails if a Stop (flush) with nothing accumulated is swallowed."""
        self.tick()
        self.tick(now=NOW + 100)
        row = self.tick(now=NOW + 105, calls=0, flush=True)
        self.assertEqual((row["calls"], row["files"]), (0, 0))
        self.assertEqual(row["since"], NOW + 100)

    def test_row_carries_a_label_not_a_path(self):
        """Fails if the heartbeat row's worktree field holds a path separator (PLAT-B)."""
        self.tick(cwd=self.repo)
        row = self.tick(now=NOW + 100, flush=True, cwd=self.repo)
        self.assertNotIn("/", row["worktree"])
        self.assertNotIn("\\", row["worktree"])
        self.assertEqual(row["worktree"], self.repo.name)

    def test_corrupt_accumulator_resets(self):
        """Fails if a corrupt accumulator crashes the tick instead of starting from zero."""
        self.tick()
        acc = self.m.heartbeat_scratch_path(self.root, self.repo, "s1")
        acc.write_text("{not json", encoding="utf-8")
        row = self.tick(now=NOW + 1, flush=True)
        self.assertEqual(row["calls"], 1)
        self.assertIsNone(row["since"])

    def test_heartbeat_verb_through_the_cli(self):
        """Fails if `coord session heartbeat --flush` does not append a heartbeat row."""
        done = self.run_cli("session", "heartbeat", "--flush", session="s1")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        rows = [r for r in self.ledger("s1") if r["kind"] == "heartbeat"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["calls"], 1)

    def test_holder_beat_renews_the_leader(self):
        """Fails if the holder's sampled beat leaves expires_at where it was (F-1)."""
        pin = self.run_cli("leader", "pin", "s1", session="s1")
        self.assertEqual(pin.returncode, 0, pin.stdout + pin.stderr)
        before = json.loads(self.run_cli("leader", "who", "--json", session="s1").stdout)
        now = time.time() + 50
        self.tick(now=now - 100)
        row = self.tick(now=now, flush=True)
        after = json.loads(self.run_cli("leader", "who", "--json", session="s1").stdout)
        self.assertIs(row["leader_renewed"], True)
        self.assertGreater(after["expires_at"], before["expires_at"])
        self.assertEqual(after["epoch"], before["epoch"])

    def test_expired_designation_is_not_reclaimed_by_a_beat(self):
        """Fails if a beat advances the epoch over an expired designation."""
        record = {"leader": "s1", "epoch": 4, "pinned_at": NOW - 1000, "expires_at": NOW - 500, "ttl": 300.0}
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=str(self.repo),
                              input=json.dumps(record, sort_keys=True), capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout.strip()
        self.git("update-ref", "refs/coord/leader", blob, "0" * 40)
        row = self.tick(now=NOW, flush=True)
        self.assertEqual(row["leader_renewed"], "expired")
        who = json.loads(self.run_cli("leader", "who", "--json", session="s1").stdout)
        self.assertEqual(who["epoch"], 4)

    def test_non_holder_beat_leaves_the_ref_alone(self):
        """Fails if a non-holder's beat renews or records anything but null."""
        self.run_cli("leader", "pin", "s1", session="s1")
        before = json.loads(self.run_cli("leader", "who", "--json", session="s1").stdout)
        row = self.tick(session="s2", now=time.time(), flush=True)
        after = json.loads(self.run_cli("leader", "who", "--json", session="s1").stdout)
        self.assertIsNone(row["leader_renewed"])
        self.assertEqual(after["expires_at"], before["expires_at"])


# --- the hook (US-1, section 7/8 of the design) ---------------------------------------------

class HookTests(LivenessCase):

    def payload(self, event="PostToolUse", tool="Edit", path="docs/x.md"):
        return {"hook_event_name": event, "session_id": "abc", "cwd": str(self.repo),
                "tool_name": tool, "tool_input": {"file_path": path}}

    def test_post_tool_use_then_stop_writes_one_row(self):
        """Fails if the hook exits non-zero, prints anything, or the Stop does not flush calls=1 files=1."""
        first = self.run_hook(self.payload())
        self.assertEqual((first.returncode, first.stdout), (0, ""), first.stderr)
        self.assertEqual([r for r in self.ledger("s1") if r["kind"] == "heartbeat"], [])
        stop = self.run_hook({"hook_event_name": "Stop", "session_id": "abc", "cwd": str(self.repo)})
        self.assertEqual((stop.returncode, stop.stdout), (0, ""), stop.stderr)
        rows = [r for r in self.ledger("s1") if r["kind"] == "heartbeat"]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["calls"], rows[0]["files"], rows[0]["host"], rows[0]["event"]),
                         (1, 1, "claude", "Stop"))

    def test_copilot_config_wires_post_tool_use_and_subagent_stop(self):
        config = json.loads(HOOK_JSONS["copilot"].read_text(encoding="utf-8"))["hooks"]
        self.assertIn("sessionStart", config)
        self.assertIn("subagentStart", config)
        self.assertIn("postToolUse", config)
        self.assertIn("subagentStop", config)
        self.assertTrue(any("session-start.py --host copilot" in entry.get("bash", "")
                            for entry in config["sessionStart"]))
        self.assertTrue(any("heartbeat.py --host copilot --event postToolUse" in entry.get("bash", "")
                            for entry in config["postToolUse"]))
        sub_stop = "\n".join(entry.get("bash", "") for entry in config["subagentStop"])
        self.assertIn("mail-doorbell.py --host copilot --event subagentStop", sub_stop)
        self.assertIn("heartbeat.py --host copilot --event subagentStop", sub_stop)
        self.assertIn("owner-review-gate.py --host copilot --event subagentStop", sub_stop)

    def test_malformed_stdin_exits_0_prints_nothing_and_counts_the_call(self):
        """Fails if garbage on stdin denies the tool call (Copilot semantics) or is not counted."""
        done = self.run_hook(None, raw="{not json")
        self.assertEqual((done.returncode, done.stdout), (0, ""))
        stop = self.run_hook({"hook_event_name": "Stop"})
        rows = [r for r in self.ledger("s1") if r["kind"] == "heartbeat"]
        self.assertEqual(rows[0]["calls"], 1)
        self.assertEqual(stop.returncode, 0)

    def test_without_a_session_nothing_is_written(self):
        """Fails if a hook with no AGENT_SESSION writes a ledger or a scratch file."""
        done = self.run_hook(self.payload(), session=None)
        self.assertEqual((done.returncode, done.stdout), (0, ""))
        self.assertEqual(sorted(p.name for p in (self.root / "log").iterdir()), [])

    def test_a_traversal_path_is_counted_never_stored_or_opened(self):
        """Fails if the file path from stdin reaches the ledger text."""
        self.run_hook(self.payload(path="../../etc/passwd"))
        self.run_hook({"hook_event_name": "Stop"})
        text = (self.root / "log" / "s1.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("passwd", text)
        rows = [r for r in self.ledger("s1") if r["kind"] == "heartbeat"]
        self.assertEqual(rows[0]["files"], 1)

    def test_hook_json_entries_per_host(self):
        """Fails if a host's hook config does not run heartbeat.py at its documented seam."""
        claude = json.loads(HOOK_JSONS["claude"].read_text(encoding="utf-8"))["hooks"]
        for event in ("PostToolUse", "Stop"):
            commands = [h["command"] for entry in claude[event] for h in entry["hooks"]]
            self.assertTrue(any("heartbeat.py --host claude" in c for c in commands), event)
        grok = json.loads(HOOK_JSONS["grok"].read_text(encoding="utf-8"))["hooks"]
        self.assertTrue(any("heartbeat.py --host grok" in h["command"]
                            for entry in grok["PreToolUse"] for h in entry["hooks"]))
        agy = json.loads(HOOK_JSONS["agy"].read_text(encoding="utf-8"))["heartbeat"]
        self.assertTrue(any("heartbeat.py" in h["command"] and "--host agy" in h["command"]
                            for event in ("PostToolUse", "Stop") for entry in agy[event]
                            for h in (entry["hooks"] if "hooks" in entry else [entry])))
        copilot = json.loads(HOOK_JSONS["copilot"].read_text(encoding="utf-8"))["hooks"]
        for event in ("postToolUse", "agentStop", "subagentStop"):
            self.assertTrue(any("heartbeat.py --host copilot" in h["bash"] for h in copilot[event]), event)
        for path in HOOK_JSONS.values():
            self.assertNotIn("/Users/", path.read_text(encoding="utf-8"))


# --- the kick ladder (US-6) -----------------------------------------------------------------

class KickLadderTests(LivenessCase):

    def stalled_target(self, session="s2", wi="WI-7"):
        self.start(session, at=time.time() - 3600, wi=wi)
        self.beat(session, time.time() - 900, calls=0, wi=wi)

    def ladder_rows(self, kicker="coord"):
        return [r for r in self.ledger(kicker) if r.get("kind") == "kick-ladder"]

    def test_two_kicks_then_the_cap(self):
        """Fails if a third kick lands, or if the two are not counted and twinned."""
        self.stalled_target()
        for expected in (1, 2):
            done = self.run_cli("kick", "s2", "--wi", "WI-7")
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual(len([m for m in self.inbox("s2") if m["kind"] == "kick"]), expected)
        third = self.run_cli("kick", "s2", "--wi", "WI-7")
        self.assertEqual(third.returncode, 3, third.stdout + third.stderr)
        self.assertIn("COORD-KICK-CAP", third.stdout)
        self.assertEqual(len([m for m in self.inbox("s2") if m["kind"] == "kick"]), 2)
        rows = self.ladder_rows()
        self.assertEqual([(r["rung"], r["outcome"]) for r in rows], [(1, "ok"), (1, "ok"), (1, "refused")])
        self.assertEqual(rows[2]["code"], "COORD-KICK-CAP")
        self.assertEqual(rows[1]["kicks_before"], 1)
        self.assertGreaterEqual(rows[0]["stall_age_s"], 899)
        self.assertEqual(rows[0]["missed_beats"], 9)
        twins = [r for r in self.ledger("coord") if r.get("type") == "mail" and r.get("kind") == "kick"]
        self.assertEqual(len(twins), 2)

    def test_rung_2_needs_a_fallback(self):
        """Fails if a decision request without a termination variant is written."""
        self.stalled_target()
        done = self.run_cli("kick", "s2", "--wi", "WI-7", "--rung", "2", "--owner", "coord")
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn("COORD-KICK-INCOMPLETE", done.stdout + done.stderr)
        self.assertFalse((self.root / "requests.jsonl").exists())

    def test_rung_2_needs_an_owner(self):
        """Fails if rung 2 escalates to nobody when no leader is designated."""
        self.stalled_target()
        done = self.run_cli("kick", "s2", "--wi", "WI-7", "--rung", "2", "--fallback", "land without P5")
        self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
        self.assertIn("COORD-KICK-NO-OWNER", done.stdout)

    def test_rung_2_writes_the_typed_request_and_the_mail(self):
        """Fails if the request lacks reason=kick-ladder, the kick mail ref, a deadline or the fallback,
        or if no decision-request mail reaches the owner."""
        self.stalled_target()
        self.run_cli("kick", "s2", "--wi", "WI-7")
        kick_id = [m for m in self.inbox("s2") if m["kind"] == "kick"][-1]["id"]
        pin = self.run_cli("leader", "pin", "coord")
        self.assertEqual(pin.returncode, 0, pin.stdout)
        done = self.run_cli("kick", "s2", "--wi", "WI-7", "--rung", "2", "--fallback", "land without P5",
                            "--deadline", "600")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        requests = [json.loads(line) for line in
                    (self.root / "requests.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        add = [r for r in requests if r["kind"] == "request-add"]
        self.assertEqual(len(add), 1)
        self.assertEqual((add[0]["to"], add[0]["reason"], add[0]["ref"], add[0]["fallback"]),
                         ("coord", "kick-ladder", kick_id, "land without P5"))
        self.assertAlmostEqual(add[0]["deadline_at"] - add[0]["at"], 600, delta=1)
        decision = [m for m in self.inbox("coord") if m["kind"] == "decision-request"]
        self.assertEqual(len(decision), 1)
        self.assertEqual(decision[0]["ref"], add[0]["id"])
        rung2 = [r for r in self.ladder_rows() if r["rung"] == 2]
        self.assertEqual((rung2[0]["outcome"], rung2[0]["request_id"]), ("ok", add[0]["id"]))

    def test_kick_on_a_live_track_is_not_due(self):
        """Fails if a live track can be kicked without a passed deadline."""
        self.start("s2", at=time.time() - 600, wi="WI-7")
        self.beat("s2", time.time() - 5, calls=3, wi="WI-7")
        done = self.run_cli("kick", "s2", "--wi", "WI-7")
        self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
        self.assertIn("COORD-KICK-NOT-DUE", done.stdout)
        self.assertEqual(self.inbox("s2"), [])
        passed = self.run_cli("kick", "s2", "--wi", "WI-7", "--deadline-at", str(time.time() - 60))
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        self.assertEqual(self.ladder_rows()[-1]["deadline_at"], float(passed.stdout.split("deadline_at=")[1].split()[0]))

    def test_blocked_track_gets_rung_0_notify(self):
        """Fails if a blocked, un-notified track does not get an inbox-only note."""
        self.start("s2", at=time.time() - 600, wi="WI-7")
        self.beat("s2", time.time() - 5, calls=3, wi="WI-7")
        self.twin("s2", "blocked", "coord", time.time() - 30, mail_id="mb")
        done = self.run_cli("kick", "s2", "--wi", "WI-7")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        notes = [m for m in self.inbox("s2") if m["kind"] == "note"]
        self.assertEqual(len(notes), 1)
        self.assertEqual(self.ladder_rows()[-1]["rung"], 0)
        self.assertEqual([r for r in self.ledger("coord") if r.get("type") == "mail"], [])

    def test_unknown_target_is_not_checked(self):
        """Fails if kicking a session with no track row sends anything."""
        done = self.run_cli("kick", "ghost", "--wi", "WI-1")
        self.assertEqual(done.returncode, 4, done.stdout + done.stderr)
        self.assertIn("COORD-KICK-NOT-CHECKED", done.stdout + done.stderr)
        self.assertEqual(self.inbox("ghost"), [])


# --- metrics and doctor (US-7) -------------------------------------------------------------

class MetricsAndDoctorTests(LivenessCase):

    def test_empty_corpus_renders_reasons_not_zeros(self):
        """Fails if a liveness counter is 0 over a corpus with no heartbeat."""
        payload = json.loads(self.run_cli("metrics", "--json").stdout)
        self.assertEqual(payload["heartbeat_reason"], "no heartbeat recorded")
        self.assertIsNone(payload["stalls_observed"])
        self.assertIsNone(payload["kicks"])

    def test_counters_over_a_fixture(self):
        """Fails if kicks, cap refusals, escalations, zero-delta beats or the stall latency median are wrong."""
        self.start("s2", at=time.time() - 3600, wi="WI-7")
        self.beat("s2", time.time() - 900, calls=0, wi="WI-7")
        self.run_cli("kick", "s2", "--wi", "WI-7")
        self.run_cli("kick", "s2", "--wi", "WI-7")
        self.run_cli("kick", "s2", "--wi", "WI-7")
        self.run_cli("leader", "pin", "coord")
        self.run_cli("kick", "s2", "--wi", "WI-7", "--rung", "2", "--fallback", "f")
        payload = json.loads(self.run_cli("metrics", "--json").stdout)
        self.assertEqual((payload["heartbeats"], payload["stalls_observed"], payload["kicks"],
                          payload["kicks_refused_cap"], payload["escalations"], payload["false_kicks"]),
                         (1, 1, 2, 1, 1, 0))
        self.assertGreaterEqual(payload["stall_latency_median_s"], 899)
        text = self.run_cli("metrics").stdout
        self.assertIn("kicks", text)
        self.assertIn("stall", text)

    def test_false_kick_is_counted(self):
        """Fails if a kick followed by a progress beat from the target within 300 s is not a false kick."""
        self.start("s2", at=time.time() - 3600, wi="WI-7")
        self.beat("s2", time.time() - 900, calls=0, wi="WI-7")
        self.run_cli("kick", "s2", "--wi", "WI-7")
        self.beat("s2", time.time() + 1, calls=4, wi="WI-7")
        payload = json.loads(self.run_cli("metrics", "--json").stdout)
        self.assertEqual(payload["false_kicks"], 1)

    def test_pack_doctor_heartbeat_line(self):
        """Fails if pack-doctor has no heartbeat check, or renders a count over an empty corpus."""
        def doctor():
            done = subprocess.run([sys.executable, str(DOCTOR), "--root", str(self.repo), "--json"],
                                  capture_output=True, text=True, encoding="utf-8")
            return {c["name"]: c for c in json.loads(done.stdout)["checks"]}
        self.assertIn("not recorded", doctor()["heartbeat"]["detail"])
        self.start("s1", at=time.time() - 600)
        self.beat("s1", time.time() - 5, calls=2)
        self.start("s2", at=time.time() - 600)
        self.beat("s2", time.time() - 5, calls=0)
        detail = doctor()["heartbeat"]["detail"]
        self.assertIn("2 session(s) beating", detail)
        self.assertIn("1 stalled", detail)


# --- F-3: the worktree field (US-9) --------------------------------------------------------

class WorktreeLabelTests(LivenessCase):

    def diagnostic_event(self, home):
        brief = home + "/repo/.git/coord-runs/example/worker.brief.json"
        return {"session": "portable", "kind": "runner", "seq": 1,
                "worktree": home + "/repo-worker", "hook_cwd": home + "/repo-worker/.agents",
                "manual_brief": brief, "detail_path": home + "/repo/.git/coord-runs/example/action.json",
                "prompt": home + "/unchanged action text",
                "result": {"manual_brief": brief, "body": home + "/unchanged body",
                           "workers": [{"manual_brief": brief, "path": home + "/unchanged path"}, None]}}

    def test_writer_normalizes_only_diagnostic_paths_without_mutating_private_result(self):
        """Fails if public event paths leak homes or normalization changes private runtime data."""
        for home in ("/Users/fixture", "/home/fixture", "C:/Users/fixture"):  # machine-path-ok: portability fixtures
            with self.subTest(home=home):
                event = self.diagnostic_event(home)
                original = json.loads(json.dumps(event))
                self.m.append_event(self.root, event)
                actual = self.ledger("portable")[-1]
                self.assertEqual("repo-worker", actual["worktree"])
                self.assertEqual("~/repo-worker/.agents", actual["hook_cwd"])
                self.assertEqual("~/repo/.git/coord-runs/example/action.json", actual["detail_path"])
                for value in (actual["manual_brief"], actual["result"]["manual_brief"],
                              actual["result"]["workers"][0]["manual_brief"]):
                    self.assertEqual("~/repo/.git/coord-runs/example/worker.brief.json", value)
                self.assertEqual(original, event)
                self.assertEqual(original["prompt"], actual["prompt"])
                self.assertEqual(original["result"]["body"], actual["result"]["body"])
                self.assertEqual(original["result"]["workers"][0]["path"], actual["result"]["workers"][0]["path"])

    def test_log_portable_covers_nested_diagnostics_and_preserves_other_bytes(self):
        """Fails if migration misses a result brief, rewrites arbitrary text, or is not idempotent."""
        path = self.root / "log" / "legacy.jsonl"
        event = self.diagnostic_event("C:\\Users\\fixture")  # machine-path-ok: foreign platform fixture
        untouched = '{"result":null,"manual_brief":null,"z":2,"a":1}\n{bad json}\n'
        path.write_text(json.dumps(event) + "\n" + untouched, encoding="utf-8")
        done = self.run_cli("log", "portable", str(path))
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("1 row(s) rewritten", done.stdout)
        first = path.read_text(encoding="utf-8")
        actual = json.loads(first.splitlines()[0])
        self.assertEqual("~/repo-worker/.agents", actual["hook_cwd"])
        self.assertEqual("~/repo/.git/coord-runs/example/action.json", actual["detail_path"])
        self.assertEqual("~/repo/.git/coord-runs/example/worker.brief.json", actual["result"]["workers"][0]["manual_brief"])
        self.assertEqual(event["prompt"], actual["prompt"])
        self.assertTrue(first.endswith(untouched))
        again = self.run_cli("log", "portable", str(path))
        self.assertIn("0 row(s) rewritten", again.stdout)
        self.assertEqual(first, path.read_text(encoding="utf-8"))

    def test_session_start_from_a_linked_worktree_carries_no_absolute_path(self):
        """Fails if the session-start row's worktree field is the path (what gate 1b refused)."""
        tree = Path(self.tmp.name) / "wt-a"
        self.git("worktree", "add", "-q", "-b", "feat/a", str(tree))
        done = self.run_cli("session", "start", session="s1", cwd=tree)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        rows = [r for r in self.ledger("s1") if r["kind"] == "session-start"]
        self.assertEqual(rows[0]["worktree"], "wt-a")
        self.assertEqual(rows[0]["tree"], "worktree")
        self.assertNotIn(self.tmp.name, (self.root / "log" / "s1.jsonl").read_text(encoding="utf-8"))
        second = self.run_cli("session", "start", session="s9", cwd=tree)
        self.assertEqual(second.returncode, 3, second.stdout)
        self.assertIn("COORD-WORKTREE-OCCUPIED", second.stdout)
        end = self.run_cli("session", "end", session="s1", cwd=tree)
        self.assertEqual(end.returncode, 0, end.stdout + end.stderr)
        self.assertEqual([r for r in self.ledger("s1") if r["kind"] == "session-end"][0]["worktree"], "wt-a")

    def test_worktree_new_records_the_label(self):
        """Fails if `coord worktree new` still writes the absolute path."""
        done = self.run_cli("worktree", "new", "--branch", "feat/b", session="s3")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        rows = [r for r in self.ledger("s3") if r["kind"] == "session-start"]
        self.assertNotIn("/", rows[0]["worktree"])
        self.assertNotIn("\\", rows[0]["worktree"])

    def test_log_portable_rewrites_only_the_worktree_field_idempotently(self):
        """Fails if any other line changes, an unparseable line is dropped, or a second run rewrites again."""
        path = self.root / "log" / "old.jsonl"
        absolute = "/Users/someone/projects/ai-forward-feat-x"  # machine-path-ok: the fixture the migration must rewrite
        lines = [
            json.dumps({"at": 1.0, "kind": "session-start", "session": "old", "worktree": absolute, "tree": "worktree"}, sort_keys=True),
            '{"at": 2.0, "kind": "claim", "path": "docs/a.md", "session": "old", "unsorted_last": 1, "aaa": 2}',
            "{not json at all",
            json.dumps({"at": 3.0, "kind": "session-end", "session": "old", "worktree": "C:\\Users\\x\\ai-forward-feat-x"}, sort_keys=True),
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        done = self.run_cli("log", "portable", str(path))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("2 row(s) rewritten", done.stdout)
        out = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(out[0])["worktree"], "ai-forward-feat-x")
        self.assertEqual(out[1], lines[1])
        self.assertEqual(out[2], lines[2])
        self.assertEqual(json.loads(out[3])["worktree"], "ai-forward-feat-x")
        again = self.run_cli("log", "portable", str(path))
        self.assertIn("0 row(s) rewritten", again.stdout)
        self.assertEqual(path.read_text(encoding="utf-8").splitlines(), out)
        self.git("add", "-f", str(path))
        gate = subprocess.run([sys.executable, str(NO_MACHINE_PATHS), "--root", str(self.repo)],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)


if __name__ == "__main__":
    unittest.main()
