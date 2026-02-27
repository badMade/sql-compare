# -*- coding: utf-8 -*-
import pytest
from sql_compare.core import (
    normalize_sql,
    canonicalize_select_list,
    canonicalize_where_and,
    canonicalize_joins,
    compare_sql
)

def test_normalize_sql():
    sql = "SELECT * FROM   table -- comment"
    expected = "SELECT * FROM TABLE"
    assert normalize_sql(sql) == expected

    # Test case sensitivity: quoted strings preserved, identifiers uppercased
    sql = "SELECT '  keep spaces  ' FROM t"
    expected = "SELECT '  keep spaces  ' FROM T"
    assert normalize_sql(sql) == expected

def test_canonicalize_select_list():
    sql = "SELECT b, a, c FROM t"
    expected = "SELECT A, B, C FROM T"
    assert canonicalize_select_list(normalize_sql(sql)) == expected

def test_canonicalize_where_and():
    sql = "SELECT * FROM t WHERE b=1 AND a=2"
    expected = "SELECT * FROM T WHERE A=2 AND B=1"
    assert canonicalize_where_and(normalize_sql(sql)) == expected

def test_compare_sql_exact():
    s1 = "SELECT * FROM table"
    s2 = "select * from table"
    result = compare_sql(s1, s2)
    assert result['exact_equal'] is True
    assert result['canonical_equal'] is True

def test_compare_sql_canonical():
    s1 = "SELECT a, b FROM t WHERE x=1 AND y=2"
    s2 = "SELECT b, a FROM t WHERE y=2 AND x=1"
    result = compare_sql(s1, s2)
    assert result['exact_equal'] is False
    assert result['canonical_equal'] is True

def test_compare_sql_whitespace():
    s1 = "SELECT * FROM t"
    s2 = "  SELECT   *   FROM   t  "

    # compare_sql calculates ws_equal based on whether they collapse to the same string
    result = compare_sql(s1, s2, ignore_ws=True)
    assert result['ws_equal'] is True

    # Even if ignore_ws is False (which is just passed for signature compatibility
    # but not used in calculation of ws_equal field in current impl),
    # ws_equal remains True because they ARE whitespace-equivalent.
    result_strict = compare_sql(s1, s2, ignore_ws=False)
    assert result_strict['ws_equal'] is True
