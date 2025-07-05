# rut - Run Unit Tests

`rut` is a modern and fully-featured test runner for Python's `unittest` framework, with simplicity as a core design goal.

## Features

- Built-in support for async code.
- Test discovery with keyword-based filtering.
- Code coverage support.

## Why use `rut`?

### For the `unittest` User: A Modern Upgrade

Are you a fan of the stability and explicitness of `unittest`, but wish you had a better runner experience? `rut` is your drop-in upgrade.

*   **Zero-Config Discovery:** Just run `rut`. No more writing `if __name__ == '__main__':` boilerplate.
*   **First-Class `asyncio` Support:** `rut` automatically detects and runs `async` tests correctly. No more `asyncio.run()` wrappers.
*   **Powerful Filtering:** Run exactly the tests you want with simple keyword filtering (`-k "my_feature"`).
*   **Integrated Coverage:** Get a full coverage report with a single flag (`--cov`).

### For the `pytest` User: Simplicity and Power, Reunited

Do you appreciate the power of modern test runners, but find yourself wrestling with the complexity and "magic" of third-party frameworks? `rut` offers a compelling alternative, embracing the explicitness of the standard library.

*   **No Magic, Just Python:** `rut` is built directly on `unittest`. There are no hidden hooks, complex fixture systems, or assertion rewriting. Your tests are plain, debuggable Python.
*   **Familiar, Powerful Features:** Get the features you rely on, like keyword filtering (`-k`), failing fast (`-x`), and seamless `asyncio` support, without the overhead of a large framework.
*   **A Leaner Dependency Tree:** `rut` is a single, focused tool, not a sprawling ecosystem. Keep your project's dependencies clean and understandable.

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

## Configuration

`rut` can be configured via the `[tool.rut]` section in your `pyproject.toml` file. If not configured, the default source is `["src", "tests"]`.

### `coverage_source`

To specify the source directories for coverage reporting, use the `coverage_source` key.

```toml
[tool.rut]
coverage_source = ["my_app", "libs/my_lib"]
```

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
