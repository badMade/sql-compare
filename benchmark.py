import time
import re
from sql_compare import _parse_from_clause_body

# Generate a large FROM clause body
body = "a JOIN b ON a.id = b.id " * 1000

start_time = time.time()
_parse_from_clause_body(body)
end_time = time.time()

print(f"Time taken: {end_time - start_time:.4f} seconds")
