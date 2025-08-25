"""
Simplified File Executor for GitLlama
Executes the planned file operations and runs tests
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..ai import OllamaClient, AIQuery

logger = logging.getLogger(__name__)


class TodoExecutor:
    """Executes planned file operations and tests"""
    
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
                # Validate file path - skip if it's a directory
                if file_path.exists() and file_path.is_dir():
                    logger.warning(f"Skipping directory path: {file_info['path']} - cannot write to directory")
                    continue
                
                # Check if file exists to provide context to AI
                original_content = ""
                if file_path.exists() and file_path.is_file():
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
                
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
                    modified_files.append(file_info['path'])
                    logger.info(f"✅ Successfully wrote file: {file_info['path']}")
                except Exception as e:
                    logger.error(f"❌ Failed to write file {file_info['path']}: {e}")
                    continue
                
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
    
    def generate_test_script(self, repo_path: Path, modified_files: List[str], action_plan: Dict) -> str:
        """Generate test.sh script to test the implemented changes"""
        logger.info("Generating test.sh script")
        
        # Build context about what was done
        files_list = "\n".join(f"- {f}" for f in modified_files)
        
        requirements = f"""Generate a comprehensive test.sh bash script to test the TODO implementation.

ENVIRONMENT INFORMATION:
- Operating System: Ubuntu Linux
- Python3 is installed and available
- A virtual environment (venv) should be used for Python projects
- The script will run from the project root: {repo_path}

MODIFIED FILES:
{files_list}

IMPLEMENTATION PLAN:
{action_plan['plan'][:1500]}

SCRIPT REQUIREMENTS:
1. Start with #!/bin/bash and set -e for error handling
2. Include ALL installation steps needed from a clean Ubuntu environment
3. For Python projects:
   - Create and activate a virtual environment
   - Install all dependencies (pip install -r requirements.txt or similar)
   - Run any setup commands
4. Test the actual functionality that was implemented
5. Include meaningful echo statements to show progress
6. Run any existing test suites if present (pytest, npm test, etc.)
7. Test the specific features mentioned in the TODO
8. Exit with code 0 on success, non-zero on failure
9. Be thorough but complete within 60 seconds

The script should verify that the TODO implementation actually works."""

        context = f"""Project Structure Information:
Modified {len(modified_files)} files to implement TODO items.

TODO excerpt that was implemented:
{action_plan.get('todo_excerpt', 'TODO implementation')}"""
        
        result = self.ai.file_write(
            requirements=requirements,
            context=context,
            context_name="test_script_generation"
        )
        
        return result.content
    
    def run_test_script(self, repo_path: Path, test_script_content: str, timeout: int = 60) -> Tuple[bool, str, int]:
        """Run test.sh script with timeout and capture output
        
        Returns:
            Tuple of (success, output, exit_code)
        """
        logger.info(f"Running test.sh with {timeout}s timeout")
        
        test_script_path = repo_path / "test.sh"
        
        try:
            # Write test script
            test_script_path.write_text(test_script_content)
            test_script_path.chmod(0o755)  # Make executable
            
            # Run the script with timeout
            start_time = time.time()
            process = subprocess.Popen(
                ["bash", str(test_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=repo_path
            )
            
            try:
                output, _ = process.communicate(timeout=timeout)
                exit_code = process.returncode
                success = exit_code == 0
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Test script timed out after {timeout}s")
                process.kill()
                output, _ = process.communicate()
                output += f"\n\n[TIMEOUT: Process killed after {timeout} seconds]"
                exit_code = -1
                success = False
            
            elapsed = time.time() - start_time
            logger.info(f"Test completed in {elapsed:.2f}s with exit code {exit_code}")
            
            return success, output, exit_code
            
        except Exception as e:
            logger.error(f"Error running test script: {e}")
            return False, f"Error executing test script: {str(e)}", -1
        
        finally:
            # Clean up test script
            if test_script_path.exists():
                test_script_path.unlink()
                logger.info("Cleaned up test.sh")
    
    def evaluate_test_results(self, test_output: str, exit_code: int, modified_files: List[str]) -> Dict:
        """Use AI to evaluate test results and determine if implementation was successful"""
        logger.info("Evaluating test results with AI")
        
        # Truncate output if too long
        max_output_length = 5000
        if len(test_output) > max_output_length:
            test_output = test_output[:max_output_length] + "\n\n[OUTPUT TRUNCATED]"
        
        files_list = "\n".join(f"- {f}" for f in modified_files)
        
        prompt = f"""Analyze these test results and determine if the TODO implementation was successful.

MODIFIED FILES:
{files_list}

TEST EXIT CODE: {exit_code}
TEST OUTPUT:
{test_output}

Please provide:
1. Overall assessment: Was the implementation successful?
2. What worked correctly (if anything)?
3. What failed or had issues (if anything)?
4. Specific recommendations for fixes if there were failures
5. Confidence level in your assessment (0-100%)

Be specific and technical in your analysis."""
        
        result = self.ai.open(
            prompt=prompt,
            context="",
            context_name="test_evaluation"
        )
        
        # Also get a simple yes/no assessment
        success_result = self.ai.multiple_choice(
            question="Based on the test results, was the TODO implementation successful?",
            options=["YES - Implementation successful", "NO - Implementation failed", "PARTIAL - Some features work"],
            context=f"Exit code: {exit_code}\nOutput summary: {test_output[:500]}",
            context_name="test_success_check"
        )
        
        return {
            "success": "YES" in success_result.value,
            "partial_success": "PARTIAL" in success_result.value,
            "detailed_analysis": result.content,
            "exit_code": exit_code,
            "confidence": success_result.confidence
        }