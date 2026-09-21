# Launch and monitor installed harnesses

Use this opt-in mode when the human asks for a multi-harness session. It supplies the
routine setup and bounded process monitoring beneath the existing coordination workflow.
The designated Owner can be Claude or Codex; a new Grok or Agy session can invoke these
same scripts. A worker's harness never determines who leads.

This first release is a **POSIX pilot**. Windows, arbitrary attachment to an already-open
terminal, dynamic mailbox prompting, automatic retry and interactive permission approval
are unsupported. The existing `--agents` and `--brief` modes retain their meaning.

## Owner workflow

1. Complete grounding and the plan/capability checks in the parent skill. Read `coord doctor`
   and the actual worktree inventory. If the designated Owner is absent, designate the
   authorized session through `coord leader pin`; if another live Owner exists, respect it.
   The runner never elects or steals leadership.
2. Compile each track's complete delegation contract, including its goal, done-when, owned
   paths, bounds, return evidence, excluded work and decision fallback. Finish the compilation
   and retain its **compilation audit ID**, not a shell command copied from its rendition.
   The runner verifies the compiled document and renders its sections into a worker prompt;
   native launch wrappers are not sent inside ACP. It supplies the assigned session's audit
   start and cwd constraint. Only finished, dispatchable compilations are admitted.
3. Write the concrete JSON launch contract below. Select installed adapter executables and
   documented native policy arguments. Never silently download an adapter, turn off trust
   controls or add blanket approval flags. Bound all effective instructions, hook files,
   policy/trust configuration and adapter lockfiles in `binding_files`.
4. Prepare once. This creates fresh worktrees from the **invoking checkout's HEAD**, reads
   back their actual paths and retains exact prompts as private manual briefs:

   ```sh
   python3 docs/ai-forward-pack/scripts/coord-runner.py prepare --contract launch.json
   python3 docs/ai-forward-pack/scripts/coord-runner.py fingerprint --run example-run
   ```

5. Qualify each actual worktree/configuration using measured observations. `fingerprint`
   computes a binding; **it does not perform qualification**. Record effective permission
   behavior and repository trust explicitly. For example, an adapter mode named `read-only`
   is not evidence that workspace writes are denied. A loaded hook is not proof it fired.
   Unknown or unsupported required capabilities mean use the retained brief or serial work.
   The qualification file is an Owner attestation, not runner-enforced native policy.
6. Run in the foreground and read the structured events. `status` is read-only recovery:

   ```sh
   python3 docs/ai-forward-pack/scripts/coord-runner.py run --run example-run --qualification qualification.json
   python3 docs/ai-forward-pack/scripts/coord-runner.py status --run example-run
   ```

7. Respond to decision requests through the existing request/ruling workflow. The runner
   admits only the finite prompt list in the contract; a later ruling requiring another
   prompt needs an explicit new attempt or the manual workflow. Never replay an interrupted
   run automatically. Each new attempt needs a new run id, worker identities and branches.
8. Read returned artifacts and review their semantics. `ready_for_review` means declared
   structural evidence was inspected, not that the work was accepted. Use the existing
   verification and `conductor-join.py` path to integrate. No automatic merge or push occurs.

## Contract

The JSON below is a shape example. Replace IDs, executable path, observed configuration
files, compilation IDs and artifact paths with actual values. `AGENT_SESSION` must equal
the declared Owner. Every worker gets explicit `AGENT_SESSION`, `AGENT_HOST`, `AGENT_WI`
and cwd, overriding the initiating harness's identity.

```json
{
  "schema": "coord-run/1",
  "run_id": "example-run",
  "owner": "owner-session",
  "parallelism": 2,
  "workers": [{
    "session": "worker-grok-1",
    "branch": "feature-track-one",
    "harness": "grok",
    "transport": "acp",
    "argv": ["grok", "agent", "--no-leader", "stdio"],
    "prompts": ["compilation-audit-id"],
    "deadline_seconds": 600,
    "output_limit": 4194304,
    "fallback": "Continue from the retained brief after Owner review",
    "required_capabilities": {
      "worktree_isolation": "observed-only",
      "instructions": "observed-only",
      "hooks": "observed-only",
      "permissions": "observed-only"
    },
    "binding_files": ["AGENTS.md", ".grok/settings.json"],
    "evidence": [{"kind": "file", "path": "docs/notes/track-result.md", "max_bytes": 65536}]
  }]
}
```

The example's configuration list is not a complete profile: inspect the actual harness's
effective files. Relative configuration paths resolve in the assigned worker checkout;
absolute configuration paths may name user-level settings. Their hashes, the executable
bytes, resolved cwd/base, argument list, admitted prompts and effective environment digest
bind the observation. Environment values are never printed. A changed binding requires a
fresh observation. The runner checks again immediately before a queued worker launches.

Codex ACP workers that must send coordination requests/mail can explicitly add
`"additional_roots": ["/canonical/primary/.agents/requests.jsonl",
"/canonical/primary/.agents/log/worker-id.jsonl",
"/canonical/primary/.agents/mail/owner-id.jsonl"]`. Select only needed files. This optional
list allows at most those three paths for the declared worker/Owner; directories, aliases,
symlinks, duplicate paths and other harnesses refuse. Existing request and Owner inbox
files must come from legitimate store operations before preparation. Only the new worker
log may be absent: its parent must exist, and normal worktree registration creates it.
The runner never creates a store file to widen access. It binds file device/inode identity,
so appends remain valid while replacement requires a new attempt. Identity is rechecked
at launch and before every prompt. Omission grants nothing. Bind instruction/configuration
contents separately in `binding_files`; never add the whole `.agents` directory.

The installed Codex adapter must identify itself as `@agentclientprotocol/codex-acp` and
advertise `sessionCapabilities.additionalDirectories`; otherwise creation blocks. This
option forwards the explicit files through ACP `session/new.additionalDirectories` into
the adapter's per-turn workspace sandbox. Native hooks and permission refusals still apply.
The measured native file sandbox and session-creation spike support this contract; each
real worker still needs its own qualification, including actual decision/mail side effects.

Bounds: 1–8 workers; width 1–4; 1–8 prompts each; 1–3600 seconds for a whole session;
1024–16777216 combined output bytes; 1–32 evidence items; aggregate admitted contract/brief
data at most 512 KiB. A stopped stdin reader, output flood or unterminated JSON line cannot
wait or allocate indefinitely. POSIX process groups contain cooperative descendants; this
is not a sandbox against a malicious executable escaping its group. Owned processes are
terminated after completion, cancellation or failure; edits are not rolled back.

For Claude or Codex select the explicitly installed ACP adapter executable. Record its
version and bind the adapter lock/configuration as well as the underlying runtime. For
Agy select `"transport":"agy"` and supply its native arguments:

```json
["agy", "--add-dir", "{worktree}", "--mode", "accept-edits", "--input-format", "stream-json", "--output-format", "stream-json"]
```

Select this file-edit profile explicitly and qualify it in the actual checkout. `plan`
is a planning profile; it did not permit the ordinary write required by the local worker
probe. The observed `accept-edits` invocation permitted that write while the native
ownership hook refused a leased replacement. Agy still reported `request-review` in
its init envelope, so neither mode label establishes effective policy. Agy cancellation terminates its owned process;
no graceful per-turn cancellation contract is claimed. ACP exposes no editor filesystem
or terminal services. Permission callbacks are denied immediately with a stable action id
and retained fallback; denial stops subsequent prompts. A different policy needs explicit
Owner selection and a new qualified attempt, never an automatic retry.

ACP extension notifications (underscore-prefixed methods without a request id) are consumed
under the same byte and time bounds; unknown requests still receive method-not-found.
Native Agy `denied_actions` and the observed native permission-error step block the attempt,
even inside a `SUCCESS` envelope. Other native error steps fail. No later prompt is sent.
The result records `extension_notifications` and `native_denials` separately from ACP
`permission_requests`; these counts describe observed traffic, not enforcement qualification.
An Agy pre-tool hook refusal can instead appear as `native_tool_error`; correlate the
native error with the ownership decision record and unchanged held bytes. That failed
attempt is never a completed handback.

Grok can emit session updates before its `session/new` reply. The transport retains one
candidate identity and a bounded count; the reply must confirm it before prompts or
permissions gain session authority. A narrowly selected Grok 1.0.34 compatibility path
accepts only its recorded `skills-reload` response during an established prompt. Its
`compatibility_responses` counter is separate from turn completion. Other unexpected
responses still fail. The reported version includes its metadata provenance.

## Qualification and results

Before preparing Claude/Codex worker bases, emit and review the native ownership entry:

```sh
python3 docs/ai-forward-pack/scripts/coord-core.py hook --config --host claude
python3 docs/ai-forward-pack/scripts/coord-core.py hook --config --host codex
python3 docs/ai-forward-pack/scripts/coord-core.py hook --config --host grok
python3 docs/ai-forward-pack/scripts/coord-core.py hook --config --host agy
```

Merge the relevant entry into project `.claude/settings.json` or `.codex/hooks.json`,
preserving other hooks. These commands only print JSON. Bind that file and the deployed
`coord-core.py` bytes. The hook checks native file tools against existing leases; it does
not contain arbitrary shell writes. `AGENT_SESSION` must reach the native hook process.
Opt-in hook decision facts record that environment identity, `hook_host`, and actual
`hook_cwd`; they never record patch contents. Check those receipts with unchanged leased
file bytes, and separately prove an unleased edit succeeds. Codex indeterminate checks
return a supported denial; legacy Claude indeterminate checks request review.
For Grok keep project ownership in `.grok/hooks/coord-ownership.json`, separate from the
pack-managed hook file. For Agy merge the named `ownership-guard` bundle into
`.agents/hooks.json`; sync and the installer refresh source-owned bundle names while
preserving project-owned names. Fresh installs do not silently opt into these guards.
Malformed existing bundle JSON is a conflict, never an empty configuration to overwrite.
Agy successful ownership checks emit no permission grant; ordinary permission policy
still decides whether the tool may run.

Codex requires native review of each exact non-managed hook definition. Inspect `hooks/list`
at the assigned cwd: the expected synchronous PreToolUse source/matcher/hash must be present,
enabled and trusted with no inventory errors. Missing, untrusted, modified, disabled or
unknown state blocks qualification. Review the concrete entry through native `/hooks`;
never bypass hook trust or write its trust database. Project trust and hook-definition
trust are separate. The installed Codex ACP adapter can set session project trust itself,
so unchanged configuration files do not prove the effective trust policy was preserved.
Record both states and actual native tool behavior before attesting enforcement.
Bind the inventory's actual `sourcePath`, not merely a same-named file in the worker.
In the CLI 0.155.1 linked-worktree probe, Codex discovered project hooks from the primary
checkout only after that checkout contained the entry. The worker's copied JSON alone
did not establish discovery. Inspect and bind that primary source plus the worker's
deployed guard bytes; a new or changed definition still requires native trust review.
The Codex Stop definition is separate from the `apply_patch` ownership definition and
needs its own exact native review. Record native Stop behavior for every harness:
the script's refusal receipt proves what it requested, not that the harness honored it.
Loop guards deliberately bound repeated native Stop feedback.

```json
{
  "schema": "coord-qualification/1",
  "workers": {
    "worker-grok-1": {
      "fingerprint": "replace-with-current-measured-binding",
      "version": "replace-with-observed-adapter-and-runtime-version",
      "evidence": "reference to the actual probes and their results",
      "effective_policy": "describe observed allowed and denied operations",
      "trust": "describe the observed trust state for this actual checkout",
      "capabilities": {
        "worktree_isolation": "observed-only",
        "instructions": "observed-only",
        "hooks": "observed-only",
        "permissions": "observed-only"
      }
    }
  }
}
```

Never copy this example as a passing observation. Use `enforced` only for a boundary whose
mechanism and negative proof establish it. Missing/unsupported requirements block launch;
there is no silent downgrade. Full pack hook enforcement remains a separate qualification.

Output states distinguish preparation, partial preparation, running/interrupted, blocked,
failed, incomplete evidence and ready for review. A successful ACP `end_turn` or matching
Agy `SUCCESS` is transport completion only. Every admitted turn must succeed. A pre-existing
artifact cannot turn cancellation, truncation, denial or unknown terminal output into success.
After inspecting receipts the runner reads a bounded, strict Owner-decision projection.
Open requests yield `RUN-DECISION-OPEN`; unreadable or malformed state yields
`RUN-DECISION-NOT-CHECKED`. It then rechecks the current Owner epoch before readiness.
Native Stop limits never override this final fence. A real Owner ruling closes the
request; a subsequent run requires a fresh explicit attempt, not replay of a started run.
The file verifier rejects symlinks and records exact inspected bytes/hash. The commit verifier
requires a new descendant of the admitted base. Neither executes a worker-supplied command.

Private manifests/briefs live in the common git directory; operational facts use the existing
coordination ledger. Status, bytes and durations come from those facts; tokens/spend remain
`not recorded`. No raw conversations, permission arguments or environment values enter the
durable events. Missing terminal evidence means `interrupted_or_running`, never success.
