import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# Identify the block of html += ...
# It starts with html = "<!DOCTYPE html>...
# Ends with html += "\n</body></html>"

lines = content.splitlines()
start = -1
end = -1

for i, line in enumerate(lines):
    if 'html = "<!DOCTYPE html>' in line:
        start = i
    if 'html += "\\n</body></html>"' in line:
        end = i
        break

if start != -1 and end != -1:
    print(f"Reverting html lines {start}-{end}")

    f_string = r'''    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SQL Compare Report</title>
<style>
body {{ font-family: Segoe UI, Tahoma, Arial, sans-serif; margin: 16px; color: #111; }}
h1,h2 {{ margin: 12px 0; }}
table.diff {{ font-family: Consolas, monospace; font-size: 12px; border-collapse: collapse; width: 100%; }}
table.diff td, table.diff th {{ border: 1px solid #ddd; padding: 4px 6px; vertical-align: top; }}
table.diff thead th {{ background: #f6f8fa; }}
/* HtmlDiff cell classes */
.diff_add {{ background: #e6ffed; color: #1a7f37; }}   /* additions: green */
.diff_sub {{ background: #ffeef0; color: #cf222e; }}   /* deletions: red */
.diff_chg {{ background: #fff5b1; color: #4d2d00; }}   /* changes: amber */
/* Line number cols */
.diff_next, .diff_header {{ background: #f6f8fa; color: #57606a; }}
</style>
</head><body>
{''.join(sections)}
</body></html>"""'''

    lines[start:end+1] = f_string.splitlines()

    with open("sql_compare.py", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Reverted.")
else:
    print("Could not find html block to revert.")
