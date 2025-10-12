# Basic Example

This example shows the most basic usage of rut.

## Project Structure

```
basic/
├── README.md
├── calculator.py
└── tests/
    └── test_calculator.py
```

## Running the Tests

From this directory:

```bash
# Run all tests
rut

# Run with coverage
rut --cov

# Run only tests matching "add"
rut -k add

# Exit on first failure
rut -x
```

## What This Example Demonstrates

1. **Zero-config discovery**: Just run `rut` and it finds your tests
2. **Simple test structure**: Standard `unittest.TestCase` usage
3. **Basic assertions**: Using unittest's assertion methods
4. **No boilerplate**: No need for `if __name__ == '__main__'`

## Expected Output

```
✔ test_calculator.TestCalculator.test_add
✔ test_calculator.TestCalculator.test_divide
✔ test_calculator.TestCalculator.test_multiply
✔ test_calculator.TestCalculator.test_subtract

----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```
