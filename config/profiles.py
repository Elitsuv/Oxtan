import json
import os
from typing import Dict, Any, List, Optional

class ProfileManager:
    """
    Manages Oxtan connection profiles.
    
    This architecture allows storing multiple named configurations 
    (host, port, username, password, database) for easy switching.
    """
    
    def __init__(self, config_path: str = "~/.oxtan/profiles.json"):
        self.config_path = os.path.expanduser(config_path)

        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
    
    def load_profiles(self) -> Dict[str, Any]:
        """Loads all saved profiles."""
        if not os.path.exists(self.config_path):
            return {"profiles": {}, "active": None}

        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"profiles": {}, "active": None}
        
    def save_profile(self, name: str, host: str, port: int, username: str, password: str, database: str):
        """
        Saves a new profile configuration.
        """
        data = self.load_profiles()

        data["profiles"][name] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)
        
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific profile configuration by name.
        """
        data = self.load_profiles()
        return data.get("profiles", {}).get(name)
        
    def delete_profile(self, name: str):
        """
        Deletes a specific profile configuration by name.
        """
        data = self.load_profiles()
        if name in data.get("profiles", {}):
            del data["profiles"][name]
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
                return True
        return False
        
    def set_active_profile(self, name: str):
        """
        Sets a specific profile as the active (default) connection profile.
        """
        data = self.load_profile()
        return data.get("active")
    
    def list_profiles(self) -> List[str]:
        """
        Returns a list of all saved profile names.
        """
        data = self.load_profiles()
        return list(data.get("profiles", {}).keys())
    