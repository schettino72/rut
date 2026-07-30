---
layout: article
title: "How rut Builds the Import Dependency Graph"
description: "Static import analysis at the module level. How rut understands your codebase structure to order tests and skip unaffected ones."
date: 2026-02-11
---

Both of <span class="rut">rut</span>'s key features — [dependency ordering]({{ '/articles/dependency-ordering' | relative_url }}) and [running only affected tests]({{ '/articles/incremental-testing' | relative_url }}) — rely on the same foundation: a dependency graph built from your Python imports.

## Static import analysis

<span class="rut">rut</span> uses [import-deps](https://github.com/schettino72/import-deps) to analyze your source files. It reads `import` and `from ... import` statements and builds a directed graph of which modules depend on which.

```python
# api.py
from myapp.db import get_connection
from myapp.auth import require_login
```

This tells <span class="rut">rut</span> that `api` depends on `db` and `auth`. No runtime instrumentation, no tracing — just reading the source.

## Module-level granularity

The graph operates at the **module level**, not individual functions or test methods. If `test_api.py` imports from `api.py`, and `api.py` imports from `db.py`, then:

- Changing `db.py` marks the entire `test_api.py` module as affected
- All tests in `test_api.py` will run, even if only some of them use `db` functionality

This is a deliberate tradeoff. Tracking at the function level would require runtime coverage tracing (like [testmon](https://github.com/tarpas/pytest-testmon) does for pytest). Module-level analysis is:

- **Fast** — no overhead during test execution
- **Predictable** — you can reason about it by looking at your imports
- **Good enough** — in well-structured codebases, modules are cohesive

If you find that changing one file always triggers all your tests, that's feedback about your architecture. A `utils.py` imported everywhere means everything is coupled to it.

## What the graph looks like

For a typical project:

<pre class="mermaid">
graph TB
    utils["utils.py"]
    db["db.py"]
    auth["auth.py"]
    models["models.py"]
    api["api.py"]
    views["views.py"]

    db --> utils
    auth --> utils
    models --> db
    api --> models
    api --> auth
    views --> models
</pre>

<span class="rut">rut</span> does a topological sort on this graph. Modules with no dependencies (like `utils`) come first. Modules that depend on everything (like `api`) come last.

You can inspect the order with:

```bash
$ rut --dry-run -v
```

## How the graph is used

**For [dependency ordering]({{ '/articles/dependency-ordering' | relative_url }})**: Tests for foundational modules run first. If `utils.py` is broken, you see that failure immediately — before the 300 cascading failures in modules that depend on it.

**For [incremental testing]({{ '/articles/incremental-testing' | relative_url }})**: When you run `rut --changed`, <span class="rut">rut</span> checks which source files changed since the last successful run, walks the graph to find all modules that depend on them (transitively), and only runs those test modules.

## What is NOT tracked

**Dynamic imports**: `importlib.import_module("myapp.db")` doesn't appear as an `import` statement in the source. <span class="rut">rut</span> won't see it.

**Conditional imports**: Imports inside `if` blocks or `try/except` are still static imports — they *are* tracked. But if a module is only imported at runtime under certain conditions, the graph won't reflect the conditional nature.

**Non-Python dependencies**: Changes to templates, SQL files, config files, or data files aren't tracked. Only `.py` files in your configured `source_dirs` are analyzed.

**Circular imports**: If A imports B and B imports A, they form a strongly-connected component. <span class="rut">rut</span> handles this but loses the ability to order them meaningfully — they'll run together. Circular imports are usually a code smell. You can detect them with [import-deps](https://github.com/schettino72/import-deps).

## Configuration

By default, <span class="rut">rut</span> scans `src/` and `tests/` for Python files. You can change this in `pyproject.toml`:

```toml
[tool.rut]
source_dirs = ["myapp", "libs", "tests"]
```

Only files in these directories are included in the graph.
