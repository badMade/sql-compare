import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from sql_compare import safe_read_file, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB

class TestSafeReadFile(unittest.TestCase):
    def test_file_not_found(self):
        """Test safe_read_file raises FileNotFoundError if file does not exist."""
        with patch("sql_compare.Path") as MockPath:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            MockPath.return_value = mock_path_instance

            with self.assertRaises(FileNotFoundError):
                safe_read_file("non_existent_file.sql")

    def test_file_too_large(self):
        """Test safe_read_file raises ValueError if file exceeds max size."""
        with patch("sql_compare.Path") as MockPath:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True

            mock_stat = MagicMock()
            mock_stat.st_size = MAX_FILE_SIZE_BYTES + 1
            mock_path_instance.stat.return_value = mock_stat

            MockPath.return_value = mock_path_instance

            with self.assertRaises(ValueError) as context:
                safe_read_file("large_file.sql")

            # Optionally check the error message
            self.assertIn("File too large", str(context.exception))
            self.assertIn(f"Limit is {MAX_FILE_SIZE_MB} MB", str(context.exception))

    def test_file_read_success(self):
        """Test safe_read_file reads and returns file content if size is valid."""
        with patch("sql_compare.Path") as MockPath:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True

            mock_stat = MagicMock()
            mock_stat.st_size = 100 # Within limit
            mock_path_instance.stat.return_value = mock_stat

            mock_path_instance.read_text.return_value = "SELECT 1;"

            MockPath.return_value = mock_path_instance

            result = safe_read_file("valid_file.sql")
            self.assertEqual(result, "SELECT 1;")
            mock_path_instance.read_text.assert_called_once_with(encoding="utf-8", errors="ignore")

if __name__ == '__main__':
    unittest.main()
