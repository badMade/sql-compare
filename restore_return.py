import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find is_reorderable
if "def is_reorderable(t: str) -> bool:" in content:
    # Replace the block.
    # It ends with return True (indented)
    # We want to add return False

    # Using regex to match the function body
    pattern = r'(def is_reorderable\(t: str\) -> bool:.*?if allow_left and tt == "LEFT":\s+return True)(\s+)'

    # We want to append return False
    # Note: re.DOTALL is needed

    replacement = r'\1\n        return False\2'

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        with open("sql_compare.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Restored return False.")
    else:
        print("Regex match failed.")
else:
    print("Function not found.")
