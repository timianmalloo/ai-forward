---
id: kb-loa-pattern-catalog
title: "LOA — Pattern Catalog"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "architecture"
tags: [loa, patterns, architecture, pattern-catalog, reference]
links:
  - { to: kb-loa, rel: refines }
  - { to: architecture, rel: relates-to }
review-by: "2026-12-31"
summary: >-
  Part IV of the Layered Optimized Architecture, held separately because it is a lookup
  surface rather than a linear read. Every pattern with its intent, structure, applicability,
  trade-offs and cost impact — extracted verbatim so the LOA's principles can be loaded
  without paying for the whole catalog on every read.
---

*Extracted verbatim from `layered-optimized-architecture.md` (Part IV). The LOA remains the
authority; this file is the same text, addressable on its own.*

## Part IV — Pattern Catalog

**Summary.** Thirty-three patterns across six categories — routing, cost, verification, state, tools, safety. Each pattern follows a consistent template: Intent, Motivation, Applicability, Structure (often with C# code), Anti-pattern, Consequences, Related. C# samples target .NET 10+ (LTS) and assume Polly v8 (resilience), OpenTelemetry (observability), `System.Threading.Channels` (backpressured pipelines), `IAsyncEnumerable<T>` (streaming), `TimeProvider` (testable time), and `IHttpClientFactory` (connection pooling) are available. Samples use C# 14 features (primary constructors, collection expressions) where they aid legibility. Appendix D maps each concern to specific .NET libraries; Appendix G provides reference Roslyn analyzers that enforce conformance criteria.

---

### Category 1 — Routing & Composition

#### Pattern 1.1: Capability Router

**Intent.** Dispatch a request to the appropriate capability tier based on declared properties of the request.

**Motivation.** Not all requests need frontier reasoning. Many are routine and should be handled deterministically or by an SLM. A static "always-LLM" architecture wastes 10–100× on the easy cases.

**Applicability.** Workflows where requests vary in complexity, ambiguity, or value-at-risk.

**Structure.** A router component — deterministic policy or SLM-backed classifier — inspects the request and selects a handler. Handlers are interchangeable behind a uniform interface; the router carries policy. The pattern composes with Polly for handler-level resilience and OpenTelemetry for tier-decision audit.

```csharp
// Pattern: Capability Router (1.1)
public interface IRequestHandler {
    Task<HandlerOutcome> HandleAsync(Request request, BudgetContext budget, CancellationToken ct);
}

public sealed class CapabilityRouter(
    IReadOnlyDictionary<Tier, IRequestHandler> handlersByTier,
    IRouterPolicy policy,
    IAuditSink audit,
    TimeProvider clock,
    ResiliencePipeline resilience) {

    public async Task<HandlerOutcome> RouteAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        var routingDecision = policy.SelectTier(request);
        await audit.RecordRoutingAsync(request.Id, routingDecision, clock.GetUtcNow(), ct);
        var handler = handlersByTier[routingDecision.Tier];
        return await resilience.ExecuteAsync(
            async token => await handler.HandleAsync(request, budget, token),
            ct);
    }
}
```

**⚠ Anti-pattern: The Silent Always-Frontier Router.**

```csharp
// ⚠ Wrong: every request goes to the frontier LLM, regardless of complexity.
// No tier selection, no audit, no budget propagation, no resilience.
public sealed class NaiveRouter(ILlmClient frontier) {
    public Task<string> Handle(Request r) =>
        frontier.CompleteAsync(r.Prompt); // burns dollars on requests a regex could answer
}
```

**Consequences.** Dramatic cost reduction; introduces routing accuracy as a new failure mode (mis-routed requests). Mitigate by logging routing decisions, periodic audit, and Capability Escalator (6.1) from the handler.

**Related.** Cascade (1.2), Capability Escalator (6.1), Confidence-Calibrated Gating (6.4), Distillation Loop (2.3), Provider Portability (6.6).

#### Pattern 1.2: Cascade

**Intent.** Apply tiered filters in order of increasing cost, eliminating cases at each stage so the next stage processes only the residual.

**Motivation.** Many workflows have a power-law distribution of difficulty. A cascade exploits the distribution: cheap stages do most of the work, expensive stages see only the difficult residual.

**Applicability.** High-volume pipelines with a long tail of difficulty.

**Structure.** N stages, each with an admission predicate. Items resolved by a predicate emit as final results; others pass to the next stage. Cascade is Capability Router (1.1) with sequential semantics.

```csharp
// Pattern: Cascade (1.2)
public interface ICascadeStage<TInput, TOutput> {
    Task<StageResult<TOutput>> ProcessAsync(
        TInput input, BudgetContext budget, CancellationToken ct);
}

public abstract record StageResult<T>;
public sealed record Resolved<T>(T Value) : StageResult<T>;
public sealed record Passthrough<T> : StageResult<T>;
public sealed record Rejected<T>(string Reason) : StageResult<T>;

public sealed class Cascade<TInput, TOutput>(
    IReadOnlyList<ICascadeStage<TInput, TOutput>> stages) {

    public async Task<TOutput> ExecuteAsync(
        TInput input, BudgetContext budget, CancellationToken ct) {
        foreach (var stage in stages) {
            var result = await stage.ProcessAsync(input, budget, ct);
            switch (result) {
                case Resolved<TOutput> resolved: return resolved.Value;
                case Rejected<TOutput> rejected:
                    throw new CascadeRejectedException(rejected.Reason);
            }
        }
        throw new CascadeUnresolvedException("No stage resolved the input.");
    }
}
```

**Consequences.** Optimal aggregate cost. Potential high tail latency for items that traverse the full cascade. Mitigate by parallelizing where dependencies allow and capping cascade depth.

**Related.** Capability Router (1.1), Adversarial Debater (3.2), Capability Escalator (6.1), Speculative Execution (1.6).

#### Pattern 1.3: Plan/Execute Split

**Intent.** Separate the cognitive task of planning a workflow from the mechanical task of executing each step.

**Motivation.** Planning benefits from frontier reasoning; per-step execution rarely does. Running both on the same model wastes tokens and conflates two different failure modes.

**Applicability.** Multi-step workflows; tool-mediated construction; structured agent tasks where the steps are knowable in advance.

**Structure.** A Planner emits a structured plan — a DAG or a list of steps with dependencies. An Executor consumes the plan and dispatches each step. The Executor may itself be a model, a deterministic runtime, or a mix.

```csharp
// Pattern: Plan/Execute Split (1.3)
public sealed record Plan(
    string Id,
    IReadOnlyList<PlanStep> Steps,
    IReadOnlyDictionary<string, IReadOnlyList<string>> Dependencies);

public sealed record PlanStep(
    string Id,
    string Operation,
    IReadOnlyDictionary<string, object> Parameters);

public interface IPlanner {
    Task<Plan> PlanAsync(string goal, BudgetContext budget, CancellationToken ct);
}

public interface IPlanExecutor {
    IAsyncEnumerable<StepResult> ExecuteAsync(
        Plan plan, BudgetContext budget, CancellationToken ct);
}
```

**⚠ Anti-pattern: The Monolithic-Call Agent.**

```csharp
// ⚠ Wrong: a single frontier call asked to plan AND execute AND format.
// No inspection of the plan, no replayability, no per-step budgeting.
var combined = await frontier.CompleteAsync(
    $"Plan and execute this goal step by step: {goal}");
```

**Consequences.** Plans are inspectable, auditable, replayable. Executors are interchangeable. Failure modes: planner over-specifies (rigid); planner under-specifies (executor fills gaps unreliably).

**Related.** Hierarchical Decomposition (1.5), Typed Tool Surface (5.1), Capability Router (1.1), Receipt Ledger (4.3).

#### Pattern 1.4: Hot Path Bypass

**Intent.** Keep AI entirely out of the latency-critical execution path; expose AI only via asynchronous side channels.

**Motivation.** AI inference latency and non-determinism are incompatible with sub-millisecond, deterministic, or regulatory-bound hot paths.

**Applicability.** Trading engines, real-time control, payments, anything with SLA or determinism guarantees.

**Structure.** The hot path runs without AI dependency. Telemetry, decisions, and results stream to a side channel where AI components consume, analyze, and produce advisory output. Advisory output may modify hot-path configuration only after human or governance review; it never participates in a hot-path transaction.

```csharp
// Pattern: Hot Path Bypass (1.4)
public sealed class HotPathProcessor(
    IDeterministicProcessor hotPath,
    Channel<HotPathEvent> advisoryChannel) {

    public async Task<HotPathResult> ProcessAsync(
        HotPathRequest request, CancellationToken ct) {
        var result = await hotPath.ProcessAsync(request, ct); // pure deterministic
        var publishEvent = advisoryChannel.Writer.TryWrite(
            new HotPathEvent(request, result, DateTimeOffset.UtcNow));
        // Best-effort publish; never block the hot path on advisory channel pressure.
        return result;
    }
}

// Advisory consumer runs in a separate background service.
public sealed class AdvisoryConsumer(
    Channel<HotPathEvent> channel, IAdvisoryAnalyzer analyzer) : BackgroundService {
    protected override async Task ExecuteAsync(CancellationToken ct) {
        await foreach (var evt in channel.Reader.ReadAllAsync(ct))
            await analyzer.AnalyzeAsync(evt, ct);
    }
}
```

**Consequences.** Preserves SLA and determinism; AI cannot directly cause incidents on the critical path. Constrains AI influence to configuration changes and human-mediated decisions.

**Related.** Audit Trail (6.3), Adversarial Debater (3.2), Grounded Context Injector (4.1), Graceful Degradation (6.5).

#### Pattern 1.5: Hierarchical Decomposition

**Intent.** Decompose a complex goal into independently scoped sub-goals, dispatched to worker agents that have their own context, memory, and tool surface.

**Motivation.** Plan/Execute Split (1.3) assumes a single shared context. Long-horizon and complex tasks exceed the context window or benefit from specialization. Hierarchical decomposition gives each sub-task isolated working memory and a scoped tool surface, with the orchestrator coordinating handoffs.

**Applicability.** Multi-disciplinary research, large refactorings, multi-phase deployments, any task where sub-tasks have semantic boundaries.

**Structure.** An orchestrator decomposes the goal. For each sub-goal, it instantiates a worker, potentially recursively decomposing further. Each worker has its own context, may run at its own tier, and returns a structured result. The orchestrator integrates results.

```csharp
// Pattern: Hierarchical Decomposition (1.5)
public interface IWorkerAgent {
    Task<WorkerResult> ExecuteAsync(
        SubGoal goal, AgentContext context, CancellationToken ct);
}

public sealed class Orchestrator(
    Func<SubGoal, IWorkerAgent> workerFactory,
    IBudgetAllocator budgetAllocator) {

    public async Task<OrchestrationResult> ExecuteAsync(
        Goal goal, BudgetContext budget, CancellationToken ct) {
        var subGoals = await DecomposeAsync(goal, budget, ct);
        var subBudgets = budgetAllocator.Allocate(budget, subGoals);
        var tasks = subGoals.Select((subGoal, index) => {
            var worker = workerFactory(subGoal);
            var context = AgentContext.For(subGoal, subBudgets[index]);
            return worker.ExecuteAsync(subGoal, context, ct);
        });
        var results = await Task.WhenAll(tasks);
        return Integrate(results);
    }
}
```

**Consequences.** Scales to tasks no single agent could hold. Adds orchestration overhead and a new failure mode (decomposition quality). Workers can diverge from the original goal if their context is too narrow; mitigate by including the parent goal in each worker context.

**Related.** Plan/Execute Split (1.3), Memory (4.4), Token Budget Throttle (2.4), Long-Horizon Agent (Archetype H).

#### Pattern 1.6: Speculative Execution

**Intent.** Run a cheaper tier and a more expensive tier in parallel; commit to the cheaper result if it converges with sufficient confidence, otherwise wait for the expensive one.

**Motivation.** Per-call latency at frontier tiers is significant. For latency-sensitive applications, the SLM is often correct on easy cases; speculative execution lets the user see the fast answer immediately while the frontier verifies in the background.

**Applicability.** Interactive applications with mixed difficulty: UI tier choices, autocomplete, chat-style interfaces.

**Structure.** Two handlers run in parallel against the same input. A confidence-calibrated arbiter selects between them. If the cheap handler's confidence exceeds threshold and arrives first, commit; if the expensive handler arrives first or the cheap one is uncertain, use the expensive result.

```csharp
// Pattern: Speculative Execution (1.6)
public sealed class SpeculativeExecutor(
    IRequestHandler cheapHandler, IRequestHandler expensiveHandler, double threshold) {

    public async Task<Response> ExecuteAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        // Each branch reserves from the shared parent, so the speculative pair can
        // never collectively exceed the request budget even though both run.
        var cheap = cheapHandler.HandleAsync(
            request, budget.TryReserveFraction(0.1) ?? throw new BudgetExhaustedException(), cts.Token);
        var expensive = expensiveHandler.HandleAsync(
            request, budget.TryReserveFraction(0.9) ?? throw new BudgetExhaustedException(), cts.Token);

        var first = await Task.WhenAny(cheap, expensive);
        if (first == cheap && (await cheap).ConfidenceExceeds(threshold)) {
            cts.Cancel(); // best-effort: cancel the expensive call
            Observe(expensive); // never leave the loser's exception unobserved
            return (await cheap).Response;
        }
        return (await expensive).Response;
    }

    // Swallow/log the loser so a faulted background task does not escalate.
    private static void Observe(Task t) =>
        t.ContinueWith(static _ => { }, TaskScheduler.Default);
}
```

**⚠ Anti-pattern: Speculation Without Cancellation.** Firing both calls and ignoring the loser doubles cost on every request. The cancellation token MUST propagate to the underlying HTTP client, and the provider MUST honor request cancellation, for speculation to be cost-neutral on hits.

**Consequences.** Median latency drops sharply; tail latency is bounded by the expensive tier. Cost rises on cancellation-unfriendly providers. Requires confidence calibration.

**Related.** Capability Router (1.1), Confidence-Calibrated Gating (6.4), Token Budget Throttle (2.4), Provider Portability (6.6).

#### Pattern 1.7: Computer-Use / GUI Agent

**Intent.** Operate a graphical user interface as a fallback when no typed tool surface is available.

**Motivation.** Some target systems offer no API and no MCP server; the only way an agent can act on them is by observing the screen and emitting clicks, keystrokes, and scrolls. Computer-use agents fill this gap. They are dramatically more expensive, more brittle, and slower than Typed Tool Surface (5.1) — apply only when no alternative exists.

**Applicability.** Legacy systems without APIs; cross-application workflows; vendor SaaS without programmatic access; accessibility tooling.

**Structure.** The agent receives screenshots or accessibility-tree representations of the target UI. It emits low-level actions: click coordinates, key sequences, scroll deltas. A safety layer constrains action scope (allowed applications, allowed regions, rate limits). Receipts capture both the visual observation and the emitted action.

```csharp
// Pattern: Computer-Use / GUI Agent (1.7)
public sealed record ScreenObservation(
    byte[] PixelData, IReadOnlyList<UIElement> AccessibilityTree, DateTimeOffset CapturedUtc);

public sealed record GuiAction(GuiActionKind Kind, IReadOnlyDictionary<string, object> Parameters);

public enum GuiActionKind { Click, Type, Scroll, KeyCombo, Wait }

public interface IGuiAgent {
    Task<GuiAction> ChooseActionAsync(
        ScreenObservation observation, AgentGoal goal,
        BudgetContext budget, CancellationToken ct);
}
```

**⚠ Anti-pattern: Computer-Use When a Typed Tool Exists.** If the target system has an API or MCP server, use it. Computer-use is a last resort, not a convenience.

**Consequences.** Enables AI in environments without APIs. Cost per task is 10–100× a typed-tool equivalent. Reliability is materially lower; verification (P5) requires UI-state assertion after every action. Security and compliance burdens are heavier (the agent can in principle see any pixel).

**Related.** Typed Tool Surface (5.1), Sandboxed Executor (5.2), Audit Trail (6.3), Multimodal Pipeline (Archetype I).

---

### Category 2 — Cost Optimization

#### Pattern 2.1: Semantic Cache

**Intent.** Reuse prior model outputs for semantically similar inputs.

**Motivation.** Production workloads have heavy duplication; a verbatim cache misses near-duplicates. A vector-keyed cache captures them.

**Applicability.** LLM-backed query services with repetitive traffic (FAQ, support, RAG, recommendations).

**Structure.** The incoming query is embedded; the nearest neighbor in the cache is retrieved. If similarity exceeds threshold, the cached response returns, possibly after a freshness check. Otherwise, the model is invoked and the result inserted.

**Consequences.** Hit rates of 30–70% are typical for FAQ-class workloads. Risks: stale responses, semantic false positives. Mitigate with TTL, similarity threshold tuning, validation sampling.

**Related.** Prompt Prefix Cache (2.2), Grounded Context Injector (4.1), Hybrid Retrieval (4.5).

#### Pattern 2.2: Prompt Prefix Cache

**Intent.** Avoid re-paying for the static portion of long prompts on every call.

**Motivation.** Agentic system prompts, tool schemas, and few-shot examples are large and identical across calls. Most frontier APIs offer prefix caching at roughly 10% of normal token cost.

**Applicability.** Any workflow with a stable prompt prefix above a few hundred tokens — essentially all agentic systems.

**Structure.** Compose prompts as `[stable prefix][variable suffix]`. Mark the prefix as cacheable per the provider's API. Monitor cache hit rate as a service-level indicator. Some providers also offer context caching for long stable contexts beyond prefixes; treat this as an extension of the same pattern.

**Consequences.** Up to 90% cost reduction on the prefix portion. Constrains prompt design — prefixes must be truly stable. Cache eviction can cause surprise cost spikes; monitor.

**Related.** Semantic Cache (2.1), Token Budget Throttle (2.4).

#### Pattern 2.3: Distillation Loop

**Intent.** Migrate routine traffic from frontier LLM to a cheaper SLM by fine-tuning on logged frontier outputs.

**Motivation.** The frontier LLM is a generalist; production traffic has a narrow distribution. After enough logged traces, a small model fine-tuned on those traces matches the frontier on the in-distribution cases at a fraction of the cost.

**Applicability.** Mature workloads with stable input distribution and audit-quality logs.

**Structure.** Continuous logging feeds trace curation, then periodic SLM fine-tune, then A/B comparison, then traffic shift via Capability Router (1.1). The frontier model continues to handle out-of-distribution cases and to provide ground truth for ongoing distillation. The Evaluation Harness (Part IX) validates each candidate against held-out cases before promotion.

**Consequences.** Order-of-magnitude cost reduction on distillable traffic. Introduces an ML-ops pipeline as a new operational surface. Requires labeled audit trail.

**Related.** Capability Router (1.1), Audit Trail (6.3), Capability Escalator (6.1), Evaluation Harness (Part IX).

#### Pattern 2.4: Token Budget Throttle

**Intent.** Enforce a hard ceiling on tokens consumed per request or per workflow.

**Motivation.** Without an enforced budget, agentic loops can spiral — a planner that retries, an executor that re-summarizes, a critic that re-debates — and a single user request can cost dollars. Budget is the reliable circuit breaker.

**Applicability.** All agentic workflows. Non-negotiable for production.

**Structure.** A budget context is established at workflow entry. Every model call atomically reserves tokens before invocation. When budget is exhausted, further calls fail or degrade to a cheaper tier via Graceful Degradation (6.5).

```csharp
// Pattern: Token Budget Throttle (2.4)
public sealed class BudgetContext(long tokenBudget) {
    private long remaining = tokenBudget;

    // Correct: compare-and-swap so the budget never goes negative.
    public bool TryCharge(long tokens) {
        while (true) {
            var current = Volatile.Read(ref remaining);
            if (current < tokens) return false;
            if (Interlocked.CompareExchange(ref remaining, current - tokens, current) == current)
                return true;
        }
    }

    public long Remaining => Volatile.Read(ref remaining);

    // Carve a child budget OUT OF this one. The reserved tokens are charged to the
    // parent NOW (via TryCharge), so the sum of all children can never exceed the
    // parent ceiling. Returns null when insufficient budget remains.
    // A detached `new BudgetContext(fraction * Remaining)` would NOT draw down the
    // parent — concurrent children would each see the full budget and collectively
    // overspend, silently violating C2.
    public BudgetContext? TryReserve(long tokens) =>
        TryCharge(tokens) ? new BudgetContext(tokens) : null;

    public BudgetContext? TryReserveFraction(double fraction) =>
        TryReserve((long)(Remaining * Math.Clamp(fraction, 0.0, 1.0)));
}
```

**Invariant.** `Remaining` is monotonically non-increasing and never negative; the sum of tokens carved into children never exceeds the parent ceiling. A child that wishes to return its unspent remainder to the parent does so explicitly (a `Release` that `Interlocked.Add`s back) — children never *implicitly* reconcile.

**⚠ Anti-pattern: Decrement-Then-Check.**

```csharp
// ⚠ Wrong: by the time the check fires, the budget has already gone negative
// under contention. Allows over-spending.
public void Charge(long tokens) {
    if (Interlocked.Add(ref remaining, -tokens) < 0)
        throw new BudgetExhaustedException();
}
```

**Consequences.** Bounded cost per request; surfaces inefficient workflows quickly. Adds error-handling complexity. Strict budget enforcement requires CAS or a lock — the seductive `Interlocked.Add` is wrong. Sub-budgets MUST be *reservations* carved from the parent (they charge it now), not detached copies; otherwise concurrent children collectively overspend the ceiling they were meant to respect.

**Related.** Capability Escalator (6.1), Audit Trail (6.3), Graceful Degradation (6.5), Test-Time Compute Budget (2.6).

#### Pattern 2.5: Schema-Constrained Output

**Intent.** Force the model to emit structured output matching a declared schema.

**Motivation.** Free-text outputs require parsing, validation, and retries. Schema-constrained generation (JSON mode, tool-calling schemas, constrained decoding) eliminates that overhead and reduces output tokens.

**Applicability.** Model output consumed programmatically by downstream code.

**Structure.** Declare a schema (JSON Schema, C# record with attributes). Pass to the model API as a tool definition or response format. Validate the response against the schema; on violation, retry or fail. For long structured outputs, prefer streaming validation via `IAsyncEnumerable<T>` to fail fast on schema violations rather than waiting for full output.

```csharp
// Pattern: Schema-Constrained Output (2.5)
public sealed record TriageDecision(
    [property: JsonPropertyName("severity")] Severity Severity,
    [property: JsonPropertyName("category")] string Category,
    [property: JsonPropertyName("reasoning")] string Reasoning,
    [property: JsonPropertyName("confidence")] double Confidence);

public async Task<TriageDecision> TriageAsync(Alert alert, CancellationToken ct) {
    var response = await llmClient.CompleteWithSchemaAsync<TriageDecision>(
        prompt: BuildPrompt(alert),
        schema: JsonSchema.FromType<TriageDecision>(),
        ct: ct);
    return response.ValidatedOrThrow();
}

// Streaming variant: validate as tokens arrive; abort on schema violation.
public async IAsyncEnumerable<TriageDecision> TriageBatchAsync(
    IAsyncEnumerable<Alert> alerts, [EnumeratorCancellation] CancellationToken ct) {
    await foreach (var alert in alerts.WithCancellation(ct)) {
        var decision = await TriageAsync(alert, ct);
        yield return decision;
    }
}
```

**⚠ Anti-pattern: Regex-Parsing of Free-Text Output.**

```csharp
// ⚠ Wrong: brittle, retries on parse failure, drifts on model upgrade.
var raw = await llm.CompleteAsync(prompt);
var severity = Regex.Match(raw, @"severity:\s*(\w+)").Groups[1].Value;
```

**Consequences.** Tighter integration; fewer parse errors; smaller output. Constrains the model's expressive range (sometimes useful, sometimes too restrictive).

**Related.** Typed Tool Surface (5.1), Plan/Execute Split (1.3).

#### Pattern 2.6: Test-Time Compute Budget

**Intent.** Allocate inference-time reasoning depth (extended thinking, chain-of-thought iterations, scratchpad tokens) based on problem difficulty rather than applying a flat depth to all calls.

**Motivation.** Reasoning models (o-series, Claude with extended thinking) let the caller spend more tokens at inference to gain capability. Flat allocation either wastes tokens on easy cases or underpowers hard ones. The decision is a separate budgeting axis from token budget.

**Applicability.** Workflows using reasoning-capable models with adjustable thinking budgets.

**Structure.** A difficulty estimator (cheap classifier, prior calls' confidence, request metadata) maps the request to a reasoning depth. The model call is parameterized accordingly.

```csharp
// Pattern: Test-Time Compute Budget (2.6)
public enum ReasoningDepth { Minimal, Standard, Extended, Maximum }

public sealed record ThinkingPolicy(ReasoningDepth Depth, int MaxThinkingTokens) {
    public static ThinkingPolicy For(RequestProfile profile) => profile switch {
        { Difficulty: < 0.3 } => new(ReasoningDepth.Minimal, 0),
        { Difficulty: < 0.6 } => new(ReasoningDepth.Standard, 2_000),
        { Difficulty: < 0.85 } => new(ReasoningDepth.Extended, 8_000),
        _ => new(ReasoningDepth.Maximum, 32_000),
    };
}
```

**Consequences.** Better capability-to-cost ratio on heterogeneous traffic. Adds a difficulty-estimation surface. Provider-dependent — not all models expose this lever.

**Related.** Capability Router (1.1), Token Budget Throttle (2.4), Confidence-Calibrated Gating (6.4).

---

### Category 3 — Verification

#### Pattern 3.1: Deterministic Verifier

**Intent.** Confirm a model's output by running a deterministic check the model could not have faked.

**Motivation.** Model outputs are plausible by construction. Plausibility is not correctness. A deterministic verifier closes the gap by executing the claim.

**Applicability.** Domains where correctness is checkable — math (compute it), code (run tests), claims about data (re-query the data), exploits (run them), proofs (check them).

**Structure.** The model produces a candidate output. A separate component, written as ordinary code, executes the verification. Passing outputs emit; failing outputs trigger retry, escalation, or rejection.

```csharp
// Pattern: Deterministic Verifier (3.1)
public interface IVerifier<TOutput> {
    Task<VerificationResult> VerifyAsync(TOutput candidate, CancellationToken ct);
}

public abstract record VerificationResult;
public sealed record Verified : VerificationResult;
public sealed record Failed(
    string Reason, IReadOnlyDictionary<string, object> Evidence) : VerificationResult;

public sealed class VerifiedHandler<TOutput>(
    IModelClient model, IVerifier<TOutput> verifier, int maxRetries) : IRequestHandler {

    public async Task<HandlerOutcome> HandleAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        for (var attempt = 0; attempt < maxRetries; attempt++) {
            var candidate = await model.GenerateAsync<TOutput>(request, budget, ct);
            var result = await verifier.VerifyAsync(candidate, ct);
            if (result is Verified) return new Resolved(candidate);
        }
        return new Escalate(
            "verification exhausted retries",
            new Dictionary<string, object> { ["attempts"] = maxRetries });
    }
}
```

**⚠ Anti-pattern: Trusting the Model's Self-Report.**

```csharp
// ⚠ Wrong: the model says it's correct; we take its word for it.
// Hallucination → plausible but wrong claim → silent failure.
var output = await llm.GenerateAsync<Answer>(prompt);
if (output.SelfReportedConfidence > 0.9) return output;
```

**Consequences.** Hallucinations caught structurally rather than statistically. Requires that the domain has a deterministic verifier — not always possible.

**Related.** Prover Agent (3.3), Adversarial Debater (3.2), Sandboxed Executor (5.2), Self-Consistency (3.5).

#### Pattern 3.2: Adversarial Debater

**Intent.** Generate explicit counter-arguments against a proposed model output before accepting it.

**Motivation.** A single model cannot reliably critique itself. An agent in a distinct role — possibly backed by a different model — finds weaknesses the proposer missed.

**Applicability.** High-stakes decisions; pipelines where false positives or false negatives carry real cost.

**Structure.** The proposer emits a candidate with reasoning. The debater receives the output and argues against it. A judge — deterministic rubric, third agent, or human — resolves the disagreement.

**Consequences.** Significant accuracy improvement at 2–3× per-decision cost (often acceptable given the high-stakes context). The debater MUST be structurally independent — different prompt, ideally different model — to avoid mode collapse.

**Related.** Prover Agent (3.3), Red Team Probe (3.4), Reflection (3.6), Self-Consistency (3.5), Plan/Execute Split (1.3).

#### Pattern 3.3: Prover Agent

**Intent.** Require a candidate finding to come with an executable artifact that demonstrates its validity.

**Motivation.** Stronger than debate. The debater argues; the prover produces a witness. In security: an exploit input. In math: a proof object. In code review: a failing test that the fix passes. In incident response: a canary replay.

**Applicability.** Vulnerability discovery, formal verification, scientific hypothesis testing, root-cause analysis.

**Structure.** The proposer generates a hypothesis. The prover constructs an artifact (input, test, proof). The artifact executes in a deterministic environment. Only proven findings pass.

**Consequences.** Eliminates plausibility-driven false positives almost entirely. Constrains output to claims for which a witness can be constructed — not all domains qualify.

**Related.** Deterministic Verifier (3.1), Sandboxed Executor (5.2), Adversarial Debater (3.2).

#### Pattern 3.4: Red Team Probe

**Intent.** Continuously generate adversarial inputs designed to expose coverage gaps in the system.

**Motivation.** Verifiers and debaters validate individual outputs. They do not reveal what the system misses. A red-team agent's job is to find inputs the system gets wrong.

**Applicability.** Security postures, content moderation, agent safety, fraud detection, compliance gates.

**Structure.** A red-team agent — an LLM with adversarial prompt and tools — generates candidate inputs. The system under test processes them. A scorer measures success rate. Failures surface as findings; the system hardens against them.

**Consequences.** Surfaces unknown unknowns. Never terminates — adversarial coverage is open-ended. Risk: the red team itself becomes a target for capture or specification gaming.

**Related.** Adversarial Debater (3.2), Audit Trail (6.3), Continuous Sentinel (Archetype G), Evaluation Harness (Part IX).

#### Pattern 3.5: Self-Consistency

**Intent.** Generate multiple independent samples from the model and select the consensus answer.

**Motivation.** A single sample reflects one trajectory through the model's distribution. Sampling N times and selecting by majority vote, semantic clustering, or LLM-judge captures the distribution's mode. For domains with a unique correct answer (math, structured extraction), this materially improves accuracy at modest cost.

**Applicability.** Tasks with a small set of admissible answers; structured extraction; classification; arithmetic and symbolic reasoning.

**Structure.** Run N samples at non-zero temperature. Aggregate by majority vote on canonicalized output, by semantic clustering, or by a judge model. Emit the consensus.

```csharp
// Pattern: Self-Consistency (3.5)
public sealed class SelfConsistentSampler<T>(
    IModelClient model, int sampleCount, IConsensusStrategy<T> consensus)
    where T : notnull {

    public async Task<ConsensusResult<T>> SampleAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        // Reserve N equal shares from the parent up front. Sharing one detached
        // `Sub(1/N)` instance across N concurrent tasks (the original shape) both
        // under-budgets each sample and fails to charge the parent.
        var share = budget.Remaining / sampleCount;
        var sampleTasks = Enumerable.Range(0, sampleCount)
            .Select(_ => model.GenerateAsync<T>(
                request,
                budget.TryReserve(share) ?? throw new BudgetExhaustedException(),
                ct));
        var samples = await Task.WhenAll(sampleTasks);
        return consensus.Aggregate(samples);
    }
}

public sealed record ConsensusResult<T>(
    T Value, double Agreement, IReadOnlyList<T> Dissenting);
```

**Consequences.** Accuracy gain at N× cost, typically N=5–10. Most cost-effective on hard cases — pair with Capability Router (1.1) so easy cases use N=1. Useless when the model is uniformly wrong; sampling does not fix systematic bias.

**Related.** Capability Router (1.1), Deterministic Verifier (3.1), Reflection (3.6), Token Budget Throttle (2.4), Adversarial Debater (3.2).

#### Pattern 3.6: Reflection (Self-Critique)

**Intent.** Have the model critique and revise its own output in a structured second pass.

**Motivation.** Models often catch their own errors on a second look, especially when prompted to focus on specific failure modes. Distinct from Adversarial Debater (3.2): reflection is the same model in two passes; debater is structurally separate. Reflection is cheap; debater is rigorous.

**Applicability.** Code generation (find your own bugs), document drafting (revise for clarity), planning (check the plan against the goal).

**Structure.** First pass: generate. Second pass: prompt with the generation and a critique rubric. Third pass: revise based on critique. Optionally iterate. Halt when the critic finds nothing to revise, or budget is exhausted.

```csharp
// Pattern: Reflection / Self-Critique (3.6)
public sealed class ReflectiveGenerator<T>(IModelClient model) {

    public async Task<T> GenerateAsync(
        string goal, IReflectionRubric rubric,
        BudgetContext budget, CancellationToken ct) {
        var draft = await model.GenerateAsync<T>(
            goal, budget.TryReserveFraction(0.4) ?? throw new BudgetExhaustedException(), ct);
        var critique = await model.CritiqueAsync(
            draft, rubric, budget.TryReserveFraction(0.5) ?? throw new BudgetExhaustedException(), ct);
        return critique.HasIssues
            ? await model.ReviseAsync<T>(
                draft, critique, budget.TryReserveFraction(1.0) ?? throw new BudgetExhaustedException(), ct)
            : draft;
    }
}
```

**⚠ Anti-pattern: Unbounded Reflection Loop.** Reflection without a termination criterion or budget is a class of Unbudgeted Loop. Each iteration finds something to revise because the prompt asks for critique.

**Consequences.** Modest accuracy gain at 2–3× cost on the calls where it fires. Lower ceiling than adversarial debate but cheaper. Risk: same-model blind spots remain invisible.

**Related.** Adversarial Debater (3.2), Self-Consistency (3.5), Token Budget Throttle (2.4).

---

### Category 4 — State & Context

#### Pattern 4.1: Grounded Context Injector

**Intent.** Inject retrieved authoritative content into the model's prompt rather than relying on training-time knowledge.

**Motivation.** Training data ages; proprietary data is absent; hallucinations reduce when the answer is in the context.

**Applicability.** Q&A over corpora, decision support with policy documents, current-event reasoning.

**Structure.** Query feeds retrieval (see Hybrid Retrieval, 4.5), then ranking, then top-k chunks injected into prompt with explicit citation markers. The model is instructed to answer from sources only and to cite.

**Consequences.** Dramatically reduced hallucination. Introduces retrieval quality as a new failure mode. Per-call latency rises by the retrieval round-trip.

**Related.** Hybrid Retrieval (4.5), Semantic Cache (2.1), Receipt Ledger (4.3), Schema-Constrained Output (2.5), Memory (4.4).

#### Pattern 4.2: Tool-Mediated State

**Intent.** Keep workflow state in tools, not in the model's context window.

**Motivation.** Context windows are finite, expensive, and lossy. Tools — databases, file systems, external services — are effectively unbounded, cheap, and lossless. The model should reach into state via tool calls rather than carry it.

**Applicability.** Long-running workflows; multi-session agents; any system where state outlives a single inference call.

**Structure.** State stores in domain-appropriate stores. Tools expose read/write operations. The model receives handles and summaries; it fetches detail on demand.

**Consequences.** Workflows run for arbitrary length. State survives model restarts and version changes. Introduces tool-call latency on state access.

**Related.** Typed Tool Surface (5.1), Receipt Ledger (4.3), Memory (4.4), Idempotent Action (5.3).

#### Pattern 4.3: Receipt Ledger

**Intent.** Maintain an append-only log of every model decision, tool invocation, and outcome.

**Motivation.** AI workflows are non-deterministic. Without a receipt ledger, debugging is impossible, compliance is unprovable, and distillation cannot start.

**Applicability.** All production AI workflows. Non-negotiable in regulated industries.

**Structure.** Each call (model or tool) writes a record: timestamp, agent identity, model identity and version, input (or input hash if large), output, cost, latency, trace ID. Records are append-only; storage is durable. The natural .NET implementation pairs OpenTelemetry `Activity` instrumentation with a durable sink, and OpenTelemetry `Meter` for cost and token metrics.

```csharp
// Pattern: Receipt Ledger (4.3)
public sealed class ReceiptLedger(
    IReceiptStore store, TimeProvider clock) : IAuditSink {

    private static readonly ActivitySource Source = new("LOA.ModelCall");
    private static readonly Meter Meter = new("LOA.ModelCall");
    private static readonly Counter<long> TokensInput =
        Meter.CreateCounter<long>("loa.tokens.input");
    private static readonly Counter<long> TokensOutput =
        Meter.CreateCounter<long>("loa.tokens.output");
    private static readonly Counter<double> CostUsd =
        Meter.CreateCounter<double>("loa.cost.usd");

    public async Task<Receipt> RecordCallAsync(
        ModelCallRequest request, ModelCallResponse response, CancellationToken ct) {
        using var activity = Source.StartActivity("model.call");
        activity?.SetTag("model.id", request.ModelId);
        activity?.SetTag("model.version", request.ModelVersion);
        activity?.SetTag("model.tier", request.Tier.ToString());

        var tags = new TagList {
            { "model.id", request.ModelId }, { "model.tier", request.Tier.ToString() }
        };
        TokensInput.Add(response.InputTokens, tags);
        TokensOutput.Add(response.OutputTokens, tags);
        CostUsd.Add(response.CostUsd, tags);

        var receipt = new Receipt(
            Id: Guid.NewGuid(),
            TimestampUtc: clock.GetUtcNow(),
            TraceId: activity?.TraceId.ToString(),
            ModelId: request.ModelId,
            ModelVersion: request.ModelVersion,
            Tier: request.Tier,
            InputHash: request.InputHash,
            OutputDigest: response.OutputDigest,
            CostUsd: response.CostUsd,
            LatencyMs: response.LatencyMs);

        await store.AppendAsync(receipt, ct);
        return receipt;
    }
}
```

**⚠ Anti-pattern: The Console-Log Audit.**

```csharp
// ⚠ Wrong: not durable, not queryable, not compliance-grade, not joinable with traces.
_logger.LogInformation("Called {Model} cost {Cost}", model, cost);
```

**Consequences.** Storage cost is modest in dollars but grows in volume. Foundational for everything downstream. Privacy considerations for input/output content; PII handling required. Records SHOULD capture the *acting principal* (whose authority the call ran under), not only the model identity — without it, P11/C11 cannot be audited.

**Related.** Audit Trail (6.3), Distillation Loop (2.3), Idempotent Action (5.3).

#### Pattern 4.4: Memory (Working / Episodic / Semantic)

**Intent.** Persist agent knowledge across sessions and across calls, distinguishing the kind of memory by access semantics.

**Motivation.** Long-horizon and multi-session agents need state that survives a context window. Treating memory as monolithic — a single blob the model retrieves — conflates information with very different retention, retrieval, and update semantics.

**Applicability.** Long-Horizon Agents (Archetype H), multi-session conversational systems, ops agents that learn from past incidents.

**Structure.** Three memory kinds with distinct stores and retrieval patterns. Working memory holds the current task focus — bounded, ephemeral, lives in context or a side-store, clears at task completion. Episodic memory records past interactions, actions, and outcomes — append-only, retrieved by recency and relevance. Semantic memory distills facts and skills accumulated over time — curated, retrieved by similarity, periodically consolidated.

```csharp
// Pattern: Memory (4.4)
public interface IAgentMemory {
    Task<IReadOnlyList<MemoryItem>> RecallAsync(
        MemoryKind kind, RecallQuery query, CancellationToken ct);
    Task RememberAsync(MemoryItem item, CancellationToken ct);
    Task<int> ConsolidateAsync(ConsolidationPolicy policy, CancellationToken ct);
}

public enum MemoryKind { Working, Episodic, Semantic }
```

**⚠ Anti-pattern: Dump-All-History-Into-Context.** Treating prior turns as monolithic context defeats the point of memory architecture. Episodic memory SHOULD be retrieved by relevance; old episodes SHOULD summarize into semantic memory and then drop.

**Consequences.** Agent capability extends well past a single context. Memory becomes an operational concern with its own pipelines — write, retrieve, consolidate, forget. Cost-effectiveness depends on retrieval precision.

**Related.** Tool-Mediated State (4.2), Hybrid Retrieval (4.5), Long-Horizon Agent (Archetype H), Grounded Context Injector (4.1).

#### Pattern 4.5: Hybrid Retrieval

**Intent.** Combine multiple retrieval strategies — vector, lexical (BM25), structured (SQL or graph), graph traversal — and merge their results.

**Motivation.** Pure vector retrieval misses exact-match cases (proper names, IDs, recent terminology). Pure lexical misses paraphrase. Structured retrieval is needed for "documents tagged X created after Y." Modern retrieval is multi-strategy.

**Applicability.** Non-trivial Grounded Synthesizer (Archetype D) implementations. Trivial FAQ retrieval can still be vector-only.

**Structure.** Multiple retrievers run in parallel against the corpus. Results merge via reciprocal rank fusion (RRF), weighted scoring, or a learned re-ranker. Top-k from the fused list passes to the synthesizer. In agentic variants, the model chooses which retrievers to use and may iterate.

**Consequences.** Substantially higher recall and precision than any single strategy. Increases retrieval-side engineering complexity. Re-ranker becomes a quality-engineering surface in its own right.

**Related.** Grounded Context Injector (4.1), Semantic Cache (2.1), Memory (4.4).

---

### Category 5 — Tool Integration

#### Pattern 5.1: Typed Tool Surface

**Intent.** Expose domain operations to models as typed, validated tool calls rather than a free-form API.

**Motivation.** When a model can call a typed tool, it does not need to generate code to call an underlying API. Syntax overhead drops; the action space is constrained; errors are typed. This is the MCP architectural insight applied to any internal domain.

**Applicability.** Any integration with a system that has a stable operation set — CAD, presentation, IaC, ticketing, CRM, observability.

**Structure.** Each tool is a function with a schema — name, parameters, return type, errors. The model emits structured tool calls; a runtime validates against schema, dispatches, returns typed results. A source generator transforms `[Tool]`-attributed records into JSON schemas at compile time, eliminating runtime reflection.

```csharp
// Pattern: Typed Tool Surface (5.1)
[Tool("create_sketch", "Create a 2D sketch on a reference plane")]
public sealed record CreateSketchTool(
    [param: Required, Description("Reference plane on which the sketch will be drawn")]
    PlaneRef Plane,
    [param: Required, Description("Closed profile defining the sketch geometry")]
    IReadOnlyList<Profile> Profile) : ITool<SketchHandle>;

public sealed record SketchHandle(Guid Id);
public sealed record ToolError(string Code, string Message);
public sealed record ToolResult<T>(T? Value, ToolError? Error) {
    public bool IsSuccess => Error is null;
}

// Compile-time schema generation skeleton.
// Full implementation in Appendix G.
[Generator]
public sealed class ToolSchemaGenerator : IIncrementalGenerator {
    public void Initialize(IncrementalGeneratorInitializationContext context) {
        var toolTypes = context.SyntaxProvider.ForAttributeWithMetadataName(
            "ToolAttribute",
            predicate: static (node, _) => node is RecordDeclarationSyntax,
            transform: static (ctx, _) => GetToolSchema(ctx));
        context.RegisterSourceOutput(toolTypes, EmitSchemaRegistration);
    }
    // GetToolSchema and EmitSchemaRegistration implementations elided here;
    // full skeleton in Appendix G.
}
```

**⚠ Anti-pattern: Free-Text-Then-Eval.**

```csharp
// ⚠ Wrong: model emits Python; we exec it. Tool surface unconstrained;
// security nightmare; verbose token use; brittle on model upgrades.
var code = await llm.CompleteAsync($"Write Python to create a sketch on plane {plane}");
ExecutePython(code); // do not do this
```

**Consequences.** Smaller token footprint; better reliability; typed failure modes. Requires investment in tool design; a poorly designed tool surface forces the model back to general reasoning.

**Related.** Schema-Constrained Output (2.5), Plan/Execute Split (1.3), Sandboxed Executor (5.2), Idempotent Action (5.3), Computer-Use Agent (1.7).

#### Pattern 5.2: Sandboxed Executor

**Intent.** Run model-generated code or model-invoked tools in an isolated environment.

**Motivation.** Models can — by mistake or by adversarial input — emit destructive operations. The system MUST constrain blast radius.

**Applicability.** Any setting where model output triggers side effects: code generation, agent tool use, SQL generation, infrastructure changes.

**Structure.** Generated artifacts execute inside a process, container, or VM with restricted capabilities. Network, filesystem, and resource limits are enforced. Outputs are validated before being released to the broader system.

**Consequences.** Bounded risk; necessary for any real-world deployment. Adds latency and infrastructure cost.

**Related.** Typed Tool Surface (5.1), Idempotent Action (5.3), Audit Trail (6.3), Computer-Use Agent (1.7).

#### Pattern 5.3: Idempotent Action

**Intent.** Design every model-triggerable action so repeated invocation is safe.

**Motivation.** Models retry; orchestrators retry; users retry. Without idempotency, retries compound. The classical "double-submit order" problem returns in agent form.

**Applicability.** All tools exposed to models — especially those with persistent side effects (writes, sends, deploys).

**Structure.** Each action accepts an idempotency key. The runtime *atomically reserves* the key before executing (e.g. Redis `SET key NX`, or a SQL row with a unique constraint), transitions it through `Pending → Completed`, and persists the result against the key. A concurrent or retried call that finds the key already reserved waits for, or returns, the original outcome — it never re-executes the side effect. Reserving *before* execution (not storing *after*) is what closes the race. Keys are scoped (per-workflow, per-request).

```csharp
// Pattern: Idempotent Action (5.3)
public readonly record struct IdempotencyKey(string Scope, string Id);

public enum ReservationState { Reserved, AlreadyCompleted, InFlight }

public interface IIdempotencyStore {
    // Atomic: only ONE caller per key receives Reserved (e.g. SET NX).
    Task<(ReservationState State, TOutput? Result)> TryReserveAsync<TOutput>(
        IdempotencyKey key, CancellationToken ct);
    Task CompleteAsync<TOutput>(IdempotencyKey key, TOutput result, CancellationToken ct);
    Task<TOutput> AwaitCompletionAsync<TOutput>(IdempotencyKey key, CancellationToken ct);
}

public sealed class IdempotentActionWrapper<TInput, TOutput>(
    IAction<TInput, TOutput> inner,
    IIdempotencyStore store) : IIdempotentAction<TInput, TOutput> {

    public async Task<TOutput> ExecuteAsync(
        IdempotencyKey key, TInput input, CancellationToken ct) {
        var (state, prior) = await store.TryReserveAsync<TOutput>(key, ct);
        switch (state) {
            case ReservationState.AlreadyCompleted: return prior!;
            case ReservationState.InFlight: return await store.AwaitCompletionAsync<TOutput>(key, ct);
            default:
                var result = await inner.ExecuteAsync(input, ct); // we hold the reservation
                await store.CompleteAsync(key, result, ct);
                return result;
        }
    }
}
```

**Invariant.** The wrapped side effect executes *at most once* per key under concurrency and retry. True *exactly-once* additionally requires the side effect and the `Completed` transition to share a transaction (or the action to be naturally idempotent); otherwise a crash after the side effect but before `CompleteAsync` leaves the key `Pending` and a retry re-executes — call this out in the action's contract.

**⚠ Anti-pattern: Store-After-Execute (Check-Then-Act).**

```csharp
// ⚠ Wrong: two concurrent calls with the same key both miss the store and both
// execute the side effect — the double-submit this pattern exists to prevent.
var existing = await store.TryGetAsync<TOutput>(key, ct);
if (existing.HasValue) return existing.Value;
var result = await inner.ExecuteAsync(input, ct); // racing duplicate fires here too
await store.StoreAsync(key, result, ct);
```

**Consequences.** Safe retries; slight implementation overhead; requires key management.

**Related.** Receipt Ledger (4.3), Sandboxed Executor (5.2), Capability Escalator (6.1).

---

### Category 6 — Quality & Safety

#### Pattern 6.1: Capability Escalator

**Intent.** Allow a lower-tier handler to escalate a request to a higher-tier handler when it cannot resolve confidently.

**Motivation.** Static routing misroutes. The handler itself is in the best position to recognize "this is beyond me."

**Applicability.** Any tiered system where individual requests may be more complex than the routing policy predicted.

**Structure.** Handlers return either a result or an `Escalate` signal with reasoning. The orchestrator catches escalation and re-dispatches to a higher tier, carrying the prior handler's analysis as context.

```csharp
// Pattern: Capability Escalator (6.1)
public abstract record HandlerOutcome;
public sealed record Resolved(Response Result) : HandlerOutcome;
public sealed record Escalate(
    string Reason,
    IReadOnlyDictionary<string, object> Context,
    int Attempts = 1) : HandlerOutcome;

public sealed class EscalatingDispatcher(
    IReadOnlyList<IRequestHandler> tiersAscending, int maxEscalations) {

    public async Task<Response> DispatchAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        var startTier = 0;
        for (var attempt = 0; attempt < maxEscalations; attempt++) {
            var outcome = await tiersAscending[startTier].HandleAsync(request, budget, ct);
            switch (outcome) {
                case Resolved r: return r.Result;
                case Escalate e when startTier + 1 < tiersAscending.Count:
                    request = request.WithContext(e.Context);
                    startTier++;
                    continue;
                default: throw new EscalationExhaustedException();
            }
        }
        throw new EscalationExhaustedException();
    }
}
```

**Consequences.** Robust to routing errors; provides training signal for routing improvement. Risk: cascading escalation when handlers are over-eager; mitigate with escalation budget.

**Related.** Capability Router (1.1), Cascade (1.2), Confidence-Calibrated Gating (6.4), Token Budget Throttle (2.4).

#### Pattern 6.2: Guardrail Filter

**Intent.** Apply policy checks to model inputs and outputs out-of-band from the primary call.

**Motivation.** Models cannot be relied on to enforce their own safety, compliance, or output policies. A dedicated filter is structurally separate.

**Applicability.** All user-facing AI systems; especially those with regulatory or brand exposure.

**Structure.** Pre-filter examines input for policy violations — jailbreak attempts, PII, prohibited content. Post-filter examines output for similar concerns plus correctness and format. Filters can themselves be small models or deterministic rules. Filter failures generate logged incidents.

**Consequences.** Bounded policy surface; adds latency. Filter quality is itself a quality-engineering problem requiring its own red-teaming.

**Related.** Sandboxed Executor (5.2), Receipt Ledger (4.3), Red Team Probe (3.4).

#### Pattern 6.3: Audit Trail

**Intent.** Maintain compliance-grade records of AI decisions sufficient to reconstruct, justify, or contest them after the fact.

**Motivation.** Regulators, auditors, customers, and engineering teams all need to understand "why did the system do that?" Without an audit trail, every such question is unanswerable.

**Applicability.** Regulated industries (finance, healthcare, defense, critical infrastructure); any system where decisions affect users, money, or safety.

**Structure.** Extends Receipt Ledger (4.3) with policy metadata: which rules applied, which guardrails fired, which model versions were involved, which prompts were used, which alternatives were considered. Designed to satisfy external audit — immutable, complete, queryable.

**Consequences.** Compliance-grade observability; significant storage and access-control investment. Enables incident response and post-mortems.

**Related.** Receipt Ledger (4.3), Guardrail Filter (6.2), Distillation Loop (2.3).

#### Pattern 6.4: Confidence-Calibrated Gating

**Intent.** Use the model's own (or an external) uncertainty estimate to decide whether to commit, escalate, or seek verification.

**Motivation.** Static routing rules cannot anticipate every request. A confidence signal — calibrated probability, ensemble agreement, judge score — provides per-request adaptivity. The key word is calibrated: an uncalibrated confidence is worse than none.

**Applicability.** Production systems with verifiable feedback loops to calibrate against.

**Structure.** Generate a candidate with an associated confidence score. Compare against thresholds. Above commit threshold: emit. Between commit and escalation thresholds: invoke verifier (3.1) or self-consistency (3.5). Below escalation threshold: escalate (6.1). Calibration maintains via Receipt Ledger feedback and periodic re-fit.

```csharp
// Pattern: Confidence-Calibrated Gating (6.4)
public sealed record CalibratedDecision<T>(T Value, double Confidence);

public sealed class ConfidenceGate<T>(
    double commitThreshold, double escalationThreshold) {

    public async Task<HandlerOutcome> EvaluateAsync(
        CalibratedDecision<T> decision,
        IVerifier<T> verifier, CancellationToken ct) =>
        decision.Confidence switch {
            var c when c >= commitThreshold => new Resolved(decision.Value!),
            var c when c < escalationThreshold => new Escalate(
                $"confidence {c:F2} below escalation threshold",
                new Dictionary<string, object> { ["original"] = decision.Value! }),
            _ => await verifier.VerifyAsync(decision.Value, ct) is Verified
                ? new Resolved(decision.Value!)
                : new Escalate("verifier rejected mid-confidence output",
                    new Dictionary<string, object>())
        };
}
```

**⚠ Anti-pattern: Uncalibrated Self-Reported Confidence.** Asking the model "how confident are you?" and using the number directly is unreliable. Models are systematically over- or under-confident. Calibrate against held-out outcomes or use ensemble agreement (3.5) instead.

**Consequences.** Better cost/quality trade-off than static rules. Adds calibration as an ongoing operational concern.

**Related.** Capability Escalator (6.1), Self-Consistency (3.5), Deterministic Verifier (3.1), Distillation Loop (2.3), Evaluation Harness (Part IX).

#### Pattern 6.5: Graceful Degradation

**Intent.** When a tier fails, exceeds budget, or times out, fall back to a lower tier with a defined behavior — never to an unhandled exception.

**Motivation.** Model providers fail. Budgets exhaust. Latency tails happen. An AI-integrated system MUST remain responsive when its preferred tier is unavailable. The fallback contract is part of the architecture, not an afterthought.

**Applicability.** All production AI workflows.

**Structure.** Each handler declares a fallback — next lower tier, cached result, deterministic response, or a "safely declined" response. On budget exhaustion, provider error, or timeout, the orchestrator invokes the fallback. The fallback is part of the contract and is independently tested. In .NET, the natural realization combines Polly resilience policies with an explicit fallback chain.

```csharp
// Pattern: Graceful Degradation (6.5)
public sealed class DegradingHandler(
    IRequestHandler primary, IRequestHandler fallback,
    ResiliencePipeline pipeline) : IRequestHandler {

    public async Task<HandlerOutcome> HandleAsync(
        Request request, BudgetContext budget, CancellationToken ct) {
        try {
            return await pipeline.ExecuteAsync(
                async token => await primary.HandleAsync(request, budget, token),
                ct);
        }
        catch (BudgetExhaustedException) {
            return await fallback.HandleAsync(request, budget, ct);
        }
        catch (BrokenCircuitException) {
            return await fallback.HandleAsync(request, budget, ct);
        }
        catch (TimeoutRejectedException) { // Polly v8 timeout strategy surfaces THIS, not OCE
            return await fallback.HandleAsync(request, budget, ct);
        }
        catch (OperationCanceledException) when (!ct.IsCancellationRequested) {
            return await fallback.HandleAsync(request, budget, ct);
        }
    }
}
```

The Polly pipeline supplies retry, timeout, and circuit-breaker; the explicit `catch` blocks supply the fall-to-floor on the failures the pipeline surfaces as exceptions. Be precise about which strategy raises which type — a v8 timeout raises `TimeoutRejectedException`; catching only `OperationCanceledException` silently misses the timeout case.

**⚠ Anti-pattern: Unhandled Provider Errors.**

```csharp
// ⚠ Wrong: provider hiccups → 500 to the user, no fallback, no telemetry.
return await llm.CompleteAsync(prompt); // production-incident generator
```

**Consequences.** Better availability; defined behavior under stress. Adds the burden of designing meaningful fallbacks per workflow.

**Related.** Capability Escalator (6.1), Token Budget Throttle (2.4), Audit Trail (6.3), Provider Portability (6.6).

#### Pattern 6.6: Provider Portability

**Intent.** Abstract over model providers so workflows can route across vendors based on availability, cost, capability, or geography.

**Motivation.** A production system that depends on a single provider inherits that provider's outages, rate limits, geographic constraints, and pricing changes. Multi-provider abstraction enables failover, cost arbitrage, geo-routing, and capability-matrix routing. The trade-off is the lowest-common-denominator problem: features only one provider supports are hard to use portably.

**Applicability.** Production systems with availability requirements above one provider's published SLA; cost-sensitive deployments at scale; geographic compliance constraints (data residency).

**Structure.** Define a provider-agnostic interface for the operations the application actually uses. Implement adapters per provider. A routing layer selects the provider per request based on capability matrix, cost, latency, and current health. Capability matrix entries are versioned; the adapter declares its supported features so the router can refuse requests that need unsupported capabilities.

```csharp
// Pattern: Provider Portability (6.6)
public interface IModelProvider {
    string ProviderId { get; }
    ProviderCapabilities Capabilities { get; }
    Task<ModelResponse> CompleteAsync(
        ModelRequest request, BudgetContext budget, CancellationToken ct);
}

public sealed record ProviderCapabilities(
    bool SupportsStreaming, bool SupportsToolCalling, bool SupportsExtendedThinking,
    bool SupportsPrefixCache, IReadOnlySet<string> SupportedModels,
    IReadOnlySet<string> AllowedRegions);

public sealed class PortableRouter(
    IReadOnlyList<IModelProvider> providers,
    IProviderHealthMonitor health) {

    public async Task<ModelResponse> RouteAsync(
        ModelRequest request, BudgetContext budget, CancellationToken ct) {
        var eligible = providers
            .Where(p => p.Capabilities.Satisfies(request.RequiredCapabilities))
            .Where(p => health.IsHealthy(p.ProviderId))
            .OrderBy(p => health.EstimatedCost(p.ProviderId, request));
        foreach (var provider in eligible) {
            try { return await provider.CompleteAsync(request, budget, ct); }
            catch (TransientProviderException) { health.MarkUnhealthy(provider.ProviderId); }
        }
        throw new NoProviderAvailableException(request.RequiredCapabilities);
    }
}
```

**⚠ Anti-pattern: Provider-Specific Calls Leaking Through Abstractions.** If the router has special-cases for one provider's parameters, the abstraction has failed. Move the special case into the adapter or accept that the feature is non-portable.

**Consequences.** Higher availability; cost optimization. Constrained feature set unless features are explicitly marked non-portable. Adds capability-matrix maintenance as an operational concern.

**Related.** Capability Router (1.1), Graceful Degradation (6.5), Token Budget Throttle (2.4).

---
