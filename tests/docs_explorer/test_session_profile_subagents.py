"""session-profile.py after the Addenda C/D profile (docs/profiles/addendum-cd.md, sp-0002):

F-18  the Claude reader walks `<session>/subagents/agent-*.jsonl` + `.meta.json` - 86% of a
      conductor programme's tokens lived there and the script reported 0 sub-agent requests.
F-19  a `<task-notification>` / local-command record is a continuation, not a human turn -
      50 of 89 "turns" were wake-ups and SP-09 fired on them.
cost  tokens and requests are the primary unit; `_meta.quota` where the harness carries it;
      dollars only as an "if API-billed" estimate at list rates that are printed.
SP-23 a sub-agent tool wait > 600 s on a non-shell tool (EnterWorktree waited 8,143 s).
SP-24 a gate's status behind a pipe (168 lines, 102 also committing).
SP-25 a failed heredoc run (70 of them).
SP-26 a resumed node whose second run set no marker (six nodes, up to 60,524 s unmeasured).
Every fixture record is in the shape the real store was observed to have (2026-09-14).
"""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pack" / "scripts" / "session-profile.py"

spec = importlib.util.spec_from_file_location("session_profile_cd", SCRIPT)
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)


def _ts(seconds):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "2026-09-12T{0:02d}:{1:02d}:{2:02d}.000Z".format(10 + h, m, s)


def _usage(cr=50000, cw=1000, out=200, inp=10):
    return {"input_tokens": inp, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw,
            "output_tokens": out}


def make_claude_home(home, repo, agent_tool_calls=60, wait_s=8000, resume_gap_s=2400,
                     notification=True, piped_gate=True, heredoc_fail=True, quota=None):
    slug = sp.claude_slug(repo)
    d = os.path.join(home, "projects", slug)
    os.makedirs(d)
    sid = "c-conductor"
    main = [
        {"type": "ai-title", "aiTitle": "conductor", "sessionId": sid},
        {"type": "user", "message": {"role": "user", "content": "dispatch wave 1"}, "origin": {"kind": "human"},
         "timestamp": _ts(0), "cwd": repo, "sessionId": sid},
        {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "text", "text": "**Goal:** wave 1. **Done when:** joined. **Tier:** T2 **Fan-out cap:** 3"},
            {"type": "tool_use", "id": "toolu_agent1", "name": "Agent", "input": {"description": "CV-1: the composer", "prompt": "..."}},
            {"type": "tool_use", "id": "toolu_bash1", "name": "Bash", "input": {
                "command": ("python tools/verify-test-run.py --update | tail -3 && git commit -qm x && git push"
                            if piped_gate else "python tools/verify-test-run.py --update"),
                "description": "Recount then commit"}},
            {"type": "tool_use", "id": "toolu_bash2", "name": "Bash", "input": {
                "command": "python - <<'EOF'\nprint('x')\nEOF", "description": "Run a program"}}],
            "usage": _usage()}, "timestamp": _ts(1), "cwd": repo, "sessionId": sid},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_bash1", "content": "5 of 35 FAILED\n[main abc] x"},
            {"type": "tool_result", "tool_use_id": "toolu_bash2", "content": (
                "/usr/bin/bash: -c: line 3: unexpected EOF while looking for matching `''" if heredoc_fail else "x")}]},
         "timestamp": _ts(2), "cwd": repo, "sessionId": sid},
    ]
    if notification:
        main.append({"type": "user", "message": {"role": "user", "content":
                     "<task-notification>\n<task-id>a1</task-id>\n<status>completed</status>\n<summary>Agent \"CV-1\" finished</summary>\n</task-notification>"},
                     "origin": {"kind": "task-notification"}, "timestamp": _ts(3000), "cwd": repo, "sessionId": sid})
        main.append({"type": "assistant", "message": {"id": "m2", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_bash3", "name": "Bash", "input": {"command": "git merge feature/cv-1", "description": "Join CV-1"}}],
            "usage": _usage(cr=60000)}, "timestamp": _ts(3001), "cwd": repo, "sessionId": sid})
        main.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_bash3", "content": "Merge made"}]},
            "timestamp": _ts(3002), "cwd": repo, "sessionId": sid})
        main.append({"type": "assistant", "message": {"id": "m3", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "text", "text": "joined"}], "usage": _usage(cr=61000)}, "timestamp": _ts(3003), "cwd": repo, "sessionId": sid})
        main.append({"type": "assistant", "message": {"id": "m4", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "text", "text": "and closed"}], "usage": _usage(cr=61500)}, "timestamp": _ts(3004), "cwd": repo, "sessionId": sid})
    if quota is not None:
        main[2]["message"]["_meta"] = {"quota": quota}
    with open(os.path.join(d, sid + ".jsonl"), "w", encoding="utf-8") as fh:
        for r in main:
            fh.write(json.dumps(r) + "\n")

    # The subagents store: one depth-1 node launched by toolu_agent1, one depth-2 review under it.
    subs = os.path.join(d, sid, "subagents")
    os.makedirs(subs)
    aid, rid = "a1111111111111111", "a2222222222222222"
    with open(os.path.join(subs, "agent-" + aid + ".meta.json"), "w", encoding="utf-8") as fh:
        json.dump({"agentType": "general-purpose", "description": "CV-1: the composer", "toolUseId": "toolu_agent1",
                   "spawnDepth": 1, "requestShape": "background"}, fh)
    with open(os.path.join(subs, "agent-" + rid + ".meta.json"), "w", encoding="utf-8") as fh:
        json.dump({"agentType": "test-architect", "description": "Gate: Test Architect", "toolUseId": "toolu_review1",
                   "parentAgentId": aid, "spawnDepth": 2}, fh)
    recs = [{"type": "user", "isSidechain": True, "agentId": aid, "message": {"role": "user", "content": "PERSONA brief"},
             "timestamp": _ts(5), "cwd": repo, "sessionId": sid}]
    t = 6
    for k in range(agent_tool_calls):
        mid = "msg_a_{0}".format(k)
        block = {"type": "tool_use", "id": "toolu_a_{0}".format(k), "name": "Bash",
                 "input": {"command": "python -m pytest -q", "description": "Run the suite"}}
        if k == 0:
            block = {"type": "tool_use", "id": "toolu_a_0", "name": "EnterWorktree", "input": {"path": "C:/wt"}}
        rec = {"type": "assistant", "isSidechain": True, "agentId": aid, "message": {
            "id": mid, "model": "claude-opus-5", "role": "assistant", "content": [block],
            "usage": _usage(cr=100000 + 5000 * k, out=300)}, "timestamp": _ts(t), "cwd": repo, "sessionId": sid}
        recs.append(rec)
        # the same message id is written once per streamed block in the real store
        recs.append(dict(rec))
        wait = wait_s if k == 0 else 1
        t += wait
        recs.append({"type": "user", "isSidechain": True, "agentId": aid, "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": block["id"], "content": (
                "Cannot enter worktree: the cwd is the repository root" if k == 0 else "ok")}]},
            "timestamp": _ts(t), "cwd": repo, "sessionId": sid})
        t += 1
    recs.append({"type": "assistant", "isSidechain": True, "agentId": aid, "message": {
        "id": "msg_a_launch", "model": "claude-opus-5", "role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_review1", "name": "Agent", "input": {"description": "Gate: Test Architect"}}],
        "usage": _usage(cr=400000)}, "timestamp": _ts(t), "cwd": repo, "sessionId": sid})
    t += 5
    recs.append({"type": "user", "isSidechain": True, "agentId": aid, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_review1", "content": "no findings"}]}, "timestamp": _ts(t), "cwd": repo, "sessionId": sid})
    recs.append({"type": "assistant", "isSidechain": True, "agentId": aid, "message": {
        "id": "msg_a_done", "model": "claude-opus-5", "role": "assistant", "content": [{"type": "text", "text": "report"}],
        "usage": _usage(cr=410000)}, "timestamp": _ts(t + 1), "cwd": repo, "sessionId": sid})
    first_run_end = t + 1
    if resume_gap_s:
        t = first_run_end + resume_gap_s
        recs.append({"type": "user", "isSidechain": True, "agentId": aid, "message": {"role": "user", "content": "apply the review fixes"},
                     "timestamp": _ts(t), "cwd": repo, "sessionId": sid})
        recs.append({"type": "assistant", "isSidechain": True, "agentId": aid, "message": {
            "id": "msg_a_resume", "model": "claude-opus-5", "role": "assistant", "content": [{"type": "text", "text": "done"}],
            "usage": _usage(cr=420000)}, "timestamp": _ts(t + 20), "cwd": repo, "sessionId": sid})
    with open(os.path.join(subs, "agent-" + aid + ".jsonl"), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    review = [
        {"type": "user", "isSidechain": True, "agentId": rid, "message": {"role": "user", "content": "PERSONA: test-architect"},
         "timestamp": _ts(t), "cwd": repo, "sessionId": sid},
        {"type": "assistant", "isSidechain": True, "agentId": rid, "message": {
            "id": "msg_r_1", "model": "claude-sonnet-5", "role": "assistant", "content": [
                {"type": "tool_use", "id": "toolu_r_1", "name": "Read", "input": {"file_path": "/r/x.md"}}],
            "usage": _usage(cr=20000, out=100)}, "timestamp": _ts(t + 1), "cwd": repo, "sessionId": sid},
        {"type": "user", "isSidechain": True, "agentId": rid, "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_r_1", "content": "..."}]}, "timestamp": _ts(t + 2), "cwd": repo, "sessionId": sid},
        {"type": "assistant", "isSidechain": True, "agentId": rid, "message": {
            "id": "msg_r_2", "model": "claude-sonnet-5", "role": "assistant", "content": [{"type": "text", "text": "no findings"}],
            "usage": _usage(cr=21000, out=100)}, "timestamp": _ts(t + 3), "cwd": repo, "sessionId": sid},
    ]
    with open(os.path.join(subs, "agent-" + rid + ".jsonl"), "w", encoding="utf-8") as fh:
        for r in review:
            fh.write(json.dumps(r) + "\n")
    return sid


class Args(object):
    def __init__(self, **kw):
        self.repo = kw.get("repo", [])
        self.days = 0
        self.harness = "claude"
        self.session = None
        self.limit = None
        self.copilot_home = kw.get("copilot_home")
        self.claude_home = kw.get("claude_home")


class SubagentStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.chome = os.path.join(self.tmp, "claude")
        self.copilot = os.path.join(self.tmp, "copilot")
        os.makedirs(self.copilot)

    def _profile(self, **kw):
        make_claude_home(self.chome, self.repo, **kw)
        args = Args(repo=[self.repo], copilot_home=self.copilot, claude_home=self.chome)
        found, _ = sp._select(args)
        self.assertEqual(1, len(found), "the fixture session is discovered by cwd")
        sessions, findings, comparison = sp._profile_all(found, args)
        return sessions[0], {f["id"]: f for f in findings}, comparison

    # ---- F-18: the store is read and attributed ----
    def test_sub_agent_requests_come_from_the_subagents_store(self):
        s, findings, _ = self._profile(agent_tool_calls=60)
        turn = s["turns"][0]
        # 60 tool-call requests + launch + done + resume = 63 for the node, 2 for the review;
        # a message id streamed twice counts once.
        self.assertEqual(65, turn["sub_requests"])
        self.assertEqual(65, s["facts"]["subagents"]["requests"])
        self.assertEqual(2, s["facts"]["subagents"]["agents"])
        node = [n for n in s["facts"]["nodes"] if n["depth"] == 1][0]
        self.assertEqual("CV-1: the composer", node["name"])
        self.assertEqual(61, node["tool_calls"])
        self.assertEqual("claude-opus-5", node["model"])
        self.assertGreater(node["ctx_max"], 400000)
        self.assertEqual(1, node["reviews"], "a depth-2 review is attached to its parent")
        self.assertIn("SP-07", findings, "sub-agent runaway now fires on a 61-tool-call node")
        self.assertIn("CV-1", findings["SP-07"]["evidence"][0]["note"])

    def test_the_turn_row_names_its_nodes_not_a_placeholder(self):
        s, _, _ = self._profile()
        names = [a["name"] for a in s["turns"][0]["sub_agents"]]
        self.assertEqual(["CV-1: the composer"], names)
        # the turn row is the DELEGATION's total: the node's 61 calls plus its review's 1 -
        # the node table keeps the two apart (depth 1 / depth 2)
        self.assertEqual(62, s["turns"][0]["sub_agents"][0]["tool_calls"])

    def test_a_missing_subagents_dir_reads_zero_and_says_so(self):
        make_claude_home(self.chome, self.repo)
        import shutil
        shutil.rmtree(os.path.join(self.chome, "projects", sp.claude_slug(self.repo), "c-conductor"))
        args = Args(repo=[self.repo], copilot_home=self.copilot, claude_home=self.chome)
        found, _ = sp._select(args)
        sessions, _, _ = sp._profile_all(found, args)
        self.assertEqual(0, sessions[0]["facts"]["subagents"]["agents"])
        self.assertEqual(sp.NOT_RECORDED, sessions[0]["facts"]["subagents"]["store"])

    # ---- F-19: notifications are continuations ----
    def test_a_task_notification_is_not_a_human_turn(self):
        s, findings, _ = self._profile(notification=True)
        self.assertEqual(1, len(s["turns"]), "the wake-up continues the dispatch turn")
        self.assertEqual(3, s["turns"][0]["main_requests"] - 1, "the join's requests belong to that turn")
        self.assertNotIn("SP-09", findings, "no goal-state finding on a notification")

    # ---- cost: tokens and requests first, dollars only if API-billed ----
    def test_tokens_and_requests_are_the_primary_unit_and_dollars_are_labelled(self):
        s, _, _ = self._profile()
        f = s["facts"]
        self.assertEqual(4, f["requests"]["main"])
        self.assertEqual(65, f["requests"]["subagents"])
        self.assertIn("cache_read", f["tokens"])
        self.assertEqual(sp.NOT_RECORDED, f["quota"])
        self.assertIsNotNone(f["est_usd_if_api_billed"])
        self.assertIn("2026-06-24", f["est_usd_note"])
        md = sp.render_markdown({"id": "sp-t", "generated": "now", "repos": [self.repo], "repo_labels": ["repo"],
                                 "window": "all", "sessions": [s], "findings": [], "comparison": [], "fixes": sp.FIXES})
        self.assertIn("if API-billed", md)
        self.assertIn("## Nodes", md)
        self.assertIn("CV-1: the composer", md)

    def test_quota_is_read_when_the_harness_carries_it(self):
        s, _, _ = self._profile(quota={"five_hour": {"used": 0.42}})
        self.assertEqual({"five_hour": {"used": 0.42}}, s["facts"]["quota"])

    # ---- SP-23 .. SP-26 ----
    def test_sp23_a_long_wait_on_a_deferred_tool_in_a_node(self):
        s, findings, _ = self._profile(wait_s=8000)
        self.assertIn("SP-23", findings)
        self.assertIn("EnterWorktree", findings["SP-23"]["evidence"][0]["note"])
        self.assertIn("F-25", findings["SP-23"]["fixes"])
        _, clean, _ = SubagentStoreTests._fresh(self).__enter__()._profile(wait_s=5)
        self.assertNotIn("SP-23", clean)

    def test_sp24_a_gate_behind_a_pipe_and_the_commit_on_the_same_line(self):
        s, findings, _ = self._profile(piped_gate=True)
        self.assertIn("SP-24", findings)
        self.assertEqual(1, findings["SP-24"]["metric"]["piped_gate_lines"])
        self.assertEqual(1, findings["SP-24"]["metric"]["also_commit_merge_push"])
        self.assertIn("F-20", findings["SP-24"]["fixes"])
        _, clean, _ = SubagentStoreTests._fresh(self).__enter__()._profile(piped_gate=False)
        self.assertNotIn("SP-24", clean)

    def test_sp25_a_failed_heredoc_run(self):
        s, findings, _ = self._profile(heredoc_fail=True)
        self.assertIn("SP-25", findings)
        self.assertEqual(1, findings["SP-25"]["metric"]["failed_heredocs"])
        self.assertIn("F-21", findings["SP-25"]["fixes"])
        _, clean, _ = SubagentStoreTests._fresh(self).__enter__()._profile(heredoc_fail=False)
        self.assertNotIn("SP-25", clean)

    def test_sp26_a_resumed_node_whose_second_run_is_unmarked(self):
        s, findings, _ = self._profile(resume_gap_s=2400)
        self.assertIn("SP-26", findings)
        self.assertIn("F-24", findings["SP-26"]["fixes"])
        node = [n for n in s["facts"]["nodes"] if n["depth"] == 1][0]
        self.assertEqual(1, node["resumes"])
        _, clean, _ = SubagentStoreTests._fresh(self).__enter__()._profile(resume_gap_s=0)
        self.assertNotIn("SP-26", clean)

    def test_new_findings_and_fixes_are_in_the_catalogs(self):
        for fid in ("SP-23", "SP-24", "SP-25", "SP-26"):
            self.assertIn(fid, sp.FINDINGS)
            for fx in sp.FINDINGS[fid][2]:
                self.assertIn(fx, sp.FIXES)
        for fx in ("F-18", "F-19", "F-20", "F-21", "F-24", "F-25"):
            self.assertIn(fx, sp.FIXES)

    class _fresh(object):
        """A second, clean fixture in a fresh temp dir - the negative half of each detector."""

        def __init__(self, outer):
            self.outer = outer

        def __enter__(self):
            t = SubagentStoreTests()
            t.setUp()
            return t


class TheScriptsOwnAuditEntryLeavesTheSkillsMarkerAlone(unittest.TestCase):
    """Pack finding #2, re-observed on 2026-09-14: `session-profile.py profile` appended its own
    audit entry and CONSUMED the /session-profiler skill's start marker, so the skill's closing
    entry measured from a re-mark. The script measures its own run with --started and never
    touches a marker."""

    def test_the_marker_survives_the_scripts_append(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "repo")
        os.makedirs(os.path.join(repo, "docs", "audit"))
        # a deployed audit-log.py beside the profiler, as in a consuming repo
        scripts = os.path.join(repo, "docs", "ai-forward-pack", "scripts")
        os.makedirs(scripts)
        import shutil
        shutil.copy(ROOT / "pack" / "scripts" / "audit-log.py", scripts)
        audit = os.path.join(scripts, "audit-log.py")
        subprocess.run([sys.executable, audit, "--root", os.path.join(repo, "docs"), "start", "--session", "profiler"],
                       check=True, capture_output=True)
        sp._audit(repo, "sp-0001", 1, 0, "profiler")
        starts = json.load(open(os.path.join(repo, "docs", "audit", ".run-starts.json"), encoding="utf-8"))
        self.assertIn("profiler", starts, "the skill's marker must survive the script's own append")
        entries = [json.loads(l) for l in open(os.path.join(repo, "docs", "audit", "audit-log.jsonl"), encoding="utf-8") if l.strip()]
        self.assertEqual(1, len(entries))
        self.assertIn("duration_seconds", entries[0], "the script measures its own run")


if __name__ == "__main__":
    unittest.main()
