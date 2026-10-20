"""Portable JSON/CSV/HTML evidence and transactional history by Jason Stys.

Functions: export_report, save_history. Variables: supported formats, SQL schema.
HTML escapes evidence; CSV emits generated IDs, fixed labels and numbers. Line map: docs/CODE_INDEX.md.
"""

import csv
import io
import json
import sqlite3
from contextlib import closing
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any

from flightlab.engine import run_id


def export_report(run: dict[str, Any], format_name: str) -> tuple[bytes, str]:
    """Render generated build_run evidence, not uploads; CSV uses fixed units and identifiers."""
    if format_name == "json":
        return (json.dumps(run, indent=2, allow_nan=False) + "\n").encode(), "application/json"
    if format_name == "csv":
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        from flightlab.engine import FIELDS

        writer.writerow(("run_sha256", "series", "clock", *FIELDS))
        for series in ("experiment", "reference"):
            for sample in run[series]["samples"]:
                writer.writerow(
                    (run["id"], series, "logical ticks", *(sample[key] for key in FIELDS))
                )
        return stream.getvalue().encode(), "text/csv"
    if format_name == "html":
        payload = escape(json.dumps(run, indent=2, allow_nan=False))
        html = (
            "<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'\">"
            "<title>Flight Software Testbed evidence</title><h1>Flight executive evidence</h1>"
            "<p>By Jason Stys. Software-only synthetic executive. Not flight software, a real-time system or flight qualified.</p>"
            f"<pre>{payload}</pre></html>"
        )
        return html.encode(), "text/html"
    raise ValueError("Expected json, csv or html")


def save_history(path: Path, run: dict[str, Any]) -> str:
    """Store at most 100 immutable, content-verified runs; SQL values are parameterized.

    path is explicitly chosen by the local CLI, never accepted from HTTP. Existing
    matching runs are idempotent. Reaching the cap refuses new data without deletion.
    """
    if run.get("id") != run_id(run):
        raise ValueError("Run content hash does not match")
    schema = files("flightlab").joinpath("resources/history.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(path, timeout=5)) as connection, connection:
        connection.executescript(schema)
        connection.execute("BEGIN IMMEDIATE")
        exists = connection.execute("SELECT 1 FROM runs WHERE id = ?", (run["id"],)).fetchone()
        if not exists:
            count = connection.execute("SELECT count(*) FROM runs").fetchone()
            if count is not None and count[0] >= 100:
                raise ValueError("History full (100 runs); choose a new database")
            connection.execute(
                "INSERT INTO runs(id, scenario, report_json) VALUES (?, ?, ?)",
                (run["id"], run["scenario"], json.dumps(run, allow_nan=False)),
            )
    return str(run["id"])
