import re

with open("sql_compare.py", "r") as f:
    code = f.read()

# Fix canonicalize_where_and
code = code.replace(
    "terms_sorted = sorted([collapse_whitespace(t) for t in terms], key=lambda z: z.upper())",
    "terms_sorted = sorted([t.strip() for t in terms], key=lambda z: z.upper())"
)

# Fix _tokenize_from_clause_body line 379
code = code.replace(
    "tokens.append((\"TEXT\", collapse_whitespace(\"\".join(buf)).strip()))",
    "tokens.append((\"TEXT\", \"\".join(buf).strip()))"
)

# Fix _tokenize_from_clause_body line 397. Wait! "collapse_whitespace(m.group(1)).upper()" handles "LEFT   JOIN". We should collapse it. Let's see if we should leave it. The regex is: r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b"
code = code.replace(
    "tokens.append((\"JOINKW\", collapse_whitespace(m.group(1)).upper()))",
    "tokens.append((\"JOINKW\", \" \".join(m.group(1).upper().split())))"
)

# Fix _extract_join_segments lines 475 and 477
code = code.replace(
    "\"table\": collapse_whitespace(table_text),",
    "\"table\": table_text.strip(),"
)
code = code.replace(
    "\"cond\": collapse_whitespace(cond_text),",
    "\"cond\": cond_text.strip(),"
)

# Fix _parse_from_clause_body line 497
code = code.replace(
    "return collapse_whitespace(base), segments",
    "return base.strip(), segments"
)


with open("sql_compare.py", "w") as f:
    f.write(code)
