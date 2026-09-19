---
id: kb-multi-agent-coordination-references
title: "Reference information — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, references, specs, papers]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  The standards, specifications, official harness documentation and seminal works this base
  rests on — what each defines and what it requires of the pack.
---

# Reference information

## Standards & specifications

- **MCP, revision 2026-07-28** — stateless core; MRTR; Tasks as extension `io.modelcontextprotocol/tasks`;
  Roots/Sampling/Logging deprecated (12-month runway); HTTP+SSE deprecated for Streamable HTTP;
  CIMD replaces DCR. Requires: do not lean on sampling; expose the coordinator to harnesses as an
  MCP **stdio** server (stdio is unaffected by the localhost DNS-rebinding class). *(Verified, [AC-11][AC-12][AC-34][P2P-20])*
- **A2A v1.0 (April 2026, Linux Foundation / AAIF)** — Agent Card at `/.well-known/agent-card.json`;
  task states `submitted, working, input_required, auth_required, completed, failed, canceled,
  rejected`; JSON-RPC 2.0 / gRPC / HTTP+JSON; SSE and webhook push; no election surface. Requires
  nothing today; keep the Session Card *shape* compatible. *(Verified, [AC-13][AC-15])*
- **Agent Client Protocol (Zed)** — editor↔agent JSON-RPC over stdio; registry with JetBrains;
  Claude Code, Codex, Copilot, Gemini CLI registered. Out of scope for agent↔agent. *(Verified, [AC-16])*
- **git-update-ref / git-push** — `update-ref <ref> <new> <old>` is a compare-and-swap (40 zeros =
  must not exist); `--stdin` transactions are atomic for writers, not isolated for readers;
  `--force-with-lease=<ref>:<expect>` refuses a stale expect; bare `--force-with-lease` is
  defeated by background fetches; `--force-if-includes` exists. *(Verified, [SCH-13][QLE-11][SPK-1][SPK-2])*
- **git merge=union driver** — keeps both sides' lines, no conflict markers, order not
  preserved; must be path-scoped to append-only files. *(Verified, [P2P-18][SPK-3])*
- **Claude Code docs (v2.1.x, 2026-09-18)** — agent teams; cross-session messaging (socket,
  token, delivery semantics, caps); channels; headless `-p`; hooks (`Stop` exit 2 blocks;
  `TeammateIdle`/`TaskCreated`/`TaskCompleted` exit 2 rejects); costs. *(Verified, [AC-5]–[AC-10][P2P-24]–[P2P-26])*
- **Codex developer commands** — `codex exec`, `app-server --listen ws://`, `--remote`, `codex mcp`.
  *(Verified, [AC-23])*
- **Copilot CLI docs** — `/fleet`; programmatic `copilot -p`; `--allow-all-tools` / `--deny-tool`
  precedence. Hook event names known only from a community reference (Flagged). *(Verified/Flagged, [AC-18][AC-19][AC-39])*
- **Antigravity docs** — custom subagents, `invoke_subagent`, `define_subagent`, `/agents`.
  *(Verified, [AC-21][AC-22])*
- **Grok Build user guide** — `spawn_subagent`, `--parallel` ≤ 8, worktree per child. *(Verified, [AC-24])*
- **Kubernetes `client-go` leader election** — LeaseDuration 15 s, RenewDeadline 10 s, RetryPeriod
  2 s, JitterFactor 1.2, constraints, no-fencing disclaimer. *(Verified, [QLE-5])*
- **Consul sessions** — lock-delay default 15 s (0–60 s). *(Verified, [QLE-10])*
- **etcd `concurrency`** — Election API, session TTL 60 s, `Rev()` as fencing token. *(Verified, [QLE-21])*
- **hashicorp/memberlist `config.go`** — Local/LAN/WAN profiles. *(Verified, [P2P-3])*
- **Akka `reference.conf`** — phi-accrual defaults. *(Verified, [P2P-6])*
- **CVE-2025-66414 / GHSA-w48q-cv73-mx4w** — DNS rebinding against localhost MCP servers; fixed
  in TS SDK 1.24.0; stdio unaffected. *(Verified, [P2P-20])*

## Seminal / foundational works

- **Fischer, Lynch, Paterson (1985)** — impossibility of consensus with one faulty process. *[QLE-1]*
- **Gray & Cheriton (SOSP 1989)** — leases: short terms, failures cost performance not correctness. *[SCH-9][P2P-8]*
- **Burrows (OSDI 2006)** — Chubby: coarse locks, sequencer, lock-delay, 45 s grace, service over library. *[QLE-8][QLE-9][SCH-10]*
- **Ongaro & Ousterhout (2014); Ongaro thesis** — Raft terms, randomized timeouts, pre-vote, leadership transfer, joint consensus. *[QLE-2][QLE-3]*
- **Howard et al. (2016)** — Flexible Paxos: intersection only across phases. *[QLE-4]*
- **Garcia-Molina (1982)** — Bully; the reorganisation phase. *[QLE-15]*
- **Kleppmann (2016)** — fencing tokens; Redlock critique. *[SCH-12][QLE-7]*
- **Jepsen, etcd 3.4.3 (2020)** — locks are not mutual exclusion; ~18% loss; revision as fencing token. *[QLE-6]*
- **Das, Gupta, Motivala (2002)** — SWIM. *[P2P-1][P2P-2]*
- **Hayashibara et al. (2004)** — phi-accrual failure detector. *[P2P-7]*
- **Leitão et al. (2007)** — Plumtree eager/lazy push. *[P2P-12]*
- **Shapiro et al. (2011)** — CRDT catalogue (G-Set, OR-Set, LWW). *[P2P-13]*
- **Kulkarni, Demirbas et al.** — Hybrid Logical Clocks. *[P2P-14]*
- **Schwarzkopf et al. (EuroSys 2013)** — Omega: shared-state optimistic scheduling. *[SCH-1]*
- **Blumofe & Leiserson (1999); Brent** — work stealing `T1/P + O(T∞)`; `T_P ≤ T1/P + T∞`. *[SCH-5][SCH-6]*
- **Gunther** — Universal Scalability Law (retrograde scalability). *[SCH-7]*
- **Topcuoglu, Hariri, Wu (2002)** — HEFT. *[SCH-14]*
- **Smith (1980)** — Contract Net. *[SCH-24]*
- **Bird et al. (FSE 2011)** — "Don't Touch My Code!" ownership and defects. *[SCH-15]*
- **Brun et al. (FSE 2011)** — 16% of merges conflict. *[SCH-16]*
- **Owhadi-Kareshk et al. (ESEM 2019); Vale et al. (EMSE 2023); ConE (TOSEM 2021)** — conflict prediction. *[SCH-17][SCH-19][SCH-18]*
- **Sadowski et al. (ICSE-SEIP 2018)** — code review at Google; one primary reviewer. *[SCH-34]*
- **Cemri et al. (2025)** — MAST failure taxonomy. *[AC-25][SCH-27][QLE-18]*
- **Anthropic (2025-06-13; 2026-02-05)** — multi-agent research system; C-compiler run. *[AC-1][AC-4]*
- **Cognition (2025-06-12)** — Don't Build Multi-Agents. *[AC-2]*
- **Magentic-UI (2025)** — human-in-the-loop agentic systems. *[AC-26]*
- **Pugachev (2025)** — CodeCRDT. *[P2P-17]*
- **Google SRE Book — Managing Incidents; Amazon Single-Threaded Owner** — designated leadership. *[QLE-20][QLE-34]*

## Repository sources read this session (not recalled)

- **ai-forward:** `pack/scripts/coord-core.py` (21 verbs; `TTL_DEFAULT=300`, `TTL_CAP=900`;
  8-hour staleness at `:32`/`:2209`; `HARNESS_STATUS` at `:1248`), `docs/design/coord-*-phase1..4.md`,
  `docs/proof/coord-collaboration-phase4.md`, `.claude/skills/{prepare-for-coordination,execute-with-coordination}/SKILL.md`,
  `.claude/knowledge/{session-worktree-discipline,execution-graph-optimization}.md`,
  `docs/dreams/drm-0010/dream.json` (p44–p58), `docs/profiles/sp-000{1,2,4,5,8}/profile.md`,
  `docs/lessons/defect-classes.md`, `.gitignore:28-32`, `/private/tmp/ai-forward-codex-readiness/docs/{investigations,plans}/codex-readiness.md`.
- **ai-de (main @ 62e3ed29):** `docs/collaboration/session-contracts.md`, `.agents/{log,decisions,requests.jsonl,sessions}`
  (counts computed read-only), `docs/coordination/join.json`, `docs/notes/d1-r5-producer-ack.md`,
  `tools/verify-ruling-citations.py`, `docs/profiles/addendum-cd.md`, `docs/notes/collaboration-not-happening.md`,
  `docs/lessons/defect-classes.md` (DC-067, DC-153, DC-163, DC-206, DC-216, DC-226, DC-227),
  `docs/knowledge/multi-agent-coordination/index.md`, `.gitignore:552-565`.
