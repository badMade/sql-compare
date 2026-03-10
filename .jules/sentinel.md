## 2025-03-10 - HTML Escape in Text/Tkinter Report generation
**Vulnerability:** XSS (Cross-Site Scripting) vulnerability during HTML report generation in `generate_report`.
**Learning:** `difflib.HtmlDiff.make_table` does not automatically escape custom arguments like `fromdesc`, `todesc`, or user-supplied strings manually injected via Python f-strings (like `result["summary"]`).
**Prevention:** Always explicitly apply `html.escape()` to dynamically generated content that gets rendered as HTML, even if partial HTML escaping is handled downstream by utility libraries. Watch out for variable shadowing (e.g., using `html` as a string variable which shadows the `html` standard library module).
