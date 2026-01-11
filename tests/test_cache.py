import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rutlib.cache import compute_hash, load_cache, save_cache, get_modified_files, update_cache, CACHE_DIR, CACHE_FILE
from rutlib.__main__ import should_update_cache


class TestComputeHash(unittest.TestCase):
    def test_compute_hash_returns_hex_string(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            try:
                result = compute_hash(Path(f.name))
                self.assertIsInstance(result, str)
                self.assertEqual(len(result), 64)  # SHA256 hex is 64 chars
            finally:
                os.unlink(f.name)

    def test_compute_hash_different_content_different_hash(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write("content1")
            f1.flush()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                f2.write("content2")
                f2.flush()
                try:
                    hash1 = compute_hash(Path(f1.name))
                    hash2 = compute_hash(Path(f2.name))
                    self.assertNotEqual(hash1, hash2)
                finally:
                    os.unlink(f1.name)
                    os.unlink(f2.name)


class TestCacheOperations(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cache_dir = CACHE_DIR
        self.original_cache_file = CACHE_FILE

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_cache_empty_when_no_file(self):
        with patch('rutlib.cache.CACHE_FILE', Path(self.test_dir) / 'nonexistent.json'):
            result = load_cache()
            self.assertEqual(result, {})

    def test_save_and_load_cache(self):
        cache_file = Path(self.test_dir) / 'cache' / 'test.json'
        with patch('rutlib.cache.CACHE_FILE', cache_file):
            with patch('rutlib.cache.CACHE_DIR', cache_file.parent):
                test_data = {'file1.py': 'abc123', 'file2.py': 'def456'}
                save_cache(test_data)
                loaded = load_cache()
                self.assertEqual(loaded, test_data)


class TestGetModifiedFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = Path(self.test_dir) / 'src'
        self.src_dir.mkdir()
        (self.src_dir / 'module.py').write_text("original")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_all_files_modified_when_no_cache(self):
        with patch('rutlib.cache.load_cache', return_value={}):
            modified = get_modified_files([str(self.src_dir)])
            self.assertIn(str(self.src_dir / 'module.py'), modified)

    def test_unchanged_file_not_in_modified(self):
        file_path = str(self.src_dir / 'module.py')
        current_hash = compute_hash(Path(file_path))
        with patch('rutlib.cache.load_cache', return_value={file_path: current_hash}):
            modified = get_modified_files([str(self.src_dir)])
            self.assertNotIn(file_path, modified)

    def test_changed_file_in_modified(self):
        file_path = str(self.src_dir / 'module.py')
        with patch('rutlib.cache.load_cache', return_value={file_path: 'old_hash'}):
            modified = get_modified_files([str(self.src_dir)])
            self.assertIn(file_path, modified)


class TestUpdateCache(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = Path(self.test_dir) / 'src'
        self.src_dir.mkdir()
        (self.src_dir / 'module.py').write_text("content")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_update_cache_stores_hashes(self):
        cache_file = Path(self.test_dir) / 'cache' / 'test.json'
        with patch('rutlib.cache.CACHE_FILE', cache_file):
            with patch('rutlib.cache.CACHE_DIR', cache_file.parent):
                update_cache([str(self.src_dir)])
                loaded = load_cache()
                file_path = str(self.src_dir / 'module.py')
                self.assertIn(file_path, loaded)
                self.assertEqual(len(loaded[file_path]), 64)


class MockResult:
    def __init__(self, successful, tests_run):
        self._successful = successful
        self.testsRun = tests_run

    def wasSuccessful(self):
        return self._successful


class TestShouldUpdateCache(unittest.TestCase):
    def test_no_update_when_keyword_filter_used(self):
        result = MockResult(successful=True, tests_run=5)
        self.assertFalse(should_update_cache(result, keyword="some_test"))

    def test_update_when_no_keyword_filter(self):
        result = MockResult(successful=True, tests_run=5)
        self.assertTrue(should_update_cache(result, keyword=None))

    def test_no_update_when_tests_failed(self):
        result = MockResult(successful=False, tests_run=5)
        self.assertFalse(should_update_cache(result, keyword=None))

    def test_no_update_when_no_tests_ran(self):
        result = MockResult(successful=True, tests_run=0)
        self.assertFalse(should_update_cache(result, keyword=None))
