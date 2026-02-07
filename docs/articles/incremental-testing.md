---
layout: article
title: "Incremental Testing: Run Only What Changed"
description: "Skip unaffected tests. Track dependencies, run only what's stale. How rut uses import analysis for faster test runs."
---

If you changed one file, why run 500 tests?

Incremental testing means running only the tests affected by your changes. It's the same principle behind `make`: track dependencies, rebuild only what's stale.

This isn't a new idea. [pytest-incremental](https://github.com/pytest-dev/pytest-incremental) (2008) and [testmon](https://github.com/tarpas/pytest-testmon) have been doing this for pytest. <span class="rut">rut</span> brings it to unittest with a focus on simplicity and AI coding workflows.

## The dependency graph

Every Python module has imports. These form a directed graph:

<pre class="mermaid">
graph LR
    auth["auth.py"]
    users["users.py"]
    db["db.py"]
    api["api.py"]
    main["main.py"]

    main --> api
    api --> auth
    api --> users
    api --> db
</pre>

If you change `db.py`, which tests need to run?

1. Tests for `db.py` (direct)
2. Tests for `api.py` (imports db)
3. Tests for `main.py` (imports api, which imports db)

Tests for `auth.py` and `users.py`? They don't depend on `db.py`. Skip them.

## How <span class="rut">rut</span> tracks this

First run builds the graph:

```bash
$ rut
Building dependency graph...
Running 50 tests
========== 50 passed in 12.5s ==========
```

Subsequent runs with `--changed` check what's stale:

```bash
$ git diff --name-only
src/db.py

$ rut --changed
Affected by changes: 12 tests
Skipping: 38 tests (unchanged)
========== 12 passed in 2.1s ==========
```

12 tests instead of 50. Same confidence, 80% less time.

## What counts as "changed"?

<span class="rut">rut</span> checks file modification times against the last test run:

- **Source files**: `src/*.py` — if changed, tests depending on them run
- **Test files**: `tests/*.py` — if changed, that test runs
- **Config files**: Can be configured to trigger full runs

```bash
$ rut --changed --verbose
Checking for changes since last run...
  src/db.py: modified
  src/api.py: unchanged
  tests/test_db.py: unchanged

Affected modules: db, api, main
Running: test_db, test_api, test_main
Skipping: test_auth, test_users
```

## The cache

<span class="rut">rut</span> stores dependency info in `.rut_cache/`:

```
.rut_cache/
├── deps.json      # import graph
└── timestamps     # last run times
```

Add to `.gitignore`. The cache rebuilds automatically if imports change.

## When incremental testing doesn't help

**Everything depends on everything**: If your `utils.py` is imported by every module, changing it runs all tests. This is feedback about your architecture — maybe `utils.py` is too big.

**Circular dependencies**: A imports B, B imports A. The graph becomes a single strongly-connected component. Everything runs together. Check for these with [import-deps](https://github.com/schettino72/import-deps).

**Heavy test fixtures**: If setup is slow (database, network), skipping tests doesn't save much. Focus on faster fixtures.

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

