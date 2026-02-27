# -*- coding: utf-8 -*-
"""
Flask application for SQL Compare.
"""
from flask import Flask, render_template, request
import re
from .core import compare_sql
from .report import generate_report_html

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    # POST handling
    sql1 = request.form.get("sql1", "")
    sql2 = request.form.get("sql2", "")
    mode = request.form.get("mode", "both")

    ignore_ws = "ignore_ws" in request.form
    enable_join = "join_reorder" in request.form
    allow_full = "allow_full" in request.form
    allow_left = "allow_left" in request.form

    result = compare_sql(
        sql1, sql2,
        ignore_ws=ignore_ws,
        enable_join_reorder=enable_join,
        allow_full_outer=allow_full,
        allow_left=allow_left
    )

    # Generate full report HTML
    full_html = generate_report_html(result, mode, ignore_ws)

    # This assumes `generate_report_html` is modified to return only the report body HTML.
    embedded_content = generate_report_html(result, mode, ignore_ws)

    return render_template("result.html", report_content=embedded_content)
