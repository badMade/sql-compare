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
    def test_combine_multiple_files(self):
        files = [
            {'filename': 'file1.txt', 'patch': '@@ -1 +1 @@\n-old\n+new'},
            {'filename': 'file2.txt', 'patch': '@@ -2 +2 @@\n-foo\n+bar'}
        ]
        expected = (
            "--- file1.txt\n+++ file1.txt\n@@ -1 +1 @@\n-old\n+new\n\n"
            "--- file2.txt\n+++ file2.txt\n@@ -2 +2 @@\n-foo\n+bar"
        )
        self.assertEqual(process_files_to_diff(files), expected)

    def test_handle_binary_file(self):
        files = [
            {'filename': 'image.png', 'patch': None}
        ]
        expected = "--- image.png\n+++ image.png\n(binary or no changes)"
        self.assertEqual(process_files_to_diff(files), expected)

    def test_handle_no_changes(self):
        files = [
            {'filename': 'empty.txt', 'patch': ''}
        ]
        expected = "--- empty.txt\n+++ empty.txt\n(binary or no changes)"
        self.assertEqual(process_files_to_diff(files), expected)

    def test_empty_file_list(self):
        self.assertEqual(process_files_to_diff([]), "")

if __name__ == '__main__':
    unittest.main()
