---
layout: article
title: "Why Test Order Matters: Dependency-Aware Testing"
description: "Topological test ordering by import dependencies. Run foundational tests first, fail fast, debug easier. How rut uses your import graph to order tests."
date: 2026-02-07
---

When a test fails, you want to know immediately. But if your test runner executes tests in arbitrary order, you might wait minutes before seeing the failure that matters.

<img src="{{ '/assets/images/dependency-order-comparison.png' | relative_url }}" alt="Comparison of alphabetical vs dependency order - showing much earlier failure detection" class="article-image">

## The problem with random test order

Most test runners discover tests alphabetically or by file modification time. This means:

```
tests/test_account.py      # runs first (alphabetically)
tests/test_currency.py     # runs second
tests/test_report.py       # runs third
tests/test_transaction.py  # runs fourth
tests/test_utils.py        # runs last
```

But what if `test_utils.py` tests the foundational code that everything else depends on? A bug in `utils.py` will cause cascading failures across all tests — but you won't see the root cause until the very end.

## Import graph to the rescue

Your code has a natural dependency structure. If `currency.py` imports from `utils.py`, then `utils` is more foundational. Tests for foundational modules should run first.

<img src="{{ '/assets/images/finance-deps.svg' | relative_url }}" alt="Finance module dependency graph showing import relationships" class="article-image">

<span class="rut">rut</span> [analyzes your imports]({{ '/articles/import-graph' | relative_url }}) to build a dependency graph and topological sorts it: `utils → currency → account → transaction → report`. A bug in `utils.py` fails fast — you see it in seconds, not minutes.

## How <span class="rut">rut</span> does it

<span class="rut">rut</span> analyzes your import graph at test discovery time:

```bash
$ rut --dry-run
Test order (by import dependencies):
  tests/test_utils.py::TestUtils
  tests/test_currency.py::TestCurrency
  tests/test_account.py::TestAccount
  tests/test_transaction.py::TestTransaction
  tests/test_report.py::TestReport
```

No configuration needed. It reads your actual imports and sorts accordingly.

## Easier debugging

There's another benefit: when a foundational module breaks, you don't have to dig through 300 failing tests to find the root cause.

A bug in `utils.py` causes cascading failures. With alphabetical order:

```
FAIL test_account.py::test_balance_in_eur - TypeError: unsupported operand type
FAIL test_currency.py::test_convert_usd_to_eur - ImportError: cannot import name
FAIL test_report.py::test_net_worth - TypeError: unsupported operand type
FAIL test_transaction.py::test_cross_currency - TypeError: unsupported operand type
... more failures ...
FAIL test_utils.py::test_round_amount - NameError: name 'round' is not defined
```

Which failure matters? You have to guess.

With dependency order and `-x` (stop on first failure):

```bash
$ rut -x
FAIL test_utils.py::test_round_amount - NameError: name 'round' is not defined
Stopping at first failure.
```

The first failure points directly to the root cause. No need to wade through cascading failures to find the one that matters.

## Limitations

- **Test isolation**: This assumes tests are independent. If test order affects results, you have flaky tests.
- See [how the import graph works]({{ '/articles/import-graph' | relative_url }}) for details on what is and isn't tracked (dynamic imports, circular dependencies, etc.).

