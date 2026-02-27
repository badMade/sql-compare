# -*- coding: utf-8 -*-
"""
CLI entry point for SQL comparison.
"""

import argparse
import sys
import os
import re
from pathlib import Path
from .core import compare_sql
from .report import generate_report_html, generate_report_text


def parse_args(argv):
    p = argparse.ArgumentParser(description="Compare two SQL statements with Exact/Canonical modes and GUI.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("files", nargs="*", help="Two SQL files to compare")
    g.add_argument("--strings", nargs=2, metavar=("SQL1", "SQL2"), help="Provide two SQL strings inline")
    p.add_argument("--stdin", action="store_true", help="Read two SQL statements from stdin separated by a line with ---")
    p.add_argument("--mode", choices=["exact", "canonical", "both"], default="both", help="Comparison mode (default: both)")
    p.add_argument("--ignore-whitespace", action="store_true", help="Consider queries equal if they differ only by whitespace")
    p.add_argument("--web", action="store_true", help="Launch the Web interface")

    # Global join reordering toggle (default ON) + fine-grained flags
    jg = p.add_mutually_exclusive_group()
    jg.add_argument("--join-reorder", dest="join_reorder", action="store_true", help="Enable join reordering (default)")
    jg.add_argument("--no-join-reorder", dest="join_reorder", action="store_false", help="Disable join reordering")
    p.set_defaults(join_reorder=True)

    p.add_argument("--allow-full-outer-reorder", action="store_true", help="When join reordering is enabled, allow FULL OUTER JOIN reordering (heuristic)")
    p.add_argument("--allow-left-reorder", action="store_true", help="When join reordering is enabled, allow LEFT JOIN reordering (heuristic)")

    p.add_argument("--report", help="Write a comparison report to this file (html or txt)")
    p.add_argument("--report-format", choices=["html", "txt"], default="html", help="Report format (default: html)")
    return p.parse_args(argv)


def read_from_stdin_two_parts():
    raw = sys.stdin.read()
    parts = re.split(r"^\s*---\s*$", raw, flags=re.M)
    if len(parts) != 2:
        raise ValueError("When using --stdin, provide exactly two parts separated by a line containing only ---")
    return parts[0].strip(), parts[1].strip()


def load_inputs(args):
    if args.strings:
        return args.strings[0], args.strings[1], "strings"
    if args.stdin:
        a, b = read_from_stdin_two_parts()
        return a, b, "stdin"
    if args.files and len(args.files) == 2:
        f1, f2 = args.files
        a = Path(f1).read_text(encoding="utf-8", errors="ignore")
        b = Path(f2).read_text(encoding="utf-8", errors="ignore")
        return a, b, "files"
    return None, None, None


def print_result_and_exit(result: dict, mode: str, ignore_ws: bool):
    print("=== SQL Compare ===")
    print(f"Whitespace-only equal: {'YES' if result['ws_equal'] else 'NO'}")
    print(f"Exact tokens equal   : {'YES' if result['exact_equal'] else 'NO'}")
    print(f"Canonical equal      : {'YES' if result['canonical_equal'] else 'NO'}")
    print("\n-- Summary of differences --")
    for line in result["summary"]:
        print(f"- {line}")
    print()

    if ignore_ws:
        print("---- Unified Diff (Whitespace-only normalized) ----")
        print(result["diff_ws"] if result["diff_ws"] else "(no differences)")
        print()
    if mode in ("both", "exact"):
        print("---- Unified Diff (Normalized) ----")
        print(result["diff_norm"] if result["diff_norm"] else "(no differences)")
        print()
    if mode in ("both", "canonical"):
        print("---- Unified Diff (Canonicalized) ----")
        print(result["diff_can"] if result["diff_can"] else "(no differences)")
        print()

    if mode == "exact":
        success = (result["ws_equal"] if ignore_ws else result["exact_equal"])
    else:
        success = result["canonical_equal"]
    sys.exit(0 if success else 1)


def run_cli(args):
    a, b, src = load_inputs(args)
    if a is None or b is None:
        print("Provide two files, or --strings, or --stdin; or run with no args to open the GUI.", file=sys.stderr)
        sys.exit(2)

    result = compare_sql(
        a, b,
        ignore_ws=args.ignore_whitespace,
        enable_join_reorder=args.join_reorder,
        allow_full_outer=args.allow_full_outer_reorder,
        allow_left=args.allow_left_reorder
    )

    if args.report:
        try:
            if args.report_format == "html":
                content = generate_report_html(result, args.mode, args.ignore_whitespace)
            else:
                content = generate_report_text(result, args.mode, args.ignore_whitespace)

            Path(args.report).write_text(content, encoding="utf-8")
            print(f"[Report] Saved to: {args.report}")
        except Exception as e:
            print(f"[Report] Failed: {e}", file=sys.stderr)
            sys.exit(2)

    print_result_and_exit(result, args.mode, args.ignore_whitespace)
