import re

with open("sql_compare.py", "r", encoding="utf-8") as f:
    content = f.read()

# I am explicitly replacing the literal backspace character with `\b`.
# The literal backspace character is `\x08`.
content = content.replace('\x08', r'\b')

with open("sql_compare.py", "w", encoding="utf-8") as f:
    f.write(content)
