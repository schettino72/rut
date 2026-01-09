---
name: rut-testing
description: Use rut test runner instead of pytest for running Python unittest tests.
allowed-tools: Bash(uv run rut:*)
---

# RUT Test Runner

This project uses `rut` - a modern test runner for Python's unittest framework.

## Running Tests

- Run all tests: `uv run rut`
- Run specific path: `uv run rut tests/test_foo.py`
- Run tests matching keyword: `uv run rut -k "test_feature"`

## Key Flags

| Flag | Description |
|------|-------------|
| `-k KEYWORD` | Only run tests matching keyword |
| `-x` | Exit on first failure |
| `-s` | Disable output capturing (show prints) |
| `-c` / `--changed` | Only run tests affected by file changes since last successful run |
| `--dry-run` | List tests without running them |
| `-v` / `--verbose` | Show import dependency ranking |
| `--cov` | Run with code coverage |
| `-a` / `--alpha` | Sort tests alphabetically (default is by import dependencies) |

## Incremental Testing (--changed)

The `--changed` flag is powerful for fast iteration:
- Only runs tests whose files changed OR whose dependencies changed
- Tracks file hashes in `.rut_cache/`
- Cache updates only after successful runs

Examples:
- `uv run rut` - first run builds the cache
- `uv run rut --changed` - only test what changed
- `uv run rut -c --dry-run` - see what would run

## Important

- Use `uv run rut` instead of `pytest`
- Tests use standard `unittest.TestCase`
- Async tests use `unittest.IsolatedAsyncioTestCase`
