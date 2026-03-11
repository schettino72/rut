# Import Dependency Graph — Technical Reference

How rut builds, sorts, and uses the import dependency graph internally.

For the user-facing explanation, see the [website article](https://schettino72.github.io/rut/articles/import-graph).

## Key files

- `src/rutlib/runner.py` — orchestrates graph building and test ordering
- `src/rutlib/cache.py` — file hash caching for `--changed`
- `import-deps` library (external):
  - `import_deps/core.py` — AST parsing, module analysis
  - `import_deps/graph.py` — topological sort, cycle detection

## AST analysis

The `import-deps` library uses `ast.NodeVisitor` to extract imports:

```python
class _ImportsFinder(ast.NodeVisitor):
    def visit_Import(self, node):
        # captures: import X
        self.imports.extend((None, n.name, n.asname, None) for n in node.names)

    def visit_ImportFrom(self, node):
        # captures: from X import Y
        self.imports.extend((node.module, n.name, n.asname, node.level) for n in node.names)
```

- Parses each `.py` file into AST
- Visits all `Import` and `ImportFrom` nodes
- Returns tuples: `(module, name, asname, level)` where `level` handles relative imports
- No runtime instrumentation — purely static

## Data structures

**import-deps graph output:**

```python
class ModuleResult(TypedDict):
    module: str              # e.g., "foo.bar.baz"
    filepath: str            # path to module file
    imports: list[str]       # direct imports (FQN)
    all_imports: list[str]   # transitive imports

class SortResult(NamedTuple):
    modules: list[str]              # topologically sorted module names
    filepaths: dict[str, str]       # module_name -> filepath
    levels: dict[str, int]          # distance from sources (entry points)
    depths: dict[str, int]          # distance from sinks (leaf nodes)
```

**In rut's runner.py:**

```python
self.module_filepaths = {}       # module_name -> filepath
self.module_all_imports = {}     # module_name -> set of transitive deps
self.sorted_modules = []         # topologically sorted test modules
```

## Topological sort algorithm

`topological_sort()` in `graph.py` uses **Kahn's algorithm** with custom ranking:

1. **Build adjacency lists** — direct dependencies + reverse graph (dependents)
2. **Detect cycles** — DFS with recursion stack, marks all nodes in cycles
3. **Calculate depth** — distance from sinks (leaf nodes have depth=1)
4. **Calculate level** — distance from sources (entry points have level=1)
5. **Kahn's algorithm** — process nodes with in_degree=0, sorted by `(-level, depth, name)`:
   - Highest level first (deepest dependencies)
   - Lowest depth as tiebreaker (simpler/leaf nodes)
   - Alphabetical as final tiebreaker

Result: dependencies always run before dependents.

## Circular dependencies

Detection uses DFS with a recursion stack to find back edges → strongly connected components.

Cycle nodes get `level=-1` and `depth=-1`, are excluded from Kahn's processing, and appended at the end in alphabetical order. Circular imports don't break sorting.

## `--changed` — affected test detection

**Hash comparison** (`cache.py`):
- SHA256 hash of every `.py` file in `source_dirs`
- Stored in `.rut_cache/file_hashes.json`
- On `--changed`, compare current hashes vs cached → set of modified files
- Cache only updated after a **successful** test run

**Transitive dependency walking** (`runner.py`):
- Convert modified file paths to module names
- For each test module, check if the module itself changed OR any of its transitive imports (`module_all_imports`) intersect with modified modules
- `get_all_imports()` computes transitive closure via BFS

```
Test is affected if:
  test_module ∈ modified_modules  OR
  module_all_imports[test_module] ∩ modified_modules ≠ ∅
```

## What is NOT tracked

- **Dynamic imports**: `importlib.import_module()` — not visible in AST
- **Non-Python files**: templates, SQL, config, data files
- **Conditional nature**: imports inside `if/try` blocks are tracked as normal imports (the conditionality is lost)
- **Cross-package**: only files within configured `source_dirs` are in the graph

## Runner integration flow

```
1. load_tests()          → discover all test files
2. sort_tests()          → _get_topological_order():
   a. scan source_dirs for .py files
   b. create ModuleSet (import-deps)
   c. AST-parse each file for imports
   d. topological_sort() → SortResult
   e. store module_filepaths, module_all_imports, sorted_modules
3. if --changed:
   a. get_modified_files() → hash comparison
   b. _filter_modified()   → walk transitive deps → affected tests only
4. execute tests in dependency order
```
