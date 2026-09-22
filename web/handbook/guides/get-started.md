# Try AI-Forward on one small task

Start with a repository you understand and a change you can review. The first useful
result is not a large plan or a swarm of agents. It is seeing whether the pack helps
you frame a small request, inspect the output, and keep a reliable next step.

You need Git, a working Python 3 interpreter, a supported coding-agent application,
and permission to change the target repository. Some maintenance operations use
PowerShell. The agent application still needs its own account, model access and
tool permissions; installing AI-Forward does not supply or bypass those.

## Choose where you are starting

**You are working inside the AI-Forward repository.** The pack is already installed
there. This is useful for learning or contributing to the pack, but it is not the
same as adopting it into your application.

**You want the pack in another local repository.** Open the AI-Forward clone in your
harness and use [add the pack to a repository](#skill-addpacktorepo), giving the
target path. The workflow inspects the target and applies the deployment map rather
than asking you to copy a random collection of files.

```text
/addpacktorepo C:\projects\harbor-tasks
```

That is a Windows example path: replace it with your own. In Codex, select
`$addpacktorepo` and provide the same target path. In a macOS/Linux environment the
target will have that platform's path form.

**The target already has AI-Forward.** Work from that target and use
[update the installed pack](#skill-updatepack), with the local pack source available.
Inspect the proposed reconciliation, especially any project-specific deviations.
Do not overwrite local policies merely to make the install look uniform.

## Understand what installation gives you

For a first adoption into an existing application, the short path is:

1. From the AI-Forward clone, use `/addpacktorepo` with the application's path.
2. Open the application repository and use `/adopt` to orient its existing code and
   documentation. Review the resulting map and gaps.
3. Choose one small task. For a new feature like the export example below, use
   `/specify`; for broken behavior, use `/investigate` instead.

In Codex, use the corresponding `$skill` invocation. This is a first-adoption recipe,
not a requirement to reinstall or repeat adoption every time you work.

The pack supplies project instructions, skills, specialist personas, knowledge
standards, templates and scripts. Different harnesses discover different installation
surfaces. For example, Codex discovers skills through `.agents/skills`, while Grok
has a `.grok` surface. [Harness setup](#harnesses) explains these differences.

These files guide and support work. Their presence does not establish that the
running harness loaded them or honored a hook. In a fresh session, ask the agent
to identify the installed skill it would use and summarize the relevant instructions.
If it cannot, correct discovery before depending on the workflow.

Run the installed doctor from the target repository root:

```powershell
python docs\ai-forward-pack\scripts\pack-doctor.py
```

On macOS/Linux, use:

```sh
python3 docs/ai-forward-pack/scripts/pack-doctor.py
```

Read the findings. A file-level readiness check is not a live permission or
enforcement test. Do not respond to a warning by enabling broad permissions.
Use the specific setup guidance for the affected harness.

## If the repository already has a history

Use [adopt an existing project](#skill-adopt) to inventory the code and documentation,
recover an initial architectural picture and identify gaps. Adoption should bring
useful existing knowledge into the working model, not replace it with generic prose.

If your main question is whether the existing system is sound, use
[a forensic review](#skill-forensicreview) instead of treating onboarding as an
architecture audit. Those are different jobs.

For a new project, begin by understanding the problem. You may need research or a
specification before there is code to inventory. The pack does not require a fictional
architecture document merely to make every folder nonempty.

## Your first exercise

HarborTasks is our illustrative task-tracking service. Imagine it already has a
project-scoped task list and a filter. The page displays 20 rows, but 63 tasks match.
Ask for a specification, not an implementation:

```text
/specify Add CSV export for the active project and filter in HarborTasks.
Export all matching tasks, not just the visible page. Keep this first slice small.
Tell me which choices about columns, access and empty results I need to make.
```

Use `$specify` for Codex. The other documented slash-command harnesses use the
slash form; confirm discovery in your running application.

An illustrative useful handback would state:

- the person using export and the outcome they need;
- the distinction between 20 visible rows and all 63 matches;
- acceptance criteria you can check;
- unresolved choices such as columns and download behavior;
- explicit exclusions, such as scheduling exports or introducing a new reporting service.

Review those choices. An agent that immediately builds a reporting platform has not
understood the intended first slice.

## Decide whether to continue

You are ready for the next step when you can explain the intended result and how you
would recognize an incorrect one. Then choose a design or implementation workflow
appropriate to the risk. [From request to reviewed change](#workflow) gives that
decision path.

Keep the first session focused. Inspect changed files before committing, and do not
equate an agent's final message with acceptance. If it is writing code, ask for the
checks that exercise the actual path a user will use.

## Common first-run problems

- **The skill is absent.** Confirm the installation location and harness-specific
  discovery rules, then refresh the session. A workflow mentioned in prose is not
  necessarily registered in the host's menu.
- **A Python command fails on Windows.** Use `python` or `py -3`, not a Microsoft
  Store `python3` alias. Let the doctor name the working interpreter.
- **Existing instructions disagree.** Resolve the project-specific conflict rather
  than installing a second competing policy.
- **The task becomes too ceremonial.** State a smaller outcome and exclusions.
  Reducing unnecessary artifacts must not remove a safety check the change needs.

**Next:** [choose the right working path](#workflow), or [look up a skill by need](#skills).
