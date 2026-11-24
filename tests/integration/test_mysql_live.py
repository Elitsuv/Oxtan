import os
import subprocess
import sys
from urllib.parse import urlparse

import pytest

from oxtan.core.connection import get_connection
from oxtan.core.profiles import ProfileManager


@pytest.mark.integration
def test_mysql_live_roundtrip(tmp_path: pytest.TempPathFactory) -> None:
    dsn = os.environ.get("OXTAN_TEST_DSN")
    if not dsn:
        pytest.skip("OXTAN_TEST_DSN environment variable not set; skipping live MySQL integration tests")

    url = urlparse(dsn)
    host = url.hostname or "127.0.0.1"
    port = url.port or 3306
    user = url.username or "root"
    password = url.password or ""
    database = url.path.lstrip("/") or "test"

    home_dir = str(tmp_path)
    env = os.environ.copy()
    env["HOME"] = home_dir
    env["USERPROFILE"] = home_dir
    env["OXTAN_PASSWORD"] = password
    env["NO_COLOR"] = "1"

    def run_oxtan(*args: str, input_str: str = "") -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "oxtan"] + list(args)
        return subprocess.run(
            cmd,
            input=input_str,
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )

    # 1. Add DB profile
    res = run_oxtan(
        "add-db", "--name", "livetest", "--host", host, "--port", str(port), "--user", user, "--database", database
    )
    assert res.returncode == 0, f"add-db failed: {res.stderr}"

    # 2. Check current and use
    res = run_oxtan("current")
    assert res.returncode == 0
    assert "livetest" in res.stdout

    res = run_oxtan("dbs")
    assert res.returncode == 0
    assert "livetest" in res.stdout

    res = run_oxtan("use", "livetest")
    assert res.returncode == 0

    # 3. Doctor check
    res = run_oxtan("doctor")
    assert res.returncode == 0
    assert "PASS" in res.stdout

    # Setup a live table for testing
    profile_mgr = ProfileManager(config_path=os.path.join(home_dir, ".oxtan", "profiles.json"))
    _, profile = profile_mgr.get_profile()
    assert profile is not None

    with get_connection(profile) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS _oxtan_live_test ("
                "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), val INT)"
            )
            cur.execute("TRUNCATE TABLE _oxtan_live_test")
            cur.execute("INSERT INTO _oxtan_live_test (name, val) VALUES ('alice', 10), ('bob', 20), ('charlie', 30)")
        conn.commit()

    try:
        # 4. Tables command
        res = run_oxtan("tables")
        assert res.returncode == 0
        assert "_oxtan_live_test" in res.stdout

        # 5. Schema command
        res = run_oxtan("schema", "_oxtan_live_test")
        assert res.returncode == 0
        assert "name" in res.stdout
        assert "val" in res.stdout

        # 6. Count command
        res = run_oxtan("count", "_oxtan_live_test")
        assert res.returncode == 0
        assert "3" in res.stdout

        # 7. Peek command
        res = run_oxtan("peek", "_oxtan_live_test", "--limit", "2")
        assert res.returncode == 0
        assert "alice" in res.stdout
        assert "bob" in res.stdout

        # 8. Query read-only
        res = run_oxtan("query", "SELECT name, val FROM _oxtan_live_test WHERE val > 15 ORDER BY val")
        assert res.returncode == 0
        assert "bob" in res.stdout
        assert "charlie" in res.stdout
        assert "alice" not in res.stdout

        # 9. Query write with --write --yes
        res = run_oxtan("query", "INSERT INTO _oxtan_live_test (name, val) VALUES ('dave', 40)", "--write", "--yes")
        assert res.returncode == 0
        assert "1 row(s) affected" in res.stdout

        res = run_oxtan("count", "_oxtan_live_test")
        assert res.returncode == 0
        assert "4" in res.stdout

        # 10. Query modifying blocked without --write
        res = run_oxtan("query", "UPDATE _oxtan_live_test SET val = 50 WHERE name = 'dave'")
        assert res.returncode == 1
        assert "read-only" in res.stderr.lower() or "read only" in res.stderr.lower()
    finally:
        with get_connection(profile) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS _oxtan_live_test")
            conn.commit()
