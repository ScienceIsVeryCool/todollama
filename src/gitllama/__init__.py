"""
GitLlama - AI-powered Git Automation Tool

Simple git automation with AI decision-making: clone, branch, change, commit, push.
"""

# Single-source versioning - version comes from pyproject.toml
try:
    from importlib.metadata import version
    __version__ = version("gitllama")
except ImportError:
    # Fallback for Python < 3.8
    try:
        from importlib_metadata import version
        __version__ = version("gitllama")
    except ImportError:
        # Last resort fallback for development or when package not installed
        __version__ = "0.8.0"
except Exception:
    # Package not installed or in development mode
    __version__ = "0.8.0"

from .core import GitAutomator, GitOperationError, SimplifiedCoordinator
from .ai import OllamaClient
from .todo import TodoAnalyzer, TodoPlanner, TodoExecutor

__all__ = [
    "GitAutomator",
    "GitOperationError", 
    "OllamaClient",
    "SimplifiedCoordinator",
    "TodoAnalyzer",
    "TodoPlanner",
    "TodoExecutor",
]