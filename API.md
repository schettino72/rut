# API Reference

This document describes the public API of rut. These are the classes and functions you can import and use in your code.

## Command Line Interface

### Main Entry Point

```bash
rut [options] [path]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | | Show version and exit |
| `--keyword KEYWORD` | `-k` | Only run tests matching the keyword |
| `--exitfirst` | `-x` | Exit on first failure |
| `--capture` | `-s` | Disable output capturing |
| `--cov` | | Run with code coverage |
| `--test-base-dir DIR` | | Base directory for conftest.py discovery |
| `--no-color` | | Disable color output |

#### Positional Arguments

- `path`: Path to tests directory (default: `tests`)

## Python API

### RutRunner

The core test runner class.

```python
from rutlib import RutRunner

runner = RutRunner(
    test_path="tests",
    test_base_dir="tests",
    keyword=None,
    failfast=False,
    capture=False,
    warning_filters=[]
)

suite = runner.load_tests(pattern="test*.py")
result = runner.run_tests(suite)
```

#### Constructor Parameters

- **test_path** (`str`): Path to discover tests from
- **test_base_dir** (`str`): Base directory for conftest.py discovery
- **keyword** (`Optional[str]`): Filter tests by keyword
- **failfast** (`bool`): Stop on first failure
- **capture** (`bool`): Whether to capture test output
- **warning_filters** (`List[Dict[str, Any]]`): Custom warning filters

#### Methods

##### `load_tests(pattern="test*.py") -> unittest.TestSuite`

Load and discover tests from the test path.

**Parameters:**
- `pattern` (`str`): File pattern for test discovery (default: "test*.py")

**Returns:**
- `unittest.TestSuite`: Test suite with sorted and filtered tests

##### `run_tests(suite, runner_class=None) -> unittest.TestResult`

Run the test suite with session hooks.

**Parameters:**
- `suite` (`unittest.TestSuite`): Test suite to run
- `runner_class` (`Optional[type]`): Custom test runner class

**Returns:**
- `unittest.TestResult`: Test result object

### RutCLI

Command-line interface handler.

```python
from rutlib import RutCLI

cli = RutCLI()
# Access parsed arguments
print(cli.args.keyword)
print(cli.test_base_dir)
print(cli.coverage_source)
```

#### Properties

##### `test_base_dir -> str`

Get the base directory for test discovery.

##### `coverage_source -> List[str]`

Get the coverage source directories from configuration.

#### Methods

##### `load_config() -> Dict[str, Any]`

Load configuration from pyproject.toml.

**Returns:**
- `Dict[str, Any]`: Configuration from [tool.rut] section

##### `warning_filters(filters_spec) -> List[Dict[str, Any]]`

Parse warning filters from configuration.

**Parameters:**
- `filters_spec` (`List[str]`): List of filter specification strings

**Returns:**
- `List[Dict[str, Any]]`: Parsed filter dictionaries

### WarningCollector

Collects and reports warnings during test execution.

```python
from rutlib import WarningCollector

wc = WarningCollector()
wc.setup(extra=[])
# ... run tests ...
wc.print_warnings()
wc.cleanup()
```

#### Methods

##### `setup(extra) -> None`

Set up warning collection with custom filters.

**Parameters:**
- `extra` (`List[Dict[str, Any]]`): Custom warning filter specifications

##### `cleanup() -> None`

Clean up and restore original warning settings.

##### `print_warnings() -> None`

Print all collected warnings in a formatted panel.

### Exceptions

#### RutError

Base exception for the rut runner.

```python
from rutlib import RutError

try:
    # ... rut operations ...
except RutError as e:
    print(f"Rut error: {e}")
```

#### InvalidAsyncTestError

Raised when an async test method is not in an IsolatedAsyncioTestCase.

```python
from rutlib import InvalidAsyncTestError

try:
    runner.load_tests()
except InvalidAsyncTestError as e:
    print(f"Invalid async test: {e}")
```

## Configuration File

Configuration via `pyproject.toml` in the `[tool.rut]` section.

### Example Configuration

```toml
[tool.rut]
# Coverage source directories
coverage_source = ["src", "lib"]

# Test base directory for conftest.py
test_base_dir = "tests"

# Warning filters
warning_filters = [
    "error::UserWarning:my_module",
    "ignore::DeprecationWarning",
]
```

### Configuration Options

#### `coverage_source`

**Type:** `List[str]`  
**Default:** `["src", "tests"]`

Directories to measure coverage for.

#### `test_base_dir`

**Type:** `str`  
**Default:** `"tests"`

Base directory for conftest.py discovery.

#### `warning_filters`

**Type:** `List[str]`  
**Default:** `[]`

Warning filter specifications in the format: `"action:message:category:module"`

**Actions:** `error`, `ignore`, `always`, `default`, `module`, `once`

## Hooks

Define these functions in `conftest.py` in your test base directory.

### `rut_session_setup()`

Called once before the test session starts.

```python
# conftest.py
def rut_session_setup():
    """Run before any tests."""
    print("Setting up test session")

# Or async version
async def rut_session_setup():
    """Run before any tests."""
    await setup_database()
```

### `rut_session_teardown()`

Called once after all tests complete, even if tests fail.

```python
# conftest.py
def rut_session_teardown():
    """Run after all tests."""
    print("Tearing down test session")

# Or async version
async def rut_session_teardown():
    """Run after all tests."""
    await cleanup_database()
```

## Environment Variables

### `TEST_RUNNER`

Set to `"rut"` when running under rut. Use this to detect when your code is being run by rut.

```python
import os

if os.environ.get('TEST_RUNNER') == 'rut':
    # Running under rut
    pass
```

## Rich Test Runner

The `RichTestRunner` provides colorized output. It's used automatically unless `--no-color` is specified.

```python
from rutlib.cli import RichTestRunner

runner = RichTestRunner(failfast=False, buffer=True)
result = runner.run(suite)
```

### Constructor Parameters

- **failfast** (`bool`): Stop on first failure
- **buffer** (`bool`): Buffer test output

## Version Information

```python
from rutlib import __version__

print(f"rut version: {__version__}")
```

## Type Hints

All public APIs include comprehensive type hints. Use a type checker like `mypy` or `pyright` for static type checking:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rutlib import RutRunner
    
    runner: RutRunner = ...
```
