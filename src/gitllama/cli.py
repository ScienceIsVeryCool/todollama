"""
GitLlama CLI Module with AI Integration

AI-powered command-line interface for git automation.
"""

import argparse
import logging
import sys

from . import __version__
from .core import GitAutomator, GitOperationError
from .ai import OllamaClient
from .utils.metrics import context_manager


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description=f"GitLlama v{__version__} - AI-powered git automation",
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
        "--version", "-V",
        action="version",
        version=f"GitLlama {__version__}",
        help="Show version and exit"
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
        # Log version information
        logging.info(f"🦙 GitLlama v{__version__} starting...")
        
        # Test Ollama connection
        print(f"🤖 Initializing GitLlama v{__version__} with AI model: {args.model}")
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
            
            # Test results info
            test_results = results.get('test_results', {})
            if test_results.get('test_executed'):
                test_status = "✅ PASSED" if test_results.get('test_passed') else "❌ FAILED"
                print(f"\n🧪 Tests: {test_status} (exit code: {test_results.get('test_exit_code', 'unknown')})")
                
                ai_eval = test_results.get('ai_evaluation', {})
                if ai_eval.get('success'):
                    print(f"  AI Assessment: ✅ Implementation successful")
                elif ai_eval.get('partial_success'):
                    print(f"  AI Assessment: ⚠️ Partially successful")
                else:
                    print(f"  AI Assessment: ❌ Implementation issues detected")
            
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
            
            # Display AI operations summary at end of runtime
            print(f"\n🧠 AI Operations Summary:")
            print("=" * 50)
            print(context_manager.get_display_summary())
            
            return 0
        else:
            print(f"✗ Workflow failed: {results['error']}")
            
            # Special handling for test failure aborts
            if results.get('commit_aborted'):
                print("🚫 COMMIT ABORTED: Tests failed with non-zero exit code")
                print("   Implementation was not committed due to test failure")
                test_results = results.get('test_results', {})
                if test_results.get('test_exit_code'):
                    print(f"   Test exit code: {test_results['test_exit_code']}")
            
            # Show failure report if available
            if results.get('report_path'):
                print(f"📊 Error Report Generated: {results['report_path']}")
                print("   Open in browser to view error details and partial analysis")
            
            # Display context window summary even on failure
            print(f"\n🧠 AI Operations Summary (Partial):")
            print("=" * 50)
            print(context_manager.get_display_summary())
            
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