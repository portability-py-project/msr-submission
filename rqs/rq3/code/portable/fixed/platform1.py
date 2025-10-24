import platform
import pytest

class TestInfo:

    def test_system_is_string(self):
        system = platform.system()
        assert isinstance(system, str)
        assert len(system) > 0

    def test_machine_is_string(self):
        machine = platform.machine()
        assert isinstance(machine, str)
        assert len(machine) > 0

    def test_python_version(self):
        version = platform.python_version()
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_platform_summary(self):
        summary = platform.platform()
        assert isinstance(summary, str)
        assert platform.system() in summary
