import argparse

import argparse

def setup(parser: argparse.ArgumentParser):
    """Shows the current active profile."""
    pass

def run(args: argparse.Namespace):
    from config.profiles import ProfileManager
    from formatters.terminal import print_info, print_error
    
    pm = ProfileManager()
    active_name = pm.get_active_profile()
    
    if active_name:
        profile_data = pm.get_profile(active_name)
        if profile_data:
            print_info(f"Active Profile: {active_name}")
            print(f"  Host:     {profile_data.get('host')}")
            print(f"  Port:     {profile_data.get('port')}")
            print(f"  User:     {profile_data.get('username')}")
            print(f"  Database: {profile_data.get('database')}")
        else:
            print_error(f"Active profile '{active_name}' is set, but its configuration is missing!")
    else:
        print_info("No active profile set. Use 'oxtan use <profile_name>' to set one.")
