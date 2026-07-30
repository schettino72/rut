# Migrating from pytest to rut — Instructions for AI Agents

You are converting a pytest test suite to use `rut`, a test runner for Python's standard `unittest` framework. Apply the following rules to each test file.

## Rules

### 1. Test classes must inherit from unittest.TestCase
```
BEFORE: class TestFoo(object):
AFTER:  class TestFoo(unittest.TestCase):
```
Add `import unittest` at the top of the file.

### 2. Convert assert statements to self.assert* methods
```
assert x == y              → self.assertEqual(x, y)
assert x != y              → self.assertNotEqual(x, y)
assert x in collection     → self.assertIn(x, collection)
assert x not in collection → self.assertNotIn(x, collection)
assert x is None           → self.assertIsNone(x)
assert x is not None       → self.assertIsNotNone(x)
assert x                   → self.assertTrue(x)
assert not x               → self.assertFalse(x)
assert isinstance(x, T)   → self.assertIsInstance(x, T)
assert abs(x-y) < tol     → self.assertAlmostEqual(x, y, places=5)
assert x > y               → self.assertGreater(x, y)
assert x >= y              → self.assertGreaterEqual(x, y)
assert x < y               → self.assertLess(x, y)
assert x <= y              → self.assertLessEqual(x, y)
```

### 3. Convert pytest.raises to self.assertRaises
```
BEFORE: pytest.raises(ValueError, int, "x")
AFTER:  self.assertRaises(ValueError, int, "x")

BEFORE: with pytest.raises(ValueError) as exc_info:
            do_thing()
        assert "msg" in str(exc_info.value)
AFTER:  with self.assertRaises(ValueError) as cm:
            do_thing()
        self.assertIn("msg", str(cm.exception))
```
Note: pytest uses `.value`, unittest uses `.exception`.

### 4. Convert fixtures to setUp/tearDown
- Fixture return values become `self.<name>` instance attributes
- `request.addfinalizer(fn)` becomes `self.addCleanup(fn)`
- Test methods no longer take fixture parameters
- Always call `super().setUp()` first and `super().tearDown()` last
```
BEFORE:
    @pytest.fixture
    def db(self, request):
        conn = create_connection()
        request.addfinalizer(conn.close)
        return conn

    def test_query(self, db):
        result = db.execute("SELECT 1")

AFTER:
    def setUp(self):
        super().setUp()
        self.db = create_connection()
        self.addCleanup(self.db.close)

    def test_query(self):
        result = self.db.execute("SELECT 1")
```

### 5. Convert shared fixtures to mixins
When multiple test classes need the same fixture, create a mixin class:
```
class MyFixtureMixin:
    def setUp(self):
        super().setUp()
        self.resource = create_resource()
    def tearDown(self):
        self.resource.close()
        super().tearDown()

class TestFoo(MyFixtureMixin, unittest.TestCase):
    def test_something(self):
        self.resource.do_thing()
```
Mixin must come before unittest.TestCase in the inheritance list.

### 6. Convert tmp_path/tmpdir to tempfile
```
BEFORE: def test_foo(self, tmp_path):
            f = tmp_path / "file.txt"

AFTER:  def setUp(self):
            super().setUp()
            self.tmp_path = tempfile.mkdtemp(prefix='test-')
            self.addCleanup(shutil.rmtree, self.tmp_path, True)

        def test_foo(self):
            f = os.path.join(self.tmp_path, "file.txt")
```
Add `import tempfile` and `import shutil` at the top.

### 7. Convert capsys to contextlib.redirect_stdout
```
BEFORE: def test_out(self, capsys):
            print_version()
            assert "1.0" in capsys.readouterr().out

AFTER:  def test_out(self):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                print_version()
            self.assertIn("1.0", out.getvalue())
```
Add `import io` and `import contextlib` at the top.

### 8. Convert monkeypatch to unittest.mock.patch
```
monkeypatch.setattr(Cls, "attr", val) → with patch.object(Cls, "attr", val):
monkeypatch.setenv('K', 'V')          → with patch.dict(os.environ, {'K': 'V'}):
monkeypatch.setattr(sys, 'argv', [...]) → with patch.object(sys, 'argv', [...]):
```
Add `from unittest.mock import patch, Mock` at the top.

### 9. Convert skip markers
```
@pytest.mark.skipif(cond, reason='R')  → @unittest.skipIf(cond, 'R')
pytest.skip("reason")                  → self.skipTest("reason")
```

### 10. Convert parametrize to subTest
```
BEFORE: @pytest.mark.parametrize('x,y', [(1,1), (2,4)])
        def test_square(self, x, y):
            assert x**2 == y

AFTER:  def test_square(self):
            for x, y in [(1,1), (2,4)]:
                with self.subTest(x=x):
                    self.assertEqual(x**2, y)
```

### 11. Wrap bare test functions in TestCase classes
```
BEFORE: def test_simple():
            assert 1 + 1 == 2

AFTER:  class TestSimple(unittest.TestCase):
            def test_simple(self):
                self.assertEqual(2, 1 + 1)
```

## Strategy

Convert one file at a time into a parallel `tests_rut/` folder. Run both suites during transition. Once done, delete old `tests/` and rename `tests_rut/` to `tests/`.

## Verification

After converting each file, run:
```
rut tests_rut/test_<name>.py
```

## conftest.py mapping

| pytest conftest.py           | rut equivalent                                    |
|------------------------------|---------------------------------------------------|
| Shared fixtures              | Mixins or helper functions in a support module     |
| autouse fixtures             | setUp/tearDown in a base class or mixin            |
| Hooks (pytest_configure)     | conftest.py with rut_session_setup/teardown        |
| fixture(params=...)          | subTest loops or class hierarchies                 |

## Configuration

```toml
# pyproject.toml
[tool.rut]
source_dirs = ["mypackage", "tests"]
```
