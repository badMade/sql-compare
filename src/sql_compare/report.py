# -*- coding: utf-8 -*-
"""
Report generation for SQL comparisons.
"""
import difflib

def generate_report_text(result: dict, mode: str, ignore_ws: bool) -> str:
    lines = []
    lines.append("=== SQL Compare Report ===")
    lines.append(f"Whitespace-only equal: {'YES' if result['ws_equal'] else 'NO'}")
    lines.append(f"Exact tokens equal   : {'YES' if result['exact_equal'] else 'NO'}")
    lines.append(f"Canonical equal      : {'YES' if result['canonical_equal'] else 'NO'}")
    lines.append("")
    lines.append("-- Summary of differences --")
    for line in result["summary"]:
        lines.append(f"- {line}")
    lines.append("")
    if ignore_ws:
        lines.append("---- Unified Diff (Whitespace-only normalized) ----")
        lines.append(result["diff_ws"] if result["diff_ws"] else "(no differences)")
        lines.append("")
    if mode in ("both", "exact"):
        lines.append("---- Unified Diff (Normalized) ----")
        lines.append(result["diff_norm"] if result["diff_norm"] else "(no differences)")
        lines.append("")
    if mode in ("both", "canonical"):
        lines.append("---- Unified Diff (Canonicalized) ----")
        lines.append(result["diff_can"] if result["diff_can"] else "(no differences)")
        lines.append("")
    return "\n".join(lines)


def generate_report_html(result: dict, mode: str, ignore_ws: bool) -> str:
    hd = difflib.HtmlDiff(wrapcolumn=120)

    def mk(title, a, b, fromname, toname):
        table = hd.make_table(a.splitlines(), b.splitlines(), fromdesc=fromname, todesc=toname, context=True, numlines=3)
        return f"<h2>{title}</h2>\n{table}"

    sections = []
    sections.append("<h1>SQL Compare Report</h1>")
    sections.append("<h2>Summary</h2>")
    sections.append("<ul>")
    sections.append(f"<li>Whitespace-only equal: <b>{'YES' if result['ws_equal'] else 'NO'}</b></li>")
    sections.append(f"<li>Exact tokens equal: <b>{'YES' if result['exact_equal'] else 'NO'}</b></li>")
    sections.append(f"<li>Canonical equal: <b>{'YES' if result['canonical_equal'] else 'NO'}</b></li>")
    sections.append("</ul>")

    sections.append("""
    <h2>Summary of differences</h2>
    <ul>
    """ + "\n".join(f"<li>{line}</li>" for line in result["summary"]) + "</ul>")

    sections.append("""
    <div style="margin:8px 0;">
      <strong>Legend:</strong>
      <span style="background:#e6ffed;border:1px solid #34d058;padding:2px 6px;margin-left:6px;">Added</span>
      <span style="background:#ffeef0;border:1px solid #d73a49;padding:2px 6px;margin-left:6px;">Removed</span>
      <span style="background:#fff5b1;border:1px solid #d9c10c;padding:2px 6px;margin-left:6px;">Changed</span>
    </div>
    """)

    if ignore_ws:
        sections.append(mk("Whitespace-only Diff", result["ws_a"], result["ws_b"], "sql1(ws)", "sql2(ws)"))
    if mode in ("both", "exact"):
        sections.append(mk("Normalized Diff", result["norm_a"], result["norm_b"], "sql1(norm)", "sql2(norm)"))
    if mode in ("both", "canonical"):
        sections.append(mk("Canonicalized Diff", result["can_a"], result["can_b"], "sql1(canon)", "sql2(canon)"))

    html = f"""<!DOCTYPE html>
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
</body></html>"""
    return html
