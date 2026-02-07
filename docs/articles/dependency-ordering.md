---
layout: article
title: "Why Test Order Matters: Dependency-Aware Testing"
description: "Run foundational tests first. Fail fast, debug easier. How rut uses your import graph to order tests."
---

When a test fails, you want to know immediately. But if your test runner executes tests in arbitrary order, you might wait minutes before seeing the failure that matters.

<img src="{{ '/assets/images/dependency-order-comparison.png' | relative_url }}" alt="Comparison of alphabetical vs dependency order - showing much earlier failure detection" class="article-image">

## The problem with random test order

Most test runners discover tests alphabetically or by file modification time. This means:

```
tests/test_api.py        # runs first (alphabetically)
tests/test_models.py     # runs second
tests/test_utils.py      # runs third
```

But what if `test_utils.py` tests the foundational code that everything else depends on? A bug in `utils.py` will cause cascading failures across all tests — but you won't see the root cause until the end.

## Import graph to the rescue

Your code has a natural dependency structure. If `models.py` imports from `utils.py`, then `utils` is more foundational. Tests for foundational modules should run first.

<pre class="mermaid">
graph TB
    utils["utils.py"]
    models["models.py"]
    auth["auth.py"]
    api["api.py"]
    views["views.py"]

    api --> models
    api --> auth
    views --> models
    models --> utils
    auth --> utils
</pre>

Topological sorting gives us: `utils → models → api`

If we run tests in this order, a bug in `utils.py` fails fast — you see it in seconds, not minutes.

## How <span class="rut">rut</span> does it

<span class="rut">rut</span> analyzes your import graph at test discovery time:

```bash
$ rut --dry-run
Test order (by import dependencies):
  tests/test_utils.py::TestUtils
  tests/test_models.py::TestModels
  tests/test_api.py::TestAPI
```

No configuration needed. It reads your actual imports and sorts accordingly.

## Easier debugging

There's another benefit: when a foundational module breaks, you don't have to dig through 300 failing tests to find the root cause.

A bug in `utils.py` causes cascading failures. With alphabetical order:

```
FAIL test_api.py::test_create_user - AttributeError: 'NoneType' has no 'id'
FAIL test_api.py::test_delete_user - AttributeError: 'NoneType' has no 'id'
FAIL test_models.py::test_user_model - AttributeError: 'NoneType' has no 'id'
... 297 more failures ...
FAIL test_utils.py::test_parse_config - KeyError: 'database'
```

Which failure matters? You have to guess.

With dependency order and `-x` (stop on first failure):

```bash
$ rut -x
FAIL test_utils.py::test_parse_config - KeyError: 'database'
Stopping at first failure.
```

The first failure points directly to the root cause. No need to wade through 300 cascading failures to find the one that matters.

## Limitations

- **Circular imports**: If A imports B and B imports A, topological sort can't help. This is a code smell anyway. You can check for circular imports with [import-deps](https://github.com/schettino72/import-deps).
- **Test isolation**: This assumes tests are independent. If test order affects results, you have flaky tests.
- **Dynamic imports**: Only static imports are analyzed. `importlib.import_module()` isn't tracked.

