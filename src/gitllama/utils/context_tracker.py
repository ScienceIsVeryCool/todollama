"""
Context Tracker for GitLlama
Tracks all context variables used in AI prompts for full transparency
"""

import logging
from typing import Dict, Any, List, Optional
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
                "responses": []
            }
            self.stage_order.append(stage_name)
        logger.debug(f"📍 Started tracking stage: {stage_name}")
    
    def store_variable(self, var_name: str, content: Any, description: str = ""):
        """Store a context variable for the current stage
        
        Args:
            var_name: Name of the variable
            content: The actual content (will be converted to string)
            description: Optional description of what this variable is for
        """
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
        self.stages[self.current_stage]["variables"][var_name] = {
            "content": content_str,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "type": type(content).__name__,
            "size": len(content_str)
        }
        
        logger.debug(f"📦 Stored variable '{var_name}' ({len(content_str)} chars) in stage '{self.current_stage}'")
    
    def store_prompt(self, prompt: str, context: str = "", question: str = ""):
        """Store a complete prompt that was sent to AI
        
        Args:
            prompt: The main prompt text
            context: Any context that was included
            question: The specific question if applicable
        """
        if not self.current_stage:
            self.start_stage("default")
        
        prompt_data = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "context": context,
            "question": question,
            "combined_size": len(prompt) + len(context) + len(question)
        }
        
        self.stages[self.current_stage]["prompts"].append(prompt_data)
        logger.debug(f"📝 Stored prompt ({len(prompt)} chars) in stage '{self.current_stage}'")
    
    def store_response(self, response: str, response_type: str = "open"):
        """Store an AI response
        
        Args:
            response: The AI's response
            response_type: Type of response (choice, open, etc.)
        """
        if not self.current_stage:
            self.start_stage("default")
        
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
            "total_variable_size": sum(v["size"] for v in stage["variables"].values()),
            "variables": stage["variables"],
            "prompts": stage["prompts"],
            "responses": stage["responses"]
        }
    
    def get_all_stages(self) -> List[Dict[str, Any]]:
        """Get all stages in order with their data"""
        return [self.get_stage_summary(stage) for stage in self.stage_order]
    
    def get_variable_across_stages(self, var_name: str) -> Dict[str, Any]:
        """Track how a variable changed across stages"""
        history = {}
        for stage_name in self.stage_order:
            if var_name in self.stages[stage_name]["variables"]:
                history[stage_name] = self.stages[stage_name]["variables"][var_name]
        return history
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_vars = sum(len(s["variables"]) for s in self.stages.values())
        total_prompts = sum(len(s["prompts"]) for s in self.stages.values())
        total_responses = sum(len(s["responses"]) for s in self.stages.values())
        total_size = sum(
            sum(v["size"] for v in s["variables"].values())
            for s in self.stages.values()
        )
        
        return {
            "num_stages": len(self.stages),
            "total_variables": total_vars,
            "total_prompts": total_prompts,
            "total_responses": total_responses,
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
        logger.info("🔄 Context tracker reset")


# Global instance
context_tracker = ContextTracker()