"""
GitLlama - AI-powered Git Automation Tool

Simple git automation with AI decision-making: clone, branch, change, commit, push.
"""

__version__ = "0.7.2"

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