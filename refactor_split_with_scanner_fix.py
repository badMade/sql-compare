def split_top_level(s: str, sep: str) -> list:
    """Split by sep at top-level (not inside quotes/parentheses/brackets/backticks)."""
    parts = []
    buf = []
    scanner = _SQLScanner(s)

    # We need to iterate carefully.
    # scanner.step() advances by 1 character (or 2 if escaped).
    # But if we match the separator, we want to skip it.

    while scanner.i < scanner.n:
        # Check separator match
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
