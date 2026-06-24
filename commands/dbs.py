import argparse

def setup(parser: argparse.ArgumentParser):
    """Lists all saved database profiles."""
    pass

def run(args: argparse.Namespace):
    from formatters.terminal import print_info
    print_info("dbs command executed. (Architecture stub)")
