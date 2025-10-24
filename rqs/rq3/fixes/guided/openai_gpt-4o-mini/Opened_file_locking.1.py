import tempfile
import os
import pytest
import atexit

from breds.commons import blocks


@pytest.fixture
def tmp_file():
    """Create a temporary file with 100 lines, each containing a single byte"""
    tmp_file = tempfile.NamedTemporaryFile(mode="wt", delete=False)
    atexit.register(lambda: os.remove(tmp_file.name))  # clean up after the test
    for _ in range(100):
        tmp_file.write("\n")
    tmp_file.flush()
    tmp_path = tmp_file.name  # store path before function exits
    tmp_file.close()  # close the file to release it for subsequent access
    yield tmp_path


def test_blocks(tmp_file):
    """Test that the blocks function returns the correct number of lines"""
    with open(tmp_file, "rb") as f_in:
        assert sum(bl.count(b"\n") for bl in blocks(f_in)) == 100