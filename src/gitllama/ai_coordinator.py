"""
AI Coordinator for GitLlama
Manages AI decision-making at each step of the git workflow
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AICoordinator:
    """Coordinates AI decisions throughout the git workflow"""
    
    def __init__(self, model: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.client = OllamaClient(base_url)
        self.context_window = []
        
    def explore_repository(self, repo_path: Path) -> Dict[str, str]:
        """Explore the repository structure and understand the project"""
        logger.info(f"AI exploring repository at {repo_path}")
        
        # Gather basic file structure
        files_info = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                relative_path = file_path.relative_to(repo_path)
                # Skip binary files and large files
                if file_path.suffix in ['.py', '.js', '.tsx', '.jsx', '.md', '.txt', '.json', '.yaml', '.yml']:
                    try:
                        if file_path.stat().st_size < 10000:  # Only read files under 10KB for context
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()[:500]  # First 500 chars
                                files_info.append(f"File: {relative_path}\nPreview: {content}\n")
                    except Exception as e:
                        logger.debug(f"Could not read {file_path}: {e}")
        
        context = "\n".join(files_info[:20])  # Limit to first 20 files
        
        prompt = f"""Analyze this repository structure and content:

{context}

Provide a brief summary of:
1. What type of project this is
2. Main technologies used
3. Current state of the codebase

Response in JSON format:
{{"project_type": "", "technologies": [], "state": ""}}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        try:
            analysis = json.loads(response)
            self.context_window.append({
                "type": "exploration",
                "analysis": analysis
            })
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "project_type": "unknown",
                "technologies": [],
                "state": response[:200]
            }
    
    def decide_branch_name(self, project_info: Dict[str, str]) -> str:
        """AI decides on an appropriate branch name"""
        logger.info("AI deciding on branch name")
        
        prompt = f"""Based on this project analysis:
{json.dumps(project_info, indent=2)}

Suggest a meaningful branch name for making an improvement to this repository.
The branch name should be specific and descriptive.
Do NOT suggest 'main' or 'master'.

Respond with ONLY the branch name, no explanation."""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        branch_name = response.strip().replace(' ', '-').lower()
        
        # Ensure we don't use main/master
        if branch_name in ['main', 'master']:
            branch_name = 'feature-improvement'
        
        self.context_window.append({
            "type": "branch_decision",
            "branch": branch_name
        })
        
        return branch_name
    
    def decide_file_operations(self, repo_path: Path, project_info: Dict[str, str]) -> List[Dict[str, str]]:
        """AI decides what file operations to perform"""
        logger.info("AI deciding on file operations")
        
        # Get current context
        context_summary = f"""Project Analysis:
{json.dumps(project_info, indent=2)}

Previous decisions:
{json.dumps(self.context_window[-2:], indent=2) if len(self.context_window) > 1 else 'None'}"""
        
        prompt = f"""{context_summary}

Based on this project, suggest ONE file operation that would improve the repository.
Choose one of these operations:
1. CREATE a new file (like documentation, config, or utility)
2. MODIFY an existing file (improve code, fix issues, add features)
3. DELETE an unnecessary file

Respond in JSON format:
{{
    "operation": "CREATE|MODIFY|DELETE",
    "file_path": "path/to/file",
    "content": "file content here (for CREATE/MODIFY)",
    "reason": "brief explanation"
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        try:
            operation = json.loads(response)
            self.context_window.append({
                "type": "file_operation",
                "operation": operation
            })
            return [operation]
        except json.JSONDecodeError:
            # Fallback: create a simple improvements file
            fallback = {
                "operation": "CREATE",
                "file_path": "IMPROVEMENTS.md",
                "content": "# Improvements\n\nThis file tracks potential improvements for the project.\n\n- [ ] Add more documentation\n- [ ] Improve test coverage\n- [ ] Optimize performance\n",
                "reason": "Document improvement ideas"
            }
            self.context_window.append({
                "type": "file_operation",
                "operation": fallback
            })
            return [fallback]
    
    def generate_commit_message(self, operations: List[Dict[str, str]]) -> str:
        """AI generates a commit message based on the operations performed"""
        logger.info("AI generating commit message")
        
        prompt = f"""Generate a concise, professional git commit message for these operations:
{json.dumps(operations, indent=2)}

Follow conventional commit format (feat:, fix:, docs:, etc.)
Keep it under 72 characters.

Respond with ONLY the commit message, no explanation."""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        commit_message = response.strip()
        
        # Fallback if response is too long or empty
        if not commit_message or len(commit_message) > 72:
            if operations and operations[0].get('operation') == 'CREATE':
                commit_message = f"feat: add {Path(operations[0]['file_path']).name}"
            elif operations and operations[0].get('operation') == 'MODIFY':
                commit_message = f"fix: update {Path(operations[0]['file_path']).name}"
            else:
                commit_message = "chore: automated improvements by GitLlama"
        
        self.context_window.append({
            "type": "commit_message",
            "message": commit_message
        })
        
        return commit_message
    
    def execute_file_operations(self, repo_path: Path, operations: List[Dict[str, str]]) -> List[str]:
        """Execute the file operations decided by the AI"""
        modified_files = []
        
        for op in operations:
            file_path = repo_path / op['file_path']
            
            if op['operation'] == 'CREATE':
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(op.get('content', ''))
                logger.info(f"Created file: {op['file_path']}")
                modified_files.append(op['file_path'])
                
            elif op['operation'] == 'MODIFY':
                if file_path.exists():
                    with open(file_path, 'w') as f:
                        f.write(op.get('content', ''))
                    logger.info(f"Modified file: {op['file_path']}")
                    modified_files.append(op['file_path'])
                else:
                    logger.warning(f"File to modify does not exist: {op['file_path']}")
                    
            elif op['operation'] == 'DELETE':
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {op['file_path']}")
                    modified_files.append(op['file_path'])
                else:
                    logger.warning(f"File to delete does not exist: {op['file_path']}")
        
        return modified_files