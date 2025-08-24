# GitLlama 🦙

A git automation tool that uses AI to analyze repositories and make code changes. GitLlama clones a repository, analyzes the codebase, selects an appropriate branch, and makes iterative improvements.

## Core Design: 4 Query Types with Templates

GitLlama's AI decision-making is built on a comprehensive 4-query system with structured templates:

- **🔤 Multiple Choice**: Lettered answers (A, B, C, etc.) for deterministic decisions
- **📝 Single Word**: Single word responses perfect for variable storage and simple classifications
- **📰 Open Response**: Essay-style detailed responses for complex analysis and explanations  
- **📄 File Write**: Complete file content generation with automatic formatting cleanup

Each query type uses carefully crafted templates with variable substitution, ensuring consistent, high-quality AI interactions while maintaining full Congressional oversight.

## Installation

```bash
pip install gitllama
```

## Prerequisites

GitLlama requires Ollama for AI features:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model
ollama pull gemma3:4b
```

## Usage

### Basic usage:

```bash
gitllama https://github.com/user/repo.git
```

### With custom model:

```bash
gitllama https://github.com/user/repo.git --model llama3:8b
```

### With specific branch:

```bash
gitllama https://github.com/user/repo.git --branch feature/my-improvement
```

### Verbose mode:

```bash
gitllama https://github.com/user/repo.git --verbose
```

## How It Works

### 1. Repository Analysis
GitLlama analyzes the repository using hierarchical summarization:
- Scans all text files and documentation
- Groups files into chunks that fit the AI's context window
- Analyzes each chunk independently
- Merges summaries hierarchically
- Produces structured insights about the project

### 2. Branch Selection
The AI makes branch decisions using multiple choice queries:
- Analyzes existing branches
- Scores reuse potential
- Decides: REUSE or CREATE
- Selects branch type: feature, fix, docs, or chore

### 3. File Modification
Iterative development with validation:
- AI selects files to modify (multiple choice)
- Generates content (open response)
- Validates changes (multiple choice)
- Continues until satisfied

### 4. Commit and Push
- Generates commit message (open response)
- Commits changes
- Pushes to remote repository

## AI Query Interface

The 4-query system provides the right tool for every task:

```python
# Multiple choice for deterministic decisions with lettered answers
result = ai.multiple_choice(
    question="Should we reuse an existing branch?",
    options=["REUSE", "CREATE"],
    context="Current branch: main"
)
# Returns: letter='A', index=0, value='REUSE'

# Single word for variable storage and classifications
result = ai.single_word(
    question="What programming language is this?",
    context="Repository analysis shows..."
)
# Returns: word='Python'

# Open response for detailed analysis and explanations
result = ai.open(
    prompt="Explain the architecture benefits",
    context="Codebase structure and requirements..."
)
# Returns: content='Detailed essay-style response...'

# File write for generating complete file content
result = ai.file_write(
    requirements="Create a Python configuration file with database settings",
    context="Application uses PostgreSQL and Redis..."
)
# Returns: content='# config.py\nDATABASE_URL = "postgres://..."'
```

## Automatic Context Compression

GitLlama now includes intelligent context compression to handle large codebases that exceed model context limits:

### How It Works

When the AI context window is too large, GitLlama automatically:
1. Detects when context exceeds 70% of model capacity (reserves 30% for prompt/response)
2. Splits context into chunks and compresses each using AI summarization
3. Extracts only information relevant to the current query
4. Performs multiple compression rounds if needed (up to 3 rounds)
5. Tracks compression metrics for performance monitoring

### Features

- **Automatic Detection**: No configuration needed - compression triggers automatically
- **Query-Focused**: Compression preserves information relevant to the specific question
- **Multi-Round Compression**: Can perform up to 3 compression rounds for very large contexts
- **Metrics Tracking**: Records compression events, ratios, and success rates
- **Fallback Handling**: Gracefully degrades to truncation if compression fails

### Performance

- Typical compression ratios: 40-60% size reduction
- Minimal impact on response quality for focused queries
- Compression time: 2-5 seconds per round depending on context size

This feature ensures GitLlama can work with repositories of any size without manual context management.

## Congressional Oversight System 🏛️

GitLlama includes a novel Congressional voting system that provides governance and validation of AI decisions:

### How It Works

Every AI response is evaluated by three virtual Representatives with distinct personalities:

- **Senator Prudence (Conservative)**: Risk-averse, prioritizes accuracy and safety
- **Representative Innovation (Progressive)**: Forward-thinking, values practical solutions
- **Justice Balance (Neutral)**: Analytical, weighs pros and cons objectively

### Features

- **Automatic Evaluation**: All AI responses get Congressional review
- **Majority Voting**: Decisions require majority approval (2 out of 3 votes)
- **Detailed Reasoning**: Each Representative provides confidence scores and reasoning
- **Full Transparency**: All votes and reasoning included in HTML reports
- **Interactive Reports**: Hover over vote symbols to see detailed Representative feedback

### In Reports

Congressional votes appear inline with AI exchanges:
- 🏛️ Congressional icon shows voting occurred
- ✓/✗ symbols show individual Representative votes
- Hover tooltips reveal detailed reasoning and confidence scores
- Summary section shows overall voting patterns by Representative

This system ensures AI decisions undergo democratic review, adding a layer of validation and transparency to the automation process.

## Query Type System 🎯

GitLlama's enhanced 4-query system provides specialized tools for every AI interaction need:

### 🔤 Multiple Choice Query
- **Purpose**: Deterministic decisions requiring selection from predefined options
- **Returns**: Letter (A, B, C, etc.), index, and option value
- **Template**: Structured prompt with lettered options and clear instructions
- **Best for**: Branch decisions, operation types, validation checks
- **Example**: Choose deployment strategy, select file operation, pick testing approach

### 📝 Single Word Query  
- **Purpose**: Variable storage and simple classifications requiring one-word answers
- **Returns**: Single cleaned word with confidence score
- **Template**: Focused prompt emphasizing single-word response requirement
- **Best for**: Language detection, status indicators, simple categorization
- **Example**: Programming language, file type, priority level

### 📰 Open Response Query
- **Purpose**: Detailed analysis, explanations, and complex reasoning tasks
- **Returns**: Comprehensive text content with proper formatting
- **Template**: Essay-style prompt encouraging detailed, structured responses  
- **Best for**: Architecture explanations, code analysis, documentation generation
- **Example**: Explain design patterns, analyze code complexity, describe system benefits

### 📄 File Write Query
- **Purpose**: Complete file content generation ready for direct use
- **Returns**: Clean file content with automatic formatting and code block removal
- **Template**: File-focused prompt with clear content requirements
- **Best for**: Configuration files, code generation, documentation creation
- **Example**: Generate config.py, create test files, produce README content

### Template Features
- **Variable Substitution**: `{context}`, `{question}`, `{options}`, `{prompt}`, `{requirements}`
- **Consistent Formatting**: Standardized instruction patterns across all query types
- **Context Integration**: Smart context compression and variable tracking
- **Congressional Oversight**: All queries evaluated by three Representatives with detailed reasoning

## Architecture

```
gitllama/
├── cli.py                 # Command-line interface
├── core/
│   ├── git_operations.py  # Git automation
│   └── coordinator.py     # AI workflow coordination
├── ai/
│   ├── client.py         # Ollama API client
│   ├── query.py          # Multiple choice / open response interface
│   ├── congress.py       # Congressional voting system for AI validation
│   ├── context_compressor.py # Automatic context compression
│   └── parser.py         # Response parsing and code extraction
├── analyzers/
│   ├── project.py        # Repository analysis
│   └── branch.py         # Branch selection logic
├── modifiers/
│   └── file.py           # File modification workflow
└── utils/
    ├── metrics.py        # Metrics collection and tracking
    ├── context_tracker.py # Context and variable tracking for reports
    └── reports.py        # HTML report generation
```

### Key Components:

- **AIQuery**: 4-query interface (multiple_choice, single_word, open, file_write) with templated prompts and automatic compression
- **Congress**: Congressional voting system with three Representatives for AI validation across all query types
- **ContextCompressor**: Intelligent context compression for large codebases
- **ContextTracker**: Tracks all variables and prompt-response pairs for detailed reports
- **MetricsCollector**: Tracks AI calls, compressions, and performance metrics
- **ProjectAnalyzer**: Hierarchical analysis of repository structure
- **BranchAnalyzer**: Branch selection using multiple choice decisions with lettered answers
- **FileModifier**: File generation using dedicated file_write queries with automatic cleanup
- **ResponseParser**: Extracts clean results from all query types with appropriate parsing

## Reports

GitLlama generates HTML reports with:
- Timeline of AI decisions with color-coded variable highlighting across all 4 query types
- Congressional voting results with interactive tooltips for every query
- Query type breakdown (multiple_choice, single_word, open, file_write) 
- Branch selection rationale using lettered multiple choice responses
- File generation details from dedicated file_write queries
- API usage statistics by query type
- Context window tracking and template usage
- Compression events and metrics
- Performance analytics across all query types
- Representative voting patterns and unanimity rates for each query type

Reports are saved to `gitllama_reports/` directory.

## Compatible Models

Works with any Ollama model:
- `gemma3:4b` - Fast and efficient (default)
- `llama3.2:1b` - Ultra-fast for simple tasks
- `codellama:7b` - Optimized for code
- `mistral:7b` - General purpose
- `gemma2:2b` - Very fast

## What Gets Analyzed

- Source code (Python, JavaScript, Java, Go, Rust, etc.)
- Configuration files (JSON, YAML, TOML)
- Documentation (Markdown, README)
- Build files (Dockerfile, package.json)
- Scripts (Shell, Batch)

## Performance

- Small repos (<100 files): ~30 seconds
- Medium repos (100-500 files): 1-2 minutes
- Large repos (500+ files): 2-5 minutes

## Development

```bash
git clone https://github.com/your-org/gitllama.git
cd gitllama
pip install -e ".[dev]"

# Run tests
pytest
```

## Troubleshooting

### Ollama not available?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Context window too small?
```bash
# Use a model with larger context
gitllama repo.git --model mistral:7b
```

### Analysis taking too long?
```bash
# Use a smaller model
gitllama repo.git --model llama3.2:1b
```

## License

GPL v3 - see LICENSE file

## Contributing

Contributions welcome! The modular architecture makes it easy to extend.

---

**Note**: GitLlama requires git credentials configured for pushing changes. Ensure you have appropriate repository access before use.