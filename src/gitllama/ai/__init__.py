"""
AI interface components
"""

from .client import OllamaClient
from .query import AIQuery, MultipleChoiceResult, SingleWordResult, OpenResult, FileWriteResult
from .parser import ResponseParser
from .context_compressor import ContextCompressor
from .congress import Congress, CongressDecision, CongressVote, Representative

__all__ = [
    "OllamaClient",
    "AIQuery",
    "MultipleChoiceResult",
    "SingleWordResult", 
    "OpenResult",
    "FileWriteResult",
    "ResponseParser",
    "ContextCompressor",
    "Congress",
    "CongressDecision",
    "CongressVote",
    "Representative"
]