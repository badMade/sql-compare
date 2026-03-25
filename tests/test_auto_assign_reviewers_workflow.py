"""Tests for auto-assign-reviewers GitHub Actions workflow."""
import unittest
from pathlib import Path
import yaml
import re


class TestAutoAssignReviewersWorkflow(unittest.TestCase):
    """Test that auto-assign-reviewers workflow is valid and properly structured."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        self.workflow_file = self.workflows_dir / 'auto-assign-reviewers.yml'

        with open(self.workflow_file, 'r', encoding='utf-8') as f:
            self.workflow = yaml.safe_load(f)

    def _get_script_from_step(self, step_name):
        """Extract script from a named step in the workflow."""
        for job_name, job in self.workflow.get('jobs', {}).items():
            for step in job.get('steps', []):
                if step.get('name') == step_name:
                    return step.get('with', {}).get('script', '')
        return None

    def test_workflow_yaml_valid(self):
        """Test that auto-assign-reviewers.yml is valid YAML."""
        self.assertTrue(self.workflow_file.exists(),
                       f"Workflow file not found: {self.workflow_file}")
        self.assertIsInstance(self.workflow, dict, "Workflow should be a dictionary")

    def test_workflow_has_required_fields(self):
        """Test that workflow has all required fields."""
        self.assertIn('name', self.workflow, "Workflow should have a 'name' field")
        self.assertIn('on', self.workflow, "Workflow should have an 'on' trigger field")
        self.assertIn('jobs', self.workflow, "Workflow should have a 'jobs' field")

    def test_workflow_triggers_on_pull_request(self):
        """Test that workflow triggers on pull_request events."""
        self.assertIn('pull_request', self.workflow['on'],
                     "Workflow should trigger on pull_request events")
        pr_types = self.workflow['on']['pull_request']['types']
        self.assertIn('opened', pr_types, "Should trigger on 'opened' PRs")
        self.assertIn('reopened', pr_types, "Should trigger on 'reopened' PRs")

    def test_workflow_has_permissions(self):
        """Test that workflow has appropriate permissions."""
        job = self.workflow['jobs']['assign-reviewers']
        self.assertIn('permissions', job, "Job should have permissions defined")
        self.assertIn('pull-requests', job['permissions'],
                     "Job should have pull-requests permission")
        self.assertEqual(job['permissions']['pull-requests'], 'write',
                        "Should have write permission for pull-requests")

    def test_workflow_only_runs_on_non_fork_prs(self):
        """Test that workflow only runs on PRs from the main repo, not forks."""
        job = self.workflow['jobs']['assign-reviewers']
        self.assertIn('if', job, "Job should have conditional execution")
        condition = job['if']
        # Should check that head repo matches the base repo
        self.assertIn('github.event.pull_request.head.repo.full_name', condition,
                     "Should check PR head repo")
        self.assertIn('github.repository', condition,
                     "Should compare against base repository")

    def test_script_has_no_variable_name_mismatches(self):
        """Test that script variables are used consistently."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Check for variable definition and usage consistency
        # If prNumber is defined, it should be used (not pullRequestNumber)
        if 'const prNumber' in script:
            self.assertNotIn('pullRequestNumber', script,
                           "Should not use undefined variable 'pullRequestNumber'")
            self.assertIn('pull_number: prNumber', script,
                         "Should use 'prNumber' consistently")

        # If reviewers array is defined, it should be used consistently
        if 'const reviewers' in script:
            # Should use 'reviewers' in the API call, not some other variable
            self.assertIn('reviewers: reviewers', script,
                         "Should use 'reviewers' variable consistently")

    def test_script_uses_individual_reviewers_not_teams(self):
        """Test that script uses individual reviewers, not team reviewers."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should NOT use team_reviewers parameter (teams aren't collaborators)
        self.assertNotIn('team_reviewers:', script,
                        "Should not use 'team_reviewers' parameter")

        # Should use 'reviewers' parameter for individual reviewers
        if 'github.rest.pulls.requestReviewers' in script:
            self.assertIn('reviewers:', script,
                         "Should use 'reviewers' parameter for individuals")

    def test_script_validates_payload_exists(self):
        """Test that script validates context.payload.pull_request exists."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should validate that pull_request payload exists
        self.assertIn('context.payload.pull_request', script,
                     "Should reference pull_request from payload")

    def test_script_has_proper_error_handling(self):
        """Test that script has proper try-catch error handling."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should have try-catch block
        self.assertIn('try {', script, "Should have try block")
        self.assertIn('catch', script, "Should have catch block")

        # Should use core.setFailed on error
        self.assertIn('core.setFailed', script,
                     "Should use core.setFailed to mark workflow as failed")

    def test_script_handles_empty_reviewers_gracefully(self):
        """Test that script handles empty reviewer list without error."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should check if reviewers list is empty before making API call
        if 'reviewers.length' in script or 'length === 0' in script:
            # Should return early if no reviewers specified
            self.assertIn('return', script,
                         "Should return early when no reviewers specified")

    def test_script_uses_correct_api_method(self):
        """Test that script uses the correct GitHub API method."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should use pulls.requestReviewers API
        self.assertIn('github.rest.pulls.requestReviewers', script,
                     "Should use pulls.requestReviewers API method")

    def test_script_uses_correct_repo_context(self):
        """Test that script uses correct repository context."""
        script = self._get_script_from_step('Request reviewers')
        self.assertIsNotNone(script, "Could not find 'Request reviewers' step")

        # Should use context.repo for owner and repo
        if 'github.rest.pulls.requestReviewers' in script:
            self.assertIn('context.repo.owner', script,
                         "Should use context.repo.owner")
            self.assertIn('context.repo.repo', script,
                         "Should use context.repo.repo")


if __name__ == '__main__':
    unittest.main()
