with open("sql_compare.py", "r") as f:
    content = f.read()

content = content.replace("re.VERBOSE,\n)", "re.VERBOSE | re.IGNORECASE,\n)")

with open("sql_compare.py", "w") as f:
    f.write(content)
