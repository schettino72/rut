# Development

Notes for working on `rut` itself. For user documentation see [README.md](README.md).

## Setup

```bash
uv sync --dev
```

## Running Tests

```bash
./run_tests.sh          # all tests
./run_tests.sh --cov    # with coverage report
```

The suite is plain `unittest` run through `unittest discover` — *not* through `rut`
itself, to avoid the runner being unable to report its own breakage.

## Linting

```bash
ruff check
```

## Dependency Sources

`pyproject.toml` declares `[tool.uv.sources]`, which makes `uv` resolve some
dependencies from local checkouts instead of PyPI:

```toml
[tool.uv.sources]
rut = { path = ".", editable = true }
```

Additionally, `uv_unreleased.toml` (not tracked in git) can override sources to point
at sibling checkouts of unreleased dependencies. To enable it, symlink it as `uv.toml`
so `uv` picks it up automatically:

```bash
ln -s uv_unreleased.toml uv.toml
```

This is how you develop against an unreleased `import-deps`. Remove the symlink to go
back to PyPI versions.

**CI sets `UV_NO_SOURCES: true`** so it ignores all of the above and installs from
PyPI. That is deliberate: it verifies the package works with the dependency versions
users will actually get. If a build passes locally but fails in CI, an unreleased local
dependency is the first thing to check:

```bash
UV_NO_SOURCES=true uv sync --dev && ./run_tests.sh
```

## Release Procedure

The version is stored in **two** places that must stay in sync:

- `pyproject.toml` → `version`
- `src/rutlib/__init__.py` → `__version__`

Steps (using `X.Y.Z` as the new version):

1. Verify the release resolves against PyPI, not local checkouts:

   ```bash
   UV_NO_SOURCES=true uv sync --dev
   ./run_tests.sh
   ruff check
   ```

   Make sure every dependency version required in `pyproject.toml` is actually
   published. Confirm CI is green on `main` for all supported Python versions.

2. In `CHANGES`, replace the `X.Y.Z (unreleased)` header with the release date:
   `X.Y.Z (YYYY-MM-DD)`.

3. Bump `version` in `pyproject.toml` and `__version__` in `src/rutlib/__init__.py`
   from `X.Y.Z.devN` to `X.Y.Z`.

4. `uv sync` to refresh `uv.lock` with the new version.

5. Commit as `release X.Y.Z` and tag:

   ```bash
   git commit -am "release X.Y.Z"
   git tag X.Y.Z
   ```

6. Build. Clear `dist/` first — it is gitignored and keeps artifacts from previous
   releases, which `twine upload dist/*` would otherwise try to re-upload:

   ```bash
   rm -rf dist/
   uv run python -m build
   uv run twine check dist/*
   ```

7. Upload:

   ```bash
   uv run twine upload dist/*
   ```

8. Push the commit and the tag:

   ```bash
   git push && git push --tags
   ```

9. Open the next development cycle: bump both version strings to the next
   `X.Y+1.0.dev0`, add a `X.Y+1.0 (unreleased)` section at the top of `CHANGES`, and
   commit as `start dev X.Y+1`.

## Website

The site is published to GitHub Pages from `docs/`, but **`docs/` is generated output —
never edit it directly.** The source lives in `marketing/gh-pages/` (a separate git
repo, gitignored here).

```bash
cd marketing
./serve.sh      # preview at http://localhost:4000/rut/
./publish.sh    # copy gh-pages/* into ../docs/
```

After `publish.sh`, commit the `docs/` changes in this repo to deploy.
