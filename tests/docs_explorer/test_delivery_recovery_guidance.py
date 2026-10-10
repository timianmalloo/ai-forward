"""Customer-facing recovery guidance follows the implemented delivery boundary."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class DeliveryRecoveryGuidanceTests(unittest.TestCase):
 def test_first_question_recovery_is_owned_by_deliver(self):
  skill=(ROOT/'pack/commands/deliver/SKILL.md').read_text(encoding='utf-8')
  reference=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
  for phrase in ('prestart', 'original raw', 'same task'):
   with self.subTest(phrase=phrase):self.assertIn(phrase,reference)
  self.assertIn('pre-start',skill)
  self.assertIn('before asking',skill)
  self.assertIn('original',skill)
 def test_customer_can_resume_first_question_and_keep_tool_authority_separate(self):
  for relative in ('web/handbook/guides/get-started.md','web/handbook/skills/deliver.md'):
   with self.subTest(page=relative):
    body=(ROOT/relative).read_text(encoding='utf-8')
    self.assertIn('first question',body)
    self.assertIn('task id',body)
    self.assertIn('existing audit',body)
    self.assertIn('tool permission',body)
    self.assertIn('valid completed work',body)
 def test_startup_readiness_is_not_checkpoint_integrity(self):
  reference=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
  self.assertIn('FAILED',reference)
  self.assertIn('NOT CHECKED',reference)
  self.assertIn('relevant',reference)
  self.assertIn('completed work',reference)
  self.assertNotIn('all startup notices require a new human approval',reference)
 def test_optional_doctor_has_portable_serial_guidance(self):
  body=(ROOT/'web/handbook/guides/get-started.md').read_text(encoding='utf-8')
  self.assertIn('uv run --no-config --no-project --python ">=3.10" docs/ai-forward-pack/scripts/pack-doctor.py',body)
  self.assertIn('inactive coordination',body)
  self.assertIn('not a setup requirement',body)
 def test_eval_is_artifact_not_workflow_qualification(self):
  body=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
  self.assertIn('positive',body)
  self.assertIn('artifact',body)
  self.assertIn('trajectory',body)
 def test_persisted_hook_does_not_claim_uv_path_discovery(self):
     body=(ROOT/'pack/adapters/hooks/README.md').read_text(encoding='utf-8')
     self.assertNotIn("PATH or through the caller's `UV_PATH`",body)
     self.assertIn('uv must be on',body)
     self.assertIn('explicit',body)
 def test_explicit_dispatch_base_is_not_always_head(self):
  body=(ROOT/'pack/commands/execute-with-coordination/reference/launch.md').read_text(encoding='utf-8')
  self.assertNotIn('This creates fresh worktrees from the **invoking checkout\'s HEAD**',body)
  self.assertIn('base',body)
