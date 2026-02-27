import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from sql_compare import _parse_from_clause_body

def test_parse(body):
    print(f"Input: '{body}'")
    try:
        base, segments = _parse_from_clause_body(body)
        print(f"Base: '{base}'")
        for i, seg in enumerate(segments):
            print(f"Segment {i}: {seg}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)

test_parse("table1")
test_parse("table1 JOIN table2 ON table1.id = table2.id")
test_parse("table1 t1 LEFT JOIN table2 t2 ON t1.id = t2.id")
test_parse("a JOIN b ON a.id = b.id JOIN c ON b.id = c.id")
test_parse("a LEFT JOIN b ON a.id = b.id RIGHT JOIN c ON b.id = c.id")
test_parse("a CROSS JOIN b")
test_parse("a NATURAL JOIN b")
test_parse("table1 JOIN (SELECT * FROM table2) t2 ON table1.id = t2.id")
