
# rut - Run Unit Tests

Experimental stuff... come back later.


pytest fixtures replacements from stdlib

tmpdir -> tempfile
capsys -> contextlib.redirect_stdout
monkeypatch -> unittest.mock.patch



## Emacs color config

;; custom hi-lock colors for python / rut
;; https://anch.dev/en/tools/emacs/hi-lock-mode/
;;# Hi-lock: (("check" (0 (quote hi-green-b) prepend)))
(add-hook 'elpy-mode-hook
          (lambda ()
            (highlight-regexp "check" (quote hi-green-b))
            (highlight-regexp "assert" (quote hi-red-b))
            ))
