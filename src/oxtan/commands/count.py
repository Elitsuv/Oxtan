"""count command: count rows in a table."""

import sys

from oxtan.core.connection import execute_query
from oxtan.core.profiles import ProfileManager
from oxtan.core.security import quote_identifier, validate_identifier


def setup(parser):
    """Setup arguments for count command."""
    parser.description = "Count the total number of rows in a table."
    parser.add_argument("table", help="Name of table to count")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute count command."""
    validate_identifier(args.table)
    _, prof = pm.get_profile()
    sql = f"SELECT COUNT(*) AS total FROM {quote_identifier(args.table)}"  # nosec B608
    cols, chunks = execute_query(prof, sql, read_only=True)
    rows = list(chunks)
    total = rows[0][0]["total"] if rows and rows[0] else 0
    sys.stdout.write(f"{total}\n")
    return 0
