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
    scanner = _SQLScanner(body)
    tokens = []
    buf = []

    def flush_buf():
        if buf:
            tokens.append(("TEXT", collapse_whitespace("".join(buf)).strip()))
            buf.clear()

    while scanner.i < scanner.n:
        if scanner.mode is None and scanner.level == 0:
            m = re.match(r"\b((?:NATURAL\s+)?(?:LEFT|RIGHT|FULL|INNER|CROSS)?(?:\s+OUTER)?\s*JOIN)\b", body[scanner.i:], flags=re.I)
            if m:
                flush_buf()
                tokens.append(("JOINKW", collapse_whitespace(m.group(1)).upper()))
                scanner.i += m.end()
                continue

            m2 = re.match(r"\b(ON|USING)\b", body[scanner.i:], flags=re.I)
            if m2:
                flush_buf()
                tokens.append(("CONDKW", m2.group(1).upper()))
                scanner.i += m2.end()
                continue

        buf.append(scanner.step())

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
            "table": collapse_whitespace(table_text),
            "cond_kw": cond_kw,
            "cond": collapse_whitespace(cond_text),
        })
    base = collapse_whitespace(base)
    return base, segments
