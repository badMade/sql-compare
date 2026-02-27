import sql_compare

def test_collapse_whitespace():
    input_str = "  a   b  c  "
    expected = "a b c"
    result = sql_compare.collapse_whitespace(input_str)
    assert result == expected, f"Expected '{expected}', but got '{result}'"
    print("test_collapse_whitespace passed!")

if __name__ == "__main__":
    test_collapse_whitespace()
