# GitLlama 🦙

Simple git automation tool. Clone, branch, change, commit, and push with one command.

## Installation

```bash
pip install gitllama
```

## Usage

Basic usage:

```bash
gitllama https://github.com/user/repo.git
```

With custom branch:

```bash
gitllama https://github.com/user/repo.git --branch my-feature
```

With custom commit message:

```bash
gitllama https://github.com/user/repo.git --message "My custom commit"
```

## What it does

1. Clones the repository
2. Creates and checks out a new branch
3. Makes a simple change (creates a file)
4. Commits the changes
5. Pushes to remote

## Python API

```python
from gitllama import GitAutomator

with GitAutomator() as automator:
    results = automator.run_full_workflow(
        git_url="https://github.com/user/repo.git",
        branch_name="my-branch"
    )
    print(f"Success: {results['success']}")
```

## Expanding

To add custom change logic, modify the `make_changes()` method in `GitAutomator`:

```python
def make_changes(self):
    # Add your custom logic here
    # Create files, modify existing files, etc.
    return ["list_of_modified_files"]
```

## Development

```bash
git clone https://github.com/your-org/gitllama.git
cd gitllama
pip install -e ".[dev]"
```

## Building

```bash
pip install build twine
python -m build
twine upload dist/*
```

## License

GPL v3 - see LICENSE file.