"""
Branch Analyzer for GitLlama
Intelligent branch selection and analysis with clear decision logic
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class BranchAnalyzer:
    """Analyzes git branches and makes intelligent branch selection decisions"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        """Initialize the Branch Analyzer.
        
        Args:
            client: OllamaClient instance
            model: Model name to use for analysis
        """
        self.client = client
        self.model = model
        self.branch_analyses = {}  # Store analysis of each branch
        
        logger.info(f"BranchAnalyzer initialized with model: {model}")
    
    def analyze_and_select_branch(self, repo_path: Path, current_branch: str, 
                                 project_info: Dict, branch_summaries: Dict[str, Dict]) -> Tuple[str, str, Dict]:
        """Main entry point for branch analysis and selection.
        
        This method orchestrates the entire branch decision pipeline.
        Each step is clearly separated for easy understanding and extension.
        
        Args:
            repo_path: Path to the repository
            current_branch: Currently checked out branch
            project_info: Project analysis from ProjectAnalyzer
            branch_summaries: Dictionary of branch names to their analysis summaries
            
        Returns:
            Tuple of (selected_branch_name, decision_reason, decision_metadata)
        """
        logger.info(f"Starting intelligent branch selection process")
        logger.info("=" * 60)
        
        # Store the branch analyses
        self.branch_analyses = branch_summaries
        
        # ============================================================
        # STEP 1: ANALYZE EXISTING BRANCHES
        # Understand what each existing branch is for
        # ============================================================
        logger.info("STEP 1: ANALYZE EXISTING BRANCHES")
        branch_purposes = self._step1_analyze_branch_purposes(branch_summaries)
        
        # ============================================================
        # STEP 2: EVALUATE REUSE POTENTIAL
        # Determine if any existing branch is suitable for our work
        # ============================================================
        logger.info("STEP 2: EVALUATE REUSE POTENTIAL")
        reuse_candidates = self._step2_evaluate_reuse_potential(
            branch_purposes, project_info
        )
        
        # ============================================================
        # STEP 3: MAKE BRANCH DECISION
        # Decide whether to use existing or create new branch
        # ============================================================
        logger.info("STEP 3: MAKE BRANCH DECISION")
        decision = self._step3_make_branch_decision(
            current_branch, reuse_candidates, project_info
        )
        
        # ============================================================
        # STEP 4: GENERATE BRANCH NAME
        # Create new name if needed, or select existing
        # ============================================================
        logger.info("STEP 4: GENERATE/SELECT BRANCH NAME")
        final_branch = self._step4_finalize_branch_selection(
            decision, reuse_candidates, project_info
        )
        
        logger.info("=" * 60)
        logger.info(f"Branch selection complete: {final_branch['branch_name']}")
        
        return final_branch['branch_name'], final_branch['reason'], final_branch
    
    # ============================================================
    # STEP 1: ANALYZE EXISTING BRANCHES
    # ============================================================
    
    def _step1_analyze_branch_purposes(self, branch_summaries: Dict[str, Dict]) -> Dict[str, Dict]:
        """STEP 1: Analyze the purpose of each existing branch.
        
        This step examines each branch's analysis to understand its purpose.
        Future enhancements could include:
        - Commit history analysis
        - Age and activity level assessment
        - Merge status checking
        
        Args:
            branch_summaries: Dictionary of branch analyses
            
        Returns:
            Dictionary mapping branch names to their purposes
        """
        logger.info(f"  Analyzing purposes of {len(branch_summaries)} branches")
        
        branch_purposes = {}
        
        for branch_name, summary in branch_summaries.items():
            # Skip if no real analysis available
            if not summary or summary.get('project_type') == 'empty':
                logger.info(f"    Branch '{branch_name}': No analyzable content")
                branch_purposes[branch_name] = {
                    'purpose': 'empty',
                    'active': False,
                    'suitable_for_work': False
                }
                continue
            
            # Extract key information
            purpose_info = {
                'purpose': summary.get('state', 'unknown'),
                'project_type': summary.get('project_type', 'unknown'),
                'technologies': summary.get('technologies', []),
                'quality': summary.get('quality', 'unknown'),
                'patterns': summary.get('patterns', []),
                'active': True,  # Could be enhanced with commit history
                'suitable_for_work': True  # Will be refined in next step
            }
            
            branch_purposes[branch_name] = purpose_info
            logger.info(f"    Branch '{branch_name}': {purpose_info['purpose'][:50]}...")
        
        return branch_purposes
    
    # ============================================================
    # STEP 2: EVALUATE REUSE POTENTIAL
    # ============================================================
    
    def _step2_evaluate_reuse_potential(self, branch_purposes: Dict[str, Dict], 
                                       project_info: Dict) -> List[Dict]:
        """STEP 2: Evaluate which branches could be reused.
        
        This step scores each branch for reuse potential.
        Future enhancements could include:
        - Conflict detection
        - Branch freshness scoring
        - Team ownership checking
        
        Args:
            branch_purposes: Branch purpose analysis
            project_info: Overall project analysis
            
        Returns:
            List of reuse candidates with scores
        """
        logger.info(f"  Evaluating reuse potential for existing branches")
        
        reuse_candidates = []
        project_type = project_info.get('project_type', 'unknown')
        
        for branch_name, purpose_info in branch_purposes.items():
            # Skip main/master branches
            if branch_name.lower() in ['main', 'master', 'develop', 'development']:
                logger.info(f"    Skipping protected branch: {branch_name}")
                continue
            
            # Skip empty branches
            if purpose_info['purpose'] == 'empty':
                continue
            
            # Calculate reuse score (0-100)
            score = 0
            reasons = []
            
            # Check project type compatibility
            if purpose_info['project_type'] == project_type:
                score += 30
                reasons.append("matching project type")
            
            # Check if it's a feature or development branch
            branch_lower = branch_name.lower()
            if any(prefix in branch_lower for prefix in ['feature/', 'feat/', 'enhance/', 'improve/']):
                score += 20
                reasons.append("feature branch")
            elif any(prefix in branch_lower for prefix in ['fix/', 'bugfix/', 'hotfix/']):
                score += 15
                reasons.append("fix branch")
            elif any(prefix in branch_lower for prefix in ['docs/', 'documentation/']):
                score += 10
                reasons.append("documentation branch")
            
            # Check for WIP or experimental branches (good for reuse)
            if any(indicator in branch_lower for indicator in ['wip', 'draft', 'experimental', 'test']):
                score += 25
                reasons.append("work-in-progress branch")
            
            # Bonus for branches that seem abandoned or stale (we can revive them)
            if any(indicator in branch_lower for indicator in ['old', 'stale', 'abandoned', 'temp']):
                score += 15
                reasons.append("potentially abandoned branch")
            
            # Check technology overlap
            if purpose_info.get('technologies'):
                tech_overlap = len(set(purpose_info['technologies']) & set(project_info.get('technologies', [])))
                if tech_overlap > 0:
                    score += min(tech_overlap * 5, 20)
                    reasons.append(f"{tech_overlap} matching technologies")
            
            if score > 0:
                reuse_candidates.append({
                    'branch_name': branch_name,
                    'score': score,
                    'reasons': reasons,
                    'purpose_info': purpose_info
                })
        
        # Sort by score
        reuse_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"  Found {len(reuse_candidates)} potential branches for reuse")
        for candidate in reuse_candidates[:3]:  # Log top 3
            logger.info(f"    {candidate['branch_name']}: score={candidate['score']}, reasons={', '.join(candidate['reasons'])}")
        
        return reuse_candidates
    
    # ============================================================
    # STEP 3: MAKE BRANCH DECISION
    # ============================================================
    
    def _step3_make_branch_decision(self, current_branch: str, 
                                   reuse_candidates: List[Dict], 
                                   project_info: Dict) -> Dict:
        """STEP 3: Decide whether to reuse or create new branch.
        
        This step makes the key decision with AI assistance.
        Future enhancements could include:
        - User preference learning
        - Risk assessment
        - Team conventions checking
        
        Args:
            current_branch: Currently checked out branch
            reuse_candidates: List of reuse candidates
            project_info: Project analysis
            
        Returns:
            Decision dictionary
        """
        logger.info(f"  Making branch selection decision")
        
        # Prepare context for AI decision
        context_parts = [
            f"Current branch: {current_branch}",
            f"Project type: {project_info.get('project_type', 'unknown')}",
            f"Number of reuse candidates: {len(reuse_candidates)}"
        ]
        
        if reuse_candidates:
            context_parts.append("\nTop reuse candidates:")
            for candidate in reuse_candidates[:3]:
                context_parts.append(f"  - {candidate['branch_name']} (score: {candidate['score']})")
                context_parts.append(f"    Reasons: {', '.join(candidate['reasons'])}")
        
        context = "\n".join(context_parts)
        
        # Strong bias towards reusing existing branches (80% probability if good candidates exist)
        reuse_threshold = 30  # Minimum score to consider reuse
        has_good_candidates = any(c['score'] >= reuse_threshold for c in reuse_candidates)
        
        if has_good_candidates:
            # AI decides which existing branch to use
            logger.info(f"🤖 AI: Deciding branch selection strategy with {len(reuse_candidates)} candidates")
            prompt = f"""{context}

You are deciding which branch to use for making improvements to this repository.
You STRONGLY PREFER to reuse existing branches (80% of the time) rather than creating new ones.

Given the reuse candidates above, decide:
1. Should we reuse an existing branch? (strongly prefer YES if score >= {reuse_threshold})
2. If yes, which branch should we use?
3. If no, what type of new branch do we need?

Respond in JSON format:
{{
    "decision": "REUSE|CREATE",
    "selected_branch": "branch-name-if-reuse",
    "new_branch_type": "feature|fix|docs|chore (if CREATE)",
    "reasoning": "brief explanation"
}}"""
        else:
            # No good candidates, likely need to create new
            logger.info(f"🤖 AI: Determining new branch type (no suitable candidates found)")
            prompt = f"""{context}

No suitable existing branches found for reuse (all scores < {reuse_threshold}).
We need to create a new branch.

What type of branch should we create for improving this {project_info.get('project_type', 'project')}?

Respond in JSON format:
{{
    "decision": "CREATE",
    "selected_branch": null,
    "new_branch_type": "feature|fix|docs|chore",
    "reasoning": "brief explanation"
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        try:
            decision = json.loads(response)
            
            # Validate and apply reuse bias
            if has_good_candidates and decision.get('decision') == 'CREATE':
                # Override 20% of CREATE decisions when good candidates exist
                import random
                if random.random() < 0.2:  # Only 20% chance to actually create new
                    logger.info("    Applying reuse bias: overriding CREATE decision")
                    decision = {
                        'decision': 'REUSE',
                        'selected_branch': reuse_candidates[0]['branch_name'],
                        'reasoning': f"Reusing existing branch with high score ({reuse_candidates[0]['score']})"
                    }
            
            logger.info(f"    Decision: {decision['decision']} - {decision.get('reasoning', 'No reason provided')}")
            return decision
            
        except json.JSONDecodeError:
            # Fallback decision
            if reuse_candidates and reuse_candidates[0]['score'] >= reuse_threshold:
                return {
                    'decision': 'REUSE',
                    'selected_branch': reuse_candidates[0]['branch_name'],
                    'reasoning': 'Using highest scoring existing branch'
                }
            else:
                return {
                    'decision': 'CREATE',
                    'new_branch_type': 'feature',
                    'reasoning': 'Creating new feature branch'
                }
    
    # ============================================================
    # STEP 4: GENERATE/SELECT BRANCH NAME
    # ============================================================
    
    def _step4_finalize_branch_selection(self, decision: Dict, 
                                        reuse_candidates: List[Dict],
                                        project_info: Dict) -> Dict:
        """STEP 4: Finalize the branch selection.
        
        This step generates a new branch name or confirms the reuse selection.
        Future enhancements could include:
        - Branch naming convention enforcement
        - Duplicate name checking
        - Team standards validation
        
        Args:
            decision: The branch decision
            reuse_candidates: Available reuse candidates
            project_info: Project analysis
            
        Returns:
            Final branch selection with metadata
        """
        logger.info(f"  Finalizing branch selection")
        
        if decision['decision'] == 'REUSE':
            selected_branch = decision.get('selected_branch')
            
            # Validate the selected branch exists in candidates
            candidate_names = [c['branch_name'] for c in reuse_candidates]
            if selected_branch not in candidate_names:
                # Fallback to best candidate
                if reuse_candidates:
                    selected_branch = reuse_candidates[0]['branch_name']
                else:
                    # Should not happen, but handle gracefully
                    logger.warning("    No reuse candidates available, creating new branch")
                    decision['decision'] = 'CREATE'
            
            if decision['decision'] == 'REUSE':
                # Find the candidate info
                candidate_info = next((c for c in reuse_candidates if c['branch_name'] == selected_branch), None)
                
                result = {
                    'branch_name': selected_branch,
                    'action': 'REUSE',
                    'reason': f"Reusing existing branch: {decision.get('reasoning', 'High compatibility score')}",
                    'score': candidate_info['score'] if candidate_info else 0,
                    'metadata': {
                        'decision': decision,
                        'candidate_info': candidate_info
                    }
                }
                
                logger.info(f"    Selected existing branch: {selected_branch}")
                return result
        
        # Create new branch
        branch_type = decision.get('new_branch_type', 'feature')
        project_type = project_info.get('project_type', 'project')
        
        # Generate branch name with AI
        logger.info(f"🤖 AI: Generating new {branch_type} branch name for {project_type} project")
        prompt = f"""Generate a branch name for a {branch_type} branch in a {project_type} project.

The branch name should:
- Start with {branch_type}/
- Be descriptive and specific
- Use lowercase and hyphens
- Be 3-5 words after the prefix
- NOT be 'main', 'master', or generic like 'feature/improvement'

Technologies in project: {', '.join(project_info.get('technologies', [])[:5])}

Respond with ONLY the branch name, no explanation."""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        
        for chunk in self.client.chat_stream(self.model, messages):
            response += chunk
        
        branch_name = response.strip().lower().replace(' ', '-')
        
        # Sanitize and validate
        if not branch_name.startswith(f"{branch_type}/"):
            branch_name = f"{branch_type}/{branch_name}"
        
        # Remove any invalid characters
        branch_name = ''.join(c if c.isalnum() or c in ['-', '/'] else '-' for c in branch_name)
        
        # Ensure it's not a protected name
        if branch_name.split('/')[-1] in ['main', 'master', 'develop']:
            branch_name = f"{branch_type}/gitllama-enhancement"
        
        result = {
            'branch_name': branch_name,
            'action': 'CREATE',
            'reason': f"Creating new {branch_type} branch: {decision.get('reasoning', 'No suitable existing branch')}",
            'score': 0,
            'metadata': {
                'decision': decision,
                'branch_type': branch_type
            }
        }
        
        logger.info(f"    Created new branch name: {branch_name}")
        return result