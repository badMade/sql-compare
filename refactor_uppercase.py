def uppercase_outside_quotes(s: str) -> str:
    """
    Uppercase characters outside of quoted regions:
      single quotes '...'; double quotes "..."; [brackets]; `backticks`
    """
    out = []
    scanner = _SQLScanner(s)

    # We loop until scanner is exhausted.
    # The 'step' method increments 'i'.
    # We must check if 'i' < 'n' to avoid stepping past end,
    # but 'step' handles boundary checks gracefully (returns "").

    while scanner.i < scanner.n:
        # Determine if we are currently inside quotes
        was_in_quote = (scanner.mode is not None)

        text = scanner.step()

        # If we were in a quote, preserve case.
        # If we were NOT in a quote, uppercase.
        # Note: if text is a quote char starting a quote, upper() is no-op.
        # If text is a quote char ending a quote, was_in_quote is True, so preserved.

        if was_in_quote:
            out.append(text)
        else:
            out.append(text.upper())

    return "".join(out)
