import pytest
from pathlib import Path

class TestFileMathWithOpen:

    def setup_method(self):
        self.test_file = Path("numbers.txt")
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("\n".join(["1", "2", "3", "4", "5"]))

    def teardown_method(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_read_numbers(self):
        with open(self.test_file, "r", encoding="utf-8") as f:
            numbers = [int(line.strip()) for line in f.readlines()]
        assert numbers == [1, 2, 3, 4, 5]

    def test_sum_numbers(self):
        with open(self.test_file, "r", encoding="utf-8") as f:
            numbers = [int(line.strip()) for line in f.readlines()]
        assert sum(numbers) == 15

    def test_average_numbers(self):
        with open(self.test_file, "r", encoding="utf-8") as f:
            numbers = [int(line.strip()) for line in f.readlines()]
        avg = sum(numbers) / len(numbers)
        assert avg == 3

    def test_square_numbers(self):
        with open(self.test_file, "r", encoding="utf-8") as f:
            numbers = [int(line.strip()) for line in f.readlines()]
        squared = [n**2 for n in numbers]
        assert squared == [1, 4, 9, 16, 25]
