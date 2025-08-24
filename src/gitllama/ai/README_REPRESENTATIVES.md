# Congressional Representatives Configuration

This file explains how to customize the congressional representatives for your specific use cases.

## Overview

The congressional system uses three AI representatives to evaluate and vote on AI responses. Each representative has their own personality, voting style, and **individual AI model**.

## Configuration File

Representatives are defined in `representatives.py` with the following structure:

```python
Representative(
    name="Representative Name",
    title="Their Role Title",
    personality="Description of their personality and approach",
    context_prompt="Instructions for how they should evaluate responses",
    voting_style="conservative|progressive|balanced",
    model="ollama-model-name"  # Individual model for this representative
)
```

## Current Representatives

### 1. Senator Prudence - The Conservative Guardian
- **Model**: `gemma3:4b`
- **Role**: Security and safety focused
- **Voting**: Skeptical by nature, votes NO if there's any doubt

### 2. Representative Innovation - The Progressive Advocate  
- **Model**: `gemma3:4b`
- **Role**: Innovation and efficiency focused
- **Voting**: Optimistic, votes YES if response shows promise

### 3. Justice Balance - The Neutral Arbiter
- **Model**: `gemma3:4b`
- **Role**: Balanced analysis of technical and practical aspects
- **Voting**: Objective evaluation based on fulfilling intended purpose

## Customizing Representatives

### Individual Models
Each representative can use a different AI model, allowing for specialized personalities:

```python
# Example: Specialized models for different aspects
Representative(
    name="Security Expert",
    model="llama3:8b",  # Great for security analysis
    # ...
),
Representative(
    name="Innovation Advocate", 
    model="qwen2.5:7b",  # Excellent for creative solutions
    # ...
),
Representative(
    name="Architecture Reviewer",
    model="gemma3:4b",  # Solid for balanced decisions
    # ...
)
```

### Personality Customization
Tailor each representative's personality to your domain:

```python
Representative(
    name="Dr. SecureCode",
    title="The Security Auditor",
    personality="Former cybersecurity consultant with 15 years experience. Extremely cautious about vulnerabilities, injection attacks, and data exposure.",
    context_prompt="""You are Dr. SecureCode, a security-focused code reviewer.
    Evaluate responses for:
    - Security vulnerabilities (SQL injection, XSS, etc.)
    - Data exposure risks
    - Authentication/authorization issues
    - Input validation problems
    Vote NO if any security concerns exist.""",
    voting_style="conservative",
    model="llama3:8b"
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