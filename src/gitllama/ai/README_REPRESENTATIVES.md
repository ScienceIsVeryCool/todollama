# The Congressional Representatives System

This file explains the congressional representatives system for AI response evaluation.

## Overview

The congressional system uses three AI representatives embodying fundamental aspects of humanity. Each votes based on their core values and personality, regardless of topic expertise - they represent human nature itself through three distinct perspectives: Logic, Creativity, and Compassion.

## Configuration File

Representatives are defined in `representatives.py` with the following structure:

```python
Representative(
    name_title="Combined Name and Title",  # Single field for identity
    personality="Core personality embodying an aspect of humanity", 
    likes=["list", "of", "values", "they", "appreciate"],  # Values they support
    dislikes=["list", "of", "things", "they", "oppose"],   # Things they reject
    voting_style="analytical|progressive|humanistic",     # How they decide
    model="ollama-model-name"  # Individual AI model
)
```

## The Three Representatives (Current Configuration)

### 1. Caspar the Rational - The Logical Mind
- **Model**: `gemma3:4b`
- **Aspect**: Logic, reason, and analytical thinking
- **Values**: evidence, consistency, methodology, precision, data, proof
- **Opposes**: assumptions, speculation, bias, shortcuts, vagueness
- **Voting**: Analytical - based on logical evaluation

### 2. Melchior the Visionary - The Creative Spirit
- **Model**: `gemma3:4b` 
- **Aspect**: Creativity, innovation, and progress
- **Values**: innovation, boldness, experimentation, transformation, possibilities
- **Opposes**: stagnation, conformity, rigid thinking, status quo, limitations
- **Voting**: Progressive - embraces change and new ideas

### 3. Balthasar the Compassionate - The Human Heart
- **Model**: `gemma3:4b`
- **Aspect**: Wisdom, empathy, and moral judgment
- **Values**: compassion, fairness, kindness, justice, human dignity, harmony
- **Opposes**: cruelty, harm, exploitation, inequality, divisiveness
- **Voting**: Humanistic - considers human impact and moral implications

## The Templated Prompt System

The system uses a templated approach where each representative's evaluation prompt is dynamically built from their personality and values:

```python
def build_context_prompt(representative: Representative) -> str:
    """Build a templated context prompt for any representative"""
    return f"""You are {representative.name_title}, a representative evaluating an AI response.

Your personality: {representative.personality}

You appreciate and value: {', '.join(representative.likes)}

You dislike and oppose: {', '.join(representative.dislikes)}

Your role is to vote YES or NO on whether the AI response is acceptable. 
Base your decision on your values and personality, even if the topic is 
outside your direct experience. Vote according to how you feel the response 
aligns with what you value and oppose."""
```

## Customizing Representatives

### Values-Based Customization
The power of the Magi system lies in the extensive likes/dislikes lists:

```python
Representative(
    name_title="Custom Representative",
    personality="Embodies specific aspect of humanity you want to represent",
    likes=[
        # Add values, concepts, approaches they should appreciate
        "accuracy", "efficiency", "user-friendliness", "sustainability"
    ],
    dislikes=[
        # Add things they should oppose or be skeptical of  
        "waste", "complexity", "user-hostile design", "short-term thinking"
    ],
    voting_style="analytical",  # or progressive, humanistic
    model="gemma3:4b"
)
```

### Individual Models
Each representative can use different AI models for specialized reasoning:

```python
# Example: Different models for different aspects
Representative(
    name_title="Logic Engine Alpha",
    model="llama3:8b",     # Strong analytical reasoning
    # ...
),
Representative(
    name_title="Creative Catalyst Beta", 
    model="qwen2.5:7b",    # Innovative thinking
    # ...
),
Representative(
    name_title="Wisdom Arbiter Gamma",
    model="gemma3:4b",     # Balanced judgment
    # ...
)
```

### Use Case Examples

#### Code Review Congress
- **Security Expert**: `llama3:8b` - Finds security vulnerabilities
- **Performance Analyst**: `qwen2.5:7b` - Optimizes for efficiency  
- **Maintainability Judge**: `gemma3:4b` - Ensures clean, readable code

#### Feature Planning Congress
- **Risk Assessor**: `llama3:8b` - Evaluates implementation risks
- **Innovation Catalyst**: `qwen2.5:7b` - Pushes for modern solutions
- **Business Analyst**: `gemma3:4b` - Balances features with business needs

#### Architecture Review Congress  
- **Security Architect**: `llama3:8b` - Security implications
- **Cloud Specialist**: `qwen2.5:7b` - Modern cloud-native patterns
- **Enterprise Architect**: `gemma3:4b` - Scalability and maintainability

## Best Practices

1. **Diverse Perspectives**: Choose models and personalities that complement each other
2. **Clear Roles**: Give each representative a specific area of expertise
3. **Balanced Voting**: Mix conservative, progressive, and balanced voting styles
4. **Domain Expertise**: Tailor personalities to your specific use case
5. **Model Selection**: Choose models that excel in each representative's area

## Testing Changes

After modifying representatives, test your changes:

```bash
python test_congress_hardcoding.py
```

## Impact on Reports

Representatives appear in generated reports showing:
- Individual model used by each representative
- Voting patterns and decisions  
- Personality and role information
- Congressional configuration details

---

**Note**: Changes to representatives.py take effect immediately - no restart required!