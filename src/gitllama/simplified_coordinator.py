"""
Simplified AI Coordinator for TODO-driven development
"""

import logging
from pathlib import Path
from typing import Dict, List
from .ollama_client import OllamaClient
from .todo_analyzer import TodoAnalyzer
from .todo_planner import TodoPlanner
from .todo_executor import TodoExecutor

logger = logging.getLogger(__name__)


class SimplifiedCoordinator:
    """Coordinates the simplified TODO-driven workflow"""
    
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.client = OllamaClient(base_url)
        self.analyzer = TodoAnalyzer(self.client, model)
        self.planner = TodoPlanner(self.client, model)
        self.executor = TodoExecutor(self.client, model)
        
        logger.info(f"Initialized Simplified TODO-driven Coordinator with model: {model}")
    
    def run_todo_workflow(self, repo_path: Path) -> Dict:
        """Run the complete simplified workflow"""
        logger.info("=" * 60)
        logger.info("STARTING SIMPLIFIED TODO-DRIVEN WORKFLOW")
        logger.info("=" * 60)
        
        # Phase 1: Analyze repository with TODO focus
        logger.info("\n📝 PHASE 1: TODO-DRIVEN ANALYSIS")
        analysis = self.analyzer.analyze_with_todo(repo_path)
        logger.info(f"Analysis complete: {analysis['total_chunks']} chunks analyzed")
        
        # Phase 2: Create action plan
        logger.info("\n📋 PHASE 2: ACTION PLANNING")
        action_plan = self.planner.create_action_plan(analysis)
        logger.info(f"Plan created: {len(action_plan['files_to_modify'])} files to modify")
        logger.info(f"Branch: {action_plan['branch_name']}")
        
        # Phase 3: Execute plan
        logger.info("\n🚀 PHASE 3: EXECUTION")
        modified_files = self.executor.execute_plan(repo_path, action_plan)
        logger.info(f"Execution complete: {len(modified_files)} files modified")
        
        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "branch_name": action_plan['branch_name'],
            "modified_files": modified_files,
            "plan": action_plan['plan'],
            "analysis_summary": analysis['summary'],
            "todo_found": bool(analysis['todo_content'])
        }