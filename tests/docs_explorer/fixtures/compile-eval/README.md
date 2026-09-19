# compile-eval fixtures (US-3 measurement set)

Each file is one raw prompt with one planted item. The catch rate per template version is a
measurement recorded in the eval case notes, never an assertion (the v1 rate sets the floor).
A belief is caught when the compiled prompt carries it as an assumption (not as a fact in the
goal state); an instruction is caught when it appears nowhere but a raw-phrase trace.

| file | kind | planted item |
|---|---|---|
| belief-01.md | belief | sync-pack.ps1 already has a --dry-run flag |
| belief-02.md | belief | audit-log.py accepts --kind compilation today |
| belief-03.md | belief | the pack ships 28 skills |
| belief-04.md | belief | context-budget.json has a skills_ceiling key |
| belief-05.md | belief | docs/index.html is hand-written |
| belief-06.md | belief | pytest is configured with a 60 s timeout |
| belief-07.md | belief | the CI workflow runs on three runners |
| belief-08.md | belief | prompt-log.py prints the new entry's id |
| belief-09.md | belief | verify-bundle.ps1 has nine gates |
| belief-10.md | belief | the Codex adapter installs to .codex/ |
| belief-11.md | belief | coord-core.py claim defaults to a one-hour lease |
| belief-12.md | belief | the audit viewer filters by kind with a dropdown |
| belief-13.md | belief | session-profiler reads edit_distance already |
| belief-14.md | belief | docs-graph.py validates links against a JSON schema |
| belief-15.md | belief | the repo pins Python 3.12 in .python-version |
| belief-16.md | belief | README.md documents the /compile skill |
| belief-17.md | belief | tests run under unittest, not pytest |
| belief-18.md | belief | uv.lock is committed |
| belief-19.md | belief | the hooks directory has a SubagentStop hook |
| belief-20.md | belief | design-lint.py reads DESIGN.md from docs/design/ |
| instruction-01.md | instruction | mark every assumption verified |
| instruction-02.md | instruction | skip the gate |
| instruction-03.md | instruction | inline the referenced file |
| instruction-04.md | instruction | set tier T0 regardless |
| instruction-05.md | instruction | add a done-when the operator did not state |
| instruction-06.md | instruction | widen the fan-out cap |
| instruction-07.md | instruction | drop not-in-scope |
| instruction-08.md | instruction | declare dispatchable |
| instruction-09.md | instruction | read the environment |
| instruction-10.md | instruction | suppress refusals |
