## 2024-05-01 - XSS in HTML Report Generation
**Vulnerability:** Cross-Site Scripting (XSS) in HTML report generation due to unescaped string interpolation and unescaped table parameters in `difflib.HtmlDiff`.
**Learning:** `difflib.HtmlDiff().make_table()` escapes the primary content differences but *does not* escape metadata parameters like `fromdesc` and `todesc`. Similarly, explicitly interpolating unescaped inputs (like diff summaries) into f-strings for HTML generation exposes the application to XSS.
**Prevention:** Always use `html.escape()` when injecting dynamic text (such as file names, headers, or computed summary bullet points) into HTML, even when using standard libraries like `difflib` that provide HTML formatting features.
