def remove_outer_parentheses(s: str) -> str:
    """Remove one or more layers of outer wrapping parentheses if they enclose the full statement."""
    def is_wrapped(text: str) -> bool:
        if not (text.startswith("(") and text.endswith(")")):
            return False
        scanner = _SQLScanner(text)
        # We need to see if level drops to 0 before the very end.
        while scanner.i < scanner.n:
            scanner.step()
            # If level drops to 0 and we are NOT at the end, then it's not fully wrapped.
            # Example: (A) + (B)
            # Starts with (, level 1.
            # After ')', level 0. i is 3. len is 9. 3 < 9. So return False.
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
