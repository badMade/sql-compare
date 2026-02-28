with open('sql_compare.py', 'r') as f:
    content = f.read()

content = content.replace("i += m.end()", "i = m.end()")
content = content.replace("i += m2.end()", "i = m2.end()")

with open('sql_compare.py', 'w') as f:
    f.write(content)
