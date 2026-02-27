from sql_compare import _parse_from_clause_body, _rebuild_from_body

def check(sql_body):
    print(f"Original: '{sql_body}'")
    base, segs = _parse_from_clause_body(sql_body)
    print(f"Segments: {segs}")
    rebuilt = _rebuild_from_body(base, segs)
    print(f"Rebuilt:  '{rebuilt}'")

check("a JOIN b ON a.id = b.id")
