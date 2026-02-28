🎯 **What:** The `uppercase_outside_quotes` function in `sql_compare.py` lacked any unit testing, leaving a gap for a pure string transformation function that should have well-defined expected outputs.
📊 **Coverage:** The new tests cover:
- Basic strings without quotes
- Single quotes
- Double quotes
- Brackets (`[...]`)
- Backticks (`\`. ..\``)
- Multiple and combinations of quotes
- Escaped single quotes (`''`) within a single-quoted string
- Escaped double quotes (`""`) within a double-quoted string
- Unclosed quote safety mechanisms
✨ **Result:** Test suite coverage has been expanded, ensuring that `uppercase_outside_quotes` works properly for edge and regular use cases. Included a missing `itertools` import to the main `sql_compare.py`.
