import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# THE PROBLEM IS \b parsing in new_top_level string format.
# When writing `m = re.match(r"\b" + re.escape(kw) + r"\b", sql[i:], flags=re.IGNORECASE)`
# the literal `r"\b"` string in python parses `\b` as `\b`.
# Wait, I used `\b` inside `re.match` successfully via:
new_top_level = "def top_level_find_kw(sql: str, kw: str, start: int = 0):\n" \
"    \"\"\"Find top-level occurrence of keyword kw (word boundary) starting at start.\"\"\"\n" \
"    kw = kw.upper()\n" \
"    i = start\n" \
"    scanner = _SQLScanner()\n" \
"    while i < len(sql):\n" \
"        ch = sql[i]\n" \
"        next_ch = sql[i + 1] if i + 1 < len(sql) else None\n" \
"        \n" \
"        if scanner.level == 0 and scanner.mode is None:\n" \
"            # The key is to match EXACTLY how it did in original.\n" \
"            m = re.match(r\"\\b\" + re.escape(kw) + r\"\\b\", sql[i:], flags=re.IGNORECASE)\n" \
"            if m: return i\n" \
"            \n" \
"        skip = scanner.update(ch, next_ch)\n" \
"        i += skip + 1\n" \
"    return -1"

old_top_level_pattern = re.compile(r'def top_level_find_kw\(sql: str, kw: str, start: int = 0\):.*?(?=\n\n\ndef clause_end_index)', re.DOTALL)
content = old_top_level_pattern.sub(new_top_level, content)

with open("sql_compare.py", "w", encoding="utf-8") as f:
    f.write(content)
