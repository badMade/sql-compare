import re
import timeit

SQL_CLAUSE_TERMINATORS = ["WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "QUALIFY", "WINDOW", "UNION", "INTERSECT", "EXCEPT"]

terminators_pattern = "|".join(r"\b" + re.sub(r"\s+", r"\\s+", term) + r"\b" for term in SQL_CLAUSE_TERMINATORS)

CLAUSE_SCANNER_RE = re.compile(
    r"""
    (?:'(?:(?:''|[^'])*?)')               # single-quoted string
  | (?:(?:(?:\bE)?")(?:(?:""|[^"])*?)")   # double-quoted string (allow E"...")
  | (?:\[(?:[^\]]*?)\])                   # [bracketed] identifier
  | (?:`(?:[^`]*?)`)                      # `backticked` identifier
  | \(                                    # open paren
  | \)                                    # close paren
  | """ + terminators_pattern + r"""      # clause terminators
    """,
    re.VERBOSE | re.IGNORECASE
)

sql = """
SELECT a, b, c
FROM my_table
WHERE id = 1
  AND name = 'John Doe'
  AND (status = 'active' OR status = 'pending')
  AND created_at > '2020-01-01'
GROUP BY a, b, c
ORDER BY a
LIMIT 10
""" * 1000

start_idx = sql.find("FROM")

def clause_end_index_optimized(sql: str, start: int) -> int:
    level = 0
    for m in CLAUSE_SCANNER_RE.finditer(sql, start):
        token = m.group(0).upper()
        if token == "(":
            level += 1
        elif token == ")":
            level = max(0, level - 1)
        elif level == 0 and not (token.startswith("'") or token.startswith('"') or token.startswith("[") or token.startswith("`") or token.startswith("E\"")):
            # It must be one of the terminators!
            return m.start()
    return len(sql)

print(clause_end_index_optimized(sql, start_idx + 4))

def bench():
    clause_end_index_optimized(sql, start_idx + 4)

print(timeit.timeit(bench, number=10))
