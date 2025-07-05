# rut - Run Unit Tests

`rut` (run unit tests) is a test runner for Python's `unittest` framework.

## Features

- Built-in support for async code.
- Test discovery with keyword-based filtering.
- Code coverage support.

## Installation

Add `rut` as a development dependency to your project:

```bash
uv add --dev rut
```

## Usage

```bash
rut [options] [path]
```

### Example

To run all tests in the `tests/` directory that have the word "feature" in their name, you would run:

```bash
rut -k "feature"
```

### Options

| Option | Short | Description |
|---|---|---|
| `--keyword` | `-k` | Only run tests that match the given keyword. |
| `--exitfirst` | `-x` | Exit on the first failure. |
| `--capture` | `-s` | Disable all output capturing. |
| `--cov` | | Run with code coverage. |

### Positional Arguments

| Argument | Description | Default |
|---|---|---|
| `path` | The path to the tests to be discovered. | `tests` |

## Writing Tests

### Basic Tests

For standard, synchronous tests, you can use the standard `unittest.TestCase`.

```python
import unittest

class MyTest(unittest.TestCase):
    def test_something(self):
        self.assertEqual(1 + 1, 2)
```

### Async Tests

To write an asynchronous test, you must use `unittest.IsolatedAsyncioTestCase` as the base class for your test case. `rut` will automatically detect and correctly run `async def` test methods within these classes.

```python
import asyncio
import unittest

class MyAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_something_async(self):
        await asyncio.sleep(0.01)
        self.assertTrue(True)
```

## Advanced

### Detecting rut

When `rut` is running, it sets the environment variable `TEST_RUNNER` to the value `rut`. You can use this in your test code to enable or disable functionality that is specific to the test runner.

```python
import os

if os.environ.get('TEST_RUNNER') == 'rut':
    # Do something specific to rut
    pass
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.