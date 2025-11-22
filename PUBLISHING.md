# Publishing to PyPI - Step-by-Step Guide

This guide walks you through publishing the Method CRM MCP Server to PyPI.

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org/account/register/
   - Verify your email address
   - Enable 2FA (highly recommended)

2. **TestPyPI Account** (for testing)
   - Create account at https://test.pypi.org/account/register/
   - Verify your email address

3. **API Tokens**
   - Generate PyPI API token at https://pypi.org/manage/account/token/
   - Generate TestPyPI token at https://test.pypi.org/manage/account/token/
   - Save tokens securely (they're shown only once!)

4. **Install Build Tools**
   ```bash
   pip install --upgrade build twine
   ```

## Step 1: Prepare Your Package

### 1.1 Update Version Number

Edit `pyproject.toml` and update version:
```toml
version = "1.0.0"  # Update for each release
```

### 1.2 Update Your Email

Edit `pyproject.toml` and replace placeholder email:
```toml
authors = [
    {name = "Avinash Sangle", email = "your-real-email@example.com"}
]
maintainers = [
    {name = "Avinash Sangle", email = "your-real-email@example.com"}
]
```

### 1.3 Verify Files are Complete

```bash
# Check that all required files exist
ls -la README.md LICENSE pyproject.toml MANIFEST.in

# Check source code structure
tree src/method_mcp
```

### 1.4 Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info src/*.egg-info
```

## Step 2: Build Distribution Packages

```bash
# Build source distribution and wheel
python -m build

# Verify build succeeded
ls -lh dist/
# Should see:
# - method-crm-mcp-1.0.0.tar.gz (source distribution)
# - method_crm_mcp-1.0.0-py3-none-any.whl (wheel)
```

### 2.1 Check Package Contents

```bash
# Inspect wheel contents
unzip -l dist/method_crm_mcp-1.0.0-py3-none-any.whl

# Inspect source distribution
tar -tzf dist/method-crm-mcp-1.0.0.tar.gz
```

### 2.2 Validate Package Metadata

```bash
# Check package for errors
twine check dist/*

# Should output: "Checking dist/... PASSED"
```

## Step 3: Test on TestPyPI (RECOMMENDED)

### 3.1 Configure TestPyPI Token

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcH...your-testpypi-token-here...

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcH...your-pypi-token-here...
```

**Security Note**: Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

### 3.2 Upload to TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# If successful, you'll see:
# Uploading distributions to https://test.pypi.org/legacy/
# Uploading method_crm_mcp-1.0.0-py3-none-any.whl
# Uploading method-crm-mcp-1.0.0.tar.gz
```

### 3.3 Test Installation from TestPyPI

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    method-crm-mcp

# Test import
python -c "from method_mcp.server import mcp; print('✓ Package works!')"

# Test CLI
python -m method_mcp.server --help

# Cleanup
deactivate
rm -rf test_env
```

### 3.4 View on TestPyPI

Visit: https://test.pypi.org/project/method-crm-mcp/

## Step 4: Publish to Production PyPI

⚠️ **WARNING**: This cannot be undone! Once published, you cannot:
- Delete the release
- Reuse the version number
- Modify the uploaded files

### 4.1 Final Pre-flight Checks

```bash
# Verify version in pyproject.toml
grep "version" pyproject.toml

# Verify all tests pass
pytest

# Verify README renders correctly
python -m readme_renderer README.md

# Check for security issues (optional)
pip install safety
safety check
```

### 4.2 Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# If successful, you'll see:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading method_crm_mcp-1.0.0-py3-none-any.whl
# Uploading method-crm-mcp-1.0.0.tar.gz
# View at: https://pypi.org/project/method-crm-mcp/1.0.0/
```

### 4.3 Verify Installation

```bash
# Create clean environment
python -m venv verify_env
source verify_env/bin/activate

# Install from PyPI
pip install method-crm-mcp

# Verify it works
python -c "from method_mcp.server import mcp; print('✓ Published successfully!')"

# Cleanup
deactivate
rm -rf verify_env
```

### 4.4 View on PyPI

Visit: https://pypi.org/project/method-crm-mcp/

## Step 5: Post-Publication Tasks

### 5.1 Create Git Tag

```bash
# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0 - Published to PyPI"
git push origin v1.0.0
```

### 5.2 Update GitHub Release

Add PyPI installation instructions to GitHub release:
```bash
gh release edit v1.0.0 --notes-file - <<EOF
# Installation

\`\`\`bash
pip install method-crm-mcp
\`\`\`

[View on PyPI](https://pypi.org/project/method-crm-mcp/)

[Rest of release notes...]
EOF
```

### 5.3 Update Documentation

Update README.md installation section:
```markdown
## Installation

### From PyPI (Recommended)

\`\`\`bash
pip install method-crm-mcp
\`\`\`

### From Source

\`\`\`bash
git clone https://github.com/avisangle/method-crm-mcp.git
cd method-crm-mcp
pip install -e .
\`\`\`
```

### 5.4 Announce the Release

- Tweet about the release
- Post in relevant Reddit communities (r/Python, r/programming)
- Share in Discord/Slack communities
- Update MCP servers registry
- Post in Method CRM community forums

## Troubleshooting

### Error: "File already exists"

You tried to upload a version that already exists. You must:
1. Increment version number in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload again: `twine upload dist/*`

### Error: "Invalid credentials"

Check your `~/.pypirc` token or use command line:
```bash
twine upload --username __token__ --password pypi-YOUR-TOKEN-HERE dist/*
```

### Error: "403 Forbidden"

You don't have permissions. Possible causes:
- Wrong API token
- Token doesn't have upload permissions
- Package name already taken by someone else

### Package Name Already Taken

Choose a different name in `pyproject.toml`:
```toml
name = "method-crm-mcp-avisangle"  # Add your username
```

## Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/):
- **1.0.0** → **1.0.1**: Bug fixes (patch)
- **1.0.0** → **1.1.0**: New features (minor)
- **1.0.0** → **2.0.0**: Breaking changes (major)

### Release Process

For each new release:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (create if needed)
3. Clean old builds: `rm -rf dist/`
4. Build: `python -m build`
5. Test on TestPyPI
6. Upload to PyPI
7. Tag in git: `git tag v1.x.x`
8. Push tag: `git push origin v1.x.x`
9. Create GitHub release

## Security Best Practices

1. **Never commit** `.pypirc` or API tokens to git
2. **Use API tokens**, not passwords
3. **Enable 2FA** on PyPI account
4. **Rotate tokens** periodically (every 6-12 months)
5. **Use environment variables** for CI/CD:
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-YOUR-TOKEN
   twine upload dist/*
   ```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
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

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Resources

- PyPI Documentation: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- Setuptools Documentation: https://setuptools.pypa.io/
- Python Packaging Guide: https://packaging.python.org/tutorials/packaging-projects/

## Support

If you encounter issues:
1. Check [PyPI Help](https://pypi.org/help/)
2. Search [Python Packaging Discussions](https://discuss.python.org/c/packaging/)
3. Open an issue in this repository

---

**Good luck with your PyPI publication! 🚀**
