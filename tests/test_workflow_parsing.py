import unittest
import yaml
import tempfile
import shutil
from pathlib import Path

def extract_workflow_script(workflow_content, step_name):
    """
    Securely parses workflow YAML content and extracts the 'script' property
    from a step matching step_name.
    """
    if workflow_content is None:
        return None
    try:
        data = yaml.safe_load(workflow_content)
    except (yaml.YAMLError, TypeError, AttributeError):
        return None

    if not data or not isinstance(data, dict) or 'jobs' not in data:
        return None

    for job_id, job in data['jobs'].items():
        if not isinstance(job, dict) or 'steps' not in job:
            continue
        for step in job['steps']:
            if not isinstance(step, dict):
                continue
            if step.get('name') == step_name:
                return step.get('with', {}).get('script')
    return None

class TestWorkflowParsing(unittest.TestCase):
    def test_cleanup_workflow_embedded_script_parses(self):
        """Test that the embedded script in a mock workflow parses correctly using a temporary directory."""
        workflow_yaml = """
name: Test Workflow
on: [push]
jobs:
  test_job:
    runs-on: ubuntu-latest
    steps:
      - name: My Step
        uses: actions/github-script@v8
        with:
          script: |
            console.log("Hello, World!");
            return true;
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wf_path = Path(tmpdir) / "workflow.yml"
            wf_path.write_text(workflow_yaml, encoding="utf-8")

            with open(wf_path, "r", encoding="utf-8") as f:
                content = f.read()

            script = extract_workflow_script(content, "My Step")
            self.assertEqual(script.strip(), 'console.log("Hello, World!");\nreturn true;')

    def test_extract_script_missing_step(self):
        """Test behavior when the specified step name is missing."""
        workflow_yaml = """
jobs:
  job1:
    steps:
      - name: Existing Step
        with:
          script: print(1)
"""
        script = extract_workflow_script(workflow_yaml, "Non-existent Step")
        self.assertIsNone(script)

    def test_extract_script_invalid_yaml(self):
        """Test behavior with malformed YAML."""
        invalid_yaml = """
jobs:
  job1:
    steps:
      - name: Step 1
      - [unbalanced bracket
"""
        script = extract_workflow_script(invalid_yaml, "Step 1")
        self.assertIsNone(script)

    def test_robustness_with_none_input(self):
        """Test robustness when input is None."""
        self.assertIsNone(extract_workflow_script(None, "Any Step"))

    def test_robustness_with_non_dict_yaml(self):
        """Test robustness when YAML parses to non-dict (e.g., list)."""
        self.assertIsNone(extract_workflow_script("- item1\n- item2", "Any Step"))

    def test_negative_script_tag_missing(self):
        """Test case where 'with' or 'script' tag is missing in the step."""
        workflow_yaml = """
jobs:
  job1:
    steps:
      - name: Step No With
      - name: Step No Script
        with:
          other: value
"""
        self.assertIsNone(extract_workflow_script(workflow_yaml, "Step No With"))
        self.assertIsNone(extract_workflow_script(workflow_yaml, "Step No Script"))

    def test_negative_empty_workflow(self):
        """Test behavior with an empty workflow file."""
        self.assertIsNone(extract_workflow_script("", "Any Step"))


class TestReviewWorkflows(unittest.TestCase):
    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.codex_workflow = (repo_root / ".github" / "workflows" / "codex.yml").read_text(encoding="utf-8")
        self.jules_workflow = (repo_root / ".github" / "workflows" / "jules.yml").read_text(encoding="utf-8")

    def test_workflows_use_shared_utils(self):
        """Ensure Codex and Jules workflows import the shared review utilities."""
        required_import = "require('./.github/actions/review-utils')"
        self.assertIn(required_import, self.codex_workflow)
        self.assertIn(required_import, self.jules_workflow)

    def test_workflows_use_safe_error_handling(self):
        """Both workflows should use the shared safeErrorMessage helper."""
        helper_call = "safeErrorMessage"
        self.assertIn(helper_call, self.codex_workflow)
        self.assertIn(helper_call, self.jules_workflow)

    def test_workflows_guard_json_parsing(self):
        """
        Workflows should guard JSON parsing by checking Content-Type or using
        a helper instead of blindly calling response.json()/text().
        """
        json_guard_marker = "isJsonResponse"
        self.assertIn(json_guard_marker, self.codex_workflow)
        self.assertIn(json_guard_marker, self.jules_workflow)

    def test_workflows_fetch_pr_object_before_outputs(self):
        """
        Both workflows must fetch the PR object via github.rest.pulls.get()
        in the 'Get PR diff' step and set pr_title / pr_body outputs after it.
        """
        pr_fetch = "github.rest.pulls.get("
        pr_title_output = "core.setOutput('pr_title', pr.title)"
        pr_body_output = "core.setOutput('pr_body', pr.body)"
        for name, content in (("codex", self.codex_workflow), ("jules", self.jules_workflow)):
            script = extract_workflow_script(content, "Get PR diff")
            self.assertIsNotNone(script, f"{name}.yml: 'Get PR diff' step not found")
            self.assertIn(pr_fetch, script, f"{name}.yml: 'Get PR diff' missing github.rest.pulls.get() call")
            self.assertIn(pr_title_output, script, f"{name}.yml: 'Get PR diff' missing pr_title output")
            self.assertIn(pr_body_output, script, f"{name}.yml: 'Get PR diff' missing pr_body output")
            # Verify ordering: API fetch must appear before the output assignments
            fetch_pos = script.index(pr_fetch)
            title_pos = script.index(pr_title_output)
            body_pos = script.index(pr_body_output)
            self.assertLess(fetch_pos, title_pos,
                            f"{name}.yml: github.rest.pulls.get() must precede pr_title output")
            self.assertLess(fetch_pos, body_pos,
                            f"{name}.yml: github.rest.pulls.get() must precede pr_body output")

if __name__ == '__main__':
    unittest.main()
