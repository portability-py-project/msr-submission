import tempfile
import os
import pytest

from breds.commons import blocks


@pytest.fixture
def tmp_file():
    with tempfile.NamedTemporaryFile(mode="wt", delete=False, dir=tempfile.gettempdir()) as f:
        for _ in range(100):
            f.write("\n")
        f.flush()
        tmp_path = f.name
    yield tmp_path
    os.remove(tmp_path)


def test_blocks(tmp_file):
    with open(tmp_file, "rb") as f_in:
        assert sum(bl.count(b"\n") for bl in blocks(f_in)) == 100