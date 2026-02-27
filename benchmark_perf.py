import time
import re
import sys
# Import the module. Ensure it's in path.
sys.path.append('.')
from sql_compare import top_level_find_kw, normalize_sql

# Create a synthetic SQL string with significant length and nesting
def generate_sql(n):
    # n clauses of SELECT ... FROM ... WHERE ...
    # Deep nesting
    parts = []
    for i in range(n):
        parts.append(f"SELECT col_{i} FROM table_{i} WHERE (a = {i} AND (b = 'str_{i}' OR c IN (SELECT x FROM y)))")

    # Join them with UNION ALL to make a long string
    return " UNION ALL ".join(parts)

def benchmark():
    # Size 1000 repeated clauses results in a decent size string
    sql = generate_sql(1000)
    # Normalize it as the tool usually does
    sql = normalize_sql(sql)

    print(f"SQL length: {len(sql)}")

    # We will search for a keyword that appears many times, and one that doesn't.
    # top_level_find_kw returns the FIRST occurrence.
    # To stress test, we can search for something at the end, or loop.

    start_time = time.time()
    # Search for "UNION" - it appears many times.
    # But top_level_find_kw finds the first one.
    # To measure scanning speed, we should search for something that is NOT found,
    # or something at the very end.

    # "MISSING_KEYWORD"
    idx = top_level_find_kw(sql, "MISSING_KEYWORD")
    end_time = time.time()

    print(f"Time to search missing keyword: {end_time - start_time:.4f} seconds")

    # Search for "UNION" with offset to traverse the whole string
    start_time = time.time()
    pos = 0
    count = 0
    while True:
        idx = top_level_find_kw(sql, "UNION", pos)
        if idx == -1:
            break
        pos = idx + 1
        count += 1
    end_time = time.time()
    print(f"Time to find all {count} UNIONS: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()
