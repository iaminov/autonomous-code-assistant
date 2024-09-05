# Contributing to Autonomous Code Assistant

Thank you for your interest in contributing to the Autonomous Code Assistant! This document provides guidelines and information for contributors.

## Development Setup

1. Fork the repository and clone your fork:
```bash
git clone https://github.com/yourusername/autonomous-code-assistant.git
cd autonomous-code-assistant
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

1. Create a new branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following the code style guidelines below.

3. Run tests to ensure everything works:
```bash
pytest
```

4. Run code quality checks:
```bash
black src tests
isort src tests
flake8 src tests
mypy src/autonomous_code_assistant
```

5. Commit your changes with a descriptive commit message:
```bash
git commit -m "feat: add new feature description"
```

6. Push to your fork and submit a pull request.

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep line length to 88 characters (Black default)
- Use meaningful variable and function names

## Commit Message Format

Use the conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

## Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting a PR
- Aim for high test coverage
- Use pytest fixtures for common test setup

## Documentation

- Update the README.md if you add new features
- Add docstrings to all public functions and classes
- Include usage examples for new functionality

## Issues and Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Full error messages and stack traces

## Feature Requests

For feature requests, please:
- Check if the feature already exists or is planned
- Provide a clear use case for the feature
- Suggest implementation approaches if possible

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose. Reviewers will check for:
- Code quality and style
- Test coverage
- Documentation
- Backward compatibility
- Performance implications

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the "question" label
- Contact the maintainer at alexeaminov@gmail.com

Thank you for contributing!
