---
name: rut-testing
description: Use rut test runner instead of pytest for running Python unittest tests.
allowed-tools: Bash(rut:*)
---

# RUT Test Runner

Use `rut` instead of `pytest` for running tests in this project.

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--keyword` | `-k` | Only run tests matching keyword |
| `--exitfirst` | `-x` | Exit on first failure |
| `--capture` | `-s` | Disable output capturing (show prints) |
| `--changed` | `-c` | Only run tests affected by file changes |
| `--dry-run` | | List tests without running them |
| `--verbose` | `-v` | Show import dependency ranking |
| `--cov` | | Run with code coverage |
| `--alpha` | `-a` | Sort tests alphabetically |
| `--version` | `-V` | Show version and exit |
| `--test-base-dir` | | Base directory for conftest.py discovery |
| `path` | | Path to tests (default: `tests`) |

## Running Tests Workflow

1. Run specific test: `rut -k "test_feature_name"`
2. On failure, use `-x` to stop at first failure: `rut -x -k "test_feature_name"`
3. Run linters: `ruff check` and `import_deps --check` (if available)
4. Run full suite: `rut --changed`
5. Debug with `-s` to see print output: `rut -s -k "failing_test"`

## Writing Tests Principles

- Don't change app code and tests simultaneously - change one at a time
- Follow TDD - make tests fail first, then make them pass
- Don't mock the database - only mock external services requiring internet
- No for-loops or if-clauses in tests - tests should be linear and explicit
- Goal: exercise code, test complex logic, fix bugs (not 100% coverage)

## Quick Reference

- Tests use `unittest.TestCase` (sync) or `unittest.IsolatedAsyncioTestCase` (async)
- Cache stored in `.rut_cache/` - updated only after successful runs
- For configuration, conftest hooks, and examples, see [REFERENCE.md](REFERENCE.md)
