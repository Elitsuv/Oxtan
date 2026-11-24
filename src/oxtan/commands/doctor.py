"""doctor command: diagnose environment, configuration, and connectivity."""

import sys

from oxtan.core.connection import test_connection
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for doctor command."""
    parser.description = "Run diagnostic checks on environment and active database connection."


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute doctor command."""
    all_passed = True
    err_stream = sys.stderr

    # 1. Check Python version
    py_ver = f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    if sys.version_info >= (3, 10):
        sys.stdout.write(f"[PASS] Python version: {py_ver}\n")
    else:
        all_passed = False
        sys.stdout.write(f"[FAIL] Python version: {py_ver} (requires Python 3.10+)\n")
        err_stream.write("       Hint: Upgrade your Python installation to Python 3.10 or newer.\n")

    # 2. Check Database Driver
    try:
        import mysql.connector

        driver_ver = getattr(mysql.connector, "__version__", "installed")
        sys.stdout.write(f"[PASS] MySQL Driver: mysql-connector-python {driver_ver}\n")
    except ImportError:
        all_passed = False
        sys.stdout.write("[FAIL] MySQL Driver: mysql-connector-python is not installed\n")
        err_stream.write("       Hint: Install runtime dependencies with 'pip install .'.\n")

    # 3. Check Active Profile
    active_name = pm.get_active_profile()
    if not active_name:
        all_passed = False
        sys.stdout.write("[FAIL] Active Profile: No active profile configured\n")
        err_stream.write(
            "       Hint: Add a profile with 'oxtan add-db <name>' and activate with 'oxtan use <name>'.\n"
        )
        return 1

    try:
        name, prof = pm.get_profile(active_name)
        host = prof.get("host")
        port = prof.get("port")
        user = prof.get("user")
        db = prof.get("database")
        sys.stdout.write(f"[PASS] Active Profile: '{name}' ({user}@{host}:{port}/{db})\n")
    except Exception as e:
        all_passed = False
        sys.stdout.write(f"[FAIL] Active Profile: Corrupt configuration ({e})\n")
        err_stream.write("       Hint: Inspect or re-create profile with 'oxtan add-db'.\n")
        return 1

    # 4. Check Connection & Latency
    try:
        success, server_ver, latency_ms = test_connection(prof)
        if success:
            sys.stdout.write(
                f"[PASS] MySQL Connection: Connected to MySQL {server_ver} ({latency_ms:.1f}ms round-trip)\n"
            )
        else:
            all_passed = False
            sys.stdout.write("[FAIL] MySQL Connection: Could not verify server version\n")
            err_stream.write("       Hint: Check database server health.\n")
    except Exception as e:
        all_passed = False
        sys.stdout.write(f"[FAIL] MySQL Connection: {e}\n")
        hint = getattr(e, "fix_hint", "Verify host, port, credentials, and network status.")
        err_stream.write(f"       Hint: {hint}\n")

    return 0 if all_passed else 1
