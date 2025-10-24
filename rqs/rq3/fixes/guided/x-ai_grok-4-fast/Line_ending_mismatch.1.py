from src import fastarg
import subprocess
import sys

def run_command(command):
    """Helper function to run a command and return normalized output"""
    completed_process = subprocess.run(f"{sys.executable} {command}", shell=True, capture_output=True, text=True)
    return completed_process.stdout

def test_foo():
    assert 'foo'.upper() == 'FOO'

def test_fastarg_no_methods():
    app = fastarg.Fastarg()

    assert len(app.commands) == 0

def test_fastarg_one_method():
    app = fastarg.Fastarg()

    @app.command()
    def foo():
        print("foo")

    assert len(app.commands) == 1

def test_command_get_name():
    app = fastarg.Fastarg()

    @app.command()
    def foo():
        print("foo")

    assert app.commands[0].get_name() == "foo"

def test_hello_world():
    output = run_command("main.py hello_world foo")
    assert output == "hello foo\n"

def test_create_todo():
    output = run_command("main.py todo create_todo \"drink water\"")
    assert output == "create todo: drink water - False\n"