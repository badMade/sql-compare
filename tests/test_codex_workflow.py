import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / ".github" / "scripts" / "build-pr-diff.js"


class TestBuildPrDiff(unittest.TestCase):
    def run_builder(self, payload):
        process = subprocess.run(
            ["node", str(SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )
        return process

    def test_combines_multiple_file_patches(self):
        files = [
            {"filename": "a.txt", "patch": "@@\n+line1"},
            {"filename": "dir/b.txt", "patch": "@@\n+line2"},
        ]
        result = self.run_builder(files)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        expected = (
            "--- a.txt\n"
            "+++ a.txt\n"
            "@@\n"
            "+line1\n"
            "\n"
            "--- dir/b.txt\n"
            "+++ dir/b.txt\n"
            "@@\n"
            "+line2"
        )
        self.assertEqual(result.stdout.strip(), expected)

    def test_handles_binary_patch_placeholder(self):
        files = [
            {"filename": "binary.dat", "patch": None},
            {"filename": "text.txt", "patch": "+hello"},
        ]
        result = self.run_builder(files)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        expected = (
            "--- binary.dat\n"
            "+++ binary.dat\n"
            "(binary)\n"
            "\n"
            "--- text.txt\n"
            "+++ text.txt\n"
            "+hello"
        )
        self.assertEqual(result.stdout.strip(), expected)

    def test_rejects_invalid_input(self):
        result = self.run_builder({"not": "a list"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid file list", result.stderr)


if __name__ == "__main__":
    unittest.main()
