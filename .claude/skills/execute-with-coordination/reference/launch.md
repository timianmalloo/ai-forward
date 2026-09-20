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
["agy", "--add-dir", "{worktree}", "--mode", "plan", "--input-format", "stream-json", "--output-format", "stream-json"]
```

`plan` alone is not a permission guarantee. Agy cancellation terminates its owned process;
no graceful per-turn cancellation contract is claimed. ACP exposes no editor filesystem
or terminal services. Permission callbacks are denied immediately with a stable action id
and retained fallback; denial stops subsequent prompts. A different policy needs explicit
Owner selection and a new qualified attempt, never an automatic retry.

## Qualification and results

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
The file verifier rejects symlinks and records exact inspected bytes/hash. The commit verifier
requires a new descendant of the admitted base. Neither executes a worker-supplied command.

Private manifests/briefs live in the common git directory; operational facts use the existing
coordination ledger. Status, bytes and durations come from those facts; tokens/spend remain
`not recorded`. No raw conversations, permission arguments or environment values enter the
durable events. Missing terminal evidence means `interrupted_or_running`, never success.
