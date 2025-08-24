"""
Context Compressor for GitLlama
Automatically handles large context windows by intelligently compressing them
"""

import logging
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result from context compression"""
    compressed_context: str
    compression_rounds: int
    original_size: int
    final_size: int
    success: bool


class ContextCompressor:
    """Intelligently compresses large contexts to fit within model limits"""
    
    def __init__(self, client, model: str):
        """
        Initialize the context compressor.
        
        Args:
            client: OllamaClient instance
            model: Model name for context size limits
        """
        self.client = client
        self.model = model
        self.max_context_size = self.client.get_model_context_size(model)
        # Reserve 30% for prompt/response overhead
        self.usable_context_size = int(self.max_context_size * 0.7)
        
    def needs_compression(self, context: str, question: str) -> bool:
        """
        Check if context needs compression.
        
        Args:
            context: The context to check
            question: The question being asked (for size calculation)
            
        Returns:
            True if compression is needed
        """
        total_tokens = self.client.count_tokens(context + question)
        return total_tokens > self.usable_context_size
    
    def compress_context(self, context: str, question: str, max_rounds: int = 3) -> CompressionResult:
        """
        Compress context to fit within model limits.
        
        Args:
            context: Original context to compress
            question: The question that needs to be answered
            max_rounds: Maximum compression rounds to attempt
            
        Returns:
            CompressionResult with compressed context and metadata
        """
        original_size = self.client.count_tokens(context)
        current_context = context
        compression_rounds = 0
        
        logger.info(f"🗜️ Starting context compression (original: {original_size} tokens)")
        
        while compression_rounds < max_rounds:
            # Check if compression is still needed
            if not self.needs_compression(current_context, question):
                logger.info(f"✅ Context fits after {compression_rounds} rounds")
                return CompressionResult(
                    compressed_context=current_context,
                    compression_rounds=compression_rounds,
                    original_size=original_size,
                    final_size=self.client.count_tokens(current_context),
                    success=True
                )
            
            compression_rounds += 1
            logger.info(f"🔄 Compression round {compression_rounds}/{max_rounds}")
            
            # Perform one round of compression
            current_context = self._compress_once(current_context, question)
            
            # Check if compression actually reduced size
            new_size = self.client.count_tokens(current_context)
            if new_size >= self.client.count_tokens(context) * 0.95:  # Less than 5% reduction
                logger.warning("Compression not effective, stopping")
                break
        
        final_size = self.client.count_tokens(current_context)
        success = not self.needs_compression(current_context, question)
        
        if success:
            logger.info(f"✅ Compression successful: {original_size} → {final_size} tokens ({compression_rounds} rounds)")
        else:
            logger.warning(f"⚠️ Compression incomplete: {original_size} → {final_size} tokens (still too large)")
        
        # Record compression metrics
        from ..utils.metrics import context_manager
        context_manager.record_compression(original_size, final_size, compression_rounds, success)
        
        return CompressionResult(
            compressed_context=current_context,
            compression_rounds=compression_rounds,
            original_size=original_size,
            final_size=final_size,
            success=success
        )
    
    def _compress_once(self, context: str, question: str) -> str:
        """
        Perform one round of compression by splitting and summarizing.
        
        Args:
            context: Context to compress
            question: The guiding question
            
        Returns:
            Compressed context
        """
        # Split context in half
        context_lines = context.split('\n')
        mid_point = len(context_lines) // 2
        
        first_half = '\n'.join(context_lines[:mid_point])
        second_half = '\n'.join(context_lines[mid_point:])
        
        # Compress each half
        logger.debug("Compressing first half...")
        first_compressed = self._compress_chunk(first_half, question, "first")
        
        logger.debug("Compressing second half...")
        second_compressed = self._compress_chunk(second_half, question, "second")
        
        # Combine compressed halves
        combined = f"""=== Compressed Context (Part 1) ===
{first_compressed}

=== Compressed Context (Part 2) ===
{second_compressed}"""
        
        return combined
    
    def _compress_chunk(self, chunk: str, question: str, chunk_label: str) -> str:
        """
        Compress a single chunk of context.
        
        Args:
            chunk: The chunk to compress
            question: The guiding question
            chunk_label: Label for this chunk (for logging)
            
        Returns:
            Compressed chunk
        """
        # Use a focused prompt to extract only relevant information
        compression_prompt = f"""You are a context compression assistant. Your task is to extract and summarize ONLY the information from the following context that is relevant to answering this question:

QUESTION: {question}

CONTEXT TO COMPRESS:
{chunk}

INSTRUCTIONS:
1. Extract only information directly relevant to the question
2. Preserve specific details, names, numbers, and facts
3. Remove redundant or irrelevant information
4. Keep your response concise but complete
5. Maintain factual accuracy - do not invent information

COMPRESSED CONTEXT:"""
        
        try:
            # Use chat_stream to get compression
            messages = [{"role": "user", "content": compression_prompt}]
            
            response = ""
            for chunk_response in self.client.chat_stream(
                self.model, 
                messages, 
                context_name=f"compress_{chunk_label}"
            ):
                response += chunk_response
            
            # Trim response if needed
            max_chunk_tokens = self.usable_context_size // 3  # Each compressed chunk should be at most 1/3
            if self.client.count_tokens(response) > max_chunk_tokens:
                response = self.client.trim_to_context_window(response, max_chunk_tokens)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Compression failed for {chunk_label}: {e}")
            # Return truncated original on failure
            return chunk[:1000] + "...[compression failed, truncated]"
    
    def auto_compress_for_query(self, context: str, question: str) -> Tuple[str, bool]:
        """
        Automatically compress context if needed for a query.
        
        Args:
            context: Original context
            question: Question to be answered
            
        Returns:
            Tuple of (context_to_use, was_compressed)
        """
        if not context:
            return context, False
        
        if not self.needs_compression(context, question):
            logger.debug("Context fits, no compression needed")
            return context, False
        
        logger.info(f"🗜️ Context too large ({self.client.count_tokens(context)} tokens), auto-compressing...")
        
        result = self.compress_context(context, question)
        
        if result.success:
            compression_ratio = (1 - result.final_size / result.original_size) * 100
            logger.info(f"📊 Compression ratio: {compression_ratio:.1f}% reduction")
            return result.compressed_context, True
        else:
            # Even if not fully successful, use the compressed version if it's smaller
            if result.final_size < result.original_size:
                logger.warning("Using partially compressed context")
                return result.compressed_context, True
            else:
                logger.error("Compression failed, using truncated context")
                # Fallback: truncate to fit
                max_chars = self.usable_context_size * 4  # Rough estimate
                return context[:max_chars] + "...[truncated]", True