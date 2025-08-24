"""
Simplified AI Coordinator for TODO-driven development
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from ..ai import OllamaClient
from ..todo import TodoAnalyzer, TodoPlanner, TodoExecutor

logger = logging.getLogger(__name__)


class SimplifiedCoordinator:
    """Coordinates the simplified TODO-driven workflow"""
    
    def __init__(self, model: str = "gemma3:4b", base_url: str = "http://localhost:11434", git_url: Optional[str] = None):
        self.model = model
        self.client = OllamaClient(base_url)
        self.analyzer = TodoAnalyzer(self.client, model)
        self.planner = TodoPlanner(self.client, model)
        self.executor = TodoExecutor(self.client, model)
        
        # Initialize report generator if git_url provided
        self.report_generator = None
        if git_url:
            try:
                from ..utils.reports import ReportGenerator
                self.report_generator = ReportGenerator(git_url)
                logger.info("Report generator initialized")
            except ImportError as e:
                logger.warning(f"Report generation dependencies not available: {e}")
        
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
        modified_files, file_diffs = self.executor.execute_plan(repo_path, action_plan)
        logger.info(f"Execution complete: {len(modified_files)} files modified")
        
        logger.info("=" * 60)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "branch_name": action_plan['branch_name'],
            "modified_files": modified_files,
            "file_diffs": file_diffs,
            "plan": action_plan['plan'],
            "analysis_summary": analysis['summary'],
            "todo_found": bool(analysis['todo_content'])
        }
    
    def generate_final_report(self, repo_path: str, branch: str, modified_files: List[str], 
                             commit_hash: str, success: bool, commit_message: str = "",
                             file_diffs: Dict = None, branch_info: Dict = None) -> Optional[Path]:
        """Generate the final HTML report if report generator is available.
        
        Args:
            repo_path: Path to the repository
            branch: Selected branch name
            modified_files: List of modified file paths
            commit_hash: Git commit hash
            success: Whether the workflow was successful
            commit_message: The exact commit message used
            file_diffs: Dictionary of file paths to their before/after content
            branch_info: Additional branch information
            
        Returns:
            Path to generated report or None if no report generator
        """
        if not self.report_generator:
            return None
        
        logger.info("Generating final HTML report...")
        
        # Set executive summary for simplified workflow
        # Get metrics from context manager
        from ..utils.metrics import context_manager
        metrics = context_manager.get_summary()
        total_decisions = metrics['total_calls']
        
        self.report_generator.set_executive_summary(
            repo_path=repo_path,
            branch=branch,
            modified_files=modified_files,
            commit_hash=commit_hash,
            success=success,
            total_decisions=total_decisions,
            commit_message=commit_message,
            file_diffs=file_diffs,
            branch_info=branch_info
        )
        
        # Set model information
        context_size = self.client.get_model_context_size(self.model)
        # Estimate tokens from operation count (rough estimate)
        estimated_tokens = total_decisions * 1000  # Rough estimate
        
        self.report_generator.set_model_info(
            model=self.model,
            context_window=context_size,
            total_tokens=estimated_tokens
        )
        
        # Add TODO-specific information to report
        if hasattr(self.report_generator, 'add_section'):
            self.report_generator.add_section(
                "TODO Analysis",
                "Simplified TODO-driven workflow was used to analyze the repository against TODO.md file."
            )
        
        # Generate and return the report
        report_path = self.report_generator.generate_report()
        logger.info(f"Report generated: {report_path}")
        return report_path