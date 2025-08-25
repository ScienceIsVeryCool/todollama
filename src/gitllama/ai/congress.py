"""
Congress Voting System for AI Response Validation
A system of three Representatives with distinct personalities to evaluate AI responses
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from .client import OllamaClient
from .representatives import Representative, REPRESENTATIVES, build_context_prompt
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
    """Congressional voting system for AI response validation with full historical context"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        """Initialize the Congress with an AI client"""
        self.client = client
        self.main_model = model
        
        # Store all congressional messages and voting decisions
        self.voting_sessions = []  # Full history of all voting sessions
        self.todo_content = ""     # Store TODO.md content for alignment evaluation
        
        models_used = [rep.model for rep in REPRESENTATIVES]
        logger.info(f"🏛️ Congress initialized with individual representative models: {models_used}")
        logger.info(f"🏛️ Main GitLlama model: {model} (Congress uses separate individual models above)")
    
    def set_todo_content(self, todo_content: str):
        """Set the TODO.md content for alignment evaluation"""
        self.todo_content = todo_content
        logger.info(f"🏛️ TODO content set for Congress alignment evaluation ({len(todo_content)} chars)")
    
    def evaluate_response(
        self,
        original_prompt: str,
        ai_response: str,
        context: str = "",
        decision_type: str = "general"
    ) -> CongressDecision:
        """
        Have all Representatives vote on whether the overall direction aligns with TODO.md
        
        Args:
            original_prompt: The original prompt sent to AI
            ai_response: The AI's response to evaluate
            context: Additional context about the decision
            decision_type: Type of decision being evaluated
            
        Returns:
            CongressDecision with all votes and final verdict
        """
        votes = []
        
        # Get the current session number
        session_num = len(self.voting_sessions) + 1
        logger.info(f"🏛️ Congress Session #{session_num}: Evaluating TODO alignment for {decision_type}")
        
        # Build comprehensive historical context for each representative
        historical_context = self._build_historical_context()
        
        for representative in REPRESENTATIVES:
            vote = self._get_representative_todo_alignment_vote(
                representative,
                original_prompt,
                ai_response,
                context,
                decision_type,
                historical_context,
                session_num
            )
            votes.append(vote)
            
            # Log individual vote
            vote_symbol = "✅" if vote.vote else "❌"
            logger.info(f"  {vote_symbol} {representative.name_title}: {vote.vote} (confidence: {vote.confidence:.2f})")
        
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
        logger.info(f"{decision_symbol} Congress Session #{session_num}: {yes_votes}-{no_votes} {'APPROVED' if approved else 'REJECTED'}")
        
        # Store complete voting session with all details
        session_record = {
            "session_number": session_num,
            "decision_type": decision_type,
            "original_prompt": original_prompt,
            "ai_response": ai_response,
            "context": context,
            "decision": decision,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "todo_content_length": len(self.todo_content),
            "votes": [
                {
                    "representative": vote.representative.name_title,
                    "vote": vote.vote,
                    "confidence": vote.confidence,
                    "reasoning": vote.reasoning
                } for vote in votes
            ]
        }
        self.voting_sessions.append(session_record)
        
        # Track in context tracker with enhanced information
        context_tracker.store_variable(
            f"congress_vote_{decision_type}",
            {
                "approved": approved,
                "votes": f"{yes_votes}-{no_votes}",
                "unanimity": unanimity,
                "session_number": session_num,
                "total_sessions": len(self.voting_sessions),
                "vote_details": [
                    {
                        "name": vote.representative.name_title,
                        "title": vote.representative.name_title.split(' - ')[1] if ' - ' in vote.representative.name_title else "Representative",
                        "vote": vote.vote,
                        "confidence": vote.confidence,
                        "reasoning": vote.reasoning[:100] + "..." if len(vote.reasoning) > 100 else vote.reasoning
                    } for vote in votes
                ]
            },
            f"Congressional TODO alignment vote (Session #{session_num})"
        )
        
        return decision
    
    def _build_historical_context(self) -> str:
        """Build a comprehensive historical context from all previous voting sessions"""
        if not self.voting_sessions:
            return "No previous voting sessions to reference."
        
        context_parts = []
        context_parts.append("=== CONGRESSIONAL VOTING HISTORY ===")
        context_parts.append(f"Total Previous Sessions: {len(self.voting_sessions)}")
        context_parts.append("")
        
        # Add each session with truncation to fit context windows
        for session in self.voting_sessions:
            context_parts.append(f"--- Session #{session['session_number']} ({session['decision_type']}) ---")
            context_parts.append(f"Decision: {'APPROVED' if session['decision'].approved else 'REJECTED'} ({session['decision'].vote_count[0]}-{session['decision'].vote_count[1]})")
            
            # Add truncated prompt and response
            prompt_preview = session['original_prompt'][:200] + ("..." if len(session['original_prompt']) > 200 else "")
            response_preview = session['ai_response'][:200] + ("..." if len(session['ai_response']) > 200 else "")
            
            context_parts.append(f"Original Prompt: {prompt_preview}")
            context_parts.append(f"AI Response: {response_preview}")
            
            # Add vote details
            for vote_record in session['votes']:
                vote_symbol = "✅" if vote_record['vote'] else "❌"
                context_parts.append(f"  {vote_symbol} {vote_record['representative']}: {vote_record['reasoning'][:150]}...")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _truncate_context_for_model(self, context: str, max_tokens: int = 8000) -> str:
        """Truncate context to fit within model's context window"""
        # Rough estimate: 4 chars per token
        max_chars = max_tokens * 4
        
        if len(context) <= max_chars:
            return context
        
        # Keep the most recent sessions by truncating from the beginning
        lines = context.split('\n')
        truncated_lines = []
        current_length = 0
        
        # Start from the end and work backwards
        for line in reversed(lines):
            if current_length + len(line) > max_chars:
                truncated_lines.insert(0, "[... Earlier voting sessions truncated for context window ...]")
                break
            truncated_lines.insert(0, line)
            current_length += len(line) + 1  # +1 for newline
        
        return '\n'.join(truncated_lines)
    
    def _get_representative_todo_alignment_vote(
        self,
        representative: Representative,
        original_prompt: str,
        ai_response: str,
        context: str,
        decision_type: str,
        historical_context: str,
        session_num: int
    ) -> CongressVote:
        """Get a representative's vote on whether the overall direction aligns with TODO.md"""
        
        # Build the personality context
        base_prompt = build_context_prompt(representative)
        
        # Truncate historical context to fit the model's context window
        truncated_history = self._truncate_context_for_model(historical_context)
        
        # Build the TODO alignment evaluation prompt
        eval_prompt = f"""{base_prompt}

=== CONGRESSIONAL SESSION #{session_num} ===
You are evaluating whether the overall direction of our AI decision-making process aligns with the goals and requirements specified in the TODO.md file.

TODO.MD CONTENT:
{self.todo_content}

CURRENT DECISION CONTEXT:
Decision Type: {decision_type}
Original Prompt: {original_prompt[:500]}{"..." if len(original_prompt) > 500 else ""}
AI Response: {ai_response[:500]}{"..." if len(ai_response) > 500 else ""}
Additional Context: {context if context else "None provided"}

{truncated_history}

=== YOUR VOTING TASK ===
Based on your personality, values, and the TODO.md requirements, vote on whether you believe the OVERALL DIRECTION of all these voting sessions (including this current one) is properly aligned with achieving the goals specified in the TODO.md file.

Consider:
1. Are we making decisions that move us toward completing the TODO items?
2. Do the patterns in our previous voting sessions show good judgment?
3. Is this current decision consistent with the TODO.md objectives?
4. Based on your personality and values, do you approve of this overall trajectory?

You must respond in this exact format:
VOTE: [YES/NO]
CONFIDENCE: [0.0-1.0]
REASON: [Your reasoning for this vote based on TODO alignment and your values]

Vote according to your nature and whether you believe we're on the right track to accomplish the TODO.md goals."""

        # Get the representative's evaluation using their individual model
        messages = [{"role": "user", "content": eval_prompt}]
        
        response = ""
        for chunk in self.client.chat_stream(
            representative.model, 
            messages, 
            context_name=f"congress_session_{session_num}_{representative.name_title.lower().replace(' ', '_')}"
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
        """Get a summary of all voting session history"""
        if not self.voting_sessions:
            return {"total_votes": 0, "approved": 0, "rejected": 0, "unanimity_rate": 0}
        
        total = len(self.voting_sessions)
        approved = sum(1 for session in self.voting_sessions if session["decision"].approved)
        rejected = total - approved
        unanimous = sum(1 for session in self.voting_sessions if session["decision"].unanimity)
        
        return {
            "total_sessions": total,
            "approved": approved,
            "rejected": rejected,
            "unanimity_rate": unanimous / total if total > 0 else 0,
            "by_type": self._get_votes_by_type(),
            "by_representative": self._get_votes_by_representative(),
            "recent_sessions": self._get_recent_session_summary()
        }
    
    def _get_votes_by_type(self) -> Dict:
        """Get voting breakdown by decision type"""
        by_type = {}
        for session in self.voting_sessions:
            dtype = session["decision_type"]
            if dtype not in by_type:
                by_type[dtype] = {"approved": 0, "rejected": 0}
            
            if session["decision"].approved:
                by_type[dtype]["approved"] += 1
            else:
                by_type[dtype]["rejected"] += 1
        
        return by_type
    
    def _get_votes_by_representative(self) -> Dict:
        """Get voting patterns for each representative"""
        rep_votes = {rep.name_title: {"yes": 0, "no": 0} for rep in REPRESENTATIVES}
        
        for session in self.voting_sessions:
            for vote in session["decision"].votes:
                if vote.vote:
                    rep_votes[vote.representative.name_title]["yes"] += 1
                else:
                    rep_votes[vote.representative.name_title]["no"] += 1
        
        return rep_votes
    
    def _get_recent_session_summary(self) -> List[Dict]:
        """Get summary of the most recent voting sessions"""
        if not self.voting_sessions:
            return []
        
        # Get the last 5 sessions
        recent = self.voting_sessions[-5:]
        
        return [
            {
                "session_number": session["session_number"],
                "decision_type": session["decision_type"],
                "approved": session["decision"].approved,
                "vote_count": f"{session['decision'].vote_count[0]}-{session['decision'].vote_count[1]}",
                "timestamp": session["timestamp"][:19]  # Remove microseconds
            }
            for session in recent
        ]
    
    def get_congress_info(self) -> Dict[str, Any]:
        """Get detailed congress information including models for each representative"""
        return {
            "models": [rep.model for rep in REPRESENTATIVES],
            "total_representatives": len(REPRESENTATIVES),
            "representatives": [
                {
                    "name_title": rep.name_title,
                    "personality": rep.personality,
                    "likes": rep.likes,
                    "dislikes": rep.dislikes,
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
            lines.append(f"{vote_icon} {vote.representative.name_title}")
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