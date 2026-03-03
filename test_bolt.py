import re
from sql_compare import canonicalize_joins, normalize_sql

print(normalize_sql("SELECT * FROM a LEFT OUTER JOIN b ON a.id = b.id"))
print(canonicalize_joins("SELECT * FROM a LEFT OUTER JOIN b ON a.id = b.id JOIN c ON a.id = c.id", allow_left=True))
