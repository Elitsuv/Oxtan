import argparse

def setup(parser: argparse.ArgumentParser):
    """Sets the active database profile."""
    pass

def run(args: argparse.Namespace):
    from formatters.terminal import print_info
    print_info("use command executed. (Architecture stub)")
