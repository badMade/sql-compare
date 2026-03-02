## 2024-05-02 - [XSS in HTML Report Generation]
**Vulnerability:** The HTML report generation feature in `sql_compare.py` injected unescaped variables (specifically from the `result["summary"]` list) directly into an f-string template, creating a Cross-Site Scripting (XSS) vulnerability if the summary contained malicious input.
**Learning:** This vulnerability existed because the script relied solely on Python's built-in `difflib.HtmlDiff` for diff content, which correctly escapes differences, but failed to apply manual escaping to custom strings injected into the surrounding HTML boilerplate.
**Prevention:** Always use `html.escape()` from the standard library to sanitize strings when injecting dynamic content directly into HTML using f-strings or string concatenation.
