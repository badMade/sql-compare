import unittest
import yaml
from pathlib import Path


class TestWorkflowSecurity(unittest.TestCase):
    """Security-focused checks for workflow scripts and shared helpers."""

    def setUp(self):
        """Load workflow YAML and shared utilities once for reuse."""
        repo_root = Path(__file__).parent.parent
        self.workflows_dir = repo_root / ".github" / "workflows"
        self.review_utils_path = repo_root / ".github" / "actions" / "review-utils.js"
        self.review_utils_text = self.review_utils_path.read_text(encoding="utf-8")
        self.codex_workflow = self._load_workflow("codex.yml")
        self.jules_workflow = self._load_workflow("jules.yml")

    def _load_workflow(self, filename):
        """Load and parse a workflow file."""
        workflow_path = self.workflows_dir / filename
        with open(workflow_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _get_script_from_step(self, workflow, step_name):
        """Extract the github-script 'script' block from a named step."""
        for job in workflow.get("jobs", {}).values():
            for step in job.get("steps", []):
                if step.get("name") == step_name:
                    return step.get("with", {}).get("script", "")
        return ""

    def test_shared_utils_define_parse_json_response(self):
        """parseJsonResponse should be defined, non-async, and include status/context details."""
        self.assertIn("function parseJsonResponse", self.review_utils_text)
        self.assertNotIn("async function parseJsonResponse", self.review_utils_text)
        self.assertIn("response.status", self.review_utils_text)
        self.assertIn("content-type", self.review_utils_text.lower())

    def test_review_steps_validate_json_and_include_status(self):
        """Review steps should guard JSON parsing and surface response status."""
        scenarios = [
            ("codex", self.codex_workflow, "Review with Codex"),
            ("jules", self.jules_workflow, "Review with Jules (Gemini)"),
        ]
        for name, workflow, step_name in scenarios:
            script = self._get_script_from_step(workflow, step_name)
            self.assertTrue(script, f"Could not find '{step_name}' step in {name}")
            self.assertIn("parseJsonResponse", script, f"{name} should parse responses safely")
            self.assertIn("non-JSON response", script, f"{name} should report non-JSON responses")
            self.assertIn("status", script, f"{name} should surface response status in errors")
            self.assertIn("safeReadBody", script, f"{name} should include safeReadBody for errors")

    def test_jobs_require_internal_repo_and_safe_label(self):
        """PR-triggered workflows should stay internal and require safety label."""
        for name, workflow in [("codex", self.codex_workflow), ("jules", self.jules_workflow)]:
            job = next(iter(workflow.get("jobs", {}).values()))
            condition = job.get("if", "")
            self.assertIn("safe-for-ai-review", condition, f"{name} must require safety label")
            self.assertIn("head.repo.full_name == github.repository", condition,
                          f"{name} must restrict to internal PRs")

    def test_get_diff_steps_use_shared_helpers(self):
        """Both workflows should rely on shared utilities for diff fetching and errors."""
        for name, workflow in [("codex", self.codex_workflow), ("jules", self.jules_workflow)]:
            script = self._get_script_from_step(workflow, "Get PR diff")
            self.assertTrue(script, f"Could not find 'Get PR diff' step in {name}")
            self.assertIn("fetchPrFilesWithPagination", script,
                          f"{name} should use pagination helper")
            self.assertIn("safeErrorMessage", script, f"{name} should log via safeErrorMessage")
            self.assertIn("parsePrNumber", script, f"{name} should validate PR number parsing")

    def test_review_steps_configure_retry_settings(self):
        """Review steps should provide explicit retry settings to fetchWithRetry."""
        for name, workflow, step_name in [
            ("codex", self.codex_workflow, "Review with Codex"),
            ("jules", self.jules_workflow, "Review with Jules (Gemini)"),
        ]:
            script = self._get_script_from_step(workflow, step_name)
            self.assertTrue(script, f"Could not find '{step_name}' step in {name}")
            self.assertIn("fetchWithRetry", script, f"{name} should wrap API calls with retries")
            self.assertIn("retries", script, f"{name} should set a retry count")
            self.assertIn("delayMs", script, f"{name} should set a retry delay")
            self.assertIn("parseJsonResponse", script, f"{name} should parse JSON responses safely")


if __name__ == "__main__":
    unittest.main()
