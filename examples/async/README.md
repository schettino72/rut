# Async Example

This example demonstrates testing asynchronous code with rut.

## Project Structure

```
async/
├── README.md
├── async_service.py
└── tests/
    └── test_async_service.py
```

## Key Points

1. **Use `IsolatedAsyncioTestCase`**: Your test class must inherit from `unittest.IsolatedAsyncioTestCase`
2. **Async test methods**: Define test methods with `async def`
3. **Await async calls**: Use `await` for all async operations
4. **No special setup**: rut automatically detects and runs async tests

## Common Mistake

❌ **Wrong** - This will fail:
```python
class MyTest(unittest.TestCase):  # Wrong base class!
    async def test_something(self):
        ...
```

✅ **Correct**:
```python
class MyTest(unittest.IsolatedAsyncioTestCase):  # Correct!
    async def test_something(self):
        ...
```

## Running the Tests

```bash
# Run all tests
rut

# Run specific async test
rut -k fetch_data
```

## Expected Output

```
✔ test_async_service.TestAsyncService.test_fetch_data
✔ test_async_service.TestAsyncService.test_process_data
✔ test_async_service.TestAsyncService.test_concurrent_operations

----------------------------------------------------------------------
Ran 3 tests in 0.105s

OK
```
