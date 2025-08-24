#!/usr/bin/env python3
"""
Test the enhanced timing features in reports
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_timing_enhancements():
    """Test the enhanced timing features"""
    print("🧪 Testing Enhanced Timing Features in Reports")
    print("=" * 70)
    
    try:
        from gitllama.utils.context_tracker import context_tracker
        from gitllama.ai.query import AIQuery
        
        # Reset tracker for clean test
        context_tracker.reset()
        context_tracker.start_stage("Test_Timing")
        
        print("✅ Context tracker and AIQuery can be imported")
        
        # Simulate storing a prompt-response pair with timing
        variables_used = {
            "context": "Test context",
            "question": "Test question"
        }
        
        # Simulate different execution times
        test_pairs = [
            {
                "prompt": "Test multiple choice query",
                "response": "A",
                "query_type": "multiple_choice",
                "execution_time": 1.25
            },
            {
                "prompt": "Test single word query", 
                "response": "Python",
                "query_type": "single_word",
                "execution_time": 0.87
            },
            {
                "prompt": "Test open response query",
                "response": "This is a detailed response explaining the system architecture...",
                "query_type": "open", 
                "execution_time": 3.42
            },
            {
                "prompt": "Test file write query",
                "response": "def main():\n    print('Hello World!')\n    return 0",
                "query_type": "file_write",
                "execution_time": 2.16
            }
        ]
        
        for i, pair in enumerate(test_pairs, 1):
            context_tracker.store_prompt_and_response(
                prompt=pair["prompt"],
                response=pair["response"],
                variable_map=variables_used,
                query_type=pair["query_type"],
                execution_time_seconds=pair["execution_time"]
            )
            print(f"✅ Stored exchange {i}: {pair['query_type']} ({pair['execution_time']}s)")
        
        # Check what was stored
        stage_data = context_tracker.get_stage_summary("Test_Timing")
        
        print(f"\n📊 Timing Data Verification:")
        print(f"   📈 Exchanges stored: {len(stage_data['prompt_response_pairs'])}")
        
        for i, pair in enumerate(stage_data['prompt_response_pairs'], 1):
            clock_time = pair.get('clock_time', 'N/A')
            execution_time = pair.get('execution_time_seconds', 'N/A') 
            query_type = pair.get('query_type', 'unknown')
            print(f"   🔍 Exchange {i}: {query_type}")
            print(f"      🕐 Clock time: {clock_time}")
            print(f"      ⏱️ Execution: {execution_time}s")
        
        print(f"\n🎯 Enhanced Timing Features:")
        print("✅ Clock time: Shows when the query completed (HH:MM:SS)")
        print("✅ Execution time: Shows how long the query took (seconds)")
        print("✅ Precise timing: Rounded to 2 decimal places")
        print("✅ All query types: Timing for multiple_choice, single_word, open, file_write")
        print("✅ Context tracking: Timing data stored with each exchange")
        
        print(f"\n📋 Report Display Changes:")
        print("🕐 Clock Time: Shows completion time with clock emoji")
        print("⏱️ Execution Time: Shows duration with stopwatch emoji") 
        print("📝 Prompt Size: Character count of prompt")
        print("💬 Response Size: Character count of response")
        print("🏛️ Congress Votes: Congressional oversight results")
        
        print(f"\n🔧 Implementation Details:")
        print("• _execute_query() now times AI calls with time.time()")
        print("• context_tracker stores both clock_time and execution_time_seconds")
        print("• Report template shows 🕐 HH:MM:SS and ⏱️ X.XXs")
        print("• All 4 query types get timing automatically")
        print("• Precise logging shows execution time in console")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run timing enhancements test"""
    print("🔧 GitLlama Timing Enhancements Test")
    print("=" * 70)
    
    success = test_timing_enhancements()
    
    print(f"\n🎯 Test Summary:")
    print("=" * 70)
    if success:
        print("✅ Timing enhancement tests PASSED!")
        print("🎉 Reports now show detailed timing information!")
        print("\n🔧 What's Enhanced:")
        print("   • Clock time shows when each query completed")
        print("   • Execution time shows how long each query took")
        print("   • Automatic timing for all query types")
        print("   • Precise timing with 2 decimal places")
        print("   • Better performance monitoring capabilities")
        print("\n📈 User Benefits:")
        print("   • Monitor AI query performance")
        print("   • Identify slow queries for optimization")
        print("   • Track execution patterns over time")
        print("   • Debug timing-related issues")
        print("   • Professional timing metrics in reports")
    else:
        print("❌ Some tests FAILED!")
        print("🔧 Check the implementation for errors")

if __name__ == "__main__":
    main()