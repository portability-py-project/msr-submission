import sys
from subprocess import run
from importlib import import_module

def run_command(command):
    module_name = 'main'
    module = import_module(module_name)
    sys.argv = [module_name] + command.split()
    try:
        output = module.main()
        return output
    except AttributeError:
        from io import StringIO
        import sys
        capturedOutput = StringIO()                  # Create StringIO object
        sys.stdout = capturedOutput                  # Redirect stdout
        try:
            module.main()
        finally:
            sys.stdout = sys.__stdout__              # Reset stdout
        return capturedOutput.getvalue()

def test_foo():
    assert 'foo'.upper() == 'FOO'

def test_fastarg_no_methods():
    fastarg = import_module('fastarg')
    app = fastarg.Fastarg()
    assert len(app.commands) == 0

def test_fastarg_one_method():
    fastarg = import_module('fastarg')
    app = fastarg.Fastarg()

    @app.command()
    def foo():
        print("foo")

    assert len(app.commands) == 1

def test_command_get_name():
    fastarg = import_module('fastarg')
    app = fastarg.Fastarg()

    @app.command()
    def foo():
        print("foo")

    assert app.commands[0].get_name() == "foo"

def test_hello_world():
    output = run_command("hello_world foo")
    assert output == "hello foo\n"

def test_create_todo():
    output = run_command("todo create_todo 'drink water'")
    assert output == "create todo: drink water - False\n"