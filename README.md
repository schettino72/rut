
# rut - Run Unit Tests

Experimental stuff... come back later.


## Usage

### Fixtures




### pytest built-in fixtures

Use stdlib context managers instead of pytest fixtures:

tmpdir -> tempfile

capsys -> contextlib.redirect_stdout

monkeypatch -> unittest.mock.patch

```
monkeypatch.setattr(DbmDB, 'DBM_CONTENT_ERROR_MSG', 'xxx')
```

```
from unitttest.mock import patch
patch.object(DbmDB, 'DBM_CONTENT_ERROR_MSG', 'xxx')
```


## Development

// pyflakes + mypy + pycodestyle
$ doit

// test
$ rut

// coverage
$ python cov.py


## internals

- __init__.py
  -> API: fixtures

- `__main__.py`
  -> rich CLI

- collect.py
  -> Collector: find & import python modules
  -> Selector: inspect python modules & get test references

- case.py
  -> TestCase: test case metadata
  -> FailureInfo, ErrorInfo: save details of test case error/failure
  -> CaseOutcome: outcome of TestCase Execution

- ctl.py
  -> high level runner + reporter

- checker.py
  -> check/assertion helpers

- saq.py
  -> Subprocess async queue. Handle multi-process execution and sync

- runner.py
  -> run selected test case

- reporter.py
  -> produce terminal output from TestOutcomes.


## Emacs color config

;; custom hi-lock colors for python / rut
;; https://anch.dev/en/tools/emacs/hi-lock-mode/
;;# Hi-lock: (("check" (0 (quote hi-green-b) prepend)))
(add-hook 'elpy-mode-hook
          (lambda ()
            (highlight-regexp "check" (quote hi-green-b))
            (highlight-regexp "assert" (quote hi-red-b))
            ))
