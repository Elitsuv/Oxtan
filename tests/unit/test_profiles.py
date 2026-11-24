"""Unit tests for configuration and profile management."""

import json
import os
from unittest.mock import patch

import pytest

from oxtan.core.errors import ConfigurationError, ProfileNotFoundError
from oxtan.core.profiles import ProfileManager


def test_profile_empty_on_missing_file(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)
    data = pm.load_profiles()
    assert data["profiles"] == {}
    assert data["active"] is None
    assert pm.list_profiles() == []
    assert pm.get_active_profile() is None


def test_save_and_retrieve_profile(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile(
        name="local_dev",
        host="localhost",
        port=3306,
        user="root",
        password="",  # Empty password must work
        database="test_db",
    )

    # Automatically set as active when first profile added
    assert pm.get_active_profile() == "local_dev"
    assert pm.list_profiles() == ["local_dev"]

    name, prof = pm.get_profile("local_dev")
    assert name == "local_dev"
    assert prof["host"] == "localhost"
    assert prof["port"] == 3306
    assert prof["user"] == "root"
    assert prof["password"] == ""
    assert prof["database"] == "test_db"

    # Default get_profile retrieves active
    active_name, active_prof = pm.get_profile()
    assert active_name == "local_dev"
    assert active_prof["database"] == "test_db"


def test_atomic_write_creates_valid_file(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "nested", "dir", "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile("prod", "10.0.0.1", 3306, "admin", "secret", "proddb")
    assert os.path.exists(config_file)

    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "prod" in data["profiles"]


def test_posix_permissions(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    with patch("os.name", "posix"):
        with patch("os.chmod") as mock_chmod:
            pm.save_profile("p", "host", 3306, "user", "pass", "db")
            # Ensure chmod with 0o600 was called
            calls = [call for call in mock_chmod.call_args_list if call[0][1] == 0o600]
            assert len(calls) >= 1


def test_corrupt_json_raises_configuration_error(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json")

    pm = ProfileManager(config_file)
    with pytest.raises(ConfigurationError) as exc_info:
        pm.load_profiles()
    assert "corrupted" in str(exc_info.value).lower()


def test_delete_active_profile_resets_active(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile("p1", "host1", 3306, "u1", "pass", "db1")
    pm.save_profile("p2", "host2", 3306, "u2", "pass", "db2")

    pm.set_active_profile("p1")
    assert pm.get_active_profile() == "p1"

    # Delete active profile
    assert pm.delete_profile("p1") is True
    assert pm.get_active_profile() is None
    assert pm.list_profiles() == ["p2"]

    # Deleting non-existent profile returns False
    assert pm.delete_profile("non_existent") is False


def test_switch_active_profile(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile("p1", "host1", 3306, "u1", "pass", "db1")
    pm.save_profile("p2", "host2", 3306, "u2", "pass", "db2")

    pm.set_active_profile("p2")
    assert pm.get_active_profile() == "p2"

    with pytest.raises(ProfileNotFoundError):
        pm.set_active_profile("unknown")


def test_profile_validation_errors(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    with pytest.raises(ConfigurationError):
        pm.save_profile("", "host", 3306, "u", "p", "d")

    with pytest.raises(ConfigurationError):
        pm.save_profile("a" * 65, "host", 3306, "u", "p", "d")

    with pytest.raises(ConfigurationError):
        pm.save_profile("bad name with spaces", "host", 3306, "u", "p", "d")

    with pytest.raises(ConfigurationError):
        pm.save_profile("p", "", 3306, "u", "p", "d")  # empty host

    with pytest.raises(ConfigurationError):
        pm.save_profile("p", "host", 99999, "u", "p", "d")  # invalid port

    with pytest.raises(ConfigurationError):
        pm.save_profile("p", "host", 3306, "", "p", "d")  # empty user

    with pytest.raises(ConfigurationError):
        pm.save_profile("p", "host", 3306, "u", "p", "")  # empty db


def test_default_config_path():
    pm = ProfileManager()
    assert ".oxtan" in pm.config_path


def test_profile_file_is_not_dict(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("[1, 2, 3]")
    pm = ProfileManager(config_file)
    with pytest.raises(ConfigurationError) as exc_info:
        pm.load_profiles()
    assert "must be a json object" in str(exc_info.value).lower()


def test_get_profile_when_no_active(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)
    with pytest.raises(ProfileNotFoundError) as exc_info:
        pm.get_profile()
    assert "no active database profile" in str(exc_info.value).lower()


def test_os_error_on_load(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("{}")
    with patch("builtins.open", side_effect=OSError("Read failure")):
        with pytest.raises(ConfigurationError) as exc_info:
            pm.load_profiles()
        assert "failed to read configuration" in str(exc_info.value).lower()


def test_profiles_with_similar_names(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile("dev", "host_dev", 3306, "u1", "p1", "db1")
    pm.save_profile("dev-1", "host_dev1", 3306, "u2", "p2", "db2")
    pm.save_profile("dev_db", "host_devdb", 3306, "u3", "p3", "db3")

    assert pm.list_profiles() == ["dev", "dev-1", "dev_db"]
    name1, prof1 = pm.get_profile("dev")
    name2, prof2 = pm.get_profile("dev-1")
    name3, prof3 = pm.get_profile("dev_db")

    assert prof1["host"] == "host_dev"
    assert prof2["host"] == "host_dev1"
    assert prof3["host"] == "host_devdb"


def test_repeated_add_db_updates_profile(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    pm.save_profile("myprofile", "host1", 3306, "user1", "pass1", "db1")
    _, prof_before = pm.get_profile("myprofile")
    assert prof_before["host"] == "host1"

    # Update with new host and port
    pm.save_profile("myprofile", "host2", 3307, "user2", "pass2", "db2")
    _, prof_after = pm.get_profile("myprofile")
    assert prof_after["host"] == "host2"
    assert prof_after["port"] == 3307


def test_atomic_write_os_error_handling(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)

    with patch("tempfile.mkstemp", side_effect=OSError("Permission denied on read-only directory")):
        with pytest.raises(ConfigurationError) as exc_info:
            pm.save_profile("dev", "localhost", 3306, "root", "", "test")
        assert "failed to write configuration" in str(exc_info.value).lower()
