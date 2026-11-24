"""Output formatting for Oxtan CLI.

Supports table, json, and csv formatting.
Table formatting is hand-crafted with column alignment and cell truncation,
requiring zero third-party table dependencies and no pandas.
Data goes to stdout; row counts and notes go to stderr.
"""

import csv
import io
import json
import sys
from typing import Any, Dict, Sequence


def truncate_cell(val: Any, max_width: int = 40) -> str:
    """Format and truncate a cell value for clean terminal display."""
    if val is None:
        return "NULL"
    if isinstance(val, (bytes, bytearray)):
        s = f"blob({len(val)}B)"
    else:
        s = str(val).replace("\r", " ").replace("\n", " ")

    if len(s) > max_width:
        return s[: max_width - 3] + "..."
    return s


def format_table(
    columns: Sequence[str],
    rows: Sequence[Dict[str, Any]],
    max_col_width: int = 40,
) -> str:
    """Format data as an aligned ASCII table.

    Maintains column headers even when rows is empty.
    """
    if not columns and rows:
        columns = list(rows[0].keys())

    cols = list(columns)
    if not cols:
        return "(no columns)"

    # Compute maximum width per column
    col_widths: Dict[str, int] = {col: len(col) for col in cols}

    for row in rows:
        for col in cols:
            formatted = truncate_cell(row.get(col), max_width=max_col_width)
            col_widths[col] = max(col_widths[col], len(formatted))

    # Build header and separator
    header_parts = [col.ljust(col_widths[col]) for col in cols]
    header_line = " | ".join(header_parts)
    separator_line = "-+-".join("-" * col_widths[col] for col in cols)

    lines = [header_line, separator_line]

    if not rows:
        lines.append(f"({'0 rows'})")
    else:
        for row in rows:
            row_parts = [truncate_cell(row.get(col), max_width=max_col_width).ljust(col_widths[col]) for col in cols]
            lines.append(" | ".join(row_parts))

    return "\n".join(lines)


def format_json(rows: Sequence[Dict[str, Any]]) -> str:
    """Format rows as a JSON array."""

    # Convert non-serializable objects (datetime, bytes) using str default
    def json_default(obj: Any) -> Any:
        if isinstance(obj, (bytes, bytearray)):
            return f"<blob: {len(obj)} bytes>"
        return str(obj)

    return json.dumps(list(rows), indent=2, default=json_default)


def format_csv(columns: Sequence[str], rows: Sequence[Dict[str, Any]]) -> str:
    """Format rows as CSV with a header row."""
    if not columns and rows:
        columns = list(rows[0].keys())

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    cols = list(columns)
    writer.writerow(cols)

    for row in rows:
        row_vals = []
        for col in cols:
            val = row.get(col)
            if val is None:
                row_vals.append("")
            elif isinstance(val, (bytes, bytearray)):
                row_vals.append(f"<blob: {len(val)} bytes>")
            else:
                row_vals.append(val)
        writer.writerow(row_vals)

    return output.getvalue()


def safe_write(stream, text: str) -> None:
    """Write text to stream safely, handling character encoding errors on legacy consoles."""
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        stream.write(text.encode(encoding, errors="replace").decode(encoding))


def print_results(
    columns: Sequence[str],
    rows: Sequence[Dict[str, Any]],
    fmt: str = "table",
    quiet: bool = False,
    out_stream=None,
    err_stream=None,
) -> None:
    """Output formatted results to stdout, and row count notes to stderr."""
    out = out_stream or sys.stdout
    err = err_stream or sys.stderr

    fmt = fmt.lower().strip()
    if fmt == "json":
        safe_write(out, format_json(rows) + "\n")
    elif fmt == "csv":
        safe_write(out, format_csv(columns, rows))
    else:  # table default
        safe_write(out, format_table(columns, rows) + "\n")
        if not quiet:
            row_count = len(rows)
            label = "1 row" if row_count == 1 else f"{row_count} rows"
            safe_write(err, f"({label})\n")
