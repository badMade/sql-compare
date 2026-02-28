import re

with open('sql_compare.py', 'r') as f:
    content = f.read()

# We need to replace the __init__ method in SQLCompareGUI
new_init = """    def __init__(self, root):
        self.root = root
        root.title("SQL Compare")
        root.geometry("980x780")

        self._init_vars()

        pad = {"padx": 8, "pady": 6}
        self._build_file_selection_frame(root, pad)
        self._build_mode_frame(root, pad)
        self._build_flags_frame(root, pad)
        self._build_buttons_frame(root, pad)
        self._build_output_frame(root, pad)

        ttk.Label(root, text="Tip: CLI supports --strings/--stdin, --mode, --ignore-whitespace, --join-reorder/--no-join-reorder, --allow-full-outer-reorder, --allow-left-reorder, and --report.").pack(anchor="w", padx=8, pady=4)

        self.last_result = None  # cache for report generation

    def _init_vars(self):
        self.sql1_path = tk.StringVar()
        self.sql2_path = tk.StringVar()
        self.mode = tk.StringVar(value="both")
        self.ignore_ws = tk.BooleanVar(value=False)
        self.enable_join = tk.BooleanVar(value=True)
        self.allow_full = tk.BooleanVar(value=False)
        self.allow_left = tk.BooleanVar(value=False)

    def _build_file_selection_frame(self, root, pad):
        frm_top = ttk.Frame(root); frm_top.pack(fill="x", **pad)
        ttk.Label(frm_top, text="SQL File 1:").grid(row=0, column=0, sticky="w")
        e1 = ttk.Entry(frm_top, textvariable=self.sql1_path, width=90); e1.grid(row=0, column=1, sticky="we", padx=(8, 8))
        ttk.Button(frm_top, text="Browse...", command=self.browse1).grid(row=0, column=2)
        ttk.Label(frm_top, text="SQL File 2:").grid(row=1, column=0, sticky="w")
        e2 = ttk.Entry(frm_top, textvariable=self.sql2_path, width=90); e2.grid(row=1, column=1, sticky="we", padx=(8, 8))
        ttk.Button(frm_top, text="Browse...", command=self.browse2).grid(row=1, column=2)
        frm_top.columnconfigure(1, weight=1)

    def _build_mode_frame(self, root, pad):
        frm_mode = ttk.Frame(root); frm_mode.pack(fill="x", **pad)
        ttk.Label(frm_mode, text="Mode:").pack(side="left")
        for text, val in [("Both", "both"), ("Exact", "exact"), ("Canonical", "canonical")]:
            ttk.Radiobutton(frm_mode, text=text, value=val, variable=self.mode).pack(side="left", padx=6)
        ttk.Checkbutton(frm_mode, text="Ignore whitespace differences", variable=self.ignore_ws).pack(side="left", padx=16)

    def _build_flags_frame(self, root, pad):
        frm_flags = ttk.Frame(root); frm_flags.pack(fill="x", **pad)
        self.chk_enable_join = ttk.Checkbutton(frm_flags, text="Enable join reordering", variable=self.enable_join, command=self._toggle_join_options)
        self.chk_enable_join.pack(side="left", padx=6)
        self.chk_full = ttk.Checkbutton(frm_flags, text="Allow FULL OUTER JOIN reordering (heuristic)", variable=self.allow_full)
        self.chk_full.pack(side="left", padx=6)
        self.chk_left = ttk.Checkbutton(frm_flags, text="Allow LEFT JOIN reordering (heuristic)", variable=self.allow_left)
        self.chk_left.pack(side="left", padx=6)
        self._toggle_join_options()  # set initial state

    def _build_buttons_frame(self, root, pad):
        frm_btns = ttk.Frame(root); frm_btns.pack(fill="x", **pad)
        ttk.Button(frm_btns, text="Compare", command=self.do_compare).pack(side="left")
        ttk.Button(frm_btns, text="Copy Output", command=self.copy_output).pack(side="left", padx=6)
        ttk.Button(frm_btns, text="Clear", command=self.clear_output).pack(side="left", padx=6)
        ttk.Button(frm_btns, text="Save Report…", command=self.save_report).pack(side="left", padx=6)

    def _build_output_frame(self, root, pad):
        frm_out = ttk.Frame(root); frm_out.pack(fill="both", expand=True, **pad)
        self.txt = tk.Text(frm_out, wrap="none", font=("Consolas", 10))
        xscroll = ttk.Scrollbar(frm_out, orient="horizontal", command=self.txt.xview)
        yscroll = ttk.Scrollbar(frm_out, orient="vertical", command=self.txt.yview)
        self.txt.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frm_out.rowconfigure(0, weight=1); frm_out.columnconfigure(0, weight=1)"""

# Find the old __init__
pattern = r"    def __init__\(self, root\):.*?(?=\n    def _toggle_join_options)"
new_content = re.sub(pattern, new_init, content, flags=re.DOTALL)

with open('sql_compare.py', 'w') as f:
    f.write(new_content)

print("Refactoring complete.")
