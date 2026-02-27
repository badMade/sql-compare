import time
import re

# --- Copied from sql_compare.py (simplified dependencies) ---

def top_level_find_kw(sql: str, kw: str, start: int = 0):
    kw = kw.upper()
    i = start; mode = None; level = 0
    while i < len(sql):
        ch = sql[i]
        if mode is None:
            if ch == "'": mode = 'single'
            elif ch == '"': mode = 'double'
            elif ch == '[': mode = 'bracket'
            elif ch == '`': mode = 'backtick'
            elif ch == '(':
                level += 1
            elif ch == ')':
                level = max(0, level - 1)
            if level == 0:
                m = re.match(rf"\b{re.escape(kw)}\b", sql[i:])
                if m: return i
        else:
            if mode == 'single' and ch == "'":
                if i + 1 < len(sql) and sql[i + 1] == "'": i += 1
                else: mode = None
            elif mode == 'double' and ch == '"':
                if i + 1 < len(sql) and sql[i + 1] == '"': i += 1
                else: mode = None
            elif mode == 'bracket' and ch == ']': mode = None
            elif mode == 'backtick' and ch == '`': mode = None
        i += 1
    return -1

def clause_end_index_original(sql: str, start: int) -> int:
    terms = ["WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "QUALIFY", "WINDOW",
             "UNION", "INTERSECT", "EXCEPT"]
    ends = []
    for term in terms:
        idx = top_level_find_kw(sql, term, start)
        if idx != -1: ends.append(idx)
    return min(ends) if ends else len(sql)

# --- Optimized Version Prototype ---

# Regex to match strings, parens, or keywords
# We use a single regex to find the next "interesting" thing.
CLAUSE_KEYWORDS = ["WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "QUALIFY", "WINDOW", "UNION", "INTERSECT", "EXCEPT"]
# Sort by length desc to ensure "GROUP BY" matches before "GROUP" if that were an issue (it's not here since we use \b, but good practice)
CLAUSE_KEYWORDS.sort(key=len, reverse=True)

# We need to be careful about regex construction.
# The original code uses a manual state machine for quotes/parens.
# A regex-based approach for the whole scan is usually faster in Python than a manual loop.

# Regex patterns:
# 1. Strings: '...', "..."
# 2. Identifiers: [...], `...`
# 3. Parens: (, )
# 4. Keywords: \bKW\b (case insensitive)

kw_pattern = "|".join(re.escape(k).replace(r"\ ", r"\s+") for k in CLAUSE_KEYWORDS)
# replace space in GROUP BY with \s+ to be robust

# We need to capture which group matched.
# Group 1: Single Quote
# Group 2: Double Quote
# Group 3: Bracket
# Group 4: Backtick
# Group 5: Open Paren
# Group 6: Close Paren
# Group 7: Keyword

SCAN_REGEX = re.compile(
    r"('(?:''|[^'])*')|"             # 1
    r"(\"(?:\"\"|[^\"])*\")|"        # 2
    r"(\[[^]]*\])|"                  # 3
    r"(`[^`]*`)|"                    # 4
    r"(\()|"                         # 5
    r"(\))|"                         # 6
    rf"(\b(?:{kw_pattern})\b)",      # 7
    re.IGNORECASE | re.DOTALL
)

def clause_end_index_optimized(sql: str, start: int) -> int:
    level = 0
    # We use finditer to jump between interesting tokens
    # Note: the regex for strings might be slightly different than the manual loop if not careful.
    # The manual loop handles:
    #   '...' with '' escape
    #   "..." with "" escape
    #   [...] no escape mentioned in code, just ends at ]
    #   `...` no escape mentioned in code, just ends at `

    # The regex above:
    #   '(?:''|[^'])*' handles '' escape
    #   "(?:""|[^"])*" handles "" escape
    #   \[[^]]*\] handles brackets (no nesting/escaping support in original code logic apparently, just waits for ])
    #   `[^`]*` handles backticks

    for match in SCAN_REGEX.finditer(sql, pos=start):
        if match.group(5): # (
            level += 1
        elif match.group(6): # )
            level = max(0, level - 1)
        elif match.group(7): # Keyword
            if level == 0:
                return match.start()
        # Groups 1-4 are skipped implicitly

    return len(sql)

# --- Correctness Check ---
# We need to make sure the regex matches the manual loop behavior for edge cases.
# Especially for nested parens and quotes.

def test_correctness():
    cases = [
        ("SELECT * FROM t WHERE a=1 ORDER BY b", "ORDER BY"),
        ("SELECT * FROM t WHERE a='(ORDER BY)' GROUP BY x", "GROUP BY"),
        ("SELECT * FROM t WHERE a=(SELECT 1 UNION SELECT 2) LIMIT 1", "LIMIT"),
        ("SELECT * FROM t WHERE a=`ORDER BY`", ""), # No keyword at top level
        ("SELECT * FROM t WHERE a=[GROUP BY]", ""),
        ("SELECT * FROM t WHERE a=1", ""),
    ]

    print("Running correctness tests...")
    for sql_snippet, expected_kw in cases:
        # Construct full SQL to start search after WHERE usually
        # But here we just test the function on the snippet starting at 0
        idx_orig = clause_end_index_original(sql_snippet, 0)
        idx_opt = clause_end_index_optimized(sql_snippet, 0)

        kw_found_orig = sql_snippet[idx_orig:] if idx_orig < len(sql_snippet) else ""
        kw_found_opt = sql_snippet[idx_opt:] if idx_opt < len(sql_snippet) else ""

        # We just check if they found the same index
        if idx_orig != idx_opt:
            print(f"FAIL: '{sql_snippet}'")
            print(f"  Orig index: {idx_orig} (rem: '{kw_found_orig}')")
            print(f"  Opt  index: {idx_opt} (rem: '{kw_found_opt}')")
        else:
            pass # print(f"PASS: '{sql_snippet}' -> {idx_orig}")

# --- Benchmark ---

def run_benchmark():
    # Long SQL string with many tokens and no keywords for a while
    conditions = " AND ".join([f"col{i} = {i} OR col{i} IN ('a', 'b', 'c')" for i in range(2000)])
    sql = f"SELECT * FROM table WHERE {conditions} ORDER BY col1"

    start_pos = sql.find("WHERE") + 5

    print(f"\nBenchmark SQL length: {len(sql)}")

    # Warmup
    clause_end_index_original(sql, start_pos)
    clause_end_index_optimized(sql, start_pos)

    # Measure Original
    t0 = time.time()
    for _ in range(10):
        clause_end_index_original(sql, start_pos)
    t1 = time.time()
    orig_time = t1 - t0

    # Measure Optimized
    t0 = time.time()
    for _ in range(10):
        clause_end_index_optimized(sql, start_pos)
    t1 = time.time()
    opt_time = t1 - t0

    print(f"Original: {orig_time:.4f}s")
    print(f"Optimized: {opt_time:.4f}s")
    print(f"Speedup:  {orig_time/opt_time:.2f}x")

if __name__ == "__main__":
    test_correctness()
    run_benchmark()
