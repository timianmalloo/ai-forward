"""Revision 108: the one delta that integrates upstream revisions 100 to 102 into the delivery line."""
import hashlib
import importlib.util
import json
import re
import unittest

from test_upstream_adoption_integration import (ROOT, UPSTREAM_MAIN_SHA, recovered_revision_107_install,
                                               recovered_revision_108_install)

_spec = importlib.util.spec_from_file_location('pack_apply_r108', ROOT / 'pack/scripts/pack-apply.py')
pack_apply = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pack_apply)
PLAIN = 'git -c alias.aif-hook=!sh aif-hook docs/ai-forward-pack/hooks/run-hook.sh '


class StartupRefreshRunsOnceTests(unittest.TestCase):
    def test_a_refreshed_startup_entry_is_replaced_not_duplicated(self):
        source = (ROOT / 'pack/adapters/hooks/claude-code.settings.hooks.json').read_text(encoding='utf-8')
        for legacy in (PLAIN + 'session-start.py --host claude',
                       pack_apply.STARTUP_LAUNCHER + 'session-start.py --host claude'):
            current = {'hooks': {event: [{'hooks': [{'type': 'command', 'command': legacy}]}]
                                 for event in ('SessionStart', 'SubagentStart')}}
            merged = json.loads(pack_apply.merge_claude_settings(source, json.dumps(current)))
            for event in ('SessionStart', 'SubagentStart'):
                with self.subTest(legacy=legacy[:60], event=event):
                    commands = [h['command'] for e in merged['hooks'][event] for h in e['hooks']]
                    self.assertEqual([pack_apply.STARTUP_LAUNCHER + 'dispatch.py --host claude --event ' + event],
                                     commands, 'startup must run once, through the dispatcher')

    def test_a_custom_startup_wrapper_survives(self):
        source = (ROOT / 'pack/adapters/hooks/claude-code.settings.hooks.json').read_text(encoding='utf-8')
        custom = 'sh ./my-start.sh && ' + PLAIN + 'session-start.py --host claude'
        current = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': custom}]}]}}
        merged = json.loads(pack_apply.merge_claude_settings(source, json.dumps(current)))
        commands = [h['command'] for e in merged['hooks']['SessionStart'] for h in e['hooks']]
        self.assertIn(custom, commands)


class UpstreamHookCostRefreshMetadataTests(unittest.TestCase):
    def test_revision_108_is_the_one_upstream_100_to_102_integration_delta(self):
        raw = recovered_revision_108_install()
        frontmatter = raw.split(b'---\n', 2)[1].decode('utf-8')
        self.assertRegex(frontmatter, r"(?m)^revision: 108$")
        self.assertIn("bundle_version: '2026.10.16.1'", frontmatter)
        self.assertIn('counts: { lenses: 23, skills: 30, knowledge_docs: 40, templates: 29, scripts: 47 }',
                      frontmatter)
        self.assertEqual(1, frontmatter.count('  - { type: changed,'))
        self.assertIn('area: upstream-hook-cost-refresh', frontmatter)
        paths = re.search(r"paths: \[(.*?)\], deploy:", frontmatter)
        assert paths is not None
        for path in re.findall(r"'([^']+)'", paths.group(1)):
            with self.subTest(source_path=path):
                self.assertTrue((ROOT / 'pack' / path).is_file(), path)
        deploy = frontmatter.split("deploy: '", 1)[1].split("', summary:", 1)[0]
        for instruction in ('SOURCE clone, not an installed applier', 'revision 107 to 108',
                            'dispatch.py', 'bounded-search session-start.py', 'custom wrappers',
                            'RE-PASTE the AGENTS.md managed block', 'grant trust or permissions'):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, deploy)
        self.assertNotRegex(raw, rb'(?m)^(?:<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)(?: |$)')

    def test_upstream_100_to_102_rows_retained_verbatim_with_distinct_provenance(self):
        raw = recovered_revision_108_install()
        blocks = re.findall(rb'<details>\n<summary>.*?\n</details>', raw, re.S)
        self.assertEqual(11, len(blocks), 'Add two archives without deleting any existing history')
        self.assertIn(UPSTREAM_MAIN_SHA.encode('ascii'), blocks[1])
        self.assertIn(b'upstream revisions 100 to 102 are not the earlier contribution revisions', blocks[1])
        rows = blocks[1].split(b'```yaml\nchanges:\n', 1)[1].split(b'\n```', 1)[0].splitlines()
        self.assertEqual((
            (976, 'ae32282f8c162fb2cf5d890fa28f3f660a379dcb468648372cb1669d2883d346'),
            (3017, '2c8a25e06e220421bfc8188f0db2a00f5c608f57226314a373949748df249c0a'),
            (1873, 'ab8d0ab8847b89be8b04cb03dd87648de46fc952093863d5658893191e344826'),
        ), tuple((len(row), hashlib.sha256(row).hexdigest()) for row in rows))
        for row in rows:
            self.assertEqual(1, raw.count(row), 'Retain each raw upstream row exactly once')

    def test_reversal_recovers_the_complete_revision_107_source(self):
        recovered = recovered_revision_107_install()
        self.assertEqual((276537, 'dea0ad85ea801dd7757e63420a254b12e6331eaefb07f99b12e6e79f672a04e8'),
                         (len(recovered), hashlib.sha256(recovered).hexdigest()))
        raw = recovered_revision_108_install()
        corrupted = raw.replace(b'area: delivery-repair-history', b'area: delivery-repair-historY', 1)
        self.assertNotEqual(raw, corrupted)
        with self.assertRaises(AssertionError):
            recovered_revision_107_install(corrupted)


if __name__ == '__main__':
    unittest.main()
