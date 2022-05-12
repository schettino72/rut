
DOIT_CONFIG = {
    'verbosity': 2,
    'continue': True,
    'default_tasks': ['pyflakes', 'mypy', 'pycodestyle'],
}

def task_pyflakes():
    return {
        'actions': ['pyflakes src tests'],
    }

def task_mypy():
    return {
        'actions': ['mypy src'],
    }

def task_pycodestyle():
    return {
        'actions': ['pycodestyle src'],
    }




def task_coverage():
    return {
        'actions': [
            'coverage erase; coverage run -m rut; coverage report -m --omit="/tmp/*"',
        ],
    }
