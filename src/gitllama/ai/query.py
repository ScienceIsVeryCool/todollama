"""
Enhanced AI Query Interface for GitLlama
4 Query Types with Templated Prompts and Congressional Oversight
"""

import logging
import re
from typing import List, Optional, Dict, Union
from dataclasses import dataclass
from .client import OllamaClient
from ..utils.metrics import context_manager
from ..utils.context_tracker import context_tracker
from .parser import ResponseParser
from .context_compressor import ContextCompressor
from .congress import Congress, CongressDecision

logger = logging.getLogger(__name__)


@dataclass
class MultipleChoiceResult:
    """Result from a multiple choice query with lettered answers"""
    letter: str  # A, B, C, etc.
    index: int   # 0, 1, 2, etc.
    value: str   # The actual option text
    confidence: float
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0
    congress_decision: Optional[CongressDecision] = None


@dataclass
class SingleWordResult:
    """Result from a single word query"""
    word: str
    confidence: float
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0
    congress_decision: Optional[CongressDecision] = None


@dataclass 
class OpenResult:
    """Result from an open essay-style response query"""
    content: str
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0
    congress_decision: Optional[CongressDecision] = None


@dataclass
class FileWriteResult:
    """Result from a file write query"""
    content: str
    raw: str
    context_compressed: bool = False
    compression_rounds: int = 0
    congress_decision: Optional[CongressDecision] = None


class AIQuery:
    """Enhanced AI query interface with 4 distinct query types"""
    
    # Query Templates
    TEMPLATES = {
        "multiple_choice": """Based on the context provided, answer the following question by selecting the best option.

Context: {context}

Question: {question}

Options:
{options}

Instructions:
- Choose the BEST answer from the options above
- Respond with ONLY the letter (A, B, C, etc.) of your chosen answer
- Do not include explanations or additional text
- Be decisive and select exactly one option

Your answer:""",

        "single_word": """Based on the context provided, answer the following question with a single word.

Context: {context}

Question: {question}

Instructions:
- Respond with ONLY one word
- No explanations, punctuation, or additional text
- The word should directly answer the question
- Be precise and specific

Your single word answer:""",

        "open": """Write a comprehensive response to the following prompt.

Context: {context}

Prompt: {prompt}

Instructions:
- Provide a detailed, well-structured response
- Use clear reasoning and examples where appropriate
- Write in a professional, informative tone
- Structure your response logically with proper flow

Your response:""",

        "file_write": """Generate the complete content for a file based on the requirements below.

Context: {context}

File Requirements: {requirements}

Instructions:
- Write ONLY the file content that should be saved
- Do not include explanations, comments about the task, or markdown formatting
- The output will be written directly to the file
- Ensure the content is complete and ready to use
- Follow appropriate syntax and conventions for the file type

File content:"""
    }
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        self.client = client
        self.model = model
        self.parser = ResponseParser()
        self.compressor = ContextCompressor(client, model)
        self._compression_enabled = True
        self.congress = Congress(client, model)
    
    def multiple_choice(
        self, 
        question: str,
        options: List[str],
        context: str = "",
        context_name: str = "multiple_choice",
        auto_compress: bool = True
    ) -> MultipleChoiceResult:
        """
        Ask AI to select from lettered options (A, B, C, etc.)
        """
        # Build variables dictionary
        variables_used = {}
        
        # Track input variables
        if question:
            variables_used["question"] = question
            context_tracker.store_variable(
                f"{context_name}_question", question, "Multiple choice question"
            )
        
        if options:
            # Create lettered options (A, B, C, etc.)
            lettered_options = []
            for i, option in enumerate(options):
                letter = chr(ord('A') + i)
                lettered_options.append(f"{letter}. {option}")
            
            options_str = "\n".join(lettered_options)
            variables_used["options"] = options_str
            context_tracker.store_variable(
                f"{context_name}_options", options, "Available lettered options"
            )
        
        # Handle context and compression
        compressed, compression_rounds, original_context = self._handle_context_compression(
            context, self.TEMPLATES["multiple_choice"], auto_compress, context_name, variables_used
        )
        
        # Build prompt from template
        prompt = self.TEMPLATES["multiple_choice"].format(
            context=context if context else "No additional context provided",
            question=question,
            options=options_str
        )
        
        # Make query and get congress decision
        response, congress_decision = self._execute_query(
            prompt, context_name, "multiple_choice"
        )
        
        # Parse the multiple choice response
        letter, index, confidence = self._parse_multiple_choice_response(response, options)
        
        # Store congress data and prompt-response pair
        congress_data = self._build_congress_data(congress_decision)
        variables_used[f"{context_name}_congress"] = congress_data
        
        context_tracker.store_prompt_and_response(
            prompt=prompt, response=response, variable_map=variables_used,
            query_type="multiple_choice"
        )
        
        # Store result
        result = MultipleChoiceResult(
            letter=letter,
            index=index,
            value=options[index] if 0 <= index < len(options) else options[0],
            confidence=confidence,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
        )
        
        context_tracker.store_variable(
            f"{context_name}_result",
            {"selected_letter": letter, "selected_option": result.value, "confidence": confidence},
            "Multiple choice result"
        )
        
        logger.info(f"✅ Selected: {letter}. {result.value} (confidence: {confidence:.2f})")
        return result
    
    def single_word(
        self,
        question: str,
        context: str = "",
        context_name: str = "single_word",
        auto_compress: bool = True
    ) -> SingleWordResult:
        """
        Ask AI for a single word response
        """
        # Build variables dictionary
        variables_used = {}
        
        if question:
            variables_used["question"] = question
            context_tracker.store_variable(
                f"{context_name}_question", question, "Single word question"
            )
        
        # Handle context and compression
        compressed, compression_rounds, original_context = self._handle_context_compression(
            context, self.TEMPLATES["single_word"], auto_compress, context_name, variables_used
        )
        
        # Build prompt from template
        prompt = self.TEMPLATES["single_word"].format(
            context=context if context else "No additional context provided",
            question=question
        )
        
        # Make query and get congress decision
        response, congress_decision = self._execute_query(
            prompt, context_name, "single_word"
        )
        
        # Parse single word response
        word, confidence = self._parse_single_word_response(response)
        
        # Store congress data and prompt-response pair
        congress_data = self._build_congress_data(congress_decision)
        variables_used[f"{context_name}_congress"] = congress_data
        
        context_tracker.store_prompt_and_response(
            prompt=prompt, response=response, variable_map=variables_used,
            query_type="single_word"
        )
        
        result = SingleWordResult(
            word=word,
            confidence=confidence,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
        )
        
        context_tracker.store_variable(
            f"{context_name}_result",
            {"word": word, "confidence": confidence},
            "Single word result"
        )
        
        logger.info(f"✅ Single word: {word} (confidence: {confidence:.2f})")
        return result
    
    def open(
        self,
        prompt: str,
        context: str = "",
        context_name: str = "open",
        auto_compress: bool = True
    ) -> OpenResult:
        """
        Ask AI for an open essay-style response
        """
        # Build variables dictionary
        variables_used = {}
        
        if prompt:
            variables_used["prompt"] = prompt
            context_tracker.store_variable(
                f"{context_name}_prompt", prompt, "Open essay prompt"
            )
        
        # Handle context and compression
        compressed, compression_rounds, original_context = self._handle_context_compression(
            context, self.TEMPLATES["open"], auto_compress, context_name, variables_used
        )
        
        # Build full prompt from template
        full_prompt = self.TEMPLATES["open"].format(
            context=context if context else "No additional context provided",
            prompt=prompt
        )
        
        # Make query and get congress decision
        response, congress_decision = self._execute_query(
            full_prompt, context_name, "open"
        )
        
        # Clean the response
        content = self.parser.clean_text(response)
        
        # Store congress data and prompt-response pair
        congress_data = self._build_congress_data(congress_decision)
        variables_used[f"{context_name}_congress"] = congress_data
        
        context_tracker.store_prompt_and_response(
            prompt=full_prompt, response=response, variable_map=variables_used,
            query_type="open"
        )
        
        result = OpenResult(
            content=content,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
        )
        
        context_tracker.store_variable(
            f"{context_name}_cleaned_response", content, "Cleaned open response"
        )
        
        logger.info(f"✅ Open response: {len(content)} chars")
        return result
    
    def file_write(
        self,
        requirements: str,
        context: str = "",
        context_name: str = "file_write",
        auto_compress: bool = True
    ) -> FileWriteResult:
        """
        Ask AI to generate file content
        """
        # Build variables dictionary
        variables_used = {}
        
        if requirements:
            variables_used["requirements"] = requirements
            context_tracker.store_variable(
                f"{context_name}_requirements", requirements, "File write requirements"
            )
        
        # Handle context and compression
        compressed, compression_rounds, original_context = self._handle_context_compression(
            context, self.TEMPLATES["file_write"], auto_compress, context_name, variables_used
        )
        
        # Build prompt from template
        prompt = self.TEMPLATES["file_write"].format(
            context=context if context else "No additional context provided",
            requirements=requirements
        )
        
        # Make query and get congress decision
        response, congress_decision = self._execute_query(
            prompt, context_name, "file_write"
        )
        
        # Clean the response for file content
        content = self._clean_file_content(response)
        
        # Store congress data and prompt-response pair
        congress_data = self._build_congress_data(congress_decision)
        variables_used[f"{context_name}_congress"] = congress_data
        
        context_tracker.store_prompt_and_response(
            prompt=prompt, response=response, variable_map=variables_used,
            query_type="file_write"
        )
        
        result = FileWriteResult(
            content=content,
            raw=response.strip(),
            context_compressed=compressed,
            compression_rounds=compression_rounds,
            congress_decision=congress_decision
        )
        
        context_tracker.store_variable(
            f"{context_name}_file_content", content, "Generated file content"
        )
        
        logger.info(f"✅ File content generated: {len(content)} chars")
        return result
    
    # Helper methods
    
    def _handle_context_compression(self, context, template, auto_compress, context_name, variables_used):
        """Handle context compression if needed"""
        compressed = False
        compression_rounds = 0
        original_context = context
        
        if auto_compress and self._compression_enabled and context:
            context_to_use, was_compressed = self.compressor.auto_compress_for_query(
                context, template
            )
            
            if was_compressed:
                logger.info(f"🗜️ Context auto-compressed for {context_name}")
                context = context_to_use
                compressed = True
                result = self.compressor.compress_context(original_context, template, max_rounds=1)
                compression_rounds = result.compression_rounds
                
                variables_used["context"] = context
                variables_used["original_context"] = original_context
                
                context_tracker.store_variable(
                    f"{context_name}_compressed_context",
                    context,
                    f"Compressed from {len(original_context)} to {len(context)} chars"
                )
        
        if context:
            variables_used["context"] = context
            context_tracker.store_variable(
                f"{context_name}_context", context, "Query context"
            )
        
        return compressed, compression_rounds, original_context
    
    def _execute_query(self, prompt, context_name, query_type):
        """Execute the query and get congress decision"""
        messages = [{"role": "user", "content": prompt}]
        
        logger.info(f"🎯 {query_type.title()}: {prompt[:50]}...")
        context_manager.record_ai_call(query_type, prompt[:50])
        
        # Get response
        response = ""
        for chunk in self.client.chat_stream(self.model, messages, context_name=context_name):
            response += chunk
        
        # Get congress evaluation
        congress_decision = self.congress.evaluate_response(
            original_prompt=prompt,
            ai_response=response,
            context="",
            decision_type=query_type
        )
        
        return response, congress_decision
    
    def _build_congress_data(self, congress_decision):
        """Build congress data dictionary for storage"""
        return {
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
    
    def _parse_multiple_choice_response(self, response, options):
        """Parse multiple choice response to extract letter and confidence"""
        # Look for single letter responses (A, B, C, etc.)
        letter_match = re.search(r'\b[A-Z]\b', response.upper().strip())
        
        if letter_match:
            letter = letter_match.group()
            index = ord(letter) - ord('A')
            if 0 <= index < len(options):
                confidence = 0.9  # High confidence for clear letter match
                return letter, index, confidence
        
        # Fallback: try to match option text
        response_clean = response.lower().strip()
        for i, option in enumerate(options):
            if option.lower() in response_clean:
                letter = chr(ord('A') + i)
                confidence = 0.7  # Medium confidence for text match
                return letter, i, confidence
        
        # Default to first option with low confidence
        logger.warning(f"Could not parse multiple choice response: {response}")
        return 'A', 0, 0.3
    
    def _parse_single_word_response(self, response):
        """Parse single word response"""
        # Clean and extract single word
        words = response.strip().split()
        if words:
            # Take the first word and clean it
            word = re.sub(r'[^\w]', '', words[0])
            if word:
                confidence = 0.9 if len(words) == 1 else 0.7
                return word, confidence
        
        # Default fallback
        logger.warning(f"Could not parse single word response: {response}")
        return "unknown", 0.3
    
    def _clean_file_content(self, response):
        """Clean response for file content"""
        # Remove common AI response patterns
        content = response.strip()
        
        # Remove markdown code block markers if present
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove first line (```language)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        return content.strip()
    
    # Legacy compatibility and utility methods
    
    def choice(self, question: str, options: List[str], context: str = "", context_name: str = "choice", auto_compress: bool = True):
        """Legacy method - redirects to multiple_choice"""
        logger.warning("Using legacy 'choice' method. Please use 'multiple_choice' instead.")
        return self.multiple_choice(question, options, context, context_name, auto_compress)
    
    def set_compression_enabled(self, enabled: bool):
        """Enable or disable automatic context compression"""
        self._compression_enabled = enabled
        logger.info(f"Context compression {'enabled' if enabled else 'disabled'}")
    
    def get_congress_summary(self) -> Dict:
        """Get summary of all Congressional votes"""
        return self.congress.get_voting_summary()