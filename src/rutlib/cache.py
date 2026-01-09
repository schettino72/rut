"""
File hash caching for incremental testing.

Stores SHA256 hashes of source files after successful test runs.
On subsequent runs with --changed, compares current hashes to detect modifications.
"""

import hashlib
import json
from pathlib import Path


CACHE_DIR = Path('.rut_cache')
CACHE_FILE = CACHE_DIR / 'file_hashes.json'


def compute_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def load_cache() -> dict[str, str]:
    """Load cached file hashes."""
    if not CACHE_FILE.exists():
        return {}
    return json.loads(CACHE_FILE.read_text())


def save_cache(hashes: dict[str, str]):
    """Save file hashes to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(hashes, indent=2))


def get_modified_files(source_dirs: list[str]) -> set[str]:
    """Get files that changed since last successful run."""
    cached = load_cache()
    modified = set()

    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.is_dir():
            continue
        for py_file in source_path.rglob('*.py'):
            path_str = str(py_file)
            current_hash = compute_hash(py_file)
            if cached.get(path_str) != current_hash:
                modified.add(path_str)

    return modified


def update_cache(source_dirs: list[str]):
    """Update cache with current file hashes (call after successful run)."""
    hashes = {}
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.is_dir():
            continue
        for py_file in source_path.rglob('*.py'):
            hashes[str(py_file)] = compute_hash(py_file)
    save_cache(hashes)
