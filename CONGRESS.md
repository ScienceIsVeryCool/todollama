# 🏛️ Congressional Voting System

The Congress system provides oversight for all AI decisions in GitLlama, featuring three Representatives with distinct personalities who vote on every AI response to evaluate its quality and appropriateness.

## Overview

The Congress system is inspired by a democratic oversight model where three Representatives with different perspectives evaluate every AI response:

- **Senator Prudence** - The Conservative Guardian
- **Representative Innovation** - The Progressive Advocate  
- **Justice Balance** - The Neutral Arbiter

## Representatives

### Senator Prudence (The Conservative Guardian)
- **Personality**: Cautious, methodical, and risk-averse
- **Values**: Accuracy, safety, and thoroughness above all else
- **Voting Style**: Conservative - votes NO if there's any doubt about correctness or safety
- **Typical Concerns**: Security risks, incomplete solutions, unverified claims

### Representative Innovation (The Progressive Advocate)
- **Personality**: Forward-thinking, creative, and optimistic
- **Values**: Innovation, efficiency, and practical solutions
- **Voting Style**: Progressive - votes YES if the response shows promise and addresses the core need
- **Typical Concerns**: Stagnation, over-caution, missed opportunities

### Justice Balance (The Neutral Arbiter)
- **Personality**: Balanced, analytical, and fair
- **Values**: Objectivity, fairness, and comprehensive evaluation
- **Voting Style**: Balanced - weighs pros and cons objectively
- **Typical Concerns**: Bias, incomplete analysis, lack of balance

## How It Works

1. **AI Response Generation**: When you ask a question, the AI generates a response
2. **Congressional Review**: Each Representative independently evaluates the response
3. **Individual Voting**: Each Representative casts a YES/NO vote with confidence level and reasoning
4. **Majority Decision**: Final decision is based on majority vote (2 out of 3)
5. **Reporting**: All votes are tracked and displayed in reports

## Usage

### Basic Usage

```python
from gitllama.ai import OllamaClient, AIQuery

# Initialize AI with Congress enabled (default)
client = OllamaClient()
ai = AIQuery(client, model="gemma3:4b")

# Make a query - Congress automatically evaluates the response
result = ai.choice(
    question="What's the best deployment strategy?",
    options=["Blue-green", "Rolling", "Canary", "Recreate"],
    context_name="deployment_decision"
)

# Access Congressional decision
if result.congress_decision:
    print(f"Congress Vote: {result.congress_decision.vote_count}")
    print(f"Decision: {'APPROVED' if result.congress_decision.approved else 'REJECTED'}")
    
    # Individual votes
    for vote in result.congress_decision.votes:
        print(f"{vote.representative.name}: {'YES' if vote.vote else 'NO'}")
        print(f"  Reasoning: {vote.reasoning}")
```

### Controlling Congressional Oversight

```python
# Disable Congress for specific operations
ai.set_congress_enabled(False)

# Re-enable when needed
ai.set_congress_enabled(True)

# Check current status
summary = ai.get_congress_summary()
```

### Accessing Vote History

```python
# Get voting summary
summary = ai.get_congress_summary()

print(f"Total votes: {summary['total_votes']}")
print(f"Approval rate: {summary['approved']/summary['total_votes']:.1%}")
print(f"Unanimity rate: {summary['unanimity_rate']:.1%}")

# Representative-specific patterns
for rep_name, votes in summary['by_representative'].items():
    approval_rate = votes['yes'] / (votes['yes'] + votes['no']) * 100
    print(f"{rep_name}: {approval_rate:.0f}% approval rate")
```

## Report Integration

Congress votes are automatically included in GitLlama reports:

- **Summary Statistics**: Total votes, approval/rejection counts, unanimity rates
- **Individual Votes**: Each prompt-response pair shows the Congressional evaluation
- **Representative Patterns**: Voting tendencies for each Representative

## Configuration

### Model Configuration
By default, Congress uses the same model as the main AI (`gemma3:4b`). This ensures:
- Consistent behavior across evaluations
- Deterministic voting patterns
- Resource efficiency

### Customization
Each Representative has:
- **Fixed Personality**: Defined context that shapes their evaluation style
- **Consistent Voting Patterns**: Based on their philosophical approach
- **Confidence Scoring**: How certain they are about their vote

## Use Cases

### Quality Assurance
- **Code Reviews**: Congress evaluates generated code for safety and best practices
- **Decision Validation**: Important architectural decisions get multi-perspective review
- **Risk Assessment**: Risky operations are scrutinized by conservative voices

### Debugging AI Behavior
- **Response Quality**: Track which types of responses consistently get approved/rejected
- **Bias Detection**: Different perspectives help identify potential biases
- **Consistency Monitoring**: Ensure AI responses meet quality standards

### Learning and Improvement
- **Pattern Recognition**: Understand what makes responses successful
- **Representative Analysis**: Learn from different evaluation perspectives
- **Historical Tracking**: Monitor improvement over time

## Best Practices

1. **Keep Congress Enabled**: Unless you have specific reasons, keep Congressional oversight active
2. **Review Rejected Responses**: When Congress rejects a response, investigate why
3. **Monitor Voting Patterns**: Unusual voting patterns may indicate issues
4. **Use Context Effectively**: Provide good context to help Representatives make informed decisions

## Examples

See `example_congress_usage.py` for a complete working example, or run `test_congress.py` to see the system in action.

## Technical Details

- **Model**: Uses the same model as main AI (typically `gemma3:4b`)
- **Deterministic**: Same input produces same votes (within model constraints)
- **Parallel Evaluation**: Each Representative votes independently
- **Context Aware**: Considers original prompt, AI response, and any additional context
- **Logged**: All votes are tracked and can be exported for analysis