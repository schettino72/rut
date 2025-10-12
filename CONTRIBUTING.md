# Contributing to rut

Thank you for your interest in contributing to rut! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/schettino72/rut.git
   cd rut
   ```

2. Install dependencies using uv:
   ```bash
   uv sync --dev
   ```

3. Run tests to ensure everything is working:
   ```bash
   ./run_tests.sh
   ```

## Running Tests

### Using the test script
```bash
./run_tests.sh
```

### With coverage
```bash
./run_tests.sh --cov
```

### Using rut itself
```bash
export PYTHONPATH=src
python3 -m rutlib
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and code formatting.

### Run the linter
```bash
uv run ruff check .
```

### Auto-fix issues
```bash
uv run ruff check --fix .
```

## Type Checking

We use type hints throughout the codebase. While we don't currently enforce type checking in CI, please add type hints to any new code.

## Pull Request Process

1. **Fork the repository** and create your branch from `main`.

2. **Make your changes**:
   - Follow existing code style and conventions
   - Add type hints to new functions and methods
   - Add docstrings to public APIs
   - Keep changes focused and minimal

3. **Add tests** for any new functionality or bug fixes.

4. **Run the test suite** and ensure all tests pass:
   ```bash
   ./run_tests.sh
   ```

5. **Run the linter** and fix any issues:
   ```bash
   uv run ruff check .
   ```

6. **Update documentation** if needed:
   - Update README.md for user-facing changes
   - Update CHANGES file with a description of your changes
   - Add docstrings for new public APIs

7. **Submit your pull request**:
   - Provide a clear description of the changes
   - Reference any related issues
   - Explain why the change is needed

## Reporting Bugs

When reporting bugs, please include:

1. **rut version**: Run `rut --version`
2. **Python version**: Run `python --version`
3. **Operating system**
4. **Steps to reproduce** the issue
5. **Expected behavior**
6. **Actual behavior**
7. **Minimal code example** if applicable

## Suggesting Features

Feature suggestions are welcome! Please:

1. Check if the feature has already been requested
2. Explain the use case and why it would be valuable
3. Consider whether it aligns with rut's goal of simplicity
4. Be open to discussion about implementation details

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or insults
- Publishing others' private information
- Other conduct that would be inappropriate in a professional setting

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for discussion
- Reach out to the maintainers

Thank you for contributing to rut!
