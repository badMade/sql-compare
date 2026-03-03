import time
import re
import itertools

JOIN_RE = re.compile(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", flags=re.I)
ON_USING_RE = re.compile(r"\b(ON|USING)\b", flags=re.I)

def collapse_whitespace(s):
    return " ".join(s.split())

def _parse_from_clause_body_old(body: str):
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
                m = re.match(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", body[i:], flags=re.I)
                if m:
                    flush_buf()
                    tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                    i += m.end()
                    continue
                m2 = re.match(r"\b(ON|USING)\b", body[i:], flags=re.I)
                if m2:
                    flush_buf()
                    tokens.append(("CONDKW", m2.group(1).upper()))
                    i += m2.end()
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

def _parse_from_clause_body_new(body: str):
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
                m = JOIN_RE.match(body, i)
                if m:
                    flush_buf()
                    tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                    i = m.end()
                    continue
                m2 = ON_USING_RE.match(body, i)
                if m2:
                    flush_buf()
                    tokens.append(("CONDKW", m2.group(1).upper()))
                    i = m2.end()
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

body = "a JOIN b ON a.id = b.id " * 2000

start_time = time.time()
tok1 = _parse_from_clause_body_old(body)
old_time = time.time() - start_time

start_time = time.time()
tok2 = _parse_from_clause_body_new(body)
new_time = time.time() - start_time

print(f"Old time: {old_time:.4f} seconds")
print(f"New time: {new_time:.4f} seconds")
print(f"Equal outputs: {tok1 == tok2}")
