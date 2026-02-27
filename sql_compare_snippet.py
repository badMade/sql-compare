        seg_type = join_kw.replace(" OUTER", "")
        if seg_type.endswith(" JOIN"):
            seg_type = seg_type[:-5]  # Strip " JOIN"
        seg_type = seg_type.strip()

        if seg_type == "":
            seg_type = "INNER"
