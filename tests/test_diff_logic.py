import unittest

def process_files_to_diff(files):
    """
    Simulates the logic in GitHub Actions to combine file patches into a unified diff.
    """
    return "\n\n".join(
        f"--- {f['filename']}\n+++ {f['filename']}\n{f.get('patch') or '(binary or no changes)'}"
        for f in files
    )

class TestDiffLogic(unittest.TestCase):
    def test_all_scenarios(self):
        test_cases = [
            (
                "multiple_files",
                [
                    {'filename': 'file1.txt', 'patch': '@@ -1 +1 @@\n-old\n+new'},
                    {'filename': 'file2.txt', 'patch': '@@ -2 +2 @@\n-foo\n+bar'}
                ],
                ("--- file1.txt\n+++ file1.txt\n@@ -1 +1 @@\n-old\n+new\n\n"
                 "--- file2.txt\n+++ file2.txt\n@@ -2 +2 @@\n-foo\n+bar")
            ),
            (
                "binary_file",
                [{'filename': 'image.png', 'patch': None}],
                "--- image.png\n+++ image.png\n(binary or no changes)"
            ),
            (
                "no_changes",
                [{'filename': 'empty.txt', 'patch': ''}],
                "--- empty.txt\n+++ empty.txt\n(binary or no changes)"
            ),
            (
                "empty_file_list",
                [],
                ""
            ),
        ]

        for name, files, expected in test_cases:
            with self.subTest(name=name):
                self.assertEqual(process_files_to_diff(files), expected)

if __name__ == '__main__':
    unittest.main()
