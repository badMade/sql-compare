from sql_compare import CLAUSE_SCANNER_RE
import re
print("FLAGS:")
print(CLAUSE_SCANNER_RE.flags)
print(CLAUSE_SCANNER_RE.flags & re.IGNORECASE)
