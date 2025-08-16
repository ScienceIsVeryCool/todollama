"""
Simple tests for GitLlama.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess

from gitllama.git_operations import GitAutomator, GitOperationError


class TestGitAutomator:
    """Basic tests for GitAutomator."""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.automator = GitAutomator(working_dir=str(self.temp_dir))
    
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Test successful git command."""
        mock_result = Mock()
        mock_result.stdout = "success"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.automator._run_git_command(['git', 'status'])
        assert result == "success"
    
    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Test git command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'status'], stderr="error"
        )
        
        with pytest.raises(GitOperationError):
            self.automator._run_git_command(['git', 'status'])
    
    def test_make_changes(self):
        """Test making changes."""
        self.automator.repo_path = self.temp_dir / "repo"
        self.automator.repo_path.mkdir()
        
        modified_files = self.automator.make_changes()
        
        assert "gitllama_was_here.txt" in modified_files
        created_file = self.automator.repo_path / "gitllama_was_here.txt"
        assert created_file.exists()
    
    def test_make_changes_without_repo(self):
        """Test making changes without repository."""
        with pytest.raises(GitOperationError):
            self.automator.make_changes()


if __name__ == "__main__":
    pytest.main([__file__])