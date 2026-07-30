---
layout: article
title: "Usage"
description: "Installation, CLI options, configuration, and writing tests with rut."
date: 2026-02-11
---

## Installation

Add <span class="rut">rut</span> as a development dependency:

```bash
uv add --dev rut
```

Or with pip:

```bash
pip install rut
```

## Writing tests

### Basic tests

Standard `unittest.TestCase` — nothing special needed.

```python
import unittest

class MyTest(unittest.TestCase):
    def test_something(self):
        self.assertEqual(1 + 1, 2)
```

### Async tests

Use `unittest.IsolatedAsyncioTestCase` as the base class. <span class="rut">rut</span> automatically detects and runs `async def` test methods.

```python
import asyncio
import unittest

class MyAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_something_async(self):
        await asyncio.sleep(0.01)
        self.assertTrue(True)
```

## Running tests

```bash
rut [options] [path]
```

By default, <span class="rut">rut</span> discovers and runs all tests in the `tests/` directory. Tests are ordered by import dependencies — foundational modules first.

```bash
rut                      # run all tests
rut --changed            # only tests affected by your changes
rut -k "auth"            # filter by keyword
rut -x                   # stop on first failure
rut --cov                # with coverage report
rut --dry-run            # list tests without running
rut tests/test_api.py    # run specific path
```

## Configuration

<span class="rut">rut</span> is configured via the `[tool.rut]` section in `pyproject.toml`.

<span class="rut">rut</span> looks for `pyproject.toml` in the current directory. If cwd is `tests/`, it also checks the parent directory and changes to it if found.

Without `pyproject.toml`, <span class="rut">rut</span> runs in ad-hoc mode with `test_dir=.` and `source_dirs=["."]`.

### `source_dirs`

Directories to scan for coverage, incremental testing (`--changed`), and import dependency analysis. Default: `["src", "tests"]`. Validated only when `--cov` or `--changed` is used.

```toml
[tool.rut]
source_dirs = ["my_app", "libs/my_lib"]
```

### `warning_filters`

Custom warning filters in `warnings.filterwarnings` format: `action:message:category:module`.

```toml
[tool.rut]
warning_filters = [
    "error::UserWarning:pydantic",
]
```

### `test_base_dir`

Base directory for `conftest.py` discovery.

```toml
[tool.rut]
test_base_dir = "my_tests"
```

## Session hooks

Create a `conftest.py` in your test base directory (usually `tests/`) to run setup/teardown once per session.

- `rut_session_setup()` — runs before any tests
- `rut_session_teardown()` — runs after all tests, even on failure

Both can be sync or async.

```python
# tests/conftest.py
from my_app.database import connect_db, disconnect_db

async def rut_session_setup():
    await connect_db()

async def rut_session_teardown():
    await disconnect_db()
```

## CLI reference

| Option | Short | Description |
|---|---|---|
| `--keyword` | `-k` | Only run tests that match the given keyword. |
| `--exitfirst` | `-x` | Exit on the first failure. |
| `--capture` | `-s` | Disable all output capturing. |
| `--alpha` | `-a` | Sort tests alphabetically instead of by import dependencies. |
| `--changed` | `-c` | Only run tests affected by file changes since last successful run. |
| `--dry-run` | | List tests in execution order without running them. |
| `--verbose` | `-v` | Show test names instead of dots. |
| `--cov` | | Run with code coverage. |
| `--no-color` | | Disable colored output. |
| `--debug` | | Show dependency graph and changed modules. |
| `--version` | `-V` | Show version and exit. |
| `--test-base-dir` | | The base directory for `conftest.py` discovery. |

| Argument | Description | Default |
|---|---|---|
| `path` | Path to test file or directory to run. Does not affect project config. | discover all in test_dir |

## Detecting rut

<span class="rut">rut</span> sets the environment variable `TEST_RUNNER=rut` during execution.

```python
import os

if os.environ.get('TEST_RUNNER') == 'rut':
    # rut-specific behavior
    pass
```

## Claude Code plugin

A [Claude Code](https://claude.com/claude-code) plugin is included for AI-assisted testing workflows.

```
/plugin marketplace add schettino72/rut
/plugin install rut-testing@rut
```
