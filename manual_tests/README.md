# Manual Tests

Test files for manual CLI testing. Not run by unittest.

## Logging Leak Test

```bash
uv run rut -k test_logging_leak manual_tests
```

## Incremental Testing (--changed)

Tests transitive dependency detection: `test_main.py` → `helper.py` → `util.py`

**Note:** The test folder must be in `source_dirs` config for `--changed` to work.
In `pyproject.toml`:
```toml
[tool.rut]
source_dirs = ["src", "tests", "manual_tests"]
```

```bash
# 1. Build the cache (run tests first)
uv run rut manual_tests/test_incremental

# 2. Verify all up-to-date
uv run rut --changed manual_tests/test_incremental
# Should show: ⚡ test_incremental.test_main (2)

# 3. Modify the leaf dependency
echo "# modified" >> manual_tests/test_incremental/util.py

# 4. Run with --changed - should detect transitive dependency
uv run rut --changed manual_tests/test_incremental
# Should run test_main tests because it depends on util via helper

# 5. Clean up
sed -i '/^# modified$/d' manual_tests/test_incremental/util.py
```
