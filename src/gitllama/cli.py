"""
GitLlama CLI Module with AI Integration

AI-powered command-line interface for git automation.
"""

import argparse
import logging
import sys

from .git_operations import GitAutomator, GitOperationError
from .ollama_client import OllamaClient
from .context_manager import context_manager


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="GitLlama - AI-powered git automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitllama https://github.com/user/repo.git
  gitllama https://github.com/user/repo.git --branch my-feature  
  gitllama https://github.com/user/repo.git --model llama3:8b
  gitllama https://github.com/user/repo.git --verbose

GitLlama uses AI to intelligently analyze repositories and make improvements.
All decisions (commits, files, messages) are handled by AI.
Requires Ollama to be running with a compatible model.
        """
    )
    
    parser.add_argument(
        "git_url",
        help="Git repository URL to clone and modify"
    )
    
    parser.add_argument(
        "--branch", "-b",
        default=None,
        help="Branch name to use (AI will decide if not specified)"
    )
    
    
    parser.add_argument(
        "--model",
        default="gemma3:4b",
        help="Ollama model to use for AI decisions (default: gemma3:4b)"
    )
    
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)"
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
        # Test Ollama connection
        print(f"🤖 Initializing GitLlama with AI model: {args.model}")
        client = OllamaClient(args.ollama_url)
        
        if not client.is_available():
            print("⚠️  Warning: Ollama server not available.")
            print("   GitLlama requires Ollama for AI features. Please ensure Ollama is running:")
            print("   Install: https://ollama.ai")
            print("   Start: ollama serve")
            print("   Pull model: ollama pull gemma3:4b")
            return 1
        
        # Run the TODO-driven workflow
        print("🚀 Running TODO-driven workflow...")
        with GitAutomator() as automator:
            results = automator.run_full_workflow(
                git_url=args.git_url,
                branch_name=args.branch,
                model=args.model,
                base_url=args.ollama_url
            )
        
        # Print results
        if results["success"]:
            print("✓ GitLlama workflow completed successfully!")
            print(f"  Repository: {results['repo_path']}")
            print(f"  Branch: {results['branch']}")
            print(f"  Modified files: {', '.join(results['modified_files'])}")
            print(f"  Commit: {results['commit_hash']}")
            
            # TODO-driven workflow info
            if results.get('todo_driven'):
                print(f"\n🎯 TODO-Driven Analysis Complete")
                if 'plan' in results:
                    plan_lines = results['plan'].split('\n')[:3]  # Show first 3 lines
                    print(f"  Plan: {' '.join(plan_lines)[:100]}...")  # Truncate
            
            # Show report path if available
            if results.get('report_path'):
                print(f"\n📊 Report Generated: {results['report_path']}")
                print("   Open in browser to view detailed AI decision log and analysis")
            
            # Display context window summary at end of runtime
            print(f"\n🧠 Context Window Summary:")
            print("=" * 50)
            print(context_manager.get_context_list_for_runtime_display())
            
            return 0
        else:
            print(f"✗ Workflow failed: {results['error']}")
            # Show failure report if available
            if results.get('report_path'):
                print(f"📊 Error Report Generated: {results['report_path']}")
                print("   Open in browser to view error details and partial analysis")
            
            # Display context window summary even on failure
            print(f"\n🧠 Context Window Summary (Partial):")
            print("=" * 50)
            print(context_manager.get_context_list_for_runtime_display())
            
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