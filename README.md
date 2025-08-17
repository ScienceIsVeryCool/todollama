# GitLlama 🦙🤖

AI-powered git automation tool with deep project understanding. GitLlama uses hierarchical AI analysis to intelligently clone, branch, change, commit, and push your code.

## 🌟 Key Features

- **🧠 Deep Project Analysis**: Hierarchical summarization system that understands entire codebases
- **📊 Smart Chunking**: Automatically splits large repositories to fit AI context windows
- **🔄 Merge-Sort Summarization**: Combines multiple analyses into comprehensive understanding
- **🎯 Intelligent Decision Making**: AI makes context-aware decisions at every step
- **📝 Detailed Logging**: See exactly how your project is being analyzed
- **🔧 Extensible Architecture**: Easy to add new analysis steps
- **⚡ Fallback Mode**: Works without AI for simple automation

## 🚀 Installation

```bash
pip install gitllama
```

## 📋 Prerequisites

For AI features, you need Ollama running locally:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model (recommended for this tool)
ollama pull llama3.2:3b
```

## 💻 Usage

### Basic AI-powered usage:

```bash
gitllama https://github.com/user/repo.git
```

### With custom model:

```bash
gitllama https://github.com/user/repo.git --model codellama:7b
```

### Manual branch name (AI still handles other decisions):

```bash
gitllama https://github.com/user/repo.git --branch feature/my-improvement
```

### Manual commit message:

```bash
gitllama https://github.com/user/repo.git --message "feat: add new feature"
```

### Disable AI (simple automation):

```bash
gitllama https://github.com/user/repo.git --no-ai
```

### Verbose mode (see detailed analysis):

```bash
gitllama https://github.com/user/repo.git --verbose
```

## 🔬 How It Works

GitLlama uses a sophisticated multi-step process to understand and improve repositories:

### 1. **Deep Repository Analysis** 🔍
   - **Step 1: Data Gathering** - Scans all text files, configs, and documentation
   - **Step 2: Smart Chunking** - Groups files to maximize AI context window usage
   - **Step 3: Parallel Analysis** - Each chunk analyzed independently for scalability
   - **Step 4: Hierarchical Merging** - Combines summaries using merge-sort approach
   - **Step 5: Result Formatting** - Creates structured insights about the project

### 2. **Intelligent Workflow** 🤖
   1. **Clones the repository**
   2. **AI explores the project** - Deep multi-level analysis
   3. **AI decides on branch name** - Context-aware and meaningful
   4. **AI makes intelligent changes** - Based on project understanding
   5. **AI generates commit message** - Follows conventional commit format
   6. **Pushes to remote**

### Example Analysis Output:
```
Starting hierarchical repository analysis
============================================================
STEP 1: DATA GATHERING
  Found 45 files with 12500 total tokens
STEP 2: CHUNKING
  Created 5 chunks for analysis
    Chunk 1: 12 files, 2500 tokens
    Chunk 2: 10 files, 2800 tokens
    Chunk 3: 8 files, 2200 tokens
    Chunk 4: 9 files, 2600 tokens
    Chunk 5: 6 files, 2400 tokens
STEP 3: CHUNK ANALYSIS
  Analyzing 5 chunks
    Processing chunk 1/5...
    Processing chunk 2/5...
    ...
STEP 4: HIERARCHICAL MERGING
  Starting hierarchical merge of 5 summaries
    Level 1: Merging 5 summaries (1800 tokens)
STEP 5: FORMAT RESULTS
  Formatting final results
============================================================
Repository analysis complete!
```

## 🐍 Python API

```python
from gitllama import GitAutomator, AICoordinator

# With AI - Full intelligent automation
ai = AICoordinator(model="llama3.2:3b")
with GitAutomator(ai_coordinator=ai) as automator:
    results = automator.run_full_workflow(
        git_url="https://github.com/user/repo.git"
    )
    
    print(f"Success: {results['success']}")
    print(f"Branch created: {results['branch']}")
    print(f"Files modified: {results['modified_files']}")
    
    # Access detailed AI analysis
    if 'ai_analysis' in results:
        analysis = results['ai_analysis']
        print(f"Project Type: {analysis['project_type']}")
        print(f"Technologies: {', '.join(analysis['technologies'])}")
        print(f"Code Quality: {analysis['quality']}")
        print(f"Architecture: {analysis['architecture']}")

# Without AI - Simple automation
with GitAutomator() as automator:
    results = automator.run_full_workflow(
        git_url="https://github.com/user/repo.git",
        branch_name="my-branch",
        commit_message="My changes"
    )
```

## 🏗️ Architecture

GitLlama is built with a modular architecture for easy extension:

```
gitllama/
├── cli.py              # Command-line interface
├── git_operations.py   # Git automation logic
├── ai_coordinator.py   # AI workflow coordination
├── project_analyzer.py # Hierarchical project analysis (NEW!)
└── ollama_client.py    # Ollama API integration
```

### Key Components:

- **ProjectAnalyzer**: Handles the 5-step hierarchical analysis process
- **AICoordinator**: Orchestrates AI decisions throughout the workflow
- **GitAutomator**: Manages git operations with optional AI integration
- **OllamaClient**: Interfaces with local Ollama models

## 🤖 AI Models

The tool works with any Ollama model. Recommended models:

- `llama3.2:3b` - Fast and efficient (default)
- `llama3.2:1b` - Ultra-fast for simple tasks
- `codellama:7b` - Optimized for code understanding
- `mistral:7b` - Good general purpose
- `gemma2:2b` - Very fast, good for simple tasks

### Context Window Sizes:
- Small models (1-3B): ~2-4K tokens
- Medium models (7B): ~4-8K tokens
- Large models (13B+): ~8-16K tokens

## 🎯 What Gets Analyzed

GitLlama intelligently analyzes:
- Source code files (Python, JavaScript, Java, Go, Rust, etc.)
- Configuration files (JSON, YAML, TOML, etc.)
- Documentation (Markdown, README, LICENSE)
- Build files (Dockerfile, Makefile, package.json)
- Scripts (Shell, Batch, PowerShell)
- Web assets (HTML, CSS, XML)

## 📊 Analysis Results

The AI provides multi-level insights:

```json
{
  "project_type": "web-application",
  "technologies": ["Python", "FastAPI", "PostgreSQL", "React"],
  "state": "Production-ready with comprehensive test coverage",
  "architecture": "Microservices with REST API",
  "quality": "High - follows best practices",
  "patterns": ["MVC", "Repository Pattern", "Dependency Injection"],
  "analysis_metadata": {
    "total_files": 156,
    "total_tokens": 45000,
    "chunks_created": 12,
    "context_window": 4096,
    "model": "llama3.2:3b"
  }
}
```

## ⚙️ Configuration

```bash
# Use a different Ollama server
gitllama https://github.com/user/repo.git --ollama-url http://remote-server:11434

# Use a specific model with more context
gitllama https://github.com/user/repo.git --model codellama:7b

# Verbose output for debugging
gitllama https://github.com/user/repo.git --verbose
```

## 🔧 Extending GitLlama

The modular design makes it easy to add new analysis steps:

```python
# In project_analyzer.py, each step is clearly separated:

def _step1_gather_repository_data(self, repo_path):
    """STEP 1: Gather all repository data"""
    # Add git history analysis here
    # Add dependency scanning here
    # Add security checks here

def _step2_create_chunks(self, files):
    """STEP 2: Create smart chunks"""
    # Add semantic grouping here
    # Add priority-based chunking here

def _step3_analyze_chunks(self, chunks):
    """STEP 3: Analyze each chunk"""
    # Add code quality metrics here
    # Add security scanning here
    # Add performance analysis here
```

## 📈 Performance

- **Small repos (<100 files)**: ~30 seconds
- **Medium repos (100-500 files)**: ~1-2 minutes
- **Large repos (500+ files)**: ~2-5 minutes

*Times vary based on model size and system performance*

## 🛠️ Development

```bash
git clone https://github.com/your-org/gitllama.git
cd gitllama
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
make lint
make format
make type-check
```

## 🐛 Troubleshooting

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
# Use a smaller, faster model
gitllama repo.git --model llama3.2:1b
```

## 📝 License

GPL v3 - see LICENSE file

## 🤝 Contributing

Contributions are welcome! The modular architecture makes it easy to add:
- New analysis steps
- Additional AI models support
- More file type handlers
- Enhanced decision strategies

## 🚀 Future Enhancements

- [ ] Git history analysis
- [ ] Dependency vulnerability scanning
- [ ] Parallel chunk processing
- [ ] Code quality metrics
- [ ] Security analysis
- [ ] Test coverage assessment
- [ ] README generation
- [ ] Automatic PR descriptions
- [ ] Multi-language documentation

---

**Note**: GitLlama requires git credentials configured for pushing to repositories. Ensure you have proper access rights to the repositories you're modifying.