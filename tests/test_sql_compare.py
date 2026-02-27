import unittest
import sys
import os
import re

# Add parent directory to path to import sql_compare
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sql_compare import canonicalize_joins, normalize_sql, collapse_whitespace

class TestCanonicalizeJoins(unittest.TestCase):

    def test_no_joins(self):
        sql = "SELECT * FROM mytable"
        expected = collapse_whitespace(sql)
        self.assertEqual(canonicalize_joins(sql), expected)

    def test_inner_joins_reordering(self):
        # A, B, C should be sorted alphabetically -> A, B, C
        # But wait, the function sorts by (type, table, cond_kw, cond).
        # Let's use tables C, A, B to see if they get sorted to A, B, C.

        # Original: FROM T1 JOIN C ON c.id=1 JOIN A ON a.id=1 JOIN B ON b.id=1
        # The first table T1 is the "base" and is not part of the reordering segments.
        # So we are reordering C, A, B.

        sql = "SELECT * FROM T1 JOIN C ON C.id=T1.id JOIN A ON A.id=T1.id JOIN B ON B.id=T1.id"
        # Expected: A, B, C sorted
        expected_part = "JOIN A ON A.id=T1.id JOIN B ON B.id=T1.id JOIN C ON C.id=T1.id"

        result = canonicalize_joins(sql)
        expected = "SELECT * FROM T1 JOIN A ON A.id=T1.id JOIN B ON B.id=T1.id JOIN C ON C.id=T1.id"
        self.assertEqual(normalize_sql(result), normalize_sql(expected))

    def test_mixed_inner_cross_natural(self):
        # INNER, CROSS, NATURAL are all reorderable by default.
        # Input: JOIN Z (INNER) -> CROSS JOIN Y -> NATURAL JOIN X
        # Sorted: CROSS JOIN Y -> JOIN Z -> NATURAL JOIN X (depending on table name?)
        # Keys:
        # 1. CROSS JOIN Y -> type=CROSS, table=Y
        # 2. JOIN Z -> type=INNER, table=Z
        # 3. NATURAL JOIN X -> type=NATURAL, table=X

        # Sort order: type, table, cond_kw, cond
        # CROSS comes before INNER? C < I. NATURAL is N.
        # So expected: CROSS JOIN Y ..., INNER JOIN Z ..., NATURAL JOIN X ...

        sql = "SELECT * FROM Base JOIN Z ON 1=1 CROSS JOIN Y NATURAL JOIN X"

        # Expected sort key order:
        # 1. ('CROSS', 'Y', '', '')  <-- CROSS JOIN Y
        # 2. ('INNER', 'Z', 'ON', '1=1') <-- INNER JOIN Z ...
        # 3. ('NATURAL', 'X', '', '') <-- NATURAL JOIN X

        result = canonicalize_joins(sql)
        # We expect CROSS JOIN Y to appear first after Base
        self.assertRegex(result, r"FROM Base CROSS JOIN Y.*JOIN Z.*NATURAL JOIN X")

    def test_left_join_no_reorder_default(self):
        # LEFT JOINs should not move if allow_left=False
        sql = "SELECT * FROM Base JOIN A ON 1=1 LEFT JOIN B ON 1=1 JOIN C ON 1=1"
        # The sequence is: JOIN A (Inner), LEFT JOIN B, JOIN C (Inner).
        # "contiguous runs of ... INNER ... are sorted".
        # Here we have: [Inner A], [Left B], [Inner C].
        # Left breaks the run of Inner.
        # So A is a run of 1. B is not reorderable. C is a run of 1.
        # Nothing should change order-wise, effectively.

        result = canonicalize_joins(sql, allow_left=False)
        # Normalize to ignore whitespace differences
        self.assertEqual(normalize_sql(result), normalize_sql(sql))

    def test_left_join_reorder_enabled(self):
        # With allow_left=True, LEFT JOIN is treated as reorderable.
        # So [Inner A, Left B, Inner C] becomes a single run of 3 reorderables.
        # Sort keys:
        # A: ('INNER', 'A', ...)
        # B: ('LEFT', 'B', ...)
        # C: ('INNER', 'C', ...)
        # 'INNER' < 'LEFT'? I < L. Yes.
        # So Inner joins should come before Left joins if table names don't force otherwise?
        # Wait, sort key is (type, table, ...).
        # 'INNER' comes before 'LEFT'.

        sql = "SELECT * FROM Base LEFT JOIN B ON 1=1 JOIN A ON 1=1"
        # B is LEFT, A is INNER.
        # allow_left=True.
        # Sorted: INNER A, then LEFT B.

        result = canonicalize_joins(sql, allow_left=True)
        expected_regex = r"FROM Base JOIN A.*LEFT JOIN B"
        self.assertRegex(result, expected_regex)

    def test_full_outer_join_reordering(self):
        # Default: no reorder
        sql = "SELECT * FROM Base JOIN A ON 1=1 FULL JOIN B ON 1=1"
        result = canonicalize_joins(sql, allow_full_outer=False)
        self.assertEqual(normalize_sql(result), normalize_sql(sql))

        # Enabled: reorder
        # 'FULL' vs 'INNER'. F < I.
        # So FULL JOIN B should come before JOIN A.
        result = canonicalize_joins(sql, allow_full_outer=True)
        expected_regex = r"FROM Base FULL JOIN B.*JOIN A"
        self.assertRegex(result, expected_regex)

    def test_right_join_never_reordered(self):
        # RIGHT JOIN is not in the list of reorderables even if flags are on.
        # Input: JOIN A, RIGHT JOIN B, JOIN C.
        # Run 1: [A]. Stop at Right.
        # Run 2: [C].
        # Order should preserve A... B... C...

        sql = "SELECT * FROM Base JOIN C ON 1=1 RIGHT JOIN B ON 1=1 JOIN A ON 1=1"
        result = canonicalize_joins(sql, allow_full_outer=True, allow_left=True)
        # Even with flags, RIGHT JOIN B blocks merging of C and A runs.
        # C stays before B, A stays after B.
        # If they were merged, A (Inner) would come before C (Inner).

        self.assertRegex(result, r"FROM Base JOIN C.*RIGHT JOIN B.*JOIN A")

    def test_complex_mix(self):
        # T1 (base)
        # JOIN C (Inner)
        # LEFT JOIN B (Left)
        # JOIN A (Inner)
        # FULL JOIN D (Full)

        # With all flags=True:
        # All 4 are reorderable.
        # Sort keys:
        # A: ('INNER', 'A')
        # B: ('LEFT', 'B')
        # C: ('INNER', 'C')
        # D: ('FULL', 'D')

        # Alphabetical types:
        # FULL (D)
        # INNER (A)
        # INNER (C)
        # LEFT (B)

        sql = "SELECT * FROM T1 JOIN C ON 1=1 LEFT JOIN B ON 1=1 JOIN A ON 1=1 FULL JOIN D ON 1=1"
        result = canonicalize_joins(sql, allow_full_outer=True, allow_left=True)

        # Verify order: D, A, C, B
        # Regex needs to be loose on whitespace/conditions
        self.assertRegex(result, r"FROM T1 FULL JOIN D.*JOIN A.*JOIN C.*LEFT JOIN B")

if __name__ == '__main__':
    unittest.main()
