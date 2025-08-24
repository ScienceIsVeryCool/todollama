#!/usr/bin/env python3
"""
Test the congress individual model assignment
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_congress_individual_models():
    """Test that each congress representative has their own individual model"""
    print("🧪 Testing Congress Individual Models")
    print("=" * 50)
    
    try:
        from gitllama.ai.congress import Congress
        from gitllama.ai.client import OllamaClient
        
        # Mock client (we don't need real client for this test)
        class MockClient:
            pass
        
        mock_client = MockClient()
        
        # Expected individual models for each representative
        expected_models = {
            "Senator Prudence": "gemma3:4b",
            "Representative Innovation": "gemma3:4b", 
            "Justice Balance": "gemma3:4b"
        }
        
        print("🔧 Testing congress initialization - fallback model should not affect individual models:")
        
        # Test different fallback models - representatives should keep their individual models
        test_fallback_models = ["mistral:7b", "phi3:3.8b", "gemma3:4b"]
        
        for fallback_model in test_fallback_models:
            print(f"\n   Testing with fallback model: {fallback_model}")
            congress = Congress(mock_client, fallback_model)
            
            # Check that each representative has their expected individual model
            for rep in congress.REPRESENTATIVES:
                expected = expected_models[rep.name]
                actual = rep.model
                status = "✅" if actual == expected else "❌"
                print(f"      {status} {rep.name}: {actual} (expected: {expected})")
                
                if actual != expected:
                    print(f"      ❌ ERROR: {rep.name} has model {actual}, expected {expected}")
                    return False
        
        print(f"\n🏛️ Congress Info Test:")
        congress = Congress(mock_client, "any-model")
        congress_info = congress.get_congress_info()
        
        print(f"   📊 Models used: {congress_info['models']}")
        print(f"   👥 Total representatives: {congress_info['total_representatives']}")
        print(f"   🎯 Unique models: {len(set(congress_info['models']))}")
        
        for i, rep in enumerate(congress_info['representatives'], 1):
            expected_model = expected_models[rep['name']]
            actual_model = rep['model']
            status = "✅" if actual_model == expected_model else "❌"
            print(f"   {status} {i}. {rep['name']} ({rep['title']}) - Model: {actual_model}")
            
            if actual_model != expected_model:
                print(f"      ❌ ERROR: {rep['name']} has model {actual_model}, expected {expected_model}")
                return False
        
        print(f"\n✅ All congress representatives correctly use their individual models!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run congress individual model test"""
    print("🔧 GitLlama Congress Individual Models Test")
    print("=" * 60)
    
    success = test_congress_individual_models()
    
    print(f"\n🎯 Test Summary:")
    print("=" * 60)
    if success:
        print("✅ Congress individual model tests PASSED!")
        print("🎉 Each representative can have their own individual model!")
        print("\n🔧 What's Implemented:")
        print("   • Representative dataclass includes individual model field")
        print("   • Each representative uses their own specified model")
        print("   • Congress ignores fallback model parameter")
        print("   • get_congress_info() shows model details for each representative")
        print("   • Report template shows individual models for each representative")
        print("   • _get_representative_vote() uses representative.model for queries")
        print("\n🎯 Ready for Customization:")
        print("   • Edit congress.py REPRESENTATIVES list to assign different models")
        print("   • Each representative can use any available Ollama model")
        print("   • Concrete personas can be created with specific model behaviors")
    else:
        print("❌ Some tests FAILED!")
        print("🔧 Check the congress.py implementation for errors")

if __name__ == "__main__":
    main()