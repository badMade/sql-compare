import re

with open("sql_compare.py", "r") as f:
    code = f.read()

# Fix _tokenize_from_clause_body line 397 properly
code = code.replace(
    "tokens.append((\"JOINKW\", m.group(1).strip().upper()))",
    "tokens.append((\"JOINKW\", \" \".join(m.group(1).upper().split())))"
)

with open("sql_compare.py", "w") as f:
    f.write(code)
