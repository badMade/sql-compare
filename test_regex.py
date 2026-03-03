import re
text = "hello INNER JOIN world"
i = 6
m = re.match(r"\bINNER JOIN\b", text[i:])
print("sliced end:", m.end())

pattern = re.compile(r"\bINNER JOIN\b")
m2 = pattern.match(text, i)
print("pos end:", m2.end())
