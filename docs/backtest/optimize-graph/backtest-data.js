window.BACKTEST = {
  meta: {
    title: "optimize-graph back-test",
    subtitle: "Twelve real prompts from three repositories, replanned as execution graphs",
    generated: "2026-08-22",
    corpus: "750 committed audit entries — TheTerrace 372 · meridian-finance-planner 320 · HealthWatch 58",
    multistep: "481 of 750 (64%) are multi-step work; 269 (36%) are single-step",
    authority: "knowledge/execution-graph-optimization.md (GO1–GO18) · docs/knowledge/graph-and-loop-engineering/"
  },

  integrity: [
    { label: "Verified — measured from the committed logs", body: "The prompt text, the summary, the outcome field, the artifact count, the skill, the repo and the entry id. These are quoted from each repo's <code>docs/audit/audit-log.jsonl</code>." },
    { label: "Inferred — derived by reading the summary", body: "The naive node list and the dependency edges. Each node corresponds to a step the summary describes or a rigor floor the change shape triggers. A different reader could count nodes slightly differently; the <em>shape</em> — what depends on what — is the load-bearing part, not the exact integer." },
    { label: "Inferred — modeled, NOT measured", body: "Time and token figures. <strong>There is no per-prompt timing or token data in these logs.</strong> Session ids span days of human-paced work (mean 55h, median 21h), so session elapsed time is not execution time. Every time and token number here is a model output, reported as an index against the naive plan, never as a measurement." },
    { label: "The model, stated so it can be attacked", body: "Uniform node cost. The naive plan is fully serial, so its span equals its work. <strong>Time index = optimized span ÷ naive span.</strong> <strong>Token index = optimized context-loads ÷ naive context-loads</strong>, where parallelism saves nothing (branches still load context) and only <em>collapse</em> and <em>avoided rework</em> reduce it. Completeness and rigor are 0–100 rubric scores anchored on the measured outcome field and on the presence of exit conditions, gates and oracles." }
  ],

  rubric: {
    completeness: "Does every branch declare an exit condition, and can the join tell done from partial? Anchored on the measured outcome — a 'partial' with open items scores low.",
    rigor: "Are the triggered floors present as explicit immovable nodes (hard vetoes, testing union, E7 surface list, red-first), does every verification node declare its oracle, and is every loop and fan-out bounded?"
  },

  cases: [
    {
      id: "al-0246", repo: "TheTerrace", skill: "updatepack", outcome: "success", artifacts: 0,
      size: "small", tag: "SKIP", title: "Pack refresh",
      prompt: "/updatepack",
      summary: "AI-Forward Pack refreshed revision 24 -> 35; delta applied: re-synced 33 knowledge docs, 19 skills, 19 prompts, 24 templates, 13 scripts; added ui-craft-detection + ui-visual-assets knowledge, /visualize skill; both managed blocks re-pasted wholesale; INSTALL advanced.",
      naive: { nodes: 2, span: 2, desc: "Read the INSTALL delta, then apply it." },
      optimized: { nodes: 2, span: 2, desc: "Triage says SKIP (GO16). Two nodes, no loop, no fan-out, no triggered gate — execute directly and say planning was skipped." },
      moves: ["Triage → skip"],
      m: { timeN: 100, timeO: 100, tokN: 100, tokO: 100, compN: 90, compO: 90, rigN: 85, rigO: 85 },
      verdict: "no-change",
      note: "The correct answer is to do nothing. 36% of the corpus looks like this, so the skip path is the normal path — a planner that fires here would cost more than the work it plans."
    },
    {
      id: "al-0204", repo: "TheTerrace", skill: "ui-design", outcome: "success", artifacts: 6,
      size: "medium", tag: "FAN-OUT", title: "UI round 3 — five surfaces",
      prompt: "create a separate working tree for continued iteration; continue iterating on the mockup and pushing on the next steps outlined — heatmaps, pitch control and visual insights in live and post-match… Feedback: like B and C, default B live and C post-match with a toggle. Missing: club/squad news focus, daily news/rumors, ask AI, trading simulator, squad view with player cards, compare players, assess fit, pre-match lineup experimentation…",
      summary: "Round 3 in a dedicated worktree. Resolved the B/C decision as view modes with a phase default and a sticky manual toggle… Built five surfaces: week, matchday with the lineup lab, squad with dossier and fit, tactics with head-to-head, and a gated transfer lab… 213 combinations verified.",
      naive: { nodes: 9, span: 9, desc: "Ground → resolve the B/C decision → build week → matchday → squad → tactics → transfer lab → verify 213 combinations → review." },
      optimized: { nodes: 8, span: 5, desc: "Ground → resolve B/C (a decision edge: it changes every surface's shape, so it must precede them) → five surfaces fan out at width 4, two waves → per-surface verification folded into each branch → one join review." },
      moves: ["Delete incidental ordering between the five surfaces", "Fan-out width 4 with per-branch exit conditions", "Collapse the global verify into each branch"],
      m: { timeN: 100, timeO: 56, tokN: 100, tokO: 89, compN: 75, compO: 90, rigN: 80, rigO: 88 },
      verdict: "gain",
      note: "The B/C decision is a genuine decision edge and stays serial. The five surfaces after it share nothing — that ordering was incidental."
    },
    {
      id: "al-0229", repo: "TheTerrace", skill: "define-architecture", outcome: "success", artifacts: 10,
      size: "large", tag: "MODEL-FIRST", title: "My Club architecture",
      prompt: "Ground yourself in the repo… Specify an updated My Club experience at /my-club… a paid-feed-grounded manager dossier… squad analysis linked to the existing player dossier; and a formation/lineup playground with player ELO and expected-performance adjustments plus Monte Carlo simulations and uncertainty-first outputs… Then run /ui-design to produce a mockup, and /define-architecture with a rock-solid data model, cache policy, chronological runners, AI model routing, and simulation infrastructure.",
      summary: "Produced the scoped My Club architecture, ADR-0011 through ADR-0014, durable chronology, paid-feed brand/staff model, global capability-aware AI policy, claim/evidence schemas, deterministic scenario engine and red-first proof plan.",
      naive: { nodes: 13, span: 13, desc: "Ground → spec → mockup → data model → cache policy → chronology runners → AI routing → simulation infra → ADR-0011 → 0012 → 0013 → 0014 → proof plan." },
      optimized: { nodes: 13, span: 5, desc: "Ground → data model first as an immovable gate (DM1: the model is the highest-priority decision) → cache, chronology, AI routing, simulation and the mockup fan out at width 4 → the four ADRs fan out → proof plan." },
      moves: ["Promote the data model to node 1 as an immovable gate (DM1)", "Fan-out the four subsystems (width 4)", "Fan-out the four ADRs", "Run the mockup concurrently with the architecture branches"],
      m: { timeN: 100, timeO: 38, tokN: 100, tokO: 100, compN: 80, compO: 92, rigN: 82, rigO: 95 },
      verdict: "gain",
      note: "The largest rigor gain in the set comes from making the data-model-first rule structural rather than remembered. Tokens are unchanged — parallelism does not save tokens."
    },
    {
      id: "al-0012", repo: "TheTerrace", skill: "define-architecture", outcome: "partial", artifacts: 9,
      size: "large", tag: "UNBOUNDED GOAL", title: "Autonomous build strategy for every slice",
      prompt: "Use the define-architecture skill and create a detailed strategy for autonomously building every slice using my design-implement-forensicreview workflow, testing, documenting and validating every slice, then yielding a fully functional application in Azure for manual end-to-end validation.",
      summary: "Defined the complete .NET 10/Azure modular-monolith architecture, six proposed ADRs, contract-spike ledger, architecture verification matrix and S00-S13 autonomous delivery strategy. Architecture remains in review behind explicit cloud/provider/privacy/test gates.",
      naive: { nodes: 12, span: 12, desc: "A serial architecture pass over an unbounded goal ('every slice'), ending in review behind four unnamed gates." },
      optimized: { nodes: 12, span: 7, desc: "Ground → the four gates (cloud, provider, privacy, test) are made explicit nodes with named clearing conditions and pulled early → independent architecture branches fan out → ADRs → strategy." },
      moves: ["Convert 'remains in review' into named gate nodes with clearing conditions", "Pull the gates early — a gate that fires late costs everything built on it", "Bound the unbounded goal with a per-slice exit condition"],
      m: { timeN: 100, timeO: 58, tokN: 100, tokO: 88, compN: 45, compO: 85, rigN: 70, rigO: 90 },
      verdict: "gain",
      note: "The measured outcome was <em>partial</em>. The plan does not make the gates clear — it makes them <strong>legible</strong>: 'blocked on the privacy basis' is actionable, 'remains in review' is not."
    },
    {
      id: "al-0058", repo: "meridian", skill: "investigate", outcome: "success", artifacts: 1,
      size: "small", tag: "PREVENTION", title: "AI advisor panel failed as a whole",
      prompt: "the AI advisors still are problematic (panel of specialists captured an error report instead of working)",
      summary: "Root cause: 5 parallel Claude calls + no retry tripped 429/529 and failed the whole panel. Fix: concurrency cap 2 + transient retry-with-backoff + broadened catch + accurate failure reason. +2 tests; API deployed",
      naive: { nodes: 9, span: 9, desc: "Reproduce → inspect the panel → find 429/529 → cap concurrency → add retry → broaden the catch → accurate failure reason → tests → deploy." },
      optimized: { nodes: 9, span: 6, desc: "Reproduce → three independent probes (logs, provider limits, retry policy) fan out → root cause → the four fixes fan out → tests → deploy." },
      moves: ["Fan-out the three independent diagnostic probes", "Fan-out the four independent fixes", "★ At original build time: require the five-part fan-out contract"],
      m: { timeN: 100, timeO: 67, tokN: 100, tokO: 100, compN: 85, compO: 95, rigN: 75, rigO: 95 },
      verdict: "prevention",
      note: "★ <strong>The headline case.</strong> The investigation itself replans modestly. The real value is upstream: GO7 requires every fan-out to declare a width cap and a transient-failure policy. Had the original five-way call carried that contract, <em>this entire nine-node investigation would not have existed.</em> The fix eventually applied — cap 2 plus retry-with-backoff — is exactly what the contract mandates."
    },
    {
      id: "al-0089", repo: "meridian", skill: "define-architecture", outcome: "success", artifacts: 9,
      size: "large", tag: "SERIAL CHAIN", title: "Identity, security & privacy refactor",
      prompt: "ground yourself in the repo, knowledge, code, specs and architecture / specifically look at all the issues we are hitting getting our security and identity management sorted out / /collectknowledge for all the best practices for identity managemnt, privacy and security for an application like this in Azure / /specify an identity, security and privacy requirements document / step back and assess the existing implementation, the entire code base, policy and architecture with an eye to refactoring… / then /define-architecture for the overall refactor / then give me an html overview… also enumerate the concrete steps in your terminal output",
      summary: "Accepted the same-origin BFF identity/security/privacy refactor architecture, six ADRs, target lifecycle and federation manifests, a digest-bound proof contract, and a standalone HTML strategy with phases ISP-PH-0 through ISP-PH-8.",
      naive: { nodes: 13, span: 13, desc: "The chain the prompt literally specifies: ground → collectknowledge → specify → assess the existing implementation → define-architecture → six ADRs → HTML overview → terminal enumeration." },
      optimized: { nodes: 12, span: 7, desc: "Ground → collectknowledge and assess-the-existing-implementation run concurrently (external research and internal audit share no data and neither changes the other's shape) → specify → architecture → six ADRs fan out → one output rendered twice." },
      moves: ["★ Break the user-authored serial chain: research ∥ code audit", "Collapse 'HTML overview' and 'terminal enumeration' — one content node, two renderings", "Fan-out the six ADRs"],
      m: { timeN: 100, timeO: 54, tokN: 100, tokO: 92, compN: 85, compO: 92, rigN: 85, rigO: 92 },
      verdict: "gain",
      note: "★ The prompt hard-codes its own execution order with the word <em>then</em> four times. Two of those steps — the external best-practice research and the internal codebase audit — are independent, and both merely feed the spec. The chain was incidental ordering written by a human."
    },
    {
      id: "al-0319", repo: "meridian", skill: "migrate", outcome: "success", artifacts: 12,
      size: "large", tag: "GATE-FIRST", title: "Squash the EF migration chain",
      prompt: "do FR-289",
      summary: "Closed FR-289: replaced the historical EF migration chain with one squashed baseline migration, added current-state RLS policy creation to the baseline, added scripts/mark-squashed-baseline-applied.ps1 for existing DB transition with old-latest and RLS validation, replaced stale historical migration guards with baseline-era guards, and added docs/proof/fr289-migration-squash.md. Focused migration gates and full .NET suites passed.",
      naive: { nodes: 10, span: 10, desc: "Read the chain → squash → add RLS → write the transition script → replace guards → write the proof doc → run migration gates → run the full suites." },
      optimized: { nodes: 10, span: 5, desc: "Characterization / golden-master pin first as an immovable gate → squash the baseline → RLS, transition script, guards and proof doc fan out at width 4 → behavioural-equivalence proof → gates." },
      moves: ["Promote characterization-first to node 1 as an immovable gate", "Fan-out the four independent artifacts", "Declare the equivalence oracle explicitly"],
      m: { timeN: 100, timeO: 50, tokN: 100, tokO: 100, compN: 90, compO: 95, rigN: 88, rigO: 97 },
      verdict: "gain",
      note: "A three-word prompt ('do FR-289') expanding to twelve artifacts. The highest rigor score in the set: pinning behaviour before a destructive migration is already the rule — making it node 1 makes it structural instead of remembered."
    },
    {
      id: "al-0310", repo: "meridian", skill: "implement", outcome: "partial", artifacts: 22,
      size: "large", tag: "JOIN BLIND", title: "Fourteen FRs in one pass",
      prompt: "re-ground yourself in the repo then do all the next items enumerated above From FR-291 all the way to FR-289",
      summary: "Implemented the verified slices from FR-287/288 and FR-291-FR-300: provider version/reasoning routing, served-family default fixes, route inventory coverage, accessibility/semantic controls, serial data-entry defaults, setup readiness, reviewer comment/reviewer-mode AI affordances, AI verifier metadata projection… FR-289, FR-295, FR-298, FR-299 remain open by design; FR-291/294/296/297 are partial as recorded in the backlog addendum.",
      naive: { nodes: 16, span: 16, desc: "Ground, then fourteen FRs worked one after another, then a backlog reconciliation to work out what actually landed." },
      optimized: { nodes: 14, span: 6, desc: "Ground → FRs grouped by real dependency and fanned out at width 4 across four waves, each branch carrying its own exit condition → a join that performs an explicit completeness check and reports done / partial / open per branch." },
      moves: ["★ Per-branch exit condition on every FR", "★ Completeness check at the join", "Fan-out width 4 by dependency group", "Eliminate the reconciliation rework pass"],
      m: { timeN: 100, timeO: 38, tokN: 100, tokO: 88, compN: 40, compO: 88, rigN: 78, rigO: 90 },
      verdict: "gain",
      note: "★ <strong>The largest completeness gain in the set (+48).</strong> Four FRs open and four partial out of fourteen, discovered by writing a backlog addendum afterwards. A join that cannot distinguish done from partial is the defect — not the fan-out."
    },
    {
      id: "al-0032", repo: "HealthWatch", skill: "updatepack", outcome: "success", artifacts: 0,
      size: "small", tag: "SKIP", title: "Pack refresh",
      prompt: "/updatepack — pull the latest AI-Forward Pack into this repo",
      summary: "revision 36 -> 38: applied rev37 (dream-manifest template, apply-learnings.py+SKILL+prompt) and rev38 (new ci-and-test-efficiency knowledge doc + Copilot wrap, continuous-improvement.md & testing-strategy.md updates, dream/apply-learnings SKILL frontmatter fix, both managed blocks re-pasted).",
      naive: { nodes: 2, span: 2, desc: "Read the delta for two revisions, apply both." },
      optimized: { nodes: 2, span: 2, desc: "Triage says SKIP. Same as the Terrace refresh — no loop, no fan-out, no gate." },
      moves: ["Triage → skip"],
      m: { timeN: 100, timeO: 100, tokN: 100, tokO: 100, compN: 90, compO: 90, rigN: 85, rigO: 85 },
      verdict: "no-change",
      note: "A second skip, from a different repo, on the same shape. Included deliberately: two of twelve cases correctly produce no plan at all."
    },
    {
      id: "al-0045", repo: "HealthWatch", skill: "implement", outcome: "success", artifacts: 6,
      size: "medium", tag: "ORACLE EARLY", title: "Charts in the PDF report",
      prompt: "the pdf report looks good as front matter, i want the charts (that are rendered in the web app) as well to follow that front matter to support whatever was in tabular form",
      summary: "Report generator Phase 2: every tabular row now carries its chart in the PDF as a small multiple. New ReportChart.TrySvg renders vector SVG from the SAME SeriesV2Dto the table was summarised from (E12)… Empty measures render an explicit no-readings panel (U9). Rendered surface verified by rasterising the PDF and inspecting it (E11), which caught a legend/palette drift. 24 tests added (345 total, 0 failures); red observed via deliberate mutation.",
      naive: { nodes: 10, span: 10, desc: "Read the spec → build TrySvg → tick contract → gaps → point readings → personal band → 7-day average → empty state → tests → rasterise and inspect." },
      optimized: { nodes: 10, span: 6, desc: "Read → build the rasterise-and-inspect harness first (the E11 oracle) → the five chart concerns fan out at width 4 → tests → verify." },
      moves: ["Pull the E11 rendered-surface oracle to node 2", "Fan-out the five independent chart concerns", "Declare the mutation oracle up front"],
      m: { timeN: 100, timeO: 60, tokN: 100, tokO: 100, compN: 90, compO: 94, rigN: 90, rigO: 96 },
      verdict: "modest",
      note: "This run was already strong — red observed by deliberate mutation, E11 and E12 both honoured. The gain is modest and mostly structural: the rasterise check <em>caught a legend/palette drift</em>, so building that oracle first makes the drift cheaper to find."
    },
    {
      id: "al-0003", repo: "HealthWatch", skill: "collectknowledge", outcome: "success", artifacts: 4,
      size: "large", tag: "ALREADY OPTIMAL", title: "Foundations research across four domains",
      prompt: "ground yourself in the repo then /collectknowledge on the following: Using Entra in Azure but allow me invitation of users by their email address… Getting health data from my apple ecosystem… from my whoop… Uploading medical records… Standard data models for: Health Records, Activity Tracking, Supplement Tracking, Nutrition Tracking — Secure web applications in Azure… also ground yourself in the architectures from the other two repos…",
      summary: "Built four sourced, confidence-labeled knowledge bases in docs/knowledge/ from 10 parallel research tracks (4 repo-mining, 6 primary-source web)… Graph seeded (35 artifacts, validate clean); 2 decision notes.",
      naive: { nodes: 12, span: 4, desc: "Already planned as a graph by the operator: ground → 10 parallel research tracks → synthesise → seed the graph." },
      optimized: { nodes: 12, span: 4, desc: "Essentially the same plan. The one change: the ten-wide fan-out gains an explicit width cap and transient-retry policy (GO7), which the run did not declare." },
      moves: ["No structural change — the operator already found the graph", "Add the missing fan-out contract (width cap + retry)"],
      m: { timeN: 100, timeO: 100, tokN: 100, tokO: 100, compN: 92, compO: 94, rigN: 85, rigO: 93 },
      verdict: "no-change",
      note: "★ <strong>The honesty case.</strong> Near-zero time gain, because a good operator had already parallelised it. The only real finding is a risk: this ran <strong>ten wide with no cap</strong>, and the meridian panel above tripped 429/529 at <strong>five</strong>. It succeeded, but it was not bounded."
    },
    {
      id: "al-0028", repo: "HealthWatch", skill: "—", outcome: "partial", artifacts: 1,
      size: "medium", tag: "EXTERNAL DEP", title: "Valid API key rejected at setup",
      prompt: "Diagnose Setup->AI rejecting the owner's valid Anthropic key",
      summary: "Root cause: app MI has read-only KV role; SetSecretAsync 403 -> unhandled 500 -> SPA catch-all painted the valid key 'didn't pass a live probe'. Fixed: endpoint 502 HW-SYS-002 on vault failure, SPA 'not judged' copy, negative test (throwing IAiKeyWriter), ROLE-NEED-A registered, TEST-CLOCK midnight flake in tile-states fixed. Deployed 56e5040. Role grant (Key Vault Secrets Officer) awaits the owner's az command; exposed key must be revoked+re-minted.",
      naive: { nodes: 9, span: 9, desc: "Diagnose → find the 403 → fix the endpoint → fix the SPA copy → negative test → register the class → fix an unrelated flake → deploy → discover an owner action is still required." },
      optimized: { nodes: 8, span: 6, desc: "Diagnose → enumerate external dependencies as explicit nodes at plan time → the role-grant request is raised immediately, in parallel with the three code fixes → tests → deploy." },
      moves: ["★ Surface the external blocker at planning, not at the end", "Fan-out the three independent code fixes", "Capture the unrelated flake fix as a next step (CT14), not scope"],
      m: { timeN: 100, timeO: 67, tokN: 100, tokO: 89, compN: 50, compO: 85, rigN: 80, rigO: 90 },
      verdict: "gain",
      note: "★ The work finished and then stopped on someone else's action. A dependency the agent cannot satisfy is still a node — naming it at plan time turns an end-of-run surprise into a request raised on day one."
    }
  ]
};
