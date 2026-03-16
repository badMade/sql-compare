import unittest
from unittest.mock import patch, mock_open
import runpy

class TestPatchFile(unittest.TestCase):
    def test_patch_file_happy_path(self):
        original_content = "Some context.\n**Prevention:** The app was found to be sufficiently secure against standard low-hanging vulnerabilities.\nMore context."
        expected_content = "Some context.\n**Prevention:** No vulnerabilities were identified in the evaluated areas before the review was halted.\nMore context."

        m = mock_open(read_data=original_content)
        with patch('builtins.open', m):
            runpy.run_path('patch_file.py')

        m.assert_any_call('.jules/sentinel.md', 'r', encoding='utf-8')
        m.assert_any_call('.jules/sentinel.md', 'w', encoding='utf-8')

        handle = m()
        handle.write.assert_called_with(expected_content)

    def test_patch_file_no_op(self):
        original_content = "Some context.\n**Prevention:** No vulnerabilities were identified in the evaluated areas before the review was halted.\nMore context."

        m = mock_open(read_data=original_content)
        with patch('builtins.open', m):
            runpy.run_path('patch_file.py')

        handle = m()
        handle.write.assert_called_with(original_content)

if __name__ == '__main__':
    unittest.main()
