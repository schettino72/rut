# This is a dummy module for testing warning filters.
import warnings

def do_warning():
    warnings.warn("This is a specific warning", UserWarning)
