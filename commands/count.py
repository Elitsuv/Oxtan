import argparse

def setup(parser: argparse.ArgumentParser):
    """Counts the number of rows in a table."""
    # parser.add_argument("table", help="Name of the table")
    pass

def run(args: argparse.Namespace):
    from formatters.terminal import print_info
    print_info("count command executed. (Architecture stub)")
