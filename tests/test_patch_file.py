import unittest
from unittest.mock import patch, mock_open
import runpy

class TestPatchFile(unittest.TestCase):
    def test_patch_file(self):
        test_cases = [
            (
                "happy_path",
                "Some context.\n**Prevention:** The app was found to be sufficiently secure against standard low-hanging vulnerabilities.\nMore context.",
                "Some context.\n**Prevention:** No vulnerabilities were identified in the evaluated areas before the review was halted.\nMore context."
            ),
            (
                "no_op",
                "Some context.\n**Prevention:** No vulnerabilities were identified in the evaluated areas before the review was halted.\nMore context.",
                "Some context.\n**Prevention:** No vulnerabilities were identified in the evaluated areas before the review was halted.\nMore context."
            )
        ]

        for name, original_content, expected_content in test_cases:
            with self.subTest(name=name):
                m = mock_open(read_data=original_content)
                with patch('builtins.open', m):
                    runpy.run_path('patch_file.py')

                m.assert_any_call('.jules/sentinel.md', 'r', encoding='utf-8')
                m.assert_any_call('.jules/sentinel.md', 'w', encoding='utf-8')

                handle = m()
                handle.write.assert_called_with(expected_content)

if __name__ == '__main__':
    unittest.main()
