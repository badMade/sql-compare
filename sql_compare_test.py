import time
from sql_compare import _parse_from_clause_body

sizes = [50000, 100000, 200000]

print("Measuring parse times...")
for size in sizes:
    body = "a " * size
    start = time.time()
    _parse_from_clause_body(body)
    end = time.time()
    print(f"N={size}: {end - start:.4f}s")
