"""
GitLlama - Git Operations Module with AI Integration

AI-powered git automation: clone, branch, change, commit, push.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class GitOperationError(Exception):
    """Custom exception for git operation errors."""
    pass


class GitAutomator:
    """TODO-driven git automation class."""
    
    def __init__(self, working_dir: Optional[str] = None):
        """Initialize the GitAutomator.
        
        Args:
            working_dir: Optional working directory path
        """
        self.working_dir = Path(working_dir) if working_dir else Path(tempfile.mkdtemp())
        self.repo_path: Optional[Path] = None
        self.original_cwd = os.getcwd()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup temporary directories
        if self.repo_path and self.repo_path.exists():
            os.chdir(self.original_cwd)
            if str(self.working_dir).startswith(tempfile.gettempdir()):
                shutil.rmtree(self.working_dir, ignore_errors=True)
    
    def _run_git_command(self, command: list, cwd: Optional[Path] = None, 
                        capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        """Execute a git command and return the result.
        
        Args:
            command: Git command as list of strings
            cwd: Working directory (defaults to repo_path)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero return code
            
        Returns:
            CompletedProcess object with returncode, stdout, stderr
        """
        work_dir = cwd or self.repo_path or self.working_dir
        
        try:
            logger.info(f"🔧 Git operation: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=work_dir,
                capture_output=capture_output,
                text=True,
                check=check
            )
            
            # For backward compatibility, if check=True and capture_output=True,
            # return the result object but also allow accessing stdout as before
            if check and capture_output:
                # Add a string representation for backward compatibility
                result.stdout_stripped = result.stdout.strip() if result.stdout else ""
                
            return result
            
        except subprocess.CalledProcessError as e:
            # Get both stderr and stdout for better error messages
            stderr_msg = e.stderr.strip() if e.stderr else "No error details available"
            stdout_msg = e.stdout.strip() if e.stdout else ""
            
            # Combine error messages
            error_details = stderr_msg
            if stdout_msg and stdout_msg != stderr_msg:
                error_details = f"{stderr_msg}\nOutput: {stdout_msg}"
            
            error_msg = f"Git command failed: {' '.join(command)}\nError: {error_details}"
            logger.error(error_msg)
            raise GitOperationError(error_msg) from e
    
    def clone_repository(self, git_url: str) -> Path:
        """Clone a git repository."""
        logger.info(f"🔧 Git: Cloning repository: {git_url}")
        
        # Extract repository name from URL
        repo_name = git_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        self.repo_path = self.working_dir / repo_name
        
        self._run_git_command(['git', 'clone', git_url, str(self.repo_path)], cwd=self.working_dir)
        logger.info(f"Successfully cloned to {self.repo_path}")
        return self.repo_path
    
    def checkout_branch(self, branch_name: str) -> str:
        """Checkout a branch, creating it if it doesn't exist."""
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        # First check if the branch already exists (locally or remotely)
        try:
            # Check if branch exists locally
            result = self._run_git_command(['git', 'rev-parse', '--verify', branch_name], 
                                          capture_output=True, check=False)
            
            if result.returncode == 0:
                # Branch exists locally, just checkout (no -b)
                logger.info(f"🔧 Git: Checking out existing branch: {branch_name}")
                self._run_git_command(['git', 'checkout', branch_name])
                logger.info(f"Successfully checked out existing branch: {branch_name}")
                return branch_name
            
            # Check if branch exists as remote
            remote_branch = f"origin/{branch_name}"
            result = self._run_git_command(['git', 'rev-parse', '--verify', remote_branch],
                                          capture_output=True, check=False)
            
            if result.returncode == 0:
                # Remote branch exists, create tracking branch
                logger.info(f"🔧 Git: Creating tracking branch from remote: {branch_name}")
                self._run_git_command(['git', 'checkout', '-b', branch_name, remote_branch])
                logger.info(f"Successfully created and checked out tracking branch: {branch_name}")
                return branch_name
            
            # Branch doesn't exist anywhere, create new
            logger.info(f"🔧 Git: Creating new branch: {branch_name}")
            self._run_git_command(['git', 'checkout', '-b', branch_name])
            logger.info(f"Successfully created and checked out new branch: {branch_name}")
            return branch_name
            
        except subprocess.CalledProcessError as e:
            raise GitOperationError(f"Failed to checkout branch {branch_name}: {e}")
    
    def make_changes(self) -> list:
        """
        Fallback method to make simple changes.
        """
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("Making simple fallback changes to repository")
        
        # Simple default change - create a file
        filename = "gitllama_was_here.txt"
        content = "This file was created by GitLlama automation tool."
        
        file_path = self.repo_path / filename
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Created file: {filename}")
        return [filename]
    
    def commit_changes(self) -> tuple[str, str]:
        """Commit changes to the repository with AI-generated commit message.
        
        Returns:
            Tuple of (commit_hash, commit_message)
        """
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("Committing changes")
        
        # Check if there are any changes to commit
        status_result = self._run_git_command(['git', 'status', '--porcelain'])
        if not status_result.stdout.strip():
            logger.warning("No changes to commit")
            # Return a dummy commit hash or raise an error
            return "no-changes", "No changes to commit"
        
        # Add all changes
        logger.info("🔧 Git: Adding all changes to staging")
        self._run_git_command(['git', 'add', '.'])
        
        # Check if there are staged changes
        diff_result = self._run_git_command(['git', 'diff', '--cached', '--stat'])
        if not diff_result.stdout.strip():
            logger.warning("No staged changes to commit after git add")
            return "no-changes", "No staged changes to commit"
        
        # Generate commit message
        message = "feat: automated improvements by GitLlama AI\n\n🤖 Generated with GitLlama v0.7.4\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
        # Commit changes
        self._run_git_command(['git', 'commit', '-m', message])
        
        # Get commit hash
        result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        commit_hash = result.stdout.strip()
        logger.info(f"🔧 Git: Successfully committed: {commit_hash[:8]}")
        
        return commit_hash, message
    
    def push_changes(self, branch: Optional[str] = None) -> str:
        """Push changes to the remote repository."""
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("🔧 Git: Pushing changes to remote")
        
        # Get current branch if not specified
        if not branch:
            result = self._run_git_command(['git', 'branch', '--show-current'])
            branch = result.stdout.strip()
        
        # Ensure branch is not None
        if not branch:
            branch = "main"
        
        # Push changes (with --set-upstream for new branches)
        try:
            result = self._run_git_command(['git', 'push', 'origin', branch])
            logger.info("🔧 Git: Successfully pushed changes")
        except GitOperationError as e:
            if "no upstream branch" in str(e) or "has no upstream branch" in str(e):
                logger.info("🔧 Git: Setting upstream branch...")
                result = self._run_git_command(['git', 'push', '--set-upstream', 'origin', branch])
                logger.info("🔧 Git: Successfully pushed changes with upstream")
            else:
                raise
        
        return branch
    
    def run_full_workflow(self, git_url: str, branch_name: Optional[str] = None, model: str = "gemma3:4b", base_url: str = "http://localhost:11434") -> dict:
        """Run the simplified TODO-driven GitLlama workflow"""
        logger.info("Starting TODO-driven GitLlama workflow")
        
        # Import simplified coordinator
        from .coordinator import SimplifiedCoordinator
        simplified = SimplifiedCoordinator(
            model=model,
            base_url=base_url,
            git_url=git_url
        )
        
        try:
            # Step 1: Clone repository
            repo_path = self.clone_repository(git_url)
            
            # Step 2: Run simplified TODO workflow (includes testing)
            logger.info("🎯 Running TODO-driven workflow with testing")
            result = simplified.run_todo_workflow(repo_path)
            
            # Step 3: Check test results - HARD FAILURE on test exit code failure
            test_results = result.get('test_results', {})
            if test_results.get('test_executed'):
                if not test_results.get('test_passed'):
                    logger.error("❌ Tests failed with exit code: {}".format(test_results.get('test_exit_code', 'unknown')))
                    logger.error("🚫 ABORTING COMMIT due to test failure - regardless of AI assessment")
                    
                    # Generate failure report before aborting
                    report_path = None
                    if hasattr(simplified, 'generate_final_report'):
                        try:
                            report_path = simplified.generate_final_report(
                                repo_path=str(repo_path),
                                branch=branch_name or "unknown",
                                modified_files=result['modified_files'],
                                commit_hash="test-failure-abort",
                                success=False,
                                commit_message="Aborted due to test failure",
                                file_diffs=result.get('file_diffs', {}),
                                branch_info={"created": False, "base_branch": "unknown"},
                                test_results=test_results
                            )
                        except Exception as e:
                            logger.warning(f"Failed to generate failure report: {e}")
                    
                    return {
                        "success": False,
                        "error": f"Tests failed with exit code {test_results.get('test_exit_code')}. Commit aborted.",
                        "repo_path": str(repo_path),
                        "branch": branch_name or "unknown", 
                        "modified_files": result['modified_files'],
                        "test_results": test_results,
                        "commit_aborted": True,
                        "report_path": str(report_path) if report_path else None
                    }
                else:
                    logger.info("✅ Tests passed - proceeding with commit regardless of AI assessment")
            
            # Step 4: Create/checkout branch
            if not branch_name:
                branch_name = result['branch_name']
            
            # Ensure branch_name is not None
            if not branch_name:
                branch_name = "gitllama-todo-automation"
            
            self.checkout_branch(branch_name)
            
            # Step 5: Commit changes
            if result['modified_files']:
                commit_hash, commit_msg = self.commit_changes()
                self.push_changes(branch=branch_name)
            else:
                commit_hash = "no-changes"
                commit_msg = "No changes to commit"
            
            # Step 6: Generate final report
            report_path = None
            if hasattr(simplified, 'generate_final_report'):
                try:
                    report_path = simplified.generate_final_report(
                        repo_path=str(repo_path),
                        branch=branch_name,
                        modified_files=result['modified_files'],
                        commit_hash=commit_hash,
                        success=True,
                        commit_message=commit_msg,
                        file_diffs=result.get('file_diffs', {}),
                        branch_info={"created": True, "base_branch": "main"},
                        test_results=test_results
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate report: {e}")
            
            return {
                "success": True,
                "repo_path": str(repo_path),
                "branch": branch_name,
                "modified_files": result['modified_files'],
                "commit_hash": commit_hash,
                "plan": result['plan'],
                "todo_driven": True,
                "test_results": test_results,
                "message": "TODO-driven workflow completed",
                "report_path": str(report_path) if report_path else None
            }
            
        except Exception as e:
            logger.error(f"TODO workflow failed: {e}")
            
            # Generate failure report
            report_path = None
            if hasattr(simplified, 'generate_final_report'):
                try:
                    report_path = simplified.generate_final_report(
                        repo_path=str(repo_path) if 'repo_path' in locals() else "",
                        branch=branch_name or "unknown",
                        modified_files=[],
                        commit_hash="failed",
                        success=False,
                        commit_message="Execution failed",
                        file_diffs={},
                        branch_info={}
                    )
                except Exception as report_error:
                    logger.warning(f"Failed to generate error report: {report_error}")
            
            return {
                "success": False, 
                "error": str(e),
                "report_path": str(report_path) if report_path else None
            }
