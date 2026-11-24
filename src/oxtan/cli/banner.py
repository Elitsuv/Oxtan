"""Oxtan banner and cheat sheet.

Suppressed when piped, in quiet mode, or in data-producing commands.
Respects NO_COLOR.
"""

import os
import sys

from oxtan.cli.output import safe_write

DOODLE_LINES = [
    r"  ___  _  _ _____ _   _  _ ",
    r" / _ \ \/ /_   _/_\ | \| |",
    r"| (_) |  /  | |/ _ \| .` |",
    r" \___/ _/\_ | /_/ \_\_|\_|",
]

CHEAT_SHEET = """Oxtan v0.1.0 - Fast, safe command-line tool for MySQL

Commands:
  add-db <name>          Save a database connection profile
  use <name>             Switch the active database profile
  dbs                    List all saved connection profiles
  current                Show active connection profile
  tables, t              List tables in active database
  schema, s <table>      Show table column schema
  peek, p <table>        Preview top rows (--limit, default: 5)
  count <table>          Count total rows in a table
  query, q "<sql>"       Run query (READ-ONLY by default; use --write)
  doctor                 Diagnose environment & connectivity
  about                  Show banner and cheat sheet

Options:
  --format table|json|csv  Output format (default: table)
  --version                Show version
  --quiet                  Suppress notes and banner
  --no-color               Disable ANSI color
  --debug                  Show tracebacks on error
"""


def should_suppress_banner(quiet: bool = False, force: bool = False, stream=None) -> bool:
    """Determine whether banner/doodle should be suppressed."""
    if quiet:
        return True
    target = stream or sys.stderr
    # The doodle never appears when piped or redirected
    if not hasattr(target, "isatty") or not target.isatty():
        return True
    return False


def is_color_enabled(no_color_flag: bool = False, stream=None) -> bool:
    """Check if color is enabled (respects NO_COLOR env var and --no-color flag)."""
    if no_color_flag:
        return False
    if "NO_COLOR" in os.environ and os.environ["NO_COLOR"].strip() != "":
        return False
    target = stream or sys.stderr
    if not hasattr(target, "isatty") or not target.isatty():
        return False
    return True


def print_banner_and_cheatsheet(
    quiet: bool = False,
    force: bool = False,
    no_color: bool = False,
    stream=None,
) -> None:
    """Print the ASCII doodle and cheat sheet."""
    target = stream or sys.stderr
    if should_suppress_banner(quiet=quiet, force=force, stream=target):
        return

    color = is_color_enabled(no_color_flag=no_color, stream=target)
    cyan = "\033[36m" if color else ""
    reset = "\033[0m" if color else ""

    doodle = "\n".join(f"{cyan}{line}{reset}" for line in DOODLE_LINES)
    safe_write(target, f"\n{doodle}\n\n{CHEAT_SHEET}\n")
