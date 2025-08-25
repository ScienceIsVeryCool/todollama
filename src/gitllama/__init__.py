"""
TODOllama - AI-powered Python Code Generation Tool

Creates containerized Python applications from TODO.md descriptions.
"""

# Single-source versioning - version comes from pyproject.toml
try:
    from importlib.metadata import version
    __version__ = version("todollama")
except ImportError:
    # Fallback for Python < 3.8
    try:
        from importlib_metadata import version
        __version__ = version("todollama")
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