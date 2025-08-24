#!/usr/bin/env python3
"""
Test script for the Congressional voting system
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gitllama.ai.client import OllamaClient
from gitllama.ai.query import AIQuery
from gitllama.ai.congress import Congress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def test_congress_voting():
    """Test the Congressional voting system"""
    print("\n" + "="*60)
    print("🏛️  CONGRESSIONAL VOTING SYSTEM TEST")
    print("="*60 + "\n")
    
    # Initialize client
    client = OllamaClient()
    
    # Check if Ollama is available
    if not client.is_available():
        print("❌ Ollama is not running. Please start Ollama first.")
        print("   Run: ollama serve")
        return
    
    # Initialize AIQuery with Congress enabled
    ai = AIQuery(client, model="gemma3:4b")
    
    print("✅ AI Query system initialized with Congress enabled\n")
    print("Representatives:")
    for rep in Congress.REPRESENTATIVES:
        print(f"  • {rep.name} - {rep.title}")
        print(f"    {rep.personality}\n")
    
    # Test 1: Multiple choice question
    print("\n" + "-"*60)
    print("TEST 1: Multiple Choice Question")
    print("-"*60)
    
    question = "What is the best approach to handle a git merge conflict?"
    options = [
        "Force push to override",
        "Carefully review and resolve conflicts manually",
        "Delete the branch and start over",
        "Accept all incoming changes blindly"
    ]
    
    print(f"Question: {question}")
    print("Options:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    
    print("\n🤖 Getting AI response...")
    result = ai.choice(question, options, context_name="merge_conflict_test")
    
    print(f"\n✨ AI Selected: {result.value}")
    print(f"   Confidence: {result.confidence:.2%}")
    
    if result.congress_decision:
        print("\n" + ai.congress.format_decision_for_display(result.congress_decision))
    
    # Test 2: Open-ended question
    print("\n" + "-"*60)
    print("TEST 2: Open-ended Question")
    print("-"*60)
    
    prompt = "Write a Python function to calculate fibonacci numbers"
    
    print(f"Prompt: {prompt}")
    print("\n🤖 Getting AI response...")
    
    result = ai.open(prompt, context_name="fibonacci_test")
    
    print(f"\n✨ AI Response:")
    print(result.content[:200] + "..." if len(result.content) > 200 else result.content)
    
    if result.congress_decision:
        print("\n" + ai.congress.format_decision_for_display(result.congress_decision))
    
    # Test 3: Generate report to verify Congress display
    print("\n" + "-"*60)
    print("TEST 3: Generating Report")
    print("-"*60)
    
    from gitllama.utils.reports import ReportGenerator
    
    print("📊 Generating HTML report with Congress votes...")
    
    report_gen = ReportGenerator("https://github.com/test/gitllama")
    report_gen.set_executive_summary(
        repo_path="/test/gitllama",
        branch="main",
        modified_files=["test.py"],
        commit_hash="abc123",
        success=True,
        total_decisions=3
    )
    
    # Generate the report
    report_path = report_gen.generate_report(auto_open=False)
    print(f"✅ Report generated: {report_path}")
    print("   Check the report to see Congress votes displayed inline with hover details!")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 CONGRESSIONAL VOTING SUMMARY")
    print("="*60)
    
    summary = ai.get_congress_summary()
    
    print(f"\nTotal Decisions Evaluated: {summary['total_votes']}")
    print(f"Approved: {summary['approved']}")
    print(f"Rejected: {summary['rejected']}")
    print(f"Unanimity Rate: {summary['unanimity_rate']:.1%}")
    
    if summary['by_representative']:
        print("\n📊 Voting Patterns by Representative:")
        for rep_name, votes in summary['by_representative'].items():
            total = votes['yes'] + votes['no']
            yes_pct = (votes['yes'] / total * 100) if total > 0 else 0
            print(f"  {rep_name}:")
            print(f"    ✅ Yes: {votes['yes']} ({yes_pct:.0f}%)")
            print(f"    ❌ No:  {votes['no']} ({100-yes_pct:.0f}%)")
    
    print("\n✅ Congress voting system test complete!")

if __name__ == "__main__":
    test_congress_voting()