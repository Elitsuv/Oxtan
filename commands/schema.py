import argparse

def setup(parser: argparse.ArgumentParser):
    """Shows the schema for a specific table."""
    # parser.add_argument("table", help="Name of the table")
    pass

def run(args: argparse.Namespace):
    from formatters.terminal import print_info
    print_info("schema command executed. (Architecture stub)")
