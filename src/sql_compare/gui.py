# -*- coding: utf-8 -*-
"""
Tkinter GUI for SQL comparison.
"""
import os
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

from .core import compare_sql
from .report import generate_report_html, generate_report_text

class SQLCompareGUI:
    def __init__(self, root):
        self.root = root
        root.title("SQL Compare")
        root.geometry("980x780")

        self.sql1_path = tk.StringVar()
        self.sql2_path = tk.StringVar()
        self.mode = tk.StringVar(value="both")
        self.ignore_ws = tk.BooleanVar(value=False)
        self.enable_join = tk.BooleanVar(value=True)
        self.allow_full = tk.BooleanVar(value=False)
        self.allow_left = tk.BooleanVar(value=False)

        pad = {"padx": 8, "pady": 6}

        frm_top = ttk.Frame(root); frm_top.pack(fill="x", **pad)
        ttk.Label(frm_top, text="SQL File 1:").grid(row=0, column=0, sticky="w")
        e1 = ttk.Entry(frm_top, textvariable=self.sql1_path, width=90); e1.grid(row=0, column=1, sticky="we", padx=(8, 8))
        ttk.Button(frm_top, text="Browse...", command=self.browse1).grid(row=0, column=2)
        ttk.Label(frm_top, text="SQL File 2:").grid(row=1, column=0, sticky="w")
        e2 = ttk.Entry(frm_top, textvariable=self.sql2_path, width=90); e2.grid(row=1, column=1, sticky="we", padx=(8, 8))
        ttk.Button(frm_top, text="Browse...", command=self.browse2).grid(row=1, column=2)
        frm_top.columnconfigure(1, weight=1)

        frm_mode = ttk.Frame(root); frm_mode.pack(fill="x", **pad)
        ttk.Label(frm_mode, text="Mode:").pack(side="left")
        for text, val in [("Both", "both"), ("Exact", "exact"), ("Canonical", "canonical")]:
            ttk.Radiobutton(frm_mode, text=text, value=val, variable=self.mode).pack(side="left", padx=6)
        ttk.Checkbutton(frm_mode, text="Ignore whitespace differences", variable=self.ignore_ws).pack(side="left", padx=16)

        frm_flags = ttk.Frame(root); frm_flags.pack(fill="x", **pad)
        self.chk_enable_join = ttk.Checkbutton(frm_flags, text="Enable join reordering", variable=self.enable_join, command=self._toggle_join_options)
        self.chk_enable_join.pack(side="left", padx=6)
        self.chk_full = ttk.Checkbutton(frm_flags, text="Allow FULL OUTER JOIN reordering (heuristic)", variable=self.allow_full)
        self.chk_full.pack(side="left", padx=6)
        self.chk_left = ttk.Checkbutton(frm_flags, text="Allow LEFT JOIN reordering (heuristic)", variable=self.allow_left)
        self.chk_left.pack(side="left", padx=6)
        self._toggle_join_options()  # set initial state

        frm_btns = ttk.Frame(root); frm_btns.pack(fill="x", **pad)
        ttk.Button(frm_btns, text="Compare", command=self.do_compare).pack(side="left")
        ttk.Button(frm_btns, text="Copy Output", command=self.copy_output).pack(side="left", padx=6)
        ttk.Button(frm_btns, text="Clear", command=self.clear_output).pack(side="left", padx=6)
        ttk.Button(frm_btns, text="Save Report…", command=self.save_report).pack(side="left", padx=6)

        frm_out = ttk.Frame(root); frm_out.pack(fill="both", expand=True, **pad)
        self.txt = tk.Text(frm_out, wrap="none", font=("Consolas", 10))
        xscroll = ttk.Scrollbar(frm_out, orient="horizontal", command=self.txt.xview)
        yscroll = ttk.Scrollbar(frm_out, orient="vertical", command=self.txt.yview)
        self.txt.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frm_out.rowconfigure(0, weight=1); frm_out.columnconfigure(0, weight=1)

        ttk.Label(root, text="Tip: CLI supports --strings/--stdin, --mode, --ignore-whitespace, --join-reorder/--no-join-reorder, --allow-full-outer-reorder, --allow-left-reorder, and --report.").pack(anchor="w", padx=8, pady=4)

        self.last_result = None  # cache for report generation

    def _toggle_join_options(self):
        if self.enable_join.get():
            self.chk_full.state(['!disabled'])
            self.chk_left.state(['!disabled'])
        else:
            self.chk_full.state(['disabled'])
            self.chk_left.state(['disabled'])

    def browse1(self):
        path = filedialog.askopenfilename(title="Select SQL File 1",
                                          filetypes=[("SQL files", "*.sql *.txt"), ("All files", "*.*")])
        if path: self.sql1_path.set(path)

    def browse2(self):
        path = filedialog.askopenfilename(title="Select SQL File 2",
                                          filetypes=[("SQL files", "*.sql *.txt"), ("All files", "*.*")])
        if path: self.sql2_path.set(path)

    def clear_output(self):
        self.txt.delete("1.0", "end")

    def copy_output(self):
        try:
            content = self.txt.get("1.0", "end-1c")
            self.root.clipboard_clear(); self.root.clipboard_append(content)
            messagebox.showinfo("Copied", "Output copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    def do_compare(self):
        p1 = self.sql1_path.get().strip(); p2 = self.sql2_path.get().strip()
        if not p1 or not p2:
            messagebox.showwarning("Missing files", "Please select both SQL files."); return
        if not os.path.exists(p1) or not os.path.exists(p2):
            messagebox.showerror("File error", "One or both files do not exist."); return
        try:
            a = Path(p1).read_text(encoding="utf-8", errors="ignore")
            b = Path(p2).read_text(encoding="utf-8", errors="ignore")
            result = compare_sql(
                a, b,
                ignore_ws=self.ignore_ws.get(),
                enable_join_reorder=self.enable_join.get(),
                allow_full_outer=self.allow_full.get(),
                allow_left=self.allow_left.get()
            )
            self.last_result = result
            self.render_result(result, self.mode.get(), self.ignore_ws.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def render_result(self, result: dict, mode: str, ignore_ws: bool):
        self.clear_output()
        # Simple text rendering for GUI text box; HTML report available via Save
        txt = generate_report_text(result, mode, ignore_ws)
        self.txt.insert("1.0", txt)

    def save_report(self):
        if not self.last_result:
            messagebox.showwarning("No results", "Run a comparison first."); return
        path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".html",
            filetypes=[("HTML report", "*.html"), ("Text report", "*.txt")]
        )
        if not path:
            return
        fmt = "html" if path.lower().endswith(".html") else "txt"
        try:
            mode = self.mode.get()
            ignore_ws = self.ignore_ws.get()
            if fmt == "html":
                content = generate_report_html(self.last_result, mode, ignore_ws)
            else:
                content = generate_report_text(self.last_result, mode, ignore_ws)

            Path(path).write_text(content, encoding="utf-8")
            messagebox.showinfo("Saved", f"Report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report:\n{e}")

def launch_gui():
    if not TK_AVAILABLE:
        print("Tkinter is not available. Provide CLI inputs, or install Python with Tk support.", file=sys.stderr)
        sys.exit(2)
    root = tk.Tk()
    SQLCompareGUI(root)
    root.mainloop()
