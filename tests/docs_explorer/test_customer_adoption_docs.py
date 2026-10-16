"""Regression controls for copyable, reader-first adoption guidance."""
from pathlib import Path
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = 'https://raw.githubusercontent.com/timianmalloo/ai-forward/main/bootstrap.py'

class CustomerAdoptionDocsTests(unittest.TestCase):
    def test_original_product_presentation_remains_alongside_short_path(self):
        # Protect the product's story and detailed reference, not a particular
        # arrangement of the new onboarding sections. Counts can grow.
        anchors = {
            'README.md': (
                "The development home of the **AI-Forward Pack** — a repository-droppable extension that turns",
                "Dogfooding: the pack is built using the pack.",
                '## Layout', '## Expanding the pack (the sandbox loop)',
                '## Documentation', '**The portal is a lens, not a copy.**',
                '**Keep-current directive (how the portal never rots).**'),
            'pack/README.md': (
                '## Why this pack exists', '## The dual-mode model in one breath',
                '## The Rigor Protocol in one line', '## The workflow skills',
                '## The persona roster (twenty-three lenses)',
                '## How it fits the Agent Knowledge Pack',
                'This pack is an **extension, not a replacement**.'),
            'pack/OVERVIEW.md': (
                'The practical orientation to the bundle:', '**The reasoning spine.**',
                '**UI Archetype Grammar**', '**Specification Standards**',
                '**Knowledge Visualization & Docs Explorer Standard**',
                '**The system tests itself.**', '**The natural flow**',
                '**A worked example — a new feature in an unfamiliar domain.**'),
            'web/handbook/guides/get-started.md': (
                '## Choose where you are starting', '## If the repository already has a history',
                '## Your first exercise',
                '/specify Add CSV export for the active project and filter in HarborTasks.'),
            'web/handbook/guides/workflow.md': (
                '## Choose the next workflow', '## What compilation adds',
                '## Planning and compilation are different decisions',
                '## A worked path through HarborTasks',
                'An overall framing prompt can be compiled before planning.')}
        for name, phrases in anchors.items():
            text = (ROOT / name).read_text(encoding='utf-8')
            for phrase in phrases:
                with self.subTest(source=name, original=phrase):
                    self.assertIn(phrase, text,
                                  'Add the short path without replacing the original product story or stage-by-stage guidance')

    def test_original_explanations_are_complete_not_just_retained_headings(self):
        # Complete upstream blocks at ccc5160603448981d6c879a8735b79129500eb64.
        # Only the directly affected 29 -> 30 skill count is normalized. New
        # sections sit outside these product/reference blocks.
        blocks = (
            ('README.md', 'The development home', 'For the pack', None,
             '5048b1c7c8fa544599734f266b21e54ba2877875436fd796bfc6c9d5cd03ec73'),
            ('README.md', '## Documentation', '## License', '### Test unmerged changes',
             '3a3059b32267ee1a65d81f9bc455f9b6ec9f50c3e7c64baa8fbef720c1308078'),
            ('pack/README.md', '## Why this pack exists', '## The workflow skills', '## Start here',
             'f8aef26b73daedb71704dea59735bd7ab21d18442880a55f16c3f3e4315f4bbd'),
            ('pack/OVERVIEW.md', '## 2. What it contains', '## 3. How to use the skills', None,
             'abcb6c4a3dec90e30b86a0766a3eb12af2c43ef71e26beb0b61b1b0054548a05'),
            ('web/handbook/guides/workflow.md', '## Planning and compilation are different decisions',
             '## Make a handback useful', None,
             '3ab1fa14b0c7e2cc6c2dee51a6913d73787d8f2e3574cb1c701bea6b6f6d2c9e'))
        for name, start, end, inserted_section, expected in blocks:
            with self.subTest(source=name, original=start):
                text = (ROOT / name).read_text(encoding='utf-8')
                self.assertIn(start, text)
                self.assertIn(end, text)
                body = text.split(start, 1)[1].split(end, 1)[0]
                if inserted_section is not None:
                    body = body.split(inserted_section, 1)[0]
                body = body.replace('twenty-nine skills', 'thirty skills').replace('29 skills', '30 skills')
                self.assertEqual(hashlib.sha256(body.encode('utf-8')).hexdigest(), expected,
                                 'Keep the full explanation; retaining only its heading is not preservation')

    def test_install_keeps_applier_and_host_mechanics_without_demoting_workflows(self):
        text = (ROOT / 'pack/adapters/INSTALL.md').read_text(encoding='utf-8')
        for phrase in ('class BOOT-A', 'repo-local deviations three-way merged',
                       'parity controls rewritten into shims',
                       '### 1.3 Why the personas and directives are fit for every host',
                       'The execution difference lives in the prompt layer',
                       'distinct labeled **inline turn**', 'invoke_subagent'):
            with self.subTest(original=phrase):
                self.assertIn(phrase, text)
        block = (ROOT / 'pack/adapters/managed-blocks/AGENTS.block.md').read_text(encoding='utf-8')
        self.assertIn('the prompts in `.github/prompts/`', block)
        self.assertNotIn('Expert reasoning workflows', block)
        self.assertIn('deliver', block)

    def test_upstream_quickstarts_use_main_without_source_overrides(self):
        for name in ('README.md','web/handbook/guides/get-started.md','pack/README.md','pack/OVERVIEW.md'):
            with self.subTest(source=name):
                text=(ROOT/name).read_text(encoding='utf-8')
                commands=re.findall(r'^uv run --no-config --no-project --script ([^\n]+)$',text,re.M)
                self.assertTrue(commands,'The reader needs a copyable setup command')
                self.assertEqual(commands[0], UPSTREAM,
                                 'Normal onboarding must use upstream/main defaults, not a contributor fork or mandatory overrides')
                self.assertNotIn('raw.githubusercontent.com/ahutanu/', text,
                                 'Contributor-specific installer URLs belong in historical proof, not customer onboarding')

    def test_refresh_history_has_no_abbreviated_recorded_entries(self):
        for name in ('pack/adapters/INSTALL.md', 'docs/ai-forward-pack/INSTALL.md'):
            with self.subTest(source=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                histories = re.findall(r'```yaml\nchanges:\n(.*?)\n```', text, re.S)
                self.assertTrue(histories, 'Prior refresh deltas must remain available')
                for history in histories:
                    self.assertIsNone(re.search(r'(?m)^  - \{ type:.*\[truncated\]\s*$', history),
                                      'A tool display excerpt is not complete historical source')
                    entries = [line for line in history.splitlines()
                               if line.strip() and not line.lstrip().startswith('#')]
                    self.assertTrue(entries, 'Do not erase the prior recorded deltas')
                    self.assertTrue(all(line.startswith('  - {') and line.rstrip().endswith('}')
                                        for line in entries),
                                    'Account for every complete refresh record, regardless of key order')

    def test_pack_readme_does_not_send_newcomers_to_a_nonexistent_manual_only_model(self):
        text=(ROOT/'pack/README.md').read_text(encoding='utf-8')
        self.assertNotIn('The pack ships no installer',text)
        self.assertIn('uv run --no-config --no-project --script',text)
        self.assertIn('Use the /deliver skill',text)

    def test_documented_progress_helper_ignores_broken_project_uv_configuration(self):
        text=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
        example=re.search(r'`(uv run [^`]+--help)`',text)
        self.assertIsNotNone(example,'The advanced helper example must be copyable')
        assert example is not None
        command=shlex.split(example.group(1))
        if not shutil.which('uv'):
            self.skipTest('uv is required to exercise the documented helper invocation')
        command[command.index('--python')+1]=sys.executable
        with tempfile.TemporaryDirectory(prefix='documented helper ') as folder:
            project=Path(folder)
            (project/'uv.toml').write_text('this is not valid = toml [\n',encoding='utf-8',newline='\n')
            installed=project/'docs/ai-forward-pack/scripts/delivery.py'
            installed.parent.mkdir(parents=True)
            installed.write_bytes((ROOT/'pack/scripts/delivery.py').read_bytes())
            result=subprocess.run(command,cwd=project,capture_output=True,text=True,encoding='utf-8',
                                  env={**os.environ,'UV_OFFLINE':'1','UV_PYTHON_DOWNLOADS':'never'},timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('resume',result.stdout)

    def test_quickstart_gives_finite_failure_pause_and_handback_examples(self):
        text=(ROOT/'web/handbook/guides/get-started.md').read_text(encoding='utf-8')
        for phrase in ('If setup fails', 'Command not found', 'Source unavailable',
                       'Authentication failed', 'Project checks unavailable',
                       'Approve', 'Change', 'Decline', 'Stop this task',
                       'Completed', 'Remaining', 'Best next action'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertRegex(text, r'Task id: `[^`]+`')
        self.assertIn('A blocked check is not a passed check', text)
        self.assertIn('If the checkpoint is missing or damaged', text)
        self.assertIn('enclosing Git root', text)
        self.assertIn('inspect the project diff', text)

if __name__=='__main__':
    unittest.main()
