import unittest
import yaml
from pathlib import Path

class TestWorkflowSecurity(unittest.TestCase):
    """Tests for security improvements in workflow files."""

    def setUp(self):
        """Load workflow files."""
        self.workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"
        self.codex_workflow = self._load_workflow("codex.yml")
        self.jules_workflow = self._load_workflow("jules.yml")

    def _load_workflow(self, filename):
        """Load and parse a workflow file."""
        workflow_path = self.workflows_dir / filename
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_script_from_step(self, workflow, step_name):
        """Extract script from a named step in the workflow."""
        for job_name, job in workflow.get('jobs', {}).items():
            for step in job.get('steps', []):
                if step.get('name') == step_name:
                    return step.get('with', {}).get('script', '')
        return None

    def test_codex_has_helper_functions(self):
        """Test that codex.yml includes helper functions for error handling."""
        script = self._get_script_from_step(self.codex_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for helper functions
        self.assertIn('safeErrorMessage', script, "Missing safeErrorMessage helper function")
        self.assertIn('parsePrNumber', script, "Missing parsePrNumber helper function")

        # Check for improved logging
        self.assertIn('core.error', script, "Should use core.error for error logging")
        self.assertIn('core.info', script, "Should use core.info for info logging")

    def test_codex_has_pagination_limit(self):
        """Test that codex.yml has pagination limits to prevent infinite loops."""
        script = self._get_script_from_step(self.codex_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for pagination logic (moved to helper)
        self.assertIn('fetchPrFilesWithPagination', script, "Missing fetchPrFilesWithPagination helper")

    def test_codex_review_has_retry_logic(self):
        """Test that codex.yml review step includes retry logic."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for retry function
        self.assertIn('fetchWithRetry', script, "Missing fetchWithRetry helper function")
        self.assertIn('retries', script, "Retry logic should have retries parameter")

    def test_codex_review_validates_content_type(self):
        """Test that codex.yml validates content-type before parsing JSON."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for content-type validation
        self.assertIn('isJsonResponse', script, "Missing isJsonResponse helper function")
        self.assertIn('safeReadBody', script, "Should use safeReadBody for robust response reading")

    def test_codex_review_truncates_errors(self):
        """Test that codex.yml truncates error messages to prevent sensitive data exposure."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for error truncation (moved to helper)
        self.assertIn('safeErrorMessage', script, "Should use safeErrorMessage for truncated errors")

    def test_codex_api_key_validation(self):
        """Test that codex.yml validates API key without logging it."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for API key validation
        self.assertIn('OPENAI_API_KEY', script, "Should reference OPENAI_API_KEY")
        # Ensure we're not logging the key value directly
        self.assertNotIn('console.log(process.env.OPENAI_API_KEY)', script,
                        "Should not log API key value")

    def test_jules_has_helper_functions(self):
        """Test that jules.yml includes helper functions for error handling."""
        script = self._get_script_from_step(self.jules_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for helper functions
        self.assertIn('safeErrorMessage', script, "Missing safeErrorMessage helper function")
        self.assertIn('parsePrNumber', script, "Missing parsePrNumber helper function")

    def test_jules_has_pagination_limit(self):
        """Test that jules.yml has pagination limits to prevent infinite loops."""
        script = self._get_script_from_step(self.jules_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for pagination logic (moved to helper)
        self.assertIn('fetchPrFilesWithPagination', script, "Missing fetchPrFilesWithPagination helper")

    def test_jules_review_has_retry_logic(self):
        """Test that jules.yml review step includes retry logic."""
        script = self._get_script_from_step(self.jules_workflow, 'Review with Jules (Gemini)')
        self.assertIsNotNone(script, "Could not find 'Review with Jules (Gemini)' step")

        # Check for retry function
        self.assertIn('fetchWithRetry', script, "Missing fetchWithRetry helper function")
        self.assertIn('retries', script, "Retry logic should have retries parameter")

    def test_jules_review_validates_content_type(self):
        """Test that jules.yml validates content-type before parsing JSON."""
        script = self._get_script_from_step(self.jules_workflow, 'Review with Jules (Gemini)')
        self.assertIsNotNone(script, "Could not find 'Review with Jules (Gemini)' step")

        # Check for content-type validation
        self.assertIn('isJsonResponse', script, "Missing isJsonResponse helper function")
        self.assertIn('safeReadBody', script, "Should use safeReadBody for robust response reading")

    def test_both_workflows_use_core_logging(self):
        """Test that both workflows use core.error, core.info, core.warning instead of console.log."""
        for workflow_name, workflow in [('codex', self.codex_workflow), ('jules', self.jules_workflow)]:
            script = self._get_script_from_step(workflow, 'Get PR diff')
            self.assertIsNotNone(script, f"Could not find 'Get PR diff' step in {workflow_name}")

            # Should use core logging methods
            self.assertIn('core.error', script, f"{workflow_name} should use core.error")
            self.assertIn('core.info', script, f"{workflow_name} should use core.info")

    def test_error_handler_catches_all_exceptions(self):
        """Test that error handlers catch and format all exception types."""
        for workflow_name, workflow, step_name in [
            ('codex', self.codex_workflow, 'Get PR diff'),
            ('codex', self.codex_workflow, 'Review with Codex'),
            ('jules', self.jules_workflow, 'Get PR diff'),
            ('jules', self.jules_workflow, 'Review with Jules (Gemini)')
        ]:
            script = self._get_script_from_step(workflow, step_name)
            self.assertIsNotNone(script, f"Could not find '{step_name}' step in {workflow_name}")

            # Check for try-catch blocks
            self.assertIn('try {', script, f"{workflow_name}/{step_name} should have try block")
            self.assertIn('catch', script, f"{workflow_name}/{step_name} should have catch block")

            # Check for safeErrorMessage usage in catch
            self.assertIn('safeErrorMessage', script, f"{workflow_name}/{step_name} should use safeErrorMessage")

    def test_pr_number_validation_consistency(self):
        """Test that PR number validation is consistent across workflows."""
        for workflow_name, workflow in [('codex', self.codex_workflow), ('jules', self.jules_workflow)]:
            script = self._get_script_from_step(workflow, 'Get PR diff')
            self.assertIsNotNone(script, f"Could not find 'Get PR diff' step in {workflow_name}")

            # Check for parsePrNumber helper
            self.assertIn('parsePrNumber', script,
                         f"{workflow_name} should use parsePrNumber helper")

if __name__ == '__main__':
    unittest.main()
