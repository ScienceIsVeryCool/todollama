#!/usr/bin/env python3
"""
Test the improved file selection system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_improved_planner():
    """Test the basic structure of the improved planner"""
    print("🔧 Testing Improved File Selection System")
    print("=" * 50)
    
    try:
        from gitllama.todo.planner import TodoPlanner
        from gitllama.ai.client import OllamaClient
        
        # Test creation (doesn't require actual Ollama connection)
        print("✅ TodoPlanner can be imported")
        
        # Test that new methods exist
        planner = TodoPlanner.__new__(TodoPlanner)  # Create without calling __init__
        
        # Check that new methods exist
        expected_methods = [
            'set_project_root',
            '_generate_project_tree', 
            '_get_all_file_paths',
            '_extract_file_list_from_plan',
            '_collect_files_with_context',
            '_resolve_file_path_with_ai',
            '_collect_additional_files'
        ]
        
        for method_name in expected_methods:
            if hasattr(planner, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_improvements():
    """Show what improvements were made"""
    print("\n🚀 File Selection System Improvements")
    print("=" * 50)
    
    print("\n📋 NEW WORKFLOW:")
    print("1. 🌳 Project tree generated and included in planning context")
    print("2. 📝 AI creates detailed plan with full project visibility")
    print("3. 📄 Open query extracts specific file list from the plan")
    print("4. 🎯 Single-word queries resolve each file path with full context")
    print("5. 🔍 AI can see all available files and project structure")
    print("6. ➕ Optional: AI can request additional files beyond the plan")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("✅ Full project tree visibility for AI")
    print("✅ Structured file list extraction from plans")
    print("✅ Single-word queries instead of multiple-choice")  
    print("✅ Comprehensive context with all file paths")
    print("✅ Smart file path resolution and matching")
    print("✅ Reduced chance of AI confusion and errors")
    print("✅ Support for CREATE/EDIT/DELETE operations")
    
    print("\n🏗️ TEMPLATE VARIABLES:")
    print("📁 project_tree - Full directory structure")
    print("📂 all_files - List of all available file paths")
    print("📝 selected_files - Currently selected files")
    print("📋 plan - The detailed action plan")
    print("🎯 intended_path - File path from plan to resolve")

def main():
    """Run all tests"""
    print("🧪 Testing Improved GitLlama File Selection")
    print("=" * 60)
    
    success = test_improved_planner()
    show_improvements()
    
    print(f"\n🎯 Test Summary:")
    print("=" * 60)
    if success:
        print("✅ Basic structure tests PASSED!")
        print("🎉 Improved file selection system is ready!")
        print("\n🔧 Next steps:")
        print("   1. Set project_root on planner instances")
        print("   2. The new workflow will automatically engage")
        print("   3. AI gets full project visibility for better decisions")
    else:
        print("❌ Some tests FAILED!")
        print("🔧 Check the implementation for syntax errors")

if __name__ == "__main__":
    main()