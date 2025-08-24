#!/usr/bin/env python3
"""
Example of how to customize congress representatives with different models
for more concrete personas
"""

# This is an example of how you can modify the REPRESENTATIVES list in congress.py
# to create more concrete personas with different AI models

EXAMPLE_CUSTOM_REPRESENTATIVES = [
    {
        "name": "Senator Prudence",
        "title": "The Conservative Security Expert",
        "personality": "Ex-cybersecurity professional. Extremely cautious about code safety and security vulnerabilities.",
        "voting_style": "conservative",
        "model": "llama3:8b",  # Use Llama for detailed security analysis
        "specialty": "Security & Safety"
    },
    {
        "name": "Representative Innovation",
        "title": "The Startup CTO",
        "personality": "Former Silicon Valley CTO. Loves cutting-edge solutions and rapid prototyping.",
        "voting_style": "progressive", 
        "model": "qwen2.5:7b",  # Use Qwen for innovative approaches
        "specialty": "Innovation & Efficiency"
    },
    {
        "name": "Justice Balance",
        "title": "The Senior Architect",
        "personality": "20 years experience in enterprise software. Balances innovation with maintainability.",
        "voting_style": "balanced",
        "model": "gemma3:4b",  # Use Gemma for balanced architectural decisions
        "specialty": "Architecture & Maintainability"
    }
]

def print_example_usage():
    """Show how to use individual models for concrete personas"""
    print("🎭 Example: Custom Congress with Concrete Personas")
    print("=" * 60)
    print()
    
    print("💡 How to customize congress for specific use cases:")
    print()
    
    for i, rep in enumerate(EXAMPLE_CUSTOM_REPRESENTATIVES, 1):
        print(f"   {i}. {rep['name']} - {rep['title']}")
        print(f"      🧠 Model: {rep['model']}")
        print(f"      🎯 Specialty: {rep['specialty']}")
        print(f"      📝 Persona: {rep['personality']}")
        print()
    
    print("🔧 Benefits of Individual Models:")
    print("   • Each representative uses AI optimized for their role")
    print("   • Conservative rep uses Llama (great for security analysis)")
    print("   • Progressive rep uses Qwen (excellent for innovation)")
    print("   • Balanced rep uses Gemma (solid for architectural decisions)")
    print()
    
    print("📝 To implement these personas:")
    print("   1. Edit src/gitllama/ai/congress.py")
    print("   2. Update the REPRESENTATIVES list with your desired models")
    print("   3. Each Representative() can have a different model field")
    print("   4. The congress system will use each model individually")
    print()
    
    print("🎯 Example use cases:")
    print("   • Code Review: Security-focused, Innovation-minded, Architecture-balanced")
    print("   • Bug Fixing: Conservative safety checks, Progressive solutions, Balanced approaches")
    print("   • Feature Planning: Risk assessment, Innovation potential, Maintainability impact")
    print("   • Architecture Decisions: Security implications, Modern approaches, Enterprise stability")

if __name__ == "__main__":
    print_example_usage()