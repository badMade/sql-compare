import re
import shutil
import subprocess
import unittest
from pathlib import Path


def get_workflow_content(filename):
    repo_root = Path(__file__).parent.parent
    workflow_path = repo_root / '.github' / 'workflows' / filename
    return workflow_path.read_text(encoding='utf-8')


def extract_job_if(workflow_content, job_name):
    match = re.search(
        rf"^  {re.escape(job_name)}:\n(?:^[ \t].*\n)*?^    if: \|\n(?P<body>(?:^      .*\n)+)",
        workflow_content,
        re.MULTILINE,
    )
    return match.group('body') if match else ''


def extract_script(workflow_content, step_name):
    marker = f"- name: {step_name}"
    marker_index = workflow_content.find(marker)
    if marker_index == -1:
        return None

    script_marker = "\n          script: |\n"
    script_start = workflow_content.find(script_marker, marker_index)
    if script_start == -1:
        return None

    content_start = script_start + len(script_marker)
    lines = []
    for line in workflow_content[content_start:].splitlines(keepends=True):
        if line.startswith('            '):
            lines.append(line[12:])
            continue
        if line.strip() == '':
            lines.append('\n')
            continue
        break

    script = ''.join(lines).rstrip('\n')
    return script or None


class TestWorkflowParsing(unittest.TestCase):
    def test_ai_workflows(self):
        scenarios = [
            {
                "filename": "codex.yml",
                "job_name": "codex-review",
                "mention": "@codex",
                "review_step_name": "Review with Codex",
            },
            {
                "filename": "jules.yml",
                "job_name": "jules-review",
                "mention": "@jules",
                "review_step_name": "Review with Jules (Gemini)",
            },
        ]

        for params in scenarios:
            with self.subTest(workflow=params["filename"]):
                content = get_workflow_content(params["filename"])

                # Test if condition for manual mentions in PR
                job_if = content.get('jobs', {}).get(params["job_name"], {}).get('if', '')
                self.assertIn(f"contains(github.event.pull_request.body, '{params['mention']}')", job_if)
                self.assertIn(f"contains(github.event.pull_request.title, '{params['mention']}')", job_if)

                # Test Get PR diff script
                diff_script = extract_script(content, 'Get PR diff')
                self.assertIsNotNone(diff_script)
                self.assertIn('const fail =', diff_script)
                self.assertIn('github.rest.pulls.get', diff_script)
                self.assertIn('page <= 10', diff_script)
                self.validate_js_syntax(diff_script)

                # Test Review script
                review_script = extract_script(content, params["review_step_name"])
                self.assertIsNotNone(review_script)
                self.assertIn('const fail =', review_script)
                self.assertIn('process.env.PR_TITLE', review_script)
                self.assertIn('process.env.PR_BODY', review_script)
                self.validate_js_syntax(review_script)

    def validate_js_syntax(self, script_content):
        node_path = shutil.which('node')
        if not node_path:
            self.skipTest('node not found, skipping JS syntax validation')

        # Wrap in async function for syntax check because github-script does this
        wrapped_script = f"async function main() {{\n{script_content}\n}}"

        # Use node -c to check syntax
        process = subprocess.run(
            [node_path, '-c'],
            input=wrapped_script,
            text=True,
            capture_output=True,
            shell=False,
        )
        if process.returncode != 0:
            self.fail(f"JS syntax error in script:\n{process.stderr}")


if __name__ == '__main__':
    unittest.main()
