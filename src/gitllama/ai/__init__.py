"""
AI interface components
"""

from .client import OllamaClient
from .query import AIQuery
from .parser import ResponseParser
from .context_compressor import ContextCompressor
from .congress import Congress, CongressDecision, CongressVote, Representative

__all__ = [
    "OllamaClient",
    "AIQuery",
    "ResponseParser",
    "ContextCompressor",
    "Congress",
    "CongressDecision",
    "CongressVote",
    "Representative"
]