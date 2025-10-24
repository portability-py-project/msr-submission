import tempfile
import os
import pytest

from breds.commons import blocks


@pytest.fixture
def tmp_file():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        for _ in range(100):
            f.write(b"\n")
        f.flush()
        tmp_path = f.name  # store path before file is closed
    yield tmp_path
    os.remove(tmp_path)  # clean up after the test


def test_blocks(tmp_file):
    with open(tmp_file, "rb") as f_in:
        assert sum(bl.count(b"\n") for bl in blocks(f_in)) == 100