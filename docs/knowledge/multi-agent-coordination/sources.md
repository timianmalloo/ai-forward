---
id: kb-multi-agent-coordination-sources
title: "Sources — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, sources]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  Every source cited in this base, by track tag, with type, URL, access date and what it was
  used for. All accessed 2026-09-18 unless noted. Executed spikes and in-session observations
  are listed as sources of the same standing.
---

# Sources

All accessed **2026-09-18**. Types: primary (paper/spec/source code), official (vendor docs),
secondary (blog/encyclopedia/community), executed (spike run this session), observed (this
session's harness).

## Executed spikes and observations

| Tag | Title | Type | Location | Used for |
|---|---|---|---|---|
| SPK-1 | `git update-ref` compare-and-swap | executed | scratchpad `spike-cas-union.sh` (git 2.54.0, macOS) | local CAS exit codes |
| SPK-2 | `git push --force-with-lease=<ref>:<expect>` | executed | `spike-lease2.sh`, `spike-lease3.sh` | stale refusal; `--force` override |
| SPK-3 | `merge=union` under merge / rebase / identical lines | executed | `spike-cas-union.sh`, `spike-union-rebase.sh` | both claims survive; convergence |
| OBS-1 | Claude Code `SendMessage` / `ListAgents` / `notify_when_idle` schemas; `CLAUDE_CODE_MESSAGING_SOCKET=/tmp/cc-socks/<pid>.sock`; `~/.claude/sessions/<pid>.json` + `.key` | observed | this session | native cross-session primitives, registry location |
| OBS-2 | Claude Code `Agent` tool (`model`, `isolation: worktree`, background), `Workflow`, `Monitor` (command/ws), `RemoteTrigger`, `PushNotification` | observed | this session | S2 primitives |
| OBS-3 | Sub-agents spawned before the parent's `EnterWorktree` lose Bash to the worktree guard | observed | four researcher hand-backs, this session | failure mode |
| OBS-4 | `claude --help` (2.1.278), `codex --help` / `exec` / `queue` / `app-server` / `agents` / `remote-control --help` (0.155.0), `agy --help` (1.2.7), `grok --help`; `copilot` absent | executed | this machine, 2026-09-19 | harness CLI contracts: headless entry, structured output, push, isolation |
| REPO-ai-forward | files listed in `references.md` | primary (repo) | `/Users/mallalieut/projects/ai-forward` @ 4e0f3b0 | coord layer, skills, dream, profiles |
| REPO-ai-de | files listed in `references.md`; counts computed read-only | primary (repo) | `/Users/mallalieut/projects/ai-de` @ 62e3ed29 | live fleet telemetry, protocol in use |

## AC — agentic coordination track

| # | Title | Type | URL | Used for |
|---|---|---|---|---|
| AC-1 | Anthropic — How we built our multi-agent research system | primary | https://www.anthropic.com/engineering/built-multi-agent-research-system | 15×, +90.2%, delegation parts, failure modes |
| AC-2 | Cognition — Don't Build Multi-Agents | primary | https://cognition.com/blog/dont-build-multi-agents | disconfirmation |
| AC-3 | LangChain — How and when to build multi-agent systems | secondary | https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems | read/write axis |
| AC-4 | Anthropic — Building a C compiler with a team of parallel Claudes | primary | https://www.anthropic.com/engineering/building-c-compiler | blackboard run |
| AC-5 | Claude Code — Orchestrate teams of Claude Code sessions | official | https://code.claude.com/docs/en/agent-teams | teams, limits, hooks, permissions |
| AC-6 | Claude Code — Message your other Claude Code sessions | official | https://code.claude.com/docs/en/cross-session-messaging | socket, token, delivery, caps |
| AC-7 | Claude Code — Channels | official | https://code.claude.com/docs/en/channels | event injection |
| AC-8 | Claude Code — Run agents in parallel | official | https://code.claude.com/docs/en/agents | parallelism surfaces |
| AC-9 | Claude Code — Run programmatically (headless) | official | https://code.claude.com/docs/en/headless | `-p`, stream-json, SIGTERM, wait ceiling |
| AC-10 | Claude Code — Manage costs | official | https://code.claude.com/docs/en/costs | ~7× |
| AC-11 | MCP blog — The 2026-07-28 specification | official | https://blog.modelcontextprotocol.io/posts/2026-07-28/ | stateless core, MRTR, deprecations |
| AC-12 | MCP — Specification 2026-07-28 | primary | https://modelcontextprotocol.io/specification/2026-07-28 | revision |
| AC-13 | A2A Protocol Specification v1.0 | primary | https://a2a-protocol.org/latest/specification/ | task states, card, push |
| AC-14 | Glukhov — A2A in 2026: adoption, hype, reality | secondary | https://www.glukhov.org/ai-systems/comparisons/a2a-protocol-2026-adoption/ | adoption disconfirmation |
| AC-15 | Linux Foundation — Agentic AI Foundation | primary | https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation | governance |
| AC-16 | Zed — Agent Client Protocol; ACP registry | official | https://zed.dev/acp · https://zed.dev/blog/acp-registry | ACP adoption |
| AC-17 | ACP Is Not One Protocol | secondary | https://medium.com/@mertbasar30/acp-is-not-one-protocol-a-chronological-guide-to-four-different-acps-and-where-acp-net-fits-41952bfef80e | disambiguation |
| AC-18 | GitHub Docs — `/fleet` | official | https://docs.github.com/en/copilot/concepts/agents/copilot-cli/fleet | Copilot fan-out |
| AC-19 | GitHub Docs — Copilot CLI programmatically | official | https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically | `-p`, allow flags |
| AC-20 | GitHub Blog — /fleet launch | primary | https://github.blog/ai-and-ml/github-copilot/run-multiple-agents-at-once-with-fleet-in-copilot-cli/ | context |
| AC-21 | Antigravity Docs — Custom Subagents | official | https://antigravity.google/docs/subagents/ | invoke/define, nesting, workspace |
| AC-22 | Antigravity Docs — /agents | official | https://antigravity.google/docs/cli/commands/agents/ | agent manager |
| AC-23 | OpenAI — Codex developer commands | official | https://learn.chatgpt.com/docs/developer-commands?surface=cli | exec, app-server, remote |
| AC-24 | xAI — grok-build subagents guide | primary | https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/16-subagents.md | spawn, cap 8 |
| AC-25 | Cemri et al. — Why Do Multi-Agent LLM Systems Fail? (MAST) | primary | https://arxiv.org/abs/2503.13657 | taxonomy |
| AC-26 | Magentic-UI | primary | https://arxiv.org/pdf/2507.22358 | co-planning, action guards |
| AC-27 | Claude Managed Agents overview | official | https://platform.claude.com/docs/en/managed-agents/overview | steer/interrupt |
| AC-28 | Claude blog — New in Managed Agents | primary | https://claude.com/blog/new-in-claude-managed-agents | multi-agent orchestration |
| AC-29 | OpenAI Agents SDK — Handoffs | official | https://openai.github.io/openai-agents-python/handoffs/ | handoff vs as-tool |
| AC-30 | LangGraph supervisor / swarm | official | https://reference.langchain.com/python/langgraph-supervisor | patterns |
| AC-31 | Frontiers — single-agent overhead study | primary | https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1877762/full | cost disconfirmation |
| AC-32 | Agent Network Protocol | official | https://agentnetworkprotocol.com/en/ | ANP status |
| AC-33 | Mapping MCP, A2A and ACP | secondary | https://dev.to/kanywst/mapping-mcp-a2a-and-acp-telling-ai-agent-protocols-apart-in-2026-1hha | merger/archival dates |
| AC-34 | MCP SEP-2663 — Tasks extension | primary | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/seps/2663-tasks-extension.md | tasks as extension |
| AC-38 | AssetOpsBench retrospective | primary | https://arxiv.org/pdf/2605.08518 | token inversion |
| AC-39 | Copilot CLI complete reference (community) | secondary | https://htekdev.github.io/copilot-cli-reference/ | hook names (Flagged) |
| AC-40 | Antigravity Docs — Hooks | official | https://antigravity.google/docs/hooks | PreInvocation injectSteps, PostInvocation force_continue, Stop |
| AC-41 | GitHub Docs — Hooks reference (Copilot) | official | https://docs.github.com/en/copilot/reference/hooks-reference | agentStop/subagentStop block+reason; exit codes |
| AC-42 | GitHub Docs — Use hooks with Copilot CLI | official | https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks | bash/powershell keys; runaway guard |

## P2P — peer-to-peer coordination track

| # | Title | Type | URL | Used for |
|---|---|---|---|---|
| P2P-1 | SWIM (DSN 2002) | primary | https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf | protocol |
| P2P-2 | SWIM Protocol (Wikipedia) | secondary | https://en.wikipedia.org/wiki/SWIM_Protocol | detection formula |
| P2P-3 | hashicorp/memberlist `config.go` | primary | https://github.com/hashicorp/memberlist/blob/master/config.go | Local/LAN/WAN constants |
| P2P-4 | HashiCorp — Lifeguard | official | https://www.hashicorp.com/en/blog/making-gossip-more-robust-with-lifeguard | FP reduction |
| P2P-5 | Lifeguard (arXiv 1707.00788) | primary | https://arxiv.org/pdf/1707.00788 | (Flagged extraction) |
| P2P-6 | akka-cluster `reference.conf` | primary | https://raw.githubusercontent.com/akka/akka-core/main/akka-cluster/src/main/resources/reference.conf | phi defaults |
| P2P-7 | Akka — Phi Accrual Failure Detector | official | https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html | φ semantics |
| P2P-8 | Gray & Cheriton — Leases (SOSP 1989) | primary | https://web.eecs.umich.edu/~mosharaf/Readings/Leases.pdf | lease liveness |
| P2P-9 | gossipsub v1.0 | primary | https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md | mesh params |
| P2P-10 | gossipsub v1.1 | primary | https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.1.md | scoring |
| P2P-11 | gossipsub v1.2 | primary | https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.2.md | IDONTWANT |
| P2P-12 | Plumtree (SRDS 2007) | primary | https://asc.di.fct.unl.pt/~jleitao/pdf/srds07-leitao.pdf | eager/lazy |
| P2P-13 | Shapiro et al. — CRDTs (SSS 2011) | primary | https://www.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf | G-Set, OR-Set, LWW |
| P2P-14 | Logical Physical Clocks (HLC) | primary | https://link.springer.com/chapter/10.1007/978-3-319-14472-6_2 | HLC |
| P2P-15 | Automerge 3.0 | official | https://automerge.org/blog/automerge-3/ | CRDT state |
| P2P-16 | y-crdt v0.28.0 | primary | https://github.com/y-crdt/y-crdt | Yjs 2026 |
| P2P-17 | CodeCRDT (arXiv 2510.18893) | primary | https://arxiv.org/abs/2510.18893 | CRDTs on code |
| P2P-18 | Automatic git conflict resolution on logs and sets | secondary | https://a3nm.net/blog/git_auto_conflicts.html | union pitfalls |
| P2P-19 | MCP transports / SSE deprecation | secondary | https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/ | transports |
| P2P-20 | GHSA-w48q-cv73-mx4w / CVE-2025-66414 | primary | https://github.com/advisories/GHSA-w48q-cv73-mx4w | localhost CVE |
| P2P-21 | GitHub Blog — Localhost dangers: CORS and DNS rebinding | official | https://github.blog/security/application-security/localhost-dangers-cors-and-dns-rebinding/ | mitigations |
| P2P-22 | Node.js `net` — IPC | official | https://nodejs.org/api/net.html | pipes vs UDS |
| P2P-23 | Windows mDNS/DNS-SD | secondary | https://learn.microsoft.com/en-us/answers/questions/266761/does-windows-10-support-mdns | mDNS (Flagged) |
| P2P-24 | Claude Code — cross-session messaging | official | https://code.claude.com/docs/en/cross-session-messaging | reference implementation |
| P2P-25 | Claude Code — agent teams | official | https://code.claude.com/docs/en/agent-teams | mailbox, locking, hooks |
| P2P-26 | Claude Code — Hooks reference | official | https://code.claude.com/docs/en/hooks | Stop exit 2 |
| P2P-27 | AWS — Transactional outbox | official | https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html | outbox |
| P2P-28 | Outbox pattern for AI agent coordination | secondary | https://zylos.ai/research/2026-06-02-transactional-outbox-pattern-ai-agent-coordination/ | constants (Flagged) |
| P2P-29 | Parallel coding agents through a shared log | secondary | https://www.ikangai.com/no-orchestration-required-how-parallel-coding-agents-coordinate-through-a-shared-log/ | parking (Flagged) |
| P2P-30 | Coordinating AI coding agents | secondary | https://munderdiffl.in/blog/coordinating-ai-coding-agents/ | single-committer |
| P2P-30S | Repository as coordination layer | secondary | https://nxtg.ai/insights/repository-as-coordination-layer | "git is enough" (Flagged) |
| P2P-32 | openai/codex #21027 — shared bus request | primary | https://github.com/openai/codex/issues/21027 | Codex gap |
| P2P-33 | A pidfile lock is only as good as its stale check | secondary | https://dev.to/raknaos/a-pidfile-lock-is-only-as-good-as-its-stale-check-3j26 | PID liveness |
| P2P-34 | Meteor — file change watcher efficiency | official | https://github.com/meteor/docs/blob/master/long-form/file-change-watcher-efficiency.md | polling |
| P2P-35 | A2A specification (security schemes) | primary | https://a2a-protocol.org/latest/specification/ | mTLS |
| P2P-36 | ANP white paper | official | https://agent-network-protocol.com/specs/1.1/white-paper | DID |
| P2P-38 | AI coding agents in 2026 — orchestration | secondary | https://mikemason.ca/writing/ai-coding-agents-jan-2026/ | lock collapse (Flagged) |

## SCH — distributed scheduling track

| # | Title | Type | URL | Used for |
|---|---|---|---|---|
| SCH-1 | Omega (EuroSys 2013) | primary | https://people.csail.mit.edu/malte/pub/papers/2013-eurosys-omega.pdf | taxonomy |
| SCH-2 | Borg (EuroSys 2015) | primary | https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/ | scale |
| SCH-3 | Mesos (NSDI 2011) | primary | https://www.usenix.org/legacy/events/nsdi11/tech/full_papers/Hindman.pdf | two-level |
| SCH-4 | Mesos in the light of Omega | secondary | https://sujithjay.com/mesos | offer locking |
| SCH-5 | Blumofe & Leiserson — work stealing | primary | https://dl.acm.org/doi/10.1145/324133.324234 | T1/P + O(T∞) |
| SCH-6 | Brent's theorem notes | secondary | https://stanford.edu/~rezab/dao/notes/lecture01/cme323_lec1.pdf | work-span |
| SCH-7 | Amdahl / USL | secondary | https://en.wikipedia.org/wiki/Amdahl%27s_law | formulae |
| SCH-8 | Temporal — timeouts and retries | official | https://docs.temporal.io/evaluate/features/timeouts-and-retries | heartbeat classes |
| SCH-9 | Gray & Cheriton — Leases | primary | https://web.eecs.umich.edu/~mosharaf/Readings/Leases.pdf | lease |
| SCH-10 | Chubby (mirror) | primary | https://mwhittaker.github.io/papers/html/burrows2006chubby.html | sequencer |
| SCH-11 | ZooKeeper Recipes 3.9.3 | official | https://zookeeper.apache.org/doc/r3.9.3/recipes.html | herd effect |
| SCH-12 | Kleppmann — distributed locking | primary | https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html | fencing |
| SCH-13 | git-update-ref | official | https://git-scm.com/docs/git-update-ref | CAS, transactions |
| SCH-14 | HEFT | secondary | https://en.wikipedia.org/wiki/Heterogeneous_earliest_finish_time | DAG scheduling |
| SCH-15 | Bird et al. — Don't Touch My Code! | primary | https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bird2011dtm.pdf | ownership |
| SCH-16 | Brun et al. — Proactive detection of collaboration conflicts | primary | https://www.cs.ubc.ca/~rtholmes/papers/fse_2011_brun.pdf | 16% |
| SCH-17 | Owhadi-Kareshk et al. (ESEM 2019) | primary | https://arxiv.org/pdf/1907.06274 | predictors |
| SCH-18 | ConE (TOSEM 2021) | primary | https://arxiv.org/pdf/2101.06542 | overlap |
| SCH-19 | Vale et al. (EMSE 2023) | primary | https://link.springer.com/article/10.1007/s10664-023-10395-8 | modularity |
| SCH-20 | AWS — Exponential backoff and jitter | official | https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/ | jitter |
| SCH-21 | SQS visibility timeout | official | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html | lease-by-timeout, DLQ |
| SCH-22 | Kubernetes node status | official | https://v1-32.docs.kubernetes.io/docs/reference/node/node-status/ | heartbeat ladder |
| SCH-23 | Airflow zombie tasks | secondary | https://medium.com/@brihati1373/zombie-and-undead-tasks-in-airflow-e09ddbe6b22f | (Flagged) |
| SCH-24 | Smith — Contract Net (1980) | primary | https://www.cs.ucf.edu/~lboloni/Teaching/EEL6788_2008/papers/The_Contract_Net_Protocol_Dec-1980.pdf | bidding |
| SCH-25 | Gerkey & Matarić — MRTA taxonomy | primary | https://journals.sagepub.com/doi/10.1177/0278364904045564 | ST-SR-TA |
| SCH-26 | Anthropic — multi-agent research system | primary | https://www.anthropic.com/engineering/multi-agent-research-system | (same as AC-1) |
| SCH-27 | MAST | primary | https://arxiv.org/abs/2503.13657 | (same as AC-25) |
| SCH-28 | Cognition — Don't Build Multi-Agents | primary | https://cognition.com/blog/dont-build-multi-agents | (same as AC-2) |
| SCH-29 | RouteLLM | primary | https://arxiv.org/abs/2406.18665 | tier routing |
| SCH-30 | MetaGPT | primary | https://arxiv.org/abs/2308.00352 | SOP pipelines |
| SCH-31 | Agentless | primary | https://arxiv.org/abs/2407.01489 | disconfirmation |
| SCH-32 | etcd tuning | official | https://etcd.io/docs/v3.4/tuning/ | ratios |
| SCH-33 | MacCormack et al. — mirroring | primary | https://www.sciencedirect.com/science/article/abs/pii/S0048733312001205 | 8× |
| SCH-34 | Sadowski et al. — code review at Google | primary | https://research.google/pubs/modern-code-review-a-case-study-at-google/ | review latency |
| SCH-35 | Fowler — CircuitBreaker | primary | https://martinfowler.com/bliki/CircuitBreaker.html | breaker |
| SCH-36 | Restate — durable execution | official | https://restate.dev/what-is-durable-execution | vendor |
| SCH-37 | DBOS — comparison | official | https://www.dbos.dev/blog/durable-execution-coding-comparison | vendor |
| SCH-38 | Van Houdt — stealing vs sharing | primary | https://arxiv.org/abs/1810.13186 | thresholds |
| SCH-39 | SWE-Dev | primary | https://arxiv.org/pdf/2506.07636 | Agentless numbers |
| SCH-40 | Thongtanunam et al. — revisiting ownership | primary | https://dl.acm.org/doi/abs/10.1145/2884781.2884852 | (Flagged) |

## QLE — quorum & leader election track

| # | Title | Type | URL | Used for |
|---|---|---|---|---|
| QLE-1 | FLP (1985) | primary | https://www.cs.princeton.edu/courses/archive/spr22/cos418/papers/flp.pdf | impossibility |
| QLE-2 | Raft (extended) | primary | https://raft.github.io/raft.pdf | terms, timeouts |
| QLE-3 | Ongaro thesis | primary | https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf | transfer, membership |
| QLE-4 | Flexible Paxos | primary | https://arxiv.org/abs/1608.06696 | quorum intersection |
| QLE-5 | client-go leaderelection.go | primary | https://github.com/kubernetes/client-go/blob/master/tools/leaderelection/leaderelection.go | defaults, no fencing |
| QLE-6 | Jepsen — etcd 3.4.3 | primary | https://jepsen.io/analyses/etcd-3.4.3 | locks unsafe |
| QLE-7 | Kleppmann — distributed locking | primary | https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html | fencing |
| QLE-8 | Burrows — Chubby (OSDI 2006) | primary | https://research.google.com/archive/chubby-osdi06.pdf | coarse locks |
| QLE-9 | Chubby notes (Whittaker) | secondary | https://mwhittaker.github.io/papers/html/burrows2006chubby.html | sequencer, grace, rationale |
| QLE-10 | Consul sessions | official | https://developer.hashicorp.com/consul/docs/automate/session | lock-delay |
| QLE-11 | git-push | official | https://git-scm.com/docs/git-push | force-with-lease |
| QLE-12 | flock(2) | official | https://man7.org/linux/man-pages/man2/flock.2.html | advisory locks |
| QLE-13 | apenwarr — file locking | secondary | https://apenwarr.ca/log/20101213 | O_EXCL, NFS |
| QLE-14 | ZooKeeper recipes 3.8.0 | official | https://zookeeper.apache.org/doc/r3.8.0/recipes.html | election recipe |
| QLE-15 | Garcia-Molina — Elections (1982) | primary | https://homepage.divms.uiowa.edu/~ghosh/Bully.pdf | Bully, reorganisation |
| QLE-16 | Azure Local / Windows Server — cluster quorum | official | https://docs.microsoft.com/en-us/azure-stack/hci/concepts/quorum | witness |
| QLE-17 | golang/go#24595 — CLOCK_BOOTTIME | primary | https://github.com/golang/go/issues/24595 | suspend clocks |
| QLE-18 | MAST | primary | https://arxiv.org/abs/2503.13657 | (same as AC-25) |
| QLE-19 | pact — multi-agent orchestration CLI | primary (repo) | https://github.com/zekariasasaminew/pact | advisory-claims caveat |
| QLE-20 | Google SRE Book — Managing Incidents | official | https://sre.google/sre-book/managing-incidents/ | IC designation |
| QLE-21 | etcd client/v3 concurrency | official | https://pkg.go.dev/go.etcd.io/etcd/client/v3/concurrency | Election API |
| QLE-22 | Locks, leases, fencing tokens, FizzBee | secondary | https://surfingcomplexity.blog/2025/03/03/locks-leases-fencing-tokens-fizzbee/ | resource-side enforcement |
| QLE-23 | A2A surpasses 150 organizations | primary | https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year | status |
| QLE-24 | Outshift — cognitive challenges in MAS (AGNTCY) | official | https://outshift.cisco.com/blog/ai-ml/cognitive-challenges-in-multi-agent-systems | OASF |
| QLE-25 | kubernetes#125861 — RetryPeriod default | primary | https://github.com/kubernetes/kubernetes/issues/125861 | tunability |
| QLE-26 | Consul — application leader election | official | https://developer.hashicorp.com/consul/docs/automate/application-leader-election | sessions |
| QLE-27 | LLM-based multi-agent orchestration survey | primary | https://doi.org/10.3390/fi18060326 | arbitration loops (Inferred) |
| QLE-28 | SQLite WAL / busy_timeout | secondary | https://dbapark.com/sqlite-database-is-locked-wal-fix/ | same-host constraint |
| QLE-29 | Agent2Agent (Wikipedia) | secondary | https://en.wikipedia.org/wiki/Agent2Agent | task states |
| QLE-31 | Coordination as an architectural layer for LLM MAS | primary | https://arxiv.org/pdf/2605.03310 | framing |
| QLE-32 | agent-triforge | primary (repo) | https://github.com/Ninety2UA/agent-triforge | static orchestrator |
| QLE-33 | Implementing Chubby (Princeton) | secondary | https://medium.com/princeton-systems-course/implementing-chubby-a-distributed-lock-service-8cf3c026c672 | 12 s / 45 s / 60 s |
| QLE-34 | Single-Threaded Leaders at Amazon | secondary | https://pedrodelgallego.github.io/blog/amazon/single-threaded-model/ | STO |
| QLE-36 | Proxmox 2-node quorum / QDevice | secondary | https://www.rack2cloud.com/proxmox-2-node-quorum-ha-fix/ | witness practice |
