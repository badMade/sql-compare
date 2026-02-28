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

sql = "SELECT * FROM t where x = 2"
start_idx = sql.find("FROM") + 4
print("Original:", clause_end_index(sql, start_idx))
print("Optimized:", clause_end_index_optimized(sql, start_idx))
