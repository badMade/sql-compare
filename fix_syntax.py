with open('sql_compare.py', 'r') as f:
    content = f.read()

bad_line = 'if not (ch in ("\'", \'"\', \'[\', \'`\') or token.upper().startswith("E\\"\")):'
fixed_line = 'if not (ch in ("\'", \'\"\', \'[\', \'`\') or token.upper().startswith("E\\"")):'
# In the file it was written as startswith("E"")): because of quoting issue.

import re
content = re.sub(r'token\.upper\(\)\.startswith\("E""\)', 'token.upper().startswith("E\\"")', content)
with open('sql_compare.py', 'w') as f:
    f.write(content)
