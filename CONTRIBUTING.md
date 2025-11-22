# Contributing to Method CRM MCP Server

Thank you for your interest in contributing to the Method CRM MCP Server! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/method-crm-mcp.git
   cd method-crm-mcp
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-webhook-support`
- `bugfix/fix-pagination-error`
- `docs/update-installation-guide`

### 2. Make Your Changes

- Write clear, concise code following existing patterns
- Add docstrings to all functions and classes
- Include type hints for all parameters and return values
- Follow PEP 8 style guidelines

### 3. Add Tests

- Add tests for all new features in the `tests/` directory
- Ensure all tests pass:
  ```bash
  pytest
  ```
- Aim for high test coverage:
  ```bash
  pytest --cov=src/method_mcp --cov-report=html
  ```

### 4. Run Code Quality Checks

```bash
# Type checking
mypy src/method_mcp

# Linting
ruff check src/method_mcp

# Formatting
black src/method_mcp
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git commit -m "feat: add webhook support for event routines"
```

Follow conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or modifications
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to any related issues
- Screenshots/examples if applicable
- Test results

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints everywhere
- Maximum line length: 100 characters
- Use descriptive variable names

### Documentation

- Add docstrings to all public functions/classes
- Use Google-style docstrings format:
  ```python
  def example_function(param1: str, param2: int) -> bool:
      """
      Brief description of function.

      Args:
          param1: Description of param1
          param2: Description of param2

      Returns:
          Description of return value

      Raises:
          ValueError: When param2 is negative
      """
      pass
  ```

### Error Handling

- Use custom exceptions from `errors.py`
- Provide actionable error messages
- Include suggestions for resolving errors

### Testing

- Write unit tests for all new functions
- Write integration tests for API interactions
- Use pytest fixtures for common setup
- Mock external API calls in unit tests

## Project Structure

```
src/method_mcp/
├── server.py           # FastMCP server initialization
├── client.py           # HTTP client with retry logic
├── auth.py             # Authentication handlers
├── models.py           # Pydantic models
├── errors.py           # Error handling utilities
├── utils.py            # Shared helper functions
└── tools/              # Tool implementations
    ├── tables.py       # Table operations
    ├── files.py        # File management
    ├── user.py         # User information
    ├── events.py       # Event automation
    └── apikeys.py      # API key management
```

## Adding New Tools

1. **Define the Pydantic model** in `models.py`:
   ```python
   class NewToolInput(BaseModel):
       """Input model for new tool."""
       param1: str = Field(..., description="Parameter description")
       response_format: ResponseFormat = ResponseFormat.JSON

       model_config = ConfigDict(str_strip_whitespace=True)
   ```

2. **Implement the tool** in appropriate file under `tools/`:
   ```python
   @mcp.tool(
       readOnlyHint=True,
       destructiveHint=False,
       idempotentHint=True
   )
   async def method_new_tool(params: NewToolInput) -> str:
       """
       Tool description.

       Comprehensive docstring with examples...
       """
       # Implementation
   ```

3. **Add tests** in `tests/`:
   ```python
   async def test_new_tool():
       """Test new tool functionality."""
       # Test implementation
   ```

4. **Update documentation**:
   - Add tool to README.md tool list
   - Update tool count
   - Add usage examples

## Reporting Issues

When reporting issues, please include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details**:
   - Python version
   - Operating system
   - Method CRM account type
   - MCP server version
5. **Error messages** (full stack traces)
6. **Code samples** demonstrating the issue

## Feature Requests

For feature requests, please include:

1. **Use case** - Why is this feature needed?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - What other approaches did you consider?
4. **Impact** - Who benefits from this feature?

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help create a welcoming community

## Questions?

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check https://developer.method.me/

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
