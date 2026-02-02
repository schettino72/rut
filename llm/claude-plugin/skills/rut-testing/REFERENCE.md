# RUT Reference

Detailed configuration, examples, and advanced features.

## Installation

```bash
uv add --dev rut
```

## Configuration

Configure via `[tool.rut]` section in `pyproject.toml`.

### source_dirs

Source directories for coverage, incremental testing, and import analysis. Default: `["src", "tests"]`.

```toml
[tool.rut]
source_dirs = ["my_app", "libs/my_lib"]
```

### warning_filters

Custom warning filters using `warnings.filterwarnings` format: `action:message:category:module`.

```toml
[tool.rut]
warning_filters = [
    "error::UserWarning:pydantic",
]
```

### test_base_dir

Base directory for `conftest.py` discovery.

```toml
[tool.rut]
test_base_dir = "my_tests"
```

## Writing Tests

### Basic Tests

```python
import unittest

class MyTest(unittest.TestCase):
    def test_something(self):
        self.assertEqual(1 + 1, 2)
```

### Async Tests

Use `unittest.IsolatedAsyncioTestCase` for async tests.

```python
import asyncio
import unittest

class MyAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_something_async(self):
        await asyncio.sleep(0.01)
        self.assertTrue(True)
```

## Incremental Testing

The `--changed` flag runs only tests affected by file changes since last successful run. This includes tests whose source files changed and tests that depend on changed modules (transitive dependencies).

```bash
rut           # First run builds the cache
rut --changed # Only run affected tests
rut -c --dry-run # Preview what would run
```

Cache stored in `.rut_cache/`, updated only after successful runs.

**Note:** Files must be in directories listed in `source_dirs` to be tracked.

## Session Hooks (conftest.py)

Create `conftest.py` in your test base directory for session-level setup/teardown.

```python
# tests/conftest.py
from my_app.database import connect_db, disconnect_db

async def rut_session_setup():
    print("Setting up the test database...")
    await connect_db()

async def rut_session_teardown():
    print("Tearing down the test database...")
    await disconnect_db()
```

Both functions can be sync (`def`) or async (`async def`).

## Detecting rut

`rut` sets `TEST_RUNNER=rut` environment variable when running.

```python
import os

if os.environ.get('TEST_RUNNER') == 'rut':
    # rut-specific behavior
    pass
```
