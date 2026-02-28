import re

with open('sql_compare.py', 'r') as f:
    content = f.read()

# Add compiled regexes before _parse_from_clause_body
target_str = "def _parse_from_clause_body(body: str):"
replacement_str = """
JOIN_SCANNER_RE = re.compile(r"\\b((?:NATURAL\\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\\s+OUTER)?\\s*JOIN)\\b", flags=re.I)
ON_USING_SCANNER_RE = re.compile(r"\\b(ON|USING)\\b", flags=re.I)

def _parse_from_clause_body(body: str):"""

if target_str in content:
    content = content.replace(target_str, replacement_str)
else:
    print("Could not find target string.")

# Replace the inner loop re.match calls
# m = re.match(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", body[i:], flags=re.I)
old_match_join = 'm = re.match(r"\\b((?:NATURAL\\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\\s+OUTER)?\\s*JOIN)\\b", body[i:], flags=re.I)'
new_match_join = 'm = JOIN_SCANNER_RE.match(body, i)'

# m2 = re.match(r"\b(ON|USING)\b", body[i:], flags=re.I)
old_match_on = 'm2 = re.match(r"\\b(ON|USING)\\b", body[i:], flags=re.I)'
new_match_on = 'm2 = ON_USING_SCANNER_RE.match(body, i)'

if old_match_join in content and old_match_on in content:
    content = content.replace(old_match_join, new_match_join)
    content = content.replace(old_match_on, new_match_on)
else:
    print("Could not find match strings.")

with open('sql_compare.py', 'w') as f:
    f.write(content)
