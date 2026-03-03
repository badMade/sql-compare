import time
from sql_compare import top_level_find_kw

# Create a large SQL string (no keywords inside)
sql = "a" * 100000 + " WHERE b=1"

start = time.time()
idx = top_level_find_kw(sql, "WHERE", 0)
end = time.time()
print(f"Time taken: {end - start:.4f} seconds, found at: {idx}")
