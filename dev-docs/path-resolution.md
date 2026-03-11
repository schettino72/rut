# Path Resolution

## Config discovery

Rut looks for `pyproject.toml` in the current working directory.
Special case: if cwd is named `tests/`, also checks the parent directory.
If found in a parent, rut changes cwd to that directory.
If not found, defaults to ad-hoc mode (`test_dir=.`, `source_dirs=["."]`).

## sys.path

Rut adds the package root to `sys.path`. If cwd contains `__init__.py`, it walks up
parent directories until it finds one without `__init__.py`, and adds that to `sys.path`.
This ensures packages are importable when running from inside a package directory.

## test_dir (project config)

Where rut looks for tests and conftest.py. Resolution order:

1. CLI option: `--test-base-dir <path>` (relative to cwd)
2. Config: `[tool.rut] test_base_dir = "..."` (relative to project root)
3. Default: `"tests"` (with config) or `"."` (without config)

Always validated — error if directory doesn't exist.
**Not affected by positional argument.**


## source_dirs (project config)

Where rut looks for source files (import analysis, coverage, `--changed`). Resolution order:

1. Config: `[tool.rut] source_dirs = [...]` (relative to project root)
2. Default: `["src", "tests"]` (with config) or `["."]` (without config)

Validated lazily — error only when `--cov` or `--changed` is used with invalid directories.
**Not affected by positional argument.**


## Positional argument (test selector)

Selects which tests to run. Does not change test_dir or source_dirs.

- Not given → discover all tests in test_dir
- Directory → discover tests in that directory
- File → discover only that file


## Scenarios

### Standard project (from project root)

```
myproject/
  pyproject.toml    # [tool.rut] source_dirs = ["src", "tests"]
  src/
  tests/
```

| Command                       | test_dir | source_dirs        | Discovers             |
|-------------------------------|----------|--------------------|-----------------------|
| `rut`                         | tests    | [src, tests]       | all tests in tests/   |
| `rut tests/test_foo.py`       | tests    | [src, tests]       | only test_foo.py      |
| `rut tests/subdir/`           | tests    | [src, tests]       | tests in subdir/      |

### Running from test directory

```
myproject/
  pyproject.toml    # [tool.rut] source_dirs = ["src", "tests"]
  src/
  tests/            # cwd
```

| Command                       | Result |
|-------------------------------|--------|
| `cd tests && rut test_foo.py` | finds parent pyproject.toml, chdir to myproject/, runs test_foo.py |
| `cd tests && rut`             | finds parent pyproject.toml, chdir to myproject/, discovers all tests |

### Ad-hoc tests (no pyproject.toml)

```
manual_tests/
  __init__.py
  test_foo.py
  test_incremental/
    __init__.py
    test_main.py
```

| Command                            | test_dir | source_dirs | Discovers        |
|------------------------------------|----------|-------------|------------------|
| `cd manual_tests && rut`           | .        | [.]         | all tests in ./  |
| `cd manual_tests && rut test_foo.py` | .      | [.]         | only test_foo.py |
| `cd manual_tests && rut test_incremental/` | . | [.]       | tests in test_incremental/ |

No pyproject.toml found — defaults to cwd. If cwd is inside a package (`__init__.py` exists),
`sys.path` is set to the package root parent so imports work correctly.

### Custom test directory

```
myproject/
  pyproject.toml    # [tool.rut] test_base_dir = "test_suite"
  src/
  test_suite/
```

| Command                       | test_dir    | Discovers                 |
|-------------------------------|-------------|---------------------------|
| `rut`                         | test_suite  | all tests in test_suite/  |

### --test-base-dir override

| Command                               | test_dir            |
|----------------------------------------|---------------------|
| `rut --test-base-dir integration_tests` | integration_tests  |

### Flat layout (no src/)

```
myproject/
  pyproject.toml    # no [tool.rut] section
  mypackage/
  tests/
```

| Command | Result |
|---------|--------|
| `rut`   | runs tests (source_dirs defaults invalid but no error unless --cov/--changed) |
| `rut --cov` | Error: source directories do not exist: src |

Fix: add `[tool.rut] source_dirs = ["mypackage", "tests"]` to pyproject.toml.
