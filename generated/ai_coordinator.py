"""
AI Coordinator for GitLlama - Updated to use simple query interface
Showing key method updates only
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .ollama_client import OllamaClient
from .ai_query import AIQuery  # New simple interface
from .project_analyzer import ProjectAnalyzer
from .branch_analyzer import BranchAnalyzer
from .file_modifier import FileModifier
from .report_generator import ReportGenerator
from .context_manager import context_manager

logger = logging.getLogger(__name__)


class AICoordinator:
    """Coordinates AI decisions throughout the git workflow"""
    
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434", repo_url: str = None):
        self.model = model
        self.client = OllamaClient(base_url)
        self.ai = AIQuery(self.client, model)  # NEW: Simple query interface
        
        # Initialize report generator if repo_url is provided
        self.report_generator = None
        if repo_url:
            self.report_generator = ReportGenerator(repo_url)
        
        # Initialize the analyzers with the new AI interface
        self.project_analyzer = ProjectAnalyzer(self.client, model, self.report_generator)
        self.branch_analyzer = BranchAnalyzer(self.client, model, self.report_generator)
        self.file_modifier = FileModifier(self.client, model, self.report_generator)
        
        logger.info(f"Initialized AI Coordinator with model: {model}")
    
    def decide_file_operations(self, repo_path: Path, project_info: Dict) -> List[Dict[str, str]]:
        """AI decides what file operations to perform using simple interface."""
        logger.info("AI deciding on file operations")
        
        # Use simple choice for operation type
        operation_result = self.ai.choice(
            question="What file operation should we perform?",
            options=["CREATE a new file", "MODIFY an existing file", "DELETE an unnecessary file"],
            context=f"Project type: {project_info.get('project_type', 'unknown')}"
        )
        
        operation = operation_result.value.split()[0]  # Extract CREATE/MODIFY/DELETE
        
        # Use choice for file type
        file_type_result = self.ai.choice(
            question=f"What type of file should we {operation.lower()}?",
            options=["documentation", "configuration", "code", "test", "build script"],
            context=f"Project: {project_info.get('project_type', 'unknown')}"
        )
        
        # Map to file path
        file_paths = {
            "documentation": "docs/AI_NOTES.md",
            "configuration": "config.json", 
            "code": "src/feature.py",
            "test": "tests/test_feature.py",
            "build script": "Makefile"
        }
        
        file_path = file_paths.get(file_type_result.value, "file.txt")
        
        # Generate content if needed
        content = ""
        if operation in ["CREATE", "MODIFY"]:
            content_result = self.ai.open(
                prompt=f"Generate complete content for {file_path}. Wrap in markdown code blocks.",
                context=f"Project type: {project_info.get('project_type', 'unknown')}"
            )
            
            # Extract code from response
            from .response_parser import ResponseParser
            parser = ResponseParser()
            content = parser.extract_code(content_result.content)
        
        logger.info(f"AI decided: {operation} {file_path}")
        
        return [{
            "operation": operation,
            "file_path": file_path,
            "content": content,
            "reason": f"{operation_result.value} - {file_type_result.value}"
        }]
    
    def generate_commit_message(self, operations: List[Dict[str, str]]) -> str:
        """AI generates a commit message using simple interface."""
        logger.info("AI generating commit message")
        
        # Use choice for commit type
        type_result = self.ai.choice(
            question="What type of commit is this?",
            options=["feat", "fix", "docs", "chore", "refactor"],
            context=f"Operations: {[op['operation'] + ' ' + op['file_path'] for op in operations]}"
        )
        
        # Generate message content
        msg_result = self.ai.open(
            prompt="Generate a short commit message (max 50 chars). Just the message, no explanation.",
            context=f"Commit type: {type_result.value}, Files: {[op['file_path'] for op in operations]}"
        )
        
        message = f"{type_result.value}: {msg_result.content.strip()}"
        return message[:72]  # Ensure max length