## 2024-05-19 - Fast String Traversal
**Learning:** Python's `while i < len(s): ch = s[i]` character-by-character string traversal loops are significant performance bottlenecks for string parsing operations (like identifying quotes, comments, or parenthesis).
**Action:** Always replace them with `re.finditer` using compiled regexes to offload the scanning loop to C, even for relatively complex state machines.
