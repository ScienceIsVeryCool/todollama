"""
File Modifier updates - showing how to use simple query interface
"""

from .ai_query import AIQuery

class FileModifier:
    """AI-driven file modification system"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b", report_generator=None):
        self.client = client
        self.model = model
        self.ai = AIQuery(client, model)  # NEW: Simple query interface
        self.report_generator = report_generator
        
    def _should_continue_modifying(self, repo_path: Path, project_info: Dict, modified_files: List[str]) -> bool:
        """Ask AI if we should continue modifying files."""
        logger.info("🤔 Asking AI if more modifications are needed")
        
        context = f"Project type: {project_info.get('project_type', 'unknown')}\n"
        context += f"Files already modified: {modified_files if modified_files else 'None'}"
        
        result = self.ai.choice(
            question="Should we continue modifying more files?",
            options=["YES - Continue modifying", "NO - Changes are sufficient"],
            context=context
        )
        
        decision = "YES" in result.value
        
        if self.report_generator:
            self.report_generator.add_ai_decision(
                "Continue Modifying Files",
                result.value,
                f"Modified {len(modified_files)} files so far"
            )
        
        return decision
    
    def _validate_file_change(self, repo_path: Path, target_file: Dict, content: str, project_info: Dict) -> Dict[str, Any]:
        """AI validates if the file change was successful."""
        logger.info(f"🔍 Validating {target_file['file_path']}")
        
        goal = target_file.get('goal', 'Improve the project')
        
        result = self.ai.choice(
            question="Does this file change meet its goal?",
            options=[
                "Perfect - No changes needed",
                "Good - Minor improvements possible", 
                "Needs work - Retry required",
                "Failed - Major issues"
            ],
            context=f"File: {target_file['file_path']}\nGoal: {goal}\nContent length: {len(content)} chars"
        )
        
        success = "Perfect" in result.value or "Good" in result.value
        
        if self.report_generator:
            self.report_generator.add_ai_decision(
                f"Validate {target_file['file_path']}",
                "PASS" if success else "RETRY",
                result.value
            )
        
        return {
            "success": success,
            "reason": result.value
        }
    
    def _generate_file_content_with_goal_reminder(self, repo_path: Path, project_info: Dict, 
                                                 target_file: Dict, retry_num: int) -> str:
        """Generate file content with goal reminder for retries."""
        file_path = target_file['file_path']
        goal = target_file.get('goal', 'Improve the project')
        
        context = f"Project Type: {project_info.get('project_type', 'unknown')}\n"
        context += f"File: {file_path}\n"
        context += f"Goal: {goal}"
        
        if retry_num > 0:
            context += f"\nThis is retry attempt {retry_num + 1}/3. Previous attempt did not meet requirements."
        
        # Get language for the file
        language = self._get_language_from_path(file_path)
        
        prompt = f"Generate complete content for this file. Wrap in ```{language} code blocks."
        
        result = self.ai.open(prompt=prompt, context=context)
        
        # Extract code from response
        from .response_parser import ResponseParser
        parser = ResponseParser()
        content = parser.extract_code(result.content)
        
        return content