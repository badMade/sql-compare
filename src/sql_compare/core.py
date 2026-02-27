# -*- coding: utf-8 -*-
"""
Core logic for SQL comparison: normalization, tokenization, and canonicalization.
"""

import difflib
import re
from collections import Counter


# =============================
# Normalization & Utilities
# =============================

def strip_sql_comments(s: str) -> str:
    """Remove -- line comments and /* ... */ block comments (non-nested)."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"--[^\n\r]*", "", s)
    return s


def collapse_whitespace_smart(s: str) -> str:
    """Collapse runs of whitespace to a single space and strip, respecting quotes."""
    res = []
    i = 0
    n = len(s)
    mode = None
    current_chunk = []

    while i < n:
        ch = s[i]

        if mode is None:
            if ch == "'":
                collapsed = re.sub(r"\s+", " ", "".join(current_chunk))
                res.append(collapsed)
                current_chunk = [ch]
                mode = 'single'
            elif ch == '"':
                collapsed = re.sub(r"\s+", " ", "".join(current_chunk))
                res.append(collapsed)
                current_chunk = [ch]
                mode = 'double'
            elif ch == '[':
                collapsed = re.sub(r"\s+", " ", "".join(current_chunk))
                res.append(collapsed)
                current_chunk = [ch]
                mode = 'bracket'
            elif ch == '`':
                collapsed = re.sub(r"\s+", " ", "".join(current_chunk))
                res.append(collapsed)
                current_chunk = [ch]
                mode = 'backtick'
            else:
                current_chunk.append(ch)

        elif mode == 'single':
            current_chunk.append(ch)
            if ch == "'":
                if i + 1 < n and s[i+1] == "'":
                    current_chunk.append(s[i+1])
                    i += 1
                else:
                    res.append("".join(current_chunk))
                    current_chunk = []
                    mode = None

        elif mode == 'double':
            current_chunk.append(ch)
            if ch == '"':
                if i + 1 < n and s[i+1] == '"':
                    current_chunk.append(s[i+1])
                    i += 1
                else:
                    res.append("".join(current_chunk))
                    current_chunk = []
                    mode = None

        elif mode == 'bracket':
            current_chunk.append(ch)
            if ch == ']':
                res.append("".join(current_chunk))
                current_chunk = []
                mode = None

        elif mode == 'backtick':
            current_chunk.append(ch)
            if ch == '`':
                res.append("".join(current_chunk))
                current_chunk = []
                mode = None

        i += 1

    if current_chunk:
        chunk = "".join(current_chunk)
        if mode is None:
            chunk = re.sub(r"\s+", " ", chunk)
        res.append(chunk)

    return "".join(res).strip()


def collapse_whitespace(s: str) -> str:
    """Legacy wrapper, now smart."""
    return collapse_whitespace_smart(s)


def uppercase_outside_quotes(s: str) -> str:
    """
    Uppercase characters outside of quoted regions.
    """
    out = []
    i = 0
    mode = None
    while i < len(s):
        ch = s[i]
        if mode is None:
            if ch == "'":
                mode = 'single'
                out.append(ch)
            elif ch == '"':
                mode = 'double'
                out.append(ch)
            elif ch == '[':
                mode = 'bracket'
                out.append(ch)
            elif ch == '`':
                mode = 'backtick'
                out.append(ch)
            else:
                out.append(ch.upper())
        elif mode == 'single':
            out.append(ch)
            if ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    out.append(s[i + 1]); i += 1
                else:
                    mode = None
        elif mode == 'double':
            out.append(ch)
            if ch == '"':
                if i + 1 < len(s) and s[i + 1] == '"':
                    out.append(s[i + 1]); i += 1
                else:
                    mode = None
        elif mode == 'bracket':
            out.append(ch)
            if ch == ']':
                mode = None
        elif mode == 'backtick':
            out.append(ch)
            if ch == '`':
                mode = None
        i += 1
    return "".join(out)


def remove_trailing_semicolon(s: str) -> str:
    s = s.strip()
    return s[:-1] if s.endswith(";") else s


def remove_outer_parentheses(s: str) -> str:
    """Remove one or more layers of outer wrapping parentheses if they enclose the full statement."""
    def is_wrapped(text: str) -> bool:
        if not (text.startswith("(") and text.endswith(")")):
            return False
        level = 0; mode = None; i = 0
        while i < len(text):
            ch = text[i]
            if mode is None:
                if ch == "'": mode = 'single'
                elif ch == '"': mode = 'double'
                elif ch == '[': mode = 'bracket'
                elif ch == '`': mode = 'backtick'
                elif ch == '(':
                    level += 1
                elif ch == ')':
                    level -= 1
                    if level == 0 and i != len(text) - 1:
                        return False
            elif mode == 'single':
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        i += 1
                    else:
                        mode = None
            elif mode == 'double':
                if ch == '"':
                    if i + 1 < len(text) and text[i + 1] == '"':
                        i += 1
                    else:
                        mode = None
            elif mode == 'bracket':
                if ch == ']': mode = None
            elif mode == 'backtick':
                if ch == '`': mode = None
            i += 1
        return level == 0
    changed = True
    while changed:
        changed = False
        s_stripped = s.strip()
        if s_stripped.startswith("(") and s_stripped.endswith(")") and is_wrapped(s_stripped):
            s = s_stripped[1:-1].strip()
            changed = True
    return s


TOKEN_REGEX = re.compile(
    r"""
    (?:'(?:(?:''|[^'])*?)')            # single-quoted string
  | (?:(?:(?:\bE)?")(?:(?:""|[^"])*?)")  # double-quoted string (allow E"..." too)
  | (?:\[(?:[^\]]*?)\])                # [bracketed] identifier
  | (?:`(?:[^`]*?)`)                   # `backticked` identifier
  | (?:[A-Z_][A-Z0-9_$]*\b)           # identifiers/keywords (after uppercasing)
  | (?:[0-9]+\.[0-9]+|[0-9]+)          # numbers
  | (?:<=|>=|<>|!=|:=|->|::)           # multi-char operators
  | (?:[(),=*\/\+\-<>\.%])             # single-char tokens
  | (?:\.)                             # dot
  | (?:\s+)                            # whitespace (filtered out)
    """,
    re.VERBOSE | re.IGNORECASE,
)

def tokenize(sql: str):
    return [m.group(0) for m in TOKEN_REGEX.finditer(sql) if not m.group(0).isspace()]


def split_top_level(s: str, sep: str) -> list:
    """Split by sep at top-level (not inside quotes/parentheses/brackets/backticks)."""
    parts, buf = [], []
    level = 0; mode = None; i = 0
    while i < len(s):
        ch = s[i]
        if mode is None:
            if ch == "'": mode = 'single'
            elif ch == '"': mode = 'double'
            elif ch == '[': mode = 'bracket'
            elif ch == '`': mode = 'backtick'
            elif ch == '(':
                level += 1
            elif ch == ')':
                level = max(0, level - 1)
            if level == 0 and s.startswith(sep, i):
                parts.append("".join(buf).strip()); buf = []; i += len(sep); continue
        else:
            if mode == 'single' and ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'": buf.append(ch); i += 1
                else: mode = None
            elif mode == 'double' and ch == '"':
                if i + 1 < len(s) and s[i + 1] == '"': buf.append(ch); i += 1
                else: mode = None
            elif mode == 'bracket' and ch == ']': mode = None
            elif mode == 'backtick' and ch == '`': mode = None
        buf.append(ch); i += 1
    if buf: parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]


def top_level_find_kw(sql: str, kw: str, start: int = 0):
    """Find top-level occurrence of keyword kw (word boundary) starting at start."""
    kw = kw.upper()
    i = start; mode = None; level = 0
    while i < len(sql):
        ch = sql[i]
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
                m = re.match(rf"\b{re.escape(kw)}\b", sql[i:])
                if m: return i
        else:
            if mode == 'single' and ch == "'":
                if i + 1 < len(sql) and sql[i + 1] == "'": i += 1
                else: mode = None
            elif mode == 'double' and ch == '"':
                if i + 1 < len(sql) and sql[i + 1] == '"': i += 1
                else: mode = None
            elif mode == 'bracket' and ch == ']': mode = None
            elif mode == 'backtick' and ch == '`': mode = None
        i += 1
    return -1


def clause_end_index(sql: str, start: int) -> int:
    """
    Find end index for a clause (FROM or WHERE) to the next top-level major keyword.
    """
    terms = ["WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "QUALIFY", "WINDOW",
             "UNION", "INTERSECT", "EXCEPT"]
    ends = []
    for term in terms:
        idx = top_level_find_kw(sql, term, start)
        if idx != -1: ends.append(idx)
    return min(ends) if ends else len(sql)


# =============================
# Canonicalization helpers
# =============================

def normalize_sql(sql: str) -> str:
    """Full normalization pipeline."""
    sql = sql.strip()
    sql = strip_sql_comments(sql)
    sql = collapse_whitespace_smart(sql)
    sql = remove_trailing_semicolon(sql)
    sql = remove_outer_parentheses(sql)
    sql = uppercase_outside_quotes(sql)
    # Re-normalize whitespace after uppercasing (though uppercasing shouldn't affect ws)
    sql = collapse_whitespace_smart(sql)
    return sql


def ws_only_normalize(sql: str) -> str:
    """
    Whitespace-only normalization:
    - collapse whitespace (smartly)
    - trim
    - remove trailing semicolon
    Does NOT remove comments or change case.
    """
    return remove_trailing_semicolon(collapse_whitespace_smart(sql))


def canonicalize_select_list(sql: str) -> str:
    s = collapse_whitespace_smart(sql)
    sel_i = top_level_find_kw(s, "SELECT", 0)
    if sel_i == -1: return s
    from_i = top_level_find_kw(s, "FROM", sel_i + 6)
    if from_i == -1: return s
    sel_list = s[sel_i + 6:from_i].strip()
    items = split_top_level(sel_list, ",")
    if len(items) > 1:
        items_sorted = sorted([collapse_whitespace_smart(it) for it in items], key=lambda z: z.upper())
        s = s[:sel_i + 6] + " " + ", ".join(items_sorted) + " " + s[from_i:]
    return collapse_whitespace_smart(s)


def canonicalize_where_and(sql: str) -> str:
    s = collapse_whitespace_smart(sql)
    where_i = top_level_find_kw(s, "WHERE", 0)
    if where_i == -1: return s
    end_i = clause_end_index(s, where_i + 5)
    body = s[where_i + 5:end_i].strip()
    terms = split_top_level(body, " AND ")
    if len(terms) > 1:
        terms_sorted = sorted([collapse_whitespace_smart(t) for t in terms], key=lambda z: z.upper())
        new_body = " AND ".join(terms_sorted)
        s = s[:where_i + 5] + " " + new_body + " " + s[end_i:]
    return collapse_whitespace_smart(s)


def _parse_from_clause_body(body: str):
    """
    Parse FROM body into base and join segments.
    Returns: (base_text, segments)
    segment = dict(type='INNER'|'LEFT'|'RIGHT'|'FULL'|'CROSS'|'NATURAL'|...,
                   table='...',
                   cond_kw='ON'|'USING'|None,
                   cond='...' or '')
    Heuristic, top-level only.
    """
    i = 0; n = len(body)
    mode = None; level = 0
    tokens = []
    buf = []
    def flush_buf():
        nonlocal buf
        if buf:
            tokens.append(("TEXT", collapse_whitespace_smart("".join(buf)).strip()))
            buf.clear()

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
                    tokens.append(("JOINKW", collapse_whitespace_smart(m.group(1)).upper()))
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
        seg_type = seg_type.replace(" JOIN", "").strip()
        if seg_type == "":
            seg_type = "INNER"

        segments.append({
            "type": seg_type,
            "table": collapse_whitespace_smart(table_text),
            "cond_kw": cond_kw,
            "cond": collapse_whitespace_smart(cond_text),
        })
    base = collapse_whitespace_smart(base)
    return base, segments


def _rebuild_from_body(base: str, segments: list) -> str:
    """Rebuild FROM body from base and segments (already normalized)."""
    parts = [base] if base else []
    for seg in segments:
        join_kw = "JOIN" if seg["type"] == "INNER" else (seg["type"] + " JOIN")
        piece = f"{join_kw} {seg['table']}"
        if seg["cond_kw"] and seg["cond"]:
            piece += f" {seg['cond_kw']} {seg['cond']}"
        parts.append(piece)
    return " ".join(parts)


def canonicalize_joins(sql: str, allow_full_outer: bool = False, allow_left: bool = False) -> str:
    """
    Canonicalize top-level FROM JOIN chains by sorting contiguous runs of:
      - INNER/CROSS/NATURAL joins (always when join reordering is enabled)
      - FULL joins (only when allow_full_outer=True)
      - LEFT joins (only when allow_left=True)
    RIGHT joins are preserved (not commutative). FULL/LEFT also preserved unless explicitly allowed.
    """
    s = collapse_whitespace_smart(sql)
    from_i = top_level_find_kw(s, "FROM", 0)
    if from_i == -1:
        return s
    end_i = clause_end_index(s, from_i + 4)
    body = s[from_i + 4:end_i].strip()
    if not body:
        return s

    base, segments = _parse_from_clause_body(body)
    if not segments:
        return s

    def is_reorderable(t: str) -> bool:
        tt = t.upper()
        if tt in ("INNER", "CROSS", "NATURAL"):
            return True
        if allow_full_outer and tt == "FULL":
            return True
        if allow_left and tt == "LEFT":
            return True
        return False

    new_segments = []
    run = []
    for seg in segments:
        if is_reorderable(seg["type"]):
            run.append(seg)
        else:
            if run:
                run = sorted(run, key=lambda z: (z["type"], z["table"].upper(), z.get("cond_kw") or "", z.get("cond") or ""))
                new_segments.extend(run); run = []
            new_segments.append(seg)
    if run:
        run = sorted(run, key=lambda z: (z["type"], z["table"].upper(), z.get("cond_kw") or "", z.get("cond") or ""))
        new_segments.extend(run)

    rebuilt = _rebuild_from_body(base, new_segments)
    s2 = s[:from_i + 4] + " " + rebuilt + " " + s[end_i:]
    return collapse_whitespace_smart(s2)


def canonicalize_common(sql: str, *, enable_join_reorder: bool = True, allow_full_outer: bool = False, allow_left: bool = False) -> str:
    """Apply canonicalizations: SELECT list, WHERE AND-terms, and (optionally) JOIN reordering."""
    s = collapse_whitespace_smart(sql)
    s = canonicalize_select_list(s)
    s = canonicalize_where_and(s)
    if enable_join_reorder:
        s = canonicalize_joins(s, allow_full_outer=allow_full_outer, allow_left=allow_left)
    return collapse_whitespace_smart(s)


# =============================
# Difference analysis (summary)
# =============================

def _select_items(sql: str):
    s = collapse_whitespace_smart(sql)
    si = top_level_find_kw(s, "SELECT", 0)
    if si == -1: return []
    fi = top_level_find_kw(s, "FROM", si + 6)
    if fi == -1: return []
    lst = s[si + 6:fi].strip()
    items = [collapse_whitespace_smart(x).upper() for x in split_top_level(lst, ",")]
    return items


def _where_and_terms(sql: str):
    s = collapse_whitespace_smart(sql)
    wi = top_level_find_kw(s, "WHERE", 0)
    if wi == -1: return []
    end = clause_end_index(s, wi + 5)
    body = s[wi + 5:end].strip()
    terms = [collapse_whitespace_smart(x).upper() for x in split_top_level(body, " AND ")]
    return terms


def _join_reorderable_segments(sql: str, enable_join_reorder: bool, allow_full_outer: bool, allow_left: bool):
    if not enable_join_reorder:
        return []
    s = collapse_whitespace_smart(sql)
    fi = top_level_find_kw(s, "FROM", 0)
    if fi == -1: return []
    end = clause_end_index(s, fi + 4)
    body = s[fi + 4:end].strip()
    base, segs = _parse_from_clause_body(body)
    if not segs: return []
    def is_reo(t: str) -> bool:
        tt = t.upper()
        return (tt in ("INNER", "CROSS", "NATURAL")
                or (allow_full_outer and tt == "FULL")
                or (allow_left and tt == "LEFT"))
    reprs = []
    for seg in segs:
        if is_reo(seg["type"]):
            reprs.append((seg["type"].upper(), seg["table"].upper(), (seg.get("cond_kw") or "").upper(), (seg.get("cond") or "").upper()))
    return reprs


def build_difference_summary(norm_a: str, norm_b: str, can_a: str, can_b: str,
                             tokens_a: list, tokens_b: list,
                             *, enable_join_reorder: bool, allow_full_outer: bool, allow_left: bool):
    summary = []

    # SELECT analysis
    sel_a = _select_items(norm_a); sel_b = _select_items(norm_b)
    if sel_a or sel_b:
        ca, cb = Counter(sel_a), Counter(sel_b)
        if ca != cb:
            missing = list((ca - cb).elements())
            added   = list((cb - ca).elements())
            if missing:
                summary.append(f"SELECT list differs: items only in SQL1: {len(missing)}")
            if added:
                summary.append(f"SELECT list differs: items only in SQL2: {len(added)}")
        elif sel_a != sel_b:
            summary.append("SELECT list order differs (same items, different order).")

    # WHERE AND analysis
    and_a = _where_and_terms(norm_a); and_b = _where_and_terms(norm_b)
    ca, cb = Counter(and_a), Counter(and_b)
    if ca != cb:
        missing = list((ca - cb).elements())
        added   = list((cb - ca).elements())
        if missing:
            summary.append(f"WHERE AND terms differ: terms only in SQL1: {len(missing)}")
        if added:
            summary.append(f"WHERE AND terms differ: terms only in SQL2: {len(added)}")
    elif and_a != and_b:
        summary.append("WHERE AND term order differs (same terms, different order).")

    # JOIN analysis (only when reordering is enabled)
    if enable_join_reorder:
        reo_a = _join_reorderable_segments(norm_a, enable_join_reorder, allow_full_outer, allow_left)
        reo_b = _join_reorderable_segments(norm_b, enable_join_reorder, allow_full_outer, allow_left)
        if reo_a or reo_b:
            ca, cb = Counter(reo_a), Counter(reo_b)
            if ca != cb:
                diff_a = sum((ca - cb).values())
                diff_b = sum((cb - ca).values())
                if diff_a:
                    summary.append(f"Reorderable JOIN components differ: {diff_a} only in SQL1.")
                if diff_b:
                    summary.append(f"Reorderable JOIN components differ: {diff_b} only in SQL2.")
            elif reo_a != reo_b:
                summary.append("Reorderable JOIN segment order differs (same components, different order).")
    else:
        summary.append("Join reordering is disabled; join order is considered significant in comparisons.")

    # Token change counts
    sm = difflib.SequenceMatcher(a=tokens_a, b=tokens_b, autojunk=False)
    ins = del_ = rep = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'insert':   ins += (j2 - j1)
        elif tag == 'delete': del_ += (i2 - i1)
        elif tag == 'replace': rep += max(i2 - i1, j2 - j1)
    if ins or del_ or rep:
        summary.append(f"Token-level changes: +{ins} inserts, -{del_} deletes, ~{rep} replaces.")

    if not summary:
        summary.append("No structural differences detected beyond normalization.")
    return summary


# =============================
# Comparison
# =============================

def compare_sql(a: str, b: str,
                *, ignore_ws: bool = False,
                enable_join_reorder: bool = True,
                allow_full_outer: bool = False,
                allow_left: bool = False):
    """
    Return a result dict with:
      - ws_equal, ws_norm forms and diff
      - exact_equal (token-based on normalized)
      - canonical_equal (with SELECT/WHERE/JOIN canonicalization per flags)
      - summary (list of bullet strings)
    """
    # use ws_only_normalize which uses collapse_whitespace_smart now
    ws_a = ws_only_normalize(a)
    ws_b = ws_only_normalize(b)
    ws_equal = (ws_a == ws_b)
    ws_diff = "\n".join(difflib.unified_diff(
        ws_a.splitlines(), ws_b.splitlines(),
        fromfile="sql1(ws)", tofile="sql2(ws)", lineterm=""
    ))

    norm_a = normalize_sql(a)
    norm_b = normalize_sql(b)
    tokens_a = tokenize(norm_a)
    tokens_b = tokenize(norm_b)
    exact_equal = (tokens_a == tokens_b)
    diff_norm = "\n".join(difflib.unified_diff(
        norm_a.splitlines(), norm_b.splitlines(),
        fromfile="sql1(norm)", tofile="sql2(norm)", lineterm=""
    ))

    can_a = canonicalize_common(norm_a, enable_join_reorder=enable_join_reorder,
                                allow_full_outer=allow_full_outer, allow_left=allow_left)
    can_b = canonicalize_common(norm_b, enable_join_reorder=enable_join_reorder,
                                allow_full_outer=allow_full_outer, allow_left=allow_left)
    canonical_equal = (can_a == can_b)
    diff_can = "\n".join(difflib.unified_diff(
        can_a.splitlines(), can_b.splitlines(),
        fromfile="sql1(canon)", tofile="sql2(canon)", lineterm=""
    ))

    summary = build_difference_summary(norm_a, norm_b, can_a, can_b, tokens_a, tokens_b,
                                       enable_join_reorder=enable_join_reorder,
                                       allow_full_outer=allow_full_outer,
                                       allow_left=allow_left)

    return {
        "ws_a": ws_a, "ws_b": ws_b, "ws_equal": ws_equal, "diff_ws": ws_diff,
        "norm_a": norm_a, "norm_b": norm_b, "tokens_a": tokens_a, "tokens_b": tokens_b,
        "exact_equal": exact_equal, "diff_norm": diff_norm,
        "can_a": can_a, "can_b": can_b, "canonical_equal": canonical_equal, "diff_can": diff_can,
        "summary": summary,
    }
