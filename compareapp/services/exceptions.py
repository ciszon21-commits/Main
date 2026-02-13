class CompareAppError(Exception):
    """Base error for compare service."""


class ParseError(CompareAppError):
    """Raised when source files cannot be parsed as expected."""


class DependencyError(CompareAppError):
    """Raised when optional dependencies are missing."""
