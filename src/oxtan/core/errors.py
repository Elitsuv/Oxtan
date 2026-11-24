"""Error types and clean error formatting for Oxtan."""

from typing import Optional


class OxtanError(Exception):
    """Base exception for all Oxtan errors."""

    def __init__(self, message: str, fix_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.fix_hint = fix_hint or ""

    def format_error(self) -> str:
        """Format the error as a clean single line with fix hint."""
        if self.fix_hint:
            return f"Error: {self.message}\nHint: {self.fix_hint}"
        return f"Error: {self.message}"


class ConfigurationError(OxtanError):
    """Raised when configuration or profile is invalid or corrupt."""


class ProfileNotFoundError(ConfigurationError):
    """Raised when a requested profile does not exist."""


class SecurityError(OxtanError):
    """Raised when an identifier or query violates security rules."""


class DatabaseConnectionError(OxtanError):
    """Raised when connection to MySQL fails or is lost."""


class QueryExecutionError(OxtanError):
    """Raised when query execution fails in MySQL."""


class UsageError(OxtanError):
    """Raised for CLI argument or command usage errors."""
