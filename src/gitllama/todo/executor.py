"""
Python Application Executor for TODOllama
Executes Python application generation with Docker containerization and comprehensive testing
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..ai import OllamaClient, AIQuery

logger = logging.getLogger(__name__)


class TodoExecutor:
    """Executes Python application generation with Docker containerization and comprehensive testing"""
    
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
    
    def build_docker_container(self, repo_path: Path, skip_docker: bool = False) -> Dict:
        """Build Docker container for the Python application"""
        if skip_docker:
            logger.info("Skipping Docker build (--no-docker flag set)")
            return {"skipped": True, "success": False, "image_name": None}
        
        logger.info("Building Docker container for Python application")
        
        dockerfile_path = repo_path / "Dockerfile" 
        if not dockerfile_path.exists():
            logger.warning("No Dockerfile found - cannot build container")
            return {"skipped": True, "success": False, "image_name": None, "error": "No Dockerfile found"}
        
        # Use docker by default, fallback to podman if available
        container_tool = "docker"
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["podman", "--version"], capture_output=True, check=True) 
                container_tool = "podman"
                logger.info("Docker not found, using Podman instead")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("Neither Docker nor Podman found")
                return {"skipped": True, "success": False, "image_name": None, "error": "No container runtime found"}
        
        # Generate image name from project
        project_name = repo_path.name.lower().replace(" ", "-")
        image_name = f"todollama-{project_name}:latest"
        
        try:
            # Build the container
            logger.info(f"Building container image: {image_name}")
            result = subprocess.run(
                [container_tool, "build", "-t", image_name, "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully built Docker image: {image_name}")
                return {
                    "skipped": False,
                    "success": True, 
                    "image_name": image_name,
                    "container_tool": container_tool,
                    "build_output": result.stdout[-1000:]  # Last 1000 chars
                }
            else:
                logger.error(f"❌ Docker build failed with exit code {result.returncode}")
                return {
                    "skipped": False,
                    "success": False,
                    "image_name": image_name,
                    "container_tool": container_tool,
                    "error": result.stderr[-1000:]  # Last 1000 chars of error
                }
        except subprocess.TimeoutExpired:
            logger.error("Docker build timed out after 5 minutes")
            return {
                "skipped": False,
                "success": False,
                "image_name": image_name,
                "error": "Build timeout after 5 minutes"
            }
        except Exception as e:
            logger.error(f"Docker build failed with exception: {e}")
            return {
                "skipped": False,
                "success": False, 
                "image_name": image_name,
                "error": str(e)
            }
    
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
            requirements = f"""You are completely rewriting the Python application file: {file_path}

TASK: Completely rewrite {file_path} according to the Python containerization plan provided in the context.

REQUIREMENTS:
- This is a COMPLETE rewrite of {file_path}
- The file currently exists and its content is shown in the context for reference  
- Follow the plan and TODO requirements exactly for Python application development
- Generate production-ready Python code with proper error handling, logging, and documentation
- Use modern Python best practices: type hints, docstrings, proper imports
- For Python files (.py): Include proper imports, error handling, logging setup
- For Docker files: Use official Python base images, multi-stage builds where appropriate
- For config files: Use environment variables, proper validation
- For requirements.txt: Pin versions for production stability
- Do NOT include markdown code blocks or explanations
- Output only the raw file content that will be saved to {file_path}"""
        else:
            # File doesn't exist - create new
            requirements = f"""You are creating a new Python application file: {file_path}

TASK: Create complete content for the new file {file_path} based on the Python containerization plan and TODO.

REQUIREMENTS:
- This is a NEW file creation for {file_path}
- Follow the plan and TODO requirements exactly for Python application development
- Generate production-ready Python code with proper error handling, logging, and documentation
- Use modern Python best practices: type hints, docstrings, proper imports
- For Python files (.py): Include proper imports, error handling, logging setup, main guards
- For Docker files: Use official Python base images, efficient layering, health checks
- For config files: Use environment variables, proper validation
- For requirements.txt: Pin versions for production stability
- For test files: Use pytest framework with proper fixtures and assertions
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
        
        requirements = f"""Generate a comprehensive test.sh bash script to test the Python application implementation with Docker containerization support.

ENVIRONMENT INFORMATION:
- Operating System: Ubuntu Linux
- Python3 is installed and available
- Docker/Podman may be available for container testing
- A virtual environment (venv) should be used for Python projects
- The script will run from the project root: {repo_path}
- IMPORTANT: Assume we are NOT running as sudo - use only user-level commands

MODIFIED FILES:
{files_list}

IMPLEMENTATION PLAN:
{action_plan['plan'][:1500]}

PYTHON + DOCKER TESTING SCRIPT REQUIREMENTS:
1. Start with #!/bin/bash and set -e for error handling
2. Begin with comprehensive environment logging:
   - Print current working directory (pwd)
   - List files in current directory (ls -la)
   - Show disk space usage (df -h .)
   - Display current user and system info (whoami, uname -a)
   - Check Python version (python3 --version)
   - Check if Docker/Podman is available
3. Test Python application directly:
   - Create and activate a virtual environment
   - Install all dependencies (pip install -r requirements.txt or similar)
   - Run Python syntax checks (python -m py_compile on .py files)
   - Run any existing test suites (pytest, unittest discover, etc.)
4. Test Docker containerization if Dockerfile exists:
   - Attempt to build Docker image (docker build or podman build)
   - Basic container functionality test if build succeeds
5. Test the specific Python functionality mentioned in the TODO
6. Include meaningful echo statements to show progress
7. Validate Python best practices: imports, syntax, basic functionality
8. Exit with code 0 on success, non-zero on failure
9. Be thorough but complete within 120 seconds (allow more time for Docker builds)

The script should verify both Python application functionality AND containerization."""

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
        logger.info(f"Running test.sh with {timeout}s timeout from {repo_path}")
        
        test_script_path = repo_path / "test.sh"
        
        # Add pre-execution environment logging
        pre_execution_info = f"""
🧪 GITLLAMA TEST EXECUTION STARTING
=====================================
📍 Execution Environment:
  Repository Path: {repo_path}
  Test Script Path: {test_script_path}
  Current Working Directory: {Path.cwd()}
  Script Size: {len(test_script_content)} bytes
  Timeout: {timeout} seconds
  
📁 Pre-execution Directory State:
"""
        
        try:
            # Gather pre-execution environment info
            try:
                import os
                import shutil
                dir_contents = subprocess.run(
                    ["ls", "-la", str(repo_path)], 
                    capture_output=True, text=True, timeout=5
                ).stdout
                disk_info = subprocess.run(
                    ["df", "-h", str(repo_path)], 
                    capture_output=True, text=True, timeout=5
                ).stdout
                pre_execution_info += f"{dir_contents}\n💾 Disk Usage:\n{disk_info}\n"
            except Exception as e:
                pre_execution_info += f"Could not gather pre-execution info: {e}\n"
            
            pre_execution_info += "=====================================\n\n"
            
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
            
            # Add post-execution summary
            post_execution_info = f"""
=====================================
🧪 GITLLAMA TEST EXECUTION COMPLETED
=====================================
📊 Execution Summary:
  Status: {'✅ SUCCESS' if success else '❌ FAILED'}
  Exit Code: {exit_code}
  Duration: {elapsed:.2f} seconds
  Timeout: {'❌ YES' if exit_code == -1 else '✅ NO'}
  
📁 Repository Path: {repo_path}
💾 Script Size: {len(test_script_content)} bytes
🎯 Test completed at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================
"""
            
            # Combine all output
            full_output = pre_execution_info + output + post_execution_info
            
            return success, full_output, exit_code
            
        except Exception as e:
            logger.error(f"Error running test script: {e}")
            error_output = pre_execution_info + f"EXECUTION ERROR: {str(e)}"
            return False, error_output, -1
        
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