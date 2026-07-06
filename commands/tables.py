import argparse

def setup(parser: argparse.ArgumentParser):
    """Lists all tables in the active database."""
    pass

def run(args: argparse.Namespace):
    from config.profiles import ProfileManager
    from core.db_operations import OxtanDB
    from formatters.terminal import print_error, print_info

    pm = ProfileManager()
    active_name = pm.get_active_profile_name()
    if active_name is None:
        print_error("No active profile found. Use 'oxtan use <profile_name>' to activate a profile.")
        return

    profile_data = pm.get_profile(active_name)
    if not profile_data:
        print_error(f"Active profile '{active_name}' configuration is missing!")
        return

    db_config = {
        "host": profile_data.get("host"),
        "port": profile_data.get("port"),
        "user": profile_data.get("username"),  # Map saved 'username' to 'user'
        "password": profile_data.get("password"),
        "database": profile_data.get("database")
    }

    try:
        db = OxtanDB(**db_config)
        tables = db.get_tables()
        
        if not tables:
            print_info(f"No tables found in database '{db_config['database']}'.")
        else:
            for table in tables:
                print(table)
                
    except Exception as e:
        print_error(f"Failed to connect or query database: {e}")