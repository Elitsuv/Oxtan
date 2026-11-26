"""Connection profile management for Oxtan.

Profiles are stored in ~/.oxtan/profiles.json with atomic writes and
restricted permissions on POSIX systems (0o600).
"""

import json
import os
import re
import stat
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from oxtan.core.errors import ConfigurationError, ProfileNotFoundError

_PROFILE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


class ProfileManager:
    """Manages database connection profiles."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = os.path.abspath(os.path.expanduser(config_path))
        else:
            self.config_path = os.path.abspath(os.path.expanduser("~/.oxtan/profiles.json"))

    def _ensure_dir(self) -> None:
        """Ensure the parent directory exists."""
        parent = os.path.dirname(self.config_path)
        if parent:
            os.makedirs(parent, mode=0o700, exist_ok=True)

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """Write configuration atomically using a temporary file and restricted permissions."""
        try:
            self._ensure_dir()
            parent = os.path.dirname(self.config_path)
            serialized = json.dumps(data, indent=2)

            # Create temporary file in same directory for atomic replace
            fd, temp_path = tempfile.mkstemp(dir=parent, prefix="oxtan_", suffix=".tmp")
            try:
                with open(fd, "w", encoding="utf-8") as f:
                    f.write(serialized)
                    f.flush()
                    os.fsync(f.fileno())

                # Set 0o600 permissions on POSIX
                if os.name == "posix":
                    os.chmod(temp_path, 0o600)

                os.replace(temp_path, self.config_path)

                if os.name == "posix":
                    os.chmod(self.config_path, 0o600)
            except Exception:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                raise
        except OSError as e:
            raise ConfigurationError(
                f"Failed to write configuration file '{self.config_path}': {e}",
                fix_hint="Check directory permissions or disk space.",
            ) from e

    def load_profiles(self) -> Dict[str, Any]:
        """Load profiles from disk. Returns empty structure if file does not exist."""
        if not os.path.exists(self.config_path):
            return {"profiles": {}, "active": None}

        if os.name == "posix":
            try:
                mode = stat.S_IMODE(os.stat(self.config_path).st_mode)
                if mode & 0o077:
                    sys.stderr.write(
                        f"Warning: '{self.config_path}' has permissive mode {oct(mode)}. "
                        "Run 'chmod 600' to protect credentials.\n"
                    )
            except OSError:
                pass  # nosec B110

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Configuration file at '{self.config_path}' is corrupted: {e}",
                fix_hint=f"Fix the JSON syntax in {self.config_path} or delete it to reset.",
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {e}",
                fix_hint="Check file read permissions.",
            ) from e

        if not isinstance(data, dict):
            raise ConfigurationError(
                "Profile configuration must be a JSON object.",
                fix_hint="Ensure the top-level element in profiles.json is an object.",
            )

        data.setdefault("profiles", {})
        data.setdefault("active", None)
        return data

    def validate_profile_name(self, name: str) -> str:
        """Validate profile name format."""
        if not name or not isinstance(name, str):
            raise ConfigurationError(
                "Profile name cannot be empty.",
                fix_hint="Provide an alphanumeric profile name, e.g. 'dev' or 'prod'.",
            )
        if len(name) > 64:
            raise ConfigurationError(
                f"Profile name '{name[:15]}...' exceeds 64 characters.",
                fix_hint="Use a shorter profile name.",
            )
        if not _PROFILE_NAME_REGEX.match(name):
            raise ConfigurationError(
                f"Invalid profile name '{name}'. Use letters, numbers, hyphens, and underscores only.",
                fix_hint="Remove spaces or special characters.",
            )
        return name

    def save_profile(
        self,
        name: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ) -> None:
        """Save or update a database connection profile."""
        valid_name = self.validate_profile_name(name)

        if not host or not isinstance(host, str):
            raise ConfigurationError("Host cannot be empty.", fix_hint="Specify a valid hostname or IP.")
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigurationError(
                "Port must be an integer between 1 and 65535.", fix_hint="Use port 3306 for MySQL."
            )
        if not user or not isinstance(user, str):
            raise ConfigurationError("User cannot be empty.", fix_hint="Specify a valid database username.")
        if not database or not isinstance(database, str):
            raise ConfigurationError("Database name cannot be empty.", fix_hint="Specify a valid database name.")
        if password is None:
            password = ""  # nosec B105

        data = self.load_profiles()
        data["profiles"][valid_name] = {
            "host": host.strip(),
            "port": port,
            "user": user.strip(),
            "password": password,
            "database": database.strip(),
        }

        # If no active profile, make this the active profile
        if not data.get("active"):
            data["active"] = valid_name

        self._atomic_write(data)

    def get_profile(self, name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Retrieve a profile by name, or the active profile if name is None.

        Returns:
            Tuple of (profile_name, profile_dict)
        """
        data = self.load_profiles()
        profiles = data.get("profiles", {})

        target_name = name
        if not target_name:
            target_name = data.get("active")
            if not target_name:
                raise ProfileNotFoundError(
                    "No active database profile selected.",
                    fix_hint="Use 'oxtan use <profile>' or 'oxtan add-db <profile>' to set one.",
                )

        if target_name not in profiles:
            raise ProfileNotFoundError(
                f"Profile '{target_name}' not found.",
                fix_hint="List available profiles with 'oxtan dbs' or create one with 'oxtan add-db'.",
            )

        return target_name, dict(profiles[target_name])

    def get_active_profile(self) -> Optional[str]:
        """Return the name of the currently active profile, or None."""
        data = self.load_profiles()
        return data.get("active")

    def set_active_profile(self, name: str) -> None:
        """Set the active profile name."""
        data = self.load_profiles()
        if name not in data.get("profiles", {}):
            raise ProfileNotFoundError(
                f"Profile '{name}' does not exist.",
                fix_hint="Add this profile first with 'oxtan add-db' or check 'oxtan dbs'.",
            )
        data["active"] = name
        self._atomic_write(data)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile. If active profile is deleted, active is reset to None."""
        data = self.load_profiles()
        if name not in data.get("profiles", {}):
            return False

        del data["profiles"][name]
        if data.get("active") == name:
            data["active"] = None

        self._atomic_write(data)
        return True

    def list_profiles(self) -> List[str]:
        """Return list of all profile names sorted alphabetically."""
        data = self.load_profiles()
        return sorted(list(data.get("profiles", {}).keys()))
