import unittest
import yaml
import subprocess
import shutil
from pathlib import Path

def get_workflow_content(filename):
    repo_root = Path(__file__).parent.parent
    workflow_path = repo_root / '.github' / 'workflows' / filename
    with open(workflow_path, 'r') as f:
        return yaml.safe_load(f)

def extract_script(workflow_content, step_name):
    for job in workflow_content.get('jobs', {}).values():
        for step in job.get('steps', []):
            if step.get('name') == step_name:
                return step.get('with', {}).get('script')
    return None

class TestWorkflowParsing(unittest.TestCase):
    def test_codex_workflow(self):
        content = get_workflow_content('codex.yml')

        # Test if condition for manual mentions in PR
        job_if = content.get('jobs', {}).get('codex-review', {}).get('if', '')
        self.assertIn("contains(github.event.pull_request.body, '@codex')", job_if)
        self.assertIn("contains(github.event.pull_request.title, '@codex')", job_if)

        # Test Get PR diff script
        diff_script = extract_script(content, 'Get PR diff')
        self.assertIsNotNone(diff_script)
        self.assertIn('const fail =', diff_script)
        self.assertIn('github.rest.pulls.get', diff_script)
        self.assertIn('page <= 10', diff_script)
        self.validate_js_syntax(diff_script)

        # Test Review with Codex script
        review_script = extract_script(content, 'Review with Codex')
        self.assertIsNotNone(review_script)
        self.assertIn('const fail =', review_script)
        self.assertIn('process.env.PR_TITLE', review_script)
        self.assertIn('process.env.PR_BODY', review_script)
        self.validate_js_syntax(review_script)

    def test_jules_workflow(self):
        content = get_workflow_content('jules.yml')

        # Test if condition for manual mentions in PR
        job_if = content.get('jobs', {}).get('jules-review', {}).get('if', '')
        self.assertIn("contains(github.event.pull_request.body, '@jules')", job_if)
        self.assertIn("contains(github.event.pull_request.title, '@jules')", job_if)

        # Test Get PR diff script
        diff_script = extract_script(content, 'Get PR diff')
        self.assertIsNotNone(diff_script)
        self.assertIn('const fail =', diff_script)
        self.assertIn('github.rest.pulls.get', diff_script)
        self.assertIn('page <= 10', diff_script)
        self.validate_js_syntax(diff_script)

        # Test Review with Jules script
        review_script = extract_script(content, 'Review with Jules (Gemini)')
        self.assertIsNotNone(review_script)
        self.assertIn('const fail =', review_script)
        self.assertIn('process.env.PR_TITLE', review_script)
        self.assertIn('process.env.PR_BODY', review_script)
        self.validate_js_syntax(review_script)

    def validate_js_syntax(self, script_content):
        node_path = shutil.which('node')
        if not node_path:
            self.skipTest("node not found, skipping JS syntax validation")

        # Wrap in async function for syntax check because github-script does this
        wrapped_script = f"async function main() {{\n{script_content}\n}}"

        # Use node -c to check syntax
        process = subprocess.run(
            [node_path, '-c'],
            input=wrapped_script,
            text=True,
            capture_output=True,
            shell=False
        )
        if process.returncode != 0:
            self.fail(f"JS syntax error in script:\n{process.stderr}")

if __name__ == '__main__':
    unittest.main()
