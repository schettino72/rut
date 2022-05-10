
DOIT_CONFIG = {
    'verbosity': 2,
    'continue': True,
}

def task_pyflakes():
    return {
        'actions': ['pyflakes src'],
    }

def task_mypy():
    return {
        'actions': ['mypy src'],
    }

def task_pycodestyle():
    return {
        'actions': ['pycodestyle src'],
    }
