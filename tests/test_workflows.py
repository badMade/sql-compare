"""Tests for GitHub Actions workflow YAML files."""
import unittest
from pathlib import Path
import yaml


class TestWorkflowYAML(unittest.TestCase):
    """Test that workflow YAML files are valid and properly structured."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'

    def test_copilot_setup_steps_yaml_valid(self):
        """Test that copilot-setup-steps.yaml is valid YAML."""
        workflow_file = self.workflows_dir / 'copilot-setup-steps.yaml'
        self.assertTrue(workflow_file.exists(),
                       f"Workflow file not found: {workflow_file}")

        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML - this will raise an exception if invalid
        data = yaml.safe_load(content)

        # Verify basic structure
        self.assertIsInstance(data, dict, "Workflow should be a dictionary")
        self.assertIn('name', data, "Workflow should have a 'name' field")
        self.assertIn('on', data, "Workflow should have an 'on' trigger field")
        self.assertIn('jobs', data, "Workflow should have a 'jobs' field")

    def test_copilot_setup_steps_on_trigger_is_dict(self):
        """Test that 'on' trigger is correctly parsed as a dictionary, not a boolean."""
        workflow_file = self.workflows_dir / 'copilot-setup-steps.yaml'

        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # The 'on' field must be a dictionary, not a boolean
        # This was the bug: unquoted 'on:' was being parsed as boolean True
        self.assertIsInstance(data['on'], dict,
                            "'on' trigger must be a dictionary, not boolean. "
                            "Use quoted 'on': or \"on\": in YAML to avoid "
                            "YAML parser treating it as a boolean keyword.")

        # Verify it contains workflow_call trigger
        self.assertIn('workflow_call', data['on'],
                     "Expected 'workflow_call' trigger in 'on' section")

    def test_copilot_setup_steps_job_structure(self):
        """Test that copilot-setup-steps job has correct structure."""
        workflow_file = self.workflows_dir / 'copilot-setup-steps.yaml'

        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Check job exists
        self.assertIn('copilot-setup-steps', data['jobs'],
                     "Expected 'copilot-setup-steps' job")

        job = data['jobs']['copilot-setup-steps']

        # Verify job structure
        self.assertIn('runs-on', job, "Job should specify 'runs-on'")
        self.assertIn('steps', job, "Job should have 'steps'")
        self.assertIsInstance(job['steps'], list, "Steps should be a list")
        self.assertGreater(len(job['steps']), 0, "Job should have at least one step")

    def test_codex_and_jules_have_same_trigger_events(self):
        """Test that Codex and Jules workflows have identical trigger events."""
        codex_file = self.workflows_dir / 'codex.yml'
        jules_file = self.workflows_dir / 'jules.yml'

        self.assertTrue(codex_file.exists(), f"Codex workflow not found: {codex_file}")
        self.assertTrue(jules_file.exists(), f"Jules workflow not found: {jules_file}")

        with open(codex_file, 'r', encoding='utf-8') as f:
            codex_data = yaml.safe_load(f)

        with open(jules_file, 'r', encoding='utf-8') as f:
            jules_data = yaml.safe_load(f)

        # The 'on' key gets parsed as boolean True in YAML
        # Both should have 'on' triggers (stored as True key)
        on_key = True if True in codex_data else 'on'
        self.assertIn(on_key, codex_data, "Codex workflow should have 'on' triggers")
        self.assertIn(on_key, jules_data, "Jules workflow should have 'on' triggers")

        # Extract pull_request types
        codex_pr_types = codex_data[on_key].get('pull_request', {}).get('types', [])
        jules_pr_types = jules_data[on_key].get('pull_request', {}).get('types', [])

        # Both should have the same pull_request event types
        self.assertEqual(
            set(codex_pr_types),
            set(jules_pr_types),
            "Codex and Jules workflows should have identical pull_request event types. "
            "This ensures both workflows trigger on the same PR events (opened, labeled, synchronize)."
        )

        # Verify 'synchronize' is included
        self.assertIn('synchronize', codex_pr_types,
                     "Codex workflow should trigger on 'synchronize' events")
        self.assertIn('synchronize', jules_pr_types,
                     "Jules workflow should trigger on 'synchronize' events")

    def test_review_workflows_require_safe_for_ai_review_label(self):
        """Test that both Codex and Jules workflows require safe-for-ai-review label."""
        codex_file = self.workflows_dir / 'codex.yml'
        jules_file = self.workflows_dir / 'jules.yml'

        with open(codex_file, 'r', encoding='utf-8') as f:
            codex_content = f.read()

        with open(jules_file, 'r', encoding='utf-8') as f:
            jules_content = f.read()

        # Both workflows should check for the safe-for-ai-review label
        self.assertIn('safe-for-ai-review', codex_content,
                     "Codex workflow should require 'safe-for-ai-review' label")
        self.assertIn('safe-for-ai-review', jules_content,
                     "Jules workflow should require 'safe-for-ai-review' label")


if __name__ == '__main__':
    unittest.main()
