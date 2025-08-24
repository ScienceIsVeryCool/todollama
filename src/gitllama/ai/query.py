"""
AI Query Interface for GitLlama
Simple, clean interface for multiple choice and open response queries
Now with automatic context compression for large contexts
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from .client import OllamaClient
from ..utils.metrics import context_manager
from .parser import ResponseParser
from .context_compressor import ContextCompressor

logger = logging.getLogger(__name__)


@dataclass
class ChoiceResult:
    """Result from a multiple choice query"""
    index: int
    value: str
    confidence: float
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0


@dataclass 
class OpenResult:
    """Result from an open response query"""
    content: str
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0


class AIQuery:
    """Simple interface for AI queries - either multiple choice or open response"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        self.client = client
        self.model = model
        self.parser = ResponseParser()
        self.compressor = ContextCompressor(client, model)
        self._compression_enabled = True  # Can be disabled for testing
    
    def choice(
        self, 
        question: str,
        options: List[str],
        context: str = "",
        context_name: str = "choice",
        auto_compress: bool = True
    ) -> ChoiceResult:
        """
        Ask AI to pick from options.
        
        Args:
            question: What to ask
            options: List of options to choose from
            context: Optional context
            context_name: For tracking
            auto_compress: Whether to automatically compress large contexts
            
        Returns:
            ChoiceResult with the selection
        """
        # Handle context compression if needed
        compressed = False
        compression_rounds = 0
        original_context = context
        
        if auto_compress and self._compression_enabled and context:
            # Check and compress if needed
            context_to_use, was_compressed = self.compressor.auto_compress_for_query(
                context, 
                self._build_choice_prompt(question, options, "")  # Pass prompt structure
            )
            
            if was_compressed:
                logger.info(f"🗜️ Context auto-compressed for choice question")
                context = context_to_use
                compressed = True
                # Get compression details
                result = self.compressor.compress_context(original_context, question, max_rounds=1)
                compression_rounds = result.compression_rounds
        
        # Build prompt with potentially compressed context
        prompt = self._build_choice_prompt(question, options, context)
        
        # Make the query
        messages = [{"role": "user", "content": prompt}]
        
        logger.info(f"🎯 Choice: {question[:50]}... ({len(options)} options)")
        if compressed:
            logger.info(f"   (Using compressed context: {compression_rounds} rounds)")
        context_manager.record_ai_call("choice", question[:50])
        
        # Get response
        response = ""
        for chunk in self.client.chat_stream(self.model, messages, context_name=context_name):
            response += chunk
        
        # Parse the choice
        index, confidence = self.parser.parse_choice(response, options)
        
        result = ChoiceResult(
            index=index,
            value=options[index] if index >= 0 else options[0],
            confidence=confidence,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds
        )
        
        logger.info(f"✅ Selected: {result.value} (confidence: {confidence:.2f})")
        return result
    
    def open(
        self,
        prompt: str,
        context: str = "",
        context_name: str = "open",
        auto_compress: bool = True
    ) -> OpenResult:
        """
        Ask AI for open response.
        
        Args:
            prompt: What to ask
            context: Optional context
            context_name: For tracking
            auto_compress: Whether to automatically compress large contexts
            
        Returns:
            OpenResult with the response
        """
        # Handle context compression if needed
        compressed = False
        compression_rounds = 0
        original_context = context
        
        if auto_compress and self._compression_enabled and context:
            # Check and compress if needed
            context_to_use, was_compressed = self.compressor.auto_compress_for_query(
                context, 
                prompt
            )
            
            if was_compressed:
                logger.info(f"🗜️ Context auto-compressed for open question")
                context = context_to_use
                compressed = True
                # Get compression details
                result = self.compressor.compress_context(original_context, prompt, max_rounds=1)
                compression_rounds = result.compression_rounds
        
        # Build prompt with potentially compressed context
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        messages = [{"role": "user", "content": full_prompt}]
        
        logger.info(f"📝 Open: {prompt[:50]}...")
        if compressed:
            logger.info(f"   (Using compressed context: {compression_rounds} rounds)")
        context_manager.record_ai_call("open", prompt[:50])
        
        # Get response
        response = ""
        for chunk in self.client.chat_stream(self.model, messages, context_name=context_name):
            response += chunk
        
        # Clean the response
        content = self.parser.clean_text(response)
        
        result = OpenResult(
            content=content,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds
        )
        
        logger.info(f"✅ Response: {len(content)} chars")
        return result
    
    def _build_choice_prompt(self, question: str, options: List[str], context: str) -> str:
        """Build a simple choice prompt"""
        parts = []
        
        if context:
            parts.append(f"Context: {context}\n")
        
        parts.append(question)
        parts.append("\nOptions:")
        
        for i, option in enumerate(options):
            parts.append(f"{i+1}. {option}")
        
        parts.append("\nRespond with ONLY the number (1, 2, 3, etc) of your choice:")
        
        return "\n".join(parts)
    
    def set_compression_enabled(self, enabled: bool):
        """
        Enable or disable automatic context compression.
        
        Args:
            enabled: Whether to enable compression
        """
        self._compression_enabled = enabled
        logger.info(f"Context compression {'enabled' if enabled else 'disabled'}")