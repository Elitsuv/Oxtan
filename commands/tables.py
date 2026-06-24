import argparse

def setup(parser: argparse.ArgumentParser):
    """Lists all tables in the active database."""
    pass

def run(args: argparse.Namespace):
    from formatters.terminal import print_info
    print_info("tables command executed. (Architecture stub)")
