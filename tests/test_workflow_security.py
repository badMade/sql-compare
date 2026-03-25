import unittest
import yaml
from pathlib import Path

class TestWorkflowSecurity(unittest.TestCase):
    """Tests for security and consistency in workflow files."""

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

    def _verify_workflow_step_security(self, workflow, step_name, workflow_label):
        """Shared helper to verify security best practices in a workflow step."""
        script = self._get_script_from_step(workflow, step_name)
        self.assertIsNotNone(script, f"Could not find '{step_name}' step in {workflow_label}")

        if step_name == 'Get PR diff':
            # Check for core helper functions from review-utils.js
            self.assertIn('parsePrNumber', script, f"{workflow_label}/{step_name} should use parsePrNumber")
            self.assertIn('fetchPrFilesWithPagination', script, f"{workflow_label}/{step_name} should use fetchPrFilesWithPagination")
            self.assertIn('safeErrorMessage', script, f"{workflow_label}/{step_name} should use safeErrorMessage")
        elif 'Review with' in step_name:
            # Check for review step security features
            self.assertIn('normalizePrNumber', script, f"{workflow_label}/{step_name} should use normalizePrNumber")
            self.assertIn('fetchWithRetry', script, f"{workflow_label}/{step_name} should use fetchWithRetry")
            self.assertIn('parseJsonResponse', script, f"{workflow_label}/{step_name} should use parseJsonResponse")
            self.assertIn('safeErrorMessage', script, f"{workflow_label}/{step_name} should use safeErrorMessage")
            # Ensure API keys are not logged
            api_key_env = 'OPENAI_API_KEY' if 'Codex' in step_name else 'GOOGLE_API_KEY'
            self.assertNotIn(f'console.log(process.env.{api_key_env})', script, f"{workflow_label} should not log API key")

        # Check for consistent logging
        self.assertIn('core.error', script, f"{workflow_label}/{step_name} should use core.error")
        self.assertIn('core.info', script, f"{workflow_label}/{step_name} should use core.info")
        self.assertIn('try {', script, f"{workflow_label}/{step_name} should have try block")
        self.assertIn('catch', script, f"{workflow_label}/{step_name} should have catch block")

    def test_codex_get_diff_security(self):
        """Verify security of Codex Get PR diff step."""
        self._verify_workflow_step_security(self.codex_workflow, 'Get PR diff', 'codex.yml')

    def test_codex_review_security(self):
        """Verify security of Codex review step."""
        self._verify_workflow_step_security(self.codex_workflow, 'Review with Codex', 'codex.yml')

    def test_jules_get_diff_security(self):
        """Verify security of Jules Get PR diff step."""
        self._verify_workflow_step_security(self.jules_workflow, 'Get PR diff', 'jules.yml')

    def test_jules_review_security(self):
        """Verify security of Jules review step."""
        self._verify_workflow_step_security(self.jules_workflow, 'Review with Jules (Gemini)', 'jules.yml')

    def test_workflows_import_utils(self):
        """Ensure both workflows import the review-utils library."""
        for workflow_name, workflow in [('codex.yml', self.codex_workflow), ('jules.yml', self.jules_workflow)]:
            for job in workflow.get('jobs', {}).values():
                for step in job.get('steps', []):
                    script = step.get('with', {}).get('script', '')
                    if 'require' in script and 'review-utils' in script:
                        self.assertIn("./.github/actions/review-utils", script,
                                     f"{workflow_name} should import review-utils with correct path")

    def test_jules_workflow_triggers(self):
        """Verify Jules workflow has consistent triggers with Codex."""
        triggers = self.jules_workflow.get('on', {})
        self.assertIn('pull_request', triggers)
        self.assertIn('synchronize', triggers['pull_request']['types'])
        self.assertIn('issue_comment', triggers)
        self.assertIn('pull_request_review_comment', triggers)

    def test_jules_gemini_api_security(self):
        """Verify Jules uses secure header for Gemini API key."""
        script = self._get_script_from_step(self.jules_workflow, 'Review with Jules (Gemini)')
        self.assertIn("'x-goog-api-key': process.env.GOOGLE_API_KEY", script)
        self.assertNotIn("key=${process.env.GOOGLE_API_KEY}", script)

    def test_review_utils_has_security_features(self):
        """Verify that review-utils.js itself has security constants and helper functions."""
        utils_path = Path(__file__).parent.parent / ".github" / "actions" / "review-utils.js"
        content = utils_path.read_text(encoding='utf-8')

        self.assertIn('MAX_ERROR_CHARS = 500', content)
        self.assertIn('DEFAULT_MAX_PAGES = 10', content)
        self.assertIn('function safeErrorMessage', content)
        self.assertIn('function fetchPrFilesWithPagination', content)
        self.assertIn('function fetchWithRetry', content)
        self.assertIn('function parseJsonResponse', content)

if __name__ == '__main__':
    unittest.main()
