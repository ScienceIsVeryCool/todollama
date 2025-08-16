# GitLlama Build and Publish Guide

This guide walks you through building and publishing the GitLlama package to PyPI.

## Prerequisites

1. **Python 3.8+** installed
2. **Git** installed and configured
3. **PyPI account** (create at https://pypi.org/account/register/)
4. **TestPyPI account** (create at https://test.pypi.org/account/register/)

## Project Structure Setup

First, create the project structure:

```bash
mkdir gitllama
cd gitllama

# Create the source directory structure
mkdir -p src/gitllama
mkdir -p tests
mkdir -p docs

# Create the main package files (use the artifacts provided)
# - src/gitllama/__init__.py
# - src/gitllama/cli.py  
# - src/gitllama/git_operations.py
# - src/gitllama/config.py
# - pyproject.toml
# - README.md
# - LICENSE (copy from the provided document)
# - .gitignore
# - .flake8
# - .pre-commit-config.yaml
# - MANIFEST.in
# - Makefile
```

## Step 1: Set Up Development Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

## Step 2: Development and Testing

```bash
# Run tests
pytest

# Check code quality
make lint        # or: flake8 src tests
make format      # or: black src tests  
make type-check  # or: mypy src

# Run all quality checks
make test lint format type-check
```

## Step 3: Version Management

Update version in two places before building:

1. **src/gitllama/__init__.py**:
```python
__version__ = "0.1.0"  # Update this
```

2. **pyproject.toml**:
```toml
[project]
version = "0.1.0"  # Update this
```

## Step 4: Build the Package

```bash
# Install build tools
pip install build twine

# Clean previous builds
make clean
# or manually:
rm -rf build/ dist/ *.egg-info/

# Build the package
python -m build
# or:
make build
```

This creates two files in the `dist/` directory:
- `gitllama-0.1.0.tar.gz` (source distribution)
- `gitllama-0.1.0-py3-none-any.whl` (wheel distribution)

## Step 5: Check the Build

```bash
# Check the package
twine check dist/*

# Optional: Test local installation
pip install dist/gitllama-0.1.0-py3-none-any.whl
gitllama --help
pip uninstall gitllama
```

## Step 6: Configure PyPI Authentication

### Option A: API Tokens (Recommended)

1. **TestPyPI** (for testing):
   - Go to https://test.pypi.org/manage/account/token/
   - Create a new API token with scope "Entire account"
   - Save the token (starts with `pypi-`)

2. **PyPI** (for production):
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope "Entire account"
   - Save the token

### Option B: Configure .pypirc file

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

### Option C: Environment Variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
```

## Step 7: Upload to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Or using environment variables:
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_TEST_TOKEN twine upload --repository testpypi dist/*

# Or using make:
make upload-test
```

## Step 8: Test Installation from TestPyPI

```bash
# Create a new virtual environment for testing
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ gitllama

# Test the installation
gitllama --help
gitllama https://github.com/octocat/Hello-World.git --dry-run

# Clean up
deactivate
rm -rf test_env
```

## Step 9: Upload to Production PyPI

Once you've verified everything works on TestPyPI:

```bash
# Upload to production PyPI
twine upload dist/*

# Or using environment variables:
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_PROD_TOKEN twine upload dist/*

# Or using make:
make upload
```

## Step 10: Verify Production Installation

```bash
# Install from PyPI
pip install gitllama

# Test the installation
gitllama --help
```

## Automation with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[test]"

    - name: Run tests
      run: pytest

  publish:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Set up GitHub Secrets

1. Go to your GitHub repository
2. Go to Settings → Secrets and variables → Actions
3. Add a new secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token

## Release Process

1. **Update version numbers** in `__init__.py` and `pyproject.toml`
2. **Update CHANGELOG.md** with new features/fixes
3. **Commit and push** changes
4. **Create a Git tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
5. **Create GitHub release** (triggers automatic publishing)

## Troubleshooting

### Common Issues

1. **"File already exists" error**:
   - You're trying to upload a version that already exists
   - Increment the version number

2. **Authentication errors**:
   - Check your API token
   - Ensure token has correct permissions
   - Check `.pypirc` configuration

3. **Import errors after installation**:
   - Check `pyproject.toml` package configuration
   - Ensure all dependencies are listed
   - Verify package structure

4. **Missing dependencies**:
   - Add missing dependencies to `pyproject.toml`
   - Test in a clean environment

### Debugging Commands

```bash
# Check package contents
tar -tzf dist/gitllama-0.1.0.tar.gz

# Check wheel contents  
python -m zipfile -l dist/gitllama-0.1.0-py3-none-any.whl

# Validate package metadata
twine check dist/*

# Test package locally
pip install -e .
```

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning** (major.minor.patch)
3. **Keep good CHANGELOG.md**
4. **Tag releases in git**
5. **Use GitHub Actions for automation**
6. **Test in clean environments**
7. **Include comprehensive tests**
8. **Document all features**

## Security Considerations

1. **Never commit API tokens** to git
2. **Use repository-scoped tokens** when possible
3. **Rotate tokens regularly**
4. **Use GitHub Secrets** for CI/CD
5. **Review dependencies** for security issues

## Maintenance

### Regular Tasks

1. **Update dependencies**:
   ```bash
   pip list --outdated
   # Update pyproject.toml accordingly
   ```

2. **Security updates**:
   ```bash
   pip audit  # Check for security issues
   ```

3. **Test with new Python versions**
4. **Monitor PyPI download statistics**
5. **Respond to user issues and PRs**

## Next Steps

After successful publication:

1. **Update README.md** with installation instructions
2. **Create documentation** website (e.g., with Sphinx)
3. **Set up continuous integration**
4. **Monitor usage and feedback**
5. **Plan future releases**

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)

## Example Complete Workflow

```bash
# 1. Set up development
git clone https://github.com/your-org/gitllama.git
cd gitllama
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 2. Make changes and test
# ... your development work ...
pytest
make lint format type-check

# 3. Update version
# Edit src/gitllama/__init__.py and pyproject.toml

# 4. Build and test
make clean build
twine check dist/*

# 5. Upload to TestPyPI
make upload-test

# 6. Test installation
pip install --index-url https://test.pypi.org/simple/ gitllama

# 7. Upload to PyPI
make upload

# 8. Create release
git tag v0.1.0
git push origin v0.1.0
```

That's it! Your package should now be available on PyPI for anyone to install with `pip install gitllama`.