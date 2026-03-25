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
        self.assertIn('formatError', script, "Missing formatError helper function")
        self.assertIn('validatePrNumber', script, "Missing validatePrNumber helper function")

        # Check for improved logging
        self.assertIn('core.error', script, "Should use core.error for error logging")
        self.assertIn('core.info', script, "Should use core.info for info logging")

    def test_codex_has_pagination_limit(self):
        """Test that codex.yml has pagination limits to prevent infinite loops."""
        script = self._get_script_from_step(self.codex_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for MAX_PAGES constant
        self.assertIn('MAX_PAGES', script, "Missing MAX_PAGES pagination limit")
        self.assertIn('while (page <= MAX_PAGES)', script, "Pagination should have upper bound")

    def test_codex_review_has_retry_logic(self):
        """Test that codex.yml review step includes retry logic."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for retry function
        self.assertIn('fetchWithRetry', script, "Missing fetchWithRetry helper function")
        self.assertIn('maxRetries', script, "Retry logic should have maxRetries parameter")

    def test_codex_review_validates_content_type(self):
        """Test that codex.yml validates content-type before parsing JSON."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for content-type validation
        self.assertIn('parseJsonResponse', script, "Missing parseJsonResponse helper function")
        self.assertIn('content-type', script, "Should validate content-type header")

    def test_codex_review_truncates_errors(self):
        """Test that codex.yml truncates error messages to prevent sensitive data exposure."""
        script = self._get_script_from_step(self.codex_workflow, 'Review with Codex')
        self.assertIsNotNone(script, "Could not find 'Review with Codex' step")

        # Check for error truncation
        self.assertIn('truncate', script.lower(), "Should truncate error messages")
        self.assertIn('substring', script, "Should use substring to limit error length")

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
        self.assertIn('formatError', script, "Missing formatError helper function")
        self.assertIn('validatePrNumber', script, "Missing validatePrNumber helper function")

    def test_jules_has_pagination_limit(self):
        """Test that jules.yml has pagination limits to prevent infinite loops."""
        script = self._get_script_from_step(self.jules_workflow, 'Get PR diff')
        self.assertIsNotNone(script, "Could not find 'Get PR diff' step")

        # Check for MAX_PAGES constant
        self.assertIn('MAX_PAGES', script, "Missing MAX_PAGES pagination limit")
        self.assertIn('while (page <= MAX_PAGES)', script, "Pagination should have upper bound")

    def test_jules_review_has_retry_logic(self):
        """Test that jules.yml review step includes retry logic."""
        script = self._get_script_from_step(self.jules_workflow, 'Review with Jules (Gemini)')
        self.assertIsNotNone(script, "Could not find 'Review with Jules (Gemini)' step")

        # Check for retry function
        self.assertIn('fetchWithRetry', script, "Missing fetchWithRetry helper function")
        self.assertIn('maxRetries', script, "Retry logic should have maxRetries parameter")

    def test_jules_review_validates_content_type(self):
        """Test that jules.yml validates content-type before parsing JSON."""
        script = self._get_script_from_step(self.jules_workflow, 'Review with Jules (Gemini)')
        self.assertIsNotNone(script, "Could not find 'Review with Jules (Gemini)' step")

        # Check for content-type validation
        self.assertIn('parseJsonResponse', script, "Missing parseJsonResponse helper function")
        self.assertIn('content-type', script, "Should validate content-type header")

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

            # Check for formatError usage in catch
            self.assertIn('formatError', script, f"{workflow_name}/{step_name} should use formatError")

    def test_pr_number_validation_consistency(self):
        """Test that PR number validation is consistent across workflows."""
        for workflow_name, workflow in [('codex', self.codex_workflow), ('jules', self.jules_workflow)]:
            script = self._get_script_from_step(workflow, 'Get PR diff')
            self.assertIsNotNone(script, f"Could not find 'Get PR diff' step in {workflow_name}")

            # Check for validatePrNumber helper
            self.assertIn('validatePrNumber', script,
                         f"{workflow_name} should use validatePrNumber helper")
            self.assertIn('parseInt', script,
                         f"{workflow_name} should parse PR number")
            self.assertIn('Number.isInteger', script,
                         f"{workflow_name} should validate integer")

class TestWorkflowIfConditions(unittest.TestCase):
    """Tests that verify the job-level 'if' conditions behave correctly."""

    def setUp(self):
        """Load workflow files."""
        self.workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"
        self.codex_workflow = self._load_workflow("codex.yml")
        self.jules_workflow = self._load_workflow("jules.yml")

    def _load_workflow(self, filename):
        workflow_path = self.workflows_dir / filename
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_job_if(self, workflow, job_name):
        """Return the 'if' expression string for a given job."""
        job = workflow.get('jobs', {}).get(job_name)
        if job is None:
            return None
        return job.get('if', '')

    def _get_pr_event_branch(self, condition):
        """Extract the pull_request event branch from the job 'if' condition.

        Top-level OR groups are delimited by ') || (' so we split on that
        pattern and identify the branch that contains 'pull_request' as the
        event name (not as part of 'pull_request_review_comment').
        """
        # Split on the top-level OR separator used in both workflow files
        branches = condition.split(') || (')
        pr_branches = [
            b for b in branches
            if "github.event_name == 'pull_request'" in b
            and "github.event_name == 'pull_request_review_comment'" not in b
        ]
        return pr_branches[0] if pr_branches else None

    def test_codex_pull_request_does_not_require_label(self):
        """pull_request events on internal PRs must run without the safe-for-ai-review label."""
        condition = self._get_job_if(self.codex_workflow, 'codex-review')
        self.assertIsNotNone(condition)
        pr_branch = self._get_pr_event_branch(condition)
        self.assertIsNotNone(pr_branch, "Could not locate pull_request branch in codex if-condition")
        self.assertNotIn('safe-for-ai-review', pr_branch,
                         "pull_request branch must not require 'safe-for-ai-review' label; "
                         "it was causing internal PRs to be skipped.")

    def test_jules_pull_request_does_not_require_label(self):
        """pull_request events on internal PRs must run without the safe-for-ai-review label."""
        condition = self._get_job_if(self.jules_workflow, 'jules-review')
        self.assertIsNotNone(condition)
        pr_branch = self._get_pr_event_branch(condition)
        self.assertIsNotNone(pr_branch, "Could not locate pull_request branch in jules if-condition")
        self.assertNotIn('safe-for-ai-review', pr_branch,
                         "pull_request branch must not require 'safe-for-ai-review' label; "
                         "it was causing internal PRs to be skipped.")

    def test_codex_pull_request_requires_internal_repo(self):
        """pull_request events must still require head.repo == current repo (security)."""
        condition = self._get_job_if(self.codex_workflow, 'codex-review')
        pr_branch = self._get_pr_event_branch(condition)
        self.assertIsNotNone(pr_branch, "Could not locate pull_request branch")
        self.assertIn('head.repo.full_name == github.repository', pr_branch,
                      "pull_request branch must still check head.repo to block fork PRs.")

    def test_jules_pull_request_requires_internal_repo(self):
        """pull_request events must still require head.repo == current repo (security)."""
        condition = self._get_job_if(self.jules_workflow, 'jules-review')
        pr_branch = self._get_pr_event_branch(condition)
        self.assertIsNotNone(pr_branch, "Could not locate pull_request branch")
        self.assertIn('head.repo.full_name == github.repository', pr_branch,
                      "pull_request branch must still check head.repo to block fork PRs.")

    def test_codex_issue_comment_still_requires_label(self):
        """issue_comment trigger must keep the safe-for-ai-review label requirement."""
        condition = self._get_job_if(self.codex_workflow, 'codex-review')
        self.assertIsNotNone(condition)
        # The full condition must still contain the label check somewhere
        # (used by issue_comment and pull_request_review_comment branches)
        self.assertIn('safe-for-ai-review', condition,
                      "The 'if' condition must still contain 'safe-for-ai-review' "
                      "for issue_comment / pull_request_review_comment branches.")
        # Verify it is NOT in the pull_request branch specifically
        pr_branch = self._get_pr_event_branch(condition)
        self.assertNotIn('safe-for-ai-review', pr_branch,
                         "Label check must NOT be in the pull_request branch.")

    def test_jules_issue_comment_still_requires_label(self):
        """issue_comment trigger must keep the safe-for-ai-review label requirement."""
        condition = self._get_job_if(self.jules_workflow, 'jules-review')
        self.assertIsNotNone(condition)
        self.assertIn('safe-for-ai-review', condition,
                      "The 'if' condition must still contain 'safe-for-ai-review' "
                      "for issue_comment / pull_request_review_comment branches.")
        pr_branch = self._get_pr_event_branch(condition)
        self.assertNotIn('safe-for-ai-review', pr_branch,
                         "Label check must NOT be in the pull_request branch.")


if __name__ == '__main__':
    unittest.main()
