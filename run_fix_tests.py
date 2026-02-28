import re
with open("sql_compare.py", "r") as f:
    text = f.read()

text = "import itertools\n" + text
with open("sql_compare.py", "w") as f:
    f.write(text)
