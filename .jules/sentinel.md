## 2025-01-01 - HTML Report XSS Vulnerability
**Vulnerability:** XSS vulnerability in HTML report generation when creating an HTML diff report. The summary items, title, and descriptions were not escaped before insertion.
**Learning:** `difflib.HtmlDiff` does escape its inputs, but strings constructed outside `difflib.HtmlDiff` manually were not HTML-escaped. In this codebase, the `result["summary"]`, `fromdesc`/`todesc`, and headings (`title`) were injected directly via f-strings into the raw HTML string, creating an XSS risk.
**Prevention:** Always HTML-escape variables when embedding them into raw HTML using f-strings or manual string concatenation, leveraging `html.escape()`.
