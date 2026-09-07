"""session-profile.py: the profiler reads the harness stores and produces findings with evidence.

The fixtures are synthetic stores in the shapes the real ones were observed to have (Copilot
CLI 1.0.83 session-store.db + events.jsonl; Claude Code 2.1.x transcript records). Each test
pins one detector against an exact oracle: the finding id appears with the evidence the fixture
planted, and does not appear when the fixture is clean. A missing store reports `not recorded`.
"""
import importlib.util
import io
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



class PlatformIndependentPathTests(unittest.TestCase):
    """A store recorded on Windows must read the same from Linux.

    `--copilot-home` exists so a store can be profiled from anywhere, and `os.path.basename`
    is per-platform: on POSIX it treats a backslash as an ordinary character, so
    "C:\\repo\\AGENTS.md" came back whole and the orientation-read detector compared it
    against a basename that could never match. Green on Windows, red on ubuntu-latest - which
    is exactly why it survived. Observed red in CI run 34061643244.
    """

    def test_basename_splits_on_both_separators(self):
        self.assertEqual(sp._basename("C:" + chr(92) + "repo" + chr(92) + "AGENTS.md"),
                         "AGENTS.md")
        self.assertEqual(sp._basename("/repo/AGENTS.md"), "AGENTS.md")
        self.assertEqual(sp._basename("C:/repo/AGENTS.md"), "AGENTS.md")
        self.assertEqual(sp._basename("AGENTS.md"), "AGENTS.md")

    def test_it_tolerates_the_empty_and_missing_cases(self):
        self.assertEqual(sp._basename(""), "")
        self.assertIsNone(sp._basename(None))



class MainLineShareTests(unittest.TestCase):
    """SP-19 (F-14, class CTX-M): the measured half of the main-line budget.

    CT19's `Main-line budget:` is a DECLARATION - an agent cannot count its own model
    requests. This is the measurement it is reconciled against, read from the store by
    `initiator`: `agent`, `user` and `compaction` are the main line; `sub-agent` is not.

    The shape it exists to surface, from sp-0003: 714 main-line requests for 89,429 AIU
    against 701 delegate requests for 8,491 - 91% of the session at 10x the cost per request,
    while every budget the pack carried bounded the delegates.
    """

    def test_the_split_names_the_main_line_and_the_delegates(self):
        share = sp.main_line_share({"agent": {"requests": 688, "cost": 74445.0},
                                    "user": {"requests": 24, "cost": 12853.0},
                                    "compaction": {"requests": 2, "cost": 2132.0},
                                    "sub-agent": {"requests": 701, "cost": 8491.0}})
        self.assertEqual(share["main_requests"], 714)
        self.assertEqual(share["sub_requests"], 701)
        self.assertAlmostEqual(share["main_pct"], 91.3, places=0)
        self.assertGreater(share["cost_ratio"], 9)

    def test_no_delegates_is_a_hundred_percent_not_a_division_by_zero(self):
        share = sp.main_line_share({"agent": {"requests": 10, "cost": 100.0}})
        self.assertEqual(share["main_pct"], 100.0)
        self.assertIsNone(share["cost_ratio"], "no delegates means no ratio to report")

    def test_an_empty_corpus_reports_not_recorded_rather_than_zero(self):
        """R4/IO8: a share over nothing is not a measurement."""
        share = sp.main_line_share({})
        self.assertIsNone(share["main_pct"])
        self.assertIsNone(share["cost_ratio"])

    def test_sp19_is_in_the_finding_catalog_and_maps_to_a_fix(self):
        ids = dict(sp.FINDINGS)
        self.assertIn("SP-19", ids)
        self.assertTrue(ids["SP-19"][2], "SP-19 must name the fix it belongs to")



class LateAdditionTests(unittest.TestCase):
    """SP-20 (F-15, class CTX-N): a late addition landing on an unbounded turn.

    `/also` exists to append a thought without derailing work in flight, and its guard is on
    DIRECTION - "an extension is absorbed; a reversal is raised". It has no guard on SIZE.
    Measured in sp-0004: two turns were `/also`, both were the only substantive turns on that
    model carrying neither a goal state nor a tier, and one became 81 main requests, 6
    sub-agents, 83 minutes and 13,411 AIU - the most expensive turn in the session.

    The skill assumed a goal state existed ("re-read the goal state") and had a branch for
    nothing-in-flight, but none for the case that actually happened: work in flight that never
    declared one. An addition to an unbounded turn inherits unboundedness rather than
    acquiring a bound.
    """

    def test_an_also_turn_with_no_goal_state_is_flagged(self):
        turns = [{"turn": 9, "prompt": "/also i wonder if we should have an external link",
                  "goal_state": False, "tier": False, "sub_agents": []}]
        self.assertTrue(sp.late_addition_findings(turns))

    def test_an_also_turn_that_fans_out_with_no_tier_is_flagged(self):
        turns = [{"turn": 10, "prompt": "/also in the content creator side",
                  "goal_state": True, "tier": False,
                  "sub_agents": [{"name": "a"}, {"name": "b"}]}]
        rows = sp.late_addition_findings(turns)
        self.assertTrue(rows)
        self.assertIn("tier", rows[0]["reason"].lower())

    def test_a_bounded_also_turn_is_not_flagged(self):
        turns = [{"turn": 11, "prompt": "/also add a sort", "goal_state": True, "tier": True,
                  "sub_agents": []}]
        self.assertEqual(sp.late_addition_findings(turns), [])

    def test_a_turn_that_is_not_an_also_is_not_this_finding(self):
        """SP-09 already owns the generic missing-goal-state case; this one is about /also."""
        turns = [{"turn": 0, "prompt": "do the next steps", "goal_state": False,
                  "tier": False, "sub_agents": []}]
        self.assertEqual(sp.late_addition_findings(turns), [])

    def test_the_command_form_is_recognised_too(self):
        """Copilot records the slash command as a command-name block, not bare text."""
        turns = [{"turn": 3, "prompt": "<command-message>also</command-message> <command-name>",
                  "goal_state": False, "tier": False, "sub_agents": []}]
        self.assertTrue(sp.late_addition_findings(turns))

    def test_sp20_is_in_the_catalog_and_maps_to_a_fix(self):
        ids = dict(sp.FINDINGS)
        self.assertIn("SP-20", ids)
        self.assertTrue(ids["SP-20"][2])


class AlsoSkillContractTests(unittest.TestCase):
    """The skill has to prescribe what the profiler measures, or SP-20 flags a rule
    that was never written down."""

    def _skill(self):
        return io.open(os.path.join(ROOT, "pack", "commands", "also", "SKILL.md"),
                       encoding="utf-8").read()

    def test_it_handles_work_in_flight_with_no_goal_state(self):
        text = self._skill().lower()
        self.assertIn("no goal state", text,
                      "the measured case - work in flight that never declared a goal state - "
                      "is the one the skill had no branch for")

    def test_it_requires_the_tier_to_be_raised_explicitly(self):
        text = self._skill().lower()
        self.assertTrue("raise the tier" in text or "raises the tier" in text,
                        "an addition that exceeds the in-flight tier must raise it explicitly "
                        "rather than absorb silently - that is the magnitude guard")

    def test_the_copilot_prompt_carries_it_too(self):
        text = io.open(os.path.join(ROOT, "pack", "adapters", "copilot", "prompts",
                                    "also.prompt.md"), encoding="utf-8").read().lower()
        self.assertIn("no goal state", text)



class EffectiveModelTests(unittest.TestCase):
    """SP-21 (F-16, class CTX-O): the recorded model is not the model that ran.

    Measured in sp-0005: the session's stored settings read `model: claude-opus-4.8` while
    the usage events record 1,022 requests to `gpt-6-astra` - 95% of the spend - plus
    gpt-5.6-sol, gpt-5.4, gpt-5.4-mini and claude-sonnet-5 across sub-agents. The main line
    switched family at turn 3 and never switched back. ELEVEN distinct model/effort
    combinations ran under one recorded setting.

    The setting is a true statement about what was CONFIGURED and is simply not a statement
    about what EXECUTED. Anything keyed to it - guidance selected per model, a cost
    expectation, this profiler's own family attribution - is keyed to the wrong field, and
    the error is invisible because both values are plausible.

    The profiler already reads the per-request model, which is the only reason the
    discrepancy was visible at all. That was a happy accident of implementation, not a
    contract. These tests make it one.
    """

    def _facts(self, setting, models):
        return {"settings": {"model": setting}, "main_models": models}

    def test_the_effective_model_is_the_costliest_main_line_model(self):
        eff = sp.effective_model({"gpt-6-astra": {"requests": 1022, "cost": 90398.0},
                                  "claude-opus-4.8": {"requests": 53, "cost": 3051.0}})
        self.assertEqual(eff["model"], "gpt-6-astra")
        self.assertEqual(eff["distinct"], 2)
        self.assertAlmostEqual(eff["share"], 96.7, places=0)

    def test_an_empty_corpus_reports_nothing_rather_than_a_guess(self):
        eff = sp.effective_model({})
        self.assertIsNone(eff["model"])
        self.assertIsNone(eff["share"])

    def test_a_mismatch_between_setting_and_effective_model_is_flagged(self):
        rows = sp.model_attribution({"model": "claude-opus-4.8"},
                                    {"gpt-6-astra": {"requests": 1022, "cost": 90398.0}})
        self.assertTrue(rows["mismatch"])
        self.assertEqual(rows["recorded"], "claude-opus-4.8")
        self.assertEqual(rows["effective"], "gpt-6-astra")

    def test_a_matching_setting_is_not_flagged(self):
        rows = sp.model_attribution({"model": "gpt-6-astra"},
                                    {"gpt-6-astra": {"requests": 10, "cost": 100.0}})
        self.assertFalse(rows["mismatch"])

    def test_an_absent_setting_is_not_a_mismatch(self):
        """Claude Code records no model setting. Absent is not wrong (IO8)."""
        rows = sp.model_attribution({}, {"claude-opus-5": {"requests": 3, "cost": 9.0}})
        self.assertFalse(rows["mismatch"])
        self.assertIsNone(rows["recorded"])

    def test_the_setting_running_as_a_minority_still_counts_as_a_mismatch(self):
        """The recorded model DID run - on 5% of requests. Presence is not attribution."""
        rows = sp.model_attribution({"model": "claude-opus-4.8"},
                                    {"gpt-6-astra": {"requests": 1022, "cost": 90398.0},
                                     "claude-opus-4.8": {"requests": 53, "cost": 3051.0}})
        self.assertTrue(rows["mismatch"],
                        "the setting ran, but it is not what the session was")

    def test_sp21_is_in_the_catalog_and_maps_to_a_fix(self):
        ids = dict(sp.FINDINGS)
        self.assertIn("SP-21", ids)
        self.assertTrue(ids["SP-21"][2])

    def test_attribution_reads_usage_events_not_settings(self):
        """The contract, pinned: the family column must be built from the per-request model.

        If this ever regresses to reading `settings.model`, every family comparison in every
        profile silently becomes a statement about configuration instead of execution.
        """
        src = io.open(os.path.join(ROOT, "pack", "scripts", "session-profile.py"),
                      encoding="utf-8").read()
        # Two ends, because the contract spans them: the turn's families are built from the
        # per-request model, and the comparison keys on those - never on the setting.
        self.assertIn('"families": sorted({model_family(m) for m in models})', src,
                      "a turn's families must come from the per-request models")
        body = src.split("def family_comparison(", 1)[1].split(chr(10) + "def ", 1)[0]
        self.assertIn('t["families"]', body,
                      "the comparison must key on the turn's measured families")
        for keyed_to_config in ('settings"]["model"', 'settings.get("model")', 'settings["model"]'):
            self.assertNotIn(keyed_to_config, body,
                             "family attribution read the recorded SETTING: every comparison in "
                             "every profile would silently become a statement about "
                             "configuration instead of execution")



class MechanicalAtReasoningPricesTests(unittest.TestCase):
    """SP-22 (F-17): a node that needed no reasoning, billed as though it did.

    Measured across sp-0006: `/updatepack` ran twice in one session - 1,179 AIU on
    claude-opus-4.8 and 8,890 AIU on gpt-6-astra. Same skill, same repo, 7.5x. And
    "yes commit and push/merge all" cost 5,173 AIU across 21 requests. None of that work is
    novel; all of it is a script with a reviewer.

    GO19 already says to allocate the model tier per PHASE. What it does not say - and what
    TheTerrace's A1 plan adds with its per-node `Capability` column - is finer and stronger:
    a node declares whether it needs REASONING at all. A node that is Deterministic mechanics
    should not be model-backed, not merely cheaply model-backed. "Cheap tier" and "no tier"
    are different answers, and the second is usually available for closing work.

    The detector is deliberately dumb about intent: it matches the mechanical-close SHAPE of
    a prompt and reports what it cost, at what effort. It never claims the work was wrong.
    """

    def test_a_mechanical_prompt_at_high_effort_and_real_cost_is_flagged(self):
        turns = [{"turn": 12, "prompt": "yes commit and push/merge all", "effort": "high",
                  "cost_aiu": 5173.3, "main_requests": 21}]
        rows = sp.mechanical_cost_findings(turns)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["turn"], 12)

    def test_updatepack_is_recognised_as_mechanical(self):
        turns = [{"turn": 11, "prompt": "/updatepack", "effort": "high",
                  "cost_aiu": 8890.4, "main_requests": 44}]
        self.assertTrue(sp.mechanical_cost_findings(turns))

    def test_a_cheap_mechanical_turn_is_not_flagged(self):
        """The finding is the PRICE, not the mechanics. Closing work is legitimate."""
        turns = [{"turn": 4, "prompt": "commit and push", "effort": "low",
                  "cost_aiu": 29.5, "main_requests": 1}]
        self.assertEqual(sp.mechanical_cost_findings(turns), [])

    def test_a_reasoning_turn_is_never_this_finding(self):
        turns = [{"turn": 5, "prompt": "ground yourself in the repo knowledge and the specs",
                  "effort": "high", "cost_aiu": 3092.7, "main_requests": 34}]
        self.assertEqual(sp.mechanical_cost_findings(turns), [])

    def test_a_turn_with_no_recorded_cost_is_not_guessed_at(self):
        """IO8: absent cost is absent, not zero and not a finding."""
        turns = [{"turn": 2, "prompt": "commit and push", "effort": "high",
                  "cost_aiu": None, "main_requests": 30}]
        self.assertEqual(sp.mechanical_cost_findings(turns), [])

    def test_sp22_is_in_the_catalog_and_maps_to_a_fix(self):
        ids = dict(sp.FINDINGS)
        self.assertIn("SP-22", ids)
        self.assertTrue(ids["SP-22"][2])


class NodeCapabilityTests(unittest.TestCase):
    """The doctrine half: a node says what it needs, or nothing can be allocated to it."""

    def _go(self):
        return io.open(os.path.join(ROOT, "pack", "knowledge",
                                    "execution-graph-optimization.md"), encoding="utf-8").read()

    def test_go19_requires_a_per_node_capability(self):
        text = self._go().lower()
        self.assertIn("deterministic mechanics", text,
                      "GO19 allocates a tier per phase; a node must also be able to say it "
                      "needs no model at all - `cheap tier` and `no tier` are different answers")

    def test_the_optimize_graph_node_table_carries_the_column(self):
        text = io.open(os.path.join(ROOT, "pack", "commands", "optimize-graph", "SKILL.md"),
                       encoding="utf-8").read().lower()
        self.assertIn("capability", text,
                      "the node table is where a plan declares it, or the rule is prose")



class EveryFindingIsReachableTests(unittest.TestCase):
    """A finding in the catalog that no detector emits is a finding that never fires.

    Written after SP-22's emit was inserted into the wrong function - `_settings_note` shares
    an anchor line with `detect`, and the pure-function tests passed because they never
    rendered a session. The real profile run caught it with a NameError. This is the control
    that catches it at test time instead.
    """

    def test_every_catalog_id_is_emitted_somewhere(self):
        src = io.open(os.path.join(ROOT, "pack", "scripts", "session-profile.py"),
                      encoding="utf-8").read()
        # The two aggregate findings are raised by the comparison, not the per-session detector.
        emitted = set()
        for fid in sp.FINDINGS:
            if 'add("{0}"'.format(fid) in src or '"id": "{0}"'.format(fid) in src:
                emitted.add(fid)
        missing = sorted(set(sp.FINDINGS) - emitted)
        self.assertEqual(missing, [],
                         "catalogued but never emitted: " + ", ".join(missing))

    def test_every_finding_names_a_fix_that_exists(self):
        fixes = set(sp.FIXES)
        for fid, (_title, _sev, fix_ids) in sp.FINDINGS.items():
            for f in fix_ids:
                self.assertIn(f, fixes, "{0} names {1}, which is not in the fix catalog".format(fid, f))


if __name__ == "__main__":
    unittest.main()
