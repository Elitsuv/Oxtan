import argparse

def setup(parser: argparse.ArgumentParser):
    """Sets the active db profiles"""

    parser.add_argument("name", help="Active profiles to use: ")

    def run(args: argparse.Namespace):
        from config.profiles import ProfileManager
        from formatters.terminal import print_success, print_error

        pm = ProfileManager()
        try:
            pm.set_active_profile(args.name)
            print_success(f"Profile '{args.name}' activated successfully!")
        except ValueError as e:
            print_error(str(e))