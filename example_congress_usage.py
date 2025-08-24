#!/usr/bin/env python3
"""
Example usage of the Congress voting system in GitLlama

This example shows how to:
1. Initialize the Congress system
2. Get AI responses with Congressional oversight
3. Control Congressional voting on/off
4. Access voting summaries and decisions
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gitllama.ai.client import OllamaClient
from gitllama.ai.query import AIQuery


def main():
    print("🏛️ Congress Voting System Example")
    print("=" * 50)
    
    # Initialize client and AI query system
    client = OllamaClient()
    if not client.is_available():
        print("❌ Ollama not available. Please start Ollama first.")
        return
    
    # Create AI query instance (Congress is enabled by default)
    ai = AIQuery(client, model="gemma3:4b")
    
    print("✅ AI Query initialized with Congressional oversight")
    
    # Show the three Representatives
    print("\n🎭 Congressional Representatives:")
    for rep in ai.congress.REPRESENTATIVES:
        print(f"  • {rep.name} ({rep.title})")
        print(f"    Style: {rep.voting_style}")
    
    # Example 1: Choice query with Congressional oversight
    print("\n" + "─" * 50)
    print("📊 Example 1: Multiple Choice with Congress")
    print("─" * 50)
    
    result = ai.choice(
        question="What's the best way to handle technical debt?",
        options=[
            "Ignore it and focus on new features",
            "Schedule regular refactoring sprints",
            "Rewrite everything from scratch",
            "Document it and hope someone else fixes it"
        ],
        context="This is for a production codebase with tight deadlines",
        context_name="tech_debt_decision"
    )
    
    print(f"AI Choice: {result.value}")
    
    if result.congress_decision:
        print(f"\nCongress Vote: {result.congress_decision.vote_count[0]}-{result.congress_decision.vote_count[1]}")
        print(f"Decision: {'APPROVED' if result.congress_decision.approved else 'REJECTED'}")
        
        # Show individual votes
        for vote in result.congress_decision.votes:
            status = "✅" if vote.vote else "❌"
            print(f"  {status} {vote.representative.name}: {vote.reasoning}")
    
    # Example 2: Open query
    print("\n" + "─" * 50)
    print("💡 Example 2: Open Response with Congress")
    print("─" * 50)
    
    result = ai.open(
        prompt="Explain the single responsibility principle in software design",
        context_name="srp_explanation"
    )
    
    print(f"AI Response: {result.content[:150]}...")
    
    if result.congress_decision:
        print(f"\nCongress Vote: {result.congress_decision.vote_count[0]}-{result.congress_decision.vote_count[1]}")
        print(f"Decision: {'APPROVED' if result.congress_decision.approved else 'REJECTED'}")
    
    # Example 3: Another choice test
    print("\n" + "─" * 50)
    print("🎯 Example 3: Another Congressional Evaluation")
    print("─" * 50)
    
    result = ai.choice(
        question="Should we use tabs or spaces?",
        options=["Tabs", "Spaces", "Both mixed together", "No indentation"],
        context_name="tabs_vs_spaces"
    )
    
    print(f"AI Choice: {result.value}")
    if result.congress_decision:
        print(f"Congress Vote: {result.congress_decision.vote_count[0]}-{result.congress_decision.vote_count[1]}")
        print(f"Decision: {'APPROVED' if result.congress_decision.approved else 'REJECTED'}")
    
    # Show voting summary
    print("\n" + "─" * 50)
    print("📋 Congressional Voting Summary")
    print("─" * 50)
    
    summary = ai.get_congress_summary()
    print(f"Total Decisions: {summary['total_votes']}")
    print(f"Approved: {summary['approved']}")
    print(f"Rejected: {summary['rejected']}")
    print(f"Unanimity Rate: {summary['unanimity_rate']:.1%}")
    
    if summary['by_representative']:
        print("\n👥 Representative Voting Patterns:")
        for rep_name, votes in summary['by_representative'].items():
            total = votes['yes'] + votes['no']
            approval_rate = (votes['yes'] / total * 100) if total > 0 else 0
            print(f"  {rep_name}: {approval_rate:.0f}% approval rate")
    
    print("\n✅ Congress example complete!")


if __name__ == "__main__":
    main()