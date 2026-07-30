---
layout: article
title: "Incremental Testing: Run Only Affected Tests"
description: "Test impact analysis for Python unittest. Run only affected tests after a change — skip what's up-to-date. Change-based selective testing with rut."
date: 2026-02-07
---

If you changed one file, why run 500 tests?

Incremental testing — also known as test impact analysis or change-based testing — means running only the tests affected by your changes. It's the same principle behind `make`: track dependencies, rebuild only what's stale.

In other ecosystems this is called "affected tests" (Nx, Bazel, Pants) or "selective testing". [pytest-incremental](https://github.com/pytest-dev/pytest-incremental) (2011) and [testmon](https://github.com/tarpas/pytest-testmon) have been doing this for pytest. <span class="rut">rut</span> brings it to unittest with a focus on simplicity and AI coding workflows.

## The dependency graph

<span class="rut">rut</span> [builds a dependency graph]({{ '/articles/import-graph' | relative_url }}) from your static imports. It tracks dependencies at the **module level**, not individual test functions. If a module you changed is imported by a test module, the entire test module runs.

If you change `currency.py`, which tests need to run? All of them — every module imports currency. If you change `account.py`? Only `test_account`, `test_transaction`, and `test_report`. `test_currency` doesn't depend on account — skip it.

<img src="{{ '/assets/images/finance-deps-changed.svg' | relative_url }}" alt="Dependency graph highlighting affected tests when transaction.py changes" class="article-image">

## How <span class="rut">rut</span> tracks this

First run builds the graph:

```bash
$ rut
tests/test_utils.py ....                [ 16%]
tests/test_currency.py ......           [ 41%]
tests/test_account.py .....             [ 62%]
tests/test_transaction.py .....         [ 83%]
tests/test_report.py ....              [100%]

────────────── 24 passed in 5.4s ──────────────
```

Subsequent runs with `--changed` check what's stale:

```bash
$ rut --changed
tests/test_utils.py ⚡ 4 up-to-date     [ 16%]
tests/test_currency.py ⚡ 6 up-to-date  [ 41%]
tests/test_account.py .....             [ 62%]
tests/test_transaction.py .....         [ 83%]
tests/test_report.py ....              [100%]

────────────── 14 passed, 10 up-to-date in 4.8s ──────────────
```

14 tests instead of 24. Same confidence, less time.

## What counts as "changed"?

<span class="rut">rut</span> hashes every file in `source_dirs` and compares against the last successful run:

- **Source files**: `finance/*.py` — if changed, tests depending on them run
- **Test files**: `tests/*.py` — if changed, that test module runs

```bash
$ rut --changed --debug
Changed modules: finance.account
Affected tests: test_account, test_transaction, test_report
Skipping: test_utils, test_currency (up-to-date)
```

## The cache

<span class="rut">rut</span> stores dependency info in `.rut_cache/`:

```
.rut_cache/
└── file_hashes.json   # SHA256 hashes of all tracked files
```

Add to `.gitignore`. The cache is only updated after a successful test run — if tests fail, the cache stays stale so the same tests run again next time.

## When incremental testing doesn't help

**Everything depends on everything**: If your `currency.py` is imported by every module, changing it runs all tests. This is feedback about your architecture — maybe that module is doing too much.

**Heavy test fixtures**: If setup is slow (database, network), skipping tests doesn't save much. Focus on faster fixtures.

See [how the import graph works]({{ '/articles/import-graph' | relative_url }}) for more details on what is and isn't tracked.

## Combining with dependency ordering

<span class="rut">rut</span> does both:

1. **Order**: Foundational tests first (fail fast)
2. **Filter**: Skip unaffected tests (save time)

```bash
$ rut --changed
# 1. Determines affected tests from graph
# 2. Orders them by dependency (foundational first)
# 3. Runs only what's needed
```

