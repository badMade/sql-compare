import unittest
from unittest.mock import patch
import sql_compare

class TestSentinelDosFix(unittest.TestCase):
    @patch('sys.stdin')
    def test_read_from_stdin_two_parts_exceeds_limit(self, mock_stdin):
        # Mock sys.stdin.read to return a string slightly larger than the limit
        mock_stdin.read.return_value = 'A' * (sql_compare.MAX_FILE_SIZE_BYTES + 1)

        with self.assertRaises(ValueError) as context:
            sql_compare.read_from_stdin_two_parts()

        self.assertIn("Standard input too large", str(context.exception))

    @patch('sys.stdin')
    def test_read_from_stdin_two_parts_within_limit(self, mock_stdin):
        # Mock valid input with '---' separator
        mock_stdin.read.return_value = 'SELECT 1;\n---\nSELECT 2;'

        part1, part2 = sql_compare.read_from_stdin_two_parts()
        self.assertEqual(part1, 'SELECT 1;')
        self.assertEqual(part2, 'SELECT 2;')

if __name__ == '__main__':
    unittest.main()
