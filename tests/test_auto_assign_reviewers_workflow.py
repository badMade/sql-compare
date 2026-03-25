import unittest
from pathlib import Path
import yaml


class TestAutoAssignReviewersWorkflow(unittest.TestCase):
    """Ensure the auto-assign reviewers workflow targets valid individual reviewers."""

    def setUp(self):
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "auto-assign-reviewers.yml"
        with open(workflow_path, "r", encoding="utf-8") as f:
            self.workflow = yaml.safe_load(f)

    def _get_request_reviewers_script(self):
        job = self.workflow["jobs"]["assign-reviewers"]
        steps = job.get("steps", [])
        for step in steps:
            if step.get("name") == "Request reviewers":
                return step.get("with", {}).get("script", "")
        return ""

    def test_uses_individual_reviewers_not_teams(self):
        """The workflow should request individual reviewers instead of non-collaborator teams."""
        script = self._get_request_reviewers_script()

        self.assertIn("const reviewers", script)
        self.assertIn("reviewers:", script)
        self.assertNotIn("team_reviewers", script)
        self.assertNotIn("teamReviewers", script)

    def test_uses_defined_pull_number_variable(self):
        """The requestReviewers call should reference the defined PR number variable."""
        script = self._get_request_reviewers_script()

        self.assertIn("const prNumber = context.payload.pull_request", script)
        self.assertIn("pull_number: prNumber", script)


if __name__ == "__main__":
    unittest.main()
