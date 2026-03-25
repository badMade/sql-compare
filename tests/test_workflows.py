"""Tests for GitHub Actions workflow YAML files."""
import re
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


class TestAutoAssignReviewersWorkflow(unittest.TestCase):
    """Tests for the auto-assign-reviewers workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        workflow_path = self.workflows_dir / 'auto-assign-reviewers.yml'
        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.workflow = yaml.safe_load(f)

    def _get_request_reviewers_script(self):
        """Extract the script from the 'Request reviewers' step."""
        for job in self.workflow.get('jobs', {}).values():
            for step in job.get('steps', []):
                if step.get('name') == 'Request reviewers':
                    return step.get('with', {}).get('script', '')
        return None

    def test_workflow_yaml_is_valid(self):
        """Test that auto-assign-reviewers.yml is valid YAML."""
        self.assertIsInstance(self.workflow, dict)
        self.assertIn('jobs', self.workflow)

    def test_workflow_uses_individual_reviewers_not_teams(self):
        """Ensure the script uses 'reviewers' (individuals), not 'team_reviewers'."""
        script = self._get_request_reviewers_script()
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")
        self.assertIn('reviewers:', script,
                      "Script must pass 'reviewers' to requestReviewers()")
        self.assertNotIn('team_reviewers:', script,
                         "Script must not use 'team_reviewers' (non-collaborator teams cause 422)")

    def test_workflow_no_undefined_variable_references(self):
        """Ensure the script does not reference stale variable names."""
        script = self._get_request_reviewers_script()
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")
        self.assertNotIn('pullRequestNumber', script,
                         "'pullRequestNumber' is undefined; use 'prNumber'")
        self.assertNotIn('collaboratorTeamSlugs', script,
                         "'collaboratorTeamSlugs' is undefined; use 'reviewers'")
        self.assertNotIn('teamReviewers', script,
                         "'teamReviewers' is stale; variable was renamed to 'reviewers'")

    def test_workflow_guards_payload_access(self):
        """Ensure the script checks context.payload.pull_request before use."""
        script = self._get_request_reviewers_script()
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")
        self.assertIn('context.payload.pull_request', script,
                      "Script must guard against missing pull_request payload")

    def test_workflow_uses_core_logging(self):
        """Ensure the script uses core.info/core.error, not console.log/console.error."""
        script = self._get_request_reviewers_script()
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")
        self.assertIn('core.info', script,
                      "Script should use core.info for informational logging")
        self.assertIn('core.error', script,
                      "Script should use core.error for error logging")
        self.assertNotIn('console.log', script,
                         "Script should not use console.log; prefer core.info")
        self.assertNotIn('console.error', script,
                         "Script should not use console.error; prefer core.error")

    def test_workflow_error_truncation(self):
        """Ensure error messages are truncated to prevent secret leakage."""
        script = self._get_request_reviewers_script()
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")
        self.assertRegex(
            script,
            r'(slice|substring)\s*\(0,\s*500\)',
            "Error messages must be truncated to 500 chars to prevent secret exposure",
        )


if __name__ == '__main__':
    unittest.main()
