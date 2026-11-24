"""schema command (alias: s): show table column schema."""

from oxtan.cli.output import print_results
from oxtan.core.connection import execute_query
from oxtan.core.profiles import ProfileManager
from oxtan.core.security import quote_identifier, validate_identifier


def setup(parser):
    """Setup arguments for schema command."""
    parser.description = "Show column schema for a table."
    parser.add_argument("table", help="Name of table to describe")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Output format")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute schema command."""
    validate_identifier(args.table)
    _, prof = pm.get_profile()
    sql = f"DESCRIBE {quote_identifier(args.table)}"
    cols, chunks = execute_query(prof, sql, read_only=True)
    all_rows = []
    for chunk in chunks:
        all_rows.extend(chunk)

    print_results(cols, all_rows, fmt=args.format, quiet=quiet)
    return 0
