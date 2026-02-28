import re

with open("sql_compare.py", "r") as f:
    content = f.read()

# I need to change CLAUSE_SCANNER_RE flags back from re.VERBOSE | re.IGNORECASE to re.VERBOSE
# Or maybe the tokens should be uppercase matched?
# If we change back to just re.VERBOSE, we will match only uppercase.

content = content.replace("re.VERBOSE | re.IGNORECASE", "re.VERBOSE")
with open("sql_compare.py", "w") as f:
    f.write(content)
