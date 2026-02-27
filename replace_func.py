import sys

with open('sql_compare.py', 'r') as f:
    lines = f.readlines()

new_func = """def uppercase_outside_quotes(s: str) -> str:
    \"\"\"
    Uppercase characters outside of quoted regions:
      single quotes '...'; double quotes "..."; [brackets]; `backticks`
    \"\"\"
    scanner = _SQLScanner(s)
    out = []
    while scanner.i < scanner.n:
        in_quote = (scanner.mode is not None)
        text = scanner.step()
        if in_quote:
            out.append(text)
        else:
            out.append(text.upper())
    return "".join(out)
"""

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip().startswith("def uppercase_outside_quotes"):
        start_idx = i
        break

if start_idx != -1:
    # Find end of function (heuristic: next def or class or end of file)
    for i in range(start_idx + 1, len(lines)):
        if line.strip().startswith("def ") or line.strip().startswith("class "): # simple check
            # But indentation matters.
            # Assuming the next top-level def starts with no indent.
            if lines[i].startswith("def ") or lines[i].startswith("class "):
                end_idx = i
                break
    if end_idx == -1:
        end_idx = len(lines)

    # Replace
    lines[start_idx:end_idx] = [new_func + "\n\n"]

    with open('sql_compare.py', 'w') as f:
        f.writelines(lines)
        print("Refactored uppercase_outside_quotes")
else:
    print("Function not found")
