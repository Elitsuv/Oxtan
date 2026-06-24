import pandas as pd
import sys
from typing import Union, List, Dict

# Ensure stdout supports emojis on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def print_table(data: Union[List[Dict], pd.DataFrame]):
    """
    Formats and prints data to the terminal.
    
    If the data is a Pandas DataFrame, it utilizes Pandas' built-in representation.
    If it's a list of dictionaries, it prints them sequentially or could be adapted 
    to use a library like rich or tabulate in the future.
    """
    if isinstance(data, pd.DataFrame):
        print(data)
    elif isinstance(data, list):
        if not data:
            print("No results found.")
            return
            
        # Basic formatting for list of dictionaries
        for row in data:
            print(row)
    else:
        print(data)

def print_success(message: str):
    """Prints a success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Prints an error message."""
    print(f"❌ {message}")
    
def print_info(message: str):
    """Prints an info message."""
    print(f"ℹ️ {message}")
