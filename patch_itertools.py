with open('sql_compare.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('import re'):
        lines.insert(i + 1, 'import itertools\n')
        break

with open('sql_compare.py', 'w') as f:
    f.writelines(lines)
