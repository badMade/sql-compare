import unittest
from sql_compare import canonicalize_joins, parse_args
import unittest.mock
import sys

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


class TestParseArgs(unittest.TestCase):
    def test_default_args(self):
        args = parse_args([])
        self.assertEqual(args.files, [])
        self.assertIsNone(args.strings)
        self.assertFalse(args.stdin)
        self.assertEqual(args.mode, "both")
        self.assertFalse(args.ignore_whitespace)
        self.assertTrue(args.join_reorder)
        self.assertFalse(args.allow_full_outer_reorder)
        self.assertFalse(args.allow_left_reorder)
        self.assertIsNone(args.report)
        self.assertEqual(args.report_format, "html")

    def test_files_args(self):
        args = parse_args(["file1.sql", "file2.sql"])
        self.assertEqual(args.files, ["file1.sql", "file2.sql"])

    def test_strings_args(self):
        args = parse_args(["--strings", "SELECT 1", "SELECT 2"])
        self.assertEqual(args.strings, ["SELECT 1", "SELECT 2"])

    def test_stdin_args(self):
        args = parse_args(["--stdin"])
        self.assertTrue(args.stdin)

    def test_mode_args(self):
        args = parse_args(["--mode", "exact"])
        self.assertEqual(args.mode, "exact")
        args = parse_args(["--mode", "canonical"])
        self.assertEqual(args.mode, "canonical")

    def test_ignore_whitespace_args(self):
        args = parse_args(["--ignore-whitespace"])
        self.assertTrue(args.ignore_whitespace)

    def test_join_reorder_toggles(self):
        args = parse_args(["--no-join-reorder"])
        self.assertFalse(args.join_reorder)
        args = parse_args(["--join-reorder"])
        self.assertTrue(args.join_reorder)

    def test_allow_reorder_flags(self):
        args = parse_args(["--allow-full-outer-reorder", "--allow-left-reorder"])
        self.assertTrue(args.allow_full_outer_reorder)
        self.assertTrue(args.allow_left_reorder)

    def test_report_args(self):
        args = parse_args(["--report", "out.html", "--report-format", "txt"])
        self.assertEqual(args.report, "out.html")
        self.assertEqual(args.report_format, "txt")

    @unittest.mock.patch('sys.stderr', new_callable=unittest.mock.MagicMock)
    def test_invalid_mode_args(self, mock_stderr):
        with self.assertRaises(SystemExit):
            parse_args(["--mode", "invalid_mode"])

    @unittest.mock.patch('sys.stderr', new_callable=unittest.mock.MagicMock)
    def test_invalid_report_format_args(self, mock_stderr):
        with self.assertRaises(SystemExit):
            parse_args(["--report-format", "invalid_format"])

if __name__ == '__main__':
    unittest.main()
