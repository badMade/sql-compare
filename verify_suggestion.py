def strip_sql_comments_original(s: str) -> str:
    # 1. Block comments (iterative approach to avoid ReDoS)
    out = []
    last_pos = 0
    while True:
        start_pos = s.find("/*", last_pos)
        if start_pos == -1:
            out.append(s[last_pos:])
            break
        end_pos = s.find("*/", start_pos + 2)
        if end_pos == -1:
            # No closing marker found; keep the rest as-is
            out.append(s[last_pos:])
            break

        # We found a comment from start_pos to end_pos + 2
        out.append(s[last_pos:start_pos])
        last_pos = end_pos + 2

    s = "".join(out)
    return s

def strip_sql_comments_suggested(s: str) -> str:
    # The suggested implementation
    if "/*" in s:
        parts = s.split("/*")
        processed_parts = [parts[0]]
        for part in parts[1:]:
            if "*/" in part:
                _, rest = part.split("*/", 1)
                processed_parts.append(rest)
            else:
                processed_parts.append("/*" + part)
        s = "".join(processed_parts)
    return s

test_cases = [
    ("SELECT /* comment */ 1", "SELECT  1"),
    ("/* A */ /* B */", "  "),
    ("/* unclosed", "/* unclosed"),
    ("/* A /* B */", "")  # This is the tricky one!
]

for i, (inp, expected) in enumerate(test_cases):
    print(f"--- Case {i+1}: {inp!r} ---")
    orig = strip_sql_comments_original(inp)
    sugg = strip_sql_comments_suggested(inp)

    print(f"Original:  {orig!r}")
    print(f"Suggested: {sugg!r}")

    if orig != sugg:
        print("MISMATCH!")
    else:
        print("MATCH")

    if orig != expected:
        # Note: Original implementation matches regex behavior for the tricky case.
        # Regex behavior for '/* A /* B */' is to strip it entirely (first /* matches first */).
        # My find loop does the same.
        pass
