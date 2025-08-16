"""
GitLlama - Simple Git Automation Tool

A Python package for automating basic git operations.
"""

__version__ = "0.1.0"

from .git_operations import GitAutomator, GitOperationError

__all__ = [
    "GitAutomator",
    "GitOperationError",
    "__version__"
]