def top_level_find_kw(sql: str, kw: str, start: int = 0):
    """Find top-level occurrence of keyword kw (word boundary) starting at start."""
    kw = kw.upper()
    scanner = _SQLScanner(sql, start)

    while scanner.i < scanner.n:
        if scanner.mode is None and scanner.level == 0:
            m = re.match(rf"\b{re.escape(kw)}\b", sql[scanner.i:])
            if m:
                return scanner.i
        scanner.step()

    return -1
