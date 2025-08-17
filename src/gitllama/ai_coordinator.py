"""
AI Coordinator for GitLlama
Manages AI decision-making at each step of the git workflow
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .ollama_client import OllamaClient
from .project_analyzer import ProjectAnalyzer
from .branch_analyzer import BranchAnalyzer

logger = logging.getLogger(__name__)


class AICoordinator:
    """Coordinates AI decisions throughout the git workflow"""
    
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.client = OllamaClient(base_url)
        self.context_window = []
        
        # Initialize the analyzers
        self.project_analyzer = ProjectAnalyzer(self.client, model)
        self.branch_analyzer = BranchAnalyzer(self.client, model)
        
        logger.info(f"Initialized AI Coordinator with model: {model}")
    
    def explore_repository(self, repo_path: Path, analyze_all_branches: bool = False) -> Dict:
        """Explore the repository using the dedicated ProjectAnalyzer.
        
        This delegates the complex analysis to ProjectAnalyzer which handles:
        - Data gathering
        - Chunking
        - Parallel analysis
        - Hierarchical merging
        - Result formatting
        - Multi-branch analysis (if requested)
        
        Args:
            repo_path: Path to the repository
            analyze_all_branches: Whether to analyze all branches
            
        Returns:
            Analysis results dictionary
        """
        logger.info(f"AI Coordinator delegating repository exploration to ProjectAnalyzer")
        
        if analyze_all_branches:
            # Analyze all branches and store comprehensive results
            current_branch, branch_analyses = self.project_analyzer.analyze_all_branches(repo_path)
            
            # Store branch analyses for branch selection
            self.branch_analyses = branch_analyses
            self.current_branch = current_branch
            
            # Use current branch analysis as the main result
            analysis_result = branch_analyses.get(current_branch, {})
            analysis_result['all_branches'] = list(branch_analyses.keys())
            analysis_result['current_branch'] = current_branch
        else:
            # Single branch analysis
            analysis_result = self.project_analyzer.analyze_repository(repo_path)
            self.branch_analyses = None
            self.current_branch = None
        
        # Store in context window for future reference
        self.context_window.append({
            "type": "exploration",
            "analysis": analysis_result,
            "branch_analyses": self.branch_analyses if analyze_all_branches else None
        })
        
        return analysis_result
    
    def decide_branch_name(self, repo_path: Path, project_info: Dict[str, str]) -> str:
        """AI decides on an appropriate branch name using BranchAnalyzer.
        
        This now uses the intelligent BranchAnalyzer which:
        - Analyzes existing branches
        - Evaluates reuse potential
        - Makes intelligent decisions about branch creation/reuse
        - Generates appropriate branch names
        
        Args:
            repo_path: Path to the repository
            project_info: Project analysis results
            
        Returns:
            Selected or generated branch name
        """
        logger.info("AI deciding on branch name using BranchAnalyzer")
        
        # If we have branch analyses from exploration, use them
        if hasattr(self, 'branch_analyses') and self.branch_analyses and hasattr(self, 'current_branch'):
            branch_summaries = self.branch_analyses
            current_branch = self.current_branch or 'main'  # Provide fallback if None
        else:
            # Fallback: analyze branches now if not done during exploration
            logger.info("Branch analyses not available, analyzing now...")
            current_branch, branch_summaries = self.project_analyzer.analyze_all_branches(repo_path)
        
        # Use BranchAnalyzer for intelligent branch selection
        selected_branch, reason, metadata = self.branch_analyzer.analyze_and_select_branch(
            repo_path, current_branch, project_info, branch_summaries
        )
        
        # Handle metadata which could be a dict or other type
        action = metadata.get('action', 'unknown') if isinstance(metadata, dict) else 'unknown'
        
        # Store decision in context
        self.context_window.append({
            "type": "branch_decision",
            "branch": selected_branch,
            "reason": reason,
            "action": action,
            "metadata": metadata
        })
        
        logger.info(f"AI selected branch: {selected_branch} (Action: {action})")
        logger.info(f"Reason: {reason}")
        
        return selected_branch
    
    def decide_file_operations(self, repo_path: Path, project_info: Dict[str, str]) -> List[Dict[str, str]]:
        """AI decides what file operations to perform based on deep project understanding."""
        logger.info("AI deciding on file operations")
        
        # Extract detailed information from the analysis
        project_type = project_info.get("project_type", "unknown")
        technologies = project_info.get("technologies", [])
        quality = project_info.get("quality", "unknown")
        patterns = project_info.get("patterns", [])
        
        # Build a comprehensive context
        context_summary = f"""Project Analysis Summary:
- Type: {project_type}
- Technologies: {', '.join(technologies[:10]) if technologies else 'none detected'}
- Code Quality: {quality}
- Key Patterns: {', '.join(patterns[:5]) if patterns else 'none detected'}
- Total Files: {project_info.get('analysis_metadata', {}).get('total_files', 0)}

Previous decisions:
{json.dumps(self.context_window[-2:], indent=2) if len(self.context_window) > 1 else 'None'}"""
        
        logger.info(f"🤖 AI: Deciding file operations based on project analysis")
        
        prompt = f"""{context_summary}

Based on this comprehensive project analysis, suggest ONE meaningful file operation that would improve the repository.

Consider:
1. What documentation might be missing?
2. What configuration could be improved?
3. What utility or helper might be useful?
4. What test or example might add value?

Choose one operation:
- CREATE a new file (documentation, config, utility, test, example)
- MODIFY an existing file (improve code, fix issues, enhance features)
- DELETE an unnecessary file

Respond in JSON format:
{{
    "operation": "CREATE|MODIFY|DELETE",
    "file_path": "path/to/file",
    "content": "file content here (for CREATE/MODIFY)",
    "reason": "brief explanation of why this improves the project"
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
            logger.info(f"AI decided on operation: {operation['operation']} {operation['file_path']}")
            return [operation]
        except json.JSONDecodeError:
            # Fallback: create a project insights file
            fallback = {
                "operation": "CREATE",
                "file_path": "PROJECT_INSIGHTS.md",
                "content": f"""# Project Insights

Generated by GitLlama AI Analysis

## Project Type
{project_type}

## Technologies Detected
{chr(10).join('- ' + tech for tech in technologies[:10]) if technologies else '- None detected'}

## Code Quality Assessment
{quality if quality else 'Not assessed'}

## Key Patterns
{chr(10).join('- ' + pattern for pattern in patterns[:5]) if patterns else '- None detected'}

## Potential Improvements
- [ ] Add comprehensive documentation
- [ ] Improve test coverage
- [ ] Optimize performance bottlenecks
- [ ] Enhance error handling
- [ ] Update dependencies

---
*This file was automatically generated based on AI analysis of the repository.*
""",
                "reason": "Document AI insights and improvement suggestions"
            }
            self.context_window.append({
                "type": "file_operation",
                "operation": fallback
            })
            logger.info("AI fallback: creating PROJECT_INSIGHTS.md")
            return [fallback]
    
    def generate_commit_message(self, operations: List[Dict[str, str]]) -> str:
        """AI generates a commit message based on the operations performed."""
        logger.info("AI generating commit message")
        
        # Get project context from exploration
        project_context = None
        for ctx in self.context_window:
            if ctx.get('type') == 'exploration':
                project_context = ctx.get('analysis', {})
                break
        
        project_type = project_context.get('project_type', 'project') if project_context else 'project'
        
        logger.info(f"🤖 AI: Generating commit message for {len(operations)} operations")
        
        prompt = f"""Generate a concise, professional git commit message for these operations:
{json.dumps(operations, indent=2)}

Project type: {project_type}

Follow conventional commit format (feat:, fix:, docs:, chore:, etc.)
Keep it under 72 characters.
Be specific about what was done.

Respond with ONLY the commit message, no explanation."""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        commit_message = response.strip()
        
        # Validate and fallback if necessary
        if not commit_message or len(commit_message) > 72:
            if operations and operations[0].get('operation') == 'CREATE':
                file_name = Path(operations[0]['file_path']).name
                commit_message = f"feat: add {file_name}"
            elif operations and operations[0].get('operation') == 'MODIFY':
                file_name = Path(operations[0]['file_path']).name
                commit_message = f"fix: update {file_name}"
            else:
                commit_message = "chore: automated improvements by GitLlama"
        
        self.context_window.append({
            "type": "commit_message",
            "message": commit_message
        })
        
        logger.info(f"AI generated commit message: {commit_message}")
        return commit_message
    
    def execute_file_operations(self, repo_path: Path, operations: List[Dict[str, str]]) -> List[str]:
        """Execute the file operations decided by the AI."""
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