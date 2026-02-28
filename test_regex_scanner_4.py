import re
from sql_compare import clause_end_index, SQL_CLAUSE_TERMINATORS

terminators_pattern = "|".join(r"\b" + re.sub(r"\s+", r"\\s+", term) + r"\b" for term in SQL_CLAUSE_TERMINATORS)

CLAUSE_SCANNER_RE = re.compile(
    r"""
    (?:'(?:(?:''|[^'])*?)')               # single-quoted string
  | (?:(?:(?:\bE)?")(?:(?:""|[^"])*?)")   # double-quoted string (allow E"...")
  | (?:\[(?:[^\]]*?)\])                   # [bracketed] identifier
  | (?:`(?:[^`]*?)`)                      # `backticked` identifier
  | \(                                    # open paren
  | \)                                    # close paren
  | (?:""" + terminators_pattern + r""")  # clause terminators
    """,
    re.VERBOSE | re.IGNORECASE
)

def clause_end_index_optimized(sql: str, start: int) -> int:
    level = 0
    for m in CLAUSE_SCANNER_RE.finditer(sql, start):
        token = m.group(0)
        ch = token[0]
        if ch == '(':
            level += 1
        elif ch == ')':
            level = max(0, level - 1)
        elif level == 0:
            if not (ch in ("'", '"', '[', '`') or token.upper().startswith("E\"")):
                return m.start()
    return len(sql)


test_cases = [
    ("SELECT * FROM t WHERE a=1", 16),
    ("SELECT * FROM t GROUP BY a", 16),
    ("SELECT * FROM t WHERE a='GROUP BY'", 16),
    ("SELECT * FROM t WHERE a=(SELECT MAX(id) FROM b WHERE id > 1) GROUP BY a", 16),
    ("SELECT * FROM [t GROUP BY x] GROUP BY a", 29),
    ("SELECT * FROM t", 15),
    ("SELECT * FROM t where x = 2", 16),
    ("SELECT * FROM t e\"WHERE\" where x = 2", 27),
    ("SELECT * FROM t E\"WHERE\" where x = 2", 27),
    ("SELECT * FROM t E\"WHERE \" where x = 2", 28),
]

for sql, expected in test_cases:
    start_idx = sql.find("FROM") + 4
    if start_idx == 3:
        start_idx = 0
    idx1 = clause_end_index(sql, start_idx)
    idx2 = clause_end_index_optimized(sql, start_idx)
    if idx1 != idx2:
        print(f"MISMATCH! SQL: {sql}")
        print(f"Original: {idx1}, Optimized: {idx2}")
        print("========")
    else:
        print(f"MATCH! SQL: {sql} => {idx1}")
