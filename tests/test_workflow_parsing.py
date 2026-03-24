import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


def get_workflow_content(filename):
    """Read and return the contents of a workflow file."""
    workflow_path = Path(__file__).resolve().parents[1] / '.github' / 'workflows' / filename
    return workflow_path.read_text(encoding='utf-8')


def extract_script(workflow_content, step_name):
    """Extract the script block from a specific step in the workflow YAML."""
    if workflow_content is None:
        return None
    try:
        data = yaml.safe_load(workflow_content)
    except yaml.YAMLError:
        return None

    if not data or 'jobs' not in data:
        return None

    for job in data['jobs'].values():
        if 'steps' not in job:
            continue
        for step in job['steps']:
            if step.get('name') == step_name:
                return step.get('with', {}).get('script')
    return None


class TestWorkflowParsing(unittest.TestCase):
    def test_get_workflow_content_exists(self):
        content = get_workflow_content('cleanup-redundant-prs.yml')
        self.assertIn('name: Cleanup Redundant PRs', content)

    def test_extract_script_basic(self):
        yaml_content = """
name: test
jobs:
  job1:
    steps:
      - name: step1
        with:
          script: |
            console.log("hello");
"""
        script = extract_script(yaml_content, 'step1')
        self.assertEqual(script.strip(), 'console.log("hello");')

    def test_extract_script_none_input(self):
        self.assertIsNone(extract_script(None, 'any'))

    def test_extract_script_malformed_yaml(self):
        self.assertIsNone(extract_script("  - invalid: yaml: :", 'any'))

    def test_extract_script_missing_step(self):
        yaml_content = """
name: test
jobs:
  job1:
    steps:
      - name: step1
"""
        self.assertIsNone(extract_script(yaml_content, 'step2'))

    def test_cleanup_workflow_uses_current_github_script(self):
        """Verify the cleanup workflow uses the pinned v8.0.0 hash."""
        content = get_workflow_content('cleanup-redundant-prs.yml')
        # We expect the pinned hash for v8.0.0
        expected_hash = 'ed597411d8f924073f98dfc5c65a23a2325f34cd'
        self.assertIn(f'uses: actions/github-script@{expected_hash}', content)

    def test_cleanup_workflow_embedded_script_parses(self):
        """Extract the script from the workflow and check syntax using node -c."""
        content = get_workflow_content('cleanup-redundant-prs.yml')
        script = extract_script(content, 'Close redundant PRs')

        self.assertIsNotNone(script, "Could not find 'Close redundant PRs' step script")
        self.assertNotEqual(script.strip(), '', 'Script block is empty')

        with tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8') as f:
            f.write(script)
            tmp_path = f.name

        try:
            # Use node -c to check script syntax
            result = subprocess.run(['node', '-c', tmp_path], capture_output=True, text=True, shell=False)
            self.assertEqual(result.returncode, 0, f'JavaScript syntax error in workflow:\n{result.stderr}')
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
