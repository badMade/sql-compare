import re

JOIN_SCANNER_RE = re.compile(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", flags=re.I)
ON_USING_SCANNER_RE = re.compile(r"\b(ON|USING)\b", flags=re.I)

def collapse_whitespace(s):
    return re.sub(r"\s+", " ", s)

def _parse_from_clause_body(body: str):
    i = 0; n = len(body)
    mode = None; level = 0
    tokens = []
    buf = []
    def flush_buf():
        nonlocal buf
        if buf:
            tokens.append(("TEXT", collapse_whitespace("".join(buf)).strip()))
            buf = []

    while i < n:
        ch = body[i]
        if mode is None:
            if ch == "'": mode = 'single'
            elif ch == '"': mode = 'double'
            elif ch == '[': mode = 'bracket'
            elif ch == '`': mode = 'backtick'
            elif ch == '(':
                level += 1
            elif ch == ')':
                level = max(0, level - 1)
            if level == 0:
                m = JOIN_SCANNER_RE.match(body, i)
                if m:
                    flush_buf()
                    tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                    i += len(m.group(0)) # <--- this is the issue probably, m.end() on .match(body, i) is the absolute position in `body` instead of relative!
                    continue
                m2 = ON_USING_SCANNER_RE.match(body, i)
                if m2:
                    flush_buf()
                    tokens.append(("CONDKW", m2.group(1).upper()))
                    i += len(m2.group(0))
                    continue
        else:
            if mode == 'single' and ch == "'":
                if i + 1 < n and body[i + 1] == "'": buf.append(ch); i += 1
                else: mode = None
            elif mode == 'double' and ch == '"':
                if i + 1 < n and body[i + 1] == '"': buf.append(ch); i += 1
                else: mode = None
            elif mode == 'bracket' and ch == ']': mode = None
            elif mode == 'backtick' and ch == '`': mode = None
        buf.append(ch); i += 1
    flush_buf()
    return tokens

print(_parse_from_clause_body("FROM t1 JOIN t3 ON t1.id=t3.id JOIN t2 ON t1.id=t2.id"))
