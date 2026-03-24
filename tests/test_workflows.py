"""Tests for GitHub Actions workflow YAML files."""
import unittest
from pathlib import Path
import yaml


class TestWorkflowYAML(unittest.TestCase):
    """Test that workflow YAML files are valid and properly structured."""

    def setUp(self):
        """Set up test fixtures."""
        self.github_dir = Path(__file__).parent.parent / '.github'

    def test_copilot_setup_steps_yaml_valid(self):
        """Test that copilot-setup-steps.yaml is valid YAML and uses simplified schema."""
        setup_file = self.github_dir / 'copilot-setup-steps.yaml'
        self.assertTrue(setup_file.exists(),
                       f"Setup file not found: {setup_file}")

        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML - this will raise an exception if invalid
        data = yaml.safe_load(content)

        # Verify simplified structure
        self.assertIsInstance(data, dict, "Setup file should be a dictionary")
        self.assertIn('env', data, "Setup file should have an 'env' field")
        self.assertIn('steps', data, "Setup file should have a 'steps' field")
        self.assertNotIn('name', data, "Simplified schema should not have 'name'")
        self.assertNotIn('on', data, "Simplified schema should not have 'on'")
        self.assertNotIn('jobs', data, "Simplified schema should not have 'jobs'")

    def test_copilot_setup_steps_structure(self):
        """Test that copilot-setup-steps has correct structure."""
        setup_file = self.github_dir / 'copilot-setup-steps.yaml'

        with open(setup_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Verify steps structure
        self.assertIsInstance(data['steps'], list, "Steps should be a list")
        self.assertGreater(len(data['steps']), 0, "Should have at least one step")
        self.assertIn('name', data['steps'][0], "Step should have a name")
        self.assertIn('run', data['steps'][0], "Step should have a run command")


if __name__ == '__main__':
    unittest.main()
