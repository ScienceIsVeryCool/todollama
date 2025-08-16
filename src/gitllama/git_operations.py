"""
GitLlama - Git Operations Module

Simple git automation: clone, branch, change, commit, push.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GitOperationError(Exception):
    """Custom exception for git operation errors."""
    pass


class GitAutomator:
    """Simple git automation class."""
    
    def __init__(self, working_dir: Optional[str] = None):
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
    
    def _run_git_command(self, command: list, cwd: Optional[Path] = None) -> str:
        """Execute a git command and return the output."""
        work_dir = cwd or self.repo_path or self.working_dir
        
        try:
            logger.info(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(command)}\nError: {e.stderr}"
            logger.error(error_msg)
            raise GitOperationError(error_msg) from e
    
    def clone_repository(self, git_url: str) -> Path:
        """Clone a git repository."""
        logger.info(f"Cloning repository: {git_url}")
        
        # Extract repository name from URL
        repo_name = git_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        self.repo_path = self.working_dir / repo_name
        
        self._run_git_command(['git', 'clone', git_url, str(self.repo_path)], cwd=self.working_dir)
        logger.info(f"Successfully cloned to {self.repo_path}")
        return self.repo_path
    
    def checkout_branch(self, branch_name: str) -> str:
        """Create and checkout a new branch."""
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info(f"Creating and checking out branch: {branch_name}")
        self._run_git_command(['git', 'checkout', '-b', branch_name])
        logger.info(f"Successfully checked out branch: {branch_name}")
        return branch_name
    
    def make_changes(self) -> list:
        """
        Make a simple change to the repository.
        
        TODO: Expand this method to add your custom change logic.
        """
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("Making changes to repository")
        
        # Simple default change - create a file
        filename = "gitllama_was_here.txt"
        content = "This file was created by GitLlama automation tool."
        
        file_path = self.repo_path / filename
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Created file: {filename}")
        return [filename]
    
    def commit_changes(self, message: Optional[str] = None) -> str:
        """Commit changes to the repository."""
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("Committing changes")
        
        # Add all changes
        self._run_git_command(['git', 'add', '.'])
        
        # Create commit message
        if not message:
            message = "Automated changes by GitLlama"
        
        # Commit changes
        self._run_git_command(['git', 'commit', '-m', message])
        
        # Get commit hash
        commit_hash = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        logger.info(f"Successfully committed: {commit_hash[:8]}")
        
        return commit_hash
    
    def push_changes(self, branch: Optional[str] = None) -> str:
        """Push changes to the remote repository."""
        if not self.repo_path:
            raise GitOperationError("No repository cloned. Call clone_repository first.")
        
        logger.info("Pushing changes")
        
        # Get current branch if not specified
        if not branch:
            branch = self._run_git_command(['git', 'branch', '--show-current'])
        
        # Push changes
        push_output = self._run_git_command(['git', 'push', 'origin', branch])
        logger.info("Successfully pushed changes")
        
        return push_output
    
    def run_full_workflow(self, git_url: str, branch_name: str = "gitllama-automation", 
                         commit_message: Optional[str] = None) -> dict:
        """Run the complete git automation workflow."""
        logger.info("Starting GitLlama workflow")
        
        try:
            # Step 1: Clone repository
            repo_path = self.clone_repository(git_url)
            
            # Step 2: Checkout branch
            self.checkout_branch(branch_name)
            
            # Step 3: Make changes
            modified_files = self.make_changes()
            
            # Step 4: Commit changes
            commit_hash = self.commit_changes(commit_message)
            
            # Step 5: Push changes
            push_output = self.push_changes(branch=branch_name)
            
            logger.info("Workflow completed successfully")
            
            return {
                "success": True,
                "repo_path": str(repo_path),
                "branch": branch_name,
                "modified_files": modified_files,
                "commit_hash": commit_hash[:8],
                "message": "Workflow completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }