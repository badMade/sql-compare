def test(join_kw):
    seg_type = join_kw.replace(" OUTER", "")
    seg_type = seg_type.upper()
    seg_type = seg_type.replace(" JOIN", "").strip()
    if seg_type == "":
        seg_type = "INNER"
    return seg_type

print(f"'JOIN' -> '{test('JOIN')}'")
print(f"'INNER JOIN' -> '{test('INNER JOIN')}'")
