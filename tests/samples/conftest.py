# This file is used by tests/test_runner.py::TestRunnerHooks

def rut_session_setup():
    # This hook is called once before the test session starts.
    # It creates a temporary file that the test will check for.
    with open("tests/samples/setup.tmp", "w") as f:
        f.write("setup")

def rut_session_teardown():
    # This hook is called once after the test session ends.
    # It creates a temporary file that the test will check for.
    with open("tests/samples/teardown.tmp", "w") as f:
        f.write("teardown")
