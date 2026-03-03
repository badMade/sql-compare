import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add itertools import back!
if "import itertools" not in content:
    content = content.replace("import sys\n", "import sys\nimport itertools\n")

scanner_class = """

class _SQLScanner:
    __slots__ = ['mode', 'level']
    def __init__(self):
        self.mode = None
        self.level = 0

    def update(self, ch: str, next_ch: str = None) -> int:
        if self.mode is None:
            if ch == "'": self.mode = 'single'
            elif ch == '"': self.mode = 'double'
            elif ch == '[': self.mode = 'bracket'
            elif ch == '`': self.mode = 'backtick'
            elif ch == '(': self.level += 1
            elif ch == ')': self.level = max(0, self.level - 1)
        else:
            if self.mode == 'single' and ch == "'":
                if next_ch == "'": return 1
                else: self.mode = None
            elif self.mode == 'double' and ch == '"':
                if next_ch == '"': return 1
                else: self.mode = None
            elif self.mode == 'bracket' and ch == ']': self.mode = None
            elif self.mode == 'backtick' and ch == '`': self.mode = None
        return 0
"""

content = content.replace("def uppercase_outside_quotes", scanner_class.lstrip() + "\ndef uppercase_outside_quotes")

new_uppercase = """def uppercase_outside_quotes(s: str) -> str:
    \"\"\"
    Uppercase characters outside of quoted regions:
      single quotes '...'; double quotes "..."; [brackets]; `backticks`
    \"\"\"
    out = []
    i = 0
    scanner = _SQLScanner()
    while i < len(s):
        ch = s[i]
        next_ch = s[i + 1] if i + 1 < len(s) else None

        if scanner.mode is None:
            out.append(ch.upper())
        else:
            out.append(ch)

        skip = scanner.update(ch, next_ch)
        if skip:
            out.append(next_ch)
            i += skip
        i += 1
    return "".join(out)
"""

old_uppercase_pattern = re.compile(r'def uppercase_outside_quotes\(s: str\) -> str:\n.*?(?=\n\n\ndef remove_trailing_semicolon)', re.DOTALL)
content = old_uppercase_pattern.sub(new_uppercase, content)

new_remove = """def remove_outer_parentheses(s: str) -> str:
    \"\"\"Remove one or more layers of outer wrapping parentheses if they enclose the full statement.\"\"\"
    def is_wrapped(text: str) -> bool:
        if not (text.startswith("(") and text.endswith(")")):
            return False
        scanner = _SQLScanner()
        i = 0
        while i < len(text):
            ch = text[i]
            next_ch = text[i + 1] if i + 1 < len(text) else None

            skip = scanner.update(ch, next_ch)
            if scanner.mode is None and ch == ')' and scanner.level == 0 and i != len(text) - 1:
                return False

            i += skip + 1
        return scanner.level == 0
    changed = True
    while changed:
        changed = False
        s_stripped = s.strip()
        if s_stripped.startswith("(") and s_stripped.endswith(")") and is_wrapped(s_stripped):
            s = s_stripped[1:-1].strip()
            changed = True
    return s"""

old_remove_pattern = re.compile(r'def remove_outer_parentheses\(s: str\) -> str:.*?(?=\n\n\nTOKEN_REGEX)', re.DOTALL)
content = old_remove_pattern.sub(new_remove, content)

new_split = """def split_top_level(s: str, sep: str) -> list:
    \"\"\"Split by sep at top-level (not inside quotes/parentheses/brackets/backticks).\"\"\"
    parts, buf = [], []
    scanner = _SQLScanner()
    i = 0
    while i < len(s):
        ch = s[i]
        next_ch = s[i + 1] if i + 1 < len(s) else None

        if scanner.level == 0 and scanner.mode is None and s.startswith(sep, i):
            parts.append("".join(buf).strip())
            buf = []
            i += len(sep)
            continue

        skip = scanner.update(ch, next_ch)
        buf.append(ch)
        if skip:
            buf.append(next_ch)
            i += skip
        i += 1
    if buf: parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]"""

old_split_pattern = re.compile(r'def split_top_level\(s: str, sep: str\) -> list:.*?(?=\n\n\ndef top_level_find_kw)', re.DOTALL)
content = old_split_pattern.sub(new_split, content)

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
"            m = re.match(r\"\\b\" + re.escape(kw) + r\"\\b\", sql[i:], flags=re.IGNORECASE)\n" \
"            if m: return i\n" \
"            \n" \
"        skip = scanner.update(ch, next_ch)\n" \
"        i += skip + 1\n" \
"    return -1"

old_top_level_pattern = re.compile(r'def top_level_find_kw\(sql: str, kw: str, start: int = 0\):.*?(?=\n\n\ndef clause_end_index)', re.DOTALL)
content = old_top_level_pattern.sub(new_top_level, content)

new_parse_from = """def _parse_from_clause_body(body: str):
    \"\"\"
    Parse FROM body into base and join segments.
    Returns: (base_text, segments)
    segment = dict(type='INNER'|'LEFT'|'RIGHT'|'FULL'|'CROSS'|'NATURAL'|...,
                   table='...',
                   cond_kw='ON'|'USING'|None,
                   cond='...' or '')
    Heuristic, top-level only.
    \"\"\"
    i = 0; n = len(body)
    tokens = []
    buf = []
    def flush_buf():
        nonlocal buf
        if buf:
            tokens.append(("TEXT", collapse_whitespace("".join(buf)).strip()))
            buf = []

    scanner = _SQLScanner()
    while i < n:
        ch = body[i]
        next_ch = body[i + 1] if i + 1 < n else None

        if scanner.level == 0 and scanner.mode is None:
            m = re.match(r"\\b((?:NATURAL\\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\\s+OUTER)?\\s*JOIN)\\b", body[i:], flags=re.I)
            if m:
                flush_buf()
                tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                i += m.end()
                continue
            m2 = re.match(r"\\b(ON|USING)\\b", body[i:], flags=re.I)
            if m2:
                flush_buf()
                tokens.append(("CONDKW", m2.group(1).upper()))
                i += m2.end()
                continue

        skip = scanner.update(ch, next_ch)
        buf.append(ch)
        if skip:
            buf.append(next_ch)
            i += skip
        i += 1
    flush_buf()"""

old_parse_from_pattern = re.compile(r'def _parse_from_clause_body\(body: str\):.*?\n    flush_buf\(\)', re.DOTALL)
content = old_parse_from_pattern.sub(lambda m: new_parse_from, content)

with open("sql_compare.py", "w", encoding="utf-8") as f:
    f.write(content)
