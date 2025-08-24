"""
Context Tracker for GitLlama
Tracks all context variables and their usage in prompts
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ContextTracker:
    """Tracks all context variables used throughout GitLlama execution"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the context tracker (only once)"""
        if not self._initialized:
            # Store contexts by stage/phase
            self.stages: Dict[str, Dict[str, Any]] = {}
            self.current_stage: Optional[str] = None
            self.stage_order: List[str] = []
            # Track the current prompt being built
            self.current_prompt_variables: Dict[str, Any] = {}
            ContextTracker._initialized = True
            logger.info("📝 Context Tracker initialized")
    
    def start_stage(self, stage_name: str):
        """Start tracking a new stage/phase"""
        self.current_stage = stage_name
        if stage_name not in self.stages:
            self.stages[stage_name] = {
                "timestamp": datetime.now().isoformat(),
                "variables": {},
                "prompts": [],
                "responses": [],
                "prompt_response_pairs": []  # New: paired prompts and responses
            }
            self.stage_order.append(stage_name)
        # Clear current prompt variables for new stage
        self.current_prompt_variables.clear()
        logger.debug(f"📍 Started tracking stage: {stage_name}")
    
    def store_variable(self, var_name: str, content: Any, description: str = ""):
        """Store a context variable for the current stage"""
        if not self.current_stage:
            logger.warning("No active stage - starting default stage")
            self.start_stage("default")
        
        # Convert content to string representation
        if isinstance(content, (list, dict)):
            content_str = json.dumps(content, indent=2, default=str)
        elif isinstance(content, Path):
            content_str = str(content)
        else:
            content_str = str(content)
        
        # Store with metadata
        var_data = {
            "content": content_str,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "type": type(content).__name__,
            "size": len(content_str)
        }
        
        self.stages[self.current_stage]["variables"][var_name] = var_data
        
        # Also store in current prompt variables for template tracking
        self.current_prompt_variables[var_name] = content_str
        
        logger.debug(f"📦 Stored variable '{var_name}' ({len(content_str)} chars) in stage '{self.current_stage}'")
    
    def store_prompt_and_response(self, prompt: str, response: str, 
                                 template: Optional[str] = None,
                                 variable_map: Optional[Dict[str, str]] = None):
        """Store a prompt with its response and variable mapping
        
        Args:
            prompt: The final prompt sent to AI
            response: The AI's response
            template: Optional template showing where variables go
            variable_map: Optional explicit mapping of variables used
        """
        if not self.current_stage:
            self.start_stage("default")
        
        # If no variable map provided, use current prompt variables
        if variable_map is None:
            variable_map = self.current_prompt_variables.copy()
        
        # Try to identify variables in the prompt if template not provided
        if not template:
            template, variable_map = self._extract_template_from_prompt(prompt, variable_map)
        
        pair_data = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "template": template,
            "variables_used": variable_map,
            "prompt_size": len(prompt),
            "response_size": len(response)
        }
        
        self.stages[self.current_stage]["prompt_response_pairs"].append(pair_data)
        
        # Also store in old format for backward compatibility
        self.stages[self.current_stage]["prompts"].append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "combined_size": len(prompt)
        })
        self.stages[self.current_stage]["responses"].append({
            "timestamp": datetime.now().isoformat(),
            "response": response,
            "type": "ai_response",
            "size": len(response)
        })
        
        logger.debug(f"📝 Stored prompt-response pair ({len(prompt)}/{len(response)} chars) in stage '{self.current_stage}'")
    
    def _extract_template_from_prompt(self, prompt: str, variables: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
        """Try to extract a template from a prompt by identifying variable content
        
        Returns:
            Tuple of (template_with_placeholders, detected_variables)
        """
        template = prompt
        detected_vars = {}
        
        # Sort variables by length (longest first) to avoid partial replacements
        sorted_vars = sorted(variables.items(), key=lambda x: len(x[1]), reverse=True)
        
        for var_name, var_content in sorted_vars:
            if var_content and len(var_content) > 10:  # Only match substantial content
                # Escape special regex characters
                escaped_content = re.escape(var_content[:500])  # Limit to first 500 chars for matching
                
                # Try to find this content in the prompt
                if escaped_content[:100] in re.escape(prompt):
                    # Replace with placeholder
                    template = template.replace(var_content, f"{{{{ {var_name} }}}}")
                    detected_vars[var_name] = var_content
        
        return template, detected_vars
    
    def store_prompt(self, prompt: str, context: str = "", question: str = ""):
        """Store a complete prompt (backward compatibility)"""
        if not self.current_stage:
            self.start_stage("default")
        
        # Build variable map from context and question
        variable_map = {}
        if context:
            variable_map["context"] = context
        if question:
            variable_map["question"] = question
        
        # Store just the prompt for now (response will be added later)
        self._last_prompt = prompt
        self._last_variable_map = variable_map
    
    def store_response(self, response: str, response_type: str = "open"):
        """Store an AI response and pair it with the last prompt"""
        if not self.current_stage:
            self.start_stage("default")
        
        # If we have a pending prompt, create a pair
        if hasattr(self, '_last_prompt'):
            self.store_prompt_and_response(
                self._last_prompt,
                response,
                variable_map=getattr(self, '_last_variable_map', {})
            )
            # Clear the pending prompt
            delattr(self, '_last_prompt')
            if hasattr(self, '_last_variable_map'):
                delattr(self, '_last_variable_map')
        else:
            # Store response alone (backward compatibility)
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "response": response,
                "type": response_type,
                "size": len(response)
            }
            self.stages[self.current_stage]["responses"].append(response_data)
        
        logger.debug(f"💬 Stored {response_type} response ({len(response)} chars) in stage '{self.current_stage}'")
    
    def get_stage_summary(self, stage_name: str) -> Dict[str, Any]:
        """Get summary of a specific stage"""
        if stage_name not in self.stages:
            return {}
        
        stage = self.stages[stage_name]
        return {
            "stage_name": stage_name,
            "timestamp": stage["timestamp"],
            "num_variables": len(stage["variables"]),
            "num_prompts": len(stage["prompts"]),
            "num_responses": len(stage["responses"]),
            "num_pairs": len(stage.get("prompt_response_pairs", [])),
            "total_variable_size": sum(v["size"] for v in stage["variables"].values()),
            "variables": stage["variables"],
            "prompts": stage["prompts"],
            "responses": stage["responses"],
            "prompt_response_pairs": stage.get("prompt_response_pairs", [])
        }
    
    def get_all_stages(self) -> List[Dict[str, Any]]:
        """Get all stages in order with their data"""
        return [self.get_stage_summary(stage) for stage in self.stage_order]
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_vars = sum(len(s["variables"]) for s in self.stages.values())
        total_prompts = sum(len(s["prompts"]) for s in self.stages.values())
        total_responses = sum(len(s["responses"]) for s in self.stages.values())
        total_pairs = sum(len(s.get("prompt_response_pairs", [])) for s in self.stages.values())
        total_size = sum(
            sum(v["size"] for v in s["variables"].values())
            for s in self.stages.values()
        )
        
        return {
            "num_stages": len(self.stages),
            "total_variables": total_vars,
            "total_prompts": total_prompts,
            "total_responses": total_responses,
            "total_pairs": total_pairs,
            "total_data_size": total_size,
            "stages": list(self.stage_order)
        }
    
    def export_for_report(self) -> Dict[str, Any]:
        """Export all tracked data for the HTML report"""
        return {
            "stats": self.get_total_stats(),
            "stages": self.get_all_stages(),
            "stage_order": self.stage_order,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset(self):
        """Reset all tracking (for testing)"""
        self.stages.clear()
        self.current_stage = None
        self.stage_order.clear()
        self.current_prompt_variables.clear()
        logger.info("🔄 Context tracker reset")


# Global instance
context_tracker = ContextTracker()