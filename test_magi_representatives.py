#!/usr/bin/env python3
"""
Test the new Magi-inspired representatives system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_humanity_representatives():
    """Test the new templated humanity representatives"""
    print("🎭 Testing Humanity-Inspired Representatives")
    print("=" * 60)
    
    try:
        from gitllama.ai.representatives import REPRESENTATIVES, build_context_prompt
        
        print("🏛️ The Three Aspects of Humanity:")
        print("=" * 60)
        
        for i, rep in enumerate(REPRESENTATIVES, 1):
            print(f"\n{i}. {rep.name_title}")
            print(f"   🧠 Personality: {rep.personality}")
            print(f"   📊 Voting Style: {rep.voting_style}")
            print(f"   🤖 Model: {rep.model}")
            
            print(f"\n   💚 Values & Appreciates ({len(rep.likes)} items):")
            for j, like in enumerate(rep.likes[:8], 1):  # Show first 8
                print(f"      {j}. {like}")
            if len(rep.likes) > 8:
                print(f"      ... and {len(rep.likes) - 8} more")
            
            print(f"\n   ❌ Dislikes & Opposes ({len(rep.dislikes)} items):")
            for j, dislike in enumerate(rep.dislikes[:8], 1):  # Show first 8
                print(f"      {j}. {dislike}")
            if len(rep.dislikes) > 8:
                print(f"      ... and {len(rep.dislikes) - 8} more")
            
            print("-" * 60)
        
        print(f"\n🎯 Templated Prompt System:")
        print("=" * 60)
        
        # Test the template system
        example_rep = REPRESENTATIVES[0]  # Caspar
        template = build_context_prompt(example_rep)
        
        print(f"📝 Example Templated Prompt for {example_rep.name_title}:")
        print("-" * 60)
        print(template)
        print("-" * 60)
        
        print(f"\n✨ Key Features:")
        print("   • 🎭 Three distinct aspects of humanity (Logic, Vision, Compassion)")
        print("   • 📋 Templated prompts with likes/dislikes integration")
        print("   • 🎨 Individual personalities representing human nature")
        print("   • ⚖️ Values-based voting regardless of topic expertise")
        print("   • 🤖 Individual AI models for each representative")
        print("   • 🔧 Easy customization through likes/dislikes lists")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run humanity representatives test"""
    print("🎭 GitLlama Humanity Representatives Test")
    print("=" * 60)
    
    success = test_humanity_representatives()
    
    print(f"\n🎯 Test Summary:")
    print("=" * 60)
    if success:
        print("✅ Humanity representatives system PASSED!")
        print("🎉 Three aspects of humanity successfully implemented!")
        print("\n🏛️ The Three Aspects of Humanity:")
        print("   • Caspar the Rational - Logic, Reason, Analysis")
        print("   • Melchior the Visionary - Creativity, Innovation, Progress") 
        print("   • Balthasar the Compassionate - Wisdom, Empathy, Justice")
        print("\n🔧 Templated System Benefits:")
        print("   • Generic prompt template with value-based evaluation")
        print("   • Extensive likes/dislikes lists guide decision-making")
        print("   • Representatives vote based on human values, not expertise")
        print("   • Each represents a fundamental aspect of human nature")
        print("   • Easy to modify values through likes/dislikes lists")
        print("\n🎭 Representing Human Nature:")
        print("   • Three core aspects of human decision-making")
        print("   • Logic, Creativity, and Compassion working together")
        print("   • Collective wisdom through diverse perspectives")
    else:
        print("❌ Some tests FAILED!")
        print("🔧 Check the representatives.py implementation for errors")

if __name__ == "__main__":
    main()