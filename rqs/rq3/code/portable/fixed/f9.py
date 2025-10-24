from src import fastarg
import subprocess
import sys

def run_command(command):
    """Helper function to run a command and return normalized output"""
    completed_process = subprocess.run(f"{sys.executable} {command}", shell=True, capture_output=True)
    return completed_process.stdout.decode("utf-8").replace('\r\n', '\n')

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

def test_create_todo_completed():
    output = run_command("main.py todo create_todo \"drink water\" --completed")
    assert output == "create todo: drink water - True\n"

def test_create_address():
    output = run_command("main.py user address create_address 123 \"456 main st\" --city bellevue --state wa --zip 98004")
    assert output == "creating address for user 123\n456 main st bellevue wa 98004\n"