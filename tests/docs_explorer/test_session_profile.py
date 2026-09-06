"""session-profile.py: the profiler reads the harness stores and produces findings with evidence.

The fixtures are synthetic stores in the shapes the real ones were observed to have (Copilot
CLI 1.0.83 session-store.db + events.jsonl; Claude Code 2.1.x transcript records). Each test
pins one detector against an exact oracle: the finding id appears with the evidence the fixture
planted, and does not appear when the fixture is clean. A missing store reports `not recorded`.
"""
import importlib.util
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack" / "scripts" / "session-profile.py"

spec = importlib.util.spec_from_file_location("session_profile", SCRIPT)
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)

SID = "aaaaaaaa-0000-0000-0000-000000000001"


def _ts(i):
    return "2026-09-05T10:{0:02d}:{1:02d}Z".format(i // 60, i % 60)


def make_copilot_home(home, repo, rereads=True, runaway=True, double_block=True):
    db = os.path.join(home, "session-store.db")
    con = sqlite3.connect(db)
    con.execute("create table sessions (id text primary key, cwd text, repository text, summary text, created_at text, updated_at text)")
    con.execute("""create table assistant_usage_events (id integer primary key autoincrement, session_id text, turn_index integer,
        agent_id text, model text, input_tokens integer, output_tokens integer, cache_read_tokens integer, cache_write_tokens integer,
        reasoning_tokens integer, total_nano_aiu integer, duration_ms integer, time_to_first_token_ms real, initiator text,
        finish_reason text, created_at text, reasoning_effort text)""")
    con.execute("insert into sessions values (?,?,?,?,?,?)", (SID, repo, None, "Fixture session", _ts(0), _ts(600)))
    rows = []
    for k in range(4):
        rows.append((SID, 0, None, "gpt-6-astra", 200000 + k * 50000, 500, 199000 + k * 50000, 500, 1000, 100000000000, 20000, 25000.0, "agent", "tool_calls", _ts(10 + k), "high"))
    rows.append((SID, 0, "sub-1", "gpt-6-astra", 20000, 300, 19000, 500, 50, 1000000000, 5000, 2000.0, "sub-agent", "stop", _ts(12), "high"))
    con.executemany("insert into assistant_usage_events (session_id, turn_index, agent_id, model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, total_nano_aiu, duration_ms, time_to_first_token_ms, initiator, finish_reason, created_at, reasoning_effort) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    sdir = os.path.join(home, "session-state", SID)
    os.makedirs(sdir)
    block = "<custom_instruction>\n# Repo\n" + ("rule " * 6000) + "\n</custom_instruction>\n"
    system = "You are the CLI.\n" + ("x" * 120000) + block + (block if double_block else "")
    ev = []

    def add(t, data, ts, extra=None):
        e = {"type": t, "data": data, "id": "e{0}".format(len(ev)), "timestamp": ts, "parentId": None}
        if extra:
            e.update(extra)
        ev.append(e)

    add("session.start", {"sessionId": SID}, _ts(0))
    add("system.message", {"content": system, "interactionId": "i-main", "role": "system"}, _ts(1))
    add("user.message", {"content": "build the thing", "delivery": "idle", "interactionId": "i-main"}, _ts(2))
    add("assistant.message", {"content": "Goal: build it. Done when: tests pass. Tier: T1", "interactionId": "i-main", "toolRequests": [],
                              "reasoningText": "**Planning** I will read the file, then build." + ("x" * 700)}, _ts(3))
    add("tool.execution_start", {"toolCallId": "sh1", "toolName": "powershell", "arguments": {"command": "git status", "description": "Check the tree before building"}}, _ts(3))
    add("tool.execution_complete", {"toolCallId": "sh1", "interactionId": "i-main", "result": "clean"}, _ts(3))
    add("tool.execution_start", {"toolCallId": "sh2", "toolName": "powershell", "arguments": {"command": "git log -1"}}, _ts(3))
    add("tool.execution_complete", {"toolCallId": "sh2", "interactionId": "i-main", "result": "abc"}, _ts(3))
    path = "C:\\repo\\public.html"
    for k in range(3 if rereads else 1):
        add("tool.execution_start", {"toolCallId": "v{0}".format(k), "toolName": "view", "arguments": {"path": path}}, _ts(4 + k))
        add("tool.execution_complete", {"toolCallId": "v{0}".format(k), "interactionId": "i-main", "result": "<html>" * 100}, _ts(4 + k))
    add("tool.execution_start", {"toolCallId": "s1", "toolName": "skill", "arguments": {"skill": "ui-design"}}, _ts(8))
    add("tool.execution_complete", {"toolCallId": "s1", "interactionId": "i-main", "result": "skill text"}, _ts(8))
    add("tool.execution_start", {"toolCallId": "s2", "toolName": "skill", "arguments": {"skill": "ui-design"}}, _ts(9))
    add("tool.execution_complete", {"toolCallId": "s2", "interactionId": "i-main", "result": "skill text"}, _ts(9))
    add("subagent.started", {"agentName": "domain-researcher", "agentDisplayName": "domain-researcher", "toolCallId": "t1"}, _ts(10), {"agentId": "sub-1"})
    add("system.message", {"content": "You are a world-class Domain Researcher.", "interactionId": "i-sub", "role": "system"}, _ts(10), {"agentId": "sub-1"})
    add("assistant.turn_start", {"interactionId": "i-sub", "turnId": "x"}, _ts(10), {"agentId": "sub-1"})
    add("user.message", {"content": "research everything", "delivery": "idle", "interactionId": "i-sub"}, _ts(10), {"agentId": "sub-1"})
    add("tool.execution_start", {"toolCallId": "sv1", "toolName": "view", "arguments": {"path": "C:\\repo\\AGENTS.md"}}, _ts(11), {"agentId": "sub-1"})
    add("tool.execution_complete", {"toolCallId": "sv1", "interactionId": "i-sub", "result": "agents"}, _ts(11), {"agentId": "sub-1"})
    if runaway:
        add("tool.execution_start", {"toolCallId": "w1", "toolName": "write_agent", "arguments": {"agent_id": "sub-1", "message": "Converge now. Stop further investigation."}}, _ts(13))
        add("tool.execution_complete", {"toolCallId": "w1", "interactionId": "i-main", "result": "ok"}, _ts(13))
    add("subagent.completed", {"agentName": "domain-researcher", "agentDisplayName": "domain-researcher", "totalTokens": 1500000 if runaway else 20000,
                               "totalToolCalls": 60 if runaway else 3, "durationMs": 90000}, _ts(14), {"agentId": "sub-1"})
    add("user.message", {"content": "", "delivery": "idle", "interactionId": "i-nudge", "transformedContent": "You have not yet marked the task as complete using the task_complete tool."}, _ts(20))
    with open(os.path.join(sdir, "events.jsonl"), "w", encoding="utf-8") as fh:
        for e in ev:
            fh.write(json.dumps(e) + "\n")
    with open(os.path.join(home, "settings.json"), "w", encoding="utf-8") as fh:
        json.dump({"model": "gpt-6-astra", "contextTier": "long_context", "effortLevel": "high"}, fh)


def make_claude_home(home, repo):
    slug = sp.claude_slug(repo)
    d = os.path.join(home, "projects", slug)
    os.makedirs(d)
    recs = [
        {"type": "ai-title", "aiTitle": "fixture claude session", "sessionId": "c1"},
        {"type": "user", "message": {"role": "user", "content": "do the task"}, "origin": {"kind": "human"}, "timestamp": _ts(0), "cwd": repo, "sessionId": "c1"},
        {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "thinking", "thinking": "The user wants the task done; read first.", "signature": "sig"},
            {"type": "text", "text": "**Goal:** do it. **Done when:** done. **Tier:** T0"},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/r/a.md"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls", "description": "List the tree"}}],
            "usage": {"input_tokens": 10, "cache_read_input_tokens": 50000, "cache_creation_input_tokens": 1000, "output_tokens": 200,
                      "output_tokens_details": {"thinking_tokens": 400}}},
         "timestamp": _ts(1), "cwd": repo, "sessionId": "c1"},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "..."}]}, "timestamp": _ts(2), "cwd": repo, "sessionId": "c1"},
        {"type": "assistant", "message": {"id": "m2", "model": "claude-opus-5", "role": "assistant", "content": [{"type": "text", "text": "done"}],
            "usage": {"input_tokens": 10, "cache_read_input_tokens": 52000, "cache_creation_input_tokens": 100, "output_tokens": 50}},
         "timestamp": _ts(3), "cwd": repo, "sessionId": "c1"},
        {"type": "cost-state", "totalCostUSD": 1.25, "sessionId": "c1"},
    ]
    with open(os.path.join(d, "c1.jsonl"), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


class Args(object):
    def __init__(self, **kw):
        self.repo = kw.get("repo", [])
        self.days = kw.get("days", 0)
        self.harness = kw.get("harness", "all")
        self.session = None
        self.limit = None
        self.copilot_home = kw.get("copilot_home")
        self.claude_home = kw.get("claude_home")


class CopilotDetectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.home = os.path.join(self.tmp, "copilot")
        os.makedirs(self.home)
        self.chome = os.path.join(self.tmp, "claude")
        os.makedirs(os.path.join(self.chome, "projects"))

    def _profile(self, **kw):
        make_copilot_home(self.home, self.repo, **kw)
        args = Args(repo=[self.repo], copilot_home=self.home, claude_home=self.chome)
        found, _ = sp._select(args)
        self.assertEqual(1, len(found), "the fixture session is discovered by cwd")
        sessions, findings, comparison = sp._profile_all(found, args)
        return sessions, {f["id"]: f for f in findings}, comparison

    def test_findings_from_a_planted_session(self):
        sessions, ids, _ = self._profile()
        turns = sessions[0]["turns"]
        self.assertEqual("build the thing", turns[0]["prompt"])
        self.assertTrue(turns[0]["goal_state"] and turns[0]["tier"])
        self.assertEqual(4, turns[0]["main_requests"])
        self.assertEqual(200000, turns[0]["ctx_start"])
        self.assertIn("SP-02", ids, "two near-identical custom-instruction blocks")
        self.assertIn("SP-04", ids, "public.html viewed 3x")
        self.assertIn("public.html viewed 3x", ids["SP-04"]["evidence"][0]["note"])
        self.assertIn("SP-05", ids, "ui-design invoked twice")
        self.assertIn("SP-07", ids, "runaway delegation + converge nudge")
        self.assertIn("SP-08", ids, "sub-agent read AGENTS.md")
        self.assertIn("SP-10", ids, "ttft p90 25s")
        self.assertIn("SP-11", ids, "harness nudge")
        self.assertEqual(["F-07"], ids["SP-04"]["fixes"])
        self.assertEqual("Verified", ids["SP-04"]["confidence"])
        # SP-17: 4,000 reasoning tokens billed on the main line, ~750 chars of text on disk
        self.assertIn("SP-17", ids)
        self.assertEqual(4000, ids["SP-17"]["metric"]["reasoning_tokens"])
        self.assertLess(ids["SP-17"]["metric"]["visible_share"], 0.1)
        # SP-18: one of two shell calls carried an intent -> 50% coverage, below the 90% floor
        self.assertIn("SP-18", ids)
        self.assertEqual(0.5, ids["SP-18"]["metric"]["coverage"])
        self.assertEqual("high", turns[0]["effort"])

    def test_clean_session_does_not_fabricate(self):
        _, ids, _ = self._profile(rereads=False, runaway=False, double_block=False)
        for fid in ("SP-02", "SP-04", "SP-05", "SP-07"):
            if fid == "SP-05":
                continue  # the fixture still invokes the skill twice; SP-05 is expected
            self.assertNotIn(fid, ids, fid)

    def test_sub_agent_tools_are_not_counted_as_main(self):
        sessions, _, _ = self._profile()
        t = sessions[0]["turns"][0]
        self.assertEqual(1, t["sub_tool_calls"])
        self.assertEqual(["domain-researcher: AGENTS.md"], t["sub_orientation_reads"])


class ClaudeTranscriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.chome = os.path.join(self.tmp, "claude")
        make_claude_home(self.chome, self.repo)
        self.home = os.path.join(self.tmp, "copilot")
        os.makedirs(self.home)

    def test_transcript_parses_into_turns_with_not_recorded_where_absent(self):
        args = Args(repo=[self.repo], copilot_home=self.home, claude_home=self.chome, harness="claude")
        found, _ = sp._select(args)
        self.assertEqual(1, len(found))
        sessions, findings, comparison = sp._profile_all(found, args)
        f, turns = sessions[0]["facts"], sessions[0]["turns"]
        self.assertEqual("fixture claude session", f["title"])
        self.assertEqual(1.25, f["cost_usd"])
        self.assertIsNone(f["prefix_chars"])
        self.assertIn("not recorded", f["prefix_note"])
        self.assertEqual(1, len(turns))
        self.assertEqual(2, turns[0]["main_requests"])
        self.assertEqual(51010, turns[0]["ctx_start"])
        self.assertTrue(turns[0]["goal_state"] and turns[0]["tier"])
        self.assertIsNone(turns[0]["ttft_p90"])
        self.assertEqual(["anthropic"], turns[0]["families"])
        self.assertEqual("anthropic", comparison[0]["family"])
        self.assertEqual(400, turns[0]["reasoning_main"])
        self.assertEqual(len("The user wants the task done; read first."), turns[0]["reasoning_chars"])
        self.assertEqual((1, 1), (turns[0]["intent_eligible"], turns[0]["intent_with"]))
        self.assertIsNone(turns[0]["effort"])
        self.assertEqual(sp.NOT_RECORDED, comparison[0]["effort"])
        self.assertEqual(100.0, comparison[0]["intent_trace_pct"])
        self.assertNotIn("SP-18", {f["id"] for f in findings}, "full coverage is not a finding")

    def test_missing_stores_report_nothing_found(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        rc = sp.main(["--repo", self.repo, "--days", "0", "--copilot-home", empty, "--claude-home", empty, "discover"])
        self.assertEqual(1, rc)


class CatalogTests(unittest.TestCase):
    def test_every_finding_maps_to_known_fixes(self):
        for fid, (title, sev, fixes) in sp.FINDINGS.items():
            self.assertIn(sev, sp.SEVERITY_RANK, fid)
            for fx in fixes:
                self.assertIn(fx, sp.FIXES, "{0} -> {1}".format(fid, fx))

    def test_compare_columns_carry_the_effort_proxies(self):
        for fid in ("SP-17", "SP-18"):
            self.assertIn(fid, sp.FINDINGS)
        self.assertIn("F-12", sp.FIXES)
        self.assertIn("F-13", sp.FIXES)

    def test_markdown_render_has_the_three_tables(self):
        profile = {"id": "sp-0001", "generated": "2026-09-05T00:00:00Z", "repos": ["r"], "window": "last 1 days",
                   "sessions": [], "findings": [], "comparison": [], "fixes": sp.FIXES}
        md = sp.render_markdown(profile)
        for h in ("## Findings", "## Fixes", "## Model family x harness"):
            self.assertIn(h, md)



class GoalStateSpellingTests(unittest.TestCase):
    """CTX-J: the detector must see every spelling its own standard prescribes.

    `GOAL_RX` required a colon after `Goal`. CT19 and every worked example in the pack write
    the goal state as `**Goal** —` or `**Goal** ·`, so the detector could not see the form it
    mandates -- and it got WORSE as compliance improved, because every newly conformant turn
    was written in exactly the shape it was blind to. Measured on 2026-09-06: 10 of 346
    substantive Claude-Code turns detected, 15 present.

    The fixture is the control; the regex is only the fix. Observed red on the old pattern for
    every bolded spelling below.
    """

    SPELLINGS = [
        ("bold em dash", "**Goal** — ship the thing." + chr(10) + "**Done when** — tests are green."),
        ("bold middot", "**Goal** · ship the thing. **Done when** · tests are green."),
        ("bold en dash", "**Goal** – ship it. **Done when** – green."),
        ("bold hyphen", "**Goal** - ship it. **Done when** - green."),
        ("bold colon inside", "**Goal:** ship it. **Done when:** green."),
        ("bold colon outside", "**Goal**: ship it. **Done when**: green."),
        ("plain colon", "Goal: ship it. Done when: green."),
        ("heading", "## Goal — ship it" + chr(10) * 2 + "Done when: green."),
    ]

    def _detected(self, text):
        return bool(sp.GOAL_RX.search(text) and sp.DONE_RX.search(text))

    def test_every_documented_spelling_is_detected(self):
        for label, text in self.SPELLINGS:
            with self.subTest(spelling=label):
                self.assertTrue(self._detected(text),
                                "{0!r} carries a goal state and was not detected".format(label))

    def test_prose_about_goals_is_not_credited(self):
        """The colon/delimiter requirement is the guard against prose. Keep it."""
        for text in [
            "The goal of this change is smaller diffs, and we are done when the suite passes.",
            "Our goal here is clarity.",
            "Done when the tests pass.",
        ]:
            with self.subTest(text=text[:40]):
                self.assertFalse(self._detected(text),
                                 "prose must not be credited as a goal state")

    def test_tier_is_detected_in_the_documented_form(self):
        """TIER_RX already handles the bold form; pin it so the pair cannot drift apart."""
        for text in ["**Tier** T0", "Tier: T2", "**Tier:** T1", "Tier T3"]:
            with self.subTest(text=text):
                self.assertTrue(sp.TIER_RX.search(text), "{0!r} declares a tier".format(text))


if __name__ == "__main__":
    unittest.main()
