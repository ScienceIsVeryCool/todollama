"""
Congress Voting System for AI Response Validation
A system of three Representatives with distinct personalities to evaluate AI responses
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from .client import OllamaClient
from .representatives import Representative, REPRESENTATIVES
from ..utils.context_tracker import context_tracker

logger = logging.getLogger(__name__)


@dataclass
class CongressVote:
    """Result of a Congressional vote on an AI response"""
    representative: Representative
    vote: bool  # True = approve, False = reject
    reasoning: str
    confidence: float


@dataclass
class CongressDecision:
    """Final decision from all Representatives"""
    votes: List[CongressVote]
    approved: bool  # Majority decision
    vote_count: Tuple[int, int]  # (yes_votes, no_votes)
    unanimity: bool


class Congress:
    """Congressional voting system for AI response validation"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        """Initialize the Congress with an AI client"""
        self.client = client
        # The fallback model is ignored since each representative has their own model
        self.voting_history = []
        models_used = [rep.model for rep in REPRESENTATIVES]
        logger.info(f"🏛️ Congress initialized with individual models: {models_used} (requested fallback: {model})")
    
    def evaluate_response(
        self,
        original_prompt: str,
        ai_response: str,
        context: str = "",
        decision_type: str = "general"
    ) -> CongressDecision:
        """
        Have all Representatives vote on an AI response
        
        Args:
            original_prompt: The original prompt sent to AI
            ai_response: The AI's response to evaluate
            context: Additional context about the decision
            decision_type: Type of decision being evaluated
            
        Returns:
            CongressDecision with all votes and final verdict
        """
        votes = []
        
        logger.info(f"🏛️ Congress convening to evaluate {decision_type} response")
        
        for representative in REPRESENTATIVES:
            vote = self._get_representative_vote(
                representative,
                original_prompt,
                ai_response,
                context,
                decision_type
            )
            votes.append(vote)
            
            # Log individual vote
            vote_symbol = "✅" if vote.vote else "❌"
            logger.info(f"  {vote_symbol} {representative.name}: {vote.vote} (confidence: {vote.confidence:.2f})")
        
        # Calculate decision
        yes_votes = sum(1 for v in votes if v.vote)
        no_votes = len(votes) - yes_votes
        approved = yes_votes > no_votes
        unanimity = yes_votes == len(votes) or no_votes == len(votes)
        
        decision = CongressDecision(
            votes=votes,
            approved=approved,
            vote_count=(yes_votes, no_votes),
            unanimity=unanimity
        )
        
        # Log final decision
        decision_symbol = "🎉" if approved else "🚫"
        logger.info(f"{decision_symbol} Congress Decision: {yes_votes}-{no_votes} {'APPROVED' if approved else 'REJECTED'}")
        
        # Store in voting history
        self.voting_history.append({
            "type": decision_type,
            "decision": decision,
            "prompt": original_prompt[:100],
            "response": ai_response[:100]
        })
        
        # Track in context tracker
        context_tracker.store_variable(
            f"congress_vote_{decision_type}",
            {
                "approved": approved,
                "votes": f"{yes_votes}-{no_votes}",
                "unanimity": unanimity,
                "representatives": [v.representative.name for v in votes]
            },
            f"Congressional vote on {decision_type}"
        )
        
        return decision
    
    def _get_representative_vote(
        self,
        representative: Representative,
        original_prompt: str,
        ai_response: str,
        context: str,
        decision_type: str
    ) -> CongressVote:
        """Get a single representative's vote on a response"""
        
        # Build the evaluation prompt
        eval_prompt = f"""{representative.context_prompt}

You are evaluating an AI response for a {decision_type} decision.

ORIGINAL PROMPT:
{original_prompt}

AI RESPONSE:
{ai_response}

ADDITIONAL CONTEXT:
{context if context else "None provided"}

Based on your personality and voting style as {representative.name}, evaluate this response.
Consider:
1. Does it correctly address the prompt?
2. Is it safe and appropriate?
3. Is it complete and useful?
4. Does it align with best practices?

Respond with ONLY:
VOTE: [YES/NO]
CONFIDENCE: [0.0-1.0]
REASON: [One sentence explanation]

Be decisive and follow your character's tendencies."""

        # Get the representative's evaluation using their individual model
        messages = [{"role": "user", "content": eval_prompt}]
        
        response = ""
        for chunk in self.client.chat_stream(
            representative.model, 
            messages, 
            context_name=f"congress_{representative.name.lower().replace(' ', '_')}"
        ):
            response += chunk
        
        # Parse the vote
        vote, confidence, reasoning = self._parse_vote_response(response)
        
        return CongressVote(
            representative=representative,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _parse_vote_response(self, response: str) -> Tuple[bool, float, str]:
        """Parse a representative's vote response"""
        lines = response.strip().split('\n')
        
        vote = False
        confidence = 0.5
        reasoning = "No reasoning provided"
        
        for line in lines:
            line = line.strip()
            
            # Parse vote
            if line.upper().startswith("VOTE:"):
                vote_text = line.split(":", 1)[1].strip().upper()
                vote = "YES" in vote_text or "APPROVE" in vote_text or "ACCEPT" in vote_text
            
            # Parse confidence
            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    conf_text = line.split(":", 1)[1].strip()
                    # Extract number from text
                    import re
                    numbers = re.findall(r'[0-9.]+', conf_text)
                    if numbers:
                        confidence = float(numbers[0])
                        if confidence > 1.0:
                            confidence = confidence / 100.0  # Handle percentage
                        confidence = max(0.0, min(1.0, confidence))
                except:
                    confidence = 0.5
            
            # Parse reasoning
            elif line.upper().startswith("REASON:"):
                reasoning = line.split(":", 1)[1].strip()
        
        return vote, confidence, reasoning
    
    def get_voting_summary(self) -> Dict:
        """Get a summary of all voting history"""
        if not self.voting_history:
            return {"total_votes": 0, "approved": 0, "rejected": 0, "unanimity_rate": 0}
        
        total = len(self.voting_history)
        approved = sum(1 for h in self.voting_history if h["decision"].approved)
        rejected = total - approved
        unanimous = sum(1 for h in self.voting_history if h["decision"].unanimity)
        
        return {
            "total_votes": total,
            "approved": approved,
            "rejected": rejected,
            "unanimity_rate": unanimous / total if total > 0 else 0,
            "by_type": self._get_votes_by_type(),
            "by_representative": self._get_votes_by_representative()
        }
    
    def _get_votes_by_type(self) -> Dict:
        """Get voting breakdown by decision type"""
        by_type = {}
        for history in self.voting_history:
            dtype = history["type"]
            if dtype not in by_type:
                by_type[dtype] = {"approved": 0, "rejected": 0}
            
            if history["decision"].approved:
                by_type[dtype]["approved"] += 1
            else:
                by_type[dtype]["rejected"] += 1
        
        return by_type
    
    def _get_votes_by_representative(self) -> Dict:
        """Get voting patterns for each representative"""
        rep_votes = {rep.name: {"yes": 0, "no": 0} for rep in REPRESENTATIVES}
        
        for history in self.voting_history:
            for vote in history["decision"].votes:
                if vote.vote:
                    rep_votes[vote.representative.name]["yes"] += 1
                else:
                    rep_votes[vote.representative.name]["no"] += 1
        
        return rep_votes
    
    def get_congress_info(self) -> Dict[str, Any]:
        """Get detailed congress information including models for each representative"""
        return {
            "models": [rep.model for rep in REPRESENTATIVES],
            "total_representatives": len(REPRESENTATIVES),
            "representatives": [
                {
                    "name": rep.name,
                    "title": rep.title,
                    "personality": rep.personality,
                    "voting_style": rep.voting_style,
                    "model": rep.model  # Each uses their own individual model
                }
                for rep in REPRESENTATIVES
            ],
            "voting_summary": self.get_voting_summary()
        }
    
    def format_decision_for_display(self, decision: CongressDecision) -> str:
        """Format a decision for nice display"""
        lines = []
        lines.append("=" * 50)
        lines.append("🏛️ CONGRESSIONAL DECISION")
        lines.append("=" * 50)
        
        for vote in decision.votes:
            vote_icon = "✅" if vote.vote else "❌"
            lines.append(f"{vote_icon} {vote.representative.name} ({vote.representative.title})")
            lines.append(f"   Vote: {'YES' if vote.vote else 'NO'} (Confidence: {vote.confidence:.1%})")
            lines.append(f"   Reasoning: {vote.reasoning}")
            lines.append("")
        
        lines.append("-" * 50)
        verdict = "APPROVED" if decision.approved else "REJECTED"
        lines.append(f"Final Verdict: {verdict} ({decision.vote_count[0]}-{decision.vote_count[1]})")
        if decision.unanimity:
            lines.append("📢 UNANIMOUS DECISION")
        lines.append("=" * 50)
        
        return "\n".join(lines)