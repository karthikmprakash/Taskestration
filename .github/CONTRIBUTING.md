# Contributing to Automation Control Panel

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Be open to different perspectives

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/automations.git
   cd automations
   ```
3. **Set up the development environment**:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Branch

Create a branch from `main` for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Run Checks Locally

Before submitting, ensure all checks pass:

```bash
# Run all checks (recommended)
./run_checks.sh

# Or individually:
uv run ruff format .      # Format code
uv run ruff check .       # Check linting
uv run mypy src scripts   # Type checking
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.
```

### 5. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub using the PR template.

## Code Style

- Follow PEP 8 style guide
- Use `ruff` for formatting and linting (configuration in `pyproject.toml`)
- Maximum line length: 100 characters
- Use type hints where appropriate
- Use descriptive variable and function names

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Test edge cases and error conditions
- Update tests when fixing bugs

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Update CHANGELOG.md for user-facing changes
- Keep code comments up-to-date

## Pull Request Process

1. **Fill out the PR template** completely
2. **Reference related issues** using `Closes #issue_number`
3. **Ensure all CI checks pass**
4. **Request review** from maintainers
5. **Respond to feedback** and make requested changes
6. **Squash commits** if requested before merging

## Issue Reporting

When reporting bugs:

- Use the bug report template
- Provide clear steps to reproduce
- Include error messages and logs
- Specify your environment (OS, Python version, etc.)

When requesting features:

- Use the feature request template
- Explain the use case and motivation
- Describe the expected behavior

## Questions?

- Open a Discussion for questions
- Check existing issues before creating new ones
- Be patient and respectful with maintainers

Thank you for contributing! 🎉
