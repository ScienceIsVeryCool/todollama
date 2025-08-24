"""
AI Query Interface for GitLlama
With integrated prompt-response pair tracking
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from .client import OllamaClient
from ..utils.metrics import context_manager
from ..utils.context_tracker import context_tracker
from .parser import ResponseParser
from .context_compressor import ContextCompressor
from .congress import Congress, CongressDecision

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
    congress_decision: Optional[CongressDecision] = None


@dataclass 
class OpenResult:
    """Result from an open response query"""
    content: str
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0
    congress_decision: Optional[CongressDecision] = None


class AIQuery:
    """Simple interface for AI queries with full context tracking"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        self.client = client
        self.model = model
        self.parser = ResponseParser()
        self.compressor = ContextCompressor(client, model)
        self._compression_enabled = True
        self.congress = Congress(client, model)
    
    def choice(
        self, 
        question: str,
        options: List[str],
        context: str = "",
        context_name: str = "choice",
        auto_compress: bool = True
    ) -> ChoiceResult:
        """
        Ask AI to pick from options with full context tracking.
        """
        # Build a dictionary of all variables being used
        variables_used = {}
        
        # Track the input variables
        if question:
            variables_used["question"] = question
            context_tracker.store_variable(
                f"{context_name}_question",
                question,
                "Multiple choice question"
            )
        
        if options:
            options_str = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            variables_used["options"] = options_str
            context_tracker.store_variable(
                f"{context_name}_options",
                options,
                "Available options for selection"
            )
        
        if context:
            variables_used["context"] = context
            context_tracker.store_variable(
                f"{context_name}_context",
                context,
                "Context provided for decision"
            )
        
        # Handle context compression if needed
        compressed = False
        compression_rounds = 0
        original_context = context
        
        if auto_compress and self._compression_enabled and context:
            context_to_use, was_compressed = self.compressor.auto_compress_for_query(
                context, 
                self._build_choice_prompt(question, options, "")
            )
            
            if was_compressed:
                logger.info(f"🗜️ Context auto-compressed for choice question")
                context = context_to_use
                compressed = True
                result = self.compressor.compress_context(original_context, question, max_rounds=1)
                compression_rounds = result.compression_rounds
                
                # Update the context in variables_used
                variables_used["context"] = context
                variables_used["original_context"] = original_context
                
                # Track the compressed context
                context_tracker.store_variable(
                    f"{context_name}_compressed_context",
                    context,
                    f"Compressed from {len(original_context)} to {len(context)} chars"
                )
        
        # Build prompt
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
        
        # Get Congress evaluation
        congress_decision = self.congress.evaluate_response(
            original_prompt=prompt,
            ai_response=response,
            context=context,
            decision_type="choice"
        )
        
        # Add Congress data to variables_used so it's included in the pair
        congress_data = {
            "approved": congress_decision.approved,
            "votes": f"{congress_decision.vote_count[0]}-{congress_decision.vote_count[1]}",
            "unanimous": congress_decision.unanimity,
            "representatives": [v.representative.name for v in congress_decision.votes],
            "vote_details": [{
                "name": v.representative.name,
                "title": v.representative.title,
                "vote": v.vote,
                "confidence": v.confidence,
                "reasoning": v.reasoning
            } for v in congress_decision.votes]
        }
        variables_used[f"{context_name}_congress"] = congress_data
        
        
        # Store the prompt-response pair with variables (now including Congress data)
        context_tracker.store_prompt_and_response(
            prompt=prompt,
            response=response,
            variable_map=variables_used
        )
        
        # Also store Congress decision as separate variable for backward compatibility
        context_tracker.store_variable(
            f"{context_name}_congress",
            congress_data,
            "Congressional evaluation of choice"
        )
        
        result = ChoiceResult(
            index=index,
            value=options[index] if index >= 0 else options[0],
            confidence=confidence,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
        )
        
        # Track the parsed result
        context_tracker.store_variable(
            f"{context_name}_result",
            {"selected": result.value, "confidence": confidence, "index": index},
            "Parsed choice result"
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
        Ask AI for open response with full context tracking.
        """
        # Build a dictionary of all variables being used
        variables_used = {}
        
        # Track the input variables
        if prompt:
            variables_used["prompt"] = prompt
            context_tracker.store_variable(
                f"{context_name}_prompt",
                prompt,
                "Open-ended prompt"
            )
        
        if context:
            variables_used["context"] = context
            context_tracker.store_variable(
                f"{context_name}_context",
                context,
                "Context for open response"
            )
        
        # Handle context compression if needed
        compressed = False
        compression_rounds = 0
        original_context = context
        
        if auto_compress and self._compression_enabled and context:
            context_to_use, was_compressed = self.compressor.auto_compress_for_query(
                context, 
                prompt
            )
            
            if was_compressed:
                logger.info(f"🗜️ Context auto-compressed for open question")
                context = context_to_use
                compressed = True
                result = self.compressor.compress_context(original_context, prompt, max_rounds=1)
                compression_rounds = result.compression_rounds
                
                # Update the context in variables_used
                variables_used["context"] = context
                variables_used["original_context"] = original_context
                
                # Track the compressed context
                context_tracker.store_variable(
                    f"{context_name}_compressed_context",
                    context,
                    f"Compressed from {len(original_context)} to {len(context)} chars"
                )
        
        # Build full prompt
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
        
        # Get Congress evaluation
        congress_decision = self.congress.evaluate_response(
            original_prompt=full_prompt,
            ai_response=response,
            context=context,
            decision_type="open"
        )
        
        # Add Congress data to variables_used so it's included in the pair
        congress_data = {
            "approved": congress_decision.approved,
            "votes": f"{congress_decision.vote_count[0]}-{congress_decision.vote_count[1]}",
            "unanimous": congress_decision.unanimity,
            "representatives": [v.representative.name for v in congress_decision.votes],
            "vote_details": [{
                "name": v.representative.name,
                "title": v.representative.title,
                "vote": v.vote,
                "confidence": v.confidence,
                "reasoning": v.reasoning
            } for v in congress_decision.votes]
        }
        variables_used[f"{context_name}_congress"] = congress_data
        
        
        # Store the prompt-response pair with variables (now including Congress data)
        context_tracker.store_prompt_and_response(
            prompt=full_prompt,
            response=response,
            variable_map=variables_used
        )
        
        # Track the cleaned content
        context_tracker.store_variable(
            f"{context_name}_cleaned_response",
            content,
            "Cleaned response content"
        )
        
        # Also store Congress decision as separate variable for backward compatibility
        context_tracker.store_variable(
            f"{context_name}_congress",
            congress_data,
            "Congressional evaluation of open response"
        )
        
        result = OpenResult(
            content=content,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
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
            parts.append(f"- {option}")
        
        parts.append("\nRespond with ONLY one word to be parsed to be read as an answer.")
        
        return "\n".join(parts)
    
    def set_compression_enabled(self, enabled: bool):
        """Enable or disable automatic context compression."""
        self._compression_enabled = enabled
        logger.info(f"Context compression {'enabled' if enabled else 'disabled'}")
    
    
    def get_congress_summary(self) -> Dict:
        """Get summary of all Congressional votes."""
        return self.congress.get_voting_summary()