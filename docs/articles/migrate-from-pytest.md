---
layout: article
title: "Migrating from pytest to rut"
description: "A practical guide for converting a pytest test suite to rut, with step-by-step instructions and an AI-agent-friendly version."
date: 2026-02-11
---

A practical guide for converting a pytest test suite to <span class="rut">rut</span>, a test runner for Python's standard `unittest` framework.

This guide was written during the migration of the [doit](https://pydoit.org) project (~545 tests, 27 test files) from pytest to <span class="rut">rut</span>.

<div class="feature-card">
  <div class="feature-header">
    <h3 class="feature-title">AI Agent Instructions</h3>
  </div>
  <p class="feature-desc">Using an AI coding agent? Download the <a href="{{ '/assets/migrate-pytest-to-rut.md' | relative_url }}">plain-text migration instructions</a> and include them in your prompt or project context. The file is structured for LLM consumption with all conversion rules in a compact format.</p>
</div>


## Strategy

We recommend a **parallel test folder** approach rather than converting files in-place:

1. Create a new `tests_rut/` folder alongside the existing `tests/`
2. Convert one test module at a time into `tests_rut/`
3. Run both suites during the transition (`py.test tests/` and `rut tests_rut/`)
4. Once coverage parity is reached, delete `tests/` and rename `tests_rut/` to `tests/`

This keeps the original suite as a safety net throughout the migration.


## Test classes

pytest allows test classes that inherit from `object` (or nothing). <span class="rut">rut</span> requires `unittest.TestCase`.

```python
# pytest
class TestFoo(object):
    def test_bar(self):
        ...

# rut
import unittest

class TestFoo(unittest.TestCase):
    def test_bar(self):
        ...
```


## Assertions

pytest relies on plain `assert` statements with magic introspection for failure messages. With `unittest.TestCase`, use the `self.assert*` methods — they provide clear failure messages without magic.

```python
# pytest                          # rut
assert x == y                     self.assertEqual(x, y)
assert x != y                     self.assertNotEqual(x, y)
assert x in collection            self.assertIn(x, collection)
assert x not in collection        self.assertNotIn(x, collection)
assert x is None                  self.assertIsNone(x)
assert x is not None              self.assertIsNotNone(x)
assert x  # truthy                self.assertTrue(x)
assert not x  # falsy             self.assertFalse(x)
assert isinstance(x, MyClass)     self.assertIsInstance(x, MyClass)
```

Less common but useful:

```python
# pytest                          # rut
assert abs(x - y) < tolerance     self.assertAlmostEqual(x, y, places=5)
assert x > y                      self.assertGreater(x, y)
                                   self.assertGreaterEqual(x, y)
                                   self.assertLess(x, y)
                                   self.assertLessEqual(x, y)
```


## Expecting exceptions

```python
# pytest — inline call
pytest.raises(ValueError, int, "not_a_number")

# rut — inline call
self.assertRaises(ValueError, int, "not_a_number")
```

```python
# pytest — context manager (inspect the exception)
with pytest.raises(ValueError) as exc_info:
    int("not_a_number")
assert "invalid literal" in str(exc_info.value)

# rut — context manager
with self.assertRaises(ValueError) as cm:
    int("not_a_number")
self.assertIn("invalid literal", str(cm.exception))
```

Note: pytest uses `.value`, unittest uses `.exception`.


## Fixtures → setUp / tearDown

pytest fixtures are the biggest migration effort. They map to `setUp`/`tearDown` methods.

### Simple fixture (per-test setup)

```python
# pytest
class TestDB(object):
    @pytest.fixture
    def db(self, request):
        conn = create_connection()
        request.addfinalizer(conn.close)
        return conn

    def test_query(self, db):
        result = db.execute("SELECT 1")
        assert result == 1

# rut
class TestDB(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.db = create_connection()
        self.addCleanup(self.db.close)

    def test_query(self):
        result = self.db.execute("SELECT 1")
        self.assertEqual(result, 1)
```

Key differences:
- The fixture return value becomes `self.db` (instance attribute)
- `request.addfinalizer(fn)` becomes `self.addCleanup(fn)`
- Test methods no longer take the fixture as a parameter


### Module-level fixture (shared across classes)

```python
# pytest
@pytest.fixture
def commands(request):
    sub_cmds = {'help': Help, 'run': Run}
    return PluginDict(sub_cmds)

class TestBash(object):
    def test_completion(self, commands):
        ...

# rut — extract a plain helper function
def _make_commands():
    sub_cmds = {'help': Help, 'run': Run}
    return PluginDict(sub_cmds)

class TestBash(unittest.TestCase):
    def test_completion(self):
        commands = _make_commands()
        ...
```

If the fixture is expensive, use `setUpClass`:

```python
class TestExpensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resource = create_expensive_resource()

    @classmethod
    def tearDownClass(cls):
        cls.resource.close()
        super().tearDownClass()
```


## Reusable fixtures → Mixins

When multiple test classes need the same setup/teardown, use **mixins** with cooperative `super()` calls.

```python
# pytest (conftest.py)
@pytest.fixture
def dep_manager(request, tmp_path_factory):
    filename = str(tmp_path_factory.mktemp('x', True) / 'testdb')
    dep_file = Dependency(DbmDB, filename)
    request.addfinalizer(dep_file.close)
    return dep_file

# rut — mixin (test_support.py)
class DepManagerMixin:
    """Provides self.dep_manager with automatic cleanup."""
    def setUp(self):
        super().setUp()
        self._dep_tmpdir = tempfile.mkdtemp(prefix='test-')
        filename = os.path.join(self._dep_tmpdir, 'testdb')
        self.dep_manager = Dependency(DbmDB, filename)

    def tearDown(self):
        if not self.dep_manager._closed:
            self.dep_manager.close()
        shutil.rmtree(self._dep_tmpdir, ignore_errors=True)
        super().tearDown()
```

Usage — mixins compose via multiple inheritance:

```python
class TestLoader(RestoreCwdMixin, DepManagerMixin, unittest.TestCase):
    def test_load(self):
        os.chdir("/tmp")
        self.dep_manager.save_success(task)
        ...
```

The `super()` calls ensure all mixins' `setUp`/`tearDown` run in MRO order.


## Temporary directories

```python
# pytest
def test_something(self, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("content")

# rut
import tempfile
import shutil

class TestSomething(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tmp_path = tempfile.mkdtemp(prefix='test-')
        self.addCleanup(shutil.rmtree, self.tmp_path, True)

    def test_something(self):
        f = os.path.join(self.tmp_path, "hello.txt")
        with open(f, "w") as fh:
            fh.write("content")
```

Note: `tmp_path` returns a `pathlib.Path`, `tmpdir` returns a `py.path.local`. With `tempfile.mkdtemp` you get a plain string — use `os.path.join` or wrap in `pathlib.Path` as needed.


## Capturing output (capsys)

```python
# pytest
def test_version(self, capsys):
    print_version()
    captured = capsys.readouterr()
    assert "1.0" in captured.out

# rut
import io
import contextlib

class TestVersion(unittest.TestCase):
    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            print_version()
        self.assertIn("1.0", out.getvalue())
```

For capturing both stdout and stderr:

```python
def test_with_stderr(self):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        do_something()
    self.assertIn("output", out.getvalue())
    self.assertIn("warning", err.getvalue())
```


## Monkeypatching

pytest's `monkeypatch` maps to `unittest.mock.patch`.

### Patching an attribute

```python
# pytest
def test_run(self, monkeypatch):
    monkeypatch.setattr(Run, "execute", Mock())
    cmd_main([])

# rut
from unittest.mock import patch, Mock

class TestRun(unittest.TestCase):
    def test_run(self):
        with patch.object(Run, "execute", Mock()):
            cmd_main([])
```

### Patching environment variables

```python
# pytest
def test_env(self, monkeypatch):
    monkeypatch.setenv('FOO', 'bar')
    assert os.environ['FOO'] == 'bar'

# rut — with patch.dict
from unittest.mock import patch

def test_env(self):
    with patch.dict(os.environ, {'FOO': 'bar'}):
        self.assertEqual('bar', os.environ['FOO'])
```

### Patching sys.argv

```python
# pytest
def test_cli(self, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['doit', 'list'])
    main()

# rut
from unittest.mock import patch

def test_cli(self):
    with patch.object(sys, 'argv', ['doit', 'list']):
        main()
```


## Skipping tests

```python
# pytest — decorator
@pytest.mark.skipif(sys.platform == 'win32', reason='Unix only')
class TestUnix(object):
    ...

# rut — decorator
@unittest.skipIf(sys.platform == 'win32', 'Unix only')
class TestUnix(unittest.TestCase):
    ...
```

```python
# pytest — runtime skip
def test_feature(self):
    if not has_feature():
        pytest.skip("feature not available")

# rut — runtime skip
def test_feature(self):
    if not has_feature():
        self.skipTest("feature not available")
```


## Parametrize → subTest

pytest's `@pytest.mark.parametrize` maps to loops with `self.subTest`.

```python
# pytest
@pytest.mark.parametrize('input,expected', [
    ('hello', 5),
    ('world', 5),
    ('', 0),
])
def test_length(self, input, expected):
    assert len(input) == expected

# rut
def test_length(self):
    cases = [
        ('hello', 5),
        ('world', 5),
        ('', 0),
    ]
    for input, expected in cases:
        with self.subTest(input=input):
            self.assertEqual(len(input), expected)
```


## Parametrized fixtures → subTest or class split

### Option A: subTest loop

```python
# pytest
@pytest.fixture(params=['json', 'sqlite3', 'dbm'])
def backend(request):
    return create_backend(request.param)

# rut
BACKENDS = ['json', 'sqlite3', 'dbm']

class TestStorage(unittest.TestCase):
    def test_save(self):
        for name in BACKENDS:
            with self.subTest(backend=name):
                backend = create_backend(name)
                try:
                    backend.save("key", "value")
                    self.assertEqual("value", backend.get("key"))
                finally:
                    backend.close()
```

### Option B: Base class with concrete subclasses

Better for large test classes where every test needs the same backend:

```python
class StorageTestBase:
    """Mixin — not discovered by rut (no TestCase)."""
    backend_name = None

    def setUp(self):
        super().setUp()
        self.backend = create_backend(self.backend_name)
        self.addCleanup(self.backend.close)

    def test_save(self):
        self.backend.save("key", "value")
        self.assertEqual("value", self.backend.get("key"))

class TestJsonStorage(StorageTestBase, unittest.TestCase):
    backend_name = 'json'

class TestSqliteStorage(StorageTestBase, unittest.TestCase):
    backend_name = 'sqlite3'
```


## Bare test functions → TestCase classes

pytest discovers bare `test_*` functions. <span class="rut">rut</span> requires `unittest.TestCase` methods.

```python
# pytest
def test_simple():
    assert 1 + 1 == 2

# rut
class TestSimple(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(2, 1 + 1)
```


## conftest.py

pytest's `conftest.py` serves multiple purposes. In <span class="rut">rut</span>, these are split:

| pytest conftest.py | rut equivalent |
|---|---|
| Fixtures shared across files | Mixins or helper functions in a support module |
| `autouse` fixtures | `setUp`/`tearDown` in a base class or mixin |
| Hooks (`pytest_configure`, etc.) | `conftest.py` with `rut_session_setup()`/`rut_session_teardown()` |
| `pytest.fixture(params=...)` | `subTest` loops or class hierarchies |


## Test data files

If your test data lives in `tests/data/`, symlink it from your new test folder:

```bash
ln -s ../tests/data tests_rut/data
```


## Configuration

Configure <span class="rut">rut</span> in `pyproject.toml`:

```toml
[tool.rut]
source_dirs = ["mypackage", "tests"]
```


## Checklist per file

For each test file you convert:

1. Replace `import pytest` with `import unittest`
2. Change `class TestX(object):` to `class TestX(unittest.TestCase):`
3. Convert all `assert` statements to `self.assert*` methods
4. Replace `pytest.raises` with `self.assertRaises`
5. Replace fixtures with `setUp`/`tearDown` or mixins
6. Replace `capsys` with `contextlib.redirect_stdout/stderr`
7. Replace `monkeypatch` with `unittest.mock.patch`
8. Replace `tmp_path`/`tmpdir` with `tempfile.mkdtemp`
9. Replace `pytest.skip` with `self.skipTest`
10. Replace `@pytest.mark.skipif` with `@unittest.skipIf`
11. Replace `@pytest.mark.parametrize` with `subTest` loops
12. Wrap bare test functions in a `TestCase` class
13. Run: `rut tests_rut/test_<name>.py`
14. Compare coverage: `rut --cov tests_rut/test_<name>.py`
