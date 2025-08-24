"""
Simplified File Executor for GitLlama
Executes the planned file operations
"""

import logging
from pathlib import Path
from typing import Dict, List
from ..ai import OllamaClient, AIQuery

logger = logging.getLogger(__name__)


class TodoExecutor:
    """Executes planned file operations"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        self.client = client
        self.model = model
        self.ai = AIQuery(client, model)
    
    def execute_plan(self, repo_path: Path, action_plan: Dict) -> tuple[List[str], Dict[str, Dict]]:
        """Execute the action plan and capture file diffs
        
        Returns:
            Tuple of (modified_files, file_diffs) where file_diffs contains before/after content
        """
        logger.info(f"Executing plan with {len(action_plan['files_to_modify'])} files")
        
        modified_files = []
        file_diffs = {}
        
        for file_info in action_plan['files_to_modify']:
            file_path = repo_path / file_info['path']
            operation = file_info['operation']
            
            logger.info(f"Executing {operation} on {file_info['path']}")
            
            if operation == 'EDIT':
                # Check if file exists to provide context to AI
                original_content = ""
                if file_path.exists():
                    original_content = file_path.read_text()
                
                content = self._edit_file_content(
                    file_info['path'],
                    original_content,
                    action_plan['plan'],
                    action_plan['todo_excerpt']
                )
                
                # Store diff information
                file_diffs[file_info['path']] = {
                    'before': original_content,
                    'after': content,
                    'operation': operation
                }
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                modified_files.append(file_info['path'])
                
            elif operation == 'DELETE':
                if file_path.exists():
                    original_content = file_path.read_text()
                    file_diffs[file_info['path']] = {
                        'before': original_content,
                        'after': '',
                        'operation': operation
                    }
                    file_path.unlink()
                    modified_files.append(file_info['path'])
                else:
                    logger.warning(f"File to delete doesn't exist: {file_info['path']}")
        
        return modified_files, file_diffs
    
    def _edit_file_content(self, file_path: str, original_content: str, plan: str, todo: str) -> str:
        """Edit file content (create new or completely rewrite existing)"""
        from ..utils.context_tracker import context_tracker
        
        # Store variables separately instead of embedding in context
        file_name = Path(file_path).name
        file_type = Path(file_path).suffix
        context_name = f"rewrite_{file_name}" if original_content else f"create_{file_name}"
        
        # Store individual variables for tracking
        context_tracker.store_variable(f"{context_name}_file_path", file_path, f"Target file path: {file_path}")
        context_tracker.store_variable(f"{context_name}_file_name", file_name, f"Target file name: {file_name}")  
        context_tracker.store_variable(f"{context_name}_file_type", file_type, f"File extension: {file_type}")
        context_tracker.store_variable(f"{context_name}_plan", plan[:1500], "Action plan excerpt")
        context_tracker.store_variable(f"{context_name}_todo", todo[:500], "TODO excerpt")
        
        if original_content:
            context_tracker.store_variable(f"{context_name}_original_content", original_content[:2000], "Current file content for reference")
        
        # Build clean context without embedded variables
        context_parts = [
            "=== PLAN CONTEXT ===",
            plan[:1500],
            "",
            "=== TODO CONTEXT ===", 
            todo[:500]
        ]
        
        if original_content:
            context_parts.extend([
                "",
                "=== CURRENT FILE CONTENT (for reference) ===",
                original_content[:2000]
            ])
        
        clean_context = "\n".join(context_parts)
        
        if original_content:
            # File exists - edit it
            requirements = f"""You are completely rewriting the file: {file_path}

TASK: Completely rewrite {file_path} according to the plan provided in the context.

REQUIREMENTS:
- This is a COMPLETE rewrite of {file_path}
- The file currently exists and its content is shown in the context for reference
- Follow the plan and TODO requirements exactly
- Generate professional, working code with appropriate comments
- Use proper syntax and conventions for {file_type} files
- Do NOT include markdown code blocks or explanations
- Output only the raw file content that will be saved to {file_path}"""
        else:
            # File doesn't exist - create new
            requirements = f"""You are creating a new file: {file_path}

TASK: Create complete content for the new file {file_path} based on the plan and TODO.

REQUIREMENTS:
- This is a NEW file creation for {file_path}
- Follow the plan and TODO requirements exactly
- Generate professional, working code with appropriate comments
- Use proper syntax and conventions for {file_type} files
- Do NOT include markdown code blocks or explanations  
- Output only the raw file content that will be saved to {file_path}"""
        
        result = self.ai.file_write(
            requirements=requirements,
            context=clean_context,
            context_name=context_name
        )
        
        # The file_write query already cleans the content
        return result.content