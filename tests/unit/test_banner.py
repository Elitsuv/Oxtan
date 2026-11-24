"""Unit tests for banner and doodle rendering."""

import io

from oxtan.cli.banner import (
    is_color_enabled,
    print_banner_and_cheatsheet,
    should_suppress_banner,
)


class MockTTYStream(io.StringIO):
    """Mock stream simulating an interactive terminal."""

    def isatty(self) -> bool:
        return True


def test_should_suppress_banner():
    # Quiet suppresses
    assert should_suppress_banner(quiet=True) is True

    # Mock non-tty stream suppresses (piped)
    non_tty = io.StringIO()
    assert should_suppress_banner(quiet=False, stream=non_tty) is True

    # Interactive TTY does not suppress
    tty = MockTTYStream()
    assert should_suppress_banner(quiet=False, stream=tty) is False


def test_is_color_enabled(monkeypatch):
    assert is_color_enabled(no_color_flag=True) is False

    monkeypatch.setenv("NO_COLOR", "1")
    assert is_color_enabled() is False

    monkeypatch.delenv("NO_COLOR", raising=False)
    non_tty = io.StringIO()
    assert is_color_enabled(stream=non_tty) is False


def test_print_banner_and_cheatsheet_suppressed_when_piped():
    # Standard StringIO has isatty() == False (piped)
    out = io.StringIO()
    print_banner_and_cheatsheet(quiet=False, stream=out)
    assert out.getvalue() == ""


def test_print_banner_and_cheatsheet_suppressed_when_quiet():
    tty = MockTTYStream()
    print_banner_and_cheatsheet(quiet=True, stream=tty)
    assert tty.getvalue() == ""


def test_print_banner_and_cheatsheet_shown_on_tty():
    tty = MockTTYStream()
    print_banner_and_cheatsheet(quiet=False, no_color=True, stream=tty)
    assert "Oxtan v0.1.0" in tty.getvalue()
    assert "Commands:" in tty.getvalue()
    assert "\033[" not in tty.getvalue()
