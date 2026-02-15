# Demo Recording Scripts

All commands assume `cd demo` first.

## Reset state

Run before each recording:

```bash
rm -rf .rut_cache __pycache__ finance/__pycache__ tests/__pycache__
sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py 2>/dev/null
sed -i 's/round(total, 4)/round(total, 2)/' finance/report.py 2>/dev/null
```


---

## Demo 1 — Main tour (~70s)

The elevator pitch. Touches every feature so new users see the full picture.

```bash
# 1. Run all tests — dot output
rut

# 2. Verbose — full test names
rut -v

# 3. Keyword filter — only transfer tests
rut -k transfer

# 4. "Update" the EUR exchange rate — a legitimate-looking change
sed -i 's/"EUR": 1.08/"EUR": 1.10/' finance/currency.py

# 5. Run only the file you changed — looks fine!
rut tests/test_currency.py

# 6. Run full suite — downstream breakage in account and report
rut

# 7. Fail fast — stop at first failure
rut -x

# 8. Fix it
sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py

# 9. Green run — also builds the cache for --changed
rut

# 10. Touch a leaf module
sed -i 's/round(total, 2)/round(total, 4)/' finance/report.py

# 11. Incremental — only 4 affected tests run, 16 skipped
rut --changed -v

# 12. Fix
sed -i 's/round(total, 4)/round(total, 2)/' finance/report.py

# 13. Nothing changed — everything up-to-date
rut --changed

# 14. Coverage — one flag, no config
rut --cov
```

**What to narrate:**
- Step 1: "20 tests, 5 seconds. just type rut."
- Step 3: "-k filters by keyword — only 5 transfer tests run"
- Step 5: "you changed currency.py, ran its tests — all green"
- Step 6: "but the full suite catches downstream breakage. rut orders tests by import dependencies, so failures in dependents surface immediately"
- Step 7: "-x stops at first failure for faster debugging"
- Step 11: "only 4 tests re-ran. rut tracks which files changed and follows the import graph to skip unaffected tests"
- Step 13: "nothing changed since last green run — zero work"
- Step 14: "built-in coverage, one flag"


---

## Demo 2 — Incremental testing (~30s)

Deep dive on `--changed`: dependency tracking, leaf vs root changes.

```bash
# 1. Baseline run — builds the cache
rut

# 2. Modify report.py (leaf module — no downstream deps)
sed -i 's/round(total, 2)/round(total, 4)/' finance/report.py

# 3. Only report tests run, rest skipped
rut --changed -v

# 4. Fix it
sed -i 's/round(total, 4)/round(total, 2)/' finance/report.py

# 5. All pass, cache updated
rut --changed -v

# 6. Nothing changed — everything up-to-date
rut --changed -v

# 7. Now change a root module — currency.py affects everything
sed -i 's/"EUR": 1.08/"EUR": 1.10/' finance/currency.py

# 8. All tests re-run (currency is at the root of the import graph)
rut --changed -v

# 9. Fix
sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py
```

**What to narrate:**
- Step 3: "report.py is a leaf — only 4 tests re-ran, 16 skipped"
- Step 6: "cache is current, nothing to do"
- Step 8: "currency.py is at the root of the import graph — changing it invalidates everything"


---

## Demo 3 — Dependency-aware testing (~25s)

The "local fix that breaks a dependency" story. Shows why running only the
changed file's tests is dangerous, and how rut catches it.

```bash
# 1. All green
rut

# 2. "Update" the EUR rate — a plausible business change
sed -i 's/"EUR": 1.08/"EUR": 1.10/' finance/currency.py

# 3. Run only the changed file — all 6 pass, "looks fine"
rut tests/test_currency.py

# 4. Run full suite — 2 failures in downstream modules
rut

# 5. Or use --changed — it follows the import graph, catches it too
rut --changed

# 6. Fix
sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py
```

**What to narrate:**
- Step 3: "you ran the tests for the file you touched — all green. easy to think you're done"
- Step 4: "but account and report depend on currency. their hardcoded expectations break"
- Step 5: "--changed doesn't just run tests for the file you touched — it follows the import graph and re-runs all dependents"


---

## Demo 4 — Failure output (~20s)

Shows quality of failure output: file links, assertion diffs, summary.

```bash
# 1. Break EUR rate
sed -i 's/"EUR": 1.08/"EUR": 1.10/' finance/currency.py

# 2. Full failure details
rut

# 3. Fail fast — stop at first
rut -x

# 4. Fix
sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py
```

**What to narrate:**
- Step 2: "each failure shows file:line, the assertion, and expected vs actual"
- Step 2: "summary at the bottom lists all failures at a glance"
- Step 3: "-x stops on the first failure — useful during debugging"


---

## Demo 5 — Coverage report (~15s)

```bash
rut --cov
```

**What to narrate:**
- "built-in coverage — no plugins, no config, one flag"
- "shows missing lines per module — 98% here"


---

## Break/fix commands reference

| What | Break | Fix |
|---|---|---|
| EUR rate 1.08→1.10 | `sed -i 's/"EUR": 1.08/"EUR": 1.10/' finance/currency.py` | `sed -i 's/"EUR": 1.10/"EUR": 1.08/' finance/currency.py` |
| Rounding 2→4 | `sed -i 's/round(total, 2)/round(total, 4)/' finance/report.py` | `sed -i 's/round(total, 4)/round(total, 2)/' finance/report.py` |


## Failure behavior reference

| Change | Tests that fail | Modules affected |
|---|---|---|
| EUR rate 1.08→1.10 | `test_balance_in_converts_currency`, `test_multi_account_multi_currency` | test_account, test_report |
| Rounding 2→4 | (none — cosmetic at current values) | test_report only re-runs with --changed |

## Why the EUR rate change works as a "local fix"

Currency tests compute expected values dynamically from `RATES`:
```python
expected = round(100 * RATES["USD"] / RATES["EUR"], 2)
```
So they always pass regardless of the rate value — they test the conversion *logic*.

But `test_account.py` and `test_report.py` have hardcoded expectations:
```python
self.assertEqual(usd_balance, 1080.0)   # account
self.assertEqual(total, 1540.0)          # report
```
These break when the rate changes. A change that looks safe locally cascades downstream.
