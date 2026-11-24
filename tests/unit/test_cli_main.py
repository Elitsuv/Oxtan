"""Unit tests for oxtan.cli.main and registry."""

from unittest.mock import MagicMock, patch

from oxtan.cli.main import build_registry, main
from oxtan.core.errors import OxtanError, UsageError


def test_build_registry():
    registry = build_registry()
    assert "add-db" in registry.commands
    assert "use" in registry.commands
    assert "tables" in registry.commands
    assert "t" in registry.aliases


def test_main_no_args(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Oxtan v0.1.0" in captured.out


def test_main_keyboard_interrupt(monkeypatch):
    registry = build_registry()
    mock_run = MagicMock(side_effect=KeyboardInterrupt)
    registry.commands["dbs"] = mock_run

    with patch("oxtan.cli.main.build_registry", return_value=registry):
        ret = main(["dbs"])
        assert ret == 130


def test_main_usage_error(monkeypatch):
    registry = build_registry()
    mock_run = MagicMock(side_effect=UsageError("Bad flag", fix_hint="Use good flag"))
    registry.commands["dbs"] = mock_run

    with patch("oxtan.cli.main.build_registry", return_value=registry):
        ret = main(["dbs"])
        assert ret == 2


def test_main_oxtan_error(monkeypatch):
    registry = build_registry()
    mock_run = MagicMock(side_effect=OxtanError("Operation failed", fix_hint="Check server"))
    registry.commands["dbs"] = mock_run

    with patch("oxtan.cli.main.build_registry", return_value=registry):
        ret = main(["dbs"])
        assert ret == 1


def test_main_unexpected_exception(monkeypatch):
    registry = build_registry()
    mock_run = MagicMock(side_effect=RuntimeError("Surprise crash"))
    registry.commands["dbs"] = mock_run

    with patch("oxtan.cli.main.build_registry", return_value=registry):
        ret = main(["dbs"])
        assert ret == 1


def test_main_debug_prints_traceback(monkeypatch, capsys):
    registry = build_registry()
    mock_run = MagicMock(side_effect=OxtanError("Detailed failure"))
    registry.commands["dbs"] = mock_run

    with patch("oxtan.cli.main.build_registry", return_value=registry):
        ret = main(["dbs", "--debug"])
        assert ret == 1
        captured = capsys.readouterr()
        assert "Traceback (most recent call last):" in captured.err
