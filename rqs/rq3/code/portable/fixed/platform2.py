import platform
import pytest

class TestPlatformDetails:

    def test_release_is_string(self):
        release = platform.release()
        assert isinstance(release, str)
        assert len(release) > 0

    def test_version_is_string(self):
        version = platform.version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_processor_info(self):
        processor = platform.processor()
        assert isinstance(processor, str)
        # processor may be empty on some platforms, so just check type
        assert processor is not None

    def test_python_build_structure(self):
        build = platform.python_build()
        assert isinstance(build, tuple)
        assert len(build) == 2
        assert all(isinstance(part, str) for part in build)
