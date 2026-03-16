import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function and constants to test
import sql_compare
from sql_compare import safe_read_file

class TestSafeReadFile(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = Path(self.test_dir.name)

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    def test_safe_read_file_success(self):
        """Test reading a valid file successfully."""
        test_file = self.test_dir_path / "valid.sql"
        test_content = "SELECT * FROM users;\n"
        test_file.write_text(test_content, encoding="utf-8")

        result = safe_read_file(str(test_file))
        self.assertEqual(result, test_content)

    def test_safe_read_file_not_found(self):
        """Test that FileNotFoundError is raised when file does not exist."""
        non_existent_file = self.test_dir_path / "does_not_exist.sql"

        with self.assertRaises(FileNotFoundError) as context:
            safe_read_file(str(non_existent_file))

        self.assertIn("File not found:", str(context.exception))
        self.assertIn("does_not_exist.sql", str(context.exception))

    @patch('pathlib.Path.stat')
    def test_safe_read_file_too_large(self, mock_stat):
        """Test that ValueError is raised when file size exceeds limit."""
        test_file = self.test_dir_path / "large_file.sql"
        test_file.write_text("dummy content", encoding="utf-8")

        # Configure the mock to return a stat object with a size larger than the limit
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = sql_compare.MAX_FILE_SIZE_BYTES + 1
        mock_stat.return_value = mock_stat_result

        with self.assertRaises(ValueError) as context:
            safe_read_file(str(test_file))

        self.assertIn("File too large:", str(context.exception))
        self.assertIn("large_file.sql", str(context.exception))
        self.assertIn(f"Limit is {sql_compare.MAX_FILE_SIZE_MB} MB", str(context.exception))

    def test_safe_read_file_ignore_encoding_errors(self):
        """Test that invalid UTF-8 bytes are ignored as specified by errors='ignore'."""
        test_file = self.test_dir_path / "invalid_encoding.txt"

        # Write some valid text followed by invalid UTF-8 bytes
        with open(test_file, 'wb') as f:
            f.write(b"Valid text ")
            f.write(b'\xff\xfe\xff') # Invalid UTF-8 sequence
            f.write(b" more valid text")

        result = safe_read_file(str(test_file))

        # The invalid bytes should be ignored/dropped
        self.assertEqual(result, "Valid text  more valid text")

if __name__ == '__main__':
    unittest.main()
