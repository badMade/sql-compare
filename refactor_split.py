def split_top_level(s: str, sep: str) -> list:
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
        buf.append(scanner.step())

    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]
