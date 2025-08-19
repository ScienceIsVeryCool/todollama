"""
Branch Analyzer updates - showing key method changes
"""

from .ai_query import AIQuery

class BranchAnalyzer:
    """Analyzes git branches and makes intelligent branch selection decisions"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b", report_generator=None):
        self.client = client
        self.model = model
        self.ai = AIQuery(client, model)  # NEW: Use simple query interface
        self.report_generator = report_generator
        
    def _step3_make_branch_decision(self, current_branch: str, 
                                   reuse_candidates: List[Dict], 
                                   project_info: Dict) -> Dict:
        """STEP 3: Decide whether to reuse or create new branch."""
        logger.info(f"  Making branch selection decision")
        
        # Prepare context
        context = f"Current branch: {current_branch}\n"
        context += f"Project type: {project_info.get('project_type', 'unknown')}\n"
        
        if reuse_candidates:
            context += f"Found {len(reuse_candidates)} reusable branches"
        
        # Simple choice: reuse or create?
        if reuse_candidates and reuse_candidates[0]['score'] >= 30:
            # We have good candidates
            action_result = self.ai.choice(
                question="Should we reuse an existing branch or create new?",
                options=["REUSE existing branch", "CREATE new branch"],
                context=context
            )
            
            if "REUSE" in action_result.value:
                # Pick which branch
                branch_options = [c['branch_name'] for c in reuse_candidates[:5]]
                branch_result = self.ai.choice(
                    question="Which branch should we reuse?",
                    options=branch_options,
                    context=f"Top candidates with scores: {[(c['branch_name'], c['score']) for c in reuse_candidates[:5]]}"
                )
                
                return {
                    'decision': 'REUSE',
                    'selected_branch': branch_result.value,
                    'reasoning': f"Reusing existing branch with score {reuse_candidates[0]['score']}"
                }
        
        # Create new branch
        type_result = self.ai.choice(
            question="What type of new branch should we create?",
            options=["feature", "fix", "docs", "chore"],
            context=context
        )
        
        return {
            'decision': 'CREATE',
            'new_branch_type': type_result.value,
            'reasoning': f"Creating new {type_result.value} branch"
        }