"""
GitLlama - AI-powered Git Automation Tool

Simple git automation with AI decision-making: clone, branch, change, commit, push.
"""

__version__ = "0.7.2"

from .git_operations import GitAutomator, GitOperationError
from .ollama_client import OllamaClient
from .simplified_coordinator import SimplifiedCoordinator
from .todo_analyzer import TodoAnalyzer
from .todo_planner import TodoPlanner
from .todo_executor import TodoExecutor

__all__ = [
    "GitAutomator",
    "GitOperationError", 
    "OllamaClient",
    "SimplifiedCoordinator",
    "TodoAnalyzer",
    "TodoPlanner",
    "TodoExecutor",
]