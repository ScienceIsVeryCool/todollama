# GitLlama 🦙

A git automation tool that uses AI to analyze repositories and make code changes. GitLlama clones a repository, analyzes the codebase, selects an appropriate branch, and makes iterative improvements.

## Core Design: Multiple Choice vs Open Response

GitLlama's AI decision-making is built on a dual approach:

- **Multiple Choice Queries**: For deterministic decisions (branch selection, file operations, validation checks)
- **Open Response Queries**: For creative tasks (code generation, commit messages, analysis)

This architecture ensures reliable decision-making while maintaining flexibility for complex tasks.

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

The dual query system provides structure where needed:

```python
# Multiple choice for decisions
result = ai.choice(
    question="Should we reuse an existing branch?",
    options=["REUSE", "CREATE"],
    context="Current branch: main"
)

# Open response for content
result = ai.open(
    prompt="Generate a Python configuration file",
    context="Project type: web application"
)
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

- **AIQuery**: Dual interface for structured choices and open responses with automatic compression
- **Congress**: Congressional voting system with three Representatives for AI validation
- **ContextCompressor**: Intelligent context compression for large codebases
- **ContextTracker**: Tracks all variables and prompt-response pairs for detailed reports
- **MetricsCollector**: Tracks AI calls, compressions, and performance metrics
- **ProjectAnalyzer**: Hierarchical analysis of repository structure
- **BranchAnalyzer**: Branch selection using multiple choice decisions
- **FileModifier**: Iterative file modification with validation
- **ResponseParser**: Extracts clean code from AI responses

## Reports

GitLlama generates HTML reports with:
- Timeline of AI decisions with color-coded variable highlighting
- Congressional voting results with interactive tooltips
- Branch selection rationale
- File modification details  
- API usage statistics
- Context window tracking
- Compression events and metrics
- Performance analytics
- Representative voting patterns and unanimity rates

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