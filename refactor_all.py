import re

with open("sql_compare.py", "r") as f:
    content = f.read()

# 1. uppercase_outside_quotes
old_func = "def uppercase_outside_quotes(s: str) -> str:"
end_func = "def remove_trailing_semicolon(s: str) -> str:"
new_func = r'''def uppercase_outside_quotes(s: str) -> str:
    """
    Uppercase characters outside of quoted regions:
      single quotes '...'; double quotes "..."; [brackets]; `backticks`
    """
    out = []
    scanner = _SQLScanner(s)

    while scanner.i < scanner.n:
        was_outside = (scanner.mode is None)
        token = scanner.step()

        if was_outside:
            if token and token[0] in ("'", '"', '[', '`'):
                out.append(token)
            else:
                out.append(token.upper())
        else:
            out.append(token)

    return "".join(out)
'''
s = content.find(old_func)
e = content.find(end_func)
if s != -1 and e != -1: content = content[:s] + new_func + "\n\n" + content[e:]

# 2. remove_outer_parentheses
old_func = "def remove_outer_parentheses(s: str) -> str:"
end_func = "TOKEN_REGEX ="
new_func = r'''def remove_outer_parentheses(s: str) -> str:
    """Remove one or more layers of outer wrapping parentheses if they enclose the full statement."""
    def is_wrapped(text: str) -> bool:
        if not (text.startswith("(") and text.endswith(")")):
            return False
        scanner = _SQLScanner(text)
        while scanner.i < scanner.n:
            token = scanner.step()
            if scanner.level == 0 and scanner.i < scanner.n:
                return False
        return scanner.level == 0

    changed = True
    while changed:
        changed = False
        s_stripped = s.strip()
        if s_stripped.startswith("(") and s_stripped.endswith(")") and is_wrapped(s_stripped):
            s = s_stripped[1:-1].strip()
            changed = True
    return s
'''
s = content.find(old_func)
e = content.find(end_func)
if s != -1 and e != -1: content = content[:s] + new_func + "\n\n" + content[e:]

# 3. split_top_level
old_func = "def split_top_level(s: str, sep: str) -> list:"
end_func = "def top_level_find_kw(sql: str, kw: str, start: int = 0):"
new_func = r'''def split_top_level(s: str, sep: str) -> list:
    """Split by sep at top-level (not inside quotes/parentheses/brackets/backticks)."""
    parts, buf = [], []
    scanner = _SQLScanner(s)

    while scanner.i < scanner.n:
        if scanner.mode is None and scanner.level == 0:
            if s.startswith(sep, scanner.i):
                parts.append("".join(buf).strip())
                buf = []
                scanner.i += len(sep)
                continue

        token = scanner.step()
        buf.append(token)

    if buf: parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]
'''
s = content.find(old_func)
e = content.find(end_func)
if s != -1 and e != -1: content = content[:s] + new_func + "\n\n" + content[e:]

# 4. top_level_find_kw
old_func = "def top_level_find_kw(sql: str, kw: str, start: int = 0):"
end_func = "def clause_end_index(sql: str, start: int) -> int:"
new_func = r'''def top_level_find_kw(sql: str, kw: str, start: int = 0):
    """Find top-level occurrence of keyword kw (word boundary) starting at start."""
    kw = kw.upper()
    scanner = _SQLScanner(sql)
    scanner.i = start

    pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)

    while scanner.i < scanner.n:
        if scanner.mode is None and scanner.level == 0:
            if pattern.match(sql, scanner.i):
                return scanner.i
        scanner.step()

    return -1
'''
s = content.find(old_func)
e = content.find(end_func)
if s != -1 and e != -1: content = content[:s] + new_func + "\n\n" + content[e:]

# 5. _parse_from_clause_body
old_func = "def _parse_from_clause_body(body: str):"
end_func = "def _rebuild_from_body(base: str, segments: list) -> str:"
new_func = r'''def _parse_from_clause_body(body: str):
    """
    Parse FROM body into base and join segments.
    Returns: (base_text, segments)
    segment = dict(type='INNER'|'LEFT'|'RIGHT'|'FULL'|'CROSS'|'NATURAL'|...,
                   table='...',
                   cond_kw='ON'|'USING'|None,
                   cond='...' or '')
    Heuristic, top-level only.
    """
    scanner = _SQLScanner(body)
    tokens = []
    buf = []

    join_pattern = re.compile(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", re.IGNORECASE)
    cond_pattern = re.compile(r"\b(ON|USING)\b", re.IGNORECASE)

    def flush_buf():
        nonlocal buf
        if buf:
            tokens.append(("TEXT", collapse_whitespace("".join(buf)).strip()))
            buf = []

    while scanner.i < scanner.n:
        if scanner.mode is None and scanner.level == 0:
            m = join_pattern.match(body, scanner.i)
            if m:
                flush_buf()
                tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                scanner.i = m.end()
                continue

            m2 = cond_pattern.match(body, scanner.i)
            if m2:
                flush_buf()
                tokens.append(("CONDKW", m2.group(1).upper()))
                scanner.i = m2.end()
                continue

        token = scanner.step()
        buf.append(token)

    flush_buf()

    base = ""
    segments = []
    idx = 0
    while idx < len(tokens) and tokens[idx][0] != "JOINKW":
        kind, text = tokens[idx]
        if kind == "TEXT":
            base = (base + " " + text).strip()
        idx += 1

    while idx < len(tokens):
        if tokens[idx][0] != "JOINKW":
            idx += 1; continue
        join_kw = tokens[idx][1]
        idx += 1

        table_text = ""
        cond_kw = None
        cond_text = ""

        while idx < len(tokens) and tokens[idx][0] not in ("CONDKW", "JOINKW"):
            k, t = tokens[idx]
            if k == "TEXT":
                table_text = (table_text + " " + t).strip()
            idx += 1

        if idx < len(tokens) and tokens[idx][0] == "CONDKW":
            cond_kw = tokens[idx][1]
            idx += 1
            while idx < len(tokens) and tokens[idx][0] != "JOINKW":
                k, t = tokens[idx]
                if k == "TEXT":
                    cond_text = (cond_text + " " + t).strip()
                idx += 1

        seg_type = join_kw.replace(" OUTER", "")
        seg_type = seg_type.upper()
        # Fix implicit JOIN parsing: remove trailing JOIN word (preceded by space or at start)
        seg_type = re.sub(r"(?:\s+|^)JOIN$", "", seg_type).strip()

        if seg_type == "":
            seg_type = "INNER"

        segments.append({
            "type": seg_type,
            "table": collapse_whitespace(table_text),
            "cond_kw": cond_kw,
            "cond": collapse_whitespace(cond_text),
        })
    base = collapse_whitespace(base)
    return base, segments
'''
s = content.find(old_func)
e = content.find(end_func)
if s != -1 and e != -1: content = content[:s] + new_func + "\n\n" + content[e:]

with open("sql_compare.py", "w") as f:
    f.write(content)
