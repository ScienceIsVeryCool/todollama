"""
GitLlama CLI Module

Simple command-line interface for git automation.
"""

import argparse
import logging
import sys

from .git_operations import GitAutomator, GitOperationError


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="GitLlama - Simple git automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitllama https://github.com/user/repo.git
  gitllama https://github.com/user/repo.git --branch my-feature
  gitllama https://github.com/user/repo.git --message "Custom commit message"
        """
    )
    
    parser.add_argument(
        "git_url",
        help="Git repository URL to clone and modify"
    )
    
    parser.add_argument(
        "--branch", "-b",
        default="gitllama-automation",
        help="Branch name to create (default: gitllama-automation)"
    )
    
    parser.add_argument(
        "--message", "-m",
        help="Custom commit message"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main() -> int:
    """Main entry point for GitLlama CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s"
    )
    
    try:
        # Run the workflow
        with GitAutomator() as automator:
            results = automator.run_full_workflow(
                git_url=args.git_url,
                branch_name=args.branch,
                commit_message=args.message
            )
        
        # Print results
        if results["success"]:
            print("✓ GitLlama workflow completed successfully!")
            print(f"  Repository: {results['repo_path']}")
            print(f"  Branch: {results['branch']}")
            print(f"  Modified files: {', '.join(results['modified_files'])}")
            print(f"  Commit: {results['commit_hash']}")
            return 0
        else:
            print(f"✗ Workflow failed: {results['error']}")
            return 1
            
    except GitOperationError as e:
        print(f"✗ Git operation failed: {e}")
        return 1
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())