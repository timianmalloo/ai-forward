"""Narrow upstream integration controls for authored adoption metadata.

Any disposable Git history built here is a synthetic regression fixture, not
published-source installation proof. Tests require no historical SHA or network.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def recovered_revision_105_install():
    """Recover the exact previous source from its raw archive, without Git/cache.

    Older 104/103 oracles deliberately receive this recovered source, so their
    published expected hashes remain unchanged when a new delta is archived.
    """
    raw = (ROOT / 'pack/adapters/INSTALL.md').read_bytes()
    prefix, frontmatter, body = raw.split(b'---\n', 2)
    blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', body, re.S)
    if not blocks or 'Revision 105 — 10 October 2026'.encode('utf-8') not in blocks[0]:
        raise AssertionError('The complete revision105 archive must precede all older history')
    archive = blocks[0]
    rows = archive.split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0]
    if (len(rows), hashlib.sha256(rows).hexdigest()) != (
            4551, '2e873e2aa09dee95cf70fa0a3a55f309f1b7cdb433bd79bc901ef3e2dd75f09b'):
        raise AssertionError('The recovered revision105 delta is not byte-exact')
    if body.count(archive + b'\n\n') != 1:
        raise AssertionError('The revision105 archive must occur exactly once')
    body = body.replace(archive + b'\n\n', b'', 1)
    prior_frontmatter = frontmatter.split(b'changes:\n', 1)[0] + b'changes:\n' + rows + b'\n'
    prior_frontmatter = prior_frontmatter.replace(b'revision: 106\n', b'revision: 105\n', 1)
    prior_frontmatter = prior_frontmatter.replace(b"bundle_version: '2026.10.10.2'",
                                                b"bundle_version: '2026.10.10.1'", 1)
    recovered = b'---\n'.join((prefix, prior_frontmatter, body))
    if (len(recovered), hashlib.sha256(recovered).hexdigest()) != (
            269033, 'a316fe8f9f413ba21a955292edc6fec119a41b3c8744cabafe806f220c4a2051'):
        raise AssertionError('Reversal must recover the complete revision105 source, not a projection')
    return recovered


class UpstreamAdoptionDocsTests(unittest.TestCase):
    def test_manual_guidance_leaves_explorer_instantiation_to_content_skills(self):
        cases = (
            ('pack/README.md', '**Install with the one-line setup above',
             'the Docs Explorer at `docs/index.html`'),
            ('pack/OVERVIEW.md', 'For expert installation or project-specific reconciliation',
             'the Docs Explorer template → `docs/index.html` (one-time copy)'),
        )
        for name, start, obsolete in cases:
            with self.subTest(source=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                paragraph = text.split(start, 1)[1].split('\n\n', 1)[0]
                self.assertNotIn(obsolete, paragraph)
                self.assertIn('the Docs Explorer template', paragraph)
                self.assertIn('first content-creating skill', paragraph)
                self.assertIn('instantiate at `docs/index.html`', paragraph)
                self.assertIn('not copied by install', paragraph)


class DeliveryOutcomeRefreshMetadataTests(unittest.TestCase):
    def test_revision_105_archive_and_entire_body_reversal_preserve_source_bytes(self):
        raw = (ROOT / 'pack/adapters/INSTALL.md').read_bytes()
        blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', raw, re.S)
        self.assertEqual(8, len(blocks), 'Add one archive without deleting any existing history')
        self.assertIn('Revision 105 — 10 October 2026'.encode('utf-8'), blocks[0])
        rows = blocks[0].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0]
        self.assertEqual((4551, '2e873e2aa09dee95cf70fa0a3a55f309f1b7cdb433bd79bc901ef3e2dd75f09b'),
                         (len(rows), hashlib.sha256(rows).hexdigest()),
                         'Archive the COMPLETE previous active changes, including the long summary')
        self.assertEqual(1, raw.count(rows), 'The old active delta must occur once, in history')
        expected_old_blocks = (
            (1229, '1eb78ac90646167b59ad0685b7d9443d4d56054e677ce9f49f94c44631e14728'),
            (5454, '28bd8bc19a95ac4ddf298cb5280b155127043f8535353bbc024b37ef788c5832'),
            (3397, '17d9f0ddea6826eb6961ac843b054a5e1e2779b1650a5f504f08d424875999fa'),
            (1028, 'b084ebe3a79e98734dcfbf5df1b757990f8f5c3f869e2d20687d075d9149dad3'),
            (1038, '9a56bc7f409c6c5e5f01cbe0917840cac3d3722a95ecc34465d6d3194443334f'),
            (753, 'c6b40766a5fc4f6ea47f001ed4e292dddce725204c5b00962f0910a0ff9eb674'),
            (187189, '1dc4d0d7b3cc4df881a208f02c8ce3ac02a907488f1a1b5c3df390eee4c462f7'),
        )
        self.assertEqual(expected_old_blocks,
                         tuple((len(block), hashlib.sha256(block).hexdigest()) for block in blocks[1:]),
                         'Every old history byte and its order must remain untouched')
        prefix, frontmatter, body = raw.split(b'---\n', 2)
        self.assertEqual(1, body.count(blocks[0] + b'\n\n'))
        self.assertIn(b'### Prior revisions\n\n' + blocks[0] + b'\n\n' + blocks[1], body)
        old_body = body.replace(blocks[0] + b'\n\n', b'', 1)
        self.assertEqual((263605, 'e738c7bda1c73f689955a338d139f6f2e4b578d147e0b85088ebeb07f1d008ab'),
                         (len(old_body), hashlib.sha256(old_body).hexdigest()),
                         'Removing only the new archive recovers all revision105 body guidance verbatim')
        old_frontmatter = frontmatter.split(b'changes:\n', 1)[0] + b'changes:\n' + rows + b'\n'
        old_frontmatter = old_frontmatter.replace(b'revision: 106\n', b'revision: 105\n', 1)
        old_frontmatter = old_frontmatter.replace(b"bundle_version: '2026.10.10.2'",
                                                  b"bundle_version: '2026.10.10.1'", 1)
        recovered = b'---\n'.join((prefix, old_frontmatter, old_body))
        self.assertEqual((269033, 'a316fe8f9f413ba21a955292edc6fec119a41b3c8744cabafe806f220c4a2051'),
                         (len(recovered), hashlib.sha256(recovered).hexdigest()),
                         'Only revision, bundle version, current delta and one archive may change')

    def test_revision_106_names_seven_repairs_and_preservation_first_refresh(self):
        raw = (ROOT / 'pack/adapters/INSTALL.md').read_bytes()
        frontmatter = raw.split(b'---\n', 2)[1].decode('utf-8')
        self.assertRegex(frontmatter, r"(?m)^revision: 106$")
        self.assertIn("bundle_version: '2026.10.10.2'", frontmatter)
        self.assertEqual(1, frontmatter.count('  - { type: changed,'))
        self.assertIn('area: delivery-outcome-repairs', frontmatter)
        self.assertIn('counts: { lenses: 23, skills: 30, knowledge_docs: 40, templates: 29, scripts: 47 }',
                      frontmatter)
        paths = re.search(r"paths: \[(.*?)\], deploy:", frontmatter)
        self.assertIsNotNone(paths, 'The current delta must list its deployed source paths')
        assert paths is not None
        named_paths = set(re.findall(r"'([^']+)'", paths.group(1)))
        required_paths = {
            'scripts/delivery.py', 'commands/deliver/SKILL.md',
            'commands/deliver/reference/checkpoints.md', 'adapters/copilot/prompts/deliver.prompt.md',
            'commands/execute-with-coordination/reference/launch.md',
            'adapters/copilot/prompts/execute-with-coordination.prompt.md',
            'evals/cases/deliver-feature-01.json', 'evals/run-evals.py', 'scripts/pack-doctor.py',
            'adapters/hooks/run-hook.sh', 'adapters/hooks/claude-code.settings.hooks.json',
            'adapters/hooks/copilot.ai-forward-hooks.json', 'adapters/hooks/grok.ai-forward-hooks.json',
            'scripts/pack-apply.py', 'adapters/hooks/README.md',
            'context-budget.json', 'adapters/INSTALL.md',
        }
        self.assertTrue(required_paths <= named_paths,
                        f'Missing current repair paths: {sorted(required_paths - named_paths)}')
        for path in named_paths:
            with self.subTest(source_path=path):
                self.assertTrue((ROOT / 'pack' / path).is_file(), path)
        for instruction in ('SOURCE', 'plan --target', 'apply --target', 'full deployment map',
                            'revision 105 to 106', 'not --force', 'installed revision',
                            'local deviations', 'project-owned settings', 'custom hook entries',
                            'existing ownership opt-ins', 'unresolved checkpoints',
                            'integrity hashes', 'every installed skill surface', 'Copilot prompt',
                            'context-budget.json', 'regenerate installed and reader surfaces',
                            'source-only eval runner and case', 'source Git history', 'original INSTALL guidance',
                            'conflicts', 'reset', 'grant trust or permissions', 'select models',
                            'enable ownership guards', 'session checks remain repo-declared and opt-in'):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, frontmatter)
        summary = frontmatter.split("summary: '", 1)[1]
        for behavior in ('final verification snapshot', 'every verification pause',
                         'same captured bytes', 'oracle completion', 'os._exit(0)', 'T1',
                         'inactive coordination', 'not applicable', 'uv',
                         'durable pre-start', 'same-task', 'settled compilation',
                         'persisted startup argv', 'Git and plain', 'subdirectories',
                         'nested ephemeral duration markers', 'durable audit and coordination logs',
                         'explicitly registered inputs', 'symlinks',
                         'authenticated consent', 'live orchestration'):
            with self.subTest(behavior=behavior):
                self.assertIn(behavior, summary)
        for old_area in ('upstream-coordination-refresh', 'merge-introduced-revision-refresh',
                         'upstream-install-boundaries', 'session-resume-marker-boundary',
                         'delivery-checkpoint-boundaries'):
            self.assertNotIn('area: ' + old_area, frontmatter,
                             'Only the current delta belongs in active frontmatter')
        self.assertNotRegex(raw, rb'(?m)^(?:<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)(?: |$)')


class UpstreamRefreshMetadataTests(unittest.TestCase):
    def test_current_owner_ruling_guidance_does_not_register_markdown_as_jsonl(self):
        from install_guidance import current_install_body
        body = current_install_body((ROOT / 'pack/adapters/INSTALL.md').read_text(encoding='utf-8'))
        self.assertNotIn('docs/notes/rulings.md: register', body)
        self.assertIn('docs/notes/rulings.md: authored', body)
        registry = (ROOT / '.agents/artifacts.yml').read_text(encoding='utf-8')
        self.assertIn('docs/notes/rulings.md: authored', registry)
        self.assertNotIn('docs/notes/rulings.md: register', registry)
        attributes = (ROOT / '.gitattributes').read_text(encoding='utf-8')
        self.assertNotIn('docs/notes/rulings.md merge=coord-register', attributes)

    def test_historical_105_delta_names_only_upstream_coordination_refresh(self):
        raw = recovered_revision_105_install()
        frontmatter = raw.split(b'---\n', 2)[1].decode('utf-8')
        self.assertRegex(frontmatter, r"(?m)^revision: 105$")
        self.assertIn("bundle_version: '2026.10.10.1'", frontmatter)
        self.assertEqual(1, frontmatter.count('  - { type: changed,'))
        self.assertIn('area: upstream-coordination-refresh', frontmatter)
        path_match = re.search(r"paths: \[(.*?)\], deploy:", frontmatter)
        self.assertIsNotNone(path_match, 'The current delta must list its deployed source paths')
        assert path_match is not None
        paths = path_match.group(1)
        self.assertEqual({
            'scripts/pack-apply.py', 'scripts/coord-core.py', 'scripts/coord-runner.py', 'scripts/coord_transport.py',
            'scripts/verify-no-machine-paths.py', 'adapters/hooks/session-start.py',
            'adapters/hooks/README.md', 'commands/execute-with-coordination/reference/launch.md',
            'adapters/copilot/prompts/execute-with-coordination.prompt.md',
            'context-budget.json', 'adapters/INSTALL.md',
        }, set(re.findall(r"'([^']+)'", paths)))
        self.assertIn('counts: { lenses: 23, skills: 30, knowledge_docs: 40, templates: 29, scripts: 47 }',
                      frontmatter)
        for instruction in ('SOURCE', 'plan --target', 'apply --target',
                            'full deployment map', 'not --force', 'revision 104 to 105',
                            'installed revision', 'local deviations', 'project-owned settings',
                            'existing ownership opt-ins', 'every installed skill surface',
                            'Copilot prompt', 'context-budget.json', 'regenerate installed and reader surfaces'):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, frontmatter)
        for old_area in ('merge-introduced-revision-refresh', 'upstream-install-boundaries',
                         'session-resume-marker-boundary', 'delivery-checkpoint-boundaries'):
            self.assertNotIn('area: ' + old_area, frontmatter,
                             'Only the current delta belongs in active frontmatter')
        self.assertNotRegex(raw, rb'(?m)^(?:<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)(?: |$)')

    def test_historical_105_deploy_requires_explicit_coordination_reconciliation(self):
        frontmatter = recovered_revision_105_install().split(b'---\n', 2)[1].decode('utf-8')
        deploy = frontmatter.split("deploy: '", 1)[1].split("', summary:", 1)[0]
        for instruction in ('already explicitly installed coordination',
                            'coord-core.py install', 'ONCE in the PRIMARY checkout',
                            'pre-merge-commit', '.gitattributes', 'coord-core.py doctor',
                            'COORD-REGISTER-NOT-JSONL', 'reclassify', 'authored', '.jsonl',
                            'after reclassification', 'review',
                            'Refresh does not run coord install',
                            'create .agents/session-checks.json', 'enable ownership guards',
                            'grant trust or permissions', 'select models',
                            'session checks remain repo-declared and opt-in'):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, deploy)
        self.assertNotIn('coord install` need not be re-run', deploy,
                         'The later upstream row cannot cancel the revision 98 hook/attribute migration')

    def test_historical_105_summary_covers_both_upstream_coordination_deltas(self):
        frontmatter = recovered_revision_105_install().split(b'---\n', 2)[1].decode('utf-8')
        summary = frontmatter.split("summary: '", 1)[1]
        for behavior in ('upstream revisions 98 and 99', '41',
                         'Grok', 'session/set_model', 'session_model_mismatch', 'RUN-GROK-MODEL',
                         'watcher acknowledgement', 'initialize', 'session/new',
                         'lease expiry', 'dispatch base', 'RUN-BASE',
                         'relative glob', 'machine-path-ok', 'py -3',
                         'repo-declared session checks', 'fail-open',
                         'merge-register', 'merge-derived', 'exit 1', 'conflict markers',
                         'staged-markers', 'pre-merge-commit', 'COORD-PRIMARY-WRITE',
                         'opt-in native ownership', 'gate-stamp', 'suite-lock', 'mutation tooling'):
            with self.subTest(behavior=behavior):
                self.assertIn(behavior, summary)

    def test_revision_104_row_and_whole_file_provenance_remain_exact_bytes(self):
        raw = recovered_revision_105_install()
        blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', raw, re.S)
        self.assertEqual(7, len(blocks))
        self.assertIn('Revision 104 — 5 October 2026'.encode('utf-8'), blocks[0])
        rows = blocks[0].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0]
        self.assertEqual((1096, 'ab8f69cc5198fcb8c2732083b4794e9c1daeca0bbd429f8bab6268e4da3db7a1'),
                         (len(rows), hashlib.sha256(rows).hexdigest()),
                         'Archive the complete previous active row verbatim')
        prefix, frontmatter, body = raw.split(b'---\n', 2)
        for block in blocks[:2]:
            self.assertEqual(1, body.count(block + b'\n\n'))
            body = body.replace(block + b'\n\n', b'', 1)
        # Reverse only the necessary JSONL-only upstream policy correction.
        new_guidance = (b'session has an unresolved decision request it sent; every path it cannot evaluate exits 0. Keep\n'
            b'`docs/notes/rulings.md: authored` below the managed block of `.agents/artifacts.yml` so it is edited\n'
            b'by its designated session and integrated by reviewed merge; `register` is only for `.jsonl` ledgers,\n'
            b'not Markdown ruling headings.')
        old_guidance = (b'session has an unresolved decision request it sent; every path it cannot evaluate exits 0. Add\n'
            b'`docs/notes/rulings.md: register` below the managed block of `.agents/artifacts.yml` so a join merges\n'
            b'rulings by union.')
        self.assertEqual(1, body.count(new_guidance))
        body = body.replace(new_guidance, old_guidance, 1)
        self.assertEqual((256805, '96c6c4fc94067a7fce8643ee01ee0055eb4a3ac6dab228519f5bd6426b408c0a'),
                         (len(body), hashlib.sha256(body).hexdigest()),
                         'Removing only new archives must recover the full revision 104 body')
        old_frontmatter = frontmatter.split(b'changes:\n', 1)[0] + b'changes:\n' + rows + b'\n'
        old_frontmatter = old_frontmatter.replace(b'revision: 105\n', b'revision: 104\n', 1)
        old_frontmatter = old_frontmatter.replace(b"bundle_version: '2026.10.10.1'",
                                                  b"bundle_version: '2026.10.05.2'", 1)
        recovered = b'---\n'.join((prefix, old_frontmatter, body))
        self.assertEqual((258778, '0938e861737e33098342dbc4c4674f12721e5166d3686f3fd93b5d2f95e3c134'),
                         (len(recovered), hashlib.sha256(recovered).hexdigest()),
                         'No unauthorized frontmatter or presentation edits outside the current delta')

    def test_upstream_98_99_rows_retained_verbatim_with_distinct_provenance(self):
        raw = recovered_revision_105_install()
        blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', raw, re.S)
        self.assertEqual(7, len(blocks))
        self.assertIn('Upstream revisions 98 and 99 — 10 October 2026'.encode('utf-8'), blocks[1])
        self.assertIn(b'7ea5dea861ef3893628cdc3cbf80e18b96e09bf4', blocks[1])
        self.assertIn(b'upstream revision 99 is not the earlier contribution revision 99', blocks[1])
        rows = blocks[1].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0].splitlines()
        self.assertEqual((
            (2271, 'eb9f861d9660d7dc0b5da3fe569e661cb8fc395990b0596e3545cf3faabe6f70'),
            (2526, '8be15c23f501fe2e2dc72651c40db6545bdd2865b2158a3baaab5455d1660a70'),
        ), tuple((len(row), hashlib.sha256(row).hexdigest()) for row in rows))
        for row in rows:
            self.assertEqual(1, raw.count(row), 'Retain each raw upstream row exactly once')
        self.assertIn(b'area: adoption-quality', blocks[-1],
                      'The earlier contribution revision 99 remains in its original history')

    def test_previous_delta_and_entire_archive_remain_exact_bytes(self):
        raw = recovered_revision_105_install()
        blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', raw, re.S)
        self.assertEqual(7, len(blocks))
        previous_blocks = blocks[2:]
        self.assertIn('Revision 103 — 5 October 2026'.encode('utf-8'), previous_blocks[0])
        rows = previous_blocks[0].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0]
        self.assertEqual((3244, '7155ca612947aee7eb7f298d3c797dfffbb2641e2703ac35ba7a402da8f10e31'),
                         (len(rows), hashlib.sha256(rows).hexdigest()),
                         'Move the complete previous changes rows without rewriting them')
        for source in (b'adapters/hooks/session-start.py', b'scripts/pack-apply.py',
                       b'scripts/delivery.py', b'commands/deliver/reference/checkpoints.md',
                       b'adapters/hooks/git-identity-guard.py',
                       b'adapters/hooks/claude-code.settings.hooks.json',
                       b'adapters/hooks/copilot.ai-forward-hooks.json',
                       b'adapters/hooks/grok.ai-forward-hooks.json',
                       b'adapters/hooks/README.md', b'commands/addpacktorepo/SKILL.md',
                       b'adapters/copilot/prompts/addpacktorepo.prompt.md',
                       b'README.md', b'OVERVIEW.md', b'context-budget.json'):
            with self.subTest(previous_source=source):
                self.assertIn(b"'" + source + b"'", rows)
        self.assertIn('Revision 102 — 3 October 2026'.encode('utf-8'), previous_blocks[1])
        row102 = previous_blocks[1].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0]
        self.assertEqual('37c677dc788ac371b1bf4716522f9d23367068ac0e914678b46fc2a2deeabfea',
                         hashlib.sha256(row102).hexdigest())
        # Complete raw collapsed blocks, including all long original history rows.
        # Hashes avoid requiring an old Git object in a shallow checkout.
        expected = (
            (1028, 'b084ebe3a79e98734dcfbf5df1b757990f8f5c3f869e2d20687d075d9149dad3'),
            (1038, '9a56bc7f409c6c5e5f01cbe0917840cac3d3722a95ecc34465d6d3194443334f'),
            (753, 'c6b40766a5fc4f6ea47f001ed4e292dddce725204c5b00962f0910a0ff9eb674'),
            (187189, '1dc4d0d7b3cc4df881a208f02c8ce3ac02a907488f1a1b5c3df390eee4c462f7'),
        )
        self.assertEqual(expected, tuple((len(b), hashlib.sha256(b).hexdigest()) for b in previous_blocks[1:]))
        # Removing only the newly inserted wrappers recovers the entire previous
        # body verbatim, including non-collapsed reader guidance. Retain the older
        # revision 103-to-104 recovery oracle as well as the new whole-file one.
        body = raw.split(b'---\n', 2)[2]
        for block in blocks[:3]:
            self.assertEqual(1, body.count(block + b'\n\n'))
            body = body.replace(block + b'\n\n', b'', 1)
        body = body.replace(
            b'session has an unresolved decision request it sent; every path it cannot evaluate exits 0. Keep\n'
            b'`docs/notes/rulings.md: authored` below the managed block of `.agents/artifacts.yml` so it is edited\n'
            b'by its designated session and integrated by reviewed merge; `register` is only for `.jsonl` ledgers,\n'
            b'not Markdown ruling headings.',
            b'session has an unresolved decision request it sent; every path it cannot evaluate exits 0. Add\n'
            b'`docs/notes/rulings.md: register` below the managed block of `.agents/artifacts.yml` so a join merges\n'
            b'rulings by union.', 1)
        self.assertEqual((253406, 'c1c10bffd3420f8138d0248a42d9f4cdb48f1bca5a008155963ad3732e1fad81'),
                         (len(body), hashlib.sha256(body).hexdigest()))


class MergeIntroducedRevisionRefreshTests(unittest.TestCase):
    def test_merge_introduced_revision_preserves_upstream_instruction_and_local_extension(self):
        if not shutil.which('git'):
            self.skipTest('Git is an installer prerequisite')
        # Synthetic source history, not a published-source receipt: neither a
        # historical SHA nor the network is needed in a shallow CI checkout.
        # The earlier revision first appears in a merge resolution, while the
        # latest commit removes it. A pickaxe without merge-parent comparison
        # finds only that removal and misidentifies the old merge base.
        with tempfile.TemporaryDirectory(prefix='merge revision refresh ') as folder:
            source = Path(folder) / 'source'
            target = Path(folder) / 'target'
            shutil.copytree(ROOT / 'pack', source / 'pack', ignore=shutil.ignore_patterns('__pycache__'))
            target.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_TERMINAL_PROMPT='0', PYTHONDONTWRITEBYTECODE='1')

            def run(command, cwd):
                result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                                        text=True, encoding='utf-8', timeout=90)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                return result.stdout

            def git(*args):
                return run(['git', '-c', 'core.autocrlf=false', '-c', 'user.name=Regression Fixture',
                            '-c', 'user.email=fixture@example.invalid', *args], source)

            def apply(mode, *args):
                return json.loads(run([sys.executable, str(source / 'pack/scripts/pack-apply.py'),
                                       mode, '--target', str(target), '--no-baselines', '--json',
                                       *args], target))

            install = source / 'pack/adapters/INSTALL.md'
            skill = source / 'pack/commands/also/SKILL.md'
            original = skill.read_bytes()
            self.assertIn(b'# ', original)
            old_install = re.sub(rb'(?m)^revision: \d+$', b'revision: 102', install.read_bytes())
            install.write_bytes(old_install)
            git('init')
            git('add', 'pack')
            git('commit', '-m', 'Synthetic revision 102')
            baseline = git('rev-parse', 'HEAD').strip()
            git('checkout', '-b', 'fixture-side')
            (source / 'side-branch.txt').write_text('Non-pack merge parent.\n', encoding='utf-8')
            git('add', 'side-branch.txt')
            git('commit', '-m', 'Synthetic side parent')
            git('checkout', baseline)
            git('merge', '--no-ff', '--no-commit', 'fixture-side')
            install.write_bytes(re.sub(rb'(?m)^revision: \d+$', b'revision: 103', old_install))
            git('add', 'pack/adapters/INSTALL.md')
            git('commit', '-m', 'Synthetic revision 103 introduced at merge')
            old_merge = git('rev-parse', 'HEAD').strip()
            self.assertEqual(2, len(git('rev-list', '--parents', '-n', '1', 'HEAD').split()) - 1)
            self.assertNotIn(old_merge, git('log', '--format=%H', '-S', 'revision: 103',
                                             '--', 'pack/adapters/INSTALL.md').split())
            self.assertIn(old_merge, git('log', '-m', '--format=%H', '-S', 'revision: 103',
                                         '--', 'pack/adapters/INSTALL.md').split())

            apply('apply', '--install')
            installed_skill = target / '.claude/skills/also/SKILL.md'
            local_extension = b'\nLocal extension must survive.\n'
            installed_skill.write_bytes(installed_skill.read_bytes() + local_extension)
            latest_install = (ROOT / 'pack/adapters/INSTALL.md').read_bytes()
            revision_match = re.search(rb'(?m)^revision: (\d+)$', latest_install)
            self.assertIsNotNone(revision_match)
            assert revision_match is not None
            source_revision = int(revision_match.group(1))
            install.write_bytes(latest_install)
            new_instruction = b'New upstream instruction must survive.\n\n'
            latest_skill = original.replace(b'# ', new_instruction + b'# ', 1)
            skill.write_bytes(latest_skill)
            git('add', 'pack')
            git('commit', '-m', 'Synthetic latest revision instruction')

            plan = apply('plan')
            self.assertEqual((source_revision, 103), (plan['source_revision'], plan['target_revision']))
            self.assertEqual('MERGE', next(row['action'] for row in plan['rows']
                                            if row['path'] == '.claude/skills/also/SKILL.md'))
            apply('apply')
            merged = installed_skill.read_bytes()
            self.assertIn(new_instruction, merged)
            self.assertIn(local_extension, merged)
            self.assertIn(original.split(b'# ', 1)[1], merged)


class Existing102RefreshTests(unittest.TestCase):
    def test_existing_102_refreshes_changed_bytes_and_preserves_project_settings(self):
        if not shutil.which('git'):
            self.skipTest('Git is an installer prerequisite')
        # This two-commit source history is SYNTHETIC: it models revision-based
        # refresh decisions, not the exact bytes/behavior of a published old pack.
        # Build it locally so shallow CI needs no old source SHA or network fetch.
        with tempfile.TemporaryDirectory(prefix='synthetic pack refresh ') as folder:
            source = Path(folder) / 'source'
            target = Path(folder) / 'target'
            shutil.copytree(ROOT / 'pack', source / 'pack', ignore=shutil.ignore_patterns('__pycache__'))
            target.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_TERMINAL_PROMPT='0', PYTHONDONTWRITEBYTECODE='1')

            def run(command, cwd):
                result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                                        text=True, encoding='utf-8', timeout=90)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                return result.stdout

            def git(*args):
                return run(['git', '-c', 'core.autocrlf=false', '-c', 'user.name=Regression Fixture',
                            '-c', 'user.email=fixture@example.invalid', *args], source)

            def apply(mode, *args):
                return json.loads(run([sys.executable, str(source / 'pack/scripts/pack-apply.py'),
                                       mode, '--target', str(target), '--no-baselines', '--json',
                                       *args], target))

            def snapshot():
                return {p.relative_to(target).as_posix(): p.read_bytes()
                        for p in target.rglob('*') if p.is_file()}

            # Latest authored bytes are copied first; modify only the disposable
            # baseline into deliberately distinguishable old fixture content.
            changed_text = (
                'adapters/hooks/session-start.py', 'scripts/delivery.py', 'scripts/pack-apply.py',
                'adapters/hooks/git-identity-guard.py',
                'adapters/hooks/README.md', 'commands/addpacktorepo/SKILL.md',
                'adapters/copilot/prompts/addpacktorepo.prompt.md', 'README.md', 'OVERVIEW.md',
            )
            configs = ('claude-code.settings.hooks.json', 'copilot.ai-forward-hooks.json',
                       'grok.ai-forward-hooks.json')
            changed = [*changed_text, 'context-budget.json', 'adapters/INSTALL.md',
                       *('adapters/hooks/' + name for name in configs)]
            latest = {name: (source / 'pack' / name).read_bytes() for name in changed}
            revision_match = re.search(rb'(?m)^revision: (\d+)$', latest['adapters/INSTALL.md'])
            self.assertIsNotNone(revision_match)
            assert revision_match is not None
            source_revision = int(revision_match.group(1))
            for name in changed_text:
                with (source / 'pack' / name).open('ab') as stream:
                    stream.write(b'\n# Synthetic revision102 baseline, not published source.\n')
            install = source / 'pack/adapters/INSTALL.md'
            install.write_bytes(re.sub(rb'(?m)^revision: \d+$', b'revision: 102', latest['adapters/INSTALL.md']))
            budget = source / 'pack/context-budget.json'
            old_budget = json.loads(budget.read_text(encoding='utf-8'))
            old_budget['synthetic_revision102_fixture'] = True
            budget.write_text(json.dumps(old_budget, indent=2) + '\n', encoding='utf-8', newline='\n')
            for name in configs:
                config = source / 'pack/adapters/hooks' / name
                old = json.loads(config.read_text(encoding='utf-8'))
                for event, entries in old['hooks'].items():
                    old['hooks'][event] = [entry for entry in entries
                                           if 'git-identity-guard.py' not in json.dumps(entry)]
                config.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8', newline='\n')
            git('init')
            git('add', 'pack')
            git('commit', '-m', 'Synthetic revision102 baseline fixture')

            product = target / 'product.txt'
            product.write_bytes(b'Project-owned content must survive.\n')
            index = target / 'docs/docs-index.js'
            index.parent.mkdir(parents=True)
            index.write_bytes(b'window.DOCS_INDEX = {projectOwned: true};\n')
            settings = target / '.claude/settings.json'
            settings.parent.mkdir()
            local_hook = {'matcher': 'ProjectOnly', 'hooks': [
                {'type': 'command', 'command': 'project-local-check', 'timeout': 17}]}
            custom = {'permissions': {'allow': ['Bash(git status)']},
                      'env': {'PROJECT_SETTING': 'preserved'},
                      'hooks': {'PreToolUse': [local_hook]}}
            settings.write_text(json.dumps(custom) + '\n', encoding='utf-8', newline='\n')
            agy = target / '.agents/hooks.json'
            agy.parent.mkdir()
            local_bundle = {'enabled': True, 'Stop': [{'command': 'project-local-stop'}]}
            agy.write_text(json.dumps({'project-local': local_bundle}) + '\n', encoding='utf-8', newline='\n')
            apply('apply', '--install')
            self.assertIn(b'revision: 102\n', (target / 'docs/ai-forward-pack/INSTALL.md').read_bytes())
            before = snapshot()
            for name, data in latest.items():
                (source / 'pack' / name).write_bytes(data)
            git('add', 'pack')
            git('commit', '-m', 'Synthetic latest integration fixture')
            plan = apply('plan')
            self.assertEqual(before, snapshot(), 'Full-map plan must not write the existing target')
            apply('apply')

            # Byte equality catches same-revision KEEP even when apply exits zero.
            # Script/hook/config refresh is exercised through the actual source CLI.
            destinations = {
                'adapters/hooks/session-start.py': 'docs/ai-forward-pack/hooks/session-start.py',
                'scripts/delivery.py': 'docs/ai-forward-pack/scripts/delivery.py',
                'scripts/pack-apply.py': 'docs/ai-forward-pack/scripts/pack-apply.py',
                'adapters/hooks/git-identity-guard.py': 'docs/ai-forward-pack/hooks/git-identity-guard.py',
                'adapters/hooks/README.md': 'docs/ai-forward-pack/hooks/README.md',
                'adapters/hooks/copilot.ai-forward-hooks.json': '.github/hooks/ai-forward.json',
                'adapters/hooks/grok.ai-forward-hooks.json': '.grok/hooks/ai-forward.json',
                'context-budget.json': 'docs/ai-forward-pack/context-budget.json',
                'README.md': 'docs/ai-forward-pack/README.md',
                'OVERVIEW.md': 'docs/ai-forward-pack/OVERVIEW.md',
            }
            for name, destination in destinations.items():
                self.assertEqual(latest[name], (target / destination).read_bytes(), destination)
            for host in ('.claude', '.grok', '.agents'):
                self.assertEqual(latest['commands/addpacktorepo/SKILL.md'],
                                 (target / host / 'skills/addpacktorepo/SKILL.md').read_bytes())
            self.assertEqual(latest['adapters/copilot/prompts/addpacktorepo.prompt.md'],
                             (target / '.github/prompts/addpacktorepo.prompt.md').read_bytes())
            self.assertEqual(latest['adapters/INSTALL.md'], (target / 'docs/ai-forward-pack/INSTALL.md').read_bytes())
            self.assertEqual(source_revision, plan['source_revision'])
            self.assertEqual(102, plan['target_revision'])
            self.assertEqual('UPDATE', next(row['action'] for row in plan['rows']
                                           if row['path'] == 'docs/ai-forward-pack/hooks/session-start.py'))
            self.assertEqual(before['product.txt'], product.read_bytes())
            self.assertEqual(before['docs/docs-index.js'], index.read_bytes())
            merged = json.loads(settings.read_text(encoding='utf-8'))
            for key in ('permissions', 'env'):
                self.assertEqual(custom[key], merged[key])
            expected = json.loads(latest['adapters/hooks/claude-code.settings.hooks.json'])
            for event, entries in expected['hooks'].items():
                self.assertCountEqual(entries + ([local_hook] if event == 'PreToolUse' else []),
                                      merged['hooks'][event])
            self.assertEqual(local_bundle, json.loads(agy.read_text(encoding='utf-8'))['project-local'])
            self.assertFalse((target / 'docs/index.html').exists(), 'Refresh is not Explorer opt-in')
            refreshed = snapshot()
            apply('apply')
            self.assertEqual(refreshed, snapshot(), 'Repeating a refresh preserves installed and project bytes')


class UpstreamWorkflowPolicyTests(unittest.TestCase):
    def test_adoption_workflow_is_manual_only_and_routes_session_resume_regression(self):
        raw = (ROOT / '.github/workflows/adoption-entrypoints.yml').read_bytes()
        triggers = raw.split(b'\non:\n', 1)[1].split(b'permissions:\n', 1)[0]
        self.assertEqual(b'  workflow_dispatch:\n', triggers,
                         'Follow the upstream manual-only Actions policy')
        routing = next(line for line in raw.splitlines()
                       if b'run: python -m pytest ' in line)
        added_tests = (
            b' tests/docs_explorer/test_delivery_session_start.py'
            b' tests/docs_explorer/test_upstream_adoption_integration.py'
            b' tests/docs_explorer/test_git_identity_guard.py'
            b' tests/docs_explorer/test_session_start_hook.py'
            b' tests/docs_explorer/test_pack_apply.py'
        )
        for name in added_tests.split():
            self.assertIn(name, routing)
        # Undo the only authorized job edit and compare the complete native proof
        # body, not just headings. Permissions, every OS and native cmd remain.
        jobs = raw[raw.index(b'permissions:\n'):]
        self.assertEqual(1, jobs.count(added_tests))
        # Revision106 adds only the maintained repair/native parser checks to the
        # same read-only job. Reverse that exact addition before applying the
        # retained complete original-job oracle below.
        repair_tests = (
            b' tests/docs_explorer/test_delivery_outcome_repairs.py'
            b' tests/docs_explorer/test_delivery_startup_composition.py'
            b' tests/docs_explorer/test_delivery_recovery_guidance.py'
            b' tests/docs_explorer/test_delivery_repair_ci_coverage.py'
            b' tests/docs_explorer/test_pack_doctor.py'
            b' tests/docs_explorer/test_run_evals.py'
            b' tests/docs_explorer/test_cross_platform_controls.py'
            b' tests/docs_explorer/test_coord_enforcement.py'
            b' tests/docs_explorer/test_coord_install_path.py'
            b' tests/docs_explorer/test_copilot_runner.py'
            b' tests/docs_explorer/test_prestart_scope_guidance.py'
            b' tests/docs_explorer/test_delivery_preexecution_gates.py'
            b' tests/docs_explorer/test_native_repair_runtime_budget.py'
        )
        self.assertEqual(1, jobs.count(repair_tests))
        jobs = jobs.replace(repair_tests, b'', 1)
        unchanged_jobs = jobs.replace(added_tests, b'', 1)
        unchanged_jobs = unchanged_jobs.replace(
            b'    # Preserve the complete matrix inventory; Windows filesystem controls need\n'
            b'    # more than the historical 20-minute cap after the recovery regressions.\n'
            b'    timeout-minutes: 45', b'    timeout-minutes: 20', 1)
        self.assertEqual('43c5bf864846a145f963e1d05282a6cddbed778571a93dbb89e47be782f9794d',
                         hashlib.sha256(unchanged_jobs).hexdigest())
        self.assertIn(b'os: [ubuntu-latest, macos-latest, windows-latest]', jobs)
        self.assertIn(b'shell: cmd', jobs)


if __name__ == '__main__':
    unittest.main()
