import unittest
from sql_compare import canonicalize_joins

class TestCanonicalizeJoins(unittest.TestCase):
    def test_basic_inner_join_reorder(self):
        """Inner joins should be reordered alphabetically by table name."""
        sql = "SELECT * FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_explicit_inner_join_reorder(self):
        """INNER JOIN keywords should be treated same as JOIN."""
        sql = "SELECT * FROM t1 INNER JOIN t3 ON t1.id=t3.id INNER JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_left_join_no_reorder(self):
        """Left joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_left_join_allow_reorder(self):
        """Left joins SHOULD be reordered if allow_left is True."""
        sql = "SELECT * FROM t1 LEFT JOIN t3 ON t1.id=t3.id LEFT JOIN t2 ON t1.id=t2.id"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON t1.id=t2.id LEFT JOIN t3 ON t1.id=t3.id"
        self.assertEqual(canonicalize_joins(sql, allow_left=True), expected)

    def test_mixed_joins_barrier(self):
        """Reorderable joins should not cross non-reorderable join barriers."""
        # t3 and t2 are INNER (reorderable), t4 is LEFT (barrier)
        sql = "SELECT * FROM t1 JOIN t3 ON x JOIN t2 ON y LEFT JOIN t4 ON z"
        # t3 and t2 should swap.
        expected = "SELECT * FROM t1 JOIN t2 ON y JOIN t3 ON x LEFT JOIN t4 ON z"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_mixed_joins_barrier_2(self):
        """Reorderable joins should not cross non-reorderable join barriers (case 2)."""
        # t1 -> LEFT t2 -> JOIN t4 -> JOIN t3
        # t4 and t3 are after the barrier t2. They should be reordered among themselves.
        sql = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t4 ON y JOIN t3 ON z"
        expected = "SELECT * FROM t1 LEFT JOIN t2 ON x JOIN t3 ON z JOIN t4 ON y"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_full_outer_join_no_reorder(self):
        """FULL OUTER joins should NOT be reordered by default."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        self.assertEqual(canonicalize_joins(sql), sql)

    def test_full_outer_join_allow_reorder(self):
        """FULL OUTER joins SHOULD be reordered if allow_full_outer is True."""
        sql = "SELECT * FROM t1 FULL JOIN t3 ON x FULL JOIN t2 ON y"
        # Note: 'FULL JOIN' is normalized to 'FULL JOIN' (OUTER is optional/removed if not handled?)
        # Let's check implementation: seg_type replaces " OUTER", so "FULL OUTER JOIN" -> "FULL JOIN".
        # Then _rebuild uses seg_type + " JOIN". So "FULL JOIN".
        # If input has "FULL OUTER JOIN", output will have "FULL JOIN".
        # We should expect "FULL JOIN".
        expected = "SELECT * FROM t1 FULL JOIN t2 ON y FULL JOIN t3 ON x"
        # However, if input is already "FULL JOIN", it stays "FULL JOIN".
        self.assertEqual(canonicalize_joins(sql, allow_full_outer=True), expected)

    def test_cross_join_reorder(self):
        """CROSS JOIN should be reordered."""
        sql = "SELECT * FROM t1 CROSS JOIN t3 CROSS JOIN t2"
        expected = "SELECT * FROM t1 CROSS JOIN t2 CROSS JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_natural_join_reorder(self):
        """NATURAL JOIN should be reordered."""
        sql = "SELECT * FROM t1 NATURAL JOIN t3 NATURAL JOIN t2"
        expected = "SELECT * FROM t1 NATURAL JOIN t2 NATURAL JOIN t3"
        self.assertEqual(canonicalize_joins(sql), expected)

import unittest
from unittest.mock import patch, MagicMock

# This assumes we will append this to tests/test_sql_compare.py
from sql_compare import load_inputs

class TestLoadInputs(unittest.TestCase):
    def test_load_inputs_strings(self):
        """Test load_inputs when args.strings is provided."""
        args = MagicMock()
        args.strings = ["SELECT 1", "SELECT 2"]
        args.stdin = False
        args.files = None

        a, b, mode = load_inputs(args)

        self.assertEqual(a, "SELECT 1")
        self.assertEqual(b, "SELECT 2")
        self.assertEqual(mode, "strings")

    @patch('sql_compare.read_from_stdin_two_parts')
    def test_load_inputs_stdin(self, mock_read_from_stdin):
        """Test load_inputs when args.stdin is true."""
        args = MagicMock()
        args.strings = None
        args.stdin = True
        args.files = None

        mock_read_from_stdin.return_value = ("SELECT A", "SELECT B")

        a, b, mode = load_inputs(args)

        self.assertEqual(a, "SELECT A")
        self.assertEqual(b, "SELECT B")
        self.assertEqual(mode, "stdin")
        mock_read_from_stdin.assert_called_once()

    @patch('sql_compare.safe_read_file')
    def test_load_inputs_files(self, mock_safe_read_file):
        """Test load_inputs when args.files is provided with exactly 2 files."""
        args = MagicMock()
        args.strings = None
        args.stdin = False
        args.files = ["file1.sql", "file2.sql"]

        mock_safe_read_file.side_effect = ["SELECT F1", "SELECT F2"]

        a, b, mode = load_inputs(args)

        self.assertEqual(a, "SELECT F1")
        self.assertEqual(b, "SELECT F2")
        self.assertEqual(mode, "files")
        self.assertEqual(mock_safe_read_file.call_count, 2)
        mock_safe_read_file.assert_any_call("file1.sql")
        mock_safe_read_file.assert_any_call("file2.sql")

    def test_load_inputs_none(self):
        """Test load_inputs when no valid arguments are provided."""
        args = MagicMock()
        args.strings = None
        args.stdin = False
        args.files = None

        a, b, mode = load_inputs(args)

        self.assertIsNone(a)
        self.assertIsNone(b)
        self.assertIsNone(mode)

    def test_load_inputs_invalid_files_length(self):
        """Test load_inputs when args.files does not contain exactly 2 files."""
        for file_list in ([], ["file1.sql"], ["f1.sql", "f2.sql", "f3.sql"]):
            with self.subTest(files=file_list):
                args = MagicMock()
                args.strings = None
                args.stdin = False
                args.files = file_list

                a, b, mode = load_inputs(args)

                self.assertIsNone(a)
                self.assertIsNone(b)
                self.assertIsNone(mode)


if __name__ == '__main__':
    unittest.main()
