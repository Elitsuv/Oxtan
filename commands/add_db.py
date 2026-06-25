import argparse

def setup(parser: argparse.ArgumentParser):
    """Adds a new database connection profile."""
    parser.add_argument("name", help="Name for the database profile")
    
    parser.add_argument("--host", required=True, help="Database host")
    parser.add_argument("--user", required=True, help="Database username")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--database", required=True, help="Database name")
    
    # Optional connection arguments
    parser.add_argument("--port", type=int, default=3306, help="Database port (default: 3306)")

def run(args: argparse.Namespace):
    from config.profiles import ProfileManager
    from formatters.terminal import print_success
    
    pm = ProfileManager()
    pm.save_profile(
        name=args.name,
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        database=args.database
    )
    print_success(f"Profile '{args.name}' saved successfully!")
